# Generated by Django 5.0.6 on 2024-12-25 05:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0004_rename_title_archive_content_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='archive',
            old_name='type',
            new_name='title',
        ),
    ]
