"""Auditoría reproducible del gold humano, pares y métricas del baseline."""
import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from src.eda import load_records
from .build_human_gold import ORIGINAL_SHA256, choices
from .evaluate_human_baseline import METHODS,SPLITS,aggregate,read
from .prepare_dataset import MEMBER

def verify(archive,folder):
    archive,folder=Path(archive),Path(folder)
    errors=[]
    source=folder/'dataset_gold.csv';target=folder/'dataset_gold_human_reviewed_v1.csv'
    old=read(source);new=read(target);pairs=read(folder/'dataset_pairs_human_reviewed.csv')
    detail=read(folder/'resultados_por_pregunta_human_v1.csv')
    before_detail=read(folder/'resultados_por_pregunta.csv')
    summaries=read(folder/'resultados_recuperacion_human_v1.csv')
    validation=json.loads((folder/'validacion_gold_humano.json').read_text(encoding='utf-8'))
    meta=json.loads((folder/'metricas_recuperacion_human_v1.json').read_text(encoding='utf-8'))
    records=load_records(archive,MEMBER);known={r['chunk_id'] for r in records}
    assert hashlib.sha256(source.read_bytes()).hexdigest()==ORIGINAL_SHA256
    assert hashlib.sha256(target.read_bytes()).hexdigest()==validation['gold_humano_sha256']==meta['gold_sha256']
    assert meta['corpus_archive_sha256']==hashlib.sha256(archive.read_bytes()).hexdigest()
    assert len(records)==585 and len(old)==len(new)==50
    assert [r['question_id'] for r in new]==[f'GLF-{i:03d}' for i in range(1,51)]
    assert [r['split'] for r in old]==[r['split'] for r in new]
    assert all(r['human_reviewed']=='true' for r in new)
    assert all(r['human_reviewed']=='false' for r in old)
    assert all(x['question']==y['question'] for x,y in zip(new,old) if x['question_id']!='GLF-005')
    changes=choices();adds=removes=0
    for i,(old_row,new_row) in enumerate(zip(old,new),1):
        before=json.loads(old_row['relevant_chunk_ids']);after=json.loads(new_row['relevant_chunk_ids'])
        decision=changes.get(i,{})
        expected=[x for x in before if x not in decision.get('remove',[])]+decision.get('add',[])
        assert after==expected and after and len(after)==len(set(after)) and set(after)<=known
        assert new_row['question']==decision.get('question',old_row['question'])
        assert len(json.loads(new_row['evidencias_por_chunk']))==len(after)
        adds+=len(decision.get('add',[]));removes+=len(decision.get('remove',[]))
    assert adds==19 and removes==13 and sum(len(json.loads(r['relevant_chunk_ids'])) for r in new)==76
    assert len(pairs)==328
    by_q=defaultdict(list)
    for p in pairs:by_q[p['question_id']].append(p)
    assert len({(p['question_id'],p['chunk_id']) for p in pairs})==len(pairs)
    assert sum(p['label']=='1' for p in pairs)==76
    for q in new:
        relevant=set(json.loads(q['relevant_chunk_ids']))
        own=by_q[q['question_id']]
        assert {p['chunk_id'] for p in own if p['label']=='1'}==relevant
        assert not {p['chunk_id'] for p in own if p['label']=='0'}&relevant
    assert all(p['human_reviewed']=='true' and p['label_status']=='human_approved_positive'
               for p in pairs if p['label']=='1')
    assert all(p['human_reviewed']=='false' and p['eligible_for_training']=='false'
               and p['label_status']=='negative_candidate_unverified' for p in pairs if p['label']=='0')
    assert len(detail)==150 and len(summaries)==12 and not meta['test_used_for_selection']
    old_rank={(r['method'],r['question_id']):r['retrieved_chunk_ids'] for r in before_detail}
    for d in detail:
        ranking=json.loads(d['retrieved_chunk_ids'])
        relevant=set(json.loads(d['approved_relevant_ids']))
        assert len(ranking)==len(set(ranking))==5
        for k in (1,3,5):
            hit=int(bool(set(ranking[:k])&relevant))
            recall=len(set(ranking[:k])&relevant)/len(relevant)
            assert int(d[f'hit_at_{k}'])==hit
            assert math.isclose(float(d[f'recall_at_{k}']),recall,abs_tol=1e-12)
        if d['question_id']!='GLF-005':
            assert d['retrieved_chunk_ids']==old_rank[(d['method'],d['question_id'])],(d['method'],d['question_id'])
    numeric=[{k:(float(v) if k in ('recall_at_1','recall_at_3','recall_at_5','hit_at_1','hit_at_3','hit_at_5','mrr_at_5','latency_seconds') else v)
              for k,v in row.items()} for row in detail]
    for summary in summaries:
        expected=aggregate(numeric,summary['method'],summary['split'])
        assert int(summary['questions'])==expected['questions']
        for key in expected:
            if key in ('method','split','questions'):continue
            assert math.isclose(float(summary[key]),expected[key],abs_tol=1e-10),(summary['method'],summary['split'],key)
    assert validation['test_question_ids_unchanged'] and validation['errores_detectados']==[]
    print('VERIFICADO: gold 50/50, 76 relaciones, 19 altas, 13 bajas; 328 pares con negativos no verificados; 12 resúmenes y test sin selección.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--folder',default='evaluacion_rag')
    a=p.parse_args();verify(a.archive,a.folder)
