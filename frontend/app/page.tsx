'use client'

import { useState, useEffect } from 'react'
import { getBooks, uploadBook, deleteBook, type Book } from '@/lib/api'

/**
 * 首页 - 书籍列表
 */
export default function HomePage() {
  const [books, setBooks] = useState<Book[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)

  // 加载书籍列表
  const loadBooks = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await getBooks()
      setBooks(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败')
    } finally {
      setLoading(false)
    }
  }

  // 初始加载
  useEffect(() => {
    loadBooks()
  }, [])

  // 处理文件上传
  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    try {
      setUploading(true)
      setError(null)
      const result = await uploadBook(file)
      if (result.success) {
        loadBooks() // 重新加载列表
      } else {
        setError(result.message)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '上传失败')
    } finally {
      setUploading(false)
      e.target.value = '' // 清空输入
    }
  }

  // 删除书籍
  const handleDelete = async (bookId: number) => {
    if (!confirm('确定要删除这本书吗？')) return

    try {
      await deleteBook(bookId)
      loadBooks()
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除失败')
    }
  }

  // 格式化时间
  const formatDuration = (ms: number) => {
    const seconds = Math.floor(ms / 1000)
    const minutes = Math.floor(seconds / 60)
    const hours = Math.floor(minutes / 60)

    if (hours > 0) {
      return `${hours}小时${minutes % 60}分钟`
    }
    return `${minutes}分钟`
  }

  return (
    <div className="container">
      {/* 页面标题 */}
      <div className="page-header">
        <div className="header-left">
          <h1>📚 我的书籍</h1>
          <p className="subtitle">共 {books.length} 本书籍</p>
        </div>
        <div className="header-actions">
          <label className="btn btn-primary upload-btn">
            <span>{uploading ? '上传中...' : '📤 上传电子书'}</span>
            <input
              type="file"
              accept=".pdf,.epub,.txt,.md"
              onChange={handleUpload}
              disabled={uploading}
              hidden
            />
          </label>
        </div>
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="error-banner">
          <span>⚠️ {error}</span>
          <button onClick={() => setError(null)}>✕</button>
        </div>
      )}

      {/* 加载状态 */}
      {loading ? (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>加载中...</p>
        </div>
      ) : books.length === 0 ? (
        /* 空状态 */
        <div className="empty-state">
          <div className="empty-icon">📖</div>
          <h2>还没有书籍</h2>
          <p>上传一本电子书开始制作有声书吧</p>
          <label className="btn btn-primary">
            <span>📤 上传电子书</span>
            <input
              type="file"
              accept=".pdf,.epub,.txt,.md"
              onChange={handleUpload}
              hidden
            />
          </label>
        </div>
      ) : (
        /* 书籍网格 */
        <div className="books-grid">
          {books.map((book) => (
            <div key={book.id} className="book-card">
              <div className="book-cover">
                <span className="book-emoji">📕</span>
              </div>
              <div className="book-info">
                <h3 className="book-title">{book.title}</h3>
                <p className="book-author">👤 {book.author}</p>
                <div className="book-meta">
                  <span>📄 {book.total_paragraphs} 段</span>
                  <span>📑 {book.total_chapters} 章</span>
                </div>

                {/* TTS 进度 */}
                <div className="tts-progress">
                  <div className="progress">
                    <div
                      className="progress-bar"
                      style={{ width: `${book.tts_progress}%` }}
                    />
                  </div>
                  <span className="progress-text">
                    {book.tts_progress.toFixed(0)}% 已合成
                  </span>
                </div>

                {/* 操作按钮 */}
                <div className="book-actions">
                  <a href={`/books/${book.id}`} className="btn btn-primary btn-sm">
                    查看详情
                  </a>
                  <button
                    className="btn btn-icon btn-sm"
                    onClick={() => handleDelete(book.id)}
                    title="删除"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <style jsx>{`
        .page-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: var(--space-8);
        }
        
        .header-left h1 {
          margin-bottom: var(--space-1);
        }
        
        .subtitle {
          color: var(--color-text-secondary);
          font-size: 0.875rem;
          margin: 0;
        }
        
        .upload-btn {
          min-width: 140px;
        }
        
        .error-banner {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: var(--space-3) var(--space-4);
          background: #FEE2E2;
          color: #991B1B;
          border-radius: var(--radius-md);
          margin-bottom: var(--space-4);
        }
        
        .error-banner button {
          background: none;
          border: none;
          cursor: pointer;
          color: inherit;
        }
        
        .loading-state,
        .empty-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: var(--space-12) 0;
          color: var(--color-text-secondary);
        }
        
        .spinner {
          width: 32px;
          height: 32px;
          border: 3px solid var(--color-border);
          border-top-color: var(--color-primary);
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin-bottom: var(--space-4);
        }
        
        .empty-icon {
          font-size: 4rem;
          margin-bottom: var(--space-4);
        }
        
        .empty-state h2 {
          margin-bottom: var(--space-2);
        }
        
        .empty-state p {
          margin-bottom: var(--space-6);
        }
        
        .books-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
          gap: var(--space-6);
        }
        
        .book-card {
          display: flex;
          background: white;
          border: 1px solid var(--color-border);
          border-radius: var(--radius-lg);
          overflow: hidden;
          transition: box-shadow 0.2s, transform 0.2s;
        }
        
        .book-card:hover {
          box-shadow: var(--shadow-md);
          transform: translateY(-2px);
        }
        
        .book-cover {
          width: 80px;
          min-height: 140px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }
        
        .book-emoji {
          font-size: 2rem;
        }
        
        .book-info {
          flex: 1;
          padding: var(--space-4);
          display: flex;
          flex-direction: column;
        }
        
        .book-title {
          font-size: 1rem;
          margin-bottom: var(--space-1);
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }
        
        .book-author {
          font-size: 0.875rem;
          color: var(--color-text-secondary);
          margin-bottom: var(--space-2);
        }
        
        .book-meta {
          display: flex;
          gap: var(--space-4);
          font-size: 0.75rem;
          color: var(--color-text-muted);
          margin-bottom: var(--space-3);
        }
        
        .tts-progress {
          margin-bottom: var(--space-3);
        }
        
        .progress-text {
          font-size: 0.75rem;
          color: var(--color-text-secondary);
          margin-top: var(--space-1);
          display: block;
        }
        
        .book-actions {
          display: flex;
          gap: var(--space-2);
          margin-top: auto;
        }
        
        .btn-sm {
          padding: var(--space-1) var(--space-3);
          font-size: 0.75rem;
        }
        
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  )
}
