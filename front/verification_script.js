const API_BASE = 'http://localhost:8000/api';

async function testIntegration() {
    console.log('--- Starting Integration Test ---');

    // 1. Fetch Books
    console.log('1. Fetching Books...');
    try {
        const booksRes = await fetch(`${API_BASE}/books`);
        if (!booksRes.ok) throw new Error(`Failed to fetch books: ${booksRes.status}`);
        const books = await booksRes.json();
        console.log(`✅ Fetched ${books.length} books.`);

        if (books.length === 0) {
            console.log('⚠️ No books found. Skipping chapter/paragraph tests.');
            return;
        }

        const bookId = books[0].id;
        console.log(`   Using Book ID: ${bookId} (${books[0].title})`);

        // 2. Fetch Chapters
        console.log('2. Fetching Chapters...');
        const chapRes = await fetch(`${API_BASE}/books/${bookId}/chapters`);
        if (!chapRes.ok) throw new Error(`Failed to fetch chapters: ${chapRes.status}`);
        const chapters = await chapRes.json();
        console.log(`✅ Fetched ${chapters.length} chapters.`);

        if (chapters.length === 0) {
            console.log('⚠️ No chapters found. Skipping paragraph tests.');
            return;
        }

        const chapterId = chapters[0].id;
        console.log(`   Using Chapter ID: ${chapterId} (${chapters[0].title})`);

        // 3. Fetch Paragraphs
        console.log('3. Fetching Paragraphs...');
        const paraRes = await fetch(`${API_BASE}/books/chapters/${chapterId}/paragraphs`);
        if (!paraRes.ok) throw new Error(`Failed to fetch paragraphs: ${paraRes.status}`);
        const paragraphs = await paraRes.json();
        console.log(`✅ Fetched ${paragraphs.length} paragraphs.`);

        if (paragraphs.length > 0) {
            // 4. Test Update (Dry run, we verify endpoint exists and allows PUT)
            // We won't actually change data to avoid messing up user data, or we change it back.
            // But for now, just logging the first paragraph.
            console.log(`   First Paragraph: ${paragraphs[0].content.substring(0, 50)}...`);
        }

    } catch (error) {
        console.error('❌ Integration Test Failed:', error);
        process.exit(1);
    }

    console.log('--- Integration Test Completed Successfully ---');
}

testIntegration();
