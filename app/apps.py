import os
import sys
import threading
from django.apps import AppConfig
from .faiss_index import FaissIndex
from .constants import UMAP_DIM


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

        def _init_models():
            init_embedding_model()
            init_summarizer()

        threading.Thread(target=_init_models, daemon=True).start()

        index_path = FaissIndex.INDEX_PATH
        ids_path = FaissIndex.IDS_PATH

        if os.path.exists(index_path) and os.path.exists(ids_path):
            FaissIndex.load_index()
        else:
            from .models import Article
            import numpy as np

            vectors = []
            for a in Article.objects.all():
                if a.embedding and len(a.embedding) == UMAP_DIM:
                    vectors.append((a.id, np.array(a.embedding, dtype='float32')))

            FaissIndex.build_index(vectors)
