from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import render
from .models import Document, ChatMessage
from .chunking import chunk_text
from .embeddings import get_embedding, translate_to_english
from .milvus_client import create_collection, insert_chunks, search
from .generation import generate_answer
import PyPDF2
import docx
import io
from .embeddings import get_embeddings_batch
from langdetect import detect

@api_view(['POST'])
def upload_document(request):
    file_obj = request.FILES.get('file')
    if not file_obj:
        return Response({"error": "Fayl topilmadi"}, status=status.HTTP_400_BAD_REQUEST)

    document = Document.objects.create(file=file_obj, title=file_obj.name)

    file_obj.seek(0)
    text = extract_text(file_obj)

    chunks = chunk_text(text, chunk_size=1200, overlap=200)

    collection_name = f"doc_{document.id}"
    create_collection(collection_name=collection_name)

    vectors = get_embeddings_batch(chunks, batch_size=100)
    data = [
       {"id": i, "vector": vectors[i], "text": chunks[i]}
       for i in range(len(chunks))
    ]

    insert_chunks(data, collection_name=collection_name)

    document.processed = True
    document.chunk_count = len(chunks)
    document.save()

    return Response({
        "document_id": document.id,
        "title": document.title,
        "chunks_count": len(chunks),
        "message": "Fayl muvaffaqiyatli qayta ishlandi"
    })


def calculate_top_k(chunk_count):
    if chunk_count <= 20:
        return 3
    elif chunk_count <= 100:
        return 6
    elif chunk_count <= 500:
        return 12
    else:
        return 25

@api_view(['POST'])
def ask_question(request):
    document_id = request.data.get('document_id')
    question = request.data.get('question')

    if not document_id or not question:
        return Response({"error": "document_id va question kerak"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        document = Document.objects.get(id=document_id)
    except Document.DoesNotExist:
        return Response({"error": "Document topilmadi"}, status=status.HTTP_404_NOT_FOUND)

    collection_name = f"doc_{document.id}"
    top_k = calculate_top_k(document.chunk_count)
    
    try:
        lang_code = detect(question)
    except Exception:
        lang_code = "uz"

    search_query = question
    if lang_code != "en":
        search_query = translate_to_english(question)

    question_vector = get_embedding(question)
    results = search(question_vector, collection_name=collection_name, top_k=top_k)
    context_chunks = [hit['entity']['text'] for hit in results[0]]
    print(f"\n--- SAVOL: {question} ---")
    print(f"--- TOP_K: {top_k} ---")
    for i, c in enumerate(context_chunks):
        print(f"Chunk {i+1}: {c[:150]}...")
    print("-------------------------\n")

    answer = generate_answer(question, context_chunks)

    ChatMessage.objects.create(document=document, question=question, answer=answer)

    return Response({
        "question": question,
        "answer": answer
    })
        


def chat_page(request):
    return render(request, 'rag/chat.html')

def extract_text(file_obj):
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


@api_view(['GET'])
def list_documents(request):
    documents = Document.objects.all().order_by('-uploaded_at')
    data = [
        {
            "id": doc.id,
            "title": doc.title,
            "uploaded_at": doc.uploaded_at.strftime("%Y-%m-%d %H:%M")
        }
        for doc in documents
    ]
    return Response(data)


@api_view(['GET'])
def get_messages(request, document_id):
    messages = ChatMessage.objects.filter(document_id=document_id).order_by('created_at')
    data = [
        {"question": m.question, "answer": m.answer}
        for m in messages
    ]
    return Response(data)



@api_view(['DELETE'])
def delete_document(request, document_id):
    try:
        document = Document.objects.get(id=document_id)
    except Document.DoesNotExist:
        return Response({"error": "Document topilmadi"}, status=status.HTTP_404_NOT_FOUND)

    collection_name = f"doc_{document.id}"

    from .milvus_client import client as milvus_client
    if milvus_client.has_collection(collection_name=collection_name):
        milvus_client.drop_collection(collection_name=collection_name)

    document.file.delete(save=False)
    document.delete()

    return Response({"message": "Fayl o'chirildi"})
