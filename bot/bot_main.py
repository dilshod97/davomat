from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from handlers import start


bot = Bot(token='7403081531:AAFUzHrxX5LOmLlhlksis2Gqj7NnWjL5gxQ', default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


async def start_bot():
    dp.include_routers(start.router)
    await dp.start_polling(bot)
