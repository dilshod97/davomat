from django.contrib import admin
from .models import Task, Attendance


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'task', 'start_date', 'end_date', 'created_at')
    search_fields = ('user__username', 'task')
    list_filter = ('start_date', 'end_date', 'created_at')
    ordering = ('-created_at',)


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'timestamp', 'latitude', 'longitude', 'created_at')
    search_fields = ('user__username', 'task_description')
    list_filter = ('timestamp', 'created_at')
    ordering = ('-created_at',)
    filter_horizontal = ('task',)
