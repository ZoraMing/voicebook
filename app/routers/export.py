"""
有声书导出路由
"""
import os
import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app import crud, schemas
from app.services import audiobook_exporter

router = APIRouter(prefix="/api", tags=["导出"])


@router.post("/books/{book_id}/export", response_model=schemas.ExportResponse)
def export_book(
    book_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    导出书籍为 WAV + LRC 文件（后台任务）
    
    将已合成的段落音频按章节分组合并为 WAV，并生成 LRC 歌词。
    短章节自动合并，保持每段 ~40 分钟。
    """
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(404, "书籍不存在")
    
    # 检查是否有已完成的音频
    from sqlalchemy import func
    from app import models
    
    completed_count = db.query(func.count(models.Paragraph.id)).filter(
        models.Paragraph.book_id == book_id,
        models.Paragraph.tts_status == "completed"
    ).scalar()
    
    if completed_count == 0:
        return schemas.ExportResponse(
            success=False,
            message="没有已合成的音频，请先执行 TTS 合成"
        )
    
    # 添加后台导出任务
    background_tasks.add_task(
        audiobook_exporter.export_book_background,
        book_id=book_id
    )
    
    return schemas.ExportResponse(
        success=True,
        message=f"已开始后台导出任务，共 {completed_count} 个已合成段落。"
                f"导出完成后可在 output/{book.title}/ 目录查看结果。"
    )


@router.post("/books/{book_id}/export/sync")
def export_book_sync(
    book_id: int,
    db: Session = Depends(get_db)
):
    """
    同步导出书籍为 WAV + LRC 文件（等待完成）
    
    适用于小书籍或调试。大书籍请使用异步 /export 端点。
    """
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(404, "书籍不存在")
    
    result = audiobook_exporter.export_book(db, book_id)
    return result


@router.get("/books/{book_id}/export/download")
def download_export(book_id: int, db: Session = Depends(get_db)):
    """
    下载导出的文件（ZIP 压缩包）
    """
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(404, "书籍不存在")
    
    book_dir = audiobook_exporter.get_export_dir(book.title)
    
    if not book_dir.exists():
        raise HTTPException(404, "导出文件不存在，请先执行导出")
    
    # 生成 ZIP 文件
    zip_path = audiobook_exporter.create_zip_archive(book.title)
    
    if not zip_path:
         raise HTTPException(500, "创建压缩包失败")
    
    return FileResponse(
        str(zip_path),
        media_type="application/zip",
        filename=f"{book.title}.zip"
    )


@router.get("/books/{book_id}/export/files")
def get_export_files(book_id: int, db: Session = Depends(get_db)):
    """
    获取导出文件列表 (用于在线播放)
    """
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(404, "书籍不存在")
        
    book_dir = audiobook_exporter.get_export_dir(book.title)
    safe_title = audiobook_exporter._sanitize_filename(book.title)
    
    if not book_dir.exists():
        return {"files": []}
    
    files = []
    # 遍历目录下的子文件夹（每个段落一个文件夹）
    if book_dir.exists():
        for item in sorted(os.listdir(book_dir)):
            item_path = book_dir / item
            if item_path.is_dir():
                # 检查子目录内的文件: {folder_name}.wav
                wav_name = f"{item}.wav"
                lrc_name = f"{item}.lrc"
                
                wav_file = item_path / wav_name
                lrc_file = item_path / lrc_name
                
                if wav_file.exists():
                    group_data = {
                        "name": item,
                        "wav": f"/outputs/{safe_title}/{item}/{wav_name}",
                        "lrc": None
                    }
                    
                    if lrc_file.exists():
                        group_data["lrc"] = f"/outputs/{safe_title}/{item}/{lrc_name}"
                    
                    files.append(group_data)
    
    return {"files": files}
