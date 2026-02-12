"""
项目统一配置管理
所有路径常量和配置项均从此处获取
"""
import os
from functools import lru_cache


class Settings:
    # 基础配置
    PROJECT_NAME: str = "有声书制作系统"
    VERSION: str = "2.1.0"

    # 路径配置
    EBOOK_INPUT_DIR: str = os.getenv("EBOOK_INPUT_DIR", "ebook_input")
    AUDIO_DIR: str = os.getenv("AUDIO_DIR", "audio")
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "output")

    # LLM 配置
    LLM_API_BASE: str = os.getenv("LLM_API_BASE", "http://192.168.188.160:11435/v1")
    LLM_MODEL_NAME: str = os.getenv("LLM_MODEL_NAME", "qwen3:14b")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "EMPTY")

    # TTS 配置
    TTS_PROVIDER: str = os.getenv("TTS_PROVIDER", "edge")

    # 功能开关
    ENABLE_SMART_PARSING: bool = os.getenv("ENABLE_SMART_PARSING", "False").lower() == "true"


@lru_cache()
def get_settings():
    return Settings()
