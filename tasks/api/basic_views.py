"""HTTP Basic auth bilan ishlaydigan hisobot API'lari.

Bu endpoint'lar tashqi integratsiyalar uchun: JWT token olish shart emas,
oddiy username/parol (Basic Authorization header) yetarli.
"""

import io
from datetime import datetime

from django.http import HttpResponse
from openpyxl import Workbook
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .report_utils import (
    DAILY_HEADERS,
    ReportScopeError,
    build_daily_report,
    daily_excel_row,
    resolve_scope_users,
)


class BasicDailyReportView(APIView):
    """GET /api/davomat/basic/daily-report/?day=2026-10-27

    Параметрлар:
        day        — мажбурий, YYYY-MM-DD
        info_type  — ихтиёрий, default "attendance"
        is_excel   — ихтиёрий, true бўлса .xlsx файл юкланади
    """

    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        day = request.query_params.get("day")
        info_type = request.query_params.get("info_type", "attendance")
        is_excel = request.query_params.get("is_excel", "false").lower() == "true"

        if not day:
            return Response({"error": "Сана киритилмади (day параметри керак)."}, status=400)

        try:
            day_obj = datetime.strptime(day, "%Y-%m-%d").date()
        except ValueError:
            return Response({"error": "Сана формати нотўғри. Масалан: 2026-10-27"}, status=400)

        try:
            users = resolve_scope_users(request.user)
        except ReportScopeError as exc:
            return Response({"error": str(exc)}, status=400)

        data = build_daily_report(users, day_obj, info_type)

        if is_excel:
            return self._excel_response(data, day)

        return Response({"kun": day, "hisobot": data})

    @staticmethod
    def _excel_response(data, day):
        wb = Workbook()
        ws = wb.active
        ws.title = "Кунлик ҳисобот"
        ws.append(DAILY_HEADERS)

        for row in data:
            ws.append(daily_excel_row(row))

        stream = io.BytesIO()
        wb.save(stream)
        stream.seek(0)

        response = HttpResponse(
            stream.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="kunlik_hisobot_{day}.xlsx"'
        return response
