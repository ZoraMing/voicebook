"use client";
import React, { useState } from "react";
import { ParagraphItem, ParagraphStatus } from "./ParagraphItem";
import { BatchActions } from "./BatchActions";

interface Paragraph {
    id: string;
    text: string;
    status: ParagraphStatus;
    characterName: string;
}

interface ParagraphListProps {
    paragraphs: Paragraph[];
    currentlyPlayingId?: string;
    onParagraphUpdate: (id: string, newText: string) => void;
    onParagraphSynth: (id: string, voiceId?: string) => void;
    onParagraphPlay: (id: string) => void;
    onBatchSynth: (ids: string[]) => void;
    onBatchExport: (ids: string[]) => void;
    fontSize?: number;
}

export function ParagraphList({
    paragraphs,
    currentlyPlayingId,
    onParagraphUpdate,
    onParagraphSynth,
    onParagraphPlay,
    onBatchSynth,
    onBatchExport,
    fontSize = 18
}: ParagraphListProps) {
    const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

    const toggleSelection = (id: string) => {
        const newSelected = new Set(selectedIds);
        if (newSelected.has(id)) {
            newSelected.delete(id);
        } else {
            newSelected.add(id);
        }
        setSelectedIds(newSelected);
    };

    const handleClearSelection = () => {
        setSelectedIds(new Set());
    };

    const handleBatchSynth = () => {
        onBatchSynth(Array.from(selectedIds));
        handleClearSelection();
    };

    const handleBatchExport = () => {
        onBatchExport(Array.from(selectedIds));
        handleClearSelection();
    };

    return (
        <div className="max-w-3xl mx-auto py-12 px-6 pb-32">
            <div className="space-y-6">
                {paragraphs.map((p) => (
                    <ParagraphItem
                        key={p.id}
                        id={p.id}
                        text={p.text}
                        status={p.status}
                        characterName={p.characterName}
                        isSelected={selectedIds.has(p.id)}
                        isPlaying={currentlyPlayingId === p.id}
                        onToggleSelect={toggleSelection}
                        onPlay={onParagraphPlay}
                        onEdit={onParagraphUpdate}
                        onSynth={onParagraphSynth}
                        fontSize={fontSize}
                    />
                ))}
            </div>

            <BatchActions
                selectedCount={selectedIds.size}
                onClearSelection={handleClearSelection}
                onSynthesizeSelected={handleBatchSynth}
                onExportSelected={handleBatchExport}
            />
        </div>
    );
}
