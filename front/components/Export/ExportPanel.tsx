"use client";
import React, { useState } from "react";
import { Download, FileAudio, FileText, Archive, X, Loader2, CheckCircle, BookOpen } from "lucide-react";
import { api } from "../../services/api";

interface ExportPanelProps {
    isOpen: boolean;
    onClose: () => void;
    bookId?: number;
}

export function ExportPanel({ isOpen, onClose, bookId }: ExportPanelProps) {
    const [isExporting, setIsExporting] = useState(false);
    const [exportResult, setExportResult] = useState<{ success: boolean, message: string } | null>(null);
    const [bookTitle, setBookTitle] = useState<string>("");
    const [hasExistingExport, setHasExistingExport] = useState(false);
    const [isChecking, setIsChecking] = useState(false);

    // Initial check when opening
    React.useEffect(() => {
        if (isOpen && bookId) {
            // Get book details
            api.getBook(bookId).then(book => {
                setBookTitle(book.title);
            }).catch(console.error);

            // Check for existing exports
            checkExportStatus();
        } else {
            // Reset state on close
            setExportResult(null);
            setBookTitle("");
            setHasExistingExport(false);
        }
    }, [isOpen, bookId]);

    const checkExportStatus = () => {
        if (!bookId) return;
        setIsChecking(true);
        api.getExportFiles(bookId).then(data => {
            if (data.files && data.files.length > 0) {
                setHasExistingExport(true);
            }
        }).catch(err => {
            console.error("Failed to check export status", err);
        }).finally(() => {
            setIsChecking(false);
        });
    };

    // Poll for status if exporting or just finished
    React.useEffect(() => {
        let interval: NodeJS.Timeout;
        if (isExporting || (exportResult?.success && !hasExistingExport)) {
            interval = setInterval(() => {
                if (bookId) {
                    api.getExportFiles(bookId).then(data => {
                        if (data.files && data.files.length > 0) {
                            setHasExistingExport(true);
                            // If we were exporting, we can stop polling now (or keep polling until all done?)
                            // For now, if we see files, we assume success enough to download
                        }
                    });
                }
            }, 3000);
        }
        return () => clearInterval(interval);
    }, [isExporting, exportResult, hasExistingExport, bookId]);

    if (!isOpen) return null;

    const handleExport = async () => {
        if (!bookId) return;
        setIsExporting(true);
        setExportResult(null);
        try {
            const res = await api.exportBook(bookId);
            if (res.success) {
                setExportResult({ success: true, message: res.message });
            } else {
                setExportResult({ success: false, message: res.message });
            }
        } catch (err: any) {
            setExportResult({ success: false, message: "导出请求失败" });
        } finally {
            setIsExporting(false);
        }
    };

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 backdrop-blur-sm animate-fade-in">
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden animate-scale-in">
                <div className="p-6 border-b border-gray-100 flex justify-between items-center bg-book-bg/50">
                    <div>
                        <h3 className="text-lg font-bold text-gray-900">导出书籍</h3>
                        <p className="text-xs text-gray-500 mt-1">生成音频与歌词文件</p>
                    </div>
                    <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors">
                        <X size={20} />
                    </button>
                </div>

                <div className="p-6 space-y-4">
                    {bookTitle && (
                         <div className="text-sm text-gray-700 bg-blue-50 p-3 rounded-lg border border-blue-100 flex items-center gap-2">
                            <BookOpen size={16} className="text-blue-500" />
                            <span>正在为 <strong>《{bookTitle}》</strong> 准备导出</span>
                         </div>
                    )}

                    {hasExistingExport && (
                        <div className="p-4 rounded-lg bg-green-50 border border-green-100">
                             <div className="flex items-center gap-2 text-green-700 mb-2">
                                <CheckCircle size={18} />
                                <span className="font-bold">导出文件已就绪</span>
                             </div>
                             <p className="text-xs text-green-600 mb-3">检测到该书已有导出的音频文件。</p>
                             {bookId && (
                                <a
                                    href={api.getExportDownloadUrl(bookId)}
                                    className="block w-full text-center py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition-colors shadow-sm"
                                >
                                    下载导出包 (ZIP)
                                </a>
                             )}
                        </div>
                    )}

                    {exportResult && (
                        <div className={`p-4 rounded-lg flex gap-3 ${exportResult.success ? 'bg-blue-50 text-blue-700' : 'bg-red-50 text-red-700'}`}>
                            {exportResult.success ? <Loader2 className="shrink-0 animate-spin" /> : <AlertCircle className="shrink-0" />}
                            <div className="text-sm">
                                <p className="font-medium">{exportResult.success ? "导出任务进行中..." : "导出失败"}</p>
                                <p className="mt-1 opacity-90">{exportResult.message}</p>
                            </div>
                        </div>
                    )}

                    {!exportResult && !hasExistingExport && (
                         <>
                            <div className="flex items-start gap-4 p-4 rounded-lg border border-gray-200 bg-gray-50/50">
                                <div className="p-2 bg-white rounded-lg shadow-sm text-book-accent">
                                    <Archive size={24} />
                                </div>
                                <div className="flex-1">
                                    <span className="font-medium text-gray-900">标准导出格式</span>
                                    <p className="text-xs text-gray-500 mt-1">包含合并后的音频 (WAV) 和同步字幕 (LRC)</p>
                                </div>
                            </div>
                            <p className="text-xs text-gray-400 text-center px-4">
                                注意：导出过程可能需要几分钟，取决于书籍长度。任务将在后台执行。
                            </p>
                        </>
                    )}
                </div>

                <div className="p-5 border-t border-gray-100 bg-gray-50 flex justify-end gap-3">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-800 transition-colors bg-white border border-gray-200 rounded-lg hover:shadow-sm"
                    >
                        关闭
                    </button>
                    {!exportResult && (
                        <button
                            onClick={handleExport}
                            disabled={isExporting || !bookId}
                            className="px-6 py-2 text-sm font-medium text-white bg-book-accent hover:bg-book-accent-hover rounded-lg shadow-sm transition-all transform active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                        >
                            {isExporting && <Loader2 size={16} className="animate-spin" />}
                            <span>{hasExistingExport ? "重新导出" : (isExporting ? "请求中..." : "开始导出")}</span>
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}

// Import helper
import { AlertCircle } from "lucide-react";
