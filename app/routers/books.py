"""
书籍管理路由
"""
import os
import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import crud, schemas
from app.services import decoder
from app.config import get_settings

router = APIRouter(prefix="/api/books", tags=["书籍管理"])

# 上传目录（从统一配置获取）
settings = get_settings()
EBOOK_INPUT_DIR = Path(settings.EBOOK_INPUT_DIR)
EBOOK_INPUT_DIR.mkdir(exist_ok=True)


@router.post("/upload", response_model=schemas.UploadResponse)
async def upload_book(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """上传并解析电子书"""
    # 检查格式
    ext = file.filename.split('.')[-1].lower()
    if ext not in decoder.get_supported_formats():
        raise HTTPException(400, f"不支持的格式: {ext}")
    
    # 保存文件
    file_path = EBOOK_INPUT_DIR / file.filename
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # 解析电子书
    book_id, message = decoder.decode_ebook(db, str(file_path))
    
    if book_id:
        book = crud.get_book(db, book_id)
        return schemas.UploadResponse(
            success=True,
            message=message,
            book_id=book_id,
            book=schemas.Book.model_validate(book)
        )
    else:
        return schemas.UploadResponse(success=False, message=message)


@router.post("/parse/{filename}", response_model=schemas.UploadResponse)
def parse_existing_book(filename: str, db: Session = Depends(get_db)):
    """解析已存在的电子书"""
    file_path = EBOOK_INPUT_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(404, f"文件不存在: {filename}")
    
    book_id, message = decoder.decode_ebook(db, str(file_path))
    
    if book_id:
        book = crud.get_book(db, book_id)
        return schemas.UploadResponse(
            success=True,
            message=message,
            book_id=book_id,
            book=schemas.Book.model_validate(book)
        )
    else:
        return schemas.UploadResponse(success=False, message=message)


@router.get("/files")
def list_ebook_files():
    """列出 ebook_input 目录中的电子书文件"""
    # 支持的格式与解码器保持一致
    supported_exts = [f'.{fmt}' for fmt in decoder.get_supported_formats()]
    files = []
    for f in EBOOK_INPUT_DIR.iterdir():
        if f.suffix.lower() in supported_exts:
            files.append({
                "name": f.name,
                "size": f.stat().st_size,
                "format": f.suffix[1:].upper()
            })
    return {"files": files}


@router.get("", response_model=List[schemas.Book])
def get_books(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """获取书籍列表"""
    return crud.get_books(db, skip=skip, limit=limit)


@router.get("/{book_id}", response_model=schemas.BookWithChapters)
def get_book(book_id: int, db: Session = Depends(get_db)):
    """获取书籍详情"""
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(404, "书籍不存在")
    return book


@router.delete("/{book_id}")
def delete_book(book_id: int, db: Session = Depends(get_db)):
    """删除书籍"""
    # 先获取书籍信息用于文件清理
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(404, "书籍不存在")
    
    book_title = book.title
    
    # 数据库删除
    if crud.delete_book(db, book_id):
        # 使用统一接口清理文件
        from app.utils.files import cleanup_book_files
        cleanup_book_files(book_id, book_title, Path(settings.OUTPUT_DIR))
            
        return {"success": True, "message": "删除成功"}
    raise HTTPException(404, "删除失败")


@router.get("/{book_id}/chapters", response_model=List[schemas.ChapterSimple])
def get_book_chapters(book_id: int, db: Session = Depends(get_db)):
    """获取书籍的所有章节"""
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(404, "书籍不存在")
    return crud.get_book_chapters(db, book_id)


@router.get("/{book_id}/paragraphs", response_model=List[schemas.Paragraph])
def get_book_paragraphs(book_id: int, db: Session = Depends(get_db)):
    """获取书籍的所有段落"""
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(404, "书籍不存在")
    return crud.get_book_paragraphs(db, book_id)


@router.get("/chapters/{chapter_id}/paragraphs", response_model=List[schemas.Paragraph])
def get_chapter_paragraphs(chapter_id: int, db: Session = Depends(get_db)):
    """获取章节的段落"""
    chapter = crud.get_chapter(db, chapter_id)
    if not chapter:
        raise HTTPException(404, "章节不存在")
    return crud.get_chapter_paragraphs(db, chapter_id)


# ==================== 编辑接口 ====================

@router.put("/chapters/{chapter_id}", response_model=schemas.ChapterSimple)
def update_chapter(
    chapter_id: int, 
    chapter_update: schemas.ChapterUpdate, 
    db: Session = Depends(get_db)
):
    """更新章节标题"""
    chapter = crud.update_chapter(db, chapter_id, chapter_update.title)
    if not chapter:
        raise HTTPException(404, "章节不存在")
    return chapter


@router.delete("/chapters/{chapter_id}")
def delete_chapter(chapter_id: int, db: Session = Depends(get_db)):
    """删除章节及其所有段落"""
    if crud.delete_chapter(db, chapter_id):
        return {"success": True, "message": "删除成功"}
    raise HTTPException(404, "章节不存在")


@router.put("/paragraphs/{paragraph_id}", response_model=schemas.Paragraph)
def update_paragraph(
    paragraph_id: int, 
    paragraph_update: schemas.ParagraphUpdate, 
    db: Session = Depends(get_db)
):
    """
    更新段落内容
    注意：修改内容会重置 TTS 状态为 pending，需要重新合成
    """
    paragraph = crud.update_paragraph(db, paragraph_id, paragraph_update.content)
    if not paragraph:
        raise HTTPException(404, "段落不存在")
    return paragraph


@router.delete("/paragraphs/{paragraph_id}")
def delete_paragraph(paragraph_id: int, db: Session = Depends(get_db)):
    """删除段落"""
    if crud.delete_paragraph(db, paragraph_id):
        return {"success": True, "message": "删除成功"}
    raise HTTPException(404, "段落不存在")
