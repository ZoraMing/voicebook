"""
TTS 语音合成路由
"""
import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import crud, schemas
from app.services import tts

router = APIRouter(prefix="/api", tags=["语音合成"])


@router.get("/voices", response_model=List[schemas.VoiceInfo])
def get_voices():
    """获取可用语音列表"""
    return [schemas.VoiceInfo(**v) for v in tts.VOICES]


@router.post("/books/{book_id}/synthesize", response_model=schemas.SynthesizeResponse)
def synthesize_book(
    book_id: int,
    background_tasks: BackgroundTasks,
    voice: str = "zh-CN-XiaoxiaoNeural",
    max_concurrent: int = 5,
    db: Session = Depends(get_db)
):
    """
    合成整本书（后台任务模式）
    
    - 请求会立即返回，合成任务在后台执行
    - 使用 /books/{book_id}/progress 端点查询进度
    - max_concurrent: 并发数（默认5，可调整以加快速度）
    """
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(404, "书籍不存在")
    
    # 获取待处理段落数量
    pending_count = len(crud.get_pending_paragraphs(db, book_id))
    
    if pending_count == 0:
        return schemas.SynthesizeResponse(
            success=True,
            message="没有待合成的段落",
            total=0,
            completed=0,
            failed=0
        )
    
    # 添加后台任务
    background_tasks.add_task(
        tts.synthesize_book_background,
        book_id=book_id,
        voice=voice,
        max_concurrent=max_concurrent
    )
    return schemas.SynthesizeResponse(
        success=True,
        message=f"已开始后台合成任务，共 {pending_count} 个段落，并发数 {max_concurrent}。请使用 /progress 端点查询进度。",
        total=pending_count,
        completed=0,
        failed=0
    )


@router.post("/books/{book_id}/paragraphs/{paragraph_id}/synthesize", response_model=bool)
async def synthesize_paragraph(
    book_id: int,
    paragraph_id: int,
    voice: str = "zh-CN-XiaoxiaoNeural",
    db: Session = Depends(get_db)
):
    """
    合成单个段落（同步/异步等待）
    """
    paragraph = crud.get_paragraph(db, paragraph_id)
    if not paragraph:
        raise HTTPException(404, "段落不存在")
    
    if paragraph.book_id != book_id:
        raise HTTPException(400, "段落不属于该书籍")

    # 调用 service 层的合成函数
    success = await tts.synthesize_paragraph(db, paragraph, voice)
    
    if not success:
         raise HTTPException(500, "合成失败")
         
    return True


@router.post("/books/{book_id}/chapters/{chapter_id}/synthesize", response_model=schemas.SynthesizeResponse)
def synthesize_chapter(
    book_id: int,
    chapter_id: int,
    background_tasks: BackgroundTasks,
    voice: str = "zh-CN-XiaoxiaoNeural",
    db: Session = Depends(get_db)
):
    """
    合成整章节（后台任务模式）
    """
    chapter = crud.get_chapter(db, chapter_id)
    if not chapter or chapter.book_id != book_id:
        raise HTTPException(404, "章节不存在或不属于该书籍")
    
    # 获取该章节待处理段落
    from app import models
    pending_paragraphs = db.query(models.Paragraph).filter(
        models.Paragraph.chapter_id == chapter_id,
        models.Paragraph.tts_status == "pending"
    ).all()
    
    paragraph_ids = [p.id for p in pending_paragraphs]
    
    if not paragraph_ids:
        return schemas.SynthesizeResponse(
            success=True,
            message="该章节没有待合成的段落",
            total=0,
            completed=0,
            failed=0
        )
    
    background_tasks.add_task(
        tts.synthesize_batch_background,
        book_id=book_id,
        paragraph_ids=paragraph_ids,
        voice=voice
    )
    
    return schemas.SynthesizeResponse(
        success=True,
        message=f"已开始章节合成任务，共 {len(paragraph_ids)} 个段落。",
        total=len(paragraph_ids),
        completed=0,
        failed=0
    )


@router.post("/books/{book_id}/synthesize-batch", response_model=schemas.SynthesizeResponse)
def synthesize_batch(
    book_id: int,
    request: schemas.BatchSynthesizeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    批量合成指定段落（后台任务模式）
    """
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(404, "书籍不存在")
    
    # 过滤掉不属于该书的段落（提高安全性）
    # 可以在 background task 里做，也可以在这里简单校验
    
    background_tasks.add_task(
        tts.synthesize_batch_background,
        book_id=book_id,
        paragraph_ids=request.paragraph_ids,
        voice=request.voice
    )
    
    return schemas.SynthesizeResponse(
        success=True,
        message=f"已开始批量合成任务，共 {len(request.paragraph_ids)} 个段落。",
        total=len(request.paragraph_ids),
        completed=0,
        failed=0
    )


@router.get("/books/{book_id}/progress")
def get_synthesis_progress(book_id: int, db: Session = Depends(get_db)):
    """
    获取合成进度
    
    返回各状态的段落数量：
    - pending: 等待处理
    - processing: 正在处理
    - completed: 已完成
    - failed: 失败
    """
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(404, "书籍不存在")
    
    # 统计各状态的段落数量
    from sqlalchemy import func
    from app import models
    
    status_counts = db.query(
        models.Paragraph.tts_status,
        func.count(models.Paragraph.id)
    ).filter(
        models.Paragraph.book_id == book_id
    ).group_by(models.Paragraph.tts_status).all()
    
    # 转换为字典
    counts = {status: count for status, count in status_counts}
    
    pending = counts.get("pending", 0)
    processing = counts.get("processing", 0)
    completed = counts.get("completed", 0)
    failed = counts.get("failed", 0)
    total = pending + processing + completed + failed
    
    # 计算进度百分比
    progress = (completed / total * 100) if total > 0 else 0
    
    # 判断整体状态
    if processing > 0:
        status = "synthesizing"
    elif pending > 0 and completed == 0:
        status = "idle"
    elif pending == 0 and failed == 0:
        status = "completed"
    elif pending == 0 and failed > 0:
        status = "completed_with_errors"
    else:
        status = "in_progress"
    
    return {
        "book_id": book_id,
        "status": status,
        "progress": round(progress, 1),
        "total_paragraphs": total,
        "pending": pending,
        "processing": processing,
        "completed": completed,
        "failed": failed
    }


@router.get("/audio/{book_id}/{paragraph_id}")
def get_audio(book_id: int, paragraph_id: int):
    """获取段落音频"""
    audio_path = tts.get_audio_path(book_id, paragraph_id)
    
    if not os.path.exists(audio_path):
        raise HTTPException(404, "音频文件不存在")
    
    return FileResponse(
        audio_path,
        media_type="audio/mpeg",
        headers={"Accept-Ranges": "bytes"}
    )
