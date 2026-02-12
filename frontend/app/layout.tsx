import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: '🎙️ 有声书制作系统',
  description: '电子书转有声书，支持 PDF/EPUB，使用 edge-tts 语音合成',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body>
        {/* 导航栏 */}
        <nav className="navbar">
          <div className="container flex items-center justify-between">
            <a href="/" className="logo">
              <span className="logo-icon">🎙️</span>
              <span className="logo-text">有声书制作系统</span>
            </a>
            <div className="nav-links">
              <a href="/" className="nav-link">书籍列表</a>
              <a href="/debug" className="nav-link nav-link-debug">调试面板</a>
            </div>
          </div>
        </nav>

        {/* 主内容 */}
        <main className="main-content">
          {children}
        </main>

        {/* 页脚 */}
        <footer className="footer">
          <div className="container">
            <p>有声书制作系统 v2.0 · 使用 Next.js + FastAPI 构建</p>
          </div>
        </footer>


      </body>
    </html>
  )
}
