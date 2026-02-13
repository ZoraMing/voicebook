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
    bitrate: str = "64k"
) -> bool:
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
        print(f"[导出] {fmt_label} 已生成: {output_path} "
              f"(时长: {duration_min:.1f}分钟, 大小: {file_size_mb:.1f}MB)")
        
        return True
        
    except Exception as e:
        print(f"[导出] 音频合并失败: {e}")
        import traceback
        traceback.print_exc()
        return False

