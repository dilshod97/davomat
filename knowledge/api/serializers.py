from rest_framework import serializers

from ..models import AnswerOption, Attempt, Document, Question


class OptionSerializer(serializers.ModelSerializer):
    """Variant — to'g'ri javob ko'rsatilmaydi (xodim uchun)."""

    class Meta:
        model = AnswerOption
        fields = ("id", "text")


class QuestionSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ("id", "text", "options")


class DocumentReadSerializer(serializers.ModelSerializer):
    """Hujjatni o'qish sahifasi uchun."""

    question_count = serializers.IntegerField(read_only=True)
    my_attempt = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = (
            "id", "title", "document_type", "summary", "full_text",
            "pass_threshold", "question_count", "published_at", "my_attempt",
        )

    def get_my_attempt(self, obj):
        attempt = self.context.get("attempt")
        if not attempt:
            return None
        return {
            "read_done": attempt.read_done,
            "passed": attempt.passed,
            "percent": attempt.percent,
            "finished_at": attempt.finished_at,
        }


class DocumentListSerializer(serializers.ModelSerializer):
    question_count = serializers.IntegerField(read_only=True)
    passed = serializers.SerializerMethodField()
    read_done = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = ("id", "title", "document_type", "question_count", "published_at", "passed", "read_done")

    def get_passed(self, obj):
        attempt = getattr(obj, "_my_attempt", None)
        return attempt.passed if attempt else False

    def get_read_done(self, obj):
        attempt = getattr(obj, "_my_attempt", None)
        return attempt.read_done if attempt else False


class SubmitAnswerSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    option_id = serializers.IntegerField()


class SubmitSerializer(serializers.Serializer):
    answers = SubmitAnswerSerializer(many=True)


class AttemptResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attempt
        fields = ("id", "score", "total", "percent", "passed", "finished_at")
