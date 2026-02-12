"""
全书音频合成脚本 (优化版)
引入 tqdm 进度条
用法: python run_full_synthesis.py <文件路径> [并发数]
"""
import sys
import os
import asyncio
import time
from tqdm import tqdm

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, init_db
from app.services import decoder, tts, audiobook_exporter
from app.config import get_settings
from app import crud

settings = get_settings()


async def synthesize_all(db, book_id, voice, max_concurrent):
    """使用 tqdm 进度条合成所有段落"""
    paragraphs = crud.get_pending_paragraphs(db, book_id)
    total = len(paragraphs)

    if total == 0:
        print("没有待合成的段落")
        return

    print(f"\n开始合成 {total} 个段落 (并发数: {max_concurrent})...")
    semaphore = asyncio.Semaphore(max_concurrent)
    
    # 使用 tqdm 进度条
    pbar = tqdm(total=total, desc="合成进度", unit="段")
    
    completed = 0
    failed = 0

    async def process_one(para):
        nonlocal completed, failed
        async with semaphore:
            try:
                success = await tts.synthesize_paragraph(db, para, voice)
                if success:
                    completed += 1
                else:
                    failed += 1
            except Exception as e:
                failed += 1
            finally:
                pbar.update(1)

    await asyncio.gather(*[process_one(p) for p in paragraphs])
    pbar.close()

    print(f"\n合成完成!")
    print(f"  成功: {completed}, 失败: {failed}")
    return completed


def main():
    file_path = sys.argv[1] if len(sys.argv) > 1 else "ebook_input/置身事内.epub"
    max_concurrent = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    voice = "zh-CN-XiaoxiaoNeural"

    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return

    init_db()
    db = SessionLocal()

    try:
        # 1. 解析
        print(f"=" * 60)
        print(f"📚 开始处理: {file_path}")
        print(f"=" * 60)

        book_id, msg = decoder.decode_ebook(db, file_path)
        if not book_id:
            print(f"解析失败: {msg}")
            return
        print(f"✅ {msg} (Book ID: {book_id})")

        # 显示章节统计
        book = crud.get_book(db, book_id)
        chapters = crud.get_book_chapters(db, book_id)
        print(f"\n📖 书籍: {book.title}")
        print(f"   作者: {book.author}")
        print(f"   章节: {book.total_chapters}")
        print(f"   段落: {book.total_paragraphs}")

        # 2. TTS 合成
        print(f"\n🔊 TTS 引擎: {voice}")
        print(f"   并发数: {max_concurrent}")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            completed = loop.run_until_complete(
                synthesize_all(db, book_id, voice, max_concurrent)
            )
        finally:
            loop.close()

        # 更新进度
        crud.update_book_tts_progress(db, book_id)

        # 3. 导出
        print(f"\n📦 开始导出音频和 LRC...")
        result = audiobook_exporter.export_book(db, book_id)

        if result['success']:
            print(f"\n✅ 导出完成!")
            print(f"   输出目录: {result['output_dir']}")
        else:
            print(f"❌ 导出失败: {result['message']}")

        print(f"\n{'=' * 60}")
        print(f"全部完成!")
        print(f"{'=' * 60}")

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\n❌ 出错: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
