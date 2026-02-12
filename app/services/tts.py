"""
TTS 语音合成服务
使用 Provider 模式支持多种 TTS 引擎（edge-tts / API / 本地模型）
"""
import asyncio
import os
import re
from pathlib import Path
from typing import List, Optional
from sqlalchemy.orm import Session

try:
    from mutagen.mp3 import MP3
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

from app import models, crud
from app.config import get_settings
from .tts_providers.base import TTSProvider
from .tts_providers.edge import EdgeTTSProvider

settings = get_settings()

# 音频存储目录（从统一配置获取）
AUDIO_DIR = Path(settings.AUDIO_DIR)
AUDIO_DIR.mkdir(exist_ok=True)


class TTSFactory:
    """
    TTS 引擎工厂
    支持注册和获取不同的 TTS Provider
    """
    _providers = {
        "edge": EdgeTTSProvider,
    }

    @classmethod
    def register(cls, name: str, provider_cls):
        """注册新的 TTS 引擎"""
        cls._providers[name] = provider_cls

    @classmethod
    def get_provider(cls, name: str = None) -> TTSProvider:
        """
        获取 TTS 引擎实例

        Args:
            name: 引擎名称，默认从配置读取
        """
        name = name or settings.TTS_PROVIDER
        if name not in cls._providers:
            available = ', '.join(cls._providers.keys())
            raise ValueError(f"不支持的 TTS 引擎: {name}，可用: {available}")
        return cls._providers[name]()


# 全局默认 Provider
_default_provider = TTSFactory.get_provider()

# 兼容旧 API 的语音列表
VOICES = _default_provider.get_voices()


def get_audio_path(book_id: int, paragraph_id: int) -> str:
    """获取音频文件路径"""
    book_dir = AUDIO_DIR / f"book_{book_id}"
    book_dir.mkdir(exist_ok=True)
    return str(book_dir / f"p_{paragraph_id}.mp3")


def get_audio_duration(audio_path: str) -> Optional[int]:
    """获取音频时长(毫秒)"""
    if not MUTAGEN_AVAILABLE or not os.path.exists(audio_path):
        return None
    try:
        audio = MP3(audio_path)
        return int(audio.info.length * 1000)
    except Exception:
        return None


def _clean_text_for_tts(text: str) -> str:
    """清理文本中不适合朗读的标点符号，替换为空格以防止朗读其名称"""
    if not text:
        return ""
    # 替换这些符号为空格: _ / \ | ~ * # % > - ” “ "
    # 这些通常是 Markdown 标识符或装饰符，朗读出来会影响流利度
    text = re.sub(r'[_/\\|~\*#%>\-”“"]', ' ', text)
    return ' '.join(text.split())


async def synthesize_paragraph(
    db: Session,
    paragraph: models.Paragraph,
    voice: str = "zh-CN-XiaoxiaoNeural",
    provider: Optional[TTSProvider] = None
) -> bool:
    """合成单个段落"""
    tts = provider or _default_provider

    try:
        # 更新状态为处理中
        crud.update_paragraph_status(db, paragraph.id, "processing")

        # 预处理文本：过滤不需要读出的符号
        clean_content = _clean_text_for_tts(paragraph.content)

        if not clean_content:
            # 如果清理后没有内容（全是无意义符号），直接标记完成并设置时长为 0
            crud.update_paragraph_audio(db, paragraph.id, "", 0)
            return True

        # 生成音频
        audio_path = get_audio_path(paragraph.book_id, paragraph.id)
        success = await tts.generate_audio(clean_content, voice, audio_path)

        if not success:
            crud.update_paragraph_status(db, paragraph.id, "failed", "TTS 合成失败")
            return False

        # 获取音频时长
        duration_ms = get_audio_duration(audio_path)
        if duration_ms is None:
            duration_ms = paragraph.estimated_duration_ms

        # 更新数据库
        crud.update_paragraph_audio(db, paragraph.id, audio_path, duration_ms)
        return True

    except Exception as e:
        crud.update_paragraph_status(db, paragraph.id, "failed", str(e))
        return False


async def _synthesize_batch_async(
    db: Session,
    paragraphs: List,
    voice: str,
    max_concurrent: int
) -> dict:
    """
    异步批量合成段落（核心并发逻辑）

    Args:
        db: 数据库会话
        paragraphs: 待合成段落列表
        voice: 语音名称
        max_concurrent: 最大并发数
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_with_limit(para):
        async with semaphore:
            return await synthesize_paragraph(db, para, voice)

    results = await asyncio.gather(*[process_with_limit(p) for p in paragraphs])

    completed = sum(1 for r in results if r)
    return {
        'total': len(paragraphs),
        'completed': completed,
        'failed': len(paragraphs) - completed
    }


def synthesize_book_background(
    book_id: int,
    voice: str = "zh-CN-XiaoxiaoNeural",
    max_concurrent: int = 5
):
    """
    后台任务专用的书籍合成函数
    - 创建独立的数据库 Session，避免线程安全问题
    - 在新事件循环中运行异步代码，适合在 BackgroundTasks 中运行
    """
    from app.database import SessionLocal

    db = SessionLocal()

    try:
        paragraphs = crud.get_pending_paragraphs(db, book_id)

        if not paragraphs:
            print(f"[TTS] 书籍 {book_id} 没有待合成的段落")
            return

        print(f"[TTS] 开始后台合成: 书籍 {book_id}, 共 {len(paragraphs)} 个段落, 并发数 {max_concurrent}")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(
                _synthesize_batch_async(db, paragraphs, voice, max_concurrent)
            )

            # 更新书籍整体进度
            crud.update_book_tts_progress(db, book_id)

            print(f"[TTS] 合成完成: 书籍 {book_id}, 成功 {result['completed']}, 失败 {result['failed']}")
        finally:
            loop.close()

    finally:
        db.close()
