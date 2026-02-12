'use client'

import { useState, useEffect, useRef, useMemo } from 'react'
import { useParams } from 'next/navigation'
import {
    getBook,
    getBookParagraphs,
    synthesizeBook,
    getVoices,
    getAudioUrl,
    type Book,
    type Chapter,
    type Paragraph,
    type VoiceInfo,
    type ExportFile,
    exportBook,
    getExportDownloadUrl,
    getExportFiles,
} from '@/lib/api'
import ChapterSidebar from '@/components/ChapterSidebar'
import PlayerControl from '@/components/PlayerControl'
import ExportPlayer from '@/components/ExportPlayer'

/**
 * 书籍详情页 - 阅读和播放
 */
export default function BookDetailPage() {
    const params = useParams()
    const bookId = Number(params.id)

    const [book, setBook] = useState<(Book & { chapters: Chapter[] }) | null>(null)
    const [paragraphs, setParagraphs] = useState<Paragraph[]>([])
    const [voices, setVoices] = useState<VoiceInfo[]>([])
    const [selectedVoice, setSelectedVoice] = useState('zh-CN-XiaoxiaoNeural')
    const [exportFiles, setExportFiles] = useState<ExportFile[]>([])
    const [loading, setLoading] = useState(true)
    const [synthesizing, setSynthesizing] = useState(false)
    const [exporting, setExporting] = useState(false)
    const [exportMessage, setExportMessage] = useState<string | null>(null)
    const [error, setError] = useState<string | null>(null)

    // 侧边栏状态
    const [isSidebarOpen, setIsSidebarOpen] = useState(false)
    const [currentChapterId, setCurrentChapterId] = useState<number | null>(null) // null for all initially? Or -1 for all

    // 播放状态
    const [currentParagraphId, setCurrentParagraphId] = useState<number | null>(null)
    const [isPlaying, setIsPlaying] = useState(false)
    const [playbackRate, setPlaybackRate] = useState(1.0)
    const audioRef = useRef<HTMLAudioElement | null>(null)

    // 筛选 - 仅用于显示过滤，播放逻辑基于全部段落
    const [statusFilter, setStatusFilter] = useState<string>('all')

    // 加载数据
    useEffect(() => {
        const loadData = async () => {
            try {
                setLoading(true)
                const [bookData, paragraphsData, voicesData, exportFilesData] = await Promise.all([
                    getBook(bookId),
                    getBookParagraphs(bookId),
                    getVoices(),
                    getExportFiles(bookId).catch(() => ({ files: [] })),
                ])
                setBook(bookData)
                setParagraphs(paragraphsData)
                setVoices(voicesData)
                setExportFiles(exportFilesData.files)
                if (bookData.tts_voice) {
                    setSelectedVoice(bookData.tts_voice)
                }
            } catch (err) {
                setError(err instanceof Error ? err.message : '加载失败')
            } finally {
                setLoading(false)
            }
        }
        loadData()
    }, [bookId])

    // 监听当前段落变化，更新章节高亮和滚动
    useEffect(() => {
        if (currentParagraphId) {
            const p = paragraphs.find(p => p.id === currentParagraphId)
            if (p && p.chapter_id !== currentChapterId && currentChapterId !== -1) {
                // 自动切换到当前播放章节（可选，这里暂不强制切换视图，只做高亮）
                // setCurrentChapterId(p.chapter_id) 
            }

            // 滚动到当前段落
            const el = document.getElementById(`p-${currentParagraphId}`)
            if (el) {
                el.scrollIntoView({ behavior: 'smooth', block: 'center' })
            }
        }
    }, [currentParagraphId, paragraphs]) // removed currentChapterId dependent logic to avoid jump

    // 初始化音频对象
    useEffect(() => {
        const audio = new Audio()
        audioRef.current = audio

        // 更新倍速
        audio.playbackRate = playbackRate

        const handleEnded = () => {
            setIsPlaying(false)
            playNext()
        }

        const handleError = () => {
            setIsPlaying(false)
            setError('音频播放失败或文件不存在')
        }

        audio.addEventListener('ended', handleEnded)
        audio.addEventListener('error', handleError)

        return () => {
            audio.pause()
            audio.removeEventListener('ended', handleEnded)
            audio.removeEventListener('error', handleError)
        }
    }, [])

    // 监听倍速变化
    useEffect(() => {
        if (audioRef.current) {
            audioRef.current.playbackRate = playbackRate
        }
    }, [playbackRate])

    // 播放指定段落
    const playParagraph = (paragraph: Paragraph) => {
        if (paragraph.tts_status !== 'completed') {
            setError('该段落尚未合成音频')
            return
        }

        if (!audioRef.current) return

        const audio = audioRef.current
        const url = getAudioUrl(bookId, paragraph.id)

        // 如果是同一首歌，仅切换播放/暂停
        if (currentParagraphId === paragraph.id && audio.src.includes(url)) {
            if (audio.paused) {
                audio.play()
                setIsPlaying(true)
            } else {
                audio.pause()
                setIsPlaying(false)
            }
            return
        }

        // 切歌
        audio.src = url
        audio.playbackRate = playbackRate
        audio.play().then(() => {
            setIsPlaying(true)
            setCurrentParagraphId(paragraph.id)
        }).catch(e => {
            console.error("Play error:", e)
            setIsPlaying(false)
            setError('播放失败')
        })
    }

    // 查找下一个可播放段落
    const playNext = () => {
        if (!currentParagraphId) return

        // 在所有段落中查找当前索引
        const currentIndex = paragraphs.findIndex(p => p.id === currentParagraphId)
        if (currentIndex === -1) return

        // 寻找下一个已完成的段落
        let nextIndex = currentIndex + 1
        while (nextIndex < paragraphs.length) {
            const nextP = paragraphs[nextIndex]
            if (nextP.tts_status === 'completed') {
                playParagraph(nextP)
                return
            }
            nextIndex++
        }
        // 没有更多可播放段落
        setIsPlaying(false)
    }

    // 查找上一个可播放段落
    const playPrev = () => {
        if (!currentParagraphId) return

        const currentIndex = paragraphs.findIndex(p => p.id === currentParagraphId)
        if (currentIndex === -1) return

        let prevIndex = currentIndex - 1
        while (prevIndex >= 0) {
            const prevP = paragraphs[prevIndex]
            if (prevP.tts_status === 'completed') {
                playParagraph(prevP)
                return
            }
            prevIndex--
        }
    }

    const togglePlay = () => {
        if (!audioRef.current) return
        if (isPlaying) {
            audioRef.current.pause()
            setIsPlaying(false)
        } else if (currentParagraphId) {
            audioRef.current.play()
            setIsPlaying(true)
        } else if (filteredParagraphs.length > 0) {
            // 如果没有当前段落，播放列表第一个
            const p = filteredParagraphs.find(p => p.tts_status === 'completed')
            if (p) playParagraph(p)
        }
    }

    // 开始合成
    const handleSynthesize = async () => {
        try {
            setSynthesizing(true)
            setError(null)
            const result = await synthesizeBook(bookId, selectedVoice)
            if (result.success) {
                const updatedParagraphs = await getBookParagraphs(bookId)
                setParagraphs(updatedParagraphs)
            } else {
                setError(result.message)
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : '合成失败')
        } finally {
            setSynthesizing(false)
        }
    }

    // 导出书籍
    const handleExport = async () => {
        try {
            setExporting(true)
            setExportMessage(null)
            setError(null)

            const result = await exportBook(bookId)

            if (result.success) {
                setExportMessage(`导出成功！共 ${result.total_segments} 个音频段。请点击下方下载。`)
                // 刷新导出文件列表
                getExportFiles(bookId).then(data => setExportFiles(data.files))
            } else {
                setError(result.message)
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : '导出失败')
        } finally {
            setExporting(false)
        }
    }

    // 章节跳转
    const handleChapterSelect = (chapterId: number) => {
        setCurrentChapterId(chapterId)
        setIsSidebarOpen(false) // Mobile auto close

        // 找到该章节第一段并滚动
        if (chapterId !== -1) {
            const firstP = paragraphs.find(p => p.chapter_id === chapterId)
            if (firstP) {
                const el = document.getElementById(`p-${firstP.id}`)
                if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
            }
        } else {
            window.scrollTo({ top: 0, behavior: 'smooth' })
        }
    }

    // 过滤显示的段落
    const filteredParagraphs = useMemo(() => {
        return paragraphs.filter(p => {
            if (currentChapterId !== null && currentChapterId !== -1 && p.chapter_id !== currentChapterId) return false
            if (statusFilter !== 'all' && p.tts_status !== statusFilter) return false
            return true
        })
    }, [paragraphs, currentChapterId, statusFilter])

    // 当前播放的段落对象
    const currentParagraph = useMemo(() =>
        paragraphs.find(p => p.id === currentParagraphId) || null
        , [paragraphs, currentParagraphId])

    // 统计
    const stats = {
        total: paragraphs.length,
        completed: paragraphs.filter(p => p.tts_status === 'completed').length,
        pending: paragraphs.filter(p => p.tts_status === 'pending').length,
        failed: paragraphs.filter(p => p.tts_status === 'failed').length,
    }

    if (loading) {
        return (
            <div className="container loading-state">
                <div className="spinner"></div>
                <p>加载中...</p>
            </div>
        )
    }

    if (!book) return <div className="container error-state"><h2>书籍不存在</h2></div>

    return (
        <div className="book-page-layout">
            {/* 侧边栏 */}
            <ChapterSidebar
                chapters={book.chapters}
                currentChapterId={currentChapterId}
                onSelectChapter={handleChapterSelect}
                onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
                isOpen={isSidebarOpen}
            />

            <div className="main-content-area">
                <div className="container">
                    {/* 顶部栏 (Mobile Sidebar Toggle) */}
                    <div className="top-bar lg-hidden">
                        <button className="btn btn-icon" onClick={() => setIsSidebarOpen(true)}>
                            ☰ 目录
                        </button>
                    </div>

                    {/* 书籍信息头 */}
                    <div className="book-header">
                        <div className="book-info-row">
                            <div className="book-cover-small">📕</div>
                            <div>
                                <h1>{book.title}</h1>
                                <p className="author">👤 {book.author}</p>
                            </div>
                        </div>

                        {/* 进度条 */}
                        <div className="progress-mini-row">
                            <div className="progress">
                                <div className="progress-bar" style={{ width: `${(stats.completed / stats.total) * 100}%` }} />
                            </div>
                            <span className="text-xs text-muted">
                                {stats.completed}/{stats.total} 段
                            </span>
                        </div>

                        {/* 控制栏 */}
                        <div className="header-controls">
                            <div className="synthesis-control">
                                <select
                                    value={selectedVoice}
                                    onChange={(e) => setSelectedVoice(e.target.value)}
                                    disabled={synthesizing}
                                >
                                    {voices.map(v => (
                                        <option key={v.id} value={v.voice}>
                                            {v.name} ({v.gender === 'female' ? '女' : '男'})
                                        </option>
                                    ))}
                                </select>
                                <button
                                    className="btn btn-primary"
                                    onClick={handleSynthesize}
                                    disabled={synthesizing || exporting}
                                >
                                    {synthesizing ? '合成中...' : '🎙️ 全书合成'}
                                </button>
                                <button
                                    className="btn btn-secondary"
                                    onClick={handleExport}
                                    disabled={synthesizing || exporting}
                                    title="导出为 WAV + LRC"
                                >
                                    {exporting ? '导出中...' : '📦 导出有声书'}
                                </button>
                                {exportMessage && (
                                    <a
                                        href={getExportDownloadUrl(bookId)}
                                        className="btn btn-success"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                    >
                                        ⬇️ 下载
                                    </a>
                                )}
                            </div>

                            <select
                                value={statusFilter}
                                onChange={(e) => setStatusFilter(e.target.value)}
                                className="status-filter"
                            >
                                <option value="all">全部显示</option>
                                <option value="pending">只看未完成</option>
                                <option value="completed">只看已完成</option>
                                <option value="failed">只看失败</option>
                            </select>
                        </div>
                    </div>

                    {/* 成功提示 */}
                    {exportMessage && (
                        <div className="success-banner">
                            <span>✅ {exportMessage}</span>
                            <button onClick={() => setExportMessage(null)}>✕</button>
                        </div>
                    )}

                    {/* 错误提示 */}
                    {error && (
                        <div className="error-banner">
                            <span>⚠️ {error}</span>
                            <button onClick={() => setError(null)}>✕</button>
                        </div>
                    )}

                    {/* 段落列表 */}
                    <div className="paragraphs-list">
                        {filteredParagraphs.map((p) => (
                            <div
                                id={`p-${p.id}`}
                                key={p.id}
                                className={`paragraph-item ${currentParagraphId === p.id ? 'active' : ''} ${p.tts_status}`}
                                onClick={() => p.tts_status === 'completed' && playParagraph(p)}
                            >
                                <div className="paragraph-main">
                                    <span className="pid">#{p.paragraph_index + 1}</span>
                                    <p>{p.content}</p>
                                </div>
                                <div className="paragraph-status">
                                    {p.tts_status === 'completed' && currentParagraphId === p.id && isPlaying && <span className="playing-icon">🔊</span>}
                                    {p.tts_status === 'failed' && <span className="error-icon" title="合成失败">❌</span>}
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* 底部留白给播放条 */}
                    <div style={{ height: '100px' }}></div>

                    {/* 导出预览播放器 */}
                    {exportFiles.length > 0 && (
                        <div className="container">
                            <ExportPlayer files={exportFiles} />
                            <div style={{ height: '50px' }}></div>
                        </div>
                    )}
                </div>
            </div>

            {/* 底部播放控制条 */}
            <PlayerControl
                isPlaying={isPlaying}
                onTogglePlay={togglePlay}
                onPrev={playPrev}
                onNext={playNext}
                playbackRate={playbackRate}
                onRateChange={setPlaybackRate}
                currentParagraph={currentParagraph}
            />

            <style jsx>{`
        .book-page-layout {
            display: flex;
            min-height: 100vh;
        }

        .main-content-area {
            flex: 1;
            background: #FAFAFA;
        }

        .lg-hidden {
            display: block;
        }
        @media (min-width: 1024px) {
            .lg-hidden { display: none; }
        }

        .top-bar {
            padding: var(--space-4) 0;
            border-bottom: 1px solid var(--color-border);
            margin-bottom: var(--space-4);
        }

        .book-header {
            background: white;
            padding: var(--space-6);
            border-radius: var(--radius-lg);
            border: 1px solid var(--color-border);
            margin-bottom: var(--space-6);
        }

        .book-info-row {
            display: flex;
            gap: var(--space-4);
            margin-bottom: var(--space-4);
        }

        .book-cover-small {
            width: 60px;
            height: 80px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: var(--radius-md);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
        }

        .book-header h1 {
            font-size: 1.5rem;
            margin-bottom: var(--space-1);
        }

        .header-controls {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: var(--space-4);
            margin-top: var(--space-4);
            padding-top: var(--space-4);
            border-top: 1px solid var(--color-border-light);
        }

        .synthesis-control {
            display: flex;
            gap: var(--space-2);
        }

        .progress-mini-row {
            display: flex;
            align-items: center;
            gap: var(--space-3);
        }

        .text-muted { color: var(--color-text-muted); }

        .paragraphs-list {
            display: flex;
            flex-direction: column;
            gap: var(--space-3);
        }

        .paragraph-item {
            display: flex;
            background: white;
            padding: var(--space-4);
            border-radius: var(--radius-md);
            border: 1px solid transparent;
            cursor: default;
            transition: all 0.2s;
        }
        
        .paragraph-item.completed {
            cursor: pointer;
        }
        
        .paragraph-item:hover {
            box-shadow: var(--shadow-sm);
        }

        .paragraph-item.active {
            border-color: var(--color-primary);
            background: #EFF6FF;
            box-shadow: var(--shadow-md);
            transform: scale(1.01);
        }

        .paragraph-main {
            flex: 1;
            display: flex;
            gap: var(--space-3);
        }

        .pid {
            font-size: 0.75rem;
            color: var(--color-text-muted);
            min-width: 24px;
            padding-top: 4px;
        }

        .paragraph-content p {
            margin: 0;
            line-height: 1.8;
            color: var(--color-text);
        }

        .playing-icon {
            font-size: 1.25rem;
            animation: pulse 1s infinite;
        }
        
        .loading-state, .error-state {
            padding: var(--space-12);
            text-align: center;
        }
        
        .spinner {
            width: 32px;
            height: 32px;
            border: 3px solid var(--color-border);
            border-top-color: var(--color-primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto var(--space-4);
        }
        
        .error-banner {
            background: #FEF2F2;
            color: #991B1B;
            padding: var(--space-3);
            border-radius: var(--radius-md);
            display: flex;
            justify-content: space-between;
            margin-bottom: var(--space-4);
        }

        .success-banner {
            background: #ECFDF5;
            color: #065F46;
            padding: var(--space-3);
            border-radius: var(--radius-md);
            display: flex;
            justify-content: space-between;
            margin-bottom: var(--space-4);
        }

        .btn-secondary {
            background: white;
            border: 1px solid var(--color-border);
            color: var(--color-text);
        }
        
        .btn-secondary:hover:not(:disabled) {
            background: #F3F4F6;
        }

        .btn-success {
            background: #10B981;
            color: white;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }
        
        .btn-success:hover {
            background: #059669;
        }
      `}</style>
        </div>
    )
}
