import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.llm_service import LLMClient
from app.config import get_settings

def test_llm_connection():
    print("Testing LLM Connection...")
    settings = get_settings()
    print(f"URL: {settings.LLM_API_BASE}")
    print(f"Model: {settings.LLM_MODEL_NAME}")
    
    client = LLMClient()
    try:
        # Test with a simple clean task
        # raw_text = """第1章 开始\n这是一个测试段落。\n   页眉信息  \n这是第二段。"""
        raw_text = ""
        with open("ebook_input\讲解ai.md",'r',encoding='utf-8') as book:
            raw_text = book.read()
        print(raw_text)
        result = client.clean_and_reshape_text(raw_text)
        print("\nResult:")
        import json
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print("\n✅ LLM Connection Successful!")
    except Exception as e:
        print(f"\n❌ LLM Connection Failed: {e}")

if __name__ == "__main__":
    test_llm_connection()
