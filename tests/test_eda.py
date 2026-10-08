"""Pruebas con datos ficticios mínimos, independientes del corpus privado."""
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from src.eda import summarize


class EdaTests(unittest.TestCase):
    def archive(self, directory, broken=False, leaked=False, empty=False):
        path = Path(directory) / 'fixture.zip'
        base = dict(document_id='d1', project_code='p1', split='desarrollo', text='uno dos', language='es', source_group='grupo', document_role='propuesta')
        chunk = dict(base, document_id='missing' if broken else 'd1', split='prueba' if leaked else 'desarrollo', text='' if empty else 'uno dos')
        with zipfile.ZipFile(path, 'w') as z:
            for name, rows in [('corpus_documentos.jsonl', [base]), ('corpus_chunks_rag.jsonl', [chunk]), ('expedientes_pareados.jsonl', [base])]:
                z.writestr(name, '\n'.join(json.dumps(r) for r in rows))
        return path

    def test_counts(self):
        with tempfile.TemporaryDirectory() as d:
            result = summarize(self.archive(d))
            self.assertEqual((result['documents'], result['projects'], result['document_words']), (1, 1, 2))

    def test_broken_reference(self):
        with tempfile.TemporaryDirectory() as d, self.assertRaises(ValueError):
            summarize(self.archive(d, broken=True))

    def test_split_leak(self):
        with tempfile.TemporaryDirectory() as d, self.assertRaises(ValueError):
            summarize(self.archive(d, leaked=True))

    def test_empty_chunk(self):
        with tempfile.TemporaryDirectory() as d, self.assertRaises(ValueError):
            summarize(self.archive(d, empty=True))
