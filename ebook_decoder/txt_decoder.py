
"""
TXT/Markdown 文件解码器
支持.txt和.md格式，按标题或正则分章
"""
import os
import re
from typing import List, Generator, Tuple
from .base_decoder import BaseDecoder
from .models import Book, Paragraph

class TxtDecoder(BaseDecoder):
    """
    纯文本和 Markdown 解码器
    
    分章策略:
    1. Markdown: 按 # (一级标题) 或 ## (二级标题) 分章
    2. TXT: 按正则表达式匹配 "第x章" 等标题
    3. 如果没有匹配到章节，则视为单章
    """
    
    def __init__(self, file_path: str):
        super().__init__(file_path)
        self.content = ""
        self.chapters = []  # [(title, content), ...]
    
    def __enter__(self):
        # 尝试多种编码读取文件
        encodings = ['utf-8', 'gbk', 'gb18030', 'utf-16']
        for enc in encodings:
            try:
                with open(self.file_path, 'r', encoding=enc) as f:
                    self.content = f.read()
                break
            except UnicodeDecodeError:
                continue
        else:
            raise ValueError(f"无法识别文件编码: {self.file_path}")
            
        self._parse_chapters()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.content = ""
        self.chapters = []
    
    def _parse_chapters(self):
        """解析章节结构"""
        filename = os.path.basename(self.file_path)
        is_markdown = filename.lower().endswith('.md')
        
        if is_markdown:
            self._parse_markdown()
        else:
            self._parse_txt()
            
        # 如果未能解析出章节，全书作为一章
        if not self.chapters:
            title = os.path.splitext(filename)[0]
            self.chapters = [(title, self.content)]
            
    def _parse_markdown(self):
        """Markdown 分章: 按一级标题 #"""
        lines = self.content.splitlines()
        current_title = "前言"
        current_lines = []
        
        for line in lines:
            # 匹配 # 标题 (一级或二级)
            if re.match(r'^#{1,2}\s+', line):
                # 保存前一章
                if current_lines:
                    self.chapters.append((current_title, '\n'.join(current_lines)))
                
                # 新章节
                current_title = re.sub(r'^#{1,2}\s+', '', line).strip()
                current_lines = []
            else:
                current_lines.append(line)
                
        # 保存最后一章
        if current_lines:
            self.chapters.append((current_title, '\n'.join(current_lines)))

    def _parse_txt(self):
        """TXT 分章: 正则匹配 第X章"""
        # 常见章节标题正则
        # 第[一二三四五六七八九十百千0-9]+[章节卷集部篇回]
        pattern = r'^\s*第[一二三四五六七八九十百千0-9]+[章节卷集部篇回].*'
        
        lines = self.content.splitlines()
        current_title = "开始"
        current_lines = []
        found_chapters = False
        
        for line in lines:
            if re.match(pattern, line):
                found_chapters = True
                if current_lines:
                    self.chapters.append((current_title, '\n'.join(current_lines)))
                
                current_title = line.strip()
                current_lines = []
            else:
                current_lines.append(line)
        
        if current_lines:
            self.chapters.append((current_title, '\n'.join(current_lines)))
            
        # 如果甚至没有找到一个章节标题，清空 chapters 让 fallback 处理
        if not found_chapters:
            self.chapters = []

    def get_page_count(self) -> int:
        """返回章节数"""
        return len(self.chapters)
    
    def decode_page(self, page_num: int, book_id: int = 0) -> List[Paragraph]:
        """解码单个章节"""
        if page_num < 0 or page_num >= len(self.chapters):
            return []
            
        title, content = self.chapters[page_num]
        
        # 将内容分为段落
        text_segments = self.split_into_paragraphs(content)
        
        paragraphs = []
        for i, text in enumerate(text_segments):
            para = Paragraph(
                book_id=book_id,
                # chapter_id=0, # ebook_decoder.models.Paragraph 不包含 chapter_id
                paragraph_index=i,
                content=text,
                char_count=len(text)
            )
            # 在返回前，我们无法知道 chapter_id，所以这里只能作为临时对象
            paragraphs.append(para)
            
        return paragraphs
        
    def decode_all_pages_concurrent(self, book_id: int = 0, max_workers: int = 1) -> List[Paragraph]:
        """TXT 解析速度很快，不需要并发"""
        all_paragraphs = []
        # 注意：这里 BaseDecoder 接口定义有些局限，通常是由外部调用者创建 Chapter 对象
        # 然后再调用 decode_page。但在 Decoder 内部我们已经分好了章节。
        # 这里我们模拟按页（章）返回。
        
        # 实际上 decode_ebook 逻辑是：
        # 1. get_page_count
        # 2. 循环 create_chapter
        # 3. decode_page -> create_paragraphs
        
        # 所以这里的实现是正确的，只需按 page_num 返回段落即可
        for i in range(self.get_page_count()):
            all_paragraphs.extend(self.decode_page(i, book_id))
            
        return all_paragraphs

    def create_book_record(self) -> Book:
        filename = os.path.basename(self.file_path)
        title = os.path.splitext(filename)[0]
        return Book(
            title=title,
            author="Unknown", # TXT 很难自动提取作者
            file_path=self.file_path,
            total_chapters=len(self.chapters)
        )
    
    def get_chapter_title(self, page_num: int) -> str:
        """获取章节标题（扩展接口）"""
        if 0 <= page_num < len(self.chapters):
            return self.chapters[page_num][0]
        return f"Chapter {page_num+1}"
