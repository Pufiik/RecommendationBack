from django.core.management.base import BaseCommand
from django.db.models import Count

from app.models import Article


class Command(BaseCommand):
    help = 'Удаляет дубликаты статей по полю annotation, оставляя только самую старую запись.'

    def handle(self, *args, **options):
        duplicates = (
            Article.objects
            .values('annotation')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
        )

        total_deleted = 0

        for entry in duplicates:
            ann = entry['annotation']
            pks = list(
                Article.objects
                .filter(annotation=ann)
                .order_by('created_at', 'id')
                .values_list('id', flat=True)
            )
            keep_pk, delete_pks = pks[0], pks[1:]
            if delete_pks:
                deleted, _ = Article.objects.filter(pk__in=delete_pks).delete()
                total_deleted += deleted
                self.stdout.write(
                    f"annotation={repr(ann[:30])}…: удалено {deleted} дубликатов (id: {delete_pks})"
                )

        self.stdout.write(self.style.SUCCESS(
            f"Готово: всего удалено {total_deleted} записей."
        ))
