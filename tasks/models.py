from django.db import models
from account.models import User


class MinistryTree(models.Model):
    name = models.CharField(max_length=512, null=True)
    parent = models.ForeignKey('MinistryTree', on_delete=models.DO_NOTHING, related_name='children', null=True)
    inn = models.CharField(max_length=150, null=False, unique=True)
    soha = models.CharField(max_length=512, null=False)
    katta_otasi = models.CharField(max_length=150, null=True)
    daraja = models.CharField(max_length=150, null=True)
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

