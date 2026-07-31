import re
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader


def clean_extracted_text(text):
    text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', text)

    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if re.fullmatch(r'\d{1,4}', stripped):
            continue
        cleaned_lines.append(line)

    result = '\n'.join(cleaned_lines)
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result


def extract_text_with_pages(file_path, filename):
    filename_lower = filename.lower()

    if filename_lower.endswith('.pdf'):
        loader = PyPDFLoader(file_path)
        docs = loader.load()
        return [(clean_extracted_text(doc.page_content), doc.metadata.get('page', 0) + 1) for doc in docs]

    elif filename_lower.endswith('.docx'):
        loader = Docx2txtLoader(file_path)
        docs = loader.load()
        return [(clean_extracted_text(docs[0].page_content), None)]

    elif filename_lower.endswith('.txt'):
        loader = TextLoader(file_path, encoding='utf-8')
        docs = loader.load()
        return [(clean_extracted_text(docs[0].page_content), None)]

    else:
        raise ValueError(f"Qo'llab-quvvatlanmaydigan fayl turi: {filename}")