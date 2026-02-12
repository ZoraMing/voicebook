'use client'

import React, { useEffect } from 'react'
import type { Paragraph } from '@/lib/api'

interface PlayerControlProps {
    isPlaying: boolean
    onTogglePlay: () => void
    onPrev: () => void
    onNext: () => void
    playbackRate: number
    onRateChange: (rate: number) => void
    currentParagraph: Paragraph | null
}

const PLAYBACK_RATES = [1, 1.1, 1.25, 1.5, 2, 3]

export default function PlayerControl({
    isPlaying,
    onTogglePlay,
    onPrev,
    onNext,
    playbackRate,
    onRateChange,
    currentParagraph
}: PlayerControlProps) {

    // 键盘快捷键
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return

            switch (e.code) {
                case 'Space':
                    e.preventDefault()
                    onTogglePlay()
                    break
                case 'ArrowLeft':
                    if (e.ctrlKey || e.metaKey) { // 避免与页面滚动冲突
                        e.preventDefault()
                        onPrev()
                    }
                    break
                case 'ArrowRight':
                    if (e.ctrlKey || e.metaKey) {
                        e.preventDefault()
                        onNext()
                    }
                    break
            }
        }

        window.addEventListener('keydown', handleKeyDown)
        return () => window.removeEventListener('keydown', handleKeyDown)
    }, [onTogglePlay, onPrev, onNext])

    if (!currentParagraph) return null

    return (
        <div className="player-bar">
            <div className="container player-content">

                {/* 当前播放信息 */}
                <div className="info-section">
                    <div className="now-playing-label">正在播放</div>
                    <div className="paragraph-preview" title={currentParagraph.content}>
                        {currentParagraph.content}
                    </div>
                </div>

                {/* 控制按钮 */}
                <div className="control-section">
                    <button className="btn btn-icon btn-round" onClick={onPrev} title="上一段 (Ctrl+Left)">
                        ⏮️
                    </button>

                    <button
                        className="btn btn-primary btn-play"
                        onClick={onTogglePlay}
                        title="播放/暂停 (Space)"
                    >
                        {isPlaying ? '⏸️' : '▶️'}
                    </button>

                    <button className="btn btn-icon btn-round" onClick={onNext} title="下一段 (Ctrl+Right)">
                        ⏭️
                    </button>
                </div>

                {/* 倍速选择 */}
                <div className="rate-section">
                    <div className="rate-selector">
                        <span className="rate-label">倍速</span>
                        <div className="rate-options">
                            {PLAYBACK_RATES.map(rate => (
                                <button
                                    key={rate}
                                    className={`rate-btn ${Math.abs(rate - playbackRate) < 0.01 ? 'active' : ''}`}
                                    onClick={() => onRateChange(rate)}
                                >
                                    {rate}x
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            <style jsx>{`
        .player-bar {
          position: fixed;
          bottom: 0;
          left: 0;
          right: 0;
          background: white;
          border-top: 1px solid var(--color-border);
          box-shadow: 0 -4px 6px -1px rgba(0, 0, 0, 0.05);
          z-index: 100;
          padding: var(--space-3) 0;
        }

        .player-content {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: var(--space-4);
        }

        .info-section {
          flex: 1;
          min-width: 0; /* Enable truncation */
          display: flex;
          flex-direction: column;
        }

        .now-playing-label {
          font-size: 0.75rem;
          color: var(--color-text-muted);
          margin-bottom: 2px;
        }

        .paragraph-preview {
          font-size: 0.875rem;
          font-weight: 500;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          color: var(--color-text);
        }

        .control-section {
          display: flex;
          align-items: center;
          gap: var(--space-4);
        }

        .btn-round {
          width: 40px;
          height: 40px;
          border-radius: 50%;
          border: 1px solid var(--color-border);
          display: flex;
          align-items: center;
          justify-content: center;
          background: white;
        }
        
        .btn-round:hover {
          background: var(--color-bg-hover);
          border-color: var(--color-primary);
        }

        .btn-play {
          width: 48px;
          height: 48px;
          border-radius: 50%;
          font-size: 1.25rem;
          padding: 0;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .rate-section {
          display: flex;
          align-items: center;
        }

        .rate-selector {
          display: flex;
          align-items: center;
          gap: var(--space-2);
          background: var(--color-bg-secondary);
          padding: 4px;
          border-radius: var(--radius-full);
        }

        .rate-label {
          font-size: 0.75rem;
          color: var(--color-text-secondary);
          padding-left: 8px;
          display: none; /* Mobile hidden */
        }
        
        @media (min-width: 768px) {
          .rate-label { display: block; }
        }

        .rate-options {
          display: flex;
        }

        .rate-btn {
          background: none;
          border: none;
          padding: 4px 8px;
          font-size: 0.75rem;
          border-radius: 12px;
          cursor: pointer;
          color: var(--color-text-secondary);
          min-width: 36px;
        }

        .rate-btn:hover {
          color: var(--color-text);
        }

        .rate-btn.active {
          background: white;
          color: var(--color-primary);
          box-shadow: 0 1px 2px rgba(0,0,0,0.1);
          font-weight: 600;
        }
        
        @media (max-width: 640px) {
          .player-content {
            flex-direction: column;
            gap: var(--space-3);
          }
          
          .info-section {
            width: 100%;
            text-align: center;
          }
          
          .rate-section {
            display: none; /* Mobile simplify */
          }
        }
      `}</style>
        </div>
    )
}
