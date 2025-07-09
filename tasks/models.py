from django.db import models
from account.models import User


class Task(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    task = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)


class Attendance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    task = models.ManyToManyField(Task)
    task_description = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

