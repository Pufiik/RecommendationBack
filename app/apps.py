import sys
import threading
from django.apps import AppConfig


class RecsysConfig(AppConfig):
    name = 'app'

    def ready(self):
        non_server_cmds = {
            'migrate', 'makemigrations',
            'collectstatic', 'shell',
            'test', 'runserver', 'dbshell'
        }
        if len(sys.argv) >= 2 and sys.argv[1] not in non_server_cmds:
            return

        from .embeddings import init_embedding_model
        from .summarization import init_summarizer

        def _init_all():
            init_embedding_model()
            init_summarizer()

        thread = threading.Thread(target=_init_all, daemon=True)
        thread.start()
