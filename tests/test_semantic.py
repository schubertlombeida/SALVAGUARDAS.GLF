import unittest
from src.semantic import passages, Hybrid


class WordTokenizer:
    def encode(self, text, **kwargs):
        return text.split() + ['start', 'end']


class FixedRetriever:
    records = [{'chunk_id': 'A'}, {'chunk_id': 'B'}]
    def __init__(self, order):
        self.order = order
    def search(self, query, limit=5):
        return [{'chunk_id': key} for key in self.order][:limit]


class SemanticTests(unittest.TestCase):
    def test_passages_preserve_all_words_and_fit(self):
        text = ' '.join('palabra'+str(i) for i in range(1200))
        pieces = passages(text, WordTokenizer())
        self.assertTrue(all(len(WordTokenizer().encode(p)) <= 512 for p in pieces))
        self.assertEqual(' '.join(p.removeprefix('passage: ') for p in pieces), text)

    def test_rrf_rewards_agreement_and_deduplicates(self):
        index = Hybrid(FixedRetriever(['A','B']), FixedRetriever(['B']))
        results = index.search('consulta')
        self.assertEqual([r['chunk_id'] for r in results], ['B','A'])
        self.assertAlmostEqual(results[0]['score'], 1/62+1/61, places=6)
