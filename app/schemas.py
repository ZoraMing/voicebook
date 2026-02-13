"""
Pydantic 模式定义
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# 段落模式
class ParagraphBase(BaseModel):
    content: str
    paragraph_index: int


class ParagraphCreate(ParagraphBase):
    chapter_id: int
    book_id: int


class Paragraph(ParagraphBase):
    id: int
    book_id: int
    chapter_id: int
    char_count: int
    start_time_ms: int
    end_time_ms: int
    audio_path: Optional[str] = None
    audio_duration_ms: Optional[int] = None
    tts_status: str = "pending"
    
    class Config:
        from_attributes = True


class ParagraphUpdate(BaseModel):
    content: str


# 章节模式
class ChapterBase(BaseModel):
    title: str
    chapter_index: int


class ChapterCreate(ChapterBase):
    book_id: int


class ChapterUpdate(BaseModel):
    title: str


class Chapter(ChapterBase):
    id: int
    book_id: int
    total_paragraphs: int
    paragraphs: List[Paragraph] = []
    
    class Config:
        from_attributes = True


class ChapterSimple(ChapterBase):
    """简化的章节信息(不含段落)"""
    id: int
    book_id: int
    total_paragraphs: int
    
    class Config:
        from_attributes = True


# 书籍模式
class BookBase(BaseModel):
    title: str
    author: str = "未知"


class BookCreate(BookBase):
    file_path: str


class Book(BookBase):
    id: int
    file_path: str
    total_chapters: int
    total_paragraphs: int
    total_duration_ms: int
    tts_progress: float
    tts_voice: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class BookWithChapters(Book):
    """包含章节的书籍信息"""
    chapters: List[ChapterSimple] = []


# API 响应模式
class UploadResponse(BaseModel):
    success: bool
    message: str
    book_id: Optional[int] = None
    book: Optional[Book] = None


class SynthesizeResponse(BaseModel):
    success: bool
    message: str
    total: int = 0
    completed: int = 0
    failed: int = 0


class VoiceInfo(BaseModel):
    id: str
    name: str
    voice: str
    gender: str


class BatchSynthesizeRequest(BaseModel):
    paragraph_ids: List[int]
    voice: str = "zh-CN-XiaoxiaoNeural"


class ExportResponse(BaseModel):
    """导出响应"""
    success: bool
    message: str
    output_dir: Optional[str] = None
    total_segments: int = 0
    success_count: int = 0
    fail_count: int = 0
