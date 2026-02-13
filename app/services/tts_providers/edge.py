"""
Microsoft Edge TTS 引擎
基于 edge-tts 库实现，免费调用微软语音合成服务
"""
import asyncio
import edge_tts
from typing import List, Dict, Tuple, Optional
from .base import TTSProvider


# 重试配置
MAX_RETRIES = 3
BASE_DELAY = 2  # 秒，指数退避基数


class EdgeTTSProvider(TTSProvider):
    """Microsoft Edge TTS 提供商（带自动重试）"""

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
                
                return True, timings
                
            except Exception as e:
                last_error = e
                if attempt < MAX_RETRIES:
                    delay = BASE_DELAY * (2 ** (attempt - 1))  # 2s, 4s, 8s
                    print(f"[EdgeTTS] 第 {attempt} 次失败，{delay}s 后重试: {e}")
                    await asyncio.sleep(delay)
                else:
                    print(f"[EdgeTTS] 合成失败 (已重试 {MAX_RETRIES} 次): {e}")

        return False, None

    def get_voices(self) -> List[Dict]:
        return self.voices

    def get_name(self) -> str:
        return "edge"

    def get_supported_formats(self) -> List[str]:
        return ["mp3"]

