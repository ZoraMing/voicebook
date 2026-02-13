"use client";

import React, { useState } from "react";
import { Play, Mic, Edit2, Check, Clock, AlertCircle } from "lucide-react";
import clsx from "clsx";
import { VoiceSelector } from "./VoiceSelector";

export type ParagraphStatus = "pending" | "processing" | "done" | "failed";

export interface ParagraphProps {
    id: string;
    text: string;
    status: ParagraphStatus;
    isSelected: boolean;
    isPlaying: boolean;
    characterName: string; // This will store the voice ID in our case
    onToggleSelect: (id: string) => void;
    onPlay: (id: string) => void;
    onEdit: (id: string, newText: string) => void;
    onSynth: (id: string, voiceId?: string) => void;
    fontSize?: number;
}

export function ParagraphItem({
    id,
    text,
    status,
    isSelected,
    isPlaying,
    characterName,
    onToggleSelect,
    onPlay,
    onEdit,
    onSynth,
    fontSize = 18
}: ParagraphProps) {
    const [isEditing, setIsEditing] = useState(false);
    const [editText, setEditText] = useState(text);
    const [selectedVoice, setSelectedVoice] = useState(characterName || "zh-CN-XiaoxiaoNeural");

    const handleVoiceChange = (newVoiceId: string) => {
        setSelectedVoice(newVoiceId);
    };

    const handleSave = () => {
        onEdit(id, editText);
        setIsEditing(false);
    };

    const handleSynthClick = (e: React.MouseEvent) => {
        e.stopPropagation();
        onSynth(id, selectedVoice);
    };

    const statusIcon = {
        pending: <div className="w-2 h-2 rounded-full bg-gray-300" title="待处理" />,
        processing: <span title="处理中"><Clock size={14} className="text-blue-500 animate-spin" /></span>,
        done: <div className="w-2 h-2 rounded-full bg-green-500" title="完成" />,
        failed: <span title="失败"><AlertCircle size={14} className="text-red-500" /></span>,
    }[status];

    return (
        <div
            className={clsx(
                "group relative p-6 rounded-xl border transition-all duration-200 mb-4 bg-white shadow-sm",
                isSelected ? "border-book-accent ring-1 ring-book-accent/10" : "border-transparent hover:border-book-border hover:shadow-md",
                isPlaying && "ring-2 ring-book-accent ring-offset-2 shadow-md"
            )}
            onClick={() => !isEditing && onToggleSelect(id)}
        >
            {/* Selection Checkbox */}
            <div className={clsx("absolute top-6 left-2 opacity-0 -translate-x-full transition-all", (isSelected || isPlaying) && "opacity-100 translate-x-0")}>
                <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={(e) => { e.stopPropagation(); onToggleSelect(id); }}
                    className="w-4 h-4 rounded border-gray-300 text-book-accent focus:ring-book-accent cursor-pointer"
                />
            </div>

            {/* Header: Character & Status */}
            <div className="flex items-center gap-2 mb-3 border-b border-dashed border-gray-100 pb-2" onClick={e => e.stopPropagation()}>
                <VoiceSelector
                    currentVoiceId={selectedVoice}
                    onVoiceChange={handleVoiceChange}
                />
                <div className="ml-auto">{statusIcon}</div>
            </div>

            {/* Content */}
            {isEditing ? (
                <div className="relative" onClick={e => e.stopPropagation()}>
                    <textarea
                        value={editText}
                        onChange={(e) => setEditText(e.target.value)}
                        className="w-full min-h-[120px] p-4 rounded-lg border border-book-accent focus:outline-none focus:ring-2 focus:ring-book-accent/10 bg-white font-serif leading-relaxed text-book-text resize-y"
                        style={{ fontSize: `${fontSize}px` }}
                        autoFocus
                    />
                    <div className="flex justify-end gap-2 mt-3 block">
                        <button
                            onClick={() => setIsEditing(false)}
                            className="px-3 py-1.5 text-sm text-gray-500 hover:text-gray-700 font-medium"
                        >
                            取消
                        </button>
                        <button
                            onClick={handleSave}
                            className="px-4 py-1.5 text-sm bg-book-accent text-white rounded-md hover:bg-book-accent-hover shadow-sm font-medium transition-colors"
                        >
                            保存
                        </button>
                    </div>
                </div>
            ) : (
                <p
                    className="font-serif leading-loose text-book-text cursor-text selection:bg-book-accent/20"
                    style={{ fontSize: `${fontSize}px` }}
                    onClick={(e) => { e.stopPropagation(); setIsEditing(true); }}
                >
                    {text}
                </p>
            )}

            {/* Actions (Hover) */}
            <div className="absolute top-4 right-4 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity bg-white/95 border border-gray-100 px-2 py-1.5 rounded-lg shadow-sm" onClick={e => e.stopPropagation()}>
                {status === "done" && (
                    <button onClick={() => onPlay(id)} className="p-1.5 hover:bg-book-bg hover:text-book-accent rounded transition-colors" title="播放">
                        <Play size={16} fill="currentColor" />
                    </button>
                )}
                {status !== "processing" && (
                    <button onClick={handleSynthClick} className="p-1.5 hover:bg-book-bg hover:text-book-accent rounded transition-colors" title="合成">
                        <Mic size={16} />
                    </button>
                )}
                {!isEditing && (
                    <button onClick={() => setIsEditing(true)} className="p-1.5 hover:bg-book-bg hover:text-gray-900 rounded transition-colors" title="编辑">
                        <Edit2 size={16} />
                    </button>
                )}
            </div>
        </div>
    );
}
