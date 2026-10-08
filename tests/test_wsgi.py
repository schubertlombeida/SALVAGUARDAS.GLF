import io
import json
import unittest
from app.wsgi import create_app
from src.retrieval import BM25


class WebDeploymentTests(unittest.TestCase):
    def request(self, app, path='/api/search', body=b'{"query":"marina"}', method='POST', mime='application/json'):
        observed = {}
        def start(status, headers):
            observed['status'] = status
        env = {'PATH_INFO': path, 'REQUEST_METHOD': method, 'CONTENT_TYPE': mime,
               'CONTENT_LENGTH': str(len(body)), 'wsgi.input': io.BytesIO(body)}
        output = b''.join(app(env, start))
        return observed['status'], output

    def test_missing_corpus_is_not_reported_ready(self):
        status, body = self.request(create_app(), '/healthz', method='GET')
        self.assertTrue(status.startswith('503'))
        self.assertFalse(json.loads(body)['ready'])

    def test_search_and_invalid_requests(self):
        app = create_app(BM25([{'text': 'biodiversidad marina', 'chunk_id': 'A'}]))
        status, body = self.request(app)
        self.assertTrue(status.startswith('200'))
        self.assertEqual(json.loads(body)['results'][0]['chunk_id'], 'A')
        for body, mime, expected in [(b'[]','application/json','400'),
                                     (b'x'*8193,'application/json','413'),
                                     (b'{}','text/plain','415'),
                                     (b'{','application/json','400')]:
            self.assertTrue(self.request(app, body=body, mime=mime)[0].startswith(expected))
        self.assertTrue(self.request(app, method='GET')[0].startswith('405'))
