from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_pages(pages, chunk_size=1200, overlap=200):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    result = []
    for page_text, page_number in pages:
        if not page_text.strip():
            continue
        page_chunks = splitter.split_text(page_text)
        for c in page_chunks:
            result.append((c, page_number))
    return result