"""E5 opcional y fusión RRF; no sustituye validación de relevancia."""
import numpy as np


def passages(text, tokenizer, max_tokens=512):
    """Dividir por palabras hasta que cada pasaje quepa; evitar truncado silencioso."""
    words = text.split()
    if not words:
        raise ValueError('Pasaje vacío.')
    result = []
    def divide(part):
        value = 'passage: ' + ' '.join(part)
        if len(tokenizer.encode(value, add_special_tokens=True)) <= max_tokens:
            result.append(value)
        elif len(part) > 1:
            middle = len(part) // 2
            divide(part[:middle])
            divide(part[middle:])
        else:
            raise ValueError('Una palabra excede el límite del modelo; revisar extracción.')
    divide(words)
    return result


class E5:
    name = 'E5-small'
    def __init__(self, records, model=None):
        if not records:
            raise ValueError('Corpus vacío.')
        if model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise RuntimeError('Instalar las dependencias semánticas antes de usar E5.') from exc
            model = SentenceTransformer('intfloat/multilingual-e5-small', device='cpu', trust_remote_code=False)
        self.model, self.records = model, records
        self.model.max_seq_length = 512
        self.owners, texts = [], []
        for i, record in enumerate(records):
            windows = passages(record['text'], model.tokenizer)
            texts.extend(windows)
            self.owners.extend([i] * len(windows))
        self.vectors = np.asarray(model.encode(texts, normalize_embeddings=True,
                                               batch_size=16, show_progress_bar=False))

    def search(self, query, limit=5):
        value = 'query: ' + query.strip()
        if not query.strip():
            return []
        if len(self.model.tokenizer.encode(value, add_special_tokens=True)) > 512:
            raise ValueError('La consulta excede 512 tokens; acórtala.')
        vector = np.asarray(self.model.encode([value], normalize_embeddings=True, show_progress_bar=False))[0]
        scores = self.vectors @ vector
        best = {}
        for owner, score in zip(self.owners, scores):
            best[owner] = max(best.get(owner, float('-inf')), float(score))
        ranked = sorted(best, key=lambda i: (-best[i], i))[:limit]
        return [dict(self.records[i], score=round(best[i], 6)) for i in ranked]


class Hybrid:
    name = 'BM25+E5-RRF'
    def __init__(self, lexical, semantic, depth=20, constant=60):
        if depth < 5 or constant <= 0:
            raise ValueError('Parámetros RRF inválidos.')
        if [r['chunk_id'] for r in lexical.records] != [r['chunk_id'] for r in semantic.records]:
            raise ValueError('Los recuperadores deben compartir corpus y orden.')
        self.records = lexical.records
        self.lexical, self.semantic = lexical, semantic
        self.depth, self.constant = depth, constant

    def search(self, query, limit=5):
        scores, rows = {}, {}
        for retriever in (self.lexical, self.semantic):
            seen = set()
            for rank, row in enumerate(retriever.search(query, max(limit, self.depth)), 1):
                key = row['chunk_id']
                if key in seen:
                    continue
                seen.add(key)
                rows[key] = row
                scores[key] = scores.get(key, 0) + 1 / (self.constant + rank)
        return [dict(rows[key], score=round(scores[key], 6))
                for key in sorted(scores, key=lambda key: (-scores[key], key))[:limit]]
