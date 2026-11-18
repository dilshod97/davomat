from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import (
    AnswerOption,
    Assignment,
    Attempt,
    AttemptAnswer,
    Document,
)
from .serializers import (
    AttemptResultSerializer,
    DocumentListSerializer,
    DocumentReadSerializer,
    QuestionSerializer,
    SubmitSerializer,
)


def _get_assignment(user, document_id):
    """Xodimga biriktirilган hujjatni oladi, aks holda 404."""
    document = get_object_or_404(Document, id=document_id)
    assignment = Assignment.objects.filter(document=document, user=user).first()
    if not assignment:
        return None, None
    return document, assignment


def _get_or_create_attempt(assignment):
    attempt, _ = Attempt.objects.get_or_create(
        assignment=assignment,
        defaults={"document": assignment.document, "user": assignment.user},
    )
    return attempt


class MyDocumentsView(APIView):
    """Xodimga biriktirilgan hujjatlar ro'yxati."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        assignments = (
            Assignment.objects.filter(user=request.user)
            .select_related("document")
            .order_by("-created_at")
        )
        attempt_map = {
            a.document_id: a
            for a in Attempt.objects.filter(user=request.user)
        }
        documents = []
        for assignment in assignments:
            doc = assignment.document
            doc._my_attempt = attempt_map.get(doc.id)
            documents.append(doc)

        serializer = DocumentListSerializer(documents, many=True)
        return Response(serializer.data)


class DocumentReadView(APIView):
    """Hujjatni o'qish (summary + to'liq matn)."""

    permission_classes = [IsAuthenticated]

    def get(self, request, document_id):
        document, assignment = _get_assignment(request.user, document_id)
        if not assignment:
            return Response(
                {"detail": "Бу ҳужжат сизга тайинланмаган."},
                status=status.HTTP_403_FORBIDDEN,
            )
        attempt = _get_or_create_attempt(assignment)
        serializer = DocumentReadSerializer(document, context={"attempt": attempt})
        return Response(serializer.data)

    def post(self, request, document_id):
        """O'qib bo'ldim — read_done = True."""
        document, assignment = _get_assignment(request.user, document_id)
        if not assignment:
            return Response(
                {"detail": "Бу ҳужжат сизга тайинланмаган."},
                status=status.HTTP_403_FORBIDDEN,
            )
        attempt = _get_or_create_attempt(assignment)
        if not attempt.read_done:
            attempt.read_done = True
            attempt.save(update_fields=["read_done"])
        return Response({"read_done": True})


class QuizView(APIView):
    """Test savollari (to'g'ri javoblarsiz)."""

    permission_classes = [IsAuthenticated]

    def get(self, request, document_id):
        document, assignment = _get_assignment(request.user, document_id)
        if not assignment:
            return Response(
                {"detail": "Бу ҳужжат сизга тайинланмаган."},
                status=status.HTTP_403_FORBIDDEN,
            )
        questions = document.questions.prefetch_related("options")
        return Response({
            "document_id": document.id,
            "title": document.title,
            "pass_threshold": document.pass_threshold,
            "questions": QuestionSerializer(questions, many=True).data,
        })


class SubmitQuizView(APIView):
    """Test javoblarini qabul qilib, natijani hisoblaydi."""

    permission_classes = [IsAuthenticated]

    def post(self, request, document_id):
        document, assignment = _get_assignment(request.user, document_id)
        if not assignment:
            return Response(
                {"detail": "Бу ҳужжат сизга тайинланмаган."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = SubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        answers = serializer.validated_data["answers"]

        questions = list(document.questions.prefetch_related("options"))
        total = len(questions)
        if total == 0:
            return Response(
                {"detail": "Бу ҳужжатда тест саволлари йўқ."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # to'g'ri javoblar xaritasi
        correct_option = {}
        valid_options = {}  # question_id -> {option_id: option}
        for q in questions:
            for opt in q.options.all():
                valid_options.setdefault(q.id, {})[opt.id] = opt
                if opt.is_correct:
                    correct_option[q.id] = opt.id

        attempt = _get_or_create_attempt(assignment)
        # eski javoblarni tozalab, qayta yozamiz (qayta topshirish)
        attempt.answers.all().delete()

        score = 0
        answered = {a["question_id"]: a["option_id"] for a in answers}
        for q in questions:
            selected_id = answered.get(q.id)
            selected_opt = valid_options.get(q.id, {}).get(selected_id)
            is_correct = selected_id is not None and selected_id == correct_option.get(q.id)
            if is_correct:
                score += 1
            AttemptAnswer.objects.create(
                attempt=attempt,
                question=q,
                selected_option=selected_opt,
                is_correct=is_correct,
            )

        percent = round(score / total * 100, 1)
        attempt.score = score
        attempt.total = total
        attempt.percent = percent
        attempt.passed = percent >= document.pass_threshold
        attempt.finished_at = timezone.now()
        attempt.save(update_fields=["score", "total", "percent", "passed", "finished_at"])

        return Response(AttemptResultSerializer(attempt).data)
