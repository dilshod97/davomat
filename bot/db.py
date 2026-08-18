from functools import wraps

from asgiref.sync import sync_to_async
from django.db import InterfaceError, OperationalError, close_old_connections


def db_sync_to_async(func):
    """Django ORM funksiyasini async qilib o'raydi.

    Bot uzoq ishlaydigan process bo'lgani uchun HTTP so'rovlardagidek
    close_old_connections() avtomatik chaqirilmaydi. Shu sababli har bir
    so'rovdan oldin va keyin uni o'zimiz chaqiramiz, ulanish o'lik bo'lsa
    bir marta qayta urinamiz.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        for attempt in range(2):
            close_old_connections()
            try:
                return func(*args, **kwargs)
            except (InterfaceError, OperationalError):
                close_old_connections()
                if attempt:
                    raise
            finally:
                close_old_connections()

    return sync_to_async(wrapper)
