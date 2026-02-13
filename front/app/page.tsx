"use client";
import React, { useState, useEffect, Suspense, useRef } from "react";
import { useSearchParams } from "next/navigation";
import useSWR, { mutate } from "swr";
import { MainLayout } from "@/components/Layout/MainLayout";
import { ParagraphList } from "@/components/Studio/ParagraphList";
import { GlobalPlayer } from "@/components/Player/GlobalPlayer";
import { ExportPanel } from "@/components/Export/ExportPanel";
import { Download, Loader2, BookOpen } from "lucide-react";
import { api, Paragraph } from "@/services/api";

function StudioContent() {
  const searchParams = useSearchParams();
  const bookId = searchParams.get("bookId") ? Number(searchParams.get("bookId")) : undefined;
  const chapterId = searchParams.get("chapterId") ? Number(searchParams.get("chapterId")) : undefined;

  const { data: paragraphs, error, isLoading, mutate: mutateParagraphs } = useSWR<Paragraph[]>(
    chapterId ? `paragraphs-${chapterId}` : null,
    () => api.getParagraphs(chapterId!),
    { refreshInterval: 5000 }
  );

  const [isPlaying, setIsPlaying] = useState(false);
  const [currentId, setCurrentId] = useState<string | undefined>(undefined);
  const [playbackRate, setPlaybackRate] = useState(1.0);
  const [showExportPanel, setShowExportPanel] = useState(false);
  const [fontSize, setFontSize] = useState(18);

  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Audio Event Listeners
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleEnded = () => {
      setIsPlaying(false);
      // Auto-play next if available
      if (currentId && paragraphs) {
        const currentIndex = paragraphs.findIndex(p => String(p.id) === currentId);
        if (currentIndex >= 0 && currentIndex < paragraphs.length - 1) {
          handlePlay(String(paragraphs[currentIndex + 1].id));
        } else {
          setCurrentId(undefined);
        }
      }
    };

    const handlePause = () => setIsPlaying(false);
    const handlePlayEvent = () => setIsPlaying(true);
    const handleError = (e: any) => {
      console.error("Audio playback error:", e);
      setIsPlaying(false);
    };

    audio.addEventListener("ended", handleEnded);
    audio.addEventListener("pause", handlePause);
    audio.addEventListener("play", handlePlayEvent);
    audio.addEventListener("error", handleError);

    return () => {
      audio.removeEventListener("ended", handleEnded);
      audio.removeEventListener("pause", handlePause);
      audio.removeEventListener("play", handlePlayEvent);
      audio.removeEventListener("error", handleError);
    };
  }, [currentId, paragraphs]);

  // Update playback rate
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.playbackRate = playbackRate;
    }
  }, [playbackRate]);


  const handlePlay = (id: string) => {
    if (!bookId) return;

    // If clicking current playing, toggle
    if (currentId === id && isPlaying) {
      audioRef.current?.pause();
      return;
    }

    // If clicking current paused, play
    if (currentId === id && !isPlaying) {
      audioRef.current?.play();
      return;
    }

    // New play
    const paragraph = paragraphs?.find(p => String(p.id) === id);
    if (paragraph) {
      // Optimistic UI update
      setCurrentId(id);
      setIsPlaying(true);

      if (audioRef.current) {
        audioRef.current.src = api.getAudioUrl(bookId, Number(id));
        audioRef.current.play().catch(e => {
          console.error("Play failed:", e);
          setIsPlaying(false);
        });
      }
    }
  };

  const handleGlobalPlayPause = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        if (currentId) {
          audioRef.current.play();
        } else if (paragraphs && paragraphs.length > 0) {
          // Play first if nothing selected
          handlePlay(String(paragraphs[0].id));
        }
      }
    }
  };

  const handleUpdate = async (id: string, newText: string) => {
    try {
      await api.updateParagraph(Number(id), newText);
      mutateParagraphs();
    } catch (err) {
      console.error("Update failed", err);
      alert("更新失败");
    }
  };

  const handleSynth = async (id: string, voiceId?: string) => {
    if (!bookId) return;
    try {
      await api.synthesizeParagraph(bookId, Number(id), voiceId);
      mutateParagraphs();
    } catch (err) {
      console.error("Synthesis failed", err);
      alert("合成请求失败");
    }
  };

  const handleBatchSynth = async (ids: string[]) => {
    if (!bookId) return;
    try {
      // Convert string IDs back to numbers
      const numIds = ids.map(id => Number(id));
      await api.synthesizeBatch(bookId, numIds);
      mutateParagraphs(); // Refresh status
      alert(`已开始批量合成 ${ids.length} 个段落`);
    } catch (err) {
      console.error("Batch synthesis failed", err);
      alert("批量合成请求失败");
    }
  };

  const handleBatchExport = (ids: string[]) => {
    alert("批量导出功能开发中...");
  };


  const increaseFontSize = () => setFontSize(prev => Math.min(prev + 2, 32));
  const decreaseFontSize = () => setFontSize(prev => Math.max(prev - 2, 12));

  // Map paragraphs for display and fix status mapping
  const displayParagraphs = paragraphs?.map(p => ({
    id: String(p.id),
    text: p.content,
    status: (p.tts_status === 'completed' ? 'done' : p.tts_status) as any,
    characterName: p.character_name || ""
  })) || [];

  return (
    <MainLayout>
      <div className="absolute top-4 right-6 z-10 flex items-center gap-3">
        <div className="flex items-center bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden h-10">
          <button
            onClick={decreaseFontSize}
            className="px-3 h-full hover:bg-gray-50 border-r border-gray-200 text-gray-600 font-medium transition-colors"
            title="减小字号"
          >
            <span className="text-sm">A-</span>
          </button>
          <div className="px-3 h-full flex items-center justify-center text-sm text-gray-500 min-w-[3rem] bg-gray-50/50">
            {fontSize}px
          </div>
          <button
            onClick={increaseFontSize}
            className="px-3 h-full hover:bg-gray-50 text-gray-600 font-medium transition-colors"
            title="增大字号"
          >
            <span className="text-lg">A+</span>
          </button>
        </div>

        <button
          onClick={() => setShowExportPanel(true)}
          className="flex items-center gap-2 px-4 h-10 bg-white text-gray-700 font-medium rounded-lg shadow-sm border border-gray-200 hover:border-book-accent hover:text-book-accent transition-all"
        >
          <Download size={18} />
          <span>导出书籍</span>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto bg-book-bg scroll-smooth">
        <div className="pt-20 pb-40 px-8 max-w-4xl mx-auto">
          {!chapterId ? (
            <div className="flex flex-col items-center justify-center h-full text-gray-400 mt-20">
              <BookOpen size={48} className="mb-4 opacity-50" />
              <p>请在左侧选择要编辑的章节</p>
            </div>
          ) : isLoading ? (
            <div className="flex items-center justify-center h-full mt-20">
              <Loader2 size={32} className="animate-spin text-book-accent" />
            </div>
          ) : (
            <ParagraphList
              paragraphs={displayParagraphs}
              currentlyPlayingId={currentId}
              onParagraphUpdate={handleUpdate}
              onParagraphSynth={handleSynth}
              onParagraphPlay={handlePlay}
              onBatchSynth={handleBatchSynth}
              onBatchExport={handleBatchExport}
              fontSize={fontSize}
            />
          )}
        </div>
      </div>

      <GlobalPlayer
        isPlaying={isPlaying}
        currentText={displayParagraphs.find(p => p.id === currentId)?.text}
        onPlayPause={handleGlobalPlayPause}
        onNext={() => {
          if (!currentId || !paragraphs) return;
          const idx = paragraphs.findIndex(p => String(p.id) === currentId);
          if (idx >= 0 && idx < paragraphs.length - 1) {
            handlePlay(String(paragraphs[idx + 1].id));
          }
        }}
        onPrev={() => {
          if (!currentId || !paragraphs) return;
          const idx = paragraphs.findIndex(p => String(p.id) === currentId);
          if (idx > 0) {
            handlePlay(String(paragraphs[idx - 1].id));
          }
        }}
        playbackRate={playbackRate}
        onPlaybackRateChange={setPlaybackRate}
      />

      <audio ref={audioRef} className="hidden" />

      <ExportPanel isOpen={showExportPanel} onClose={() => setShowExportPanel(false)} bookId={bookId} />
    </MainLayout>
  );
}

export default function StudioPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center h-screen"><Loader2 className="animate-spin text-book-accent" /></div>}>
      <StudioContent />
    </Suspense>
  );
}
