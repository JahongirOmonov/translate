from import_export.admin import ImportExportModelAdmin
from django.contrib import admin

from django.apps import apps

from .models import *
from .resources import (
    TelegramProfileResource,
    LanguageResource,
    CodeResource,
    TextResource
)


class TextInline(admin.TabularInline):
    extra = 0
    model = Text


@admin.register(TelegramProfile)
class TelegramProfileAdmin(ImportExportModelAdmin):
    list_display = ('id', 'chat_id', 'username', 'first_name', 'created_at', 'role')
    list_display_links = ('chat_id', 'username',)
    list_editable = ('role',)
    list_filter = ('role',)
    search_fields = ('chat_id', 'username', 'first_name', 'role')
    resource_class = TelegramProfileResource


@admin.register(Archive)
class ArchiveAdmin(ImportExportModelAdmin):
    list_display = ('short_title', 'author', 'created_at')

    def short_title(self, obj):
        return obj.type[:100]
    short_title.short_description = 'Type'


@admin.register(Language)
class LanguageAdmin(ImportExportModelAdmin):
    list_display = ('id', 'title', 'code')
    list_display_links = 'title', 'code'
    resource_class = LanguageResource


@admin.register(Code)
class CodeAdmin(ImportExportModelAdmin):
    list_display = ('id', 'title')
    list_display_links = ('title',)
    search_fields = ('title',)
    inlines = (TextInline,)
    resource_class = CodeResource




@admin.register(Text)
class TextAdmin(ImportExportModelAdmin):
    list_display = ('id', 'value', 'code', 'language', 'order', 'type')
    list_display_links = ('value', 'code')
    search_fields = ('value', 'code')
    resource_class = TextResource


for model in apps.get_models():
    try:
        admin.site.register(model)
    except admin.sites.AlreadyRegistered:
        pass





