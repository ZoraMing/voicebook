"""
EPUB解码器 - 使用ebooklib和BeautifulSoup提取EPUB内容
支持并发处理多个章节
"""
import re
import os
from typing import List, Tuple, Generator, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import ebooklib
    from ebooklib import epub
    from bs4 import BeautifulSoup
    EPUB_AVAILABLE = True
except ImportError:
    EPUB_AVAILABLE = False

from .base_decoder import BaseDecoder
from .models import Book, Paragraph


class EPUBDecoder(BaseDecoder):
    """
    EPUB文档解码器
    将EPUB内容提取并分割成段落，类似歌词/字幕的格式
    """
    
    def __init__(self, epub_path: str):
        """
        初始化EPUB解码器
        
        Args:
            epub_path: EPUB文件路径
        
        Raises:
            ImportError: 如果ebooklib未安装
            FileNotFoundError: 如果文件不存在
        """
        if not EPUB_AVAILABLE:
            raise ImportError(
                "EPUB支持未安装。请运行: pip install ebooklib beautifulsoup4 lxml"
            )
        
        super().__init__(epub_path)
        self.book: Optional[epub.EpubBook] = None
        self.chapters: List[epub.EpubHtml] = []
        self._load_book()
    
    def _load_book(self):
        """加载EPUB文件并提取章节"""
        self.book = epub.read_epub(self.file_path, options={'ignore_ncx': True})
        
        # 提取所有文档类型的项目（章节）
        self.chapters = []
        for item in self.book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                self.chapters.append(item)
        
        # 提取元数据
        self.title = self.book.get_metadata('DC', 'title')
        self.title = self.title[0][0] if self.title else os.path.basename(self.file_path)
        
        self.author = self.book.get_metadata('DC', 'creator')
        self.author = self.author[0][0] if self.author else ''
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # ebooklib 不需要显式关闭
        self.book = None
        self.chapters = []
    
    def get_page_count(self) -> int:
        """获取章节数"""
        return len(self.chapters)
    
    def extract_chapter_text(self, chapter_index: int) -> str:
        """
        提取单个章节的纯文本内容
        
        Args:
            chapter_index: 章节索引（0开始）
        
        Returns:
            章节的纯文本内容
        """
        if chapter_index < 0 or chapter_index >= len(self.chapters):
            return ""
        
        chapter = self.chapters[chapter_index]
        content = chapter.get_content()
        
        # 使用 BeautifulSoup 解析 HTML
        soup = BeautifulSoup(content, 'lxml')
        
        # 移除脚本和样式
        for script in soup(['script', 'style', 'head', 'meta', 'link']):
            script.decompose()
        
        # 提取文本，保留段落结构
        paragraphs = []
        for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div']):
            text = element.get_text(strip=True)
            if text:
                paragraphs.append(text)
        
        # 如果没找到段落，直接获取所有文本
        if not paragraphs:
            text = soup.get_text()
            return text
        
        return '\n\n'.join(paragraphs)
    
    def decode_page(self, page_num: int, book_id: int = 0) -> List[Paragraph]:
        """
        解码单个章节，返回段落列表
        
        Args:
            page_num: 章节号（0开始）
            book_id: 书籍ID
        
        Returns:
            该章节的段落列表
        """
        text = self.extract_chapter_text(page_num)
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
    
    def decode_all_pages_concurrent(
        self, 
        book_id: int = 0, 
        max_workers: int = 4
    ) -> List[Paragraph]:
        """
        并发解码所有章节
        
        Args:
            book_id: 书籍ID
            max_workers: 最大并发线程数
        
        Returns:
            所有段落的列表，按章节号和段落序号排序
        """
        all_paragraphs = []
        chapter_count = len(self.chapters)
        
        if chapter_count == 0:
            return all_paragraphs
        
        # 使用线程池并发处理
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有章节的解码任务
            future_to_chapter = {
                executor.submit(self.decode_page, chapter_num, book_id): chapter_num
                for chapter_num in range(chapter_count)
            }
            
            # 收集结果
            chapter_results = {}
            for future in as_completed(future_to_chapter):
                chapter_num = future_to_chapter[future]
                try:
                    paragraphs = future.result()
                    chapter_results[chapter_num] = paragraphs
                except Exception as e:
                    print(f"解码第 {chapter_num + 1} 章时出错: {e}")
                    chapter_results[chapter_num] = []
        
        # 按章节顺序合并结果
        for chapter_num in range(chapter_count):
            if chapter_num in chapter_results:
                all_paragraphs.extend(chapter_results[chapter_num])
        
        return all_paragraphs
    
    def create_book_record(self) -> Book:
        """创建书籍记录对象"""
        return Book(
            file_path=self.file_path,
            title=self.title,
            author=self.author,
            total_chapters=len(self.chapters)
        )


def is_epub_available() -> bool:
    """检查EPUB支持是否可用"""
    return EPUB_AVAILABLE
