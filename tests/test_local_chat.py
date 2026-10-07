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
from src.retrieval import BM25
from src.retrieval_optimized import OptimizedGLFRetriever, load_optimized

ROW = {
    'chunk_id': 'DOC::0001',
    'document_id': 'DOC',
    'text': 'El plan incluye participación de la comunidad.',
    'language': 'es',
}


class FakeResponse:
    def __init__(self, content):
        self.content = content

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def read(self, *_):
        return json.dumps({'message': {'content': self.content}}).encode()


class LocalChatTests(unittest.TestCase):
    def request(self, generator, query='participación comunidad'):
        server = ThreadingHTTPServer(
            ('127.0.0.1', 0),
            handler_for(BM25([ROW]), generator),
        )
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        payload = json.dumps({'query': query}).encode()
        req = Request(
            f'http://127.0.0.1:{server.server_port}/api/ask',
            payload,
            {'Content-Type': 'application/json'},
            method='POST',
        )
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
        status, body = self.request(
            lambda question, rows: (
                'Participación [DOC::0001]',
                [{'document_id': 'DOC', 'chunk_id': 'DOC::0001'}],
            )
        )
        self.assertEqual(status, 200)
        self.assertTrue(body['generated'])
        self.assertEqual(body['sources'][0]['chunk_id'], 'DOC::0001')
        self.assertEqual(len(body['results']), 1)
        self.assertEqual(
            set(body['timings']),
            {'retrieval_seconds', 'generation_seconds', 'total_seconds'},
        )

    def test_unavailable_keeps_results_and_rejects_long_input(self):
        def missing(*_):
            raise OllamaUnavailable('Ollama local no respondió.')

        status, body = self.request(missing)
        self.assertEqual(status, 503)
        self.assertFalse(body['generated'])
        self.assertEqual(body['results'][0]['chunk_id'], 'DOC::0001')

        status, _ = self.request(missing, 'a' * 1001)
        self.assertEqual(status, 400)

    def test_bad_chunk_citation_gets_grounded_retry(self):
        responses = iter([
            FakeResponse('Respuesta [OTHER::0002]'),
            FakeResponse('Respuesta corregida [DOC::0001]'),
        ])

        with patch('app.ollama.urlopen', side_effect=lambda *args, **kwargs: next(responses)):
            answer, sources = generate_answer('¿Participación?', [ROW])

        self.assertIn('[DOC::0001]', answer)
        self.assertEqual(sources[0]['chunk_id'], 'DOC::0001')

    def test_source_footnote_is_not_treated_as_chunk_citation(self):
        response = FakeResponse('Respuesta basada en la fuente [^8] [DOC::0001]')
        with patch('app.ollama.urlopen', return_value=response):
            answer, sources = generate_answer('¿Participación?', [ROW])

        self.assertNotIn('[^8]', answer)
        self.assertIn('[DOC::0001]', answer)
        self.assertEqual(sources[0]['chunk_id'], 'DOC::0001')

    def test_second_invalid_format_degrades_safely(self):
        responses = iter([
            FakeResponse('Respuesta sin cita'),
            FakeResponse('Otra respuesta sin cita'),
        ])
        with patch('app.ollama.urlopen', side_effect=lambda *args, **kwargs: next(responses)):
            answer, sources = generate_answer('¿Participación?', [ROW])

        self.assertIn('insuficiente', answer)
        self.assertEqual(sources, [])

    def test_category_a_evidence_is_sent_with_original_citation(self):
        question = '¿Son elegibles para financiamiento del GLF los proyectos de Categoría A?'
        row = {
            'chunk_id': 'GLF_MANUAL_SGAS_ES::0005',
            'document_id': 'GLF_MANUAL_SGAS_ES',
            'text': (
                'La categoría determina el alcance de evaluación. '
                'Los proyectos A son inelegibles. '
                + 'Otros instrumentos dependen del riesgo. ' * 160
            ),
        }
        captured = {}

        def fake_urlopen(request, timeout):
            captured['payload'] = json.loads(request.data)
            return FakeResponse('No. [GLF_MANUAL_SGAS_ES::0005]')

        with patch('app.ollama.urlopen', side_effect=fake_urlopen):
            answer, sources = generate_answer(question, [row])

        prompt = captured['payload']['messages'][0]['content']
        self.assertIn('Los proyectos A son inelegibles.', prompt)
        self.assertIn('CHUNK_ID: GLF_MANUAL_SGAS_ES::0005', prompt)
        self.assertEqual(sources[0]['chunk_id'], row['chunk_id'])
        self.assertTrue(answer.startswith('No.'))

    def test_relevant_sentence_after_old_cutoff_and_no_duplicates(self):
        text = (
            'Texto introductorio sin relación. ' * 130
            + 'Los proyectos A son inelegibles. ' * 2
        )
        self.assertGreater(text.index('Los proyectos A son inelegibles.'), 3500)
        passages = relevant_passages(
            '¿Son elegibles los proyectos de categoría A?',
            text,
        )
        self.assertEqual(
            passages.count('Los proyectos A son inelegibles.'),
            1,
        )
        self.assertLessEqual(len(passages), 1050)

    def test_insufficient_evidence_remains_allowed(self):
        response = FakeResponse(
            'La documentación recuperada es insuficiente para responder esta pregunta.'
        )
        with patch('app.ollama.urlopen', return_value=response):
            answer, sources = generate_answer('¿Qué dice sobre un tema ausente?', [ROW])

        self.assertIn('insuficiente', answer)
        self.assertEqual(sources, [])

    def test_cited_output_omits_uncited_claims_and_acronym_expansion(self):
        response = FakeResponse(
            'Plan de Gestión Inventado (PGAS) [DOC::0001]\n'
            'Conclusión sin cita.'
        )
        with patch('app.ollama.urlopen', return_value=response):
            answer, _ = generate_answer('¿Qué indica?', [ROW])

        self.assertIn('PGAS [DOC::0001]', answer)
        self.assertNotIn('Inventado', answer)
        self.assertNotIn('Conclusión', answer)

    def test_optimized_retriever_prefers_heading_and_glf_authority(self):
        rows = [
            {
                'chunk_id': 'REF::0001',
                'document_id': 'CREF_X',
                'text': 'Texto general sobre riesgos ambientales.',
                'language': 'es',
            },
            {
                'chunk_id': 'GLF::0001',
                'document_id': 'GLF_MANUAL',
                'text': '# Riesgos ambientales\nTexto general sobre riesgos.',
                'language': 'es',
            },
        ]
        index = OptimizedGLFRetriever(rows)
        ranked = index.search('riesgos ambientales', limit=2)
        self.assertEqual(ranked[0]['chunk_id'], 'GLF::0001')

    def test_real_corpus_regressions_when_available(self):
        archive = Path(
            os.getenv(
                'GLF_CORPUS_ZIP',
                r'C:\Users\NIKO\Desktop\Estudios 2025\Maestria Inteligencia Artificial\Proyecto Integrador\GLF_SGAS_Corpus_ES.zip',
            )
        )
        if not archive.exists():
            self.skipTest('ZIP autorizado no disponible en este equipo')

        index = load_optimized(archive)
        self.assertEqual(len(index.records), 585)

        questions = [
            '¿Qué instrumentos ambientales y sociales son obligatorios para todos los proyectos?',
            '¿Qué debe hacer el GLF durante la evaluación de la detección?',
            '¿Qué diferencia existe entre los proyectos de Categoría B y Categoría C?',
            '¿Qué instrumentos de salvaguarda puede pedir la herramienta ESSA?',
        ]
        selected = [select_chat_results(index, q) for q in questions]

        self.assertTrue(all(len(rows) == 5 for rows in selected))
        self.assertTrue(
            any(
                r['chunk_id'] == 'GLF_MANUAL_SGAS_ES::0005'
                for r in selected[0]
            )
        )
        self.assertTrue(
            any(
                r['chunk_id'] == 'GLF_MANUAL_SGAS_ES::0005'
                for r in selected[3]
            )
        )


if __name__ == '__main__':
    unittest.main()
