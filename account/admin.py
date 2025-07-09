from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Sector


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
