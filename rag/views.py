from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import render
from .models import Document, ChatMessage
from .chunking import chunk_text
from .embeddings import get_embedding
from .milvus_client import create_collection, insert_chunks, search
from .generation import generate_answer
import PyPDF2
import docx
import io

@api_view(['POST'])
def upload_document(request):
    """
    Fayl yuklash endpoint'i.
    Fayl kelganda: saqlaydi -> chunklaydi -> embedding qiladi -> Milvus'ga yozadi
    """
    file_obj = request.FILES.get('file')
    if not file_obj:
        return Response({"error": "Fayl topilmadi"}, status=status.HTTP_400_BAD_REQUEST)

    # 1. Document sifatida saqlash
    document = Document.objects.create(file=file_obj, title=file_obj.name)

    # 2. Fayl matnini o'qish
    text = extract_text(file_obj)

    # 3. Chunklash
    chunks = chunk_text(text, chunk_size=500, overlap=50)

    # 4. Har chunk uchun embedding va Milvus'ga tayyorlash
    # Har bir document uchun alohida collection nomi ishlatamiz
    collection_name = f"doc_{document.id}"
    create_collection(collection_name=collection_name)

    data = []
    for i, chunk in enumerate(chunks):
        vector = get_embedding(chunk)
        data.append({"id": i, "vector": vector, "text": chunk})

    insert_chunks(data, collection_name=collection_name)

    document.processed = True
    document.save()

    return Response({
        "document_id": document.id,
        "title": document.title,
        "chunks_count": len(chunks),
        "message": "Fayl muvaffaqiyatli qayta ishlandi"
    })


@api_view(['POST'])
def ask_question(request):
    """
    Savol-javob endpoint'i.
    """
    document_id = request.data.get('document_id')
    question = request.data.get('question')

    if not document_id or not question:
        return Response({"error": "document_id va question kerak"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        document = Document.objects.get(id=document_id)
    except Document.DoesNotExist:
        return Response({"error": "Document topilmadi"}, status=status.HTTP_404_NOT_FOUND)

    collection_name = f"doc_{document.id}"

    question_vector = get_embedding(question)
    results = search(question_vector, collection_name=collection_name, top_k=3)
    context_chunks = [hit['entity']['text'] for hit in results[0]]

    answer = generate_answer(question, context_chunks)

    # Suhbat tarixini saqlash
    ChatMessage.objects.create(document=document, question=question, answer=answer)

    return Response({
        "question": question,
        "answer": answer
    })


def chat_page(request):
    return render(request, 'rag/chat.html')

def extract_text(file_obj):
    """
    Fayl kengaytmasiga qarab matnni ajratib oladi.
    """
    filename = file_obj.name.lower()

    if filename.endswith('.txt'):
        return file_obj.read().decode('utf-8')

    elif filename.endswith('.pdf'):
        reader = PyPDF2.PdfReader(file_obj)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text

    elif filename.endswith('.docx'):
        document = docx.Document(io.BytesIO(file_obj.read()))
        text = "\n".join([para.text for para in document.paragraphs])
        return text

    else:
        raise ValueError("Faqat .txt, .pdf, .docx fayllar qo'llab-quvvatlanadi")
