import threading

from django.apps import AppConfig


class RecsysConfig(AppConfig):
    name = 'app'

    def ready(self):
        import app.signals
        from .embeddings import init_model
        thread = threading.Thread(target=init_model, daemon=True)
        thread.start()
