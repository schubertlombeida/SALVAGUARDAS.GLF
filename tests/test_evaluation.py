import unittest
from src.evaluation import evaluate, metrics
from src.retrieval import BM25


class EvaluationTests(unittest.TestCase):
    def test_recall_is_not_hit_rate(self):
        result = metrics(['A', 'A', 'X'], ['A', 'B'])
        self.assertEqual(result['recall_at_5'], .5)
        self.assertEqual(result['precision_at_5'], .2)
        self.assertEqual(result['hit_rate_at_5'], 1)

    def test_review_and_corpus_validation(self):
        index = BM25([{'chunk_id': 'A', 'text': 'biodiversidad marina'}])
        q = dict(query_id='Q1', query='marina', relevant_chunk_ids=['A'],
                 review_status='draft', reviewer='Especialista', split='development')
        with self.assertRaises(ValueError):
            evaluate(index, [q])
        q['review_status'] = 'approved'
        self.assertEqual(evaluate(index, [q])['metrics']['recall_at_5'], 1)
        with self.assertRaises(ValueError):
            evaluate(index, [q, dict(q, query_id='Q2', split='test')])
        q['relevant_chunk_ids'] = ['inexistente']
        with self.assertRaises(ValueError):
            evaluate(index, [q])
