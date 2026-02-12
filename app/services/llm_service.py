import json
import logging
from typing import List, Dict, Optional
from openai import OpenAI
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        self.client = OpenAI(
            base_url=settings.LLM_API_BASE,
            api_key=settings.LLM_API_KEY,
        )
        self.model = settings.LLM_API_BASE

    def _get_system_prompt(self) -> str:
        return """
            你是一个专业的电子书排版整理助手。
            你的任务是将输入的电子书原始文本（可能包含页眉、页脚、分页符导致的断句、无关的出版信息等）进行清洗和重新分章。

            请遵循以下规则：
            1. **去噪**：识别并删除页眉、页脚、页码、出版社广告等无关信息。
            2. **合并**：将因为分页而断开的句子重新合并。
            3. **分章**：根据文本内容的逻辑结构进行分章。通常章节会有 "第X章" 或具体的章节名。
            4. **输出格式**：必须返回合法的 JSON 格式列表，不要包含 Markdown 代码块标记。格式如下：
            [
                {
                    "title": "章节标题（如果无法识别则根据内容生成总结或使用 '未命名章节'）",
                    "content": "清洗并合并后的章节正文内容..."
                },
                ...
            ]
            5. 保持原文的意思，不要修改正文措辞，只做格式和结构整理。
            6. 如果输入文本太短或是目录、前言等非正文内容，请根据情况判断，如果是目录则可以忽略或整理为一个特殊章节。
            """

    def clean_and_reshape_text(self, raw_text: str) -> List[Dict[str, str]]:
        """
        使用 LLM 清洗和重组文本
        
        Args:
            raw_text: 原始文本块
            
        Returns:
            结构化的章节列表 [{'title': '...', 'content': '...'}]
        """
        if not raw_text or not raw_text.strip():
            return []

        try:
            response = self.client.chat.completions.create(
                model=settings.LLM_MODEL_NAME,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": f"请处理以下文本：\n\n{raw_text[:20000]}"} # 限制长度防止溢出
                ],
                temperature=0.2,
            )
            
            content = response.choices[0].message.content.strip()
            print(content,"\n=================")
            # 尝试清理可能存在的 markdown 标记
            content = content.split('</think>')[1]
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            
            result = json.loads(content.strip())
            return result
            
        except json.JSONDecodeError:
            logger.error("LLM 返回了无法解析的 JSON")
            # 兜底策略：如果解析失败，作为单个章节返回并尝试简单清理
            return [{"title": "解析错误兜底章节", "content": raw_text}]
        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            return [{"title": "处理失败章节", "content": raw_text}]

    def _get_paragraph_split_prompt(self) -> str:
        """获取段落拆分的系统提示词"""
        return """你是一个专业的文本处理助手，擅长将长文本智能拆分为适合 TTS 朗读的段落。

            请遵循以下规则：
            1. **语义完整性**：每个段落应该是一个完整的语义单元，不要在句子中间断开。
            2. **适合朗读**：段落长度适中（通常 50-150 字），便于 TTS 合成和听众理解。
            3. **自然断句**：在标点符号处断句，优先在句号、问号、感叹号处分割。
            4. **保留结构**：识别对话、引用、标题等特殊结构，并标记类型。
            5. **预估时长**：按每分钟 300 字的语速预估朗读时长。

            **输出格式**（必须返回合法 JSON 数组，不要包含 Markdown 标记）：
            [
                {
                    "content": "段落文本内容",
                    "segment_type": "paragraph|dialogue|quote|title|subtitle",
                    "speaker": "说话人（对话时填写，否则为空字符串）",
                    "estimated_duration_ms": 预估时长毫秒数,
                    "pause_after_ms": 段后停顿毫秒数（通常 300-800）
                },
                ...
            ]

            **segment_type 类型说明**：
            - paragraph: 普通段落
            - dialogue: 对话（通常有引号或破折号开头）
            - quote: 引用文本
            - title: 章节标题
            - subtitle: 小节标题"""

    def smart_split_paragraphs(self, text: str, max_chars_per_segment: int = 150) -> List[Dict]:
        """
        使用 LLM 智能拆分文本为段落
        
        Args:
            text: 待拆分的文本
            max_chars_per_segment: 单段最大字符数提示
            
        Returns:
            段落列表，每段包含 content, segment_type, speaker, estimated_duration_ms, pause_after_ms
        """
        if not text or not text.strip():
            return []
        
        try:
            user_prompt = f"""请将以下文本智能拆分为适合 TTS 朗读的段落。
                单段建议不超过 {max_chars_per_segment} 字符。

                待处理文本：
                {text[:15000]}"""
            
            response = self.client.chat.completions.create(
                model=settings.LLM_MODEL_NAME,
                messages=[
                    {"role": "system", "content": self._get_paragraph_split_prompt()},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,  # 较低温度保证一致性
            )
            
            content = response.choices[0].message.content.strip()
            content = content.split('</think>')[1]
            # 清理可能存在的 markdown 标记
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            
            result = json.loads(content.strip())
            
            # 验证并补充缺失字段
            validated_result = []
            for item in result:
                validated_item = {
                    "content": item.get("content", ""),
                    "segment_type": item.get("segment_type", "paragraph"),
                    "speaker": item.get("speaker", ""),
                    "estimated_duration_ms": item.get("estimated_duration_ms", 
                        int(len(item.get("content", "")) / 300 * 60 * 1000)),
                    "pause_after_ms": item.get("pause_after_ms", 500)
                }
                if validated_item["content"].strip():
                    validated_result.append(validated_item)
            
            return validated_result
            
        except json.JSONDecodeError as e:
            logger.error(f"LLM 返回 JSON 解析失败: {e}")
            # 兜底：使用简单规则拆分
            return self._fallback_split(text)
        except Exception as e:
            logger.error(f"LLM 段落拆分失败: {e}")
            return self._fallback_split(text)
    
    def _fallback_split(self, text: str) -> List[Dict]:
        """
        兜底拆分策略：按句号分割
        """
        import re
        # 按中文句号、英文句号、问号、感叹号分割
        sentences = re.split(r'(?<=[。！？.!?])\s*', text)
        
        result = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                result.append({
                    "content": sentence,
                    "segment_type": "paragraph",
                    "speaker": "",
                    "estimated_duration_ms": int(len(sentence) / 300 * 60 * 1000),
                    "pause_after_ms": 500
                })
        return result
