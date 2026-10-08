"""Recuperador GLF optimizado y reproducible para el asistente local.

Combina BM25 del cuerpo, BM25 de encabezados y una prioridad pequena para
fuentes GLF frente a referencias externas. Los parametros se seleccionaron
sin usar test y no contiene reglas por pregunta ni IDs de chunks.
"""
import math
import re
import unicodedata
from collections import Counter

import numpy as np

from .eda import load_records

MEMBER = 'work/GLF_SGAS_Corpus_ES/04_corpus_rag/Corpus_GLF_SGAS_ES.jsonl'
STOP = set('a al de del el la las los un una unos unas y o en por para con que se es sobre como cuales'.split())


def tokens(text):
    value = ''.join(c for c in unicodedata.normalize('NFKD', text.lower())
                    if not unicodedata.combining(c))
    return [t for t in re.findall(r'[a-z0-9]+', value) if t not in STOP and len(t) > 1]


class BM25Field:
    def __init__(self, texts, k1=1.5, b=.75):
        self.k1, self.b = k1, b
        self.counts = [Counter(tokens(text)) for text in texts]
        self.lengths = np.asarray([sum(c.values()) for c in self.counts], dtype=float)
        if not len(self.lengths) or np.any(self.lengths <= 0):
            raise ValueError('Corpus vacio o con campos sin terminos indexables.')
        self.average = float(self.lengths.mean())
        df = Counter(term for counts in self.counts for term in counts)
        n = len(texts)
        self.idf = {term: math.log(1 + (n - freq + .5) / (freq + .5))
                    for term, freq in df.items()}

    def scores(self, query):
        terms = set(tokens(query))
        out = np.zeros(len(self.counts), dtype=float)
        for i, counts in enumerate(self.counts):
            length = self.lengths[i]
            for term in terms:
                tf = counts.get(term, 0)
                if tf:
                    out[i] += self.idf.get(term, 0) * tf * (self.k1 + 1) / (
                        tf + self.k1 * (1 - self.b + self.b * length / self.average)
                    )
        return out


def normalize(values):
    top = float(values.max()) if len(values) else 0.0
    return values / top if top > 0 else values


class OptimizedGLFRetriever:
    name = 'BM25-heading-authority-v2'

    def __init__(self, records):
        if not records or any(not r.get('text', '').strip() for r in records):
            raise ValueError('Corpus vacio o con fragmentos sin texto.')
        self.records = records
        body = [r['text'] for r in records]
        headings = []
        for record in records:
            markdown = re.findall(r'(?m)^#{1,6}\s+(.+)$', record['text'])
            bold = re.findall(r'(?m)^\s*\*\*(.+?)\*\*\s*$', record['text'])
            headings.append(' '.join(markdown + bold) or 'vacio')
        self.body = BM25Field(body, k1=.8, b=.2)
        self.headings = BM25Field(headings, k1=1.2, b=.3)
        self.glf = np.asarray([
            1.0 if r.get('document_id', '').startswith('GLF_') else 0.0
            for r in records
        ])

    def search(self, query, limit=5):
        if not query.strip() or limit < 1:
            return []
        score = (
            normalize(self.body.scores(query))
            + 0.30 * normalize(self.headings.scores(query))
            + 0.15 * self.glf
        )
        ranked = np.argsort(-score, kind='stable')[:limit]
        return [dict(self.records[i], score=round(float(score[i]), 6))
                for i in ranked if score[i] > 0]


def load_optimized(archive):
    records = load_records(archive, MEMBER)
    if len(records) != 585 or len({r['chunk_id'] for r in records}) != 585:
        raise ValueError('Corpus GLF inesperado.')
    if any(r.get('language') != 'es' for r in records):
        raise ValueError('El corpus seleccionado debe estar en espanol.')
    return OptimizedGLFRetriever(records)
