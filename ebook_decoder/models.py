"""
解码器数据模型定义
仅包含解码阶段需要的轻量数据类，TTS相关字段由 app/models.py ORM 层管理
"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class Paragraph:
    """
    段落数据模型 - 解码器输出的最小单元

    类比:
    - LRC歌词: [00:12.34]这是一句歌词
    - SRT字幕: 1\n00:00:12,340 --> 00:00:15,000\n这是一句字幕
    """
    # 基础字段
    book_id: int = 0                   # 所属书籍ID
    paragraph_index: int = 0           # 段落序号
    content: str = ""                  # 文本内容
    char_count: int = 0                # 字符数

    # 时间戳字段（预估值，解码阶段计算）
    estimated_duration_ms: int = 0     # 预估朗读时长(毫秒)
    start_time_ms: int = 0             # 开始时间戳(毫秒)
    end_time_ms: int = 0               # 结束时间戳(毫秒)

    def __post_init__(self):
        """自动计算字符数和预估时长"""
        if self.content:
            self.char_count = len(self.content)
            # 按每分钟300字计算预估朗读时长
            self.estimated_duration_ms = int(self.char_count / 300 * 60 * 1000)

    def to_lrc_line(self) -> str:
        """转换为LRC歌词格式"""
        minutes = self.start_time_ms // 60000
        seconds = (self.start_time_ms % 60000) // 1000
        centiseconds = (self.start_time_ms % 1000) // 10
        return f"[{minutes:02d}:{seconds:02d}.{centiseconds:02d}]{self.content}"


@dataclass
class Book:
    """书籍元数据（解码阶段使用）"""
    title: str = ""
    author: str = ""
    file_path: str = ""
    total_chapters: int = 0
    total_paragraphs: int = 0
