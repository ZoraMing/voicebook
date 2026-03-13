# 🎙️ VoiceBook - 智能有声书制作系统

VoiceBook 是一个现代化的有声书制作平台，集成了智能文本解析、高精度语音合成与可视化的编辑管理功能。它能够将电子书（PDF/EPUB/TXT/MD）转换为结构化的音频内容，支持逐段精细调整、批量合成导出，并提供极致的 Web Studio 编辑体验。

## 核心特性

### 现代化 Web Studio
- **沉浸式编辑体验**: 基于 **Next.js 16** 和 **Tailwind CSS v4** 构建的全新界面，支持夜间模式与响应式设计。
- **实时预览与编辑**: 所见即所得的段落编辑器，支持文本修改、语音角色切换与实时试听。
- **智能进度追踪**: 全局进度条实时反馈合成状态，支持多任务并发处理。

### 高效合成工作流
- **批量合成引擎**: 支持**全书**、**单章**或**多选段落**的一键批量合成。
- **高精度 TTS**: 集成 Microsoft Edge TTS，支持 **WordBoundary** 级时间戳，实现毫秒级音画同步。
- **异步并发架构**: 后端采用 FastAPI 异步任务队列，支持大规模文本并发处理，稳定高效。

### 智能内容管理
- **多格式解析**: 完美支持 PDF、EPUB、TXT 和 Markdown 格式，自动识别目录结构与章节。
- **智能分章**: 内置 LLM 辅助解析（可选），智能优化断句与章节划分。
- **高品质导出**: 一键导出为按章节合并的 WAV 音频与精确时间戳 LRC 歌词文件，完美适配主流音乐播放器。

---

## 快速启动

### 1. 环境准备

确保已安装 Python 3.12+ 和 Node.js 20+。

```bash
python -m venv .venv
# 激活 Python 虚拟环境
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# 安装后端依赖
pip install -r requirements.txt

# 针对 Python 3.13+ 用户 (必须安装否则无法合并音频)
pip install audioop-lts
```

### 2. 启动系统

您可以同时通过 Web 界面和 CLI 命令行工具使用系统。

**启动后端与前端：**
```bash
# 启动后端 (Terminal 1)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 启动前端 Studio (Terminal 2)
cd front
npm install
npm run dev
```

**快速导出工具：**
如果您只需导出已合成的书籍，可直接使用：
```bash
python cli_export.py 书本路径
```

---

## 导出文件说明

导出完成后，文件将保存在项目根目录的 `output/` 文件夹下。为了获得最佳播放体验，系统会将章节按时长进行智能分组（默认每段约 40 分钟）：

```text
output/
└── 书籍名称/
    ├── chapters1-5/           # 第 1 到 5 章合并段
    │   ├── chapters1-5.mp3    # 音频文件 (已内嵌封面与元数据)
    │   └── chapters1-5.lrc    # 同步歌词文件
    └── chapters6-10/
        ├── chapters6-10.mp3
        └── chapters6-10.lrc
```

### 播放建议
- **内嵌封面**: 导出的 MP3 已自动生成并内嵌了带有书名和作者信息的渐变封面。
- **歌词同步**: 将导出的文件夹导入支持 LRC 的播放器（如网易云音乐、手机系统内置播放器），即可享受精确到词的朗读同步。

---

## 常见问题

### 1. Python 3.13 报错 `No module named 'audioop'`
这是由于 Python 3.13 移除了官方的 `audioop` 模块。
**解决方法**：安装 `pip install audioop-lts`。项目已集成兼容补丁。

### 2. 导出时显示“音频合并失败”
- 请确保电脑已安装 **FFmpeg** 并已加入系统环境变量（PATH）。
- 在终端输入 `ffmpeg -version` 确认其可用性。

### 3. Edge TTS 合成超时
- 检查网络连接。如果环境受限，可在 `app/config.py` 中配置代理支持。

