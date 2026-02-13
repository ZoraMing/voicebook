import re
from typing import List

def split_to_sentences(text: str) -> List[str]:
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


def sanitize_filename(name: str) -> str:
    """清理文件名，移除不合法字符"""
    # 替换 Windows 不允许的字符
    invalid_chars = r'<>:"/\|?*'
    for c in invalid_chars:
        name = name.replace(c, '_')
    return name.strip()


def clean_text_for_tts(text: str) -> str:
    """清理文本中不适合朗读的标点符号，替换为空格以防止朗读其名称"""
    if not text:
        return ""
    # 替换这些符号为空格: _ / \ | ~ * # % > - ” “ "
    # 这些通常是 Markdown 标识符或装饰符，朗读出来会影响流利度
    text = re.sub(r'[_/\\|~\*#%>\-”“"]', ' ', text)
    return ' '.join(text.split())
