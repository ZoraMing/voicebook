/**
 * 有声书制作系统 - API 封装
 * 所有与后端通信的接口
 */

const API_BASE = '/api'

// ========== 类型定义 ==========

/** 书籍信息 */
export interface Book {
    id: number
    title: string
    author: string
    file_path: string
    total_chapters: number
    total_paragraphs: number
    total_duration_ms: number
    tts_progress: number
    tts_voice: string
    created_at: string
}

/** 章节信息 */
export interface Chapter {
    id: number
    book_id: number
    chapter_index: number
    title: string
    total_paragraphs: number
}

/** 段落信息 */
export interface Paragraph {
    id: number
    book_id: number
    chapter_id: number
    paragraph_index: number
    content: string
    char_count: number
    start_time_ms: number
    end_time_ms: number
    audio_path: string | null
    audio_duration_ms: number | null
    tts_status: 'pending' | 'processing' | 'completed' | 'failed'
}

/** 语音信息 */
export interface VoiceInfo {
    id: string
    name: string
    voice: string
    gender: string
}

/** 上传响应 */
export interface UploadResponse {
    success: boolean
    message: string
    book_id?: number
    book?: Book
}

/** 合成响应 */
export interface SynthesizeResponse {
    success: boolean
    message: string
    total: number
    completed: number
    failed: number
}

/** 合成进度 */
export interface SynthesisProgress {
    book_id: number
    status: 'idle' | 'synthesizing' | 'completed' | 'completed_with_errors' | 'in_progress'
    progress: number
    total_paragraphs: number
    pending: number
    processing: number
    completed: number
    failed: number
}

/** 导出响应 */
export interface ExportResponse {
    success: boolean
    message: string
    output_dir?: string
    total_segments: number
    success_count: number
    fail_count: number
}

/** 导出文件组 */
export interface ExportFile {
    name: string
    wav: string
    lrc: string | null
}

/** 电子书文件 */
export interface EbookFile {
    name: string
    size: number
    format: string
}

// ========== API 函数 ==========

/** 通用请求函数 */
async function request<T>(url: string, options?: RequestInit): Promise<T> {
    const res = await fetch(`${API_BASE}${url}`, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options?.headers,
        },
    })

    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: '请求失败' }))
        throw new Error(error.detail || `请求失败: ${res.status}`)
    }

    return res.json()
}

// ========== 书籍管理 ==========

/** 获取书籍列表 */
export async function getBooks(): Promise<Book[]> {
    return request<Book[]>('/books')
}

/** 获取书籍详情 */
export async function getBook(bookId: number): Promise<Book & { chapters: Chapter[] }> {
    return request<Book & { chapters: Chapter[] }>(`/books/${bookId}`)
}

/** 删除书籍 */
export async function deleteBook(bookId: number): Promise<{ success: boolean; message: string }> {
    return request<{ success: boolean; message: string }>(`/books/${bookId}`, {
        method: 'DELETE',
    })
}

/** 获取书籍章节 */
export async function getBookChapters(bookId: number): Promise<Chapter[]> {
    return request<Chapter[]>(`/books/${bookId}/chapters`)
}

/** 获取书籍段落 */
export async function getBookParagraphs(bookId: number): Promise<Paragraph[]> {
    return request<Paragraph[]>(`/books/${bookId}/paragraphs`)
}

/** 获取章节段落 */
export async function getChapterParagraphs(chapterId: number): Promise<Paragraph[]> {
    return request<Paragraph[]>(`/books/chapters/${chapterId}/paragraphs`)
}

// ========== 文件上传 ==========

/** 上传电子书文件 */
export async function uploadBook(file: File): Promise<UploadResponse> {
    const formData = new FormData()
    formData.append('file', file)

    const res = await fetch(`${API_BASE}/books/upload`, {
        method: 'POST',
        body: formData,
    })

    return res.json()
}

/** 获取电子书文件列表 */
export async function getEbookFiles(): Promise<{ files: EbookFile[] }> {
    return request<{ files: EbookFile[] }>('/books/files')
}

/** 解析已存在的电子书 */
export async function parseExistingBook(filename: string): Promise<UploadResponse> {
    return request<UploadResponse>(`/books/parse/${encodeURIComponent(filename)}`, {
        method: 'POST',
    })
}

// ========== TTS 语音合成 ==========

/** 获取可用语音列表 */
export async function getVoices(): Promise<VoiceInfo[]> {
    return request<VoiceInfo[]>('/voices')
}

/** 合成书籍语音 */
export async function synthesizeBook(bookId: number, voice?: string): Promise<SynthesizeResponse> {
    const url = voice
        ? `/books/${bookId}/synthesize?voice=${encodeURIComponent(voice)}`
        : `/books/${bookId}/synthesize`

    return request<SynthesizeResponse>(url, { method: 'POST' })
}

/** 获取合成进度 */
export async function getSynthesisProgress(bookId: number): Promise<SynthesisProgress> {
    return request<SynthesisProgress>(`/books/${bookId}/progress`)
}

// ========== 导出功能 ==========

/** 导出书籍 (异步) */
export async function exportBook(bookId: number): Promise<ExportResponse> {
    return request<ExportResponse>(`/books/${bookId}/export`, { method: 'POST' })
}

/** 导出书籍 (同步) */
export async function exportBookSync(bookId: number): Promise<ExportResponse> {
    return request<ExportResponse>(`/books/${bookId}/export/sync`, { method: 'POST' })
}

/** 获取导出下载链接 */
export function getExportDownloadUrl(bookId: number): string {
    return `${API_BASE}/books/${bookId}/export/download`
}

/** 获取导出文件列表 */
export async function getExportFiles(bookId: number): Promise<{ files: ExportFile[] }> {
    return request<{ files: ExportFile[] }>(`/books/${bookId}/export/files`)
}

/** 获取段落音频 URL */
export function getAudioUrl(bookId: number, paragraphId: number): string {
    return `${API_BASE}/audio/${bookId}/${paragraphId}`
}

// ========== 健康检查 ==========

/** 检查后端服务状态 */
export async function checkHealth(): Promise<{ status: string }> {
    const res = await fetch('/health')
    return res.json()
}
