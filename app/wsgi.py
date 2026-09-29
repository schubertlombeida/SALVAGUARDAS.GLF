"""Aplicación WSGI para demostración; corpus indicado por configuración."""
import json
import os
from pathlib import Path
from time import perf_counter
from src.retrieval import load_spanish


def create_app(index=None):
    page = Path(__file__).with_name('index.html').read_bytes()
    def application(env, start_response):
        def reply(code, payload, mime='application/json; charset=utf-8'):
            body = payload if isinstance(payload, bytes) else json.dumps(payload, ensure_ascii=False).encode('utf-8')
            start_response(code, [('Content-Type', mime), ('Content-Length', str(len(body))),
                                  ('Cache-Control', 'no-store'), ('X-Content-Type-Options', 'nosniff')])
            return [body]
        path, method = env.get('PATH_INFO', '/'), env.get('REQUEST_METHOD', 'GET')
        if method == 'GET' and path == '/':
            return reply('200 OK', page, 'text/html; charset=utf-8')
        if method == 'GET' and path in ('/api/status', '/healthz'):
            if index is None:
                return reply('503 Service Unavailable', {'error': 'Corpus no configurado.', 'ready': False})
            return reply('200 OK', {'ready': True, 'chunks': len(index.records), 'method': 'BM25', 'evaluated': False})
        if path != '/api/search':
            return reply('404 Not Found', {'error': 'Ruta no encontrada.'})
        if method != 'POST':
            return reply('405 Method Not Allowed', {'error': 'Usa POST.'})
        if index is None:
            return reply('503 Service Unavailable', {'error': 'Corpus no configurado.'})
        if env.get('CONTENT_TYPE', '').split(';')[0].strip().lower() != 'application/json':
            return reply('415 Unsupported Media Type', {'error': 'Se requiere JSON.'})
        try:
            size = int(env.get('CONTENT_LENGTH') or 0)
            if not 0 < size <= 8192:
                return reply('413 Payload Too Large', {'error': 'Tamaño de consulta no permitido.'})
            payload = json.loads(env['wsgi.input'].read(size))
            query = payload.get('query') if isinstance(payload, dict) else None
            if not isinstance(query, str) or not 3 <= len(query.strip()) <= 1000:
                raise ValueError()
        except (ValueError, UnicodeDecodeError):
            return reply('400 Bad Request', {'error': 'Escribe una consulta válida de 3 a 1000 caracteres.'})
        try:
            started = perf_counter()
            results = index.search(query.strip())
            return reply('200 OK', {'results': results, 'seconds': round(perf_counter() - started, 4)})
        except Exception:
            return reply('500 Internal Server Error', {'error': 'No se pudo completar la búsqueda.'})
    return application


def main():
    from waitress import serve
    archive = os.environ.get('GLF_CORPUS_ZIP')
    index = load_spanish(archive) if archive else None
    serve(create_app(index), host=os.environ.get('GLF_HOST', '127.0.0.1'),
          port=int(os.environ.get('PORT', '7860')), threads=4,
          max_request_body_size=8192, channel_timeout=30, connection_limit=100)


if __name__ == '__main__':
    main()
