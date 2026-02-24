import os
import subprocess
import shutil
import sys
from pathlib import Path
from typing import List, Optional

# Python 3.13+ audioop 兼容性补丁
try:
    import audioop
except ImportError:
    try:
        import audioop_lts as audioop
        sys.modules['audioop'] = audioop
    except ImportError:
        pass

from app.config import get_settings

try:
    from mutagen.mp3 import MP3
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False


def get_audio_duration(audio_path: str) -> Optional[int]:
    """获取音频时长(毫秒)"""
    if not MUTAGEN_AVAILABLE or not os.path.exists(audio_path):
        return None
    try:
        audio = MP3(audio_path)
        return int(audio.info.length * 1000)
    except Exception:
        return None


def merge_audio_to_wav(
    audio_paths: List[str],
    output_path: str,
    sample_rate: int = 16000,
    channels: int = 1
) -> bool:
    """
    向后兼容的 WAV 合并函数，内部调用 merge_audio。
    """
    return merge_audio(audio_paths, output_path, output_format="wav",
                       sample_rate=sample_rate, channels=channels)


def merge_audio(
    audio_paths: List[str],
    output_path: str,
    output_format: str = "mp3",
    sample_rate: int = 24000,
    channels: int = 1,
    bitrate: str = "64k") -> bool:
    """
    将多个音频文件合并为单个音频文件。
    
    Args:
        audio_paths: 音频文件路径列表
        output_path: 输出文件路径
        output_format: 输出格式 ("mp3", "wav", "ogg")
        sample_rate: 采样率（默认 24kHz，有声书足够）
        channels: 声道数（默认单声道）
        bitrate: MP3 比特率（默认 64k，有声书推荐值）
    
    Returns:
        是否成功
    """
    try:
        from pydub import AudioSegment
    except Exception as e:
        print(f"[导出] 报错详情: {e}")
        return False
    
    try:
        # 创建空音频
        combined = AudioSegment.empty()
        skipped = 0
        
        for audio_path in audio_paths:
            if not audio_path:
                skipped += 1
                continue
                
            full_path = os.path.abspath(audio_path)
            if not os.path.exists(full_path):
                skipped += 1
                continue
            
            # 加载音频片段
            try:
                segment = AudioSegment.from_file(full_path)
                combined += segment
            except Exception as e:
                print(f"[导出] 警告: 加载音频失败 {audio_path}: {e}")
                skipped += 1
                continue
        
        if len(combined) == 0:
            print("[导出] 错误: 没有可用的音频片段")
            return False
        
        if skipped > 0:
            print(f"[导出] 跳过了 {skipped} 个无音频的段落")
        
        # 转换参数：采样率、单声道
        combined = combined.set_frame_rate(sample_rate)
        combined = combined.set_channels(channels)
        
        # 导出
        export_params = {"format": output_format}
        if output_format == "mp3":
            export_params["bitrate"] = bitrate
        elif output_format == "wav":
            combined = combined.set_sample_width(2)  # 16位 WAV
        
        combined.export(output_path, **export_params)
        
        file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        duration_min = len(combined) / 60000
        fmt_label = output_format.upper()
        # print(f"[导出] {fmt_label} 已生成: {output_path} "
        #       f"(时长: {duration_min:.1f}分钟, 大小: {file_size_mb:.1f}MB)")
        
        return True
        
    except Exception as e:
        print(f"[导出] 音频合并失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def _generate_cover_image(
    book_title: str,
    author: str,
    segment_name: str,
    size: int = 600,
) -> bytes:
    """
    生成文字专辑封面图片（JPEG 字节流）。

    尝试用 Pillow 绘制渐变背景 + 标题文字。
    若 Pillow 不可用，退回为纯色 JPEG 占位图。

    Args:
        book_title:   书名（大标题）
        author:       作者名
        segment_name: 当前音频段名称（如 chapters1-3）
        size:         正方形封面边长（像素）

    Returns:
        JPEG 图像的字节内容
    """
    import io

    try:
        from PIL import Image, ImageDraw, ImageFont

        # ---- 背景渐变（从深蓝到深紫） ----
        img = Image.new("RGB", (size, size))
        draw = ImageDraw.Draw(img)
        top_color    = (20,  30,  80)   # 深蓝
        bottom_color = (60,  10,  80)   # 深紫

        for y in range(size):
            ratio = y / size
            r = int(top_color[0] + (bottom_color[0] - top_color[0]) * ratio)
            g = int(top_color[1] + (bottom_color[1] - top_color[1]) * ratio)
            b = int(top_color[2] + (bottom_color[2] - top_color[2]) * ratio)
            draw.line([(0, y), (size, y)], fill=(r, g, b))

        # ---- 字体（优先系统中文字体，回退 default） ----
        def _load_font(size_pt: int) -> ImageFont.ImageFont:
            candidates = [
                "msyh.ttc",          # 微软雅黑（Windows）
                "simhei.ttf",        # 黑体（Windows）
                "PingFang.ttc",      # 苹方（macOS）
                "NotoSansCJK-Regular.ttc",  # Noto（Linux）
                "Arial.ttf",
            ]
            for name in candidates:
                try:
                    return ImageFont.truetype(name, size_pt)
                except Exception:
                    continue
            return ImageFont.load_default()

        font_title  = _load_font(52)
        font_author = _load_font(34)
        font_seg    = _load_font(26)

        # ---- 辅助：自动换行 ----
        def _wrap(text: str, font, max_w: int) -> list[str]:
            lines, cur = [], ""
            for ch in text:
                test = cur + ch
                w = font.getlength(test) if hasattr(font, "getlength") else len(test) * 20
                if w > max_w:
                    lines.append(cur)
                    cur = ch
                else:
                    cur = test
            if cur:
                lines.append(cur)
            return lines or [text]

        margin = 48
        max_w  = size - margin * 2
        y_cur  = size // 4   # 从 1/4 高度开始绘文字

        # ---- 书名 ----
        for line in _wrap(book_title, font_title, max_w):
            draw.text((size // 2, y_cur), line,
                      font=font_title, fill=(255, 255, 255),
                      anchor="mt", stroke_width=2, stroke_fill=(0, 0, 0))
            y_cur += 66

        y_cur += 16

        # ---- 作者 ----
        if author:
            draw.text((size // 2, y_cur), f"— {author} —",
                      font=font_author, fill=(200, 210, 255),
                      anchor="mt")
            y_cur += 50

        # ---- 分隔线 ----
        lx = size // 4
        draw.line([(lx, y_cur + 12), (size - lx, y_cur + 12)],
                  fill=(100, 120, 200), width=2)
        y_cur += 36

        # ---- 段落标签 ----
        draw.text((size // 2, y_cur), segment_name,
                  font=font_seg, fill=(160, 180, 220),
                  anchor="mt")

        # ---- 转为 JPEG bytes ----
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        return buf.getvalue()

    except Exception:
        # Pillow 不可用或绘图失败：返回纯深蓝色 JPEG 占位
        import struct, zlib
        # 构造最小 1x1 深蓝色 JPEG（约 600 字节）
        try:
            from PIL import Image
            img = Image.new("RGB", (size, size), color=(20, 30, 80))
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=80)
            return buf.getvalue()
        except Exception:
            # 硬编码最小黑色 JPEG
            return (
                b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
                b'\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t'
                b'\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a'
                b'\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\x1e'
                b'\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00'
                b'\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00'
                b'\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b'
                b'\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xfb\xff\xd9'
            )


def tag_mp3_metadata(
    mp3_path: str,
    title: str,
    album: str,
    artist: str,
    segment_name: str = "",
    track: int = 0,
    total_tracks: int = 0,
) -> bool:
    """
    使用 mutagen 为 MP3 文件写入 ID3 元数据标签，并嵌入文字专辑封面。

    Args:
        mp3_path:     目标 MP3 文件路径
        title:        曲目标题（通常为"书名 · segmentName"）
        album:        专辑名（书名）
        artist:       艺术家/作者名
        segment_name: 段落名称，用于封面生成
        track:        当前曲目序号（0 = 不写入）
        total_tracks: 总曲目数（0 = 不写入）

    Returns:
        成功写入返回 True，mutagen 不可用或异常返回 False
    """
    if not MUTAGEN_AVAILABLE:
        return False

    if not os.path.exists(mp3_path):
        return False

    try:
        from mutagen.id3 import (
            ID3, ID3NoHeaderError,
            TIT2, TALB, TPE1, TPE2, TRCK, TCON,
            APIC, Encoding
        )

        # 加载或创建 ID3 标签
        try:
            tags = ID3(mp3_path)
        except ID3NoHeaderError:
            tags = ID3()

        # 基础文本标签
        tags["TIT2"] = TIT2(encoding=Encoding.UTF8, text=title)
        tags["TALB"] = TALB(encoding=Encoding.UTF8, text=album)
        tags["TPE1"] = TPE1(encoding=Encoding.UTF8, text=artist)   # 主要艺术家
        tags["TPE2"] = TPE2(encoding=Encoding.UTF8, text=artist)   # 专辑艺术家
        tags["TCON"] = TCON(encoding=Encoding.UTF8, text="Audiobook")

        if track > 0:
            track_str = f"{track}/{total_tracks}" if total_tracks > 0 else str(track)
            tags["TRCK"] = TRCK(encoding=Encoding.UTF8, text=track_str)

        # 生成并嵌入封面图
        cover_data = _generate_cover_image(album, artist, segment_name or title)
        tags["APIC"] = APIC(
            encoding=Encoding.UTF8,
            mime="image/jpeg",
            type=3,          # 3 = 封面（front cover）
            desc="Cover",
            data=cover_data,
        )

        tags.save(mp3_path, v2_version=3)
        return True

    except Exception as e:
        print(f"[元数据] ⚠️ 写入 ID3 标签失败 {mp3_path}: {e}")
        return False
