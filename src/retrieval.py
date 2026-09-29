"""Recuperador lexical BM25. No genera respuestas ni estima confianza."""
import math
import re
import unicodedata
from collections import Counter
from .eda import load_records

STOP = set('a al de del el la las los un una unos unas y o en por para con que se es sobre como cuales'.split())


def tokens(text):
    value = ''.join(c for c in unicodedata.normalize('NFKD', text.lower()) if not unicodedata.combining(c))
    return [t for t in re.findall(r'[a-z0-9]+', value) if t not in STOP and len(t) > 1]


class BM25:
    def __init__(self, records):
        self.records = records
        if not records or any(not r.get('text', '').strip() for r in records):
            raise ValueError('Corpus vacío o con fragmentos sin texto.')
        self.counts = [Counter(tokens(r['text'])) for r in records]
        self.lengths = [sum(c.values()) for c in self.counts]
        self.average = sum(self.lengths) / len(records)
        if not self.average:
            raise ValueError('Corpus sin términos indexables.')
        df = Counter(t for c in self.counts for t in c)
        self.idf = {t: math.log(1 + (len(records) - n + .5) / (n + .5)) for t, n in df.items()}

    def search(self, query, limit=5):
        terms = set(tokens(query))
        scores = []
        for i, counts in enumerate(self.counts):
            score = sum(self.idf.get(t, 0) * counts[t] * 2.5 /
                        (counts[t] + 1.5 * (.25 + .75 * self.lengths[i] / self.average))
                        for t in terms)
            if score > 0:
                scores.append((score, i))
        return [dict(self.records[i], score=round(s, 5)) for s, i in sorted(scores, key=lambda x: (-x[0], x[1]))[:limit]]


def load_spanish(archive):
    member = 'work/GLF_SGAS_Corpus_ES/04_corpus_rag/Corpus_GLF_SGAS_ES.jsonl'
    records = load_records(archive, member)
    if any(r.get('language') != 'es' for r in records):
        raise ValueError('El corpus seleccionado debe estar en español.')
    return BM25(records)
