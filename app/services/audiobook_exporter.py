"""
有声书导出服务
将已合成的段落音频按章节分组合并为 WAV 文件，并生成 LRC 歌词文件。
"""
import os
import re
import shutil
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session

from app import models, crud
from app.config import get_settings

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


def _split_to_sentences(text: str) -> List[str]:
    """
    将文本按句子拆分。
    仅支持在明确的终止符号（句号、问号、感叹号）处拆分。
    """
    if not text:
        return []

    # 1. 核心拆分逻辑：识别主要句末标点
    # 仅保留：。！？；!?;… 以及点号 .
    # 使用后行断言 (?<=[...]) 保留标点；
    # 对于点号 .，使用否定预查 (?![0-9a-zA-Z]) 确保后面不是数字或字母，避免在 1.7 或 e.g. 处断开
    pattern = r'(?<=[。！？；!?;…])|(?<=\.(?![0-9a-zA-Z]))'
    parts = re.split(pattern, text)
    
    # 2. 清理空白项
    raw_sentences = [p.strip() for p in parts if p.strip()]
    
    # 3. 后处理：合并孤立的括号引用 (例如注脚数字 "(35)")
    result = []
    for s in raw_sentences:
        # 正则检查是否仅仅是括号包裹的数字，形如 (1), [42], (35)
        is_reference = re.match(r'^[\(\[（【]\d+[\)\]）】]$', s)
        
        if is_reference and result:
            # 将引用内容直接合并到上一句末尾
            result[-1] = f"{result[-1]} {s}"
        else:
            result.append(s)
            
    return result if result else [text]


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
        
        # 将段落拆分为句子
        sentences = _split_to_sentences(para.content)
        total_chars = sum(len(s) for s in sentences)
        
        if total_chars == 0:
            current_time_ms += para_duration
            continue
        
        # 按句子字数比例分配时间
        for sentence in sentences:
            # 格式化时间戳
            minutes = current_time_ms // 60000
            seconds = (current_time_ms % 60000) // 1000
            centiseconds = (current_time_ms % 1000) // 10
            
            lines.append(f"[{minutes:02d}:{seconds:02d}.{centiseconds:02d}]{sentence}")
            
            # 按字数比例推进时间
            sentence_duration = int(para_duration * len(sentence) / total_chars)
            current_time_ms += sentence_duration
    
    return "\n".join(lines)


def merge_audio_to_wav(
    paragraphs: List[models.Paragraph],
    output_path: str,
    sample_rate: int = 16000,
    channels: int = 1
) -> bool:
    """
    将多个段落的 MP3 音频合并为单个 WAV 文件。
    使用低采样率和单声道保持小体积。
    
    Args:
        paragraphs: 段落列表
        output_path: 输出 WAV 文件路径
        sample_rate: 采样率（默认 16kHz）
        channels: 声道数（默认单声道）
    
    Returns:
        是否成功
    """
    try:
        from pydub import AudioSegment
    except ImportError:
        print("[导出] 错误: 需要安装 pydub 库: pip install pydub")
        return False
    
    try:
        # 创建空音频
        combined = AudioSegment.empty()
        skipped = 0
        
        for para in paragraphs:
            audio_path = para.audio_path
            if not audio_path or not os.path.exists(audio_path):
                # 跳过没有音频的段落
                skipped += 1
                continue
            
            # 加载音频片段
            try:
                segment = AudioSegment.from_file(audio_path)
                combined += segment
            except Exception as e:
                print(f"[导出] 警告: 加载音频失败 {audio_path}: {e}")
                skipped += 1
                continue
        
        if len(combined) == 0:
            print("[导出] 错误: 没有可用的音频片段")
            return False
        
        if skipped > 0:
            print(f"[导出] 跳过了 {skipped} 个无音频的段落")
        
        # 转换参数：低采样率、单声道、16位
        combined = combined.set_frame_rate(sample_rate)
        combined = combined.set_channels(channels)
        combined = combined.set_sample_width(2)  # 16位
        
        # 导出为 WAV
        combined.export(output_path, format="wav")
        
        file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        duration_min = len(combined) / 60000
        print(f"[导出] WAV 已生成: {output_path} "
              f"(时长: {duration_min:.1f}分钟, 大小: {file_size_mb:.1f}MB)")
        
        return True
        
    except Exception as e:
        print(f"[导出] 音频合并失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def export_book(
    db: Session,
    book_id: int,
    output_base_dir: str = None
) -> Dict:
    """
    导出整本书为 WAV + LRC 文件。
    
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
    book_dir = base_dir / _sanitize_filename(book.title)
    
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
        
        wav_path = segment_dir / f"{folder_name}.wav"
        lrc_path = segment_dir / f"{folder_name}.lrc"
        
        duration_min = group['total_duration_ms'] / 60000
        chapter_titles = ", ".join(
            c.title for c in group['chapters'] if c.title
        )
        print(f"[导出] 段 {i+1}/{len(groups)}: {folder_name} "
              f"(预估 {duration_min:.1f} 分钟, 章节: {chapter_titles})")
        
        # 生成 LRC 歌词
        lrc_content = generate_lrc(
            group['paragraphs'],
            book_title=book.title,
            author=book.author
        )
        with open(lrc_path, 'w', encoding='utf-8') as f:
            f.write(lrc_content)
        print(f"[导出] LRC 已生成: {lrc_path}")
        
        # 合并音频为 WAV
        wav_success = merge_audio_to_wav(group['paragraphs'], str(wav_path))
        
        if wav_success:
            success_count += 1
        else:
            fail_count += 1
        
        results.append({
            'folder': folder_name,
            'chapters': group['chapter_indices'],
            'duration_ms': group['total_duration_ms'],
            'wav_generated': wav_success,
            'lrc_generated': True,
            'wav_path': str(wav_path),
            'lrc_path': str(lrc_path)
        })
    
    total = len(groups)
    message = f"导出完成: {success_count}/{total} 个音频段成功"
    if fail_count > 0:
        message += f", {fail_count} 个失败（可能缺少已合成的音频）"
    
    print(f"[导出] {message}")
    print(f"[导出] 输出目录: {book_dir}")
    
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


def get_export_dir(book_title: str) -> Path:
    """获取书籍导出目录"""
    return OUTPUT_DIR / _sanitize_filename(book_title)

def get_zip_path(book_title: str) -> Path:
    """获取书籍导出压缩包路径"""
    return OUTPUT_DIR / f"{_sanitize_filename(book_title)}.zip"

def create_zip_archive(book_title: str) -> Optional[Path]:
    """
    创建书籍导出的压缩包
    
    Returns:
        压缩包路径，如果失败则返回 None
    """
    book_dir = get_export_dir(book_title)
    if not book_dir.exists():
        return None
        
    zip_path = get_zip_path(book_title)
    
    try:
        if zip_path.exists():
            zip_path.unlink()
            
        import zipfile
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(book_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(book_dir)
                    zipf.write(file_path, arcname)
        return zip_path
    except Exception as e:
        print(f"[导出] 创建压缩包失败: {e}")
        return None

def cleanup_book_files(book_id: int, book_title: str) -> None:
    """
    清理书籍相关的所有文件（音频、导出、压缩包）
    """
    # 1. 清理临时音频目录
    audio_dir = Path("audio") / f"book_{book_id}"
    if audio_dir.exists():
        try:
            shutil.rmtree(audio_dir)
            print(f"[清理] 已删除音频目录: {audio_dir}")
        except Exception as e:
            print(f"[清理] 删除音频目录失败: {e}")
            
    # 2. 清理导出目录
    export_dir = get_export_dir(book_title)
    if export_dir.exists():
        try:
            shutil.rmtree(export_dir)
            print(f"[清理] 已删除导出目录: {export_dir}")
        except Exception as e:
            print(f"[清理] 删除导出目录失败: {e}")
            
    # 3. 清理 ZIP 包
    zip_path = get_zip_path(book_title)
    if zip_path.exists():
        try:
            zip_path.unlink()
            print(f"[清理] 已删除压缩包: {zip_path}")
        except Exception as e:
            print(f"[清理] 删除压缩包失败: {e}")

def _sanitize_filename(name: str) -> str:
    """清理文件名，移除不合法字符"""
    # 替换 Windows 不允许的字符
    invalid_chars = r'<>:"/\|?*'
    for c in invalid_chars:
        name = name.replace(c, '_')
    return name.strip()
