import spacy
import pytextrank

SUM_MODEL = "ru_core_news_md"
nlp = None


def init_summarizer():
    global nlp
    if nlp is None:
        nlp = spacy.load(SUM_MODEL)
        if "textrank" not in nlp.pipe_names:
            nlp.add_pipe("textrank", last=True)


def create_annotation(text: str, length: int = 7, limit_sent: int = 30) -> str:
    if nlp is None:
        init_summarizer()
    doc = nlp(text)
    raw_summary = doc._.textrank.summary(limit_sentences=limit_sent)
    summary_sentences = [str(sent) for sent in raw_summary if "?" not in str(sent)]
    return " ".join(summary_sentences[:length])
