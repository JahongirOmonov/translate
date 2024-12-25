from datetime import timezone, datetime
from termios import BSDLY

from django.db import models
from utils import BaseModel, Profile, TextType
from ckeditor.fields import RichTextField


# Create your models here.


class TelegramProfile(Profile):
    objects = models.Manager()

    class Meta:
        ordering = ('-created_at', 'role')

    def __str__(self):
        return self.username if self.username else self.first_name


class BannedUser(models.Model):
    telegram_profile = models.ForeignKey(TelegramProfile, on_delete=models.CASCADE, related_name='bans')
    reason = models.TextField()
    banned_until = models.DateTimeField()  # Qachongacha ban bo'lishi kerak
    banned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.telegram_profile.first_name




class Language(BaseModel):
    title = models.CharField(max_length=31)
    code = models.CharField(max_length=31, unique=True)

    def __str__(self):
        return self.title


class Code(BaseModel):
    title = models.CharField(max_length=255, unique=True)

    objects = models.Manager()

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return self.title


class Text(BaseModel):
    value = RichTextField()
    type = models.CharField(max_length=31, choices=TextType.choices, default=TextType.TEXT)

    code = models.ForeignKey(Code, on_delete=models.CASCADE)
    language = models.ForeignKey(Language, on_delete=models.CASCADE)

    order = models.PositiveSmallIntegerField(default=0)

    objects = models.Manager()

    class Meta:
        ordering = ('-created_at',)

    def save(self, *args, **kwargs):
        if self.order > 0:
            self.type = TextType.BUTTON
        super().save(*args, **kwargs)

    def __str__(self):
        return self.value


class RequiredChannels(BaseModel):
    title = models.CharField(max_length=255, verbose_name="Channel Name")
    url = models.URLField(max_length=511, unique=True, help_text="For example: https://t.me/anychannel")
    username = models.CharField(max_length=255, editable=False, blank=True, null=True)
    chat_id = models.CharField(max_length=255, blank=True, null=True)

    objects = models.Manager()

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.username:
            usernames = str(self.url).split('/')
            self.username = usernames[-1] if usernames[-1] != '' else usernames[-2]

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Archive(BaseModel):
    type = models.CharField(max_length=255, blank=True, null=True)
    content = models.TextField()
    author = models.ForeignKey(TelegramProfile, on_delete=models.CASCADE, related_name='archives')

    def __str__(self):
        return self.title[:20]