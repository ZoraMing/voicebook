"""
解码器工厂 - 根据文件类型自动选择合适的解码器
"""
import os
from typing import Union, Type

from .base_decoder import BaseDecoder
from .models import Book, Paragraph


class DecoderFactory:
    """
    电子书解码器工厂
    
    根据文件扩展名自动选择并创建合适的解码器实例。
    
    使用示例:
        with DecoderFactory.create("book.epub") as decoder:
            paragraphs = decoder.decode_all_pages_concurrent(book_id=1)
    """
    
    # 支持的格式映射
    _decoders = {}
    
    @classmethod
    def register(cls, extension: str, decoder_class: Type[BaseDecoder]):
        """
        注册新的解码器
        
        Args:
            extension: 文件扩展名（小写，不含点号）
            decoder_class: 解码器类
        """
        cls._decoders[extension.lower()] = decoder_class
    
    @classmethod
    def create(cls, file_path: str) -> BaseDecoder:
        """
        根据文件类型创建解码器实例
        
        Args:
            file_path: 电子书文件路径
        
        Returns:
            对应格式的解码器实例
        
        Raises:
            ValueError: 如果文件格式不支持
            FileNotFoundError: 如果文件不存在
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 获取文件扩展名
        _, ext = os.path.splitext(file_path)
        ext = ext.lower().lstrip('.')
        
        # 查找对应的解码器
        if ext not in cls._decoders:
            supported = ', '.join(cls._decoders.keys()) or '无'
            raise ValueError(
                f"不支持的文件格式: .{ext}\n"
                f"支持的格式: {supported}"
            )
        
        decoder_class = cls._decoders[ext]
        return decoder_class(file_path)
    
    @classmethod
    def get_supported_formats(cls) -> list:
        """
        获取所有支持的文件格式
        
        Returns:
            支持的扩展名列表
        """
        return list(cls._decoders.keys())
    
    @classmethod
    def is_supported(cls, file_path: str) -> bool:
        """
        检查文件格式是否支持
        
        Args:
            file_path: 文件路径
        
        Returns:
            是否支持该格式
        """
        _, ext = os.path.splitext(file_path)
        ext = ext.lower().lstrip('.')
        return ext in cls._decoders


# 注册默认解码器
def _register_default_decoders():
    """注册默认支持的解码器"""
    try:
        from .pdf_decoder import PDFDecoder
        DecoderFactory.register('pdf', PDFDecoder)
    except ImportError:
        pass  # PyMuPDF 未安装
    
    try:
        from .epub_decoder import EPUBDecoder, is_epub_available
        if is_epub_available():
            DecoderFactory.register('epub', EPUBDecoder)
    except ImportError:
        pass  # ebooklib 未安装

    try:
        from .txt_decoder import TxtDecoder
        DecoderFactory.register('txt', TxtDecoder)
        DecoderFactory.register('md', TxtDecoder)
    except ImportError:
        pass


# 自动注册
_register_default_decoders()
