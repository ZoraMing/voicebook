"use client";
import Link from 'next/link';
import { Home, AlertTriangle } from 'lucide-react';

export default function NotFound() {
    return (
        <div className="min-h-screen bg-book-bg flex flex-col items-center justify-center p-4">
            <div className="bg-white p-8 rounded-2xl shadow-lg max-w-md w-full text-center border border-gray-100">
                <div className="w-16 h-16 bg-red-50 rounded-full flex items-center justify-center mx-auto mb-6">
                    <AlertTriangle className="text-red-500" size={32} />
                </div>

                <h2 className="text-2xl font-bold text-gray-900 mb-2">页面未找到</h2>
                <p className="text-gray-500 mb-8">
                    抱歉，您访问的页面不存在或已被移除。
                </p>

                <Link
                    href="/"
                    className="flex items-center justify-center gap-2 w-full py-3 bg-book-accent text-white rounded-lg hover:bg-book-accent-hover transition-colors font-medium shadow-sm active:scale-95 transform transition-transform"
                >
                    <Home size={18} />
                    <span>返回首页</span>
                </Link>
            </div>

            <div className="mt-8 text-xs text-gray-400">
                © 2026 VoiceBook Studio
            </div>
        </div>
    );
}
