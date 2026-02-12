"""
导出功能测试脚本
测试章节分组、LRC 生成和音频合并
"""
import sys
from pathlib import Path

# 添加项目根目录
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal, init_db
from app import crud
from app.services.audiobook_exporter import (
    group_chapters_by_duration,
    generate_lrc,
    export_book,
    _split_to_sentences,
)


def test_sentence_split():
    """测试句子拆分"""
    print("=" * 50)
    print("📝 测试句子拆分")
    print("=" * 50)
    
    test_cases = [
        "你好世界。这是一个测试。你觉得怎么样？",
        "这是一段没有标点的长文本内容需要被拆分开来",
        "第一句话，第二句话，第三句话。然后结束。",
        "Hello World! How are you? I'm fine.",
    ]
    
    for text in test_cases:
        sentences = _split_to_sentences(text)
        print(f"\n原文: {text}")
        print(f"拆分: {sentences}")
    
    print("\n✅ 句子拆分测试完成")


def test_grouping():
    """测试章节分组"""
    print("\n" + "=" * 50)
    print("📚 测试章节分组")
    print("=" * 50)
    
    init_db()
    db = SessionLocal()
    
    try:
        books = crud.get_books(db)
        if not books:
            print("⚠️ 数据库中没有书籍，跳过分组测试")
            return
        
        book = books[0]
        print(f"使用书籍: {book.title} (ID: {book.id})")
        
        groups = group_chapters_by_duration(db, book.id)
        
        print(f"共分为 {len(groups)} 个分组:")
        for i, group in enumerate(groups):
            duration_min = group['total_duration_ms'] / 60000
            para_count = len(group['paragraphs'])
            chapters = group['chapter_indices']
            print(f"  分组 {i+1}: 章节 {chapters}, "
                  f"{para_count} 段落, "
                  f"预估 {duration_min:.1f} 分钟")
        
        # 测试 LRC 生成
        if groups:
            print(f"\n📄 测试 LRC 生成 (第一个分组):")
            lrc = generate_lrc(
                groups[0]['paragraphs'],
                book_title=book.title,
                author=book.author
            )
            # 只打印前 10 行
            lrc_lines = lrc.split('\n')
            for line in lrc_lines[:10]:
                print(f"  {line}")
            if len(lrc_lines) > 10:
                print(f"  ... (共 {len(lrc_lines)} 行)")
        
        print("\n✅ 分组测试完成")
    finally:
        db.close()


def test_export():
    """测试完整导出"""
    print("\n" + "=" * 50)
    print("🎵 测试完整导出")
    print("=" * 50)
    
    init_db()
    db = SessionLocal()
    
    try:
        books = crud.get_books(db)
        if not books:
            print("⚠️ 数据库中没有书籍")
            return
        
        book = books[0]
        print(f"导出书籍: {book.title} (ID: {book.id})")
        
        result = export_book(db, book.id)
        
        print(f"\n导出结果:")
        print(f"  成功: {result['success']}")
        print(f"  消息: {result['message']}")
        if result.get('output_dir'):
            print(f"  输出目录: {result['output_dir']}")
            
            # 检查输出文件
            output_dir = Path(result['output_dir'])
            if output_dir.exists():
                print(f"\n  目录结构:")
                for item in sorted(output_dir.rglob("*")):
                    if item.is_file():
                        size_kb = item.stat().st_size / 1024
                        rel = item.relative_to(output_dir)
                        print(f"    {rel} ({size_kb:.1f} KB)")
        
        print("\n✅ 导出测试完成")
    finally:
        db.close()


if __name__ == "__main__":
    # 运行所有测试
    test_sentence_split()
    test_grouping()
    
    # 导出测试（需要已有合成音频）
    if len(sys.argv) > 1 and sys.argv[1] == "--export":
        test_export()
    else:
        print("\n💡 提示: 使用 --export 参数运行完整导出测试")
        print("   python tests/test_export.py --export")
