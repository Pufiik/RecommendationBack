from django.core.management.base import BaseCommand
from app.faiss_index import FaissIndex

class Command(BaseCommand):
    help = "Построить FAISS-индекс один раз после загрузки данных"

    def handle(self, *args, **options):
        self.stdout.write("Начинаем перестройку FAISS-индекса…")
        try:
            FaissIndex.build_index()
            self.stdout.write(self.style.SUCCESS("FAISS-индекс успешно построен."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка при построении индекса: {e}"))
            raise
