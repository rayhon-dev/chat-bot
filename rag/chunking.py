def chunk_text(text, chunk_size=500, overlap=50):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        # Agar oxirgi belgi so'z o'rtasida bo'lsa, orqaga qaytib bo'sh joy top
        if end < len(text):
            while end > start and text[end] not in [" ", "\n"]:
                end -= 1

        chunk = text[start:end]
        chunks.append(chunk.strip())
        start += chunk_size - overlap

    return chunks

if __name__ == "__main__":
    # Test qilish uchun
    with open("data/python_intro.txt", "r", encoding="utf-8") as f:
        text = f.read()

    chunks = chunk_text(text, chunk_size=500, overlap=50)

    print(f"Jami chunklar soni: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"\n--- Chunk {i+1} ---")
        print(chunk)