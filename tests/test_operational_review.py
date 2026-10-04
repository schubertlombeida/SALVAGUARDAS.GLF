"""Validate the published manifest against the local, versioned adjudications."""
import json
from pathlib import Path

from evaluacion_rag.integrate_operational_review import digest, read

ROOT = Path(__file__).resolve().parents[1] / 'evaluacion_rag'


def test_operational_counts_and_test_freeze():
    manifest = json.loads((ROOT / 'validacion_revision_operativa_v2.json').read_text(encoding='utf-8'))
    gold = read(ROOT / 'dataset_gold_operational_v2.csv')
    pairs = read(ROOT / 'dataset_pairs_operational_v2.csv')
    assert len(gold) == 50 and len(pairs) == 328
    assert sum(len(json.loads(r['relevant_chunk_ids'])) for r in gold) == 82
    assert sum(r['label'] == '1' for r in pairs) == 82
    assert sum(r['label_status'] == 'operational_negative_v2' for r in pairs) == 186
    test = [r for r in pairs if r['split'] == 'test' and r['label'] == '0']
    assert len(test) == 60
    assert all(r['label_status'] == 'negative_candidate_unverified' and r['human_reviewed'] == 'false' for r in test)
    assert all(r['eligible_for_training'] == 'false' for r in pairs if r['split'] != 'train')
    assert all(digest(ROOT / name) == sha for name, sha in manifest['v2_sha256'].items())


def test_source_provenance_and_cross_split_exclusions():
    rows = read(ROOT / 'dataset_pairs_operational_v2.csv')
    decided = [r for r in rows if r['label_status'] in ('operational_positive_v2', 'operational_negative_v2')]
    assert len(decided) == 192
    assert sum(r['validation_individual'] == 'CONFIRMACION_USUARIO' for r in decided) == 166
    assert sum(r['validation_individual'] == 'NO' for r in decided) == 26
    restricted = {('GLF-001', 'GLF_ANEXO_J_DEFINICIONES_ES::0001'),
                  ('GLF-038', 'GLF_ANEXO_H_FUNCIONES_RESPONSABILIDADES_SGAS_ES::0001'),
                  ('GLF-031', 'CREF-03_ES_20210614-ifc-ps-guidance-note-1-es::0052')}
    bykey = {(r['question_id'], r['chunk_id']): r for r in rows}
    assert all(bykey[key]['label'] == '1' and bykey[key]['eligible_for_training'] == 'false' for key in restricted)
