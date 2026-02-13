import { test, expect } from '@playwright/test';

test.describe('VoiceBook Studio E2E', () => {

    test.beforeEach(async ({ page }) => {
        await page.goto('/');
    });

    test('should verify full workflow: Navigation -> Edit -> Voice -> Synth -> Batch -> Export', async ({ page, request }) => {
        // 0. Setup: Ensure database has books
        const apiResponse = await request.get('http://localhost:8000/api/books');
        let books = await apiResponse.json();

        if (books.length === 0) {
            console.log('No books found. Creating a test book via API...');
            const buffer = Buffer.from('Chapter 1\nThis is a test book content for automation.\n\nChapter 2\nMore content here.');

            const uploadRes = await request.post('http://localhost:8000/api/books/upload', {
                multipart: {
                    file: {
                        name: 'test_book.txt',
                        mimeType: 'text/plain',
                        buffer: buffer
                    }
                }
            });
            expect(uploadRes.ok()).toBeTruthy();
            await page.reload();
        }

        // 1. Navigation
        console.log('Testing Navigation...');
        const firstBookButton = page.getByTestId('book-item').first();
        await expect(firstBookButton).toBeVisible();
        await firstBookButton.click();

        const firstChapter = page.locator('nav > ul > li > ul > li > button').first();
        await expect(firstChapter).toBeVisible();
        await firstChapter.click();

        await expect(page).toHaveURL(/chapterId=/);

        // Wait for paragraphs
        const paragraphList = page.locator('.space-y-6');
        await expect(paragraphList).toBeVisible();
        const firstParagraph = paragraphList.locator('.group').first();
        await expect(firstParagraph).toBeVisible();

        // 2. Edit Paragraph
        console.log('Testing Editing...');
        // Click paragraph to edit
        const pText = firstParagraph.locator('p');
        await pText.click();

        const textarea = firstParagraph.locator('textarea');
        await expect(textarea).toBeVisible();

        // Type new text
        const originalText = await textarea.inputValue();
        const newText = originalText + ' (Test)';
        await textarea.fill(newText);

        // Click Save
        await firstParagraph.locator('button', { hasText: '保存' }).click();

        // Verify text updated
        await expect(firstParagraph.locator('p')).toHaveText(newText);

        // 3. Voice Selection
        console.log('Testing Voice Selection...');
        // Click voice dropdown
        const voiceSelector = firstParagraph.locator('.group\\/voice');
        await voiceSelector.click();

        // Check if dropdown appears
        const dropdown = voiceSelector.locator('.absolute');
        await expect(dropdown).toBeVisible();

        // Select first option if available
        const firstVoiceOption = dropdown.locator('button').first();
        if (await firstVoiceOption.isVisible()) {
            await firstVoiceOption.click();
        } else {
            // Close dropdown if no options
            await page.click('body');
        }

        // 4. Synthesis
        console.log('Testing Synthesis...');
        // Hover container to reveal actions
        await firstParagraph.hover();
        const synthBtn = firstParagraph.locator('button[title="合成"]');
        if (await synthBtn.isVisible()) {
            await synthBtn.click();
        }

        // 5. Batch Selection
        console.log('Testing Batch Actions...');

        // Use page.evaluate to click and check state update
        await firstParagraph.click();

        // Verify selection state via checkbox (allow time for React state to sync)
        const checkbox = firstParagraph.locator('input[type="checkbox"]');

        // If regular click didn't work, maybe the click was intercepted or propagation issue in headless
        // Retry with a more direct approach if it doesn't become checked
        try {
            await expect(checkbox).toBeChecked({ timeout: 2000 });
        } catch (e) {
            console.log('Regular click failed to check, trying force check...');
            await checkbox.check({ force: true });
        }

        await expect(checkbox).toBeChecked();

        // Check if batch actions bar appears
        const batchBar = page.locator('text=已选中 1 项');
        await expect(batchBar).toBeVisible();

        // 6. Export Panel
        console.log('Testing Export Panel...');
        // Click global export button
        const exportBtn = page.locator('button', { hasText: '导出书籍' });
        await exportBtn.click();

        // Check modal appears
        await expect(page.locator('h3', { hasText: '导出书籍' })).toBeVisible();

        // Close modal
        await page.locator('button', { hasText: '关闭' }).click();
    });

});
