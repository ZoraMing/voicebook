"use client";

import React, { useState, useEffect, useRef } from "react";
import { Play, Pause, SkipBack, SkipForward, Volume2 } from "lucide-react";

interface GlobalPlayerProps {
    currentText?: string;
    isPlaying: boolean;
    onPlayPause: () => void;
    onNext: () => void;
    onPrev: () => void;
    playbackRate: number;
    onPlaybackRateChange: (rate: number) => void;
}

export function GlobalPlayer({
    currentText = "No paragraph selected",
    isPlaying,
    onPlayPause,
    onNext,
    onPrev,
    playbackRate,
    onPlaybackRateChange
}: GlobalPlayerProps) {

    // Mock progress for now
    const [progress, setProgress] = useState(0);

    return (
        <div className="h-20 bg-white border-t border-claude-border flex items-center px-6 justify-between shadow-sm z-50">
            {/* Left: Current Text Preview */}
            <div className="w-1/3 truncate text-sm text-claude-text opacity-80 font-serif italic">
                {currentText}
            </div>

            {/* Center: Controls */}
            <div className="flex flex-col items-center gap-2 w-1/3">
                <div className="flex items-center gap-4">
                    <button onClick={onPrev} className="text-gray-400 hover:text-claude-accent transition-colors">
                        <SkipBack size={20} />
                    </button>
                    <button
                        onClick={onPlayPause}
                        className="w-10 h-10 rounded-full bg-claude-accent hover:bg-claude-accent-hover text-white flex items-center justify-center transition-colors shadow-md"
                    >
                        {isPlaying ? <Pause size={20} fill="currentColor" /> : <Play size={20} fill="currentColor" className="ml-0.5" />}
                    </button>
                    <button onClick={onNext} className="text-gray-400 hover:text-claude-accent transition-colors">
                        <SkipForward size={20} />
                    </button>
                </div>
                {/* Progress Bar (Mock) */}
                <div className="w-full h-1 bg-gray-200 rounded-full overflow-hidden">
                    <div
                        className="h-full bg-claude-accent transition-all duration-300"
                        style={{ width: `${progress}%` }}
                    />
                </div>
            </div>

            {/* Right: Settings */}
            <div className="w-1/3 flex items-center justify-end gap-4">
                <div className="flex items-center gap-2 text-xs font-medium text-gray-500">
                    <span className="uppercase tracking-wider">Speed</span>
                    <select
                        value={playbackRate}
                        onChange={(e) => onPlaybackRateChange(parseFloat(e.target.value))}
                        className="bg-transparent border-none outline-none cursor-pointer hover:text-claude-accent text-right"
                    >
                        <option value="1.0">1.0x</option>
                        <option value="1.25">1.25x</option>
                        <option value="1.5">1.5x</option>
                        <option value="2.0">2.0x</option>
                    </select>
                </div>
                <Volume2 size={18} className="text-gray-400" />
            </div>
        </div>
    );
}
