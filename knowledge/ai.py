"""AI qatlami: hujjat matnini ajratish va GLM orqali summary + test tuzish."""

import json
import re
import time

import requests
from django.conf import settings


class AIError(Exception):
    pass


# --------------------------------------------------------------------------- #
#  Matn ajratish
# --------------------------------------------------------------------------- #
def extract_text_from_docx(file_field) -> str:
    """Word (.docx) fayldan matn ajratadi."""
    from docx import Document as DocxDocument

    file_field.open("rb")
    try:
        doc = DocxDocument(file_field)
    finally:
        file_field.close()

    parts = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            parts.append(text)

    # jadvallardagi matn ham
    for table in doc.tables:
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells if c.text.strip()]
            if cells:
                parts.append(" | ".join(cells))

    return "\n".join(parts).strip()


def extract_text_from_url(url: str) -> str:
    """lex.uz yoki boshqa havoladan matn ajratadi (best-effort)."""
    from bs4 import BeautifulSoup

    resp = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; davomat-bot/1.0)"},
        timeout=60,
        verify=False,
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()

    # Qonun matni asosan <p>/<li>/<td> va sarlavhalarda bo'ladi; menyu va
    # ulashish tugmalari esa <a>/<div>/<span> da — shu sababli faqat matnli
    # teglarni, hujjat tartibida yig'amiz (lex.uz uchun toza natija beradi).
    JUNK = {
        "telegram", "facebook", "twitter", "instagram", "ulashish", "online translate",
        "рус", "eng", "ўзб", "o‘zb", "o’zb", "a", "hammasi",
    }
    content_tags = soup.find_all(["h1", "h2", "h3", "h4", "p", "li", "td", "th"])
    lines = []
    seen = set()
    for tag in content_tags:
        txt = tag.get_text(" ", strip=True)
        if not txt or txt.lower() in JUNK:
            continue
        key = (id(tag.parent), txt)
        if txt in seen and len(txt) < 40:
            continue
        seen.add(txt)
        lines.append(txt)

    text = "\n".join(lines).strip()

    # Agar matnli teglardan kam chiqsa — butun sahifa matniga qaytamiz
    if len(text) < 400:
        container = soup.find("article") or soup.find("main") or soup.body or soup
        raw = container.get_text(separator="\n")
        text = "\n".join(ln.strip() for ln in raw.splitlines() if ln.strip()).strip()

    return text


# --------------------------------------------------------------------------- #
#  GLM chaqirish
# --------------------------------------------------------------------------- #
def _chat(messages, temperature=0.3, max_tokens=16000) -> str:
    try:
        resp = requests.post(
            settings.GLM_API_URL,
            headers={
                "Authorization": f"Bearer {settings.GLM_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.GLM_MODEL,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                # GLM reasoning model: o'ylash yoqilsa butun token limiti
                # reasoning_content ga ketib, content bo'sh qaytadi.
                "thinking": {"type": "disabled"},
            },
            timeout=settings.GLM_TIMEOUT,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise AIError(f"GLM API xatosi: {exc}") from exc

    data = resp.json()
    try:
        choice = data["choices"][0]
        content = choice["message"].get("content") or ""
    except (KeyError, IndexError, AttributeError) as exc:
        raise AIError(f"GLM javobi kutilmagan formatda: {data}") from exc
    if not content.strip():
        raise AIError(
            f"GLM bo'sh javob qaytardi (finish_reason={choice.get('finish_reason')})."
        )
    return content


def _parse_json(content: str) -> dict:
    """GLM javobidan JSON ni ajratib oladi (```json ... ``` bo'lsa ham)."""
    content = content.strip()
    # ```json ... ``` fence ni olib tashlash
    fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", content, re.DOTALL)
    if fence:
        content = fence.group(1)
    else:
        # birinchi { dan oxirgi } gacha
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1:
            content = content[start:end + 1]

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise AIError(f"GLM JSON javobini o'qib bo'lmadi: {exc}") from exc
    if not isinstance(data, dict):
        raise AIError("GLM JSON javobi obyekt emas.")
    return data


SYSTEM_PROMPT = (
    "Siz O'zbekiston qonunchiligi va rasmiy hujjatlari bo'yicha mutaxassis "
    "hamda tajribali test tuzuvchisiz. Doim faqat to'g'ri JSON qaytaring, "
    "hech qanday izoh yoki matn qo'shmang."
)


def build_prompt(text: str, n_questions: int) -> str:
    return (
        "Quyida rasmiy hujjat matni berilgan (farmon/qaror/qonun).\n"
        "Vazifang:\n"
        "1) Hujjatning eng muhim va amaliy ahamiyatga ega qoidalarini "
        "xodim tez tushunadigan qilib qisqa bayon qil. summary — markdown "
        "ko'rinishida, 6-15 ta band (bullet) bo'lsin.\n"
        f"2) Shu hujjat mazmunidan {n_questions} ta test savoli tuz. Har savolda "
        "4 ta variant bo'lsin va faqat bittasi to'g'ri bo'lsin. Savollar "
        "hujjatning mohiyatini tekshirsin, juda yengil yoki aldamchi bo'lmasin.\n"
        "Hamma matn o'zbek tilida bo'lsin.\n\n"
        "Javobni QAT'IY quyidagi JSON formatida ber:\n"
        '{"summary": "markdown matn", "questions": ['
        '{"text": "savol matni", "options": ["variant1","variant2","variant3","variant4"], '
        '"correct_index": 0}]}\n\n'
        "Hujjat matni:\n"
        "\"\"\"\n"
        f"{text}\n"
        "\"\"\""
    )


def generate_summary_and_questions(text: str, n_questions: int = 10) -> dict:
    """GLM orqali summary va test savollarini tuzadi.

    Qaytaradi: {"summary": str, "questions": [{"text", "options": [...], "correct_index"}]}
    """
    if not text or not text.strip():
        raise AIError("Hujjat matni bo'sh — AI uchun matn yo'q.")

    # Juda uzun matnlarni cheklaymiz (model konteksti uchun)
    max_chars = getattr(settings, "GLM_MAX_INPUT_CHARS", 40000)
    clipped = text[:max_chars]

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_prompt(clipped, n_questions)},
    ]
    # Model ba'zan buzilgan JSON qaytaradi — vaqt yetsa qayta urinamiz
    # (gunicorn timeout 300s, shuning uchun jami ~150s dan oshirmaymiz).
    started = time.monotonic()
    last_error = None
    for _attempt in range(3):
        if last_error and time.monotonic() - started > 150:
            break
        try:
            data = _parse_json(_chat(messages))
            cleaned = _clean_questions(data.get("questions") or [])
            if not cleaned:
                raise AIError("AI test savollarini qaytarmadi. Qayta urinib ko'ring.")
            return {"summary": (data.get("summary") or "").strip(), "questions": cleaned}
        except AIError as exc:
            last_error = exc
    raise last_error


def _clean_questions(questions) -> list:
    """Minimal validatsiya: matnsiz yoki 2 tadan kam variantli savollar tashlanadi."""
    cleaned = []
    for q in questions:
        if not isinstance(q, dict):
            continue
        opts = q.get("options") or []
        if not q.get("text") or len(opts) < 2:
            continue
        ci = q.get("correct_index", 0)
        if not isinstance(ci, int) or ci < 0 or ci >= len(opts):
            ci = 0
        cleaned.append({"text": str(q["text"]).strip(), "options": [str(o).strip() for o in opts], "correct_index": ci})
    return cleaned
