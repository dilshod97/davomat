from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from handlers import start


bot = Bot(token='7988185659:AAHkp0AnenS5_P674Tkf47baNJ3uM3azwRU', default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


async def start_bot():
    dp.include_routers(start.router)
    await dp.start_polling(bot)
