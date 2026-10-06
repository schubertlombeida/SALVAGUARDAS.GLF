"""Mide latencia extremo a extremo del asistente local GLF.

Requiere que app.server y Ollama esten ejecutandose. Por defecto usa solo
train/validation del gold v2 y nunca consulta test.
"""
import argparse
import csv
import json
import math
import time
from pathlib import Path
from urllib.request import Request, urlopen


def percentile_nearest(values, p):
    values = sorted(values)
    return values[max(0, math.ceil(p * len(values)) - 1)]


def load_questions(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as handle:
        rows = list(csv.DictReader(handle))
    rows = [r for r in rows if r.get('split') in ('train', 'validation')]
    if not rows:
        raise ValueError('Gold sin preguntas train/validation.')
    return rows


def ask(base_url, query, timeout):
    payload = json.dumps({'query': query}, ensure_ascii=False).encode('utf-8')
    request = Request(
        base_url.rstrip('/') + '/api/ask',
        data=payload,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    started = time.perf_counter()
    with urlopen(request, timeout=timeout) as response:
        body = json.load(response)
    wall = time.perf_counter() - started
    if not body.get('generated'):
        raise RuntimeError('La API no genero respuesta con Ollama.')
    return body, wall


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gold', required=True, type=Path)
    parser.add_argument('--base-url', default='http://127.0.0.1:8765')
    parser.add_argument('--samples', type=int, default=40)
    parser.add_argument('--warmup', type=int, default=3)
    parser.add_argument('--timeout', type=float, default=30.0)
    parser.add_argument('--output', type=Path, default=Path('results/e2e_latency_v2.json'))
    args = parser.parse_args()
    if args.samples < 20 or args.warmup < 0:
        raise ValueError('Usa al menos 20 muestras y warmup no negativo.')

    questions = load_questions(args.gold)

    for i in range(args.warmup):
        ask(args.base_url, questions[i % len(questions)]['question'], args.timeout)

    rows = []
    for i in range(args.samples):
        q = questions[i % len(questions)]
        body, wall = ask(args.base_url, q['question'], args.timeout)
        timings = body.get('timings') or {}
        rows.append({
            'sample': i + 1,
            'question_id': q['question_id'],
            'split': q['split'],
            'retrieval_seconds': float(timings.get('retrieval_seconds', 0)),
            'generation_seconds': float(timings.get('generation_seconds', 0)),
            'api_total_seconds': float(timings.get('total_seconds', wall)),
            'wall_seconds': wall,
            'sources': len(body.get('sources') or []),
            'answer_chars': len(body.get('answer') or ''),
        })

    totals = [r['api_total_seconds'] for r in rows]
    walls = [r['wall_seconds'] for r in rows]
    p95 = percentile_nearest(totals, .95)
    payload = {
        'samples': len(rows),
        'warmup_excluded': args.warmup,
        'scope': 'POST /api/ask completo: recuperacion + Qwen local; navegador no incluido.',
        'test_used': False,
        'p50_total_seconds': percentile_nearest(totals, .50),
        'p95_total_seconds': p95,
        'p95_wall_seconds': percentile_nearest(walls, .95),
        'target_seconds': 7.0,
        'target_met': p95 <= 7.0,
        'rows': rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in payload.items() if k != 'rows'},
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
