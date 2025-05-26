from django.apps import AppConfig


class RecsysConfig(AppConfig):
    name = 'app'

    def ready(self):
        import app.signals
