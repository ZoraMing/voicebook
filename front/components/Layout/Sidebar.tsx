"use client";

import React, { useState, useRef } from "react";
import { BookOpen, Mic, Upload, ChevronRight, ChevronDown, Loader2, Trash2 } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import useSWR from "swr";
import { api, Book, Chapter } from "../../services/api";
import { Suspense } from "react";

interface SidebarProps {
    className?: string;
}

function SidebarContent({ className }: SidebarProps) {
    const router = useRouter();
    const searchParams = useSearchParams();
    const currentChapterId = Number(searchParams.get("chapterId"));

    const [expandedBooks, setExpandedBooks] = useState<Record<number, boolean>>({});
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [isUploading, setIsUploading] = useState(false);

    // Fetch Books
    const { data: books, error, mutate: mutateBooks } = useSWR<Book[]>('books', api.getBooks);

    const toggleBook = (bookId: number) => {
        setExpandedBooks(prev => ({ ...prev, [bookId]: !prev[bookId] }));
    };

    const handleImportClick = () => {
        fileInputRef.current?.click();
    };

    const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setIsUploading(true);
        try {
            await api.uploadBook(file);
            mutateBooks();
        } catch (err) {
            console.error(err);
            alert("导入失败，请重试。");
        } finally {
            setIsUploading(false);
            if (fileInputRef.current) fileInputRef.current.value = "";
        }
    };

    const handleDeleteBook = async (bookId: number, title: string) => {
        if (confirm(`确定要删除书籍《${title}》及其所有内容吗？`)) {
            try {
                await api.deleteBook(bookId);
                mutateBooks();
                if (currentChapterId) {
                    router.push('/');
                }
            } catch (err) {
                console.error(err);
                alert("删除失败");
            }
        }
    };

    const handleChapterClick = (bookId: number, chapterId: number) => {
        router.push(`/?bookId=${bookId}&chapterId=${chapterId}`);
    };

    return (
        <aside className={`bg-book-sidebar border-r border-book-border h-full flex flex-col ${className || 'w-72'}`}>
            <div className="p-6">
                <h1 className="text-2xl font-bold tracking-tight text-book-accent flex items-center gap-2">
                    <BookOpen className="text-book-accent" />
                    <span>VoiceBook</span>
                </h1>
            </div>

            <div className="px-4 mb-4">
                <button
                    onClick={handleImportClick}
                    disabled={isUploading}
                    className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-book-accent text-white rounded-lg hover:bg-book-accent-hover transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {isUploading ? (
                        <Loader2 size={18} className="animate-spin" />
                    ) : (
                        <>
                            <Upload size={18} />
                            <span className="text-sm font-medium">导入书籍</span>
                        </>
                    )}
                </button>
                <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileChange}
                    className="hidden"
                    accept=".epub,.pdf,.txt,.md"
                />
            </div>

            <nav className="flex-1 px-4 overflow-y-auto custom-scrollbar">
                <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2 pl-2">
                    我的书库
                </div>

                {(!books && !error) && <div className="pl-4 text-gray-400 text-sm italic">加载中...</div>}
                {error && <div className="pl-4 text-red-400 text-sm">加载失败</div>}

                <ul className="space-y-1">
                    {books?.map((book) => (
                        <BookItem
                            key={book.id}
                            book={book}
                            isExpanded={!!expandedBooks[book.id]}
                            onToggle={() => toggleBook(book.id)}
                            currentChapterId={currentChapterId}
                            onChapterClick={handleChapterClick}
                            onDelete={handleDeleteBook}
                        />
                    ))}
                </ul>

                {books?.length === 0 && (
                    <div className="text-center py-8 text-gray-400 text-sm">
                        暂无书籍，请先导入
                    </div>
                )}
            </nav>

            <div className="p-4 border-t border-book-border">
                <div className="text-[10px] text-gray-400 text-center">
                    VoiceBook v1.0 · 智能有声书制作
                </div>
            </div>
        </aside>
    );
}

export function Sidebar(props: SidebarProps) {
    return (
        <Suspense fallback={<aside className="w-72 bg-book-sidebar border-r border-book-border h-full" />}>
            <SidebarContent {...props} />
        </Suspense>
    );
}


function BookItem({ book, isExpanded, onToggle, currentChapterId, onChapterClick, onDelete }: {
    book: Book;
    isExpanded: boolean;
    onToggle: () => void;
    currentChapterId: number;
    onChapterClick: (bookId: number, chapterId: number) => void;
    onDelete: (bookId: number, title: string) => void;
}) {
    const { data: chapters } = useSWR<Chapter[]>(isExpanded ? `chapters-${book.id}` : null, () => api.getChapters(book.id));

    // Progress Polling
    const { data: progressData, mutate: mutateProgress } = useSWR(
        isExpanded ? `progress-${book.id}` : null,
        () => api.getSynthesisProgress(book.id),
        { refreshInterval: 3000 }
    );

    const isSynthesizing = progressData?.status === "synthesizing";

    const handleFullSynth = async (e: React.MouseEvent) => {
        e.stopPropagation();
        if (confirm(`是否开始合成整本书《${book.title}》？`)) {
            try {
                await api.synthesizeFullBook(book.id);
                mutateProgress();
            } catch (err) {
                console.error(err);
                alert("启动失败");
            }
        }
    };

    const handleDelete = async (e: React.MouseEvent) => {
        e.stopPropagation();
        onDelete(book.id, book.title);
    };

    const handleChapterSynth = async (e: React.MouseEvent, chapterId: number, chapterTitle: string) => {
        e.stopPropagation();
        if (confirm(`是否开始合成章节《${chapterTitle}》？`)) {
            try {
                await api.synthesizeChapter(book.id, chapterId);
                mutateProgress();
            } catch (err) {
                console.error(err);
                alert("启动失败");
            }
        }
    };

    return (
        <li>
            <div
                data-testid="book-item"
                onClick={onToggle}
                className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg transition-colors group cursor-pointer ${isExpanded ? "bg-white text-book-text font-medium shadow-sm" : "text-gray-600 hover:bg-white/50 hover:text-book-text"
                    }`}
            >
                {isExpanded ? <ChevronDown size={14} className="text-gray-400" /> : <ChevronRight size={14} className="text-gray-400" />}
                <BookOpen size={16} className={isExpanded ? "text-book-accent" : "text-gray-400 group-hover:text-book-accent"} />
                <span className="truncate text-sm flex-1">{book.title}</span>

                <button
                    onClick={handleDelete}
                    className="p-1 opacity-0 group-hover:opacity-100 hover:bg-red-50 hover:text-red-500 rounded text-gray-400 transition-all"
                    title="删除书籍"
                >
                    <Trash2 size={14} />
                </button>

                <button
                    onClick={handleFullSynth}
                    className="p-1 opacity-0 group-hover:opacity-100 hover:bg-book-bg rounded text-gray-400 hover:text-book-accent transition-all"
                    title="整书批量合成"
                >
                    <Mic size={14} />
                </button>
            </div>

            {isExpanded && (
                <div className="ml-4 mt-1 space-y-0.5 border-l border-gray-200 pl-2">
                    {/* Progress indicator */}
                    {progressData && (progressData.status !== "idle" || progressData.progress > 0) && (
                        <div className="px-3 py-2 mb-2 bg-book-bg/30 rounded-md">
                            <div className="flex justify-between text-[10px] text-gray-500 mb-1">
                                <span>合成进度: {progressData.progress}%</span>
                                {isSynthesizing && <Loader2 size={10} className="animate-spin text-book-accent" />}
                            </div>
                            <div className="h-1 bg-gray-200 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-book-accent transition-all duration-1000"
                                    style={{ width: `${progressData.progress}%` }}
                                />
                            </div>
                        </div>
                    )}

                    <ul className="space-y-0.5">
                        {chapters ? chapters.map(chapter => (
                            <li key={chapter.id} className="group/chapter flex items-center">
                                <button
                                    onClick={() => onChapterClick(book.id, chapter.id)}
                                    className={`flex-1 flex items-center gap-2 px-3 py-1.5 rounded-md text-sm transition-colors text-left ${currentChapterId === chapter.id
                                        ? "bg-book-accent/10 text-book-accent font-medium"
                                        : "text-gray-500 hover:bg-gray-100 hover:text-gray-900"
                                        }`}
                                >
                                    <span className="truncate">{chapter.title}</span>
                                </button>
                                <button
                                    onClick={(e) => handleChapterSynth(e, chapter.id, chapter.title)}
                                    className="p-1 mr-1 opacity-0 group-hover/chapter:opacity-100 hover:bg-gray-100 rounded text-gray-400 hover:text-book-accent transition-all"
                                    title="本章合成"
                                >
                                    <Mic size={12} />
                                </button>
                            </li>
                        )) : (
                            <li className="px-3 py-1.5 text-xs text-gray-400 italic">加载章节...</li>
                        )}
                        {chapters?.length === 0 && (
                            <li className="px-3 py-1.5 text-xs text-gray-400">无章节信息</li>
                        )}
                    </ul>
                </div>
            )}
        </li>
    );
}
