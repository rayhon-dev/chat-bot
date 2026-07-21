from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
import tempfile
import os


def extract_text_with_pages(file_path, filename):
    filename_lower = filename.lower()

    if filename_lower.endswith('.pdf'):
        loader = PyPDFLoader(file_path)
        docs = loader.load()
        return [(doc.page_content, doc.metadata.get('page', 0) + 1) for doc in docs]

    elif filename_lower.endswith('.docx'):
        loader = Docx2txtLoader(file_path)
        docs = loader.load()
        return [(docs[0].page_content, None)]

    elif filename_lower.endswith('.txt'):
        loader = TextLoader(file_path, encoding='utf-8')
        docs = loader.load()
        return [(docs[0].page_content, None)]

    else:
        raise ValueError(f"Qo'llab-quvvatlanmaydigan fayl turi: {filename}")