"""Servidor de desarrollo local; no destinado a exposición pública."""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from time import perf_counter
from urllib.parse import urlsplit
from src.retrieval import load_spanish

PAGE = Path(__file__).with_name('index.html')


def handler_for(index):
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
                self.reply(200, {'chunks': len(index.records), 'method': 'BM25', 'evaluated': False})
            else:
                self.reply(404, {'error': 'Ruta no encontrada.'})

        def do_POST(self):
            if self.path != '/api/search':
                return self.reply(404, {'error': 'Ruta no encontrada.'})
            origin = self.headers.get('Origin')
            if origin and origin != 'http://' + self.headers.get('Host', ''):
                return self.reply(403, {'error': 'Origen no permitido.'})
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 < size <= 8192:
                    raise ValueError('Consulta demasiado grande o vacía.')
                payload = json.loads(self.rfile.read(size))
                query = payload.get('query') if isinstance(payload, dict) else None
                if not isinstance(query, str) or not 3 <= len(query.strip()) <= 1000:
                    raise ValueError('Escribe una consulta de 3 a 1000 caracteres.')
            except (ValueError, UnicodeDecodeError) as error:
                return self.reply(400, {'error': str(error)})
            started = perf_counter()
            rows = index.search(query)
            self.reply(200, {'results': rows, 'seconds': round(perf_counter() - started, 4)})
    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', required=True, type=Path)
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    index = load_spanish(args.archive)
    server = ThreadingHTTPServer(('127.0.0.1', args.port), handler_for(index))
    print(f'GLF: http://127.0.0.1:{args.port} — {len(index.records)} fragmentos', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
