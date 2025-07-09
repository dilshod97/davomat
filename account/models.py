from django.db import models
from django.contrib.auth.models import AbstractUser


class Sector(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=512)
    ministries = models.TextField(null=True)
    profiles = models.TextField(null=True)
    one_profiles = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name


class User(AbstractUser):
    pinfl = models.CharField(max_length=150)
    sector = models.ForeignKey(Sector, on_delete=models.DO_NOTHING, related_name='user_sector', null=True)
    my_mehnat_inn = models.CharField(max_length=255, null=True)
    middle_name = models.CharField(max_length=150, blank=True, null=True)
    birth_date = models.DateField(default=None, null=True, blank=True)
    as_user = models.IntegerField(default=1)
    is_admin = models.IntegerField(default=0)
    lavozim = models.CharField(max_length=150, blank=True, null=True)
    profiles = models.TextField(null=True)
    phone = models.CharField(max_length=150, blank=False, null=False, default=0)
    chat_id = models.BigIntegerField(default=0, null=True)
    img = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    organization = models.TextField()
    position = models.IntegerField(default=0)
    sector_leader = models.BooleanField(default=False, null=True)

    def __str__(self):
        return self.username