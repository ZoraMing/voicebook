'use client'

import { useState, useEffect } from 'react'
import { getBooks, type Book } from '@/lib/api'

/**
 * 状态监控组件
 * 显示所有书籍的 TTS 合成状态概览
 */
export default function StatusMonitor() {
    const [books, setBooks] = useState<Book[]>([])
    const [loading, setLoading] = useState(false)

    const loadData = async () => {
        try {
            setLoading(true)
            const data = await getBooks()
            setBooks(data)
        } catch (e) {
            console.error(e)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        loadData()
        // 轮询更新
        const timer = setInterval(loadData, 5000)
        return () => clearInterval(timer)
    }, [])

    return (
        <div className="card debug-card">
            <div className="card-header">
                <h3>📊 任务监控</h3>
                <button className="btn btn-sm btn-secondary" onClick={loadData} disabled={loading}>
                    {loading ? '刷新中...' : '刷新'}
                </button>
            </div>

            <div className="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>书籍名称</th>
                            <th>总段落</th>
                            <th>进度</th>
                            <th>耗时</th>
                            <th>状态</th>
                        </tr>
                    </thead>
                    <tbody>
                        {books.map(book => (
                            <tr key={book.id}>
                                <td>{book.id}</td>
                                <td className="truncate" title={book.title}>{book.title}</td>
                                <td>{book.total_paragraphs}</td>
                                <td>
                                    <div className="progress-mini">
                                        <div
                                            className="progress-bar"
                                            style={{ width: `${book.tts_progress}%` }}
                                        />
                                    </div>
                                    <span className="text-xs">{book.tts_progress.toFixed(1)}%</span>
                                </td>
                                <td>{(book.total_duration_ms / 1000 / 60).toFixed(1)}m</td>
                                <td>
                                    <span className={`status-dot ${book.tts_progress >= 100 ? 'done' : book.tts_progress > 0 ? 'active' : 'idle'}`} />
                                    {book.tts_progress >= 100 ? '完成' : book.tts_progress > 0 ? '进行中' : '等待'}
                                </td>
                            </tr>
                        ))}
                        {books.length === 0 && (
                            <tr>
                                <td colSpan={6} className="text-center">暂无数据</td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            <style jsx>{`
        .debug-card {
          margin-bottom: var(--space-6);
        }
        
        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: var(--space-4);
        }
        
        .table-container {
          overflow-x: auto;
        }
        
        table {
          width: 100%;
          border-collapse: collapse;
          font-size: 0.875rem;
        }
        
        th, td {
          padding: var(--space-2) var(--space-3);
          text-align: left;
          border-bottom: 1px solid var(--color-border);
        }
        
        th {
          font-weight: 500;
          color: var(--color-text-secondary);
          background: var(--color-bg-secondary);
        }
        
        .truncate {
          max-width: 200px;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
        
        .progress-mini {
          width: 80px;
          height: 4px;
          background: var(--color-bg-secondary);
          border-radius: var(--radius-full);
          margin-bottom: 2px;
          display: inline-block;
          margin-right: var(--space-2);
          vertical-align: middle;
        }
        
        .text-xs {
          font-size: 0.75rem;
          color: var(--color-text-secondary);
        }
        
        .status-dot {
          display: inline-block;
          width: 8px;
          height: 8px;
          border-radius: 50%;
          margin-right: var(--space-2);
        }
        
        .status-dot.done { background-color: var(--color-success); }
        .status-dot.active { background-color: var(--color-primary); }
        .status-dot.idle { background-color: var(--color-text-muted); }
        
        .text-center { text-align: center; color: var(--color-text-muted); }
        
        .btn-sm { padding: 2px 8px; font-size: 0.75rem; }
      `}</style>
        </div>
    )
}
