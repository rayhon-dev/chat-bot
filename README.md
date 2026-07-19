# Chat Bot — Milvus asosidagi RAG (Retrieval-Augmented Generation) tizimi

Fayl yuklansa, uni chunklarga bo'lib, embedding qilib, Milvus vector database'iga saqlaydigan va shu fayl asosida savol-javob beradigan chatbot. LangChain yoki LangGraph ishlatilmagan — barcha RAG logikasi (chunking, embedding chaqiruvi, vector qidiruv, prompt qurish) qo'lda yozilgan.

## Loyiha maqsadi

Bu loyiha mentor tomonidan berilgan experiment topshirig'i sifatida qurilgan: Milvus vector database bilan ishlaydigan, fayl yuklansa uni chunklarga bo'lib embedding qiladigan chatbot yaratish, tayyor RAG framework'larsiz.

## Texnik stack

| Qism | Texnologiya |
|---|---|
| Backend | Django + Django REST Framework |
| Vector database | Milvus (standalone, Docker orqali — etcd + MinIO + Milvus) |
| Embedding | OpenAI `text-embedding-3-small` |
| LLM (javob generatsiyasi) | OpenAI `gpt-4o-mini` |
| Til aniqlash | `langdetect` |
| Fayl parsing | `PyPDF2` (PDF), `python-docx` (DOCX), oddiy o'qish (TXT) |
| Frontend | Django template (vanilla HTML/CSS/JS) |
| Muhit | WSL2 (Ubuntu) — Milvus Lite Windows'ni qo'llab-quvvatlamagani uchun |

## Arxitektura

```
Fayl yuklash
    │
    ▼
Matn ajratish (PDF/DOCX/TXT parser)
    │
    ▼
Chunklarga bo'lish (chunk_size=1200, overlap=200, so'z chegarasidan)
    │
    ▼
Har bir chunk uchun OpenAI embedding (1536-o'lchamli vektor)
    │
    ▼
Milvus'ga saqlash (har fayl uchun alohida collection: doc_<id>)
    │
    ▼
Foydalanuvchi savol beradi
    │
    ▼
Savol tili aniqlanadi (langdetect) → hujjat tiliga mos qidiruv so'zi tayyorlanadi
    │
    ▼
Savol embedding qilinadi → Milvus'dan top-k eng yaqin chunk qidiriladi
    │  (top_k fayl hajmiga qarab moslashadi: 3 / 6 / 12 / 25)
    ▼
Topilgan chunklar + savol → GPT-4o-mini'ga yuboriladi
    │
    ▼
Javob savol tilida qaytariladi, suhbat tarixiga saqlanadi
```

## Asosiy funksiyalar

- **Ko'p fayl** — bir nechta fayl yuklash mumkin, sidebar orqali ular orasida almashish
- **Suhbat tarixi** — har bir fayl uchun savol-javoblar saqlanadi, sahifa yangilanganda yo'qolmaydi
- **Fayl o'chirish** — sidebar'dan faylni va uning Milvus ma'lumotlarini o'chirish
- **Moslashuvchan `top_k`** — kichik fayllar uchun kam, katta fayllar uchun ko'proq chunk qidiriladi
- **Ko'p tillilik** — javob har doim savol tilida qaytariladi (o'zbek/ingliz/rus)
- **Halyuqinatsiyaga qarshi himoya** — system prompt orqali, faqat kontekstdagi ma'lumotdan foydalanish, aks holda "topilmadi" javobi

## O'rnatish va ishga tushirish

### 1. Talablar
- Python 3.10+
- Docker Desktop (WSL2 integratsiyasi yoqilgan)
- OpenAI API key

### 2. Muhitni sozlash

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. `.env` fayl yaratish

```
OPENAI_API_KEY=sizning-api-keyingiz
```

### 4. Milvus'ni ishga tushirish (Docker Compose)

```bash
docker compose up -d
```

Bu `milvus-etcd`, `milvus-minio`, `milvus-standalone` konteynerlarini ishga tushiradi.

### 5. Django migratsiyalari

```bash
python3 manage.py migrate
```

### 6. Serverni ishga tushirish

```bash
python3 manage.py runserver 0.0.0.0:8000
```

Brauzerda: `http://localhost:8000`

## Experiment natijalari

Loyiha ustida ishlash davomida bir nechta RAG bilan bog'liq real muammolar aniqlandi va hal qilindi:

### 1. Katta hujjatlarda retrieval sifati past bo'lishi

Frankenstein romani (912 chunk, `chunk_size=500`) bilan test qilinganda, 10 ta kontent savolidan faqat **6 tasi** to'g'ri javob oldi (60%). Sabab: bosh qahramon ismi ("Frankenstein") juda ko'p takrorlanishi embedding qidiruvini chalg'itgan, va kichik chunklar muhim sahnalarni parchalab tashlagan.

**Yechim**: `chunk_size`ni 500dan 1200ga, `top_k`ni fayl hajmiga moslashtirib 12dan 25ga oshirish orqali, aniqlik **90%**ga ko'tarildi.

### 2. Tillar aro qidiruv muammosi (cross-lingual retrieval)

Inglizcha hujjatga o'zbekcha savol berilganda, ba'zan kerakli ma'lumot topilmadi, aynan shu savolning inglizcha versiyasi esa to'g'ri javob oldi. Bu — embedding modelining bir xil tildagi so'rov-hujjat juftligini boshqa til juftligiga qaraganda aniqroq mos kelishi bilan bog'liq, hujjatlashtirilgan RAG cheklovi.

### 3. Struktura/sintez talab qiluvchi savollar

"Roman qanday tugaydi?" kabi savollar barqaror ravishda yomon natija berdi — bunday savollar butun hujjat bo'ylab tarqalgan ma'lumotni sintez qilishni talab qiladi, RAG esa faqat mahalliy o'xshash bo'laklarni topa oladi. Bu — chunk_size yoki top_k bilan to'liq hal qilib bo'lmaydigan, RAG arxitekturasining tabiiy cheklovi.

### 4. Fayl kursori (file pointer) xatosi

Fayl parsing paytida `Document.objects.create()` faylni to'liq o'qib chiqqani uchun, keyingi `extract_text()` chaqiruvi bo'sh natija qaytargan. `file_obj.seek(0)` bilan hal qilindi.

## Bilingan cheklovlar

- Struktura/xulosa talab qiladigan savollarda aniqlik pastroq (RAG'ning tabiiy cheklovi)
- Hozircha faqat vector search ishlatiladi — keyword search bilan birlashtirish (hybrid search) rejalashtirilgan, lekin amalga oshirilmagan
- Milvus Windows'da to'g'ridan-to'g'ri ishlamaydi, WSL2 talab qilinadi

## Keyingi bosqichlar

- Hybrid search (vector + keyword) qo'shish — "Frankenstein" kabi ko'p takrorlanadigan so'zlar muammosini yanada kamaytirish uchun
- Suhbat tarixini kontekstga qo'shib, ketma-ket savollarni yaxshiroq tushunish
