from django.db import models

from account.models import User, Sector


class Document(models.Model):
    """Rahbariyat/mas'ul xodim kiritgan hujjat (farmon, qaror, qonun, ...).

    Word fayl yoki lex.uz havolasi orqali kiritiladi, AI uning eng muhim
    joylarini (summary) ajratadi va test savollarini tuzadi.
    """

    DOCUMENT_CHOICES = [
        ("decree", "Фармон/Қарор"),
        ("law", "Қонун"),
        ("article", "Мақола"),
        ("other", "Бошқа"),
    ]
    SOURCE_CHOICES = [
        ("docx", "Word файл"),
        ("url", "lex.uz ҳавола"),
        ("manual", "Қўлда киритилган"),
    ]
    STATUS_CHOICES = [
        ("draft", "Қоралама"),
        ("generated", "AI тайёрлади"),
        ("published", "Юборилган"),
    ]
    TARGET_CHOICES = [
        ("all", "Барча ходимлар"),
        ("sector", "Шўъба бўйича"),
        ("users", "Танланган ходимлар"),
    ]

    title = models.CharField(max_length=512, verbose_name="Сарлавҳа")
    document_type = models.CharField(
        max_length=50, choices=DOCUMENT_CHOICES, default="other", verbose_name="Ҳужжат тури"
    )

    source_type = models.CharField(
        max_length=20, choices=SOURCE_CHOICES, default="manual", verbose_name="Манба тури"
    )
    source_file = models.FileField(
        upload_to="knowledge/docs/", blank=True, null=True, verbose_name="Word файл"
    )
    source_url = models.URLField(blank=True, null=True, verbose_name="lex.uz ҳавола")

    cover_image = models.FileField(
        upload_to="knowledge/covers/", blank=True, null=True, verbose_name="Муқова расм"
    )
    full_text = models.TextField(blank=True, default="", verbose_name="Тўлиқ матн")
    summary = models.TextField(blank=True, default="", verbose_name="Асосий мазмун (AI)")

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="draft", verbose_name="Ҳолат"
    )
    pass_threshold = models.PositiveIntegerField(
        default=70, verbose_name="Ўтиш чегараси (%)"
    )

    # Kimlarga yuboriladi
    target_type = models.CharField(
        max_length=20, choices=TARGET_CHOICES, default="all", verbose_name="Кимга"
    )
    target_sectors = models.ManyToManyField(
        Sector, blank=True, related_name="knowledge_documents", verbose_name="Шўъбалар"
    )
    target_users = models.ManyToManyField(
        User, blank=True, related_name="knowledge_targeted", verbose_name="Ходимлар"
    )

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="created_documents", verbose_name="Яратувчи"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Ҳужжат"
        verbose_name_plural = "Ҳужжатлар"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def question_count(self):
        return self.questions.count()

    def target_user_queryset(self):
        """target_type bo'yicha yuboriladigan xodimlar ro'yxati."""
        qs = User.objects.filter(is_active=True).exclude(chat_id__isnull=True).exclude(chat_id=0)
        if self.target_type == "sector":
            sector_ids = list(self.target_sectors.values_list("id", flat=True))
            qs = qs.filter(sector_id__in=sector_ids)
        elif self.target_type == "users":
            user_ids = list(self.target_users.values_list("id", flat=True))
            qs = qs.filter(id__in=user_ids)
        return qs


class Question(models.Model):
    document = models.ForeignKey(
        Document, related_name="questions", on_delete=models.CASCADE
    )
    text = models.TextField(verbose_name="Савол")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Савол"
        verbose_name_plural = "Саволлар"
        ordering = ["order", "id"]

    def __str__(self):
        return self.text[:80]


class AnswerOption(models.Model):
    question = models.ForeignKey(
        Question, related_name="options", on_delete=models.CASCADE
    )
    text = models.TextField(verbose_name="Вариант")
    is_correct = models.BooleanField(default=False, verbose_name="Тўғри жавоб")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Вариант"
        verbose_name_plural = "Вариантлар"
        ordering = ["order", "id"]

    def __str__(self):
        return self.text[:60]


class Assignment(models.Model):
    """Hujjat qaysi xodimga biriktirilgan."""

    document = models.ForeignKey(
        Document, related_name="assignments", on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        User, related_name="knowledge_assignments", on_delete=models.CASCADE
    )
    notified = models.BooleanField(default=False, verbose_name="Бот хабар юборди")
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Тайинлов"
        verbose_name_plural = "Тайинловлар"
        unique_together = ("document", "user")

    def __str__(self):
        return f"{self.document_id} → {self.user_id}"


class Attempt(models.Model):
    """Xodimning hujjatni o'qishi va testdan o'tishi."""

    assignment = models.ForeignKey(
        Assignment, related_name="attempts", on_delete=models.CASCADE
    )
    document = models.ForeignKey(
        Document, related_name="attempts", on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        User, related_name="knowledge_attempts", on_delete=models.CASCADE
    )

    read_done = models.BooleanField(default=False, verbose_name="Тўлиқ ўқиди")
    score = models.PositiveIntegerField(default=0, verbose_name="Тўғри жавоблар")
    total = models.PositiveIntegerField(default=0, verbose_name="Жами саволлар")
    percent = models.FloatField(default=0, verbose_name="Фоиз")
    passed = models.BooleanField(default=False, verbose_name="Ўтди")

    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Уриниш"
        verbose_name_plural = "Уринишлар"
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.user_id} — {self.document_id} ({self.percent}%)"


class AttemptAnswer(models.Model):
    attempt = models.ForeignKey(
        Attempt, related_name="answers", on_delete=models.CASCADE
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(
        AnswerOption, on_delete=models.SET_NULL, null=True, blank=True
    )
    is_correct = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Берилган жавоб"
        verbose_name_plural = "Берилган жавоблар"
