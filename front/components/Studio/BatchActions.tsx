"use client";
import React from "react";
import { Mic, Download, X } from "lucide-react";

interface BatchActionsProps {
    selectedCount: number;
    onClearSelection: () => void;
    onSynthesizeSelected: () => void;
    onExportSelected: () => void;
}

export function BatchActions({ selectedCount, onClearSelection, onSynthesizeSelected, onExportSelected }: BatchActionsProps) {
    if (selectedCount === 0) return null;

    return (
        <div className="fixed bottom-24 left-1/2 -translate-x-1/2 z-50 animate-slide-up">
            <div className="bg-gray-900 text-white px-6 py-3 rounded-full shadow-xl flex items-center gap-6 border border-gray-800">
                <div className="font-medium text-sm text-gray-300">
                    已选中 {selectedCount} 项
                </div>

                <div className="h-4 w-px bg-white/20" />

                <button
                    onClick={onSynthesizeSelected}
                    className="flex items-center gap-2 hover:text-book-accent transition-colors font-medium text-sm"
                >
                    <Mic size={16} />
                    <span>批量合成</span>
                </button>

                <button
                    onClick={onExportSelected}
                    className="flex items-center gap-2 hover:text-book-accent transition-colors font-medium text-sm"
                >
                    <Download size={16} />
                    <span>批量导出</span>
                </button>

                <div className="h-4 w-px bg-white/20" />

                <button
                    onClick={onClearSelection}
                    className="p-1 hover:bg-white/10 rounded-full transition-colors text-gray-400 hover:text-white"
                    title="取消选择"
                >
                    <X size={16} />
                </button>
            </div>
        </div>
    );
}
