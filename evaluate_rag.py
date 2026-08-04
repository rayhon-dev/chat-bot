import os
import django
from dotenv import load_dotenv

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chatbot_project.settings")
django.setup()
load_dotenv()  # .env faylni yuklaydi
os.environ["OPENAI_API_KEY"] = os.getenv("PLATFORM_OPENAI_API_KEY", "")

import json
import os as _os

from datasets import Dataset
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from ragas import evaluate
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import AnswerRelevancy, context_precision, context_recall, faithfulness
from ragas.run_config import RunConfig

from clients.models import Bot
from rag.services.chat import get_bot_response
from rag.services.retrieval import retrieve_relevant_chunks

# ==============================================================================
# SOZLAMALAR
# ==============================================================================

BOT_ID = 2
CACHE_FILE = "eval_cache.json"

# 1. Sinov savollari va etalon (ground truth) javoblari
#    Har bir element: {"question": "...", "ground_truth": "..."}
TEST_CASES = [
    {
        "question": "Ushbu Mehnat Kodeksining asosiy vazifalari nimalardan iborat?",
        "ground_truth": "Mehnat kodeksining asosiy vazifalari xodimlar, ish beruvchilar va davlatning manfaatlarini muvozanatlash, mehnat bozorining samarali faoliyat ko'rsatishini ta'minlash, mehnat erkinligini va xodimlarning adolatli mehnat sharoitlariga bo'lgan huquqlarini kafolatlashdan iborat."
    },
    {
        "question": "Yakka tartibdagi mehnat munosabatlarini huquqiy tartibga solishning asosiy prinsiplari qaysilar?",
        "ground_truth": "Asosiy prinsiplar sirasiga mehnat erkinligi, mehnat sohasida kamsitishga yo'l qo'ymaslik, majburiy mehnatni taqiqlash, mehnat munosabatlari barqarorligi, xodimlar va ish beruvchilar huquqlarining tengligi hamda ijtimoiy sheriklik kiradi."
    },
    {
        "question": "Mehnat va mashgʻulotlar sohasida qanday holatlar kamsitish deb hisoblanmaydi?",
        "ground_truth": "Muayyan ishning xususiyatlaridan kelib chiqadigan talablar, xodimlarning ijtimoiy va huquqiy jihatdan davlat tomonidan qo'shimcha ravishda qo'riqlanishga muhtoj bo'lgan toifalariga (ayollar, yoshlar, nogironligi bo'lgan shaxslar) nisbatan belgilanadigan farqlovchi choralar kamsitish deb hisoblanmaydi."
    },
    {
        "question": "Mehnat erkinligi nima va u mehnat shartnomasida qanday namoyon boʻladi?",
        "ground_truth": "Mehnat erkinligi har bir shaxsning o'z qobiliyatlarini mehnat qilish uchun tasarruf etish, kasb va faoliyat turini erkin tanlash huquqini anglatadi, bu huquq mehnat shartnomasini ixtiyoriy tuzish orqali amalga oshiriladi."
    },
    {
        "question": "Qanday ishlar majburiy mehnat deb hisoblanmaydi?",
        "ground_truth": "Harbiy yoki muqobil xizmat vazifalarini bajarish, favqulodda vaziyatlar (tabiiy yoki texnogen xususiyatdagi ofatlar) sharoitida bajariladigan ishlar hamda sudning qonuniy kuchga kirgan hukmiga ko'ra bajariladigan majburiy ishlar majburiy mehnat deb hisoblanmaydi."
    },
    {
        "question": "Mehnat sohasidagi ijtimoiy sheriklik prinsipiga asoslangan holda mehnat toʻgʻrisidagi qonunchilik nimalarni kafolatlaydi?",
        "ground_truth": "Ijtimoiy sheriklik prinsipi xodimlar va ish beruvchilar manfaatlarini kelishish, jamoa shartnomalari va bitimlarini tuzish hamda mehnat nizolarini hal etishda ularning vakillarining ishtirok etishini kafolatlaydi."
    },
    {
        "question": "Normativ-huquqiy hujjatlarning xodimning huquqiy holatiga nisbatan qanday cheklovlari bor?",
        "ground_truth": "Mehnat to'g'risidagi qonunchilik yoki boshqa normativ hujjatlar xodimlarning huquqiy holatini amaldagi qonunlar belgilangan darajadan pastga tushirishi yoki ularning huquqlarini cheklashi mumkin emas."
    },
    {
        "question": "Mehnat toʻgʻrisidagi qonunchilikda muddatlarni hisoblash qanday amalga oshiriladi?",
        "ground_truth": "Muddatlar kalendar kunlari, oylar yoki yillar bilan belgilanadi, agar muddatning oxirgi kuni dam olish yoki ish kuni bo'lmagan kunga to'g'ri kelsa, undan keyingi birinchi ish kuni muddatning tugash kuni deb hisoblanadi."
    },
    {
        "question": "Qaysi shaxslarga mehnat toʻgʻrisidagi qonunchilik tatbiq etilmaydi?",
        "ground_truth": "Harbiy xizmatchilar, sudya lavozimida ishlayotgan shaxslar, qonun hujjatlarida belgilangan boshqa maxsus toifadagi shaxslarga umumiy mehnat to'g'risidagi qonunchilik tatbiq etilmaydi yoki o'ziga xos xususiyatlar bilan tartibga solinadi."
    },
    {
        "question": "Mehnat haqidagi boshqa huquqiy hujjatlar jumlasiga nimalar kiradi?",
        "ground_truth": "Boshqa huquqiy hujjatlarga jamoa kelishuvlari, jamoa shartnomalari, shuningdek ish beruvchi tomonidan xodimlar vakillik organi bilan kelishib qabul qilinadigan ichki idoraviy hujjatlar kiradi."
    },
    {
        "question": "Ichki hujjatlarning oʻzaro nisbati qanday tartibga solinadi va kasaba uyushmasi qoʻmitasining roziligi qancha muddatda berilishi kerak?",
        "ground_truth": "Ichki hujjatlar qonunchilikka zid kelmasligi kerak va kasaba uyushmasi qo'mitasi o'z roziligini yoki asoslangan e'tirozini qonunda belgilangan muddatda (odatda 10 ish kuni ichida) taqdim etishi lozim."
    },
    {
        "question": "Xodim va ish beruvchi yakka tartibdagi mehnat munosabatlarining subyektlari sifatida kimlar boʻlishi mumkin?",
        "ground_truth": "Xodim sifatida mehnat layoqatiga ega bo'lgan jismoniy shaxs, ish beruvchi sifatida esa xodim bilan mehnat munosabatlariga kirish huquqiga ega bo'lgan yuridik yoki jismoniy shaxs bo'lishi mumkin."
    },
    {
        "question": "Xodimning mehnatga oid huquq layoqati va muomala layoqati necha yoshdan vujudga keladi?",
        "ground_truth": "Mehnat huquq layoqati va muomala layoqati shaxs tug'ilganidan boshlab vujudga keladi, biroq mustaqil ravishda mehnat shartnomasini tuzish huquqi odatda 16 yoshdan (ayrim istisno holatlarda qonuniy vakillarning roziligi bilan undan kichik yoshda ham) yuzaga keladi."
    },
    {
        "question": "Xodimning asosiy majburiyatlari nimalardan iborat?",
        "ground_truth": "Mehnat shartnomasiga muvofiq o'z vazifalarini vicdonan bajarish, ichki mehnat tartibi qoidalariga rioya qilish, mehnat muhofazasi va texnika xavfsizligi talablariga bo'ysunish hamda ish beruvchining mol-mulkiga ehtiyotkorona munosabatda bo'lish."
    },
    {
        "question": "Ish beruvchining asosiy majburiyatlari qaysilar?",
        "ground_truth": "Xodimlarga mehnat shartnomasida kelishilgan ish haqini o'z vaqtida to'lash, xavfsiz mehnat sharoitlarini yaratish, ularni zarur vositalar bilan ta'minlash va mehnat qonunchiligiga to'liq rioya qilish."
    },
    {
        "question": "Yakka tartibdagi mehnatga oid munosabatlar qanday asoslarga koʻra yuzaga keladi?",
        "ground_truth": "Yakka tartibdagi mehnat munosabatlari xodim va ish beruvchi o'rtasida tuziladigan mehnat shartnomasi, shuningdek qonunda nazarda tutilgan boshqa asoslar (saylanish, tayinlanish yoki sud qarori) bo'yicha yuzaga keladi."
    },
    {
        "question": "Mehnat sohasidagi ijtimoiy sheriklikning darajalari qaysilar?",
        "ground_truth": "Ijtimoiy sheriklik respublika, tarmoq, hududiy va tashkilot darajalarida amalga oshirilishi mumkin."
    },
    {
        "question": "Mehnat jamoasining umumiy yigʻilishi (konferensiyasi) qaysi hollarda vakolatli hisoblanadi va uning qabul qilgan qarorlari qanday kuchga ega?",
        "ground_truth": "Agar yig'ilishda xodimlarning umumiy sonining yarmidan ko'pi (yoki konferensiyada delegatlarning kamida uchdan ikki qismi) qatnashsa vakolatli hisoblanadi va qabul qilingan qarorlar belgilangan tartibda majburiy kuchga ega bo'ladi."
    },
    {
        "question": "Xodimlarning vakillik organlari tarkibiga saylangan shaxslarga qanday mehnat kafolatlari beriladi?",
        "ground_truth": "Ushbu shaxslarga jamoatchilik vazifalarini bajarishi davrida asosiy ish joyi va o'rtacha ish haqi saqlab qolinishi, shuningdek ularni intizomiy javobgarlikka tortish yoki boshqa ishga o'tkazishda qo'shimcha kafolatlar taqdim etiladi."
    },
    {
        "question": "Jamoaviy muzokaralar jarayonida taraflar kelishuvga erisha olmasa, qanday hujjat tuziladi?",
        "ground_truth": "Taraflar kelishuvga erisha olmagan taqdirda, yuzaga kelgan kelishmovchiliklar bayonnomasi (kelishmovchiliklar to'g'risida dalolatnoma) tuziladi."
    }
]

# ==============================================================================
# RAGAS UCHUN LLM VA EMBEDDING (evaluator sifatida)
# ==============================================================================

_ragas_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4o-mini", temperature=0))
_ragas_embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings(model="text-embedding-3-small"))

# strictness=1 (standart 3 o'rniga) — answer_relevancy metrikasi bitta savol uchun
# bir necha marta (odatda 3) javob generatsiya qilishga urinadi, ba'zi modellar/proksilar
# buni qo'llab-quvvatlamaydi va "LLM returned 1 generations instead of requested 3" deb
# jimgina 1 tasi bilan davom etadi — bu natijani sun'iy pasaytiradi. strictness=1 bilan
# bu muammoning oldi olinadi.
_answer_relevancy = AnswerRelevancy(strictness=1)

# Standart 16 ta parallel worker o'rniga kamroq — Milvus/Postgres/LLM'ni haddan
# tashqari yuklamaslik va timeout xatolarining oldini olish uchun.
_ragas_run_config = RunConfig(max_workers=4)


# ==============================================================================
# BOT JAVOBLARI VA KONTEKSTLARINI YIG'ISH (keshlash bilan)
# ==============================================================================

def gather_contexts(chunks) -> list:
    context_texts = []
    for chunk in chunks:
        if hasattr(chunk, "chunk_text"):
            context_texts.append(chunk.chunk_text)
        elif hasattr(chunk, "page_content"):
            context_texts.append(chunk.page_content)
        elif isinstance(chunk, dict) and "text" in chunk:
            context_texts.append(chunk["text"])
        elif isinstance(chunk, dict) and "page_content" in chunk:
            context_texts.append(chunk["page_content"])
        else:
            context_texts.append(str(chunk))
    return context_texts or ["(hech qanday kontekst topilmadi)"]


def collect_records(bot_instance, test_cases: list) -> dict:
    questions, answers, contexts, ground_truths = [], [], [], []

    for case in test_cases:
        q = case["question"]
        gt = case["ground_truth"]

        bot_response, _usage = get_bot_response(bot=bot_instance, question=q)
        if not isinstance(bot_response, str):
            print(f"OGOHLANTIRISH: '{q}' uchun bot_response {type(bot_response)} turida edi, str()ga o'tkazildi")
            bot_response = str(bot_response)

        retrieved_chunks = retrieve_relevant_chunks(bot=bot_instance, query_text=q)
        context_texts = gather_contexts(retrieved_chunks)

        questions.append(q)
        answers.append(bot_response)
        contexts.append(context_texts)
        ground_truths.append(gt)

    return {
        "questions": questions,
        "answers": answers,
        "contexts": contexts,
        "ground_truths": ground_truths,
    }


def get_records(test_cases: list) -> dict:
    if _os.path.exists(CACHE_FILE):
        print("--- Keshdan o'qilmoqda (qayta so'rov yuborilmaydi) ---")
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    print("--- Test ma'lumotlari yig'ilmoqda va bot javoblari olinmoqda ---")
    bot_instance = Bot.objects.get(id=BOT_ID)
    records = collect_records(bot_instance, test_cases)

    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    return records


# ==============================================================================
# RAGAS BAHOLASH
# ==============================================================================

def run_ragas(records: dict):
    dataset = Dataset.from_dict(
        {
            "user_input": records["questions"],
            "response": records["answers"],
            "retrieved_contexts": records["contexts"],
            "reference": records["ground_truths"],
        }
    )
    return evaluate(
        dataset=dataset,
        metrics=[context_precision, context_recall, faithfulness, _answer_relevancy],
        llm=_ragas_llm,
        embeddings=_ragas_embeddings,
        run_config=_ragas_run_config,
    )


def main():
    if not TEST_CASES:
        raise ValueError(
            "TEST_CASES bo'sh! Fayl boshidagi TEST_CASES ro'yxatiga savol/javoblaringizni qo'shing."
        )

    records = get_records(TEST_CASES)

    print("--- Ragas baholash jarayoni boshlandi ---")
    result = run_ragas(records)

    print("\n=== BAHOLASH NATIJALARI ===")
    print(result)

    dataframe = result.to_pandas()
    print("\n=== DATAFRAME KO'RINISHIDA ===")
    print(dataframe[["user_input", "faithfulness", "answer_relevancy", "context_precision", "context_recall"]])

    dataframe.to_csv("eval_results.csv", index=False, encoding="utf-8-sig")
    print("\nTo'liq natijalar 'eval_results.csv' fayliga saqlandi.")


if __name__ == "__main__":
    main()