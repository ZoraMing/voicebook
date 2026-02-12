"""
TTS 提供商基类
定义所有 TTS 引擎的统一接口，便于替换和扩展
"""
from abc import ABC, abstractmethod
from typing import List, Dict


class TTSProvider(ABC):
    """TTS 提供商基类"""

    @abstractmethod
    async def generate_audio(self, text: str, voice: str, output_path: str) -> bool:
        """
        生成音频文件

        Args:
            text: 待合成文本
            voice: 语音ID/名称
            output_path: 输出文件路径

        Returns:
            bool: 成功返回 True
        """
        pass

    @abstractmethod
    def get_voices(self) -> List[Dict]:
        """
        获取支持的语音列表

        Returns:
            List[Dict]: [{'id': '...', 'name': '...', 'voice': '...', 'gender': '...'}, ...]
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """返回引擎名称，如 'edge', 'azure', 'local'"""
        pass

    def get_supported_formats(self) -> List[str]:
        """返回引擎支持的输出音频格式，默认 mp3"""
        return ["mp3"]
