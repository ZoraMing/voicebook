"""
电子书解码服务
使用 ebook_decoder 模块解析电子书，统一通过基类接口调用
"""
import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple
from sqlalchemy.orm import Session

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ebook_decoder import DecoderFactory
from app import crud
from app.config import get_settings
from app.services.llm_service import LLMClient

settings = get_settings()


def decode_ebook(db: Session, file_path: str) -> Tuple[int, str]:
    """
    解码电子书并存入数据库

    Args:
        db: 数据库会话
        file_path: 电子书文件路径

    Returns:
        (book_id, message) 元组
    """
    if not os.path.exists(file_path):
        return None, f"文件不存在: {file_path}"

    try:
        with DecoderFactory.create(file_path) as decoder:
            # 使用基类统一接口获取元数据
            book_record = decoder.create_book_record()
            title = book_record.title or Path(file_path).stem
            author = book_record.author or '未知'

            # 创建书籍记录
            book = crud.create_book(db, title=title, author=author, file_path=file_path)

            # 获取章节数据
            if settings.ENABLE_SMART_PARSING:
                print("正在使用 LLM 进行智能分章...")
                chapters_data = _smart_extract_chapters(decoder)
            else:
                chapters_data = _extract_chapters(decoder)

            # 创建章节和段落
            total_time_ms = 0
            for chapter_index, chapter_data in enumerate(chapters_data):
                # 创建章节
                chapter = crud.create_chapter(
                    db,
                    book_id=book.id,
                    chapter_index=chapter_index + 1,
                    title=chapter_data.get('title', f"章节 {chapter_index + 1}")
                )

                # 创建段落
                paragraphs_batch = []
                for para_index, content in enumerate(chapter_data['paragraphs']):
                    if content.strip():
                        char_count = len(content)
                        duration_ms = int(char_count / 300 * 60 * 1000)

                        paragraphs_batch.append({
                            'book_id': book.id,
                            'chapter_id': chapter.id,
                            'paragraph_index': para_index + 1,
                            'content': content.strip(),
                            'start_time_ms': total_time_ms,
                            'end_time_ms': total_time_ms + duration_ms
                        })
                        total_time_ms += duration_ms

                if paragraphs_batch:
                    crud.create_paragraphs_batch(db, paragraphs_batch)

                # 更新章节统计
                crud.update_chapter_stats(db, chapter.id)

            # 更新书籍统计
            crud.update_book_stats(db, book.id)

            # 刷新获取最新统计
            db.refresh(book)

            return book.id, f"解析完成: {book.total_chapters} 章, {book.total_paragraphs} 段落"

    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"解析失败: {str(e)}"


def _extract_chapters(decoder) -> List[Dict]:
    """
    从解码器提取章节数据（统一使用基类接口）

    所有解码器（PDF/EPUB/TXT/MD）都实现了相同的基类方法:
    - get_page_count()
    - decode_page(page_num, book_id)
    - get_chapter_title(page_num)
    """
    chapters = []
    page_count = decoder.get_page_count()

    for i in range(page_count):
        paras = decoder.decode_page(i, book_id=0)
        if paras:
            title = decoder.get_chapter_title(i)
            chapters.append({
                'title': title,
                'paragraphs': [p.content for p in paras]
            })

    return chapters


def _smart_extract_chapters(decoder) -> List[Dict]:
    """
    智能提取章节: 提取所有文本 -> 切片 -> LLM 清洗和重组
    """
    # 使用基类接口提取所有原始文本
    all_text = ""
    page_count = decoder.get_page_count()

    for i in range(page_count):
        paras = decoder.decode_page(i, book_id=0)
        if paras:
            page_text = "\n".join(p.content for p in paras)
            all_text += page_text + "\n\n"

    # 切片（按固定长度，LLM 可处理 ~15000 字符的块）
    chunk_size = 15000
    chunks = [all_text[i:i+chunk_size] for i in range(0, len(all_text), chunk_size)]

    llm_client = LLMClient()
    final_chapters = []

    for i, chunk in enumerate(chunks):
        print(f"正在处理第 {i+1}/{len(chunks)} 个文本块...")
        processed_chapters = llm_client.clean_and_reshape_text(chunk)

        for item in processed_chapters:
            final_chapters.append({
                'title': item.get('title', f"智能分章 {len(final_chapters)+1}"),
                'paragraphs': item.get('content', '').split('\n\n')
            })

    return final_chapters


def get_supported_formats() -> List[str]:
    """获取支持的文件格式"""
    return DecoderFactory.get_supported_formats()
