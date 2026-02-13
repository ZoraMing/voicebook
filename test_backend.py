import requests
import json
import sys

BASE_URL = "http://localhost:8000/api"

def test_health():
    try:
        resp = requests.get("http://localhost:8000/health")
        print(f"Health Check: {resp.status_code}, {resp.json()}")
    except Exception as e:
        print(f"Health Check Failed: {e}")

def test_voices():
    resp = requests.get(f"{BASE_URL}/voices")
    print(f"Voices: {resp.status_code}, Count: {len(resp.json())}")

def test_books():
    resp = requests.get(f"{BASE_URL}/books")
    if resp.status_code == 200:
        books = resp.json()
        print(f"Books: {len(books)} found")
        return books
    else:
        print(f"Failed to get books: {resp.status_code}")
        return []

def test_paragraph_edit_and_synth(book_id):
    # Get paragraphs
    resp = requests.get(f"{BASE_URL}/books/{book_id}/paragraphs")
    if resp.status_code != 200 or not resp.json():
        print("No paragraphs found for book")
        return
    
    p = resp.json()[0]
    p_id = p['id']
    print(f"Testing Paragraph {p_id}")

    # Update paragraph
    new_content = p['content'] + " (Test Update)"
    resp = requests.put(f"{BASE_URL}/books/paragraphs/{p_id}", json={"content": new_content})
    print(f"Update Paragraph: {resp.status_code}")
    if resp.status_code == 200:
        print(f"New TTS Status: {resp.json()['tts_status']}") # Should be pending

    # Synthesize single paragraph
    resp = requests.post(f"{BASE_URL}/books/{book_id}/paragraphs/{p_id}/synthesize")
    print(f"Synthesize Paragraph: {resp.status_code}, Result: {resp.text}")

def test_batch_synth(book_id):
    resp = requests.get(f"{BASE_URL}/books/{book_id}/paragraphs")
    ps = resp.json()
    if len(ps) < 2:
        print("Not enough paragraphs for batch test")
        return
    
    ids = [ps[0]['id'], ps[1]['id']]
    print(f"Batch Synthesizing: {ids}")
    resp = requests.post(f"{BASE_URL}/books/{book_id}/synthesize-batch", json={
        "paragraph_ids": ids,
        "voice": "zh-CN-XiaoxiaoNeural"
    })
    print(f"Batch Synthesis: {resp.status_code}, {resp.json()}")

if __name__ == "__main__":
    test_health()
    test_voices()
    books = test_books()
    if not books:
        print("No books found, trying to parse 讲解ai.md...")
        resp = requests.post(f"{BASE_URL}/books/parse/讲解ai.md")
        if resp.status_code == 200:
            books = test_books()
            
    if books:
        book_id = books[0]['id']
        test_paragraph_edit_and_synth(book_id)
        test_batch_synth(book_id)
    else:
        print("Please upload a book via UI first or ensure backend is running with data.")
