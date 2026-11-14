from django.contrib import admin, messages

from . import services
from .models import (
    AnswerOption,
    Assignment,
    Attempt,
    AttemptAnswer,
    Document,
    Question,
)


class AnswerOptionInline(admin.TabularInline):
    model = AnswerOption
    extra = 0


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 0
    show_change_link = True


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "document_type", "status", "question_count", "target_type", "created_at")
    list_filter = ("status", "document_type", "target_type")
    search_fields = ("title",)
    readonly_fields = ("full_text", "summary", "status", "published_at", "created_at", "updated_at")
    filter_horizontal = ("target_sectors", "target_users")
    inlines = [QuestionInline]
    actions = ("action_analyze", "action_publish")

    fieldsets = (
        ("Ҳужжат", {
            "fields": ("title", "document_type", "source_type", "source_file", "source_url", "pass_threshold")
        }),
        ("Кимга юборилади", {
            "fields": ("target_type", "target_sectors", "target_users")
        }),
        ("AI натижаси", {
            "fields": ("summary", "full_text", "status", "published_at")
        }),
    )

    @admin.action(description="🤖 AI билан таҳлил қилиш (summary + тест)")
    def action_analyze(self, request, queryset):
        for document in queryset:
            try:
                services.analyze_document(document)
                self.message_user(
                    request,
                    f"✅ «{document.title}» таҳлил қилинди ({document.question_count} савол).",
                    level=messages.SUCCESS,
                )
            except Exception as exc:
                self.message_user(
                    request, f"❌ «{document.title}»: {exc}", level=messages.ERROR
                )

    @admin.action(description="📣 Ходимларга юбориш (бот орқали)")
    def action_publish(self, request, queryset):
        for document in queryset:
            if document.status == "draft":
                self.message_user(
                    request,
                    f"⚠️ «{document.title}» — аввал AI таҳлилидан ўтказинг.",
                    level=messages.WARNING,
                )
                continue
            try:
                stats = services.publish_document(document)
                self.message_user(
                    request,
                    f"✅ «{document.title}» юборилди: {stats['sent']}/{stats['total']} "
                    f"(хато: {stats['failed']}).",
                    level=messages.SUCCESS,
                )
            except Exception as exc:
                self.message_user(
                    request, f"❌ «{document.title}»: {exc}", level=messages.ERROR
                )

    def save_model(self, request, obj, form, change):
        if not obj.created_by_id and request.user.is_authenticated:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("text", "document", "order")
    list_filter = ("document",)
    inlines = [AnswerOptionInline]


class AttemptAnswerInline(admin.TabularInline):
    model = AttemptAnswer
    extra = 0
    readonly_fields = ("question", "selected_option", "is_correct")
    can_delete = False


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ("user", "document", "percent", "passed", "read_done", "finished_at")
    list_filter = ("passed", "read_done", "document")
    search_fields = ("user__username", "user__first_name", "user__last_name")
    readonly_fields = ("assignment", "document", "user", "score", "total", "percent", "passed", "read_done", "started_at", "finished_at")
    inlines = [AttemptAnswerInline]


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("document", "user", "notified", "sent_at")
    list_filter = ("notified", "document")
    search_fields = ("user__username", "user__first_name", "user__last_name")
