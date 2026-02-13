
import sys
import os
import shutil
import asyncio
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, init_db
from app import crud, models
from app.services import audiobook_exporter, tts
from app.utils.audio import merge_audio
from app.utils.files import get_zip_path, create_zip_archive
from app.config import get_settings

try:
    from tqdm import tqdm
except ImportError:
    print("Warning: tqdm not installed. Install with `pip install tqdm` for progress bars.")
    tqdm = lambda x, **kwargs: x

def list_books(db):
    """List all books with their status"""
    books = crud.get_books(db, limit=100)
    if not books:
        print("没有找到任何书籍。请先上传电子书。")
        return []
    
    print("\n📚 可用书籍列表:")
    print(f"{'ID':<5} {'标题':<30} {'作者':<15} {'进度':<20}")
    print("-" * 75)
    
    VALID_BOOKS = []
    
    for book in books:
        total = db.query(models.Paragraph).filter(models.Paragraph.book_id == book.id).count()
        completed = db.query(models.Paragraph).filter(
            models.Paragraph.book_id == book.id, 
            models.Paragraph.tts_status == 'completed'
        ).count()
        failed = db.query(models.Paragraph).filter(
            models.Paragraph.book_id == book.id, 
            models.Paragraph.tts_status == 'failed'
        ).count()
        
        progress = f"{completed}/{total}"
        if failed > 0:
            progress += f" ({failed} 失败)"
            
        print(f"{book.id:<5} {book.title[:28]:<30} {(book.author or '')[:13]:<15} {progress:<20}")
        VALID_BOOKS.append(book.id)
        
    print("-" * 75)
    return VALID_BOOKS

async def run_synthesis(db, book_id, max_concurrent=20):
    """运行 TTS 合成，带自动重试失败段落"""
    paragraphs = crud.get_pending_paragraphs(db, book_id)
    total = len(paragraphs)
    
    if total == 0:
        return True

    print(f"\n🔊 开始合成音频 (待合成: {total}, 并发: {max_concurrent})...")
    voice = "zh-CN-XiaoxiaoNeural"
    
    max_rounds = 3  # 最多重试 3 轮
    
    for round_num in range(1, max_rounds + 1):
        if round_num > 1:
            # 重新获取待合成段落（上一轮失败的）
            paragraphs = crud.get_pending_paragraphs(db, book_id)
            # 加上 failed 状态的段落
            failed_paras = db.query(models.Paragraph).filter(
                models.Paragraph.book_id == book_id,
                models.Paragraph.tts_status == 'failed'
            ).all()
            paragraphs = list(paragraphs) + list(failed_paras)
            
            if not paragraphs:
                break
            print(f"\n🔄 第 {round_num} 轮重试 (剩余: {len(paragraphs)})...")

        semaphore = asyncio.Semaphore(max_concurrent)
        pbar = tqdm(total=len(paragraphs), desc=f"合成进度 (第{round_num}轮)", unit="段")
        
        async def process_one(para):
            async with semaphore:
                try:
                    success = await tts.synthesize_paragraph(db, para, voice)
                    return success
                except Exception:
                    return False
                finally:
                    pbar.update(1)

        results = await asyncio.gather(*[process_one(p) for p in paragraphs])
        pbar.close()
        
        success_count = sum(1 for r in results if r)
        fail_count = len(paragraphs) - success_count
        print(f"  ✅ 成功: {success_count}, ❌ 失败: {fail_count}")
        
        if fail_count == 0:
            break
    
    # 最终统计
    final_completed = db.query(models.Paragraph).filter(
        models.Paragraph.book_id == book_id,
        models.Paragraph.tts_status == 'completed'
    ).count()
    final_total = db.query(models.Paragraph).filter(
        models.Paragraph.book_id == book_id
    ).count()
    print(f"📊 最终合成结果: {final_completed}/{final_total}")
    return final_completed > 0

def export_with_progress(db, book_id):
    """Run export with tqdm progress bar"""
    book = crud.get_book(db, book_id)
    if not book:
        print("书籍不存在")
        return

    print(f"\n� 开始准备导出: 《{book.title}》")
    
    # Check if we have any audio at all
    completed_count = db.query(models.Paragraph).filter(
        models.Paragraph.book_id == book_id,
        models.Paragraph.tts_status == 'completed'
    ).count()
    
    if completed_count == 0:
        print("❌ 错误: 该书籍没有任何已完成的音频。请先运行合成任务。")
        return

    # 1. Prepare
    settings = get_settings()
    output_base_dir = Path(settings.OUTPUT_DIR)
    
    print("正在分析章节分组...")
    groups = audiobook_exporter.group_chapters_by_duration(db, book_id)
    
    if not groups:
        print("没有可导出的章节 (可能没有完成的音频)")
        return

    # Prepare output dir
    book_dir = output_base_dir / audiobook_exporter.sanitize_filename(book.title)
    if book_dir.exists():
        # Keep old files? Better clear them for a fresh export
        shutil.rmtree(book_dir)
    book_dir.mkdir(parents=True, exist_ok=True)
    
    total_steps = len(groups)
    success_count = 0
    
    # 2. Process with Progress Bar
    pbar = tqdm(groups, desc="导出进度", unit="段")
    
    for group in pbar:
        folder_name = audiobook_exporter._get_group_folder_name(group['chapter_indices'])
        pbar.set_postfix_str(f"处理: {folder_name}")
        
        # Create segment dir
        segment_dir = book_dir / folder_name
        segment_dir.mkdir(parents=True, exist_ok=True)
        
        mp3_path = segment_dir / f"{folder_name}.mp3"
        lrc_path = segment_dir / f"{folder_name}.lrc"
        
        # 生成 LRC
        try:
            lrc_content = audiobook_exporter.generate_lrc(
                group['paragraphs'],
                book_title=book.title,
                author=book.author
            )
            with open(lrc_path, 'w', encoding='utf-8') as f:
                f.write(lrc_content)
        except Exception as e:
            pbar.write(f"❌ LRC 生成失败 ({folder_name}): {e}")
            continue

        # 合并音频为 MP3
        audio_paths = [p.audio_path for p in group['paragraphs']]
        wav_success = merge_audio(audio_paths, str(mp3_path), output_format="mp3", bitrate="64k")
        
        if wav_success:
            success_count += 1
        else:
            # Cleanup on failure
            if lrc_path.exists():
                lrc_path.unlink()
            if segment_dir.exists():
                # Only remove if empty
                try:
                    segment_dir.rmdir()
                except OSError:
                    pass
            pbar.write(f"⚠️ 音频合并失败，跳过: {folder_name}")

    pbar.close()
    
    print(f"\n📊 导出统计: {success_count}/{total_steps} 个音频段成功")
    
    # 3. Create ZIP
    if success_count > 0:
        print("📦 正在创建 ZIP 压缩包...")
        zip_path = create_zip_archive(output_base_dir, book.title)
        if zip_path:
            size_mb = zip_path.stat().st_size / (1024 * 1024)
            print(f"✅ ZIP 创建成功: {zip_path}")
            print(f"   大小: {size_mb:.2f} MB")
        else:
            print("❌ ZIP 创建失败")
    else:
        print("❌ 没有生成任何有效音频，跳过 ZIP 创建")


async def main():
    init_db()
    db = SessionLocal()
    try:
        book_id = None
        
        if len(sys.argv) > 1:
            arg = sys.argv[1]
            if os.path.exists(arg):
                # 如果是文件路径，先通过 decoder 获取或导入书籍
                from app.services import decoder
                print(f"🔍 正在处理文件: {arg}...")
                book_id, msg = decoder.decode_ebook(db, arg)
                if not book_id:
                    print(f"❌ 解析失败: {msg}")
                    return
                print(f"✅ {msg} (ID: {book_id})")
            else:
                # 尝试作为 ID 处理
                try:
                    book_id = int(arg)
                except ValueError:
                    print(f"❌ 路径不存在且不是有效的 ID: {arg}")
                    return
        
        if book_id is None:
            valid_ids = list_books(db)
            if not valid_ids:
                return

            try:
                choice = input("\n请输入要导出的书籍 ID (0 退出): ")
                if choice == '0':
                    return
                book_id = int(choice)
            except ValueError:
                print("请输入数字")
                return

        # Check if synthesis is needed
        total = db.query(models.Paragraph).filter(models.Paragraph.book_id == book_id).count()
        completed = db.query(models.Paragraph).filter(
            models.Paragraph.book_id == book_id, 
            models.Paragraph.tts_status == 'completed'
        ).count()
        
        if completed < total:
            print(f"\n⚠️ 提示: 书籍尚未完成合成 ({completed}/{total})")
            choice = input("是否现在开始音频合成任务? (y/n): ").lower()
            if choice == 'y':
                await run_synthesis(db, book_id)
                # Refresh progress
                crud.update_book_tts_progress(db, book_id)
            elif completed == 0:
                print("未合成音频，无法导出。")
                return

        export_with_progress(db, book_id)

    except KeyboardInterrupt:
        print("\n已取消")
    except Exception as e:
        print(f"\n发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
