"""
电子书分段解码工具
用于将PDF、EPUB等格式的电子书按内容分段，生成类似歌词/字幕的格式
支持后续TTS有声书制作
"""

__version__ = "0.3.0"

# 核心模型
from .models import Book, Paragraph

# 解码器
from .base_decoder import BaseDecoder
from .pdf_decoder import PDFDecoder, calculate_timestamps
from .decoder_factory import DecoderFactory

# 可选：EPUB 解码器
try:
    from .epub_decoder import EPUBDecoder, is_epub_available
except ImportError:
    EPUBDecoder = None
    is_epub_available = lambda: False

# 公共 API
__all__ = [
    '__version__',
    'Book',
    'Paragraph',
    'BaseDecoder',
    'PDFDecoder',
    'EPUBDecoder',
    'DecoderFactory',
    'calculate_timestamps',
    'is_epub_available',
]

