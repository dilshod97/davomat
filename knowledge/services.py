"""Hujjat ustidagi amallar: matn ajratish, AI tahlil, botga yuborish."""

from django.db import transaction
from django.utils import timezone

from . import ai
from .models import AnswerOption, Assignment, Document, Question


def extract_text(document: Document) -> str:
    """Hujjat manbasiga qarab matnni ajratadi va full_text ga yozadi."""
    if document.source_type == "docx" and document.source_file:
        text = ai.extract_text_from_docx(document.source_file)
    elif document.source_type == "url" and document.source_url:
        text = ai.extract_text_from_url(document.source_url)
    else:
        text = document.full_text or ""

    document.full_text = text
    document.save(update_fields=["full_text", "updated_at"])
    return text


@transaction.atomic
def analyze_document(document: Document, n_questions: int = 10) -> Document:
    """To'liq AI tahlil: matn ajratish → summary + savollar → bazaga saqlash."""
    text = document.full_text
    if not text or document.source_type in ("docx", "url"):
        text = extract_text(document)

    result = ai.generate_summary_and_questions(text, n_questions=n_questions)

    document.summary = result["summary"]
    document.status = "generated"
    document.save(update_fields=["summary", "status", "updated_at"])

    # eski savollarni tozalab, yangisini yozamiz
    document.questions.all().delete()
    for q_index, q in enumerate(result["questions"]):
        question = Question.objects.create(
            document=document, text=q["text"], order=q_index
        )
        for o_index, opt_text in enumerate(q["options"]):
            AnswerOption.objects.create(
                question=question,
                text=opt_text,
                is_correct=(o_index == q["correct_index"]),
                order=o_index,
            )

    return document


def assign_users(document: Document):
    """target_type bo'yicha xodimlarga Assignment yaratadi."""
    users = document.target_user_queryset()
    created = []
    for user in users:
        obj, _ = Assignment.objects.get_or_create(document=document, user=user)
        created.append(obj)
    return created


def publish_document(document: Document):
    """Xodimlarga tayinlab, bot orqali yuboradi."""
    from .broadcast import send_document_to_user

    assignments = assign_users(document)

    sent, failed = 0, 0
    for assignment in assignments:
        if assignment.notified:
            continue
        ok = send_document_to_user(document, assignment.user)
        if ok:
            assignment.notified = True
            assignment.sent_at = timezone.now()
            assignment.save(update_fields=["notified", "sent_at"])
            sent += 1
        else:
            failed += 1

    document.status = "published"
    document.published_at = timezone.now()
    document.save(update_fields=["status", "published_at", "updated_at"])

    return {"total": len(assignments), "sent": sent, "failed": failed}
