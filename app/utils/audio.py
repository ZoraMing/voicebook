import os
from typing import List, Optional
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
    将多个音频文件合并为单个 WAV 文件。
    使用低采样率和单声道保持小体积。
    
    Args:
        audio_paths: 音频文件路径列表
        output_path: 输出 WAV 文件路径
        sample_rate: 采样率（默认 16kHz）
        channels: 声道数（默认单声道）
    
    Returns:
        是否成功
    """
    try:
        from pydub import AudioSegment
    except ImportError:
        print("[导出] 错误: 需要安装 pydub 库: pip install pydub")
        return False
    
    try:
        # 创建空音频
        combined = AudioSegment.empty()
        skipped = 0
        
        for audio_path in audio_paths:
            # 调试信息
            # print(f"[合并调试] 检查路径: {audio_path}")
            if not audio_path:
                skipped += 1
                continue
                
            full_path = os.path.abspath(audio_path)
            if not os.path.exists(full_path):
                # print(f"[合并调试] 物理文件不存在: {full_path}")
                skipped += 1
                continue
            
            # 加载音频片段
            try:
                # print(f"[合并调试] 正在加载: {audio_path}")
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
        
        # 转换参数：低采样率、单声道、16位
        combined = combined.set_frame_rate(sample_rate)
        combined = combined.set_channels(channels)
        combined = combined.set_sample_width(2)  # 16位
        
        # 导出为 WAV
        combined.export(output_path, format="wav")
        
        file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        duration_min = len(combined) / 60000
        print(f"[导出] WAV 已生成: {output_path} "
              f"(时长: {duration_min:.1f}分钟, 大小: {file_size_mb:.1f}MB)")
        
        return True
        
    except Exception as e:
        print(f"[导出] 音频合并失败: {e}")
        import traceback
        traceback.print_exc()
        return False
