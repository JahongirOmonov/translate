# Generated by Django 5.0.6 on 2024-12-23 20:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0002_requiredchannels_chat_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='archive',
            name='file_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]