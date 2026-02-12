# VoiceBook 数据流

本文档描述系统的核心数据处理流程。

---

## 整体数据流

```mermaid
flowchart LR
    subgraph Input["输入"]
        PDF[PDF文件]
        EPUB[EPUB文件]
    end

    subgraph Decode["解析阶段"]
        Factory[解码器工厂]
        Extract[文本提取]
        Split[段落分割]
        LLM[LLM智能分章]
    end

    subgraph Store["存储"]
        DB[(SQLite)]
        Book[Book表]
        Chapter[Chapter表]
        Para[Paragraph表]
    end

    subgraph TTS["合成阶段"]
        Queue[待合成队列]
        Edge[Edge TTS]
        AudioFiles[/音频片段/]
    end

    subgraph Export["导出阶段"]
        Merge[音频合并]
        LRC[LRC生成]
        ZIP[ZIP打包]
    end

    subgraph Output["输出"]
        API[REST API]
        Player[播放器/下载]
    end

    PDF --> Factory
    EPUB --> Factory
    Factory --> Extract
    Extract --> Split
    Split --> LLM
    LLM --> Book
    Book --> Chapter
    Chapter --> Para
    Para --> DB

    DB --> Queue
    Queue --> Edge
    Edge --> AudioFiles
    AudioFiles --> DB

    DB --> Merge
    Merge --> AudioFiles
    Merge --> LRC
    LRC --> ZIP
    ZIP --> API
    API --> Output
```

---

## 电子书解析流程

### 流程图

```mermaid
sequenceDiagram
    participant U as 用户
    participant R as Router
    participant S as Decoder Service
    participant F as DecoderFactory
    participant D as PDF/EPUB Decoder
    participant L as LLM Service
    participant C as CRUD

    U->>R: POST /api/books/upload
    R->>R: 保存文件到 ebook_input/
    R->>S: decode_ebook(file_path)
    S->>F: create(file_path)
    F->>D: 根据扩展名选择解码器
    D-->>S: 返回解码器实例

    alt 智能分章模式
        S->>D: 提取全文
        S->>L: clean_and_reshape_text(text)
        L-->>S: 返回结构化章节
    else 普通模式
        S->>D: _extract_chapters()
        D-->>S: 返回原始章节
    end

    S->>C: create_book()
    loop 每个章节
        S->>C: create_chapter()
        S->>C: create_paragraphs_batch()
    end
    S->>C: update_book_stats()
    S-->>R: 返回 book_id
    R-->>U: 返回解析结果
```

### 数据转换

```
原始文件 → 解码器提取 → 段落分割 → LLM清洗 → 数据库存储
   ↓           ↓            ↓          ↓           ↓
 PDF/EPUB   原始文本     段落列表    章节结构   Book/Chapter/Paragraph
```

---

## TTS 合成流程

### 流程图

```mermaid
sequenceDiagram
    participant U as 用户
    participant R as Router
    participant S as TTS Service
    participant P as Edge Provider
    participant C as CRUD
    participant FS as 文件系统

    U->>R: POST /api/tts/{book_id}/start
    R->>S: synthesize_book_background()
    S->>C: get_pending_paragraphs()
    C-->>S: 待合成段落列表

    par 并发合成 (max_concurrent=5)
        loop 每个段落
            S->>C: update_status("processing")
            S->>P: generate_audio(text, voice)
            P->>FS: 保存 audio/book_X/p_Y.mp3
            P-->>S: success
            S->>C: update_paragraph_audio()
        end
    end

    S->>C: update_book_tts_progress()
    S-->>R: 合成完成
```

### 状态变化

```
pending → processing → completed
                  ↘→ failed (错误)
```

---

## 有声书导出流程 (New)

### 流程图

```mermaid
sequenceDiagram
    participant U as 用户
    participant R as Router
    participant E as Exporter Service
    participant FS as 文件系统
    participant DB as SQLite

    U->>R: POST /api/books/{book_id}/export
    R->>E: export_book_background()
    E->>DB: 查询已合成段落
    DB-->>E: 返回段落文本与音频路径
    
    loop 每个导出单元 (每单元约40分钟)
        E->>E: 合并音频片段 (WAV)
        E->>E: 计算绝对时间偏移
        E->>E: 生成 LRC 文件
        E->>FS: 写入 output/{book}/
    end
    
    E->>FS: 创建 ZIP 压缩包
    E-->>U: 导出完成，可供下载
```

---

## 数据模型关系

```mermaid
erDiagram
    Book ||--o{ Chapter : "1:N"
    Book ||--o{ Paragraph : "1:N"
    Chapter ||--o{ Paragraph : "1:N"

    Book {
        int id PK "主键"
        string title "书名"
        string author "作者"
        string file_path "源文件路径"
        int total_chapters "章节数"
        int total_paragraphs "段落数"
        int total_duration_ms "总时长"
        float tts_progress "合成进度%"
        string tts_voice "语音类型"
        datetime created_at "创建时间"
    }

    Chapter {
        int id PK "主键"
        int book_id FK "书籍ID"
        int chapter_index "章节序号"
        string title "章节标题"
        int total_paragraphs "段落数"
    }

    Paragraph {
        int id PK "主键"
        int book_id FK "书籍ID"
        int chapter_id FK "章节ID"
        int paragraph_index "段落序号"
        text content "文本内容"
        int char_count "字符数"
        int start_time_ms "开始时间"
        int end_time_ms "结束时间"
        int estimated_duration_ms "预估时长"
        string audio_path "音频路径"
        int audio_duration_ms "实际时长"
        string tts_status "合成状态"
        text tts_error "错误信息"
    }
```

---

## API 数据流

```mermaid
flowchart LR
    subgraph Request["请求"]
        Upload["POST /upload"]
        Parse["POST /parse/{file}"]
        Sync["POST /tts/{id}/start"]
        Get["GET /books/{id}"]
    end

    subgraph Response["响应"]
        UploadRes["UploadResponse"]
        BookRes["Book"]
        ChapterRes["Chapter[]"]
        ParaRes["Paragraph[]"]
    end

    Upload --> UploadRes
    Parse --> UploadRes
    Sync --> BookRes
    Get --> BookRes
    Get --> ChapterRes
    Get --> ParaRes
```
