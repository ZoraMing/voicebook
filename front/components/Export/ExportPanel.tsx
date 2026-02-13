"use client";
import React, { useState } from "react";
import { Download, FileAudio, FileText, Archive, X, Loader2, CheckCircle } from "lucide-react";
import { api } from "../../services/api";

interface ExportPanelProps {
    isOpen: boolean;
    onClose: () => void;
    bookId?: number;
}

export function ExportPanel({ isOpen, onClose, bookId }: ExportPanelProps) {
    const [isExporting, setIsExporting] = useState(false);
    const [exportResult, setExportResult] = useState<{ success: boolean, message: string } | null>(null);

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

                <div className="p-6 space-y-3">
                    {exportResult ? (
                        <div className={`p-4 rounded-lg flex gap-3 ${exportResult.success ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
                            {exportResult.success ? <CheckCircle className="shrink-0" /> : <AlertCircle className="shrink-0" />}
                            <div className="text-sm">
                                <p className="font-medium">{exportResult.success ? "导出任务已启动" : "导出失败"}</p>
                                <p className="mt-1 opacity-90">{exportResult.message}</p>
                                {exportResult.success && bookId && (
                                    <a
                                        href={api.getExportDownloadUrl(bookId)}
                                        target="_blank"
                                        rel="noreferrer"
                                        className="inline-block mt-3 text-xs font-bold underline cursor-pointer hover:opacity-80"
                                    >
                                        下载 ZIP 归档 (生成完成后)
                                    </a>
                                )}
                            </div>
                        </div>
                    ) : (
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
                                注意：导出过程可能需要几分钟，取决于书籍长度。请确保大部分段落已完成合成。
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
                            <span>{isExporting ? "请求中..." : "开始导出"}</span>
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}

// Import helper
import { AlertCircle } from "lucide-react";
