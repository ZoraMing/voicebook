
import { useState, useEffect, useRef } from 'react';
import { ExportFile } from '@/lib/api';
import { parseLrc, LrcLine } from '@/lib/lrc-parser';

interface ExportPlayerProps {
    files: ExportFile[];
}

export default function ExportPlayer({ files }: ExportPlayerProps) {
    const [currentFileIndex, setCurrentFileIndex] = useState(0);
    const [lrcLines, setLrcLines] = useState<LrcLine[]>([]);
    const [currentLineIndex, setCurrentLineIndex] = useState(-1);

    // 播放状态
    const audioRef = useRef<HTMLAudioElement | null>(null);
    const lrcContainerRef = useRef<HTMLDivElement | null>(null);

    const currentFile = files[currentFileIndex];

    // 加载 LRC
    useEffect(() => {
        if (currentFile && currentFile.lrc) {
            fetch(currentFile.lrc)
                .then(res => res.text())
                .then(text => {
                    const lines = parseLrc(text);
                    setLrcLines(lines);
                })
                .catch(err => {
                    console.error("Failed to load LRC", err);
                    setLrcLines([]);
                });
        } else {
            setLrcLines([]);
        }
        setCurrentLineIndex(-1);
    }, [currentFile]);

    // 监听播放进度
    const handleTimeUpdate = () => {
        if (!audioRef.current || lrcLines.length === 0) return;

        const currentTime = audioRef.current.currentTime;

        // 查找当前行
        let index = lrcLines.findIndex(line => line.time > currentTime);
        if (index === -1) {
            index = lrcLines.length - 1;
        } else {
            index = index - 1;
        }

        if (index !== currentLineIndex) {
            setCurrentLineIndex(index);
            scrollToLine(index);
        }
    };

    const scrollToLine = (index: number) => {
        if (index < 0 || !lrcContainerRef.current) return;

        const container = lrcContainerRef.current;
        const lineEl = container.children[index] as HTMLElement;

        if (lineEl) {
            const offset = lineEl.offsetTop - container.offsetTop - container.clientHeight / 2 + lineEl.clientHeight / 2;
            container.scrollTo({ top: offset, behavior: 'smooth' });
        }
    };

    if (files.length === 0) return null;

    return (
        <div className="export-player">
            <div className="player-header">
                <h3>📖 导出预览播放</h3>
                <div className="file-selector">
                    <select
                        value={currentFileIndex}
                        onChange={(e) => setCurrentFileIndex(Number(e.target.value))}
                    >
                        {files.map((f, i) => (
                            <option key={i} value={i}>{f.name}</option>
                        ))}
                    </select>
                </div>
            </div>

            <div className="lrc-container" ref={lrcContainerRef}>
                {lrcLines.length > 0 ? (
                    lrcLines.map((line, i) => (
                        <p
                            key={i}
                            className={`lrc-line ${i === currentLineIndex ? 'active' : ''}`}
                            onClick={() => {
                                if (audioRef.current) {
                                    audioRef.current.currentTime = line.time;
                                }
                            }}
                        >
                            {line.text}
                        </p>
                    ))
                ) : (
                    <p className="no-lrc">暂无歌词或正在加载...</p>
                )}
            </div>

            <audio
                ref={audioRef}
                src={currentFile.wav}
                controls
                className="audio-control"
                onTimeUpdate={handleTimeUpdate}
            />

            <style jsx>{`
                .export-player {
                    background: white;
                    border: 1px solid var(--color-border);
                    border-radius: var(--radius-lg);
                    padding: var(--space-4);
                    margin-top: var(--space-6);
                }
                
                .player-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: var(--space-4);
                    border-bottom: 1px solid var(--color-border-light);
                    padding-bottom: var(--space-2);
                }
                
                .lrc-container {
                    height: 300px;
                    overflow-y: auto;
                    background: #f9f9f9;
                    border-radius: var(--radius-md);
                    padding: var(--space-4);
                    margin-bottom: var(--space-4);
                    text-align: center;
                }
                
                .lrc-line {
                    padding: 8px 0;
                    margin: 0;
                    color: var(--color-text-muted);
                    cursor: pointer;
                    transition: all 0.2s;
                    border-radius: 4px;
                }
                
                .lrc-line:hover {
                    background: #eee;
                }
                
                .lrc-line.active {
                    color: var(--color-primary);
                    font-weight: bold;
                    font-size: 1.1em;
                    transform: scale(1.05);
                }
                
                .audio-control {
                    width: 100%;
                }
                
                .no-lrc {
                    color: var(--color-text-muted);
                    padding-top: 100px;
                }
            `}</style>
        </div>
    );
}
