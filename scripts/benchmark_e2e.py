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
from urllib.error import HTTPError, URLError
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
    try:
        with urlopen(request, timeout=timeout) as response:
            body = json.load(response)
        wall = time.perf_counter() - started
        return body, wall, None
    except HTTPError as error:
        wall = time.perf_counter() - started
        try:
            body = json.load(error)
            message = body.get('error') or str(error)
        except Exception:
            message = str(error)
        return None, wall, f'HTTP {error.code}: {message}'
    except (URLError, TimeoutError, OSError) as error:
        wall = time.perf_counter() - started
        return None, wall, f'{type(error).__name__}: {error}'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gold', required=True, type=Path)
    parser.add_argument('--base-url', default='http://127.0.0.1:8765')
    parser.add_argument('--samples', type=int, default=40)
    parser.add_argument('--warmup', type=int, default=3)
    parser.add_argument('--timeout', type=float, default=60.0)
    parser.add_argument('--output', type=Path, default=Path('results/e2e_latency_v2.json'))
    args = parser.parse_args()
    if args.samples < 20 or args.warmup < 0:
        raise ValueError('Usa al menos 20 muestras y warmup no negativo.')

    questions = load_questions(args.gold)

    print(f'Calentamiento: {args.warmup} consultas', flush=True)
    for i in range(args.warmup):
        q = questions[i % len(questions)]
        _, wall, error = ask(args.base_url, q['question'], args.timeout)
        status = 'OK' if error is None else 'ERROR'
        print(f'  warmup {i+1}/{args.warmup}: {wall:.2f}s [{status}]', flush=True)

    rows = []
    print(f'Medicion: {args.samples} consultas', flush=True)
    for i in range(args.samples):
        q = questions[i % len(questions)]
        body, wall, error = ask(args.base_url, q['question'], args.timeout)
        timings = (body or {}).get('timings') or {}
        generated = bool((body or {}).get('generated'))
        answer_text = (body or {}).get('answer') or ''
        insufficient = 'documentación recuperada es insuficiente' in answer_text.casefold()
        row = {
            'sample': i + 1,
            'question_id': q['question_id'],
            'split': q['split'],
            'success': error is None and generated,
            'error': error or (None if generated else 'API no genero respuesta'),
            'retrieval_seconds': float(timings.get('retrieval_seconds', 0)),
            'generation_seconds': float(timings.get('generation_seconds', 0)),
            'api_total_seconds': float(timings.get('total_seconds', wall)),
            'wall_seconds': wall,
            'sources': len((body or {}).get('sources') or []),
            'answer_chars': len(answer_text),
            'insufficient_answer': insufficient,
        }
        rows.append(row)
        status = 'OK' if row['success'] else 'ERROR'
        print(f"  {i+1:02d}/{args.samples}: {q['question_id']} - {row['api_total_seconds']:.2f}s [{status}]", flush=True)

    successful = [r for r in rows if r['success']]
    failures = len(rows) - len(successful)
    insufficient_answers = sum(1 for r in successful if r['insufficient_answer'])

    if successful:
        totals = [r['api_total_seconds'] for r in successful]
        walls = [r['wall_seconds'] for r in successful]
        p50 = percentile_nearest(totals, .50)
        p95 = percentile_nearest(totals, .95)
        p95_wall = percentile_nearest(walls, .95)
    else:
        p50 = p95 = p95_wall = None

    payload = {
        'samples': len(rows),
        'successful_samples': len(successful),
        'failed_samples': failures,
        'insufficient_answers': insufficient_answers,
        'success_rate': len(successful) / len(rows),
        'warmup_excluded': args.warmup,
        'request_timeout_seconds': args.timeout,
        'scope': 'POST /api/ask completo: recuperacion + Qwen local; navegador no incluido.',
        'test_used': False,
        'p50_total_seconds_successful': p50,
        'p95_total_seconds_successful': p95,
        'p95_wall_seconds_successful': p95_wall,
        'target_seconds': 7.0,
        'latency_target_met': bool(p95 is not None and p95 <= 7.0),
        'fully_valid_run': failures == 0,
        'target_met': bool(p95 is not None and p95 <= 7.0 and failures == 0),
        'rows': rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')

    print('')
    print(json.dumps({k: v for k, v in payload.items() if k != 'rows'},
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
