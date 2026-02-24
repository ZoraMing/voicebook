import logging
import shutil
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session

from app import models, crud
from app.config import get_settings
from app.utils.text import split_to_sentences, sanitize_filename
from app.utils.audio import merge_audio_to_wav, merge_audio, tag_mp3_metadata
from app.utils.files import get_export_dir, get_zip_path, create_zip_archive, cleanup_book_files

logger = logging.getLogger(__name__)

settings = get_settings()

# 导出根目录（从统一配置获取）
OUTPUT_DIR = Path(settings.OUTPUT_DIR)
OUTPUT_DIR.mkdir(exist_ok=True)

# 时长阈值（毫秒）
MIN_DURATION_MS = 25 * 60 * 1000   # 25 分钟
TARGET_DURATION_MS = 40 * 60 * 1000  # 40 分钟


def group_chapters_by_duration(
    db: Session,
    book_id: int
) -> List[Dict]:
    """
    按时长分组章节，目标 ~40 分钟，最低 25 分钟。
    
    返回:
        [
            {
                'chapter_indices': [1, 2],      # 章节编号列表
                'chapters': [chapter1, chapter2], # 章节对象列表
                'paragraphs': [...],             # 所有段落
                'total_duration_ms': 2400000     # 总时长(毫秒)
            },
            ...
        ]
    """
    chapters = crud.get_book_chapters(db, book_id)
    if not chapters:
        return []
    
    groups = []
    current_group = {
        'chapter_indices': [],
        'chapters': [],
        'paragraphs': [],
        'total_duration_ms': 0
    }
    
    for chapter in chapters:
        # 获取此章节的所有段落
        paragraphs = crud.get_chapter_paragraphs(db, chapter.id)
        if not paragraphs:
            continue
        
        # 计算章节时长：优先用实际音频时长，否则用预估时长
        chapter_duration = sum(
            (p.audio_duration_ms or p.estimated_duration_ms or 0)
            for p in paragraphs
        )
        
        # 添加到当前分组
        current_group['chapter_indices'].append(chapter.chapter_index)
        current_group['chapters'].append(chapter)
        current_group['paragraphs'].extend(paragraphs)
        current_group['total_duration_ms'] += chapter_duration
        
        # 判断是否需要切分
        if current_group['total_duration_ms'] >= MIN_DURATION_MS:
            groups.append(current_group)
            current_group = {
                'chapter_indices': [],
                'chapters': [],
                'paragraphs': [],
                'total_duration_ms': 0
            }
    
    # 处理剩余部分
    if current_group['paragraphs']:
        if groups and current_group['total_duration_ms'] < MIN_DURATION_MS:
            # 太短就合并到上一组
            last = groups[-1]
            last['chapter_indices'].extend(current_group['chapter_indices'])
            last['chapters'].extend(current_group['chapters'])
            last['paragraphs'].extend(current_group['paragraphs'])
            last['total_duration_ms'] += current_group['total_duration_ms']
        else:
            groups.append(current_group)
    
    return groups


def _get_group_folder_name(chapter_indices: List[int]) -> str:
    """生成分组文件夹名称，如 chapters1-2 或 chapters3"""
    if len(chapter_indices) == 1:
        return f"chapters{chapter_indices[0]}"
    else:
        return f"chapters{chapter_indices[0]}-{chapter_indices[-1]}"



def generate_lrc(
    paragraphs: List[models.Paragraph],
    book_title: str = "",
    author: str = ""
) -> str:
    """
    为一组段落生成 LRC 歌词内容。
    每个句子一行 LRC，时间戳按句子字数比例分配。
    
    Args:
        paragraphs: 段落列表（已按顺序排列）
        book_title: 书名（LRC 元数据）
        author: 作者（LRC 元数据）
    
    Returns:
        LRC 格式字符串
    """
    lines = []
    
    # LRC 元数据头
    if book_title:
        lines.append(f"[ti:{book_title}]")
    if author:
        lines.append(f"[ar:{author}]")
    lines.append("")
    
    # 累计时间偏移（毫秒）
    current_time_ms = 0
    
    for para in paragraphs:
        # 段落实际时长
        para_duration = para.audio_duration_ms or para.estimated_duration_ms or 0
        
        # 尝试使用精确的句子时间戳
        if getattr(para, 'sentence_timings', None):
            try:
                import json
                timings = json.loads(para.sentence_timings)
                if timings:
                    for timing in timings:
                        # 转换时间单位: 1 unit = 100ns = 0.0001ms
                        ts_offset_ms = timing['offset'] / 10000
                        
                        # 计算绝对时间戳
                        abs_time_ms = current_time_ms + ts_offset_ms
                        
                        minutes = int(abs_time_ms // 60000)
                        seconds = int((abs_time_ms % 60000) // 1000)
                        centiseconds = int((abs_time_ms % 1000) // 10)
                        
                        text = timing['text'].strip()
                        if text:
                            lines.append(f"[{minutes:02d}:{seconds:02d}.{centiseconds:02d}]{text}")
                    
                    # 累加段落时长
                    current_time_ms += para_duration
                    continue
            except Exception as e:
                print(f"Error parsing timings for para {para.id}: {e}")
        
        # === 回退逻辑：将段落拆分为句子并估算时间 ===
        sentences = split_to_sentences(para.content)
        total_chars = sum(len(s) for s in sentences)
        
        if total_chars == 0:
            current_time_ms += para_duration
            continue
        
        # 按句子字数比例分配时间
        for sentence in sentences:
            # 格式化时间戳
            minutes = int(current_time_ms // 60000)
            seconds = int((current_time_ms % 60000) // 1000)
            centiseconds = int((current_time_ms % 1000) // 10)
            
            lines.append(f"[{minutes:02d}:{seconds:02d}.{centiseconds:02d}]{sentence}")
            
            # 按字数比例推进时间
            sentence_duration = int(para_duration * len(sentence) / total_chars)
            current_time_ms += sentence_duration
    
    return "\n".join(lines)


def export_book(
    db: Session,
    book_id: int,
    output_base_dir: str = None
) -> Dict:
    """
    导出整本书为 MP3 + LRC 文件。
    
    Args:
        db: 数据库会话
        book_id: 书籍 ID
        output_base_dir: 输出根目录（默认 output/）
    
    Returns:
        导出结果字典
    """
    book = crud.get_book(db, book_id)
    if not book:
        return {'success': False, 'message': '书籍不存在'}
    
    # 准备输出目录
    base_dir = Path(output_base_dir) if output_base_dir else OUTPUT_DIR
    book_dir = base_dir / sanitize_filename(book.title)
    
    # 清空旧的导出
    if book_dir.exists():
        shutil.rmtree(book_dir)
    book_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"[导出] 开始导出书籍: {book.title} (ID: {book_id})")
    
    # 分组章节
    groups = group_chapters_by_duration(db, book_id)
    
    if not groups:
        return {'success': False, 'message': '没有可导出的章节'}
    
    print(f"[导出] 共分为 {len(groups)} 个音频段")
    
    results = []
    success_count = 0
    fail_count = 0
    
    for i, group in enumerate(groups):
        folder_name = _get_group_folder_name(group['chapter_indices'])
        
        # 创建段落子文件夹
        segment_dir = book_dir / folder_name
        segment_dir.mkdir(parents=True, exist_ok=True)
        
        mp3_path = segment_dir / f"{folder_name}.mp3"
        lrc_path = segment_dir / f"{folder_name}.lrc"
        
        duration_min = group['total_duration_ms'] / 60000
        chapter_titles = ", ".join(
            c.title for c in group['chapters'] if c.title
        )
        logger.info(
            "[导出] 段 %d/%d: %s (预估 %.1f 分钟, 章节: %s)",
            i + 1, len(groups), folder_name, duration_min, chapter_titles
        )
        
        try:
            # 验证有效音频路径（存在且大小 > 0）
            audio_paths = [
                p.audio_path for p in group['paragraphs']
                if p.audio_path and Path(p.audio_path).exists() and Path(p.audio_path).stat().st_size > 0
            ]
            total_para = len(group['paragraphs'])
            skipped = total_para - len(audio_paths)
            if skipped > 0:
                logger.warning(
                    "[导出] ⚠️ 段 %s：%d/%d 个段落缺少有效音频文件，将跳过。",
                    folder_name, skipped, total_para
                )
            
            if not audio_paths:
                logger.warning(
                    "[导出] ⚠️ 段 %s：所有段落均无有效音频，跳过该段。",
                    folder_name
                )
                fail_count += 1
                results.append({
                    'folder': folder_name,
                    'chapters': group['chapter_indices'],
                    'duration_ms': group['total_duration_ms'],
                    'mp3_generated': False,
                    'lrc_generated': False,
                    'mp3_path': None,
                    'lrc_path': None,
                    'error': '所有段落均无有效音频'
                })
                continue
            
            # 生成 LRC 歌词（音频验证通过后再写 LRC）
            lrc_content = generate_lrc(
                group['paragraphs'],
                book_title=book.title,
                author=book.author
            )
            with open(lrc_path, 'w', encoding='utf-8') as f:
                f.write(lrc_content)
            logger.info("[导出] LRC 已生成: %s", lrc_path)
            
            # 合并音频为 MP3
            mp3_success = merge_audio(audio_paths, str(mp3_path), output_format="mp3", bitrate="64k")
            
            if mp3_success:
                success_count += 1
                # 写入 ID3 元数据标签（专辑、作者、封面）
                tag_mp3_metadata(
                    mp3_path=str(mp3_path),
                    title=f"{book.title} · {folder_name}",
                    album=book.title,
                    artist=book.author or "",
                    segment_name=folder_name,
                    track=success_count,
                    total_tracks=len(groups),
                )
                results.append({
                    'folder': folder_name,
                    'chapters': group['chapter_indices'],
                    'duration_ms': group['total_duration_ms'],
                    'mp3_generated': True,
                    'lrc_generated': True,
                    'mp3_path': str(mp3_path),
                    'lrc_path': str(lrc_path)
                })
            else:
                fail_count += 1
                # 音频合并失败：清理已生成的 LRC 和空文件夹
                if lrc_path.exists():
                    lrc_path.unlink()
                try:
                    segment_dir.rmdir()  # 仅在目录为空时才删除
                except OSError:
                    pass
                logger.warning("[导出] ⚠️ 音频合并失败，已清理 LRC，跳过该段: %s", folder_name)
                results.append({
                    'folder': folder_name,
                    'chapters': group['chapter_indices'],
                    'duration_ms': group['total_duration_ms'],
                    'mp3_generated': False,
                    'lrc_generated': False,
                    'mp3_path': None,
                    'lrc_path': None,
                    'error': '音频合并失败'
                })
        
        except Exception as e:
            fail_count += 1
            # 清理当前 group 的残留文件
            for f_path in [lrc_path, mp3_path]:
                if f_path.exists():
                    try:
                        f_path.unlink()
                    except OSError:
                        pass
            try:
                segment_dir.rmdir()
            except OSError:
                pass
            logger.error("[导出] ❌ 段 %s 处理异常: %s", folder_name, e, exc_info=True)
            results.append({
                'folder': folder_name,
                'chapters': group['chapter_indices'],
                'duration_ms': group['total_duration_ms'],
                'mp3_generated': False,
                'lrc_generated': False,
                'mp3_path': None,
                'lrc_path': None,
                'error': str(e)
            })
    
    total = len(groups)
    message = f"导出完成: {success_count}/{total} 个音频段成功"
    if fail_count > 0:
        message += f"，{fail_count} 个失败（部分段落缺少已合成的音频，请检查合成状态后重新导出）"
    
    logger.info("[导出] %s", message)
    logger.info("[导出] 输出目录: %s", book_dir)
    
    return {
        'success': success_count > 0,
        'message': message,
        'output_dir': str(book_dir),
        'total_segments': total,
        'success_count': success_count,
        'fail_count': fail_count,
        'segments': results
    }


def export_book_background(book_id: int, output_base_dir: str = None):
    """
    后台任务专用的导出函数。
    创建独立的数据库 Session。
    """
    from app.database import SessionLocal
    
    db = SessionLocal()
    try:
        result = export_book(db, book_id, output_base_dir)
        if result['success']:
            print(f"[导出] 后台导出完成: 书籍 {book_id}")
        else:
            print(f"[导出] 后台导出失败: {result['message']}")
    finally:
        db.close()

# get_export_dir, get_zip_path, create_zip_archive, cleanup_book_files, _sanitize_filename 
# 均已移至 app.utils 或不再需要

