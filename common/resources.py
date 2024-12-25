from import_export import resources, fields
from import_export.widgets import ManyToManyWidget, ForeignKeyWidget, DateTimeWidget
from common import models


class TelegramProfileResource(resources.ModelResource):
    created_at = fields.Field(attribute='created_at', column_name='created_at',
                              widget=DateTimeWidget("%m/%d/%Y, %I:%M:%S %p"))
    updated_at = fields.Field(
        attribute="updated_at", column_name="updated_at", widget=DateTimeWidget("%m/%d/%Y, %I:%M:%S %p")
    )

    class Meta:
        model = models.TelegramProfile
        fields = (
            'id',
            'chat_id',
            'username',
            'first_name',
            'lastname',
            'language',
            'role',
            'created_at',
            'updated_at'
        )


class LanguageResource(resources.ModelResource):
    created_at = fields.Field(attribute='created_at', column_name='created_at',
                              widget=DateTimeWidget("%m/%d/%Y, %I:%M:%S %p"))
    updated_at = fields.Field(
        attribute="updated_at", column_name="updated_at", widget=DateTimeWidget("%m/%d/%Y, %I:%M:%S %p")
    )

    class Meta:
        model =models.Language
        fields = (
            'id',
            'title',
            'code',
            'created_at',
            'updated_at',
        )


class CodeResource(resources.ModelResource):
    created_at = fields.Field(attribute='created_at', column_name='created_at',
                              widget=DateTimeWidget("%m/%d/%Y, %I:%M:%S %p"))
    updated_at = fields.Field(
        attribute="updated_at", column_name="updated_at", widget=DateTimeWidget("%m/%d/%Y, %I:%M:%S %p")
    )

    class Meta:
        model = models.Code
        fields = (
            'id',
            'title',
            'created_at',
            'updated_at'
        )


class TextResource(resources.ModelResource):
    code = fields.Field(
        attribute='code',
        column_name='code',
        widget=ForeignKeyWidget(model=models.Code, field='title')
    )
    language = fields.Field(
        attribute='language',
        column_name='language',
        widget=ForeignKeyWidget(model=models.Language, field='title')
    )

    created_at = fields.Field(attribute='created_at', column_name='created_at',
                              widget=DateTimeWidget("%m/%d/%Y, %I:%M:%S %p"))
    updated_at = fields.Field(
        attribute="updated_at", column_name="updated_at", widget=DateTimeWidget("%m/%d/%Y, %I:%M:%S %p")
    )

    class Meta:
        model = models.Text
        fields = (
            'id',
            'value',
            'code',
            'type',
            'language',
            'order',
            'created_at',
            'updated_at'
        )


