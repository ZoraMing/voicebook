"""
Microsoft Edge TTS 引擎
基于 edge-tts 库实现，免费调用微软语音合成服务
"""
import asyncio
import os
import edge_tts
from typing import List, Dict, Tuple, Optional
from .base import TTSProvider


# 重试配置
MAX_RETRIES = 3
BASE_DELAY = 2  # 秒，指数退避基数
MIN_AUDIO_SIZE = 1024  # 最小有效音频大小（字节），小于此值视为生成失败


class EdgeTTSProvider(TTSProvider):
    """Microsoft Edge TTS 提供商（带自动重试和文件完整性验证）"""

    def __init__(self):
        self.voices = [
            {"id": "xiaoxiao", "name": "晓晓", "voice": "zh-CN-XiaoxiaoNeural", "gender": "女"},
            {"id": "yunxi", "name": "云希", "voice": "zh-CN-YunxiNeural", "gender": "男"},
            {"id": "xiaoyi", "name": "晓伊", "voice": "zh-CN-XiaoyiNeural", "gender": "女"},
            {"id": "yunjian", "name": "云健", "voice": "zh-CN-YunjianNeural", "gender": "男"},
        ]

    async def generate_audio(self, text: str, voice: str, output_path: str) -> Tuple[bool, Optional[List[dict]]]:
        # 如果传入的是短 id（如 xiaoxiao），转换为完整 voice key
        voice_key = voice
        for v in self.voices:
            if v["id"] == voice:
                voice_key = v["voice"]
                break

        last_error = None
        for attempt in range(1, MAX_RETRIES + 1):
            # 每次尝试前清理可能存在的不完整文件
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except OSError as e:
                    print(f"[EdgeTTS] 警告: 清理旧文件失败 {output_path}: {e}")

            try:
                communicate = edge_tts.Communicate(text, voice_key)
                timings = []

                with open(output_path, "wb") as f:
                    async for chunk in communicate.stream():
                        if chunk["type"] == "audio":
                            f.write(chunk["data"])
                        elif chunk["type"] == "WordBoundary":
                            timings.append({
                                "text": chunk["text"],
                                "offset": chunk["offset"],
                                "duration": chunk["duration"]
                            })

                # 验证输出文件是否有效（非空且大小正常）
                file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
                if file_size < MIN_AUDIO_SIZE:
                    raise ValueError(
                        f"生成的音频文件过小或为空 (大小: {file_size} 字节，最小要求: {MIN_AUDIO_SIZE} 字节)"
                    )

                return True, timings

            except Exception as e:
                last_error = e
                # 清理本次失败产生的空/不完整文件
                if os.path.exists(output_path):
                    try:
                        os.remove(output_path)
                    except OSError:
                        pass

                if attempt < MAX_RETRIES:
                    delay = BASE_DELAY * (2 ** (attempt - 1))  # 2s, 4s, 8s
                    print(f"[EdgeTTS] ⚠️ 第 {attempt} 次失败，{delay}s 后重试: {e}")
                    await asyncio.sleep(delay)
                else:
                    print(f"[EdgeTTS] ❌ 合成失败（已重试 {MAX_RETRIES} 次）: {e}")

        return False, None

    def get_voices(self) -> List[Dict]:
        return self.voices

    def get_name(self) -> str:
        return "edge"

    def get_supported_formats(self) -> List[str]:
        return ["mp3"]
