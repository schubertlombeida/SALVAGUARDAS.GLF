import json
import os
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

from app.ollama import OllamaUnavailable, generate_answer, relevant_passages
from app.server import handler_for, select_chat_results
from src.retrieval import BM25, load_spanish

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

    def test_category_a_evidence_is_sent_with_original_citation(self):
        question = '¿Son elegibles para financiamiento del GLF los proyectos de Categoría A?'
        row = {'chunk_id': 'GLF_MANUAL_SGAS_ES::0005', 'document_id': 'GLF_MANUAL_SGAS_ES',
               'text': 'La categoría determina el alcance de evaluación. Los proyectos A son inelegibles. ' +
                       'Otros instrumentos dependen del riesgo. ' * 160}
        captured = {}
        class FakeResponse:
            def __enter__(self): return self
            def __exit__(self, *_): pass
            def read(self, *_):
                return json.dumps({'message': {'content': 'No. [GLF_MANUAL_SGAS_ES::0005]'}}).encode()
        def fake_urlopen(request, timeout):
            captured['payload'] = json.loads(request.data)
            return FakeResponse()
        with patch('app.ollama.urlopen', side_effect=fake_urlopen):
            answer, sources = generate_answer(question, [row])
        prompt = captured['payload']['messages'][0]['content']
        self.assertIn('Los proyectos A son inelegibles.', prompt)
        self.assertIn('CHUNK_ID: GLF_MANUAL_SGAS_ES::0005', prompt)
        self.assertIn('Empieza por la primera fuente si responde', prompt)
        self.assertEqual(sources[0]['chunk_id'], row['chunk_id'])
        self.assertTrue(answer.startswith('No.'))

    def test_relevant_sentence_after_old_cutoff_and_no_duplicates(self):
        text = ('Texto introductorio sin relación. ' * 130) + 'Los proyectos A son inelegibles. ' * 2
        self.assertGreater(text.index('Los proyectos A son inelegibles.'), 3500)
        passages = relevant_passages('¿Son elegibles los proyectos de categoría A?', text)
        self.assertEqual(passages.count('Los proyectos A son inelegibles.'), 1)
        self.assertLessEqual(len(passages), 1050)
        seen = set()
        self.assertIn('inelegibles', relevant_passages('proyectos A elegibles', text, seen=seen))
        self.assertNotIn('inelegibles', relevant_passages('proyectos A elegibles', text, seen=seen))

    def test_insufficient_evidence_remains_allowed(self):
        class FakeResponse:
            def __enter__(self): return self
            def __exit__(self, *_): pass
            def read(self, *_):
                return json.dumps({'message': {'content': 'La documentación recuperada es insuficiente para responder esta pregunta.'}}).encode()
        with patch('app.ollama.urlopen', return_value=FakeResponse()):
            answer, sources = generate_answer('¿Qué dice sobre un tema ausente?', [ROW])
        self.assertIn('insuficiente', answer)
        self.assertEqual(sources, [])

    def test_insufficient_answer_discards_irrelevant_citation(self):
        class FakeResponse:
            def __enter__(self): return self
            def __exit__(self, *_): pass
            def read(self, *_):
                return json.dumps({'message': {'content': 'La documentación recuperada es insuficiente. [DOC::0001]'}}).encode()
        with patch('app.ollama.urlopen', return_value=FakeResponse()):
            answer, sources = generate_answer('¿Tema sin evidencia?', [ROW])
        self.assertEqual(sources, [])
        self.assertNotIn('[DOC::0001]', answer)

    def test_cited_output_omits_uncited_claims_and_acronym_expansion(self):
        class FakeResponse:
            def __enter__(self): return self
            def __exit__(self, *_): pass
            def read(self, *_):
                content = 'Plan de Gestión Inventado (PGAS) [DOC::0001]\nConclusión sin cita.'
                return json.dumps({'message': {'content': content}}).encode()
        with patch('app.ollama.urlopen', return_value=FakeResponse()):
            answer, _ = generate_answer('¿Qué indica?', [ROW])
        self.assertIn('PGAS [DOC::0001]', answer)
        self.assertNotIn('Inventado', answer)
        self.assertNotIn('Conclusión', answer)

    def test_three_real_corpus_regressions_when_available(self):
        archive = Path(os.getenv('GLF_CORPUS_ZIP',
            r'C:\Users\NIKO\Desktop\Estudios 2025\Maestria Inteligencia Artificial\Proyecto Integrador\GLF_SGAS_Corpus_ES.zip'))
        if not archive.exists():
            self.skipTest('ZIP autorizado no disponible en este equipo')
        index = load_spanish(archive)
        self.assertEqual(len(index.records), 585)
        questions = [
            '¿Qué instrumentos ambientales y sociales son obligatorios para todos los proyectos?',
            '¿Qué debe hacer el GLF durante la evaluación de la detección?',
            '¿Qué diferencia existe entre los proyectos de Categoría B y Categoría C?',
        ]
        selected = [select_chat_results(index, question) for question in questions]
        self.assertTrue(all(len(rows) == 5 for rows in selected))
        self.assertTrue(all(any(r['chunk_id'] == 'GLF_MANUAL_SGAS_ES::0005' for r in rows) for rows in selected))
        manual = next(r for r in selected[0] if r['chunk_id'] == 'GLF_MANUAL_SGAS_ES::0005')
        passage = relevant_passages(questions[0], manual['text'])
        self.assertIn('Todo proyecto necesita un PGAS, PPPI y mecanismo de reclamaciones', passage)
        self.assertIn('- PPPI.', passage)
        step = relevant_passages(questions[1], manual['text'])
        self.assertIn('Paso 3: evaluación de la detección', step)
        self.assertNotIn('Paso 5: evaluación e informe', step)
        comparison = relevant_passages(questions[2], manual['text'])
        self.assertIn('Los B requieren evaluación ajustada', comparison)
        self.assertIn('Los C normalmente no requieren evaluación completa', comparison)


if __name__ == '__main__':
    unittest.main()
