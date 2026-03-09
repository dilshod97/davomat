from rest_framework.views import APIView
from rest_framework.response import Response
from openpyxl import Workbook
from django.utils.timezone import make_aware
from django.db.models import Count, Case, When, Value, CharField
import io
from django.utils import timezone
from account.api.permission import AuthRemoteChecking, HasPermissionToAPI
from account.models import User
from rest_framework.permissions import IsAuthenticated
from datetime import datetime, time
from ..models import Attendance, Task, Distance
import requests

BOT_TOKEN = "7988185659:AAHkp0AnenS5_P674Tkf47baNJ3uM3azwRU"
BOT_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"


from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import time, date


class SummaryReportView(APIView):
    permission_classes = [HasPermissionToAPI]
    authentication_classes = [AuthRemoteChecking]

    def get(self, request):
        print(request.user)
        info_type = request.query_params.get("info_type", "attendance")
        today = date.today()

        users = User.objects.all()

        user_ids = list(users.values_list("id", flat=True))

        # BUGUNGI ATTENDANCE
        attendances = (
            Attendance.objects
            .filter(user_id__in=user_ids, created_at__date=today, info_type=info_type)
            .select_related("user")
        )

        attendance_map = {a.user_id: a for a in attendances}

        results = {
            "staff": users.count(),
            "in_office": [],
            "in_object_tashkent": [],
            "in_object_region": [],
            "ill": [],
            "in_remote": [],
            "exclude": [],
            "in_vacation": [],
            "not_entered": [],
            "lates": [],
            "tibbiy_korik_idora": [],
            "tibbiy_korik_obyekt": []

        }

        d = {
            "idora": "Идорада",
            "obyekt_tashkent": "Объектда (Тошкент ш.)",
            "obyekt_hudud": "Объектда (Ҳудуд)",
            "tibbiy_korik_idora": "Тиббий кўрик (Идорага бораман)",
            "tibbiy_korik_obyekt": "Тиббий кўрик (Объектга бораман)",
            "kasal": "Касал",
            "masofaviy": "Масофавий",
            "taatil": "Таътил",
            "ruxsat_olganman": "Рухсат олганман",
        }

        where_map = {
            "idora": "in_office",
            "obyekt_tashkent": "in_object_tashkent",
            "obyekt_hudud": "in_object_region",
            "kasal": "ill",
            "tibbiy_korik_idora": "tibbiy_korik_idora",
            "tibbiy_korik_obyekt": "tibbiy_korik_obyekt",
            "masofaviy": "in_remote",
            "taatil": "in_vacation",
            "ruxsat_olganman": "exclude"
        }

        for u in users:

            rec = attendance_map.get(u.id)

            full_name = f"{u.first_name} {getattr(u, 'middle_name', '')} {u.last_name}".strip()

            name = full_name

            if not rec:
                results["not_entered"].append({
                    "user": {
                        "name": name,
                        "pinfl": u.pinfl
                    }
                })
                continue

            status_key = rec.task_description

            work = ""
            for i, data in enumerate(rec.task.all()):
                work += f"{i + 1}. {data.task}\n"

            item = {
                "user": {
                    "name": name,
                    "pinfl": u.pinfl
                },
                "where": {
                    "value": status_key,
                    "name": d.get(status_key)
                },
                "location": {
                    "reason": None,
                    "address": None
                },
                "_id": str(rec.id),
                "entered_at": rec.timestamp.strftime("%H:%M") if rec.timestamp else None,
                "unix_time": int(rec.created_at.timestamp()),
                "works": work
            }
            if rec.created_at.time() > time(9, 0):
                results["lates"].append(item)

            category = where_map.get(status_key)

            if category:
                results[category].append(item)

        return Response({
            "isOk": True,
            "message": None,
            "results": results
        })


from datetime import date, timedelta
from itertools import groupby
from rest_framework.views import APIView
from rest_framework.response import Response


class ReportView(APIView):
    permission_classes = [HasPermissionToAPI]
    authentication_classes = [AuthRemoteChecking]

    def post(self, request):
        info_type = request.data.get("info_type", "attendance")
        start_date = request.data.get("start_date", date.today())
        end_date = request.data.get("end_date")
        if start_date and end_date:
            if isinstance(start_date, str):
                start_date = date.fromisoformat(start_date)
            if isinstance(end_date, str):
                end_date = date.fromisoformat(end_date)

            users = User.objects.select_related("sector").order_by("sector__ordering", "position")

            attendances = (
                Attendance.objects
                .filter(created_at__date__range=[start_date, end_date], info_type=info_type)
                .select_related("user")
                .order_by("user_id", "-created_at")
            )

            # Har bir user bo‘yicha oxirgi attendance har kun uchun
            attendance_map = {}
            for user_id, group in groupby(attendances, key=lambda x: x.user_id):
                attendance_map[user_id] = {}
                for a in group:
                    day = a.created_at.date()
                    if day not in attendance_map[user_id]:
                        attendance_map[user_id][day] = a  # oxirgi (order_by -created_at bo‘yicha)

            # Dates listi
            dates_list = []
            current_date = start_date
            while current_date <= end_date:
                dates_list.append({
                    "p": str(current_date),
                    "is_sunday": current_date.weekday() == 6  # endi current_date albatta date
                })
                current_date += timedelta(days=1)

            sectors = {}

            for u in users:
                sector_name = u.sector.name if u.sector else "Сектор бириктирилмаган"
                if sector_name not in sectors:
                    sectors[sector_name] = {
                        "sector_name": sector_name,
                        "members": []
                    }

                periods = []
                for d in dates_list:
                    period_date = date.fromisoformat(d["p"])
                    rec = attendance_map.get(u.id, {}).get(period_date)
                    if rec:
                        entered = int(rec.created_at.timestamp())
                    else:
                        entered = "-"
                    periods.append({
                        "period": d["p"],
                        "is_sunday": d["is_sunday"],
                        "user": u.username,
                        "entered": entered
                    })
                full_name = f"{u.first_name} {getattr(u, 'middle_name', '')} {u.last_name}".strip()
                member = {
                    "user": u.username,
                    "name": full_name,
                    "pname": getattr(u, "lavozim", ""),
                    "periods": periods
                }

                sectors[sector_name]["members"].append(member)

            return Response({
                "isOk": True,
                "results": {
                    "dates": dates_list,
                    "off": list(sectors.values())
                }
            })
        else:
            users = User.objects.select_related("sector").order_by("sector__ordering", "position")

            # Attendance yozuvlarini oxirgi bo'yicha olish
            attendances = (
                Attendance.objects
                .filter(created_at__date=start_date, info_type=info_type)
                .select_related("user")
                .order_by("user_id", "-created_at")  # user bo'yicha kamayuvchi tartib
            )

            # Foydalanuvchi bo'yicha oxirgi attendance ni olish
            attendance_map = {}
            for user_id, group in groupby(attendances, key=lambda x: x.user_id):
                attendance_map[user_id] = list(group)[0]  # -created_at bo‘yicha birinchi = oxirgi

            # Event dictionary
            d = {
                "idora": "Идорада",
                "obyekt_tashkent": "Объектда (Тошкент ш.)",
                "obyekt_hudud": "Объектда (Ҳудуд)",
                "tibbiy_korik_idora": "Тиббий кўрик (Идорага бораман)",
                "tibbiy_korik_obyekt": "Тиббий кўрик (Объектга бораман)",
                "kasal": "Касал",
                "masofaviy": "Масофавий",
                "taatil": "Таътил",
                "ruxsat_olganman": "Рухсат олганман",
            }

            sectors = {}

            for u in users:
                sector_name = u.sector.name if u.sector else "Сектор бириктирилмаган"
                if sector_name not in sectors:
                    sectors[sector_name] = {
                        "sector_name": sector_name,
                        "members": []
                    }

                rec = attendance_map.get(u.id)

                work = ""
                entered = None
                unix_time = None
                event = None
                latitude = None
                longitude = None
                rec_id = None

                if rec:
                    rec_id = str(rec.id)

                    for i, data in enumerate(rec.task.all()):
                        work += f"{i + 1}. {data.task}\n"

                    entered = rec.timestamp.strftime("%H:%M") if rec.timestamp else None
                    unix_time = int(rec.created_at.timestamp())
                    event = d.get(rec.task_description)
                    latitude = rec.latitude
                    longitude = rec.longitude

                full_name = f"{u.first_name} {getattr(u, 'middle_name', '')} {u.last_name}".strip()

                member = {
                    "_id": rec_id,
                    "uimage": getattr(u, "img", "") or "",
                    "fname": full_name,
                    "pname": getattr(u, "lavozim", ""),
                    "contacts": {
                        "office": getattr(u, "office_phone", ""),
                        "tablet": getattr(u, "extra_phone", ""),
                        "mobile": getattr(u, "mobile_phone", "")
                    },
                    "entered": entered,
                    "unix_time": unix_time,
                    "event": event,
                    "works": work,
                    "location": {
                        "coordinates": {
                            "latitude": latitude,
                            "longitude": longitude
                        },
                        "reason": None,
                        "address": None
                    }
                }

                sectors[sector_name]["members"].append(member)

            results = list(sectors.values())

            return Response({
                "isOk": True,
                "message": None,
                "results": results
            })