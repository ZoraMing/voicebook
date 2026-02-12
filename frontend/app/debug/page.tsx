'use client'

import ApiTester from '@/components/debug/ApiTester'
import StatusMonitor from '@/components/debug/StatusMonitor'

/**
 * 调试面板页面
 */
export default function DebugPage() {
    return (
        <div className="container">
            <div className="header">
                <h1>🛠️ 调试面板</h1>
                <p className="subtitle">系统状态监控与 API 调试工具</p>
            </div>

            <div className="grid grid-cols-2 gap-6">
                <div className="col-span-2">
                    <StatusMonitor />
                </div>
                <div className="col-span-2">
                    <ApiTester />
                </div>
            </div>

            <div className="info-card">
                <h3>ℹ️ 系统信息</h3>
                <p>Frontend: Next.js 14 + React 18</p>
                <p>Backend: FastAPI + SQLite + edge-tts</p>
                <p>Environment: Development</p>
            </div>

            <style jsx>{`
        .header {
          margin-bottom: var(--space-8);
        }
        
        .subtitle {
          color: var(--color-text-secondary);
        }
        
        .col-span-2 {
          grid-column: span 2;
        }
        
        .info-card {
          margin-top: var(--space-8);
          padding: var(--space-6);
          background: var(--color-bg-secondary);
          border-radius: var(--radius-lg);
          color: var(--color-text-secondary);
          font-size: 0.875rem;
        }
        
        .info-card h3 {
          margin-bottom: var(--space-2);
          color: var(--color-text);
        }
      `}</style>
        </div>
    )
}
