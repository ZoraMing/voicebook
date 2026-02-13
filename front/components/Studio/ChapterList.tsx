"use client";
import React from "react";
import { Folder, MoreVertical, Edit2, Trash2 } from "lucide-react";
import Link from "next/link";

interface Chapter {
    id: string;
    title: string;
    isActive: boolean;
}

interface ChapterListProps {
    chapters?: Chapter[];
}

export function ChapterList({ chapters = [] }: ChapterListProps) {
    // Mock data if empty
    const items = chapters.length > 0 ? chapters : [
        { id: "1", title: "Chapter 1: The Beginning", isActive: true },
        { id: "2", title: "Chapter 2: The Journey", isActive: false },
        { id: "3", title: "Chapter 3: The End", isActive: false },
    ];

    return (
        <div className="mt-8 px-4">
            <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4 px-2">Chapters</h2>
            <ul className="space-y-1">
                {items.map((chapter) => (
                    <li key={chapter.id} className="group relative">
                        <Link
                            href={`/studio/chapter/${chapter.id}`}
                            className={`block px-3 py-2 rounded text-sm transition-colors ${chapter.isActive
                                    ? "bg-white text-claude-accent font-medium shadow-sm border border-claude-border"
                                    : "text-gray-600 hover:bg-white/50 hover:text-claude-text"
                                }`}
                        >
                            <span className="truncate block pr-6">{chapter.title}</span>
                        </Link>

                        {/* Quick Actions */}
                        <div className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
                            <button className="p-1 hover:text-claude-accent text-gray-400">
                                <Edit2 size={12} />
                            </button>
                        </div>
                    </li>
                ))}
            </ul>
        </div>
    );
}
