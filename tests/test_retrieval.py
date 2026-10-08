import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from http.server import ThreadingHTTPServer
from app.server import handler_for
from src.retrieval import BM25


class RetrievalTests(unittest.TestCase):
    def setUp(self):
        self.index = BM25([{'text': 'Conservación de biodiversidad marina', 'chunk_id': 'A'},
                           {'text': 'Salud y seguridad laboral', 'chunk_id': 'B'}])

    def test_accent_ranking_and_no_match(self):
        self.assertEqual(self.index.search('conservacion')[0]['chunk_id'], 'A')
        self.assertEqual(self.index.search('astronautas'), [])
        self.assertEqual(self.index.search('de la y'), [])

    def test_invalid_corpus(self):
        for rows in ([], [{'text': ''}], [{'text': 'de la'}]):
            with self.assertRaises(ValueError):
                BM25(rows)

    def test_http_validation_and_search(self):
        server = ThreadingHTTPServer(('127.0.0.1', 0), handler_for(self.index))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f'http://127.0.0.1:{server.server_port}'
        try:
            with urlopen(base + '/api/status') as r:
                self.assertEqual(json.load(r)['chunks'], 2)
            for payload in ({'query': ''}, {'query': 12}, [], {'query': 'a' * 1001}):
                req = Request(base + '/api/search', data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
                with self.assertRaises(HTTPError) as error:
                    urlopen(req)
                self.assertEqual(error.exception.code, 400)
            req = Request(base + '/api/search', data=b'{"query":"seguridad"}', headers={'Content-Type': 'application/json'})
            with urlopen(req) as r:
                self.assertEqual(json.load(r)['results'][0]['chunk_id'], 'B')
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
