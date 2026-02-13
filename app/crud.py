"""
CRUD 数据库操作
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from . import models


# ==================== 书籍操作 ====================

def create_book(db: Session, title: str, author: str, file_path: str) -> models.Book:
    """创建书籍"""
    book = models.Book(title=title, author=author, file_path=file_path)
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def get_book(db: Session, book_id: int) -> Optional[models.Book]:
    """获取书籍"""
    return db.query(models.Book).filter(models.Book.id == book_id).first()


def get_books(db: Session, skip: int = 0, limit: int = 100) -> List[models.Book]:
    """获取书籍列表"""
    return db.query(models.Book).offset(skip).limit(limit).all()


def delete_book(db: Session, book_id: int) -> bool:
    """删除书籍"""
    book = get_book(db, book_id)
    if book:
        db.delete(book)
        db.commit()
        return True
    return False


def update_book_stats(db: Session, book_id: int):
    """更新书籍统计"""
    book = get_book(db, book_id)
    if book:
        book.total_chapters = db.query(models.Chapter).filter(
            models.Chapter.book_id == book_id
        ).count()
        book.total_paragraphs = db.query(models.Paragraph).filter(
            models.Paragraph.book_id == book_id
        ).count()
        book.total_duration_ms = db.query(func.sum(models.Paragraph.estimated_duration_ms)).filter(
            models.Paragraph.book_id == book_id
        ).scalar() or 0
        db.commit()


def update_book_tts_progress(db: Session, book_id: int):
    """更新 TTS 进度"""
    book = get_book(db, book_id)
    if book:
        total = db.query(models.Paragraph).filter(
            models.Paragraph.book_id == book_id
        ).count()
        completed = db.query(models.Paragraph).filter(
            models.Paragraph.book_id == book_id,
            models.Paragraph.tts_status == "completed"
        ).count()
        book.tts_progress = (completed / total * 100) if total > 0 else 0
        db.commit()


# ==================== 章节操作 ====================

def create_chapter(db: Session, book_id: int, chapter_index: int, title: str = "") -> models.Chapter:
    """创建章节"""
    chapter = models.Chapter(book_id=book_id, chapter_index=chapter_index, title=title)
    db.add(chapter)
    db.commit()
    db.refresh(chapter)
    return chapter


def get_chapter(db: Session, chapter_id: int) -> Optional[models.Chapter]:
    """获取章节"""
    return db.query(models.Chapter).filter(models.Chapter.id == chapter_id).first()


def get_book_chapters(db: Session, book_id: int) -> List[models.Chapter]:
    """获取书籍的所有章节"""
    return db.query(models.Chapter).filter(
        models.Chapter.book_id == book_id
    ).order_by(models.Chapter.chapter_index).all()


def update_chapter_stats(db: Session, chapter_id: int):
    """更新章节统计"""
    chapter = get_chapter(db, chapter_id)
    if chapter:
        chapter.total_paragraphs = db.query(models.Paragraph).filter(
            models.Paragraph.chapter_id == chapter_id
        ).count()
        db.commit()


# ==================== 段落操作 ====================

def create_paragraph(
    db: Session, 
    book_id: int, 
    chapter_id: int, 
    paragraph_index: int, 
    content: str,
    start_time_ms: int = 0,
    end_time_ms: int = 0
) -> models.Paragraph:
    """创建段落"""
    char_count = len(content)
    estimated_duration_ms = int(char_count / 300 * 60 * 1000)  # 每分钟300字
    
    paragraph = models.Paragraph(
        book_id=book_id,
        chapter_id=chapter_id,
        paragraph_index=paragraph_index,
        content=content,
        char_count=char_count,
        estimated_duration_ms=estimated_duration_ms,
        start_time_ms=start_time_ms,
        end_time_ms=end_time_ms
    )
    db.add(paragraph)
    db.commit()
    db.refresh(paragraph)
    return paragraph


def create_paragraphs_batch(db: Session, paragraphs_data: List[dict]) -> int:
    """批量创建段落"""
    paragraphs = []
    for data in paragraphs_data:
        char_count = len(data['content'])
        estimated_duration_ms = int(char_count / 300 * 60 * 1000)
        
        paragraph = models.Paragraph(
            book_id=data['book_id'],
            chapter_id=data['chapter_id'],
            paragraph_index=data['paragraph_index'],
            content=data['content'],
            char_count=char_count,
            estimated_duration_ms=estimated_duration_ms,
            start_time_ms=data.get('start_time_ms', 0),
            end_time_ms=data.get('end_time_ms', 0)
        )
        paragraphs.append(paragraph)
    
    db.add_all(paragraphs)
    db.commit()
    return len(paragraphs)


def get_paragraph(db: Session, paragraph_id: int) -> Optional[models.Paragraph]:
    """获取单个段落"""
    return db.query(models.Paragraph).filter(models.Paragraph.id == paragraph_id).first()


def get_chapter_paragraphs(db: Session, chapter_id: int) -> List[models.Paragraph]:
    """获取章节的所有段落"""
    return db.query(models.Paragraph).filter(
        models.Paragraph.chapter_id == chapter_id
    ).order_by(models.Paragraph.paragraph_index).all()


def get_book_paragraphs(db: Session, book_id: int) -> List[models.Paragraph]:
    """获取书籍的所有段落"""
    return db.query(models.Paragraph).filter(
        models.Paragraph.book_id == book_id
    ).order_by(models.Paragraph.chapter_id, models.Paragraph.paragraph_index).all()


def get_pending_paragraphs(db: Session, book_id: int) -> List[models.Paragraph]:
    """获取待合成的段落"""
    return db.query(models.Paragraph).filter(
        models.Paragraph.book_id == book_id,
        models.Paragraph.tts_status == "pending"
    ).order_by(models.Paragraph.id).all()


def update_paragraph_audio(
    db: Session, 
    paragraph_id: int, 
    audio_path: str, 
    audio_duration_ms: int,
    sentence_timings: str = None,
    status: str = "completed"
):
    """更新段落音频信息"""
    paragraph = db.query(models.Paragraph).filter(
        models.Paragraph.id == paragraph_id
    ).first()
    if paragraph:
        paragraph.audio_path = audio_path
        paragraph.audio_duration_ms = audio_duration_ms
        if sentence_timings is not None:
            paragraph.sentence_timings = sentence_timings
        paragraph.tts_status = status
        db.commit()


def update_paragraph_status(db: Session, paragraph_id: int, status: str, error: str = None):
    """更新段落 TTS 状态"""
    paragraph = db.query(models.Paragraph).filter(
        models.Paragraph.id == paragraph_id
    ).first()
    if paragraph:
        paragraph.tts_status = status
        paragraph.tts_error = error
        db.commit()


def update_chapter(db: Session, chapter_id: int, title: str) -> Optional[models.Chapter]:
    """更新章节标题"""
    chapter = get_chapter(db, chapter_id)
    if chapter:
        chapter.title = title
        db.commit()
    return chapter


def update_paragraph(db: Session, paragraph_id: int, content: str) -> Optional[models.Paragraph]:
    """更新段落内容并重置 TTS 状态"""
    paragraph = db.query(models.Paragraph).filter(models.Paragraph.id == paragraph_id).first()
    if paragraph:
        paragraph.content = content
        
        # 重置 TTS 状态
        paragraph.tts_status = "pending"
        paragraph.audio_path = None
        paragraph.audio_duration_ms = None
        paragraph.sentence_timings = None
        paragraph.tts_error = None
        
        # 重新计算字数和估算时长
        paragraph.char_count = len(content)
        paragraph.estimated_duration_ms = int(len(content) / 300 * 60 * 1000)
        
        db.commit()
    return paragraph


def delete_chapter(db: Session, chapter_id: int) -> bool:
    """删除章节及其关联段落"""
    chapter = get_chapter(db, chapter_id)
    if chapter:
        db.delete(chapter)
        db.commit()
        return True
    return False


def delete_paragraph(db: Session, paragraph_id: int) -> bool:
    """删除段落"""
    paragraph = db.query(models.Paragraph).filter(models.Paragraph.id == paragraph_id).first()
    if paragraph:
        # 更新章节统计
        chapter_id = paragraph.chapter_id
        db.delete(paragraph)
        db.commit()
        
        # 重新统计章节段落数
        update_chapter_stats(db, chapter_id)
        return True
    return False
