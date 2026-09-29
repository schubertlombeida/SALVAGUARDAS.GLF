"""Evaluación macro de recuperación sobre etiquetas revisadas."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from time import perf_counter
from .retrieval import load_spanish


def metrics(retrieved, relevant, k=5):
    if k < 1 or not relevant:
        raise ValueError('Se requiere k positivo y al menos un fragmento relevante.')
    ranked = list(dict.fromkeys(retrieved))[:k]
    gold = set(relevant)
    hits = len(set(ranked) & gold)
    return {'recall_at_5': hits / len(gold), 'precision_at_5': hits / k,
            'hit_rate_at_5': float(hits > 0)}


def evaluate(index, queries):
    if not queries:
        raise ValueError('No hay consultas para evaluar.')
    ids = set()
    known = {r['chunk_id'] for r in index.records}
    # Validar todas las etiquetas antes de ejecutar consultas.
    for q in queries:
        if not isinstance(q, dict) or not isinstance(q.get('query_id'), str) or not q['query_id'].strip():
            raise ValueError('Falta query_id.')
        if q['query_id'] in ids:
            raise ValueError('Identificador de consulta duplicado.')
        ids.add(q['query_id'])
        if q.get('review_status') != 'approved' or not str(q.get('reviewer', '')).strip():
            raise ValueError('Todas las consultas requieren revisión aprobada y responsable.')
        if not isinstance(q.get('query'), str) or not q['query'].strip():
            raise ValueError('Consulta vacía.')
        gold = q.get('relevant_chunk_ids')
        if not isinstance(gold, list) or not gold or any(not isinstance(x, str) for x in gold):
            raise ValueError('Se requieren identificadores relevantes revisados.')
        if len(set(gold)) != len(gold) or not set(gold) <= known:
            raise ValueError('Etiquetas duplicadas o fragmentos ajenos al corpus.')
        if q.get('split') not in ('development', 'validation', 'test'):
            raise ValueError('Partición no válida.')
    splits = {q['split'] for q in queries}
    if len(splits) != 1:
        raise ValueError('Evaluar una partición por ejecución.')
    rows = []
    for q in queries:
        started = perf_counter()
        retrieved = [r['chunk_id'] for r in index.search(q['query'], limit=5)]
        seconds = perf_counter() - started
        rows.append(dict(query_id=q['query_id'], retrieved_chunk_ids=retrieved,
                         seconds=seconds, **metrics(retrieved, q['relevant_chunk_ids'])))
    times = sorted(r['seconds'] for r in rows)
    return {'method': getattr(index, 'name', 'BM25'), 'unit': 'chunk', 'aggregation': 'macro',
            'split': next(iter(splits)), 'queries': len(rows),
            'metrics': {key: sum(r[key] for r in rows) / len(rows)
                        for key in ('recall_at_5', 'precision_at_5', 'hit_rate_at_5')},
            'retrieval_only_p95_seconds': times[math.ceil(.95 * len(times)) - 1],
            'latency_scope': 'Solo búsqueda local; excluye carga, red, interfaz y generación. No verifica la meta p95 del sistema.',
            'per_query': rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', required=True, type=Path)
    parser.add_argument('--labels', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--method', choices=['bm25', 'e5', 'hybrid'], default='bm25')
    args = parser.parse_args()
    queries = [json.loads(line) for line in args.labels.read_text(encoding='utf-8-sig').split('\n') if line.strip()]
    index = load_spanish(args.archive)
    if args.method != 'bm25':
        from .semantic import E5, Hybrid
        semantic = E5(index.records)
        index = semantic if args.method == 'e5' else Hybrid(index, semantic)
    report = evaluate(index, queries)
    report['archive_sha256'] = hashlib.sha256(args.archive.read_bytes()).hexdigest()
    report['labels_sha256'] = hashlib.sha256(args.labels.read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Evaluación guardada. La latencia corresponde solo al recuperador.')


if __name__ == '__main__':
    main()
