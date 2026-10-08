"""Servidor de desarrollo local; no destinado a exposicion publica."""
import argparse
import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from time import perf_counter
from urllib.parse import urlsplit

from src.retrieval_optimized import load_optimized
from .ollama import OllamaUnavailable, generate_answer

PAGE = Path(__file__).with_name('index.html')


def select_chat_results(index, query, limit=5):
    """Seleccion final para chat sin alterar el benchmark del recuperador.

    El recuperador optimizado ya incorpora cuerpo, encabezados y autoridad GLF.
    Solo las consultas que comparan varias categorias reciben un desempate
    generico por cobertura de las categorias solicitadas.
    """
    candidates = index.search(query, limit=max(limit, 30))
    categories = set(re.findall(r'categor[ií]a\s+([a-z])\b', query.casefold()))
    if len(categories) < 2:
        return candidates[:limit]

    def category_rank(row):
        text = row['text'].casefold()
        hits = sum(
            bool(re.search(r'categor[ií]a\s+' + re.escape(letter) + r'\b', text))
            or bool(re.search(r'\b(?:proyectos?|los|las)\s+' + re.escape(letter) + r'\b', text))
            for letter in categories
        )
        return hits, row.get('score', 0)

    return sorted(candidates, key=category_rank, reverse=True)[:limit]


def handler_for(index, generator=generate_answer):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # No registrar consultas del especialista.

        def reply(self, code, body, mime='application/json; charset=utf-8'):
            data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode('utf-8')
            self.send_response(code)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if urlsplit(self.path).path == '/':
                self.reply(200, PAGE.read_bytes(), 'text/html; charset=utf-8')
            elif self.path == '/api/status':
                self.reply(200, {
                    'chunks': len(index.records),
                    'method': getattr(index, 'name', 'desconocido'),
                    'evaluated': True,
                    'development_recall_at_5': 0.8355263158,
                    'validation_recall_at_5': 0.9090909091,
                    'test_used_for_selection': False,
                })
            else:
                self.reply(404, {'error': 'Ruta no encontrada.'})

        def do_POST(self):
            if self.path not in ('/api/search', '/api/ask'):
                return self.reply(404, {'error': 'Ruta no encontrada.'})
            origin = self.headers.get('Origin')
            if origin and origin != 'http://' + self.headers.get('Host', ''):
                return self.reply(403, {'error': 'Origen no permitido.'})
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 < size <= 8192:
                    raise ValueError('Consulta demasiado grande o vacia.')
                payload = json.loads(self.rfile.read(size))
                query = payload.get('query') if isinstance(payload, dict) else None
                if not isinstance(query, str) or not 3 <= len(query.strip()) <= 1000:
                    raise ValueError('Escribe una consulta de 3 a 1000 caracteres.')
            except (ValueError, UnicodeDecodeError) as error:
                return self.reply(400, {'error': str(error)})

            started = perf_counter()
            rows = select_chat_results(index, query)
            retrieval_seconds = round(perf_counter() - started, 4)
            if self.path == '/api/search':
                return self.reply(200, {'results': rows, 'seconds': retrieval_seconds})

            if not rows:
                return self.reply(200, {
                    'answer': 'La documentacion recuperada es insuficiente para responder esta pregunta.',
                    'sources': [], 'results': [], 'generated': False,
                    'timings': {
                        'retrieval_seconds': retrieval_seconds,
                        'generation_seconds': 0,
                        'total_seconds': round(perf_counter() - started, 4),
                    },
                })

            generation_started = perf_counter()
            try:
                answer, sources = generator(query, rows)
            except OllamaUnavailable as error:
                return self.reply(503, {
                    'error': str(error), 'results': rows, 'generated': False,
                    'timings': {
                        'retrieval_seconds': retrieval_seconds,
                        'generation_seconds': round(perf_counter() - generation_started, 4),
                        'total_seconds': round(perf_counter() - started, 4),
                    },
                })

            return self.reply(200, {
                'answer': answer,
                'sources': sources,
                'results': rows,
                'generated': True,
                'timings': {
                    'retrieval_seconds': retrieval_seconds,
                    'generation_seconds': round(perf_counter() - generation_started, 4),
                    'total_seconds': round(perf_counter() - started, 4),
                },
            })
    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', required=True, type=Path)
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    index = load_optimized(args.archive)
    server = ThreadingHTTPServer(('127.0.0.1', args.port), handler_for(index))
    print(
        f'GLF: http://127.0.0.1:{args.port} — {len(index.records)} fragmentos — {index.name}',
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
