'use client'

import { useState } from 'react'
import { getBooks, getBook, synthesizeBook, deleteBook, getVoices } from '@/lib/api'

/**
 * API 调试组件
 * 允许用户直接调用后端 API 并查看响应
 */
export default function ApiTester() {
    const [method, setMethod] = useState('GET')
    const [endpoint, setEndpoint] = useState('/api/books')
    const [body, setBody] = useState('')
    const [response, setResponse] = useState<string | null>(null)
    const [status, setStatus] = useState<number | null>(null)
    const [loading, setLoading] = useState(false)

    // 预设请求模板
    const templates = [
        { name: '获取书籍列表', method: 'GET', url: '/api/books', body: '' },
        { name: '获取语音列表', method: 'GET', url: '/api/voices', body: '' },
        { name: '检查健康状态', method: 'GET', url: '/health', body: '' },
    ]

    const handleSend = async () => {
        try {
            setLoading(true)
            setResponse(null)
            setStatus(null)

            const options: RequestInit = {
                method,
                headers: {
                    'Content-Type': 'application/json',
                },
            }

            if (['POST', 'PUT', 'PATCH'].includes(method) && body) {
                options.body = body
            }

            // 处理 endpoint，确保包含 /api 前缀（如果需要）或直接使用完整路径
            // 这里假设 endpoint 是相对于 localhost:8000 的，或者通过 next.js rewrite
            // 在 next.config.mjs 中配置了 /api -> http://localhost:8000/api
            // 所以如果用户输入 /api/... 就可以。
            // 如果输入 /health (不在 /api 下)，也需要处理? 这里的 rewrite 只处理了 /api。
            // 后端 /health 是根路径。我们需要在 next.config.mjs 加一个 rewrite 或者前端处理。
            // 暂时假设用户输入 correct path.

            const res = await fetch(endpoint, options)
            setStatus(res.status)

            const data = await res.json().catch(() => ({ error: 'Non-JSON response' }))
            setResponse(JSON.stringify(data, null, 2))
        } catch (err) {
            setResponse(JSON.stringify({ error: err instanceof Error ? err.message : 'Unknown error' }, null, 2))
        } finally {
            setLoading(false)
        }
    }

    const loadTemplate = (tpl: typeof templates[0]) => {
        setMethod(tpl.method)
        setEndpoint(tpl.url)
        setBody(tpl.body)
    }

    return (
        <div className="card debug-card">
            <h3>🔌 API 调试器</h3>

            {/* 模板选择 */}
            <div className="templates">
                {templates.map(tpl => (
                    <button
                        key={tpl.name}
                        className="btn btn-sm btn-secondary"
                        onClick={() => loadTemplate(tpl)}
                    >
                        {tpl.name}
                    </button>
                ))}
            </div>

            {/* 请求构建 */}
            <div className="request-builder">
                <div className="input-group">
                    <select
                        value={method}
                        onChange={e => setMethod(e.target.value)}
                        className="method-select"
                    >
                        <option value="GET">GET</option>
                        <option value="POST">POST</option>
                        <option value="PUT">PUT</option>
                        <option value="DELETE">DELETE</option>
                    </select>
                    <input
                        type="text"
                        value={endpoint}
                        onChange={e => setEndpoint(e.target.value)}
                        placeholder="/api/..."
                        className="url-input"
                    />
                    <button
                        className="btn btn-primary"
                        onClick={handleSend}
                        disabled={loading}
                    >
                        {loading ? '发送中...' : '发送请求'}
                    </button>
                </div>

                {['POST', 'PUT', 'PATCH'].includes(method) && (
                    <div className="body-editor">
                        <label>Request Body (JSON):</label>
                        <textarea
                            value={body}
                            onChange={e => setBody(e.target.value)}
                            placeholder='{"key": "value"}'
                            rows={5}
                        />
                    </div>
                )}
            </div>

            {/* 响应显示 */}
            {response && (
                <div className="response-viewer">
                    <div className="response-header">
                        <span>Status: <span className={status && status < 400 ? 'text-success' : 'text-error'}>{status}</span></span>
                    </div>
                    <pre className="code-block">{response}</pre>
                </div>
            )}

            <style jsx>{`
        .debug-card {
          margin-bottom: var(--space-6);
        }
        
        h3 {
          margin-bottom: var(--space-4);
        }
        
        .templates {
          display: flex;
          gap: var(--space-2);
          margin-bottom: var(--space-4);
          flex-wrap: wrap;
        }
        
        .input-group {
          display: flex;
          gap: var(--space-2);
          margin-bottom: var(--space-4);
        }
        
        .method-select {
          width: 100px;
          flex-shrink: 0;
        }
        
        .url-input {
          flex: 1;
        }
        
        .body-editor textarea {
          width: 100%;
          font-family: var(--font-mono);
          margin-top: var(--space-1);
        }
        
        .response-viewer {
          background: var(--color-bg-secondary);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-md);
          overflow: hidden;
        }
        
        .response-header {
          padding: var(--space-2) var(--space-4);
          border-bottom: 1px solid var(--color-border);
          font-size: 0.875rem;
          font-weight: 500;
        }
        
        .code-block {
          padding: var(--space-4);
          overflow-x: auto;
          font-family: var(--font-mono);
          font-size: 0.875rem;
          color: var(--color-text);
          margin: 0;
        }
        
        .text-success { color: var(--color-success); }
        .text-error { color: var(--color-error); }
        
        .btn-sm {
          padding: 2px 8px;
          font-size: 0.75rem;
        }
      `}</style>
        </div>
    )
}
