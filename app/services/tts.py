"""
TTS 语音合成服务
使用 Provider 模式支持多种 TTS 引擎（edge-tts / API / 本地模型）
"""
import asyncio
import logging
import os
import re
from pathlib import Path
from typing import List, Optional
from sqlalchemy.orm import Session

from app import models, crud
from app.config import get_settings
from .tts_providers.base import TTSProvider
from .tts_providers.edge import EdgeTTSProvider

logger = logging.getLogger(__name__)

settings = get_settings()

# 音频存储目录（从统一配置获取）
AUDIO_DIR = Path(settings.AUDIO_DIR)
AUDIO_DIR.mkdir(exist_ok=True)

# 后台任务：合成失败后最多重试轮次
BACKGROUND_RETRY_ROUNDS = 2


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


from app.utils.text import clean_text_for_tts
from app.utils.audio import get_audio_duration

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
        clean_content = clean_text_for_tts(paragraph.content)

        if not clean_content:
            # 如果清理后没有内容（全是无意义符号），直接标记完成并设置时长为 0
            crud.update_paragraph_audio(db, paragraph.id, "", 0)
            return True

        # 生成音频
        audio_path = get_audio_path(paragraph.book_id, paragraph.id)
        result = await tts.generate_audio(clean_content, voice, audio_path)

        # 处理返回值：可能是 bool 或 (bool, timings)
        if isinstance(result, tuple):
            success, timings = result
        else:
            success = result
            timings = None

        if not success:
            crud.update_paragraph_status(db, paragraph.id, "failed", "TTS 合成失败（Provider 返回失败）")
            return False

        # 二次验证：确认磁盘上的音频文件存在且大小正常
        if not os.path.exists(audio_path) or os.path.getsize(audio_path) < 512:
            error_msg = f"音频文件缺失或过小: {audio_path}"
            logger.warning("[TTS] ⚠️ %s", error_msg)
            crud.update_paragraph_status(db, paragraph.id, "failed", error_msg)
            return False

        # 获取音频时长
        duration_ms = get_audio_duration(audio_path)
        if duration_ms is None:
            duration_ms = paragraph.estimated_duration_ms

        # 序列化时间戳
        sentence_timings_json = None
        if timings:
            import json
            sentence_timings_json = json.dumps(timings, ensure_ascii=False)

        # 更新数据库
        crud.update_paragraph_audio(db, paragraph.id, audio_path, duration_ms, sentence_timings_json)
        return True

    except Exception as e:
        logger.error("[TTS] ❌ 段落 %d 合成异常: %s", paragraph.id, e)
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


def _retry_synthesis_loop(
    db: Session,
    book_id: int,
    voice: str,
    max_concurrent: int,
    loop: asyncio.AbstractEventLoop
) -> None:
    """
    带轮次重试的合成主循环。
    第 1 轮处理 pending，后续轮次处理 failed，最多 BACKGROUND_RETRY_ROUNDS 轮重试。
    """
    # 第 1 轮：待合成段落
    paragraphs = crud.get_pending_paragraphs(db, book_id)
    if not paragraphs:
        logger.info("[TTS] 书籍 %d 没有待合成段落，跳过。", book_id)
        return

    result = loop.run_until_complete(
        _synthesize_batch_async(db, paragraphs, voice, max_concurrent)
    )
    logger.info(
        "[TTS] 第 1 轮合成完成 — 成功: %d / %d，失败: %d",
        result['completed'], result['total'], result['failed']
    )

    # 后续轮次：重试 failed 段落
    for round_num in range(2, BACKGROUND_RETRY_ROUNDS + 2):
        failed_paragraphs = db.query(models.Paragraph).filter(
            models.Paragraph.book_id == book_id,
            models.Paragraph.tts_status == 'failed'
        ).all()

        if not failed_paragraphs:
            logger.info("[TTS] 没有失败段落，停止重试。")
            break

        logger.warning(
            "[TTS] ⚠️ 第 %d 轮重试 — 共 %d 个失败段落",
            round_num, len(failed_paragraphs)
        )

        # 重置状态为 pending 以便重新合成
        for p in failed_paragraphs:
            crud.update_paragraph_status(db, p.id, "pending")
        db.commit()

        result = loop.run_until_complete(
            _synthesize_batch_async(db, failed_paragraphs, voice, max_concurrent)
        )
        logger.info(
            "[TTS] 第 %d 轮重试完成 — 成功: %d / %d，失败: %d",
            round_num, result['completed'], result['total'], result['failed']
        )

        if result['failed'] == 0:
            break

    # 记录最终统计
    from sqlalchemy import func
    status_counts = db.query(
        models.Paragraph.tts_status,
        func.count(models.Paragraph.id)
    ).filter(
        models.Paragraph.book_id == book_id
    ).group_by(models.Paragraph.tts_status).all()
    counts = {s: c for s, c in status_counts}
    logger.info(
        "[TTS] 书籍 %d 最终合成结果 — 完成: %d，失败: %d，待处理: %d",
        book_id,
        counts.get('completed', 0),
        counts.get('failed', 0),
        counts.get('pending', 0)
    )

    # 如果仍有失败段落，打印警告
    if counts.get('failed', 0) > 0:
        logger.warning(
            "[TTS] ⚠️ 书籍 %d 仍有 %d 个段落合成失败，请检查网络连接或重新运行合成。",
            book_id, counts.get('failed', 0)
        )


def synthesize_book_background(
    book_id: int,
    voice: str = "zh-CN-XiaoxiaoNeural",
    max_concurrent: int = 5
):
    """
    后台任务专用的书籍合成函数（带轮次重试）
    """
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            _retry_synthesis_loop(db, book_id, voice, max_concurrent, loop)
            crud.update_book_tts_progress(db, book_id)
        finally:
            loop.close()
    finally:
        db.close()


def synthesize_batch_background(
    book_id: int,
    paragraph_ids: List[int],
    voice: str = "zh-CN-XiaoxiaoNeural",
    max_concurrent: int = 5
):
    """
    后台任务：批量合成指定段落（带一次重试）
    """
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        paragraphs = db.query(models.Paragraph).filter(
            models.Paragraph.book_id == book_id,
            models.Paragraph.id.in_(paragraph_ids)
        ).all()

        if not paragraphs:
            return

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                _synthesize_batch_async(db, paragraphs, voice, max_concurrent)
            )
            logger.info(
                "[TTS] 批量合成第 1 轮完成 — 成功: %d / %d，失败: %d",
                result['completed'], result['total'], result['failed']
            )

            # 重试一次失败的段落
            if result['failed'] > 0:
                failed_paragraphs = db.query(models.Paragraph).filter(
                    models.Paragraph.id.in_(paragraph_ids),
                    models.Paragraph.tts_status == 'failed'
                ).all()
                if failed_paragraphs:
                    logger.warning(
                        "[TTS] ⚠️ 批量合成重试 — %d 个段落失败，开始第 2 轮",
                        len(failed_paragraphs)
                    )
                    for p in failed_paragraphs:
                        crud.update_paragraph_status(db, p.id, "pending")
                    db.commit()
                    result2 = loop.run_until_complete(
                        _synthesize_batch_async(db, failed_paragraphs, voice, max_concurrent)
                    )
                    logger.info(
                        "[TTS] 批量合成第 2 轮完成 — 成功: %d / %d，失败: %d",
                        result2['completed'], result2['total'], result2['failed']
                    )
                    if result2['failed'] > 0:
                        logger.warning(
                            "[TTS] ⚠️ 批量合成仍有 %d 个段落失败。",
                            result2['failed']
                        )

            crud.update_book_tts_progress(db, book_id)
        finally:
            loop.close()
    finally:
        db.close()
