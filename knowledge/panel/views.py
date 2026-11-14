"""Mas'ul/super admin uchun alohida panel (session login/parol bilan)."""

import json
from functools import wraps

from django.contrib.auth import authenticate, login, logout
from django.db.models import Avg, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from account.models import Sector, User

from .. import services
from ..ai import AIError
from ..models import AnswerOption, Assignment, Attempt, Document, Question


def panel_login_required(view):
    """Faqat is_staff/is_superuser kira oladi, aks holda /panel/login/ ga."""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        u = request.user
        if not u.is_authenticated or not (u.is_staff or u.is_superuser):
            return redirect(f"/panel/login/?next={request.path}")
        return view(request, *args, **kwargs)

    return wrapper


# --------------------------------------------------------------------------- #
#  Auth
# --------------------------------------------------------------------------- #
def login_view(request):
    error = None
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user and (user.is_staff or user.is_superuser):
            login(request, user)
            return redirect(request.GET.get("next") or "/panel/")
        error = "Логин ёки парол нотўғри, ёки рухсат йўқ."
    return render(request, "panel/login.html", {"error": error})


def logout_view(request):
    logout(request)
    return redirect("/panel/login/")


# --------------------------------------------------------------------------- #
#  Dashboard
# --------------------------------------------------------------------------- #
@panel_login_required
def dashboard(request):
    documents = Document.objects.all().order_by("-created_at")
    rows = []
    for d in documents:
        finished = Attempt.objects.filter(document=d, finished_at__isnull=False)
        rows.append({
            "doc": d,
            "assigned": Assignment.objects.filter(document=d).count(),
            "finished": finished.count(),
            "passed": finished.filter(passed=True).count(),
        })
    stats = {
        "total": documents.count(),
        "published": documents.filter(status="published").count(),
        "draft": documents.exclude(status="published").count(),
    }
    return render(request, "panel/dashboard.html", {"rows": rows, "stats": stats})


# --------------------------------------------------------------------------- #
#  Hujjat yaratish / ko'rish / tahrirlash
# --------------------------------------------------------------------------- #
@panel_login_required
def document_new(request):
    if request.method == "POST":
        doc = Document.objects.create(
            title=request.POST.get("title", "").strip() or "Номсиз ҳужжат",
            document_type=request.POST.get("document_type", "other"),
            source_type=request.POST.get("source_type", "manual"),
            source_url=request.POST.get("source_url", "").strip() or None,
            full_text=request.POST.get("full_text", "").strip(),
            pass_threshold=int(request.POST.get("pass_threshold") or 70),
            created_by=request.user,
        )
        if request.FILES.get("source_file"):
            doc.source_file = request.FILES["source_file"]
            doc.source_type = "docx"
        if request.FILES.get("cover_image"):
            doc.cover_image = request.FILES["cover_image"]
        doc.save()
        return redirect(f"/panel/documents/{doc.id}/")
    return render(request, "panel/document_form.html", {
        "document_types": Document.DOCUMENT_CHOICES,
    })


@panel_login_required
def document_detail(request, document_id):
    doc = get_object_or_404(Document, id=document_id)
    questions = doc.questions.prefetch_related("options")
    sectors = Sector.objects.all().order_by("name")
    users = (
        User.objects.filter(is_active=True)
        .exclude(chat_id__isnull=True).exclude(chat_id=0)
        .order_by("last_name", "first_name")
    )
    return render(request, "panel/document_detail.html", {
        "doc": doc,
        "questions": questions,
        "document_types": Document.DOCUMENT_CHOICES,
        "sectors": sectors,
        "users": users,
        "selected_sectors": set(doc.target_sectors.values_list("id", flat=True)),
        "selected_users": set(doc.target_users.values_list("id", flat=True)),
    })


@panel_login_required
@require_POST
def action_analyze(request, document_id):
    doc = get_object_or_404(Document, id=document_id)
    try:
        n = int(request.POST.get("n_questions") or 10)
        services.analyze_document(doc, n_questions=n)
        return JsonResponse({"ok": True})
    except AIError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)
    except Exception as exc:
        return JsonResponse({"ok": False, "error": f"Хатолик: {exc}"}, status=500)


@panel_login_required
@require_POST
def save_document(request, document_id):
    """Summary, savollar, chegaraga va kimga yuborilishini saqlaydi (JSON)."""
    doc = get_object_or_404(Document, id=document_id)
    data = json.loads(request.body or "{}")

    doc.title = (data.get("title") or doc.title).strip()
    doc.summary = data.get("summary", doc.summary)
    doc.pass_threshold = int(data.get("pass_threshold") or doc.pass_threshold)
    doc.target_type = data.get("target_type", doc.target_type)
    doc.save()

    doc.target_sectors.set(data.get("sector_ids", []))
    doc.target_users.set(data.get("user_ids", []))

    # savollar
    questions = data.get("questions")
    if questions is not None:
        doc.questions.all().delete()
        for qi, q in enumerate(questions):
            question = Question.objects.create(document=doc, text=q.get("text", "").strip(), order=qi)
            for oi, opt in enumerate(q.get("options", [])):
                AnswerOption.objects.create(
                    question=question,
                    text=(opt.get("text") or "").strip(),
                    is_correct=bool(opt.get("is_correct")),
                    order=oi,
                )
    if doc.status == "draft" and doc.questions.exists():
        doc.status = "generated"
        doc.save(update_fields=["status"])

    return JsonResponse({"ok": True})


@panel_login_required
@require_POST
def upload_cover(request, document_id):
    doc = get_object_or_404(Document, id=document_id)
    if request.FILES.get("cover_image"):
        doc.cover_image = request.FILES["cover_image"]
        doc.save(update_fields=["cover_image"])
    return redirect(f"/panel/documents/{doc.id}/")


@panel_login_required
@require_POST
def action_publish(request, document_id):
    doc = get_object_or_404(Document, id=document_id)
    if not doc.questions.exists():
        return JsonResponse({"ok": False, "error": "Аввал тест саволларини тайёрланг."}, status=400)
    try:
        stats = services.publish_document(doc)
        return JsonResponse({"ok": True, **stats})
    except Exception as exc:
        return JsonResponse({"ok": False, "error": f"Хатолик: {exc}"}, status=500)


# --------------------------------------------------------------------------- #
#  Statistika
# --------------------------------------------------------------------------- #
@panel_login_required
def document_stats(request, document_id):
    doc = get_object_or_404(Document, id=document_id)
    finished = Attempt.objects.filter(document=doc, finished_at__isnull=False).select_related("user")
    assigned = Assignment.objects.filter(document=doc).select_related("user")

    done_ids = set(finished.values_list("user_id", flat=True))
    not_done = [a for a in assigned if a.user_id not in done_ids]

    summary = {
        "assigned": assigned.count(),
        "finished": finished.count(),
        "passed": finished.filter(passed=True).count(),
        "failed": finished.filter(passed=False).count(),
        "read": Attempt.objects.filter(document=doc, read_done=True).count(),
        "avg_percent": round(finished.aggregate(a=Avg("percent"))["a"] or 0, 1),
        "not_finished": len(not_done),
    }

    def full_name(u):
        return f"{u.last_name} {u.first_name} {u.middle_name or ''}".strip()

    results = [{
        "name": full_name(a.user),
        "read_done": a.read_done,
        "score": a.score, "total": a.total, "percent": a.percent, "passed": a.passed,
        "finished_at": a.finished_at,
    } for a in finished.order_by("-percent")]

    pending = [{"name": full_name(a.user)} for a in not_done]

    return render(request, "panel/stats.html", {
        "doc": doc, "summary": summary, "results": results, "pending": pending,
    })
