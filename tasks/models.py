from django.db import models
from account.models import User


class MinistryTree(models.Model):
    name = models.CharField(max_length=512, null=True)
    parent = models.ForeignKey('MinistryTree', on_delete=models.DO_NOTHING, related_name='children', null=True)
    inn = models.CharField(max_length=150, null=False, unique=True)
    soha = models.CharField(max_length=512, null=False)
    katta_otasi = models.CharField(max_length=150, null=True)
    daraja = models.CharField(max_length=150, null=True)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    status = models.CharField(max_length=150, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name


class Region(models.Model):
    id = models.AutoField(primary_key=True)
    name_uz = models.CharField(max_length=255)
    name_ru = models.CharField(max_length=255)
    name_cr = models.CharField(max_length=255)
    name_en = models.CharField(max_length=255, null=True)

    def __str__(self):
        return self.name_uz


class District(models.Model):
    id = models.AutoField(primary_key=True)
    name_uz = models.CharField(max_length=255, null=True)
    name_ru = models.CharField(max_length=255, null=True)
    name_cr = models.CharField(max_length=255, null=True)
    pid = models.BigIntegerField(default=0)
    region = models.ForeignKey(Region, on_delete=models.DO_NOTHING, related_name='region', null=False)


class Task(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    task = models.TextField()
    ministry = models.ForeignKey(MinistryTree, on_delete=models.DO_NOTHING, related_name='task', null=True)
    region = models.ForeignKey(Region, on_delete=models.DO_NOTHING, related_name='task', null=True)
    district = models.ForeignKey(District, on_delete=models.DO_NOTHING, related_name='task', null=True)
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    is_deleted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Attendance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    task = models.ManyToManyField(Task)
    task_description = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)


class Distance(models.Model):
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE)
    distance = models.FloatField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Reminder(models.Model):
    REPEAT_CHOICES = [
        ("none", "Qaytmaydi"),
        ("daily", "Kunlik"),
        ("weekly", "Haftalik"),
        ("monthly", "Oylik"),
        ("yearly", "Yillik"),
    ]

    title = models.CharField(max_length=255, verbose_name="Qisqa matn")
    description = models.TextField(blank=True, null=True, verbose_name="To‘liq matn")
    alert_date = models.DateField(verbose_name="Ogohlantirish sanasi")
    repeat_type = models.CharField(
        max_length=10, choices=REPEAT_CHOICES, default="none", verbose_name="Qaytarilish turi"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class News(models.Model):
    DOCUMENT_CHOICES = [
        ("decree", "Фармон/Қарор"),
        ("law", "Қонун"),
        ("article", "Мақола"),
        ("other", "Бошқа"),
    ]

    document_type = models.CharField(
        max_length=50, choices=DOCUMENT_CHOICES, default="other", verbose_name="Ҳужжат тури"
    )
    title = models.CharField(max_length=255, verbose_name="Янгилик сарлавҳаси")
    summary = models.TextField(verbose_name="Қисқа мазмун")
    link = models.URLField(blank=True, null=True, verbose_name="Ссылка")
    document_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Янгилик"
        verbose_name_plural = "Янгиликлар"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class NewsMedia(models.Model):
    MEDIA_TYPE_CHOICES = [
        ("image", "Расм"),
        ("video", "Видео"),
        ("file", "file"),
    ]

    news = models.ForeignKey(News, related_name="media", on_delete=models.CASCADE)
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES)
    file = models.FileField(upload_to="news/media/", blank=True, null=True)
    url = models.URLField(blank=True, null=True)

    class Meta:
        verbose_name = "Янгилик медиа"
        verbose_name_plural = "Янгилик медиа файллари"

    def __str__(self):
        return f"{self.media_type} - {self.news.title}"



