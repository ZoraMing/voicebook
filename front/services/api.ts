const API_BASE = 'http://localhost:8000/api';

export interface Book {
    id: number;
    title: string;
    author: string | null;
    cover_image: string | null;
    status: string;
}

export interface Chapter {
    id: number;
    title: string;
    book_id: number;
    index: number;
}

export interface Paragraph {
    id: number;
    content: string;
    character_name: string | null;
    tts_status: 'pending' | 'processing' | 'completed' | 'failed';
    book_id: number;
    chapter_id: number;
    sequence: number;
}

export interface Voice {
    id: string;
    name: string;
    voice: string;
    gender: string;
    locale: string;
}

export const api = {
    // Books
    getBooks: async (): Promise<Book[]> => {
        const res = await fetch(`${API_BASE}/books`);
        if (!res.ok) throw new Error('Failed to fetch books');
        return res.json();
    },

    uploadBook: async (file: File) => {
        const formData = new FormData();
        formData.append("file", file);
        const res = await fetch(`${API_BASE}/books/upload`, {
            method: "POST",
            body: formData,
        });
        if (!res.ok) throw new Error('Failed to upload book');
        return res.json();
    },

    deleteBook: async (bookId: number) => {
        const res = await fetch(`${API_BASE}/books/${bookId}`, {
            method: 'DELETE',
        });
        if (!res.ok) throw new Error('Failed to delete book');
        return res.json();
    },

    // Chapters
    getChapters: async (bookId: number): Promise<Chapter[]> => {
        const res = await fetch(`${API_BASE}/books/${bookId}/chapters`);
        if (!res.ok) throw new Error('Failed to fetch chapters');
        return res.json();
    },

    // Paragraphs
    getParagraphs: async (chapterId: number): Promise<Paragraph[]> => {
        const res = await fetch(`${API_BASE}/books/chapters/${chapterId}/paragraphs`);
        if (!res.ok) throw new Error('Failed to fetch paragraphs');
        const data = await res.json();
        return data;
    },

    updateParagraph: async (id: number, content: string) => {
        const res = await fetch(`${API_BASE}/books/paragraphs/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content }),
        });
        if (!res.ok) throw new Error('Failed to update paragraph');
        return res.json();
    },

    // TTS & Voices
    getVoices: async (): Promise<Voice[]> => {
        const res = await fetch(`${API_BASE}/voices`);
        if (!res.ok) throw new Error('Failed to fetch voices');
        return res.json();
    },

    synthesizeParagraph: async (bookId: number, paragraphId: number, voice: string = "zh-CN-XiaoxiaoNeural") => {
        const res = await fetch(`${API_BASE}/books/${bookId}/paragraphs/${paragraphId}/synthesize?voice=${voice}`, {
            method: 'POST',
        });
        if (!res.ok) throw new Error('Failed to synthesize paragraph');
        return res.json();
    },

    synthesizeBatch: async (bookId: number, paragraphIds: number[], voice: string = "zh-CN-XiaoxiaoNeural") => {
        const res = await fetch(`${API_BASE}/books/${bookId}/synthesize-batch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ paragraph_ids: paragraphIds, voice }),
        });
        if (!res.ok) throw new Error('Failed to batch synthesize');
        return res.json();
    },

    synthesizeFullBook: async (bookId: number, voice: string = "zh-CN-XiaoxiaoNeural") => {
        const res = await fetch(`${API_BASE}/books/${bookId}/synthesize?voice=${voice}`, {
            method: 'POST',
        });
        if (!res.ok) throw new Error('Failed to start full book synthesis');
        return res.json();
    },

    synthesizeChapter: async (bookId: number, chapterId: number, voice: string = "zh-CN-XiaoxiaoNeural") => {
        const res = await fetch(`${API_BASE}/books/${bookId}/chapters/${chapterId}/synthesize?voice=${voice}`, {
            method: 'POST',
        });
        if (!res.ok) throw new Error('Failed to start chapter synthesis');
        return res.json();
    },

    getSynthesisProgress: async (bookId: number): Promise<{
        status: string;
        progress: number;
        total_paragraphs: number;
        completed: number;
        failed: number;
    }> => {
        const res = await fetch(`${API_BASE}/books/${bookId}/progress`);
        if (!res.ok) throw new Error('Failed to fetch progress');
        return res.json();
    },

    // Export
    exportBook: async (bookId: number) => {
        const res = await fetch(`${API_BASE}/books/${bookId}/export`, {
            method: 'POST',
        });
        if (!res.ok) throw new Error('Failed to start export');
        return res.json();
    },

    getExportDownloadUrl: (bookId: number) => `${API_BASE}/books/${bookId}/export/download`,

    getAudioUrl: (bookId: number, paragraphId: number) => `${API_BASE}/audio/${bookId}/${paragraphId}`,
};
