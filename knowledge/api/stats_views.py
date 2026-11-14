from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Assignment, Attempt, Document


class DocumentStatsView(APIView):
    """Bitta hujjat bo'yicha statistika (mas'ul xodim uchun)."""

    permission_classes = [IsAuthenticated]

    def get(self, request, document_id):
        document = get_object_or_404(Document, id=document_id)

        total_assigned = Assignment.objects.filter(document=document).count()
        attempts = Attempt.objects.filter(document=document)

        read_count = attempts.filter(read_done=True).count()
        finished = attempts.filter(finished_at__isnull=False)
        passed_count = finished.filter(passed=True).count()
        avg_percent = finished.aggregate(a=Avg("percent"))["a"] or 0

        # kim topshirmagan
        done_user_ids = set(finished.values_list("user_id", flat=True))
        not_done = (
            Assignment.objects.filter(document=document)
            .exclude(user_id__in=done_user_ids)
            .select_related("user")
        )

        rows = []
        for a in finished.select_related("user"):
            u = a.user
            rows.append({
                "user_id": u.id,
                "full_name": f"{u.last_name} {u.first_name} {u.middle_name or ''}".strip(),
                "read_done": a.read_done,
                "score": a.score,
                "total": a.total,
                "percent": a.percent,
                "passed": a.passed,
                "finished_at": a.finished_at,
            })

        return Response({
            "document": {"id": document.id, "title": document.title, "pass_threshold": document.pass_threshold},
            "summary": {
                "assigned": total_assigned,
                "read": read_count,
                "finished": finished.count(),
                "passed": passed_count,
                "failed": finished.count() - passed_count,
                "avg_percent": round(avg_percent, 1),
                "not_finished": total_assigned - finished.count(),
            },
            "results": rows,
            "not_finished_users": [
                {
                    "user_id": a.user_id,
                    "full_name": f"{a.user.last_name} {a.user.first_name} {a.user.middle_name or ''}".strip(),
                }
                for a in not_done
            ],
        })


class DocumentStatsListView(APIView):
    """Barcha hujjatlar bo'yicha qisqa statistika."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        documents = Document.objects.filter(status="published").order_by("-published_at")
        data = []
        for d in documents:
            attempts = Attempt.objects.filter(document=d, finished_at__isnull=False)
            assigned = Assignment.objects.filter(document=d).count()
            finished = attempts.count()
            passed = attempts.filter(passed=True).count()
            data.append({
                "id": d.id,
                "title": d.title,
                "assigned": assigned,
                "finished": finished,
                "passed": passed,
                "published_at": d.published_at,
            })
        return Response(data)
