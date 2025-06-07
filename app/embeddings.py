import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel

tokenizer = None
model = None


def init_model():
    global tokenizer, model
    tokenizer = AutoTokenizer.from_pretrained("cointegrated/LaBSE-en-ru")
    model = AutoModel.from_pretrained("cointegrated/LaBSE-en-ru")
    if torch.cuda.is_available():
        model.cuda()
    model.eval()


def embed_bert_cls(text: str) -> np.ndarray:
    global tokenizer, model
    if tokenizer is None or model is None:
        init_model()
    inputs = tokenizer(text, padding=True, truncation=True, return_tensors='pt')
    inputs = {k: v.to(model.device) for k, v in inputs.items()}
    with torch.no_grad():
        output = model(**inputs)
    emb = output.last_hidden_state[:, 0, :]
    emb = torch.nn.functional.normalize(emb, dim=1, p=2)
    return emb[0].cpu().numpy()
