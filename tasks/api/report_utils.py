from datetime import time

from account.models import User

from ..models import Attendance, Distance

# Excel ustunlari: kalit -> sarlavha, tartib muhim.
DAILY_EXCEL_FIELDS = [
    ("user", "Ходим"),
    ("position", "Лавозими"),
    ("entered_time", "Келган вақт"),
    ("system_time", "Тизим вақти"),
    ("distance", "Масофа"),
    ("status", "Ҳолат"),
    ("tasks", "Амалга оширадиган ишлари"),
    ("where_is_it", "Қаердалиги"),
    ("description", "Изоҳ"),
    ("location", "Жойлашув"),
    ("username", "Логин"),
    ("phone", "Телефон"),
    ("pinfl", "ЖШШИР (ПИНФЛ)"),
]

DAILY_HEADERS = [header for _, header in DAILY_EXCEL_FIELDS]


def daily_excel_row(row):
    """Hisobot qatorini Excel ustunlari tartibida ro'yxatga aylantiradi."""
    return [row.get(key, "") for key, _ in DAILY_EXCEL_FIELDS]


def _clean(value):
    """Bo'sh yoki model default'i ("0") bo'lsa "-" qaytaradi."""
    value = (str(value) if value is not None else "").strip()
    return value if value and value != "0" else "-"


def _user_identity(user):
    return {
        "username": _clean(user.username),
        "phone": _clean(getattr(user, "phone", "")),
        "pinfl": _clean(getattr(user, "pinfl", "")),
    }


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
        **_user_identity(user),
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
            **_user_identity(user),
            "entered_time": rec.timestamp.strftime("%Y-%m-%d %H:%M:%S") if rec.timestamp else "-",
            "system_time": rec.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "distance": f"{rec.distance} м" if getattr(rec, "distance", None) else "-",
            "status": holat,
            "tasks": task_list,
            "where_is_it": rec.task_description,
            "description": izoh if info_type == "attendance" else rec.description,
            "location": f"https://yandex.com/maps/?pt={rec.longitude},{rec.latitude}&z=16&l=map",
        })

    return data
