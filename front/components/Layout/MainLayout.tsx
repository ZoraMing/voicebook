import React, { useState } from "react";
import { Sidebar } from "./Sidebar";
import { PanelLeftClose, PanelLeftOpen } from "lucide-react";

interface MainLayoutProps {
    children: React.ReactNode;
}

export function MainLayout({ children }: MainLayoutProps) {
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);

    return (
        <div className="flex h-screen bg-book-bg overflow-hidden relative">
            {/* Sidebar with transition */}
            <div
                className={`flex-shrink-0 bg-book-sidebar border-r border-book-border transition-all duration-300 ease-in-out ${isSidebarOpen ? "w-72 translate-x-0" : "w-0 -translate-x-full opacity-0"
                    }`}
            >
                <div className="w-72 h-full">
                    <Sidebar className="w-full h-full" />
                </div>
            </div>

            <main className="flex-1 flex flex-col relative overflow-hidden min-w-0">
                {/* Collapse Toggle Button */}
                <div className="absolute top-4 left-4 z-20">
                    <button
                        onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                        className="p-2 bg-white/80 backdrop-blur-sm border border-gray-200 text-gray-500 rounded-lg shadow-sm hover:bg-white hover:text-book-accent transition-colors"
                        title={isSidebarOpen ? "收起侧边栏" : "展开侧边栏"}
                    >
                        {isSidebarOpen ? <PanelLeftClose size={20} /> : <PanelLeftOpen size={20} />}
                    </button>
                </div>

                {children}
                {/* Player will go here */}
            </main>
        </div>
    );
}
