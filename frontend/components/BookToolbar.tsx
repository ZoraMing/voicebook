import React from 'react'
import { VoiceInfo } from '@/lib/api'

interface BookToolbarProps {
    voices: VoiceInfo[]
    selectedVoice: string
    onVoiceChange: (voice: string) => void
    onSynthesize: () => void
    onExport: () => void
    isSynthesizing: boolean
    isExporting: boolean
    exportSuccess: boolean
    downloadUrl: string | null
    synthesisProgress?: {
        progress: number
        status: string
    }
}

export default function BookToolbar({
    voices,
    selectedVoice,
    onVoiceChange,
    onSynthesize,
    onExport,
    isSynthesizing,
    isExporting,
    exportSuccess,
    downloadUrl,
    synthesisProgress
}: BookToolbarProps) {

    // 格式化进度显示
    const getProgressLabel = () => {
        if (!synthesisProgress) return ''
        if (synthesisProgress.status === 'processing' || synthesisProgress.status === 'synthesizing') {
            return `合成中 ${synthesisProgress.progress}%`
        }
        return ''
    }

    return (
        <div className="book-toolbar card">
            <div className="toolbar-section">
                <div className="toolbar-group">
                    <label className="toolbar-label">🗣️ 语音选择</label>
                    <select
                        className="voice-select"
                        value={selectedVoice}
                        onChange={(e) => onVoiceChange(e.target.value)}
                        disabled={isSynthesizing}
                    >
                        {voices.map(v => (
                            <option key={v.id} value={v.voice}>
                                {v.name} ({v.gender === 'female' ? '女' : '男'})
                            </option>
                        ))}
                    </select>
                </div>

                <div className="toolbar-group">
                    <button
                        className={`btn ${isSynthesizing ? 'btn-secondary' : 'btn-primary'}`}
                        onClick={onSynthesize}
                        disabled={isSynthesizing || isExporting}
                    >
                        {isSynthesizing ? (
                            <>
                                <span className="spinner-sm"></span>
                                {getProgressLabel() || '正在合成...'}
                            </>
                        ) : (
                            '🎙️ 开始合成'
                        )}
                    </button>

                    {/* 分隔线 */}
                    <div className="divider"></div>

                    <button
                        className={`btn ${isExporting ? 'btn-secondary' : 'btn-secondary'}`}
                        onClick={onExport}
                        disabled={isSynthesizing || isExporting}
                        title="将所有章节导出为音频文件"
                    >
                        {isExporting ? (
                            <>
                                <span className="spinner-sm"></span>
                                正在导出...
                            </>
                        ) : (
                            '📦 导出有声书'
                        )}
                    </button>

                    {downloadUrl && (
                        <a
                            href={downloadUrl}
                            className="btn btn-success"
                            target="_blank"
                            rel="noopener noreferrer"
                        >
                            ⬇️ 下载 ZIP
                        </a>
                    )}
                </div>
            </div>

            <style jsx>{`
                .book-toolbar {
                    background: white;
                    padding: var(--space-4);
                    border-radius: var(--radius-lg);
                    margin-bottom: var(--space-6);
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    flex-wrap: wrap;
                    gap: var(--space-4);
                }

                .toolbar-section {
                    display: flex;
                    align-items: center;
                    gap: var(--space-6);
                    flex-wrap: wrap;
                    width: 100%;
                }

                .toolbar-group {
                    display: flex;
                    align-items: center;
                    gap: var(--space-3);
                }

                .toolbar-label {
                    font-size: 0.875rem;
                    font-weight: 500;
                    color: var(--color-text-secondary);
                }

                .voice-select {
                    min-width: 160px;
                }

                .divider {
                    width: 1px;
                    height: 24px;
                    background-color: var(--color-border);
                    margin: 0 var(--space-2);
                }

                .spinner-sm {
                    width: 16px;
                    height: 16px;
                    border: 2px solid currentColor;
                    border-top-color: transparent;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin-right: var(--space-2);
                }

                @media (max-width: 640px) {
                    .toolbar-section {
                        flex-direction: column;
                        align-items: stretch;
                        gap: var(--space-4);
                    }
                    
                    .toolbar-group {
                        flex-direction: column;
                        align-items: stretch;
                    }
                    
                    .divider {
                        display: none;
                    }
                }
            `}</style>
        </div>
    )
}
