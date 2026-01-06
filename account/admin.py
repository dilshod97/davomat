from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Sector
from django.contrib import admin, messages
import asyncio
from aiogram.client.default import DefaultBotProperties
from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from rest_framework_simplejwt.tokens import AccessToken


def generate_simplejwt_token(user):
    access = AccessToken.for_user(user)
    return str(access)


bot = Bot(token='7988185659:AAHkp0AnenS5_P674Tkf47baNJ3uM3azwRU', default=DefaultBotProperties(parse_mode=ParseMode.HTML))


def webapp_button(user):
    print(generate_simplejwt_token(user))
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="📋 Давоматни киритиш",
                web_app=WebAppInfo(url=f"https://davomat-dev.netlify.app/information?token={generate_simplejwt_token(user)}")
            )]
        ]
    )


def send_webapp_to_users(modeladmin, request, queryset):
    users = list(
        queryset
        .filter(is_active=True)
        .exclude(chat_id__isnull=True)
        .values("id", "chat_id")
    )

    async def _send():
        sent = 0

        for u in users:
            try:
                user = User(id=u["id"])

                await bot.send_message(
                    chat_id=u["chat_id"],
                    text="📢 Давоматни киритиш учун тугмани босинг:",
                    reply_markup=webapp_button(user)
                )
                sent += 1
                await asyncio.sleep(0.05)

            except TelegramForbiddenError:
                continue

            except TelegramRetryAfter as e:
                await asyncio.sleep(e.retry_after)

            except Exception as e:
                print(f"Xatolik {u['chat_id']}: {e}")

        return sent

    sent_count = asyncio.run(_send())

    messages.success(
        request,
        f"✅ {sent_count} ta foydalanuvchiga WebApp yuborildi"
    )


send_webapp_to_users.short_description = "📋 Маълумотнома киритиш тугмасини юбориш"


@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name', 'ministries')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Shaxsiy maʼlumotlar', {
            'fields': (
                'first_name', 'last_name', 'middle_name', 'birth_date', 'pinfl',
                'phone', 'chat_id', 'img'
            )
        }),
        ('Tashkiliy', {
            'fields': (
                'sector', 'organization', 'lavozim', 'profiles', 'my_mehnat_inn',
                'as_user', 'is_admin', 'position', 'sector_leader'
            )
        }),
        ('Ruxsatlar', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Muhim vaqtlar', {'fields': ('last_login', 'date_joined')}),
    )

    list_display = ('username', 'first_name', 'last_name', 'phone', 'sector', 'is_staff', 'is_superuser')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'sector')
    search_fields = ('username', 'first_name', 'last_name', 'phone', 'pinfl')

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'phone', 'password1', 'password2', 'sector'),
        }),
    )
    actions = [send_webapp_to_users]
