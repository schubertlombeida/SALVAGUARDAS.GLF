import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

from app.ollama import OllamaUnavailable, generate_answer
from app.server import handler_for
from src.retrieval import BM25

ROW = {'chunk_id': 'DOC::0001', 'document_id': 'DOC', 'text': 'El plan incluye participación de la comunidad.', 'language': 'es'}


class LocalChatTests(unittest.TestCase):
    def request(self, generator, query='participación comunidad'):
        server = ThreadingHTTPServer(('127.0.0.1', 0), handler_for(BM25([ROW]), generator))
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        payload = json.dumps({'query': query}).encode()
        req = Request(f'http://127.0.0.1:{server.server_port}/api/ask', payload,
                      {'Content-Type': 'application/json'}, method='POST')
        try:
            with urlopen(req, timeout=3) as response:
                return response.status, json.load(response)
        except HTTPError as error:
            return error.code, json.load(error)
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=3)

    def test_ask_returns_generated_answer_sources_and_timings(self):
        status, body = self.request(lambda question, rows: ('Participación [DOC::0001]',
                                                             [{'document_id': 'DOC', 'chunk_id': 'DOC::0001'}]))
        self.assertEqual(status, 200)
        self.assertTrue(body['generated'])
        self.assertEqual(body['sources'][0]['chunk_id'], 'DOC::0001')
        self.assertEqual(len(body['results']), 1)
        self.assertEqual(set(body['timings']), {'retrieval_seconds', 'generation_seconds', 'total_seconds'})

    def test_unavailable_keeps_bm25_results_and_rejects_long_input(self):
        def missing(*_):
            raise OllamaUnavailable('Ollama local no respondió.')
        status, body = self.request(missing)
        self.assertEqual(status, 503)
        self.assertFalse(body['generated'])
        self.assertEqual(body['results'][0]['chunk_id'], 'DOC::0001')
        status, _ = self.request(missing, 'a' * 1001)
        self.assertEqual(status, 400)

    def test_ollama_rejects_unverified_citation(self):
        class FakeResponse:
            def __enter__(self): return self
            def __exit__(self, *_): pass
            def read(self, *_): return b'{"message":{"content":"Respuesta [OTHER::0002]"}}'
        with patch('app.ollama.urlopen', return_value=FakeResponse()):
            with self.assertRaises(OllamaUnavailable):
                generate_answer('¿Participación?', [ROW])


if __name__ == '__main__':
    unittest.main()
