from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django import forms
from .models import (
    MinistryTree,
    Region,
    District,
    Task,
    Attendance,
    Distance,
    Reminder,
    News,
    NewsMedia,
)


class MinistryTreeForm(forms.ModelForm):
    class Meta:
        model = MinistryTree
        fields = '__all__'

    class Media:
        css = {
            'all': (
                'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',
                'https://unpkg.com/leaflet-control-geocoder/dist/Control.Geocoder.css',
                'https://unpkg.com/leaflet.locatecontrol/dist/L.Control.Locate.min.css',
            )
        }
        js = (
            'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js',
            'https://unpkg.com/leaflet-control-geocoder/dist/Control.Geocoder.js',
            'https://unpkg.com/leaflet.locatecontrol/dist/L.Control.Locate.min.js',
            '/static/js/map_picker.js',
        )

@admin.register(MinistryTree)
class MinistryTreeAdmin(admin.ModelAdmin):
    form = MinistryTreeForm
    list_display = (
        "id", "name", "name_cr", "inn", "soha", "daraja", "katta_otasi", "status", "parent"
    )
    search_fields = ("name", "name_cr", "inn", "soha", "katta_otasi")
    list_filter = ("status", "daraja")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("name",)


# ---------------------------
# Region
# ---------------------------
@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ("id", "name_uz", "name_ru", "name_cr", "name_en")
    search_fields = ("name_uz", "name_ru", "name_cr")
    ordering = ("name_uz",)


# ---------------------------
# District
# ---------------------------
@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ("id", "name_uz", "region", "pid")
    list_filter = ("region",)
    search_fields = ("name_uz", "name_ru", "region__name_uz")
    ordering = ("region__name_uz", "name_uz")


# ---------------------------
# Task
# ---------------------------
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "id", "user", "region", "district", "ministry", "start_date", "end_date", "is_active"
    )
    list_filter = ("is_active", "is_deleted", "region", "district")
    search_fields = ("task", "user__username", "region__name_uz", "district__name_uz")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)

    actions = ["make_inactive", "make_active"]

    def make_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} ta topshiriq o‘chirildi.")
    make_inactive.short_description = "Tanlangan topshiriqlarni faol emas deb belgilash"

    def make_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} ta topshiriq faollashtirildi.")
    make_active.short_description = "Tanlangan topshiriqlarni faollashtirish"


# ---------------------------
# Attendance
# ---------------------------
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "timestamp", "latitude", "longitude", "created_at")
    search_fields = ("user__username",)
    list_filter = ("user", "timestamp")
    readonly_fields = ("created_at",)
    ordering = ("-timestamp",)


# ---------------------------
# Distance
# ---------------------------
@admin.register(Distance)
class DistanceAdmin(admin.ModelAdmin):
    list_display = ("id", "attendance", "distance", "created_at")
    search_fields = ("attendance__user__username",)
    list_filter = ("created_at",)
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)


# ---------------------------
# Reminder
# ---------------------------
@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "alert_date", "repeat_type", "created_at")
    list_filter = ("repeat_type", "alert_date")
    search_fields = ("title", "description")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-alert_date",)

    actions = ["set_daily", "set_weekly", "set_none"]

    def set_daily(self, request, queryset):
        updated = queryset.update(repeat_type="daily")
        self.message_user(request, f"{updated} ta eslatma kunlik qilib o‘zgartirildi.")
    set_daily.short_description = "Tanlangan eslatmalarni kunlik qilish"

    def set_weekly(self, request, queryset):
        updated = queryset.update(repeat_type="weekly")
        self.message_user(request, f"{updated} ta eslatma haftalik qilib o‘zgartirildi.")
    set_weekly.short_description = "Tanlangan eslatmalarni haftalik qilish"

    def set_none(self, request, queryset):
        updated = queryset.update(repeat_type="none")
        self.message_user(request, f"{updated} ta eslatma qaytmaslikka o‘zgartirildi.")
    set_none.short_description = "Tanlangan eslatmalarni qaytmaydigan qilish"


# ---------------------------
# NewsMedia inline
# ---------------------------
class NewsMediaInline(admin.TabularInline):
    model = NewsMedia
    extra = 1
    fields = ("media_type", "file_preview", "file", "url")
    readonly_fields = ("file_preview",)

    def file_preview(self, obj):
        if obj.media_type == "image" and obj.file:
            return format_html('<img src="{}" style="max-height:100px; border-radius:8px;" />', obj.file.url)
        elif obj.url:
            return format_html('<a href="{}" target="_blank">Link</a>', obj.url)
        return "-"
    file_preview.short_description = "Preview"


# ---------------------------
# News
# ---------------------------
@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = (
        "id", "title", "document_type", "document_date", "created_at", "link"
    )
    list_filter = ("document_type", "document_date")
    search_fields = ("title", "summary")
    readonly_fields = ("created_at", "updated_at")
    inlines = [NewsMediaInline]
    ordering = ("-document_date",)

    actions = ["mark_as_decree", "mark_as_law"]

    def mark_as_decree(self, request, queryset):
        updated = queryset.update(document_type="decree")
        self.message_user(request, f"{updated} ta yangilik 'Фармон/Қарор' turiga o‘zgartirildi.")
    mark_as_decree.short_description = "Tanlangan yangiliklarni 'Фармон/Қарор' turiga o‘tkazish"

    def mark_as_law(self, request, queryset):
        updated = queryset.update(document_type="law")
        self.message_user(request, f"{updated} ta yangilik 'Қонун' turiga o‘zgartirildi.")
    mark_as_law.short_description = "Tanlangan yangiliklarni 'Қонун' turiga o‘tkazish"


# ---------------------------
# NewsMedia (faqat agar alohida kerak bo‘lsa)
# ---------------------------
@admin.register(NewsMedia)
class NewsMediaAdmin(admin.ModelAdmin):
    list_display = ("id", "news", "media_type", "file", "url")
    list_filter = ("media_type",)
    search_fields = ("news__title",)
