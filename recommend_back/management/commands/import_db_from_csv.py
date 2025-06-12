# your_app/management/commands/import_articles.py

import csv
import ast

import numpy as np
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from app.models import Article


class Command(BaseCommand):
    help = "Импортирует статьи из CSV в модель Article"

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_path',
            type=str,
            help='Путь до CSV-файла (абсолютный или относительно manage.py)'
        )

    def handle(self, *args, **options):
        path = options['csv_path']
        created_count = updated_count = 0

        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:

                dt = row.get('created_at')
                if dt:
                    naive = parse_datetime(dt)
                    if naive is None:
                        created_at = None
                    else:
                        created_at = timezone.make_aware(naive, timezone.get_default_timezone())
                else:
                    created_at = None

                emb_str = row.get('embedding', '').strip()
                if emb_str.startswith('[') and emb_str.endswith(']'):
                    body = emb_str[1:-1]
                    try:
                        embedding = np.fromstring(body, sep=' ')
                        embedding = embedding.tolist()
                    except Exception as e:
                        self.stderr.write(f"Ошибка парсинга embedding для «{row['title']}»: {e}")
                        embedding = []

                obj, created = Article.objects.update_or_create(
                    title=row['title'],
                    defaults={
                        'annotation': row.get('annotation', ''),
                        'content': row.get('content', ''),
                        'language': row.get('language', Article.RU),
                        'embedding': embedding,
                        **({'created_at': created_at} if created_at else {})
                    }
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Импорт завершён: создано {created_count}, обновлено {updated_count} статей."
        ))

        print(created_count)
        print(updated_count)
