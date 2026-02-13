"use client";
import React from "react";
import { ChevronDown, Loader2 } from "lucide-react";
import useSWR from "swr";
import { api } from "../../services/api";

interface VoiceSelectorProps {
    currentVoiceId: string;
    currentVoiceName?: string;
    onVoiceChange: (voiceId: string) => void;
}

export function VoiceSelector({ currentVoiceId, currentVoiceName, onVoiceChange }: VoiceSelectorProps) {
    const { data: voices, isLoading } = useSWR('voices', api.getVoices);

    // Find current voice name if not provided or to ensure it matches
    const displayVoice = voices?.find(v => v.voice === currentVoiceId) || { name: '默认语音', voice: currentVoiceId };
    const displayName = currentVoiceName || displayVoice.name;

    return (
        <div className="relative group/voice inline-block">
            <div className="flex items-center gap-1 text-xs font-medium text-book-text-light uppercase tracking-wide cursor-pointer hover:text-book-accent transition-colors bg-white border border-book-border px-2 py-0.5 rounded shadow-sm">
                <span>{isLoading ? "加载中..." : displayName}</span>
                <ChevronDown size={12} />
            </div>

            {/* Dropdown menu */}
            <div className="absolute top-full left-0 mt-1 w-64 max-h-60 overflow-y-auto bg-white border border-gray-200 rounded-lg shadow-xl opacity-0 invisible group-hover/voice:opacity-100 group-hover/voice:visible transition-all z-20 custom-scrollbar">
                <div className="p-1">
                    {isLoading ? (
                        <div className="p-4 flex justify-center"><Loader2 size={16} className="animate-spin text-gray-400" /></div>
                    ) : voices?.map((voice) => (
                        <button
                            key={voice.voice} // Using voice ID (e.g. zh-CN-XiaoxiaoNeural) as key
                            onClick={() => onVoiceChange(voice.voice)}
                            className={`w-full text-left px-3 py-2 text-sm rounded hover:bg-gray-50 transition-colors flex flex-col ${voice.voice === currentVoiceId ? "text-book-accent font-medium bg-book-bg" : "text-gray-700"
                                }`}
                        >
                            <span>{voice.name}</span>
                            <span className="text-[10px] text-gray-400">{voice.gender} · {voice.locale}</span>
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
}
