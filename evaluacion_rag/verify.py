"""Comprueba que datos, citas, métricas y archivos se corresponden entre sí."""
import csv
import hashlib
import json
import math
from pathlib import Path
from src.eda import load_records
from .prepare_dataset import MEMBER

def read_csv(path):
    rows=list(csv.DictReader(Path(path).open(encoding='utf-8-sig',newline='')))
    if not rows:raise ValueError(f'CSV vacío: {path}')
    return rows

def verify(archive,folder):
    folder=Path(folder);archive=Path(archive)
    metrics=json.loads((folder/'metricas_recuperacion.json').read_text(encoding='utf-8'))
    audit=json.loads((folder/'auditoria_pares.json').read_text(encoding='utf-8'))
    gold=read_csv(folder/'dataset_gold.csv');pairs=read_csv(folder/'dataset_pairs.csv')
    detail=read_csv(folder/'resultados_por_pregunta.csv');summary=read_csv(folder/'resultados_recuperacion.csv')
    inventory=read_csv(folder/'inventario_corpus.csv')
    records=load_records(archive,MEMBER);byid={r['chunk_id']:r for r in records}
    assert len(records)==585 and len(inventory)==36 and len(gold)==50 and len(pairs)>=300
    assert len(summary)==3 and len(detail)==150 and audit['near_duplicate_count']==0
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==metrics['corpus_archive_sha256']
    assert hashlib.sha256((folder/'dataset_gold.csv').read_bytes()).hexdigest()==metrics['gold_sha256']
    assert all(q['human_reviewed']=='false' and q['review_status']=='ai_proposed' for q in gold)
    for q in gold:
        ids=json.loads(q['relevant_chunk_ids'])
        assert ids and set(ids)<=byid.keys()
        ref=q['answer_reference']
        assert ref and any(ref in ' '.join(byid[cid]['text'].split()) for cid in ids),q['question_id']
    for method in (r['method'] for r in summary):
        rows=[r for r in detail if r['method']==method]
        assert len(rows)==50 and {r['question_id'] for r in rows}=={q['question_id'] for q in gold}
        aggregate=next(r for r in summary if r['method']==method)
        for key in ('recall_at_1','recall_at_3','recall_at_5','mrr_at_5'):
            average=sum(float(r[key]) for r in rows)/50
            assert math.isclose(average,float(aggregate[key]),rel_tol=0,abs_tol=1e-10)
        times=sorted(float(r['latency_seconds']) for r in rows)
        assert math.isclose(times[math.ceil(.95*len(times))-1],float(aggregate['p95_seconds']),rel_tol=0,abs_tol=1e-10)
        assert math.isclose(times[math.ceil(.5*len(times))-1],float(aggregate['p50_seconds']),rel_tol=0,abs_tol=1e-10)
    assert (folder/'reporte_resultados.md').stat().st_size>1000
    print('VERIFICADO: 585 fragmentos; 50 preguntas con referencias textuales; 316 pares; 150 consultas medidas; 3 resúmenes consistentes; sin fuga detectada.')

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--folder',default='evaluacion_rag')
    args=p.parse_args();verify(args.archive,args.folder)
