from datetime import time

from account.models import User

from ..models import Attendance, Distance

DAILY_HEADERS = [
    "Ходим",
    "Лавозими",
    "Келган вақт",
    "Тизим вақти",
    "Масофа",
    "Ҳолат",
    "Амалга оширадиган ишлари",
    "Қаердалиги",
    "Изоҳ",
    "Жойлашув",
]


class ReportScopeError(Exception):
    """Foydalanuvchi uchun hisobot qamrovini aniqlash imkoni bo'lmaganda."""


def resolve_scope_users(user):
    """as_user qiymatiga qarab hisobotga kiradigan foydalanuvchilarni qaytaradi.

    0 -> faqat o'zi, 1 -> o'z sektori, 2 -> hammasi.
    """
    if user.as_user == 0:
        return User.objects.filter(id=user.id)
    if user.as_user == 1:
        if not user.sector_id:
            raise ReportScopeError("Фойдаланувчи секторга бириктирилмаган.")
        return User.objects.filter(sector_id=user.sector_id)
    if user.as_user == 2:
        return User.objects.all()
    raise ReportScopeError("as_user нотўғри қийматга эга.")


def _empty_row(user):
    return {
        "user": user.get_full_name() if hasattr(user, "get_full_name") else str(user),
        "position": getattr(user, "lavozim", "-"),
        "entered_time": "-",
        "system_time": "-",
        "distance": "-",
        "status": "Давомат киритмади",
        "tasks": "",
        "where_is_it": "-",
        "description": "",
        "location": "",
    }


def build_daily_report(users, day_obj, info_type="attendance"):
    """Berilgan kun uchun har bir foydalanuvchining oxirgi davomat yozuvini qatorga aylantiradi."""
    data = []

    for user in users:
        rec = Attendance.objects.filter(
            user=user, created_at__date=day_obj, info_type=info_type
        ).order_by("-created_at").first()

        if not rec:
            data.append(_empty_row(user))
            continue

        izoh = rec.task_description or ""

        if not rec.timestamp:
            holat = "Давомат киритмади"
        else:
            holat = "Кечикди" if rec.created_at.time() > time(9, 0) else "Ўз вақтида келди"

            other_address = Distance.objects.filter(
                attendance=rec, distance__gt=1000
            ).exists()

            if other_address:
                holat = "Шубҳали (жой узоқ)"
                izoh += " | Киритилган локация ва объект ўртасидаги масофа катта."

        tasks = list(rec.task.values_list("task", flat=True))
        task_list = "\n".join(f"{i + 1}. {t}" for i, t in enumerate(tasks)) if tasks else "-"

        data.append({
            "user": user.get_full_name() if hasattr(user, "get_full_name") else str(user),
            "position": getattr(user, "lavozim", "-"),
            "entered_time": rec.timestamp.strftime("%Y-%m-%d %H:%M") if rec.timestamp else "-",
            "system_time": rec.created_at.strftime("%Y-%m-%d %H:%M"),
            "distance": f"{rec.distance} м" if getattr(rec, "distance", None) else "-",
            "status": holat,
            "tasks": task_list,
            "where_is_it": rec.task_description,
            "description": izoh if info_type == "attendance" else rec.description,
            "location": f"https://yandex.com/maps/?pt={rec.longitude},{rec.latitude}&z=16&l=map",
        })

    return data
