# Generated by Django 5.2.4 on 2025-07-15 10:53

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0002_district_region_task_district_district_region_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='MinistryTree',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=512, null=True)),
                ('inn', models.CharField(max_length=150, unique=True)),
                ('soha', models.CharField(max_length=512)),
                ('katta_otasi', models.CharField(max_length=150, null=True)),
                ('daraja', models.CharField(max_length=150, null=True)),
                ('status', models.CharField(max_length=150, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('parent', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='children', to='tasks.ministrytree')),
            ],
        ),
        migrations.AddField(
            model_name='task',
            name='ministry',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='task', to='tasks.ministrytree'),
        ),
    ]
