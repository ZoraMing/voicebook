import logging
import os
import shutil
from pathlib import Path
from typing import Optional
from app.utils.text import sanitize_filename

logger = logging.getLogger(__name__)

def get_export_dir(output_base_dir: Path, book_title: str) -> Path:
    """获取书籍导出目录"""
    return output_base_dir / sanitize_filename(book_title)


def get_zip_path(output_base_dir: Path, book_title: str) -> Path:
    """获取书籍导出压缩包路径"""
    return output_base_dir / f"{sanitize_filename(book_title)}.zip"


def create_zip_archive(output_base_dir: Path, book_title: str) -> Optional[Path]:
    """
    创建书籍导出的压缩包
    
    Returns:
        压缩包路径，如果失败则返回 None
    """
    book_dir = get_export_dir(output_base_dir, book_title)
    if not book_dir.exists():
        return None
        
    zip_path = get_zip_path(output_base_dir, book_title)
    
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
        logger.error("[导出] 创建压缩包失败: %s", e)
        return None


def cleanup_book_files(book_id: int, book_title: str, output_base_dir: Path) -> None:
    """
    清理书籍相关的所有文件（音频、导出、压缩包）
    """
    # 1. 清理临时音频目录
    audio_dir = Path("audio") / f"book_{book_id}"
    if audio_dir.exists():
        try:
            shutil.rmtree(audio_dir)
            logger.info("[清理] 已删除音频目录: %s", audio_dir)
        except Exception as e:
            logger.warning("[清理] 删除音频目录失败: %s", e)
            
    # 2. 清理导出目录
    export_dir = get_export_dir(output_base_dir, book_title)
    if export_dir.exists():
        try:
            shutil.rmtree(export_dir)
            logger.info("[清理] 已删除导出目录: %s", export_dir)
        except Exception as e:
            logger.warning("[清理] 删除导出目录失败: %s", e)
            
    # 3. 清理 ZIP 包
    zip_path = get_zip_path(output_base_dir, book_title)
    if zip_path.exists():
        try:
            zip_path.unlink()
            logger.info("[清理] 已删除压缩包: %s", zip_path)
        except Exception as e:
            logger.warning("[清理] 删除压缩包失败: %s", e)
