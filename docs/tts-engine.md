# TTS 引擎管理与扩展指南

本指南介绍如何在 VoiceBook 项目中切换 TTS (语音合成) 引擎，以及如何编写新的 TTS 引擎接口。

## 1. 切换 TTS 引擎

VoiceBook 支持通过环境变量配置使用的 TTS 引擎。目前默认使用 `edge-tts`。

### 配置方法

在项目根目录的 `.env` 文件中修改 `TTS_PROVIDER` 变量：

```env
# 可选值: edge (默认), openai (示例)
TTS_PROVIDER=edge
```

### 已支持的引擎

-   **edge**: 使用 Microsoft Edge 在线语音合成服务（免费，效果好，无需 Key）。
-   *(更多引擎待添加...)*

---

## 2. 开发新的 TTS 引擎

如果您需要接入其他 TTS 服务（如 OpenAI、Azure、Google、讯飞等），请按照以下步骤操作。

### 步骤 1: 创建引擎实现类

在 `app/services/tts_providers/` 目录下创建一个新的 Python 文件（例如 `openai_tts.py`），并定义一个类继承自 `TTSProvider` 基类。

**基类位置**: `app/services/tts_providers/base.py`

**代码示例**:

```python
# app/services/tts_providers/openai_tts.py

from typing import List, Dict
from .base import TTSProvider
# import openai  # 导入必要的库

class OpenAITTSProvider(TTSProvider):
    """OpenAI TTS 引擎实现示例"""
    
    def __init__(self):
        # 在这里初始化客户端，读取配置等
        # self.api_key = ...
        pass

    async def generate_audio(self, text: str, voice: str, output_path: str) -> Tuple[bool, Optional[List[dict]]]:
        """
        生成音频文件
        
        Args:
            text: 要合成的文本
            voice: 发音人 ID/名称
            output_path: 音频文件保存路径 (绝对路径)
            
        Returns:
            Tuple[bool, Optional[List[dict]]]: 
                - 第一个元素为是否成功
                - 第二个元素为时间戳列表，如果引擎不支持则返回 None
        """
        try:
            # 调用 API 生成音频
            # ...
            # timings = [{"text": "Hello", "offset": 0, "duration": 100}, ...]
            print(f"[OpenAI] Generating audio for: {text[:20]}...")
            return True, None # 示例暂未实现时间戳
        except Exception as e:
            print(f"[OpenAI] Error: {e}")
            return False, None

    def get_voices(self) -> List[Dict]:
        """
        获取支持的发音人列表
        
        Returns:
            List[Dict]: 包含 id, name, gender 等信息的字典列表
        """
        return [
            {"id": "alloy", "name": "Alloy", "voice": "alloy", "gender": "neutral"},
            {"id": "echo", "name": "Echo", "voice": "echo", "gender": "neutral"},
            # ...
        ]

    def get_name(self) -> str:
        """返回引擎唯一标识符 (与 .env 中 TTS_PROVIDER 对应)"""
        return "openai"

    def get_supported_formats(self) -> List[str]:
        """返回支持的音频格式"""
        return ["mp3"]
```

### 步骤 2: 注册新引擎

修改 `app/services/tts_providers/__init__.py` 工厂类，将新引擎注册进去。

**代码示例**:

```python
# app/services/tts_providers/__init__.py

from .base import TTSProvider
from .edge import EdgeTTSProvider
# 导入新引擎
from .openai_tts import OpenAITTSProvider 

class TTSFactory:
    _providers = {}

    @classmethod
    def register(cls, name: str, provider_cls):
        cls._providers[name] = provider_cls

    @classmethod
    def create(cls, provider_name: str) -> TTSProvider:
        if provider_name not in cls._providers:
            # 默认回退到 edge
            print(f"Warning: TTS provider '{provider_name}' not found, using 'edge'.")
            return cls._providers.get("edge")()
        
        return cls._providers[provider_name]()
    
    @classmethod
    def get_available_providers(cls) -> List[str]:
        return list(cls._providers.keys())

# 注册引擎
TTSFactory.register("edge", EdgeTTSProvider)
TTSFactory.register("openai", OpenAITTSProvider) # 注册新引擎
```

### 步骤 3: 验证

1.  修改 `.env` 将 `TTS_PROVIDER` 设置为您新注册的引擎名称（例如 `openai`）。
2.  重启后端服务。
3.  在前端页面刷新，检查“声音选择”列表是否加载了新引擎的声音列表。
4.  尝试合成一段文本，检查后台日志和输出文件。

---

## 3. 高精度同步 (WordBoundary)

从 v2.1 版本开始，项目支持捕获 TTS 引擎的 WordBoundary 事件。

如果您开发的新引擎支持返回每个词或句子的时间戳（例如 Azure TTS, Google TTS 等），请确保 `generate_audio` 返回一个包含以下字段的列表：
- `text`: 该时间戳对应的文本内容。
- `offset`: 偏移量（单位：100纳秒）。
- `duration`: 持续时间（单位：100纳秒）。

这些数据将被存入数据库并直接用于生成 LRC 文件，确保歌词与语音完美同步。
