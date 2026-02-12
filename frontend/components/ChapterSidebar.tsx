'use client'

import React from 'react'
import type { Chapter } from '@/lib/api'

interface ChapterSidebarProps {
  chapters: Chapter[]
  currentChapterId: number | null
  onSelectChapter: (id: number) => void
  onToggle: () => void
  isOpen: boolean
}

export default function ChapterSidebar({
  chapters,
  currentChapterId,
  onSelectChapter,
  onToggle,
  isOpen
}: ChapterSidebarProps) {
  return (
    <>
      {/* 遮罩层 (移动端) */}
      <div 
        className={`sidebar-overlay ${isOpen ? 'open' : ''}`}
        onClick={onToggle}
      />

      {/* 侧边栏 */}
      <div className={`sidebar ${isOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <h3>📑 目录</h3>
          <button className="btn btn-icon close-btn" onClick={onToggle}>✕</button>
        </div>
        
        <div className="chapter-list">
          <div 
            className={`chapter-item ${currentChapterId === null ? 'active' : ''}`}
            onClick={() => onSelectChapter(-1)} // -1 表示全部
          >
            <span className="chapter-index">ALL</span>
            <span className="chapter-title">全部章节</span>
          </div>
          
          {chapters.map((chapter) => (
            <div
              key={chapter.id}
              className={`chapter-item ${currentChapterId === chapter.id ? 'active' : ''}`}
              onClick={() => onSelectChapter(chapter.id)}
            >
              <span className="chapter-index">{(chapter.chapter_index + 1).toString().padStart(2, '0')}</span>
              <span className="chapter-title" title={chapter.title}>
                {chapter.title || `第 ${chapter.chapter_index + 1} 章`}
              </span>
              <span className="chapter-count">{chapter.total_paragraphs}</span>
            </div>
          ))}
        </div>
      </div>

      <style jsx>{`
        .sidebar {
          position: fixed;
          top: 0;
          left: 0;
          bottom: 0;
          width: 280px;
          background: white;
          border-right: 1px solid var(--color-border);
          z-index: 50;
          transform: translateX(-100%);
          transition: transform 0.3s ease;
          display: flex;
          flex-direction: column;
        }

        .sidebar.open {
          transform: translateX(0);
        }

        /* 桌面端默认显示(如果布局需要，这里暂时做成抽屉式，后续在page布局中调整为固定) */
        @media (min-width: 1024px) {
          .sidebar {
            position: sticky;
            top: 73px; /* Navbar height + border */
            height: calc(100vh - 73px);
            transform: none;
            width: 300px;
            flex-shrink: 0;
            z-index: 10;
          }
          
          .close-btn {
            display: none;
          }
        }

        .sidebar-overlay {
          position: fixed;
          inset: 0;
          background: rgba(0, 0, 0, 0.5);
          z-index: 40;
          opacity: 0;
          pointer-events: none;
          transition: opacity 0.3s;
        }

        .sidebar-overlay.open {
          opacity: 1;
          pointer-events: auto;
        }
        
        @media (min-width: 1024px) {
          .sidebar-overlay { display: none; }
        }

        .sidebar-header {
          padding: var(--space-4);
          border-bottom: 1px solid var(--color-border);
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .chapter-list {
          flex: 1;
          overflow-y: auto;
          padding: var(--space-2);
        }

        .chapter-item {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          padding: var(--space-3) var(--space-2);
          border-radius: var(--radius-md);
          cursor: pointer;
          transition: background 0.2s;
          color: var(--color-text-secondary);
        }

        .chapter-item:hover {
          background: var(--color-bg-hover);
          color: var(--color-text);
        }

        .chapter-item.active {
          background: #EFF6FF; /* blue-50 */
          color: var(--color-primary);
        }

        .chapter-index {
          font-family: var(--font-mono);
          font-size: 0.75rem;
          color: var(--color-text-muted);
          min-width: 24px;
        }
        
        .chapter-item.active .chapter-index {
          color: var(--color-primary);
        }

        .chapter-title {
          flex: 1;
          font-size: 0.875rem;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
        
        .chapter-count {
          font-size: 0.75rem;
          color: var(--color-text-muted);
          background: var(--color-bg-secondary);
          padding: 2px 6px;
          border-radius: var(--radius-full);
        }
      `}</style>
    </>
  )
}
