import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel

EMBED_MODEL_NAME = "cointegrated/LaBSE-en-ru"
tokenizer = None
model = None


def init_embedding_model():
    global tokenizer, model
    if tokenizer is None or model is None:
        tokenizer = AutoTokenizer.from_pretrained(EMBED_MODEL_NAME)
        model = AutoModel.from_pretrained(EMBED_MODEL_NAME)
        if torch.cuda.is_available():
            model.cuda()
        model.eval()


def embed_bert_cls(text: str) -> np.ndarray:
    if tokenizer is None or model is None:
        init_embedding_model()
    inputs = tokenizer(text, padding=True, truncation=True, return_tensors='pt')
    inputs = {k: v.to(model.device) for k, v in inputs.items()}
    with torch.no_grad():
        output = model(**inputs)
    emb = output.last_hidden_state[:, 0, :]
    emb = torch.nn.functional.normalize(emb, dim=1, p=2)
    return emb[0].cpu().numpy()
