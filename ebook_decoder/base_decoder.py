"""
解码器抽象基类
定义所有电子书解码器的统一接口
"""
from abc import ABC, abstractmethod
from typing import List, Generator
from .models import Book, Paragraph


class BaseDecoder(ABC):
    """
    电子书解码器抽象基类
    
    所有格式的解码器（PDF、EPUB等）都必须实现这些接口，
    确保统一的调用方式。
    """
    
    def __init__(self, file_path: str):
        """
        初始化解码器
        
        Args:
            file_path: 电子书文件路径
        """
        self.file_path = file_path
    
    @abstractmethod
    def __enter__(self):
        """上下文管理器入口"""
        pass
    
    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出，清理资源"""
        pass
    
    @abstractmethod
    def get_page_count(self) -> int:
        """
        获取总页数/章节数
        
        Returns:
            页面或章节的总数
        """
        pass
    
    @abstractmethod
    def decode_page(self, page_num: int, book_id: int = 0) -> List[Paragraph]:
        """
        解码单个页面/章节
        
        Args:
            page_num: 页码或章节号（0开始）
            book_id: 书籍ID
        
        Returns:
            该页面/章节的段落列表
        """
        pass
    
    def decode_all_pages_sequential(self, book_id: int = 0) -> Generator[Paragraph, None, None]:
        """
        顺序解码所有页面（生成器模式）
        适合内存受限的情况
        
        Args:
            book_id: 书籍ID
        
        Yields:
            逐个返回段落对象
        """
        for page_num in range(self.get_page_count()):
            paragraphs = self.decode_page(page_num, book_id)
            for para in paragraphs:
                yield para
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def create_book_record(self) -> Book:
        """
        创建书籍记录对象
        
        Returns:
            包含元数据的 Book 对象
        """
        pass
    
    def get_chapter_title(self, page_num: int) -> str:
        """
        获取指定页面/章节的标题
        
        Args:
            page_num: 页面/章节索引
        
        Returns:
            章节标题，默认为 "Chapter {page_num+1}"
        """
        return f"Chapter {page_num + 1}"
    
    def split_into_paragraphs(self, text: str, min_length: int = 2) -> List[str]:
        """
        将文本分割成段落（改进版：防止小数点误断和孤立括号）
        """
        import re
        
        # 1. 预处理：修复在小数点处被物理折行的特殊情况（PDF 提取常见问题）
        # 将 "1.\n7" 恢复为 "1.7"
        text = re.sub(r'(\d+)\.\s*\n\s*(\d+)', r'\1.\2', text)
        
        # 2. 按双换行分割 (电子书通常使用双换行作为段落标志)
        paragraphs = re.split(r'\n\s*\n', text)
        
        # 3. 清理和初步过滤
        raw_result = []
        for p in paragraphs:
            cleaned = ' '.join(p.split())
            if cleaned:
                raw_result.append(cleaned)
        
        # 4. 二次处理：合并“伪段落”（如孤立的页码、括号引用、数字注脚等）
        result = []
        for p in raw_result:
            # 匹配纯括注或极短的非完整句
            is_ref_only = re.match(r'^[\(\[（【]\d+[\)\]）】]$', p)
            # 如果段落极短且不以显著标点结尾，则视为上一段的延续
            is_too_short = len(p) < 4 and not re.search(r'[。！？.!?]', p)

            if (is_ref_only or is_too_short) and result:
                result[-1] = f"{result[-1]} {p}"
            else:
                if len(p) >= min_length:
                    result.append(p)
        
        return result
