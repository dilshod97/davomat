from aiogram import Router, F
from aiogram.types import Message, Contact
from asgiref.sync import sync_to_async
from account.models import User
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from rest_framework_simplejwt.tokens import AccessToken


def generate_simplejwt_token(user):
    access = AccessToken.for_user(user)
    return str(access)


def contact_request_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📲 Телефон рақамни юбориш", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def webapp_button(user):
    print(generate_simplejwt_token(user))
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="📋 Давоматни киритиш",
                web_app=WebAppInfo(url=f"https://davomat-dev.netlify.app/?token={generate_simplejwt_token(user)}")  # <-- Web App URL
            )]
        ]
    )


router = Router()


@sync_to_async
def get_user_by_telegram_id(telegram_id):
    return User.objects.filter(chat_id=telegram_id).first()


@sync_to_async
def get_user_by_phone(phone):
    return User.objects.filter(phone=phone).first()


@sync_to_async
def attach_telegram_id(user, telegram_id):
    user.chat_id = telegram_id
    user.save()


@router.message(F.text == "/start")
async def start_handler(message: Message):
    user = await get_user_by_telegram_id(message.from_user.id)
    if user:
        await message.answer("✅ Сиз тизимдасиз!", reply_markup=webapp_button(user))
    else:
        await message.answer("📱 Илтимос, телефон рақамингизни юборинг:", reply_markup=contact_request_kb())


@router.message(F.contact)
async def contact_handler(message: Message):
    contact: Contact = message.contact
    phone = contact.phone_number

    user = await get_user_by_phone(phone)
    if user:
        await attach_telegram_id(user, message.from_user.id)
        await message.answer("✅ Рақамингиз тасдиқланди!", reply_markup=webapp_button(user))
    else:
        await message.answer("❌ Сиз рўйхатдан ўтмагансиз.\nИлтимос, админ билан боғланинг.")
