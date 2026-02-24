# TTS 引擎管理与扩展指南

本指南介绍如何在 VoiceBook 项目中切换 TTS 语音合成引擎，以及如何接入新的 TTS 引擎。

## 1. 切换 TTS 引擎

在项目根目录的 `.env` 文件中修改 `TTS_PROVIDER` 变量：

```env
# 可选值: edge (默认)
TTS_PROVIDER=edge
```

### 已支持的引擎

| 引擎 | 说明 | 需要 Key |
|------|------|----------|
| `edge` | Microsoft Edge 在线语音合成（推荐） | 否 |

---

## 2. 开发新的 TTS 引擎

### 步骤 1：创建引擎实现类

在 `app/services/tts_providers/` 下新建文件（如 `openai_tts.py`），继承 `TTSProvider` 基类：

**基类位置**: `app/services/tts_providers/base.py`

```python
# app/services/tts_providers/openai_tts.py

import os
from typing import List, Dict, Tuple, Optional
from .base import TTSProvider


class OpenAITTSProvider(TTSProvider):
    """OpenAI TTS 引擎示例"""

    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY", "")
        self.voices = [
            {"id": "alloy", "name": "Alloy", "voice": "alloy", "gender": "中性"},
            {"id": "echo",  "name": "Echo",  "voice": "echo",  "gender": "中性"},
        ]

    async def generate_audio(
        self, text: str, voice: str, output_path: str
    ) -> Tuple[bool, Optional[List[dict]]]:
        """
        生成音频文件。

        Returns:
            (success, timings)
            timings 格式: [{"text": str, "offset": int(100ns), "duration": int(100ns)}, ...]
            不支持时间戳时返回 (success, None)
        """
        try:
            # 调用 OpenAI TTS API，将结果写入 output_path ...
            return True, None
        except Exception as e:
            print(f"[OpenAI] 合成失败: {e}")
            return False, None

    def get_voices(self) -> List[Dict]:
        return self.voices

    def get_name(self) -> str:
        return "openai"  # 与 .env 中 TTS_PROVIDER 对应

    def get_supported_formats(self) -> List[str]:
        return ["mp3"]
```

### 步骤 2：在工厂中注册新引擎

修改 `app/services/tts.py`，在 `TTSFactory._providers` 字典中添加新引擎：

```python
# app/services/tts.py

from .tts_providers.openai_tts import OpenAITTSProvider

class TTSFactory:
    _providers = {
        "edge":   EdgeTTSProvider,
        "openai": OpenAITTSProvider,  # 新增此行
    }
```

### 步骤 3：验证

1. 在 `.env` 中设置 `TTS_PROVIDER=openai`。
2. 重启后端服务。
3. 访问前端"声音选择"列表，确认显示新引擎的语音。
4. 合成一段测试文本，检查日志中无报错，音频文件正常生成。

---

## 3. 高精度时间戳（WordBoundary）

若引擎支持逐词/逐句时间戳（如 Azure TTS、Google TTS），可在 `generate_audio` 中返回 `timings` 列表，系统会直接用于生成精确 LRC：

```python
timings = [
    {"text": "你好", "offset": 0,       "duration": 5000000},
    {"text": "世界", "offset": 5000000, "duration": 4500000},
    # offset 和 duration 单位为 100 纳秒
]
return True, timings
```

不支持时间戳时返回 `None`，系统会自动回退为按字数比例估算时间戳。

---

## 4. 现有 EdgeTTS 特性说明

- **自动重试**：最多重试 3 次，间隔 2/4/8 秒（指数退避）。
- **文件验证**：每次重试前删除上次不完整文件；生成后验证文件大小 ≥ 1 KB。
- **并发控制**：上层服务通过 `asyncio.Semaphore` 控制并发数（默认 5）。
- **多轮重试**：API 后台任务支持自动对失败段落进行最多 2 轮全局重试。
