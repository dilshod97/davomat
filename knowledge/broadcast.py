"""Telegram bot orqali xodimlarga hujjat + test knopkalarini yuborish.

Django tomonidan (sync) to'g'ridan-to'g'ri Telegram Bot API ga requests
orqali yuboriladi — bot process'iga bog'liq emas.
"""

import html
import re

import requests
from django.conf import settings
from rest_framework_simplejwt.tokens import AccessToken

TYPE_EMOJI = {
    "decree": "📜",
    "law": "⚖️",
    "article": "📰",
    "other": "📄",
}
TYPE_HASHTAG = {
    "decree": "фармон_қарор",
    "law": "қонун",
    "article": "мақола",
    "other": "ҳужжат",
}


def _token(user) -> str:
    return str(AccessToken.for_user(user))


def _webapp_urls(document, user):
    base = settings.WEBAPP_BASE_URL.rstrip("/")
    token = _token(user)
    read_url = f"{base}/knowledge/read/{document.id}/?token={token}"
    quiz_url = f"{base}/knowledge/quiz/{document.id}/?token={token}"
    return read_url, quiz_url


def _summary_excerpt(summary: str, limit: int = 450) -> str:
    """Markdown summary'dan qisqa, toza parcha (blockquote uchun)."""
    if not summary:
        return ""
    text = re.sub(r"[*_#>`]+", "", summary)  # markdown belgilarini olib tashlash
    text = re.sub(r"^\s*[-•]\s*", "• ", text, flags=re.MULTILINE)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    text = "\n".join(lines)
    if len(text) > limit:
        text = text[:limit].rsplit(" ", 1)[0] + "…"
    return html.escape(text)


def build_caption(document) -> str:
    emoji = TYPE_EMOJI.get(document.document_type, "📄")
    type_label = document.get_document_type_display()
    title = html.escape(document.title)
    excerpt = _summary_excerpt(document.summary)
    n = document.question_count
    hashtag = TYPE_HASHTAG.get(document.document_type, "ҳужжат")

    parts = [
        f"📣 <b>ЯНГИ ҲУЖЖАТ</b> · {emoji} {html.escape(type_label)}",
        "",
        f"{emoji} <b>{title}</b>",
    ]
    if excerpt:
        parts += ["", f"<blockquote expandable>{excerpt}</blockquote>"]
    parts += [
        "",
        f"📝 <b>{n}</b> та тест саволи   ·   🎯 Ўтиш: <b>{document.pass_threshold}%</b>",
        "",
        "Қуйидаги тугмалар орқали ҳужжатни ўқинг ва тестдан ўтинг 👇",
        "",
        f"#билим #тест #{hashtag}",
    ]
    return "\n".join(parts)


def _keyboard(read_url, quiz_url):
    return {
        "inline_keyboard": [
            [{"text": "📖 Тўлиқ ўқиш", "web_app": {"url": read_url}}],
            [{"text": "✅ Тестдан ўтиш", "web_app": {"url": quiz_url}}],
        ]
    }


def send_document_to_user(document, user) -> bool:
    """Bitta xodimga chiroyli xabar (rasm bo'lsa — rasm bilan) + knopkalar."""
    if not user.chat_id:
        return False

    read_url, quiz_url = _webapp_urls(document, user)
    caption = build_caption(document)
    keyboard = _keyboard(read_url, quiz_url)
    api = f"https://api.telegram.org/bot{settings.BOT_TOKEN}"

    cover = getattr(document, "cover_image", None)
    default_cover = getattr(settings, "KNOWLEDGE_DEFAULT_COVER", "")

    try:
        if cover:
            # yuklangan muqova rasm — multipart bilan
            cover.open("rb")
            try:
                resp = requests.post(
                    f"{api}/sendPhoto",
                    data={
                        "chat_id": user.chat_id,
                        "caption": caption[:1024],
                        "parse_mode": "HTML",
                        "reply_markup": __import__("json").dumps(keyboard),
                    },
                    files={"photo": cover},
                    timeout=60,
                )
            finally:
                cover.close()
        elif default_cover:
            resp = requests.post(
                f"{api}/sendPhoto",
                json={
                    "chat_id": user.chat_id,
                    "photo": default_cover,
                    "caption": caption[:1024],
                    "parse_mode": "HTML",
                    "reply_markup": keyboard,
                },
                timeout=60,
            )
        else:
            resp = requests.post(
                f"{api}/sendMessage",
                json={
                    "chat_id": user.chat_id,
                    "text": caption,
                    "parse_mode": "HTML",
                    "reply_markup": keyboard,
                    "disable_web_page_preview": True,
                },
                timeout=30,
            )
        return resp.status_code == 200 and resp.json().get("ok", False)
    except requests.RequestException:
        return False
