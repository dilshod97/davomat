import os
import sys
import django
import asyncio

# project ildizini sys.path ga qo‘shamiz
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # <-- bu muhim!

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "davomat.settings")  # o‘zgarishi mumkin
django.setup()

from bot.bot_main import start_bot

if __name__ == "__main__":
    asyncio.run(start_bot())
