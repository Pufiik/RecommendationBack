import re
from django.contrib import admin
from app.models import *
import ast
from import_export import resources, fields
from import_export.widgets import Widget
from import_export.admin import ImportExportModelAdmin
from .models import Article


class ListWidget(Widget):
    def clean(self, value, row=None, *args, **kwargs):
        if not value:
            return []
        flat = value.replace('\n', ' ')
        flat = re.sub(r'(?<=[\d\]\)])\s+(?=[\d\-\[])', ',', flat)
        return ast.literal_eval(flat)

    def render(self, value, obj=None):
        return str(value)


class ArticleResource(resources.ModelResource):
    embedding = fields.Field(
        column_name='embedding',
        attribute='embedding',
        widget=ListWidget()
    )

    class Meta:
        model = Article
        fields = (
            'id',
            'title',
            'annotation',
            'content',
            'language',
            'embedding',
            'created_at',
        )
        import_id_fields = ('id',)


@admin.register(Article)
class ArticleAdmin(ImportExportModelAdmin):
    resource_class = ArticleResource
    list_display = ('title', 'language', 'created_at')


admin.site.register(ArticleInteraction)
admin.site.register(UserProfile)
