"""
SQLAlchemy ORM 模型定义
"""
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from .database import Base


class Book(Base):
    """书籍模型"""
    __tablename__ = "books"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    author = Column(String(200), default="未知")
    file_path = Column(String(1000), nullable=False)
    total_chapters = Column(Integer, default=0)
    total_paragraphs = Column(Integer, default=0)
    total_duration_ms = Column(Integer, default=0)
    tts_progress = Column(Float, default=0.0)
    tts_voice = Column(String(100), default="zh-CN-XiaoxiaoNeural")
    created_at = Column(DateTime, default=datetime.now)
    
    # 关系
    chapters = relationship("Chapter", back_populates="book", cascade="all, delete-orphan")
    paragraphs = relationship("Paragraph", back_populates="book", cascade="all, delete-orphan")


class Chapter(Base):
    """章节模型"""
    __tablename__ = "chapters"
    
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    chapter_index = Column(Integer, nullable=False)
    title = Column(String(500), default="")
    total_paragraphs = Column(Integer, default=0)
    
    # 关系
    book = relationship("Book", back_populates="chapters")
    paragraphs = relationship("Paragraph", back_populates="chapter", cascade="all, delete-orphan")


class Paragraph(Base):
    """段落模型 - 类似字幕的数据结构"""
    __tablename__ = "paragraphs"
    
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=False)
    paragraph_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    char_count = Column(Integer, default=0)
    
    # 时间戳 (类似字幕)
    start_time_ms = Column(Integer, default=0)
    end_time_ms = Column(Integer, default=0)
    estimated_duration_ms = Column(Integer, default=0)
    
    # TTS 音频
    audio_path = Column(String(1000), nullable=True)
    audio_duration_ms = Column(Integer, nullable=True)
    tts_status = Column(String(20), default="pending")  # pending/processing/completed/failed
    tts_error = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.now)
    
    # 关系
    book = relationship("Book", back_populates="paragraphs")
    chapter = relationship("Chapter", back_populates="paragraphs")
