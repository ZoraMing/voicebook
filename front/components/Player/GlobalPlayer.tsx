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
    currentTime: number;
    duration: number;
    onSeek: (time: number) => void;
}

export function GlobalPlayer({
    currentText = "No paragraph selected",
    isPlaying,
    onPlayPause,
    onNext,
    onPrev,
    playbackRate,
    onPlaybackRateChange,
    currentTime,
    duration,
    onSeek
}: GlobalPlayerProps) {

    const formatTime = (time: number) => {
        if (isNaN(time)) return "00:00";
        const mins = Math.floor(time / 60);
        const secs = Math.floor(time % 60);
        return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
    };

    const progress = duration > 0 ? (currentTime / duration) * 100 : 0;

    const handleProgressClick = (e: React.MouseEvent<HTMLDivElement>) => {
        if (duration === 0) return;
        const rect = e.currentTarget.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const clickedPct = x / rect.width;
        onSeek(clickedPct * duration);
    };

    return (
        <div className="h-24 bg-white border-t border-book-border flex flex-col items-center px-6 justify-center shadow-sm z-50">
            <div className="w-full flex items-center justify-between mb-2">
                {/* Left: Current Text Preview */}
                <div className="w-1/4 truncate text-sm text-book-text opacity-80 font-serif italic">
                    {currentText}
                </div>

                {/* Center: Controls */}
                <div className="flex items-center gap-6">
                    <button onClick={onPrev} className="text-gray-400 hover:text-book-accent transition-colors">
                        <SkipBack size={20} />
                    </button>
                    <button
                        onClick={onPlayPause}
                        className="w-12 h-12 rounded-full bg-book-accent hover:bg-book-accent-hover text-white flex items-center justify-center transition-colors shadow-md"
                    >
                        {isPlaying ? <Pause size={24} fill="currentColor" /> : <Play size={24} fill="currentColor" className="ml-0.5" />}
                    </button>
                    <button onClick={onNext} className="text-gray-400 hover:text-book-accent transition-colors">
                        <SkipForward size={20} />
                    </button>
                </div>

                {/* Right: Settings */}
                <div className="w-1/4 flex items-center justify-end gap-4">
                    <div className="flex items-center gap-2 text-xs font-medium text-gray-500">
                        <span className="uppercase tracking-wider">Speed</span>
                        <select
                            value={playbackRate}
                            onChange={(e) => onPlaybackRateChange(parseFloat(e.target.value))}
                            className="bg-transparent border-none outline-none cursor-pointer hover:text-book-accent text-right"
                        >
                            <option value="1.0">1.0x</option>
                            <option value="1.25">1.25x</option>
                            <option value="1.5">1.5x</option>
                            <option value="2.0">2.0x</option>
                        </select>
                    </div>
                </div>
            </div>

            {/* Bottom: Progress Bar and Time */}
            <div className="w-full max-w-2xl flex items-center gap-3">
                <span className="text-[10px] tabular-nums text-gray-400 min-w-[35px] text-right">
                    {formatTime(currentTime)}
                </span>
                <div
                    className="flex-1 h-1.5 bg-gray-100 rounded-full cursor-pointer relative group"
                    onClick={handleProgressClick}
                >
                    <div
                        className="absolute h-full bg-book-accent rounded-full transition-all"
                        style={{ width: `${progress}%` }}
                    />
                    <div
                        className="absolute w-3 h-3 bg-book-accent rounded-full border-2 border-white shadow-sm -top-[3px] opacity-0 group-hover:opacity-100 transition-opacity"
                        style={{ left: `calc(${progress}% - 6px)` }}
                    />
                </div>
                <span className="text-[10px] tabular-nums text-gray-400 min-w-[35px]">
                    {formatTime(duration)}
                </span>
            </div>
        </div>
    );
}
