"""
PDF解码器 - 使用PyMuPDF提取PDF内容
支持并发处理多个页面
"""
import re
import fitz  # PyMuPDF
import os
from typing import List, Tuple, Generator
from concurrent.futures import ThreadPoolExecutor, as_completed
from .models import Book, Paragraph
from .base_decoder import BaseDecoder


class PDFDecoder(BaseDecoder):
    """
    PDF文档解码器
    将PDF内容提取并分割成段落，类似歌词/字幕的格式
    """
    
    def __init__(self, pdf_path: str):
        super().__init__(pdf_path)
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.title = self.doc.metadata.get('title', '') or os.path.basename(pdf_path)
        self.author = self.doc.metadata.get('author', '')
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.doc.close()
    
    def get_page_count(self) -> int:
        """获取总页数"""
        return len(self.doc)
    
    def extract_page_text(self, page_num: int) -> str:
        """提取单页文本"""
        page = self.doc[page_num]
        return page.get_text("text")
    
    
    def decode_page(self, page_num: int, book_id: int = 0) -> List[Paragraph]:
        """
        解码单个页面，返回段落列表
        
        Args:
            page_num: 页码（0开始）
            book_id: 书籍ID
        
        Returns:
            该页面的段落列表
        """
        text = self.extract_page_text(page_num)
        raw_paragraphs = self.split_into_paragraphs(text)
        
        paragraphs = []
        for idx, content in enumerate(raw_paragraphs):
            para = Paragraph(
                book_id=book_id,
                paragraph_index=idx + 1,
                content=content
            )
            paragraphs.append(para)
        
        return paragraphs
    
    def decode_all_pages_sequential(self, book_id: int = 0) -> Generator[Paragraph, None, None]:
        """
        顺序解码所有页面（生成器模式）
        适合内存受限的情况
        """
        for page_num in range(len(self.doc)):
            paragraphs = self.decode_page(page_num, book_id)
            for para in paragraphs:
                yield para
    
    def decode_all_pages_concurrent(
        self, 
        book_id: int = 0, 
        max_workers: int = 4
    ) -> List[Paragraph]:
        """
        并发解码所有页面
        
        Args:
            book_id: 书籍ID
            max_workers: 最大并发线程数
        
        Returns:
            所有段落的列表，按页码和段落序号排序
        """
        all_paragraphs = []
        page_count = len(self.doc)
        
        # 使用线程池并发处理
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有页面的解码任务
            future_to_page = {
                executor.submit(self.decode_page, page_num, book_id): page_num
                for page_num in range(page_count)
            }
            
            # 收集结果
            page_results = {}
            for future in as_completed(future_to_page):
                page_num = future_to_page[future]
                try:
                    paragraphs = future.result()
                    page_results[page_num] = paragraphs
                except Exception as e:
                    print(f"解码第 {page_num + 1} 页时出错: {e}")
                    page_results[page_num] = []
        
        # 按页码顺序合并结果
        for page_num in range(page_count):
            if page_num in page_results:
                all_paragraphs.extend(page_results[page_num])
        
        return all_paragraphs
    
    def create_book_record(self) -> Book:
        """创建书籍记录对象"""
        return Book(
            file_path=self.pdf_path,
            title=self.title,
            author=self.author,
            total_chapters=len(self.doc)
        )


def calculate_timestamps(paragraphs: List[Paragraph]) -> List[Paragraph]:
    """
    计算每个段落的开始和结束时间戳
    类似歌词/字幕的时间轴计算
    
    Args:
        paragraphs: 段落列表
    
    Returns:
        添加了时间戳的段落列表
    """
    current_time_ms = 0
    
    for para in paragraphs:
        para.start_time_ms = current_time_ms
        para.end_time_ms = current_time_ms + para.estimated_duration_ms
        current_time_ms = para.end_time_ms
    
    return paragraphs
