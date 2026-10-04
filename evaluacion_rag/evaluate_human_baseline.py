"""Repite baselines congelados con gold humano; nunca ajusta parámetros con test."""
import argparse
import csv
import hashlib
import json
import math
import platform
import time
from datetime import date
from pathlib import Path

from src.eda import load_records
from src.retrieval import BM25
from src.semantic import Hybrid
from .e5_index import E5Index,MODEL_ID,MODEL_REVISION
from .evaluate_retrieval import percentile_nearest
from .prepare_dataset import MEMBER,csv_write

METHODS=('BM25','E5-base','BM25+E5-RRF')
SPLITS=('train','validation','test')

def read(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))

def aggregate(rows,method,split):
    subset=[r for r in rows if r['method']==method and (split=='global' or r['split']==split)]
    times=[r['latency_seconds'] for r in subset]
    out={'method':method,'split':split,'questions':len(subset)}
    for metric in ('recall_at_1','recall_at_3','recall_at_5','hit_at_1','hit_at_3','hit_at_5','mrr_at_5'):
        out[metric]=sum(r[metric] for r in subset)/len(subset)
    out['latency_mean_seconds']=sum(times)/len(times)
    out['p50_seconds']=percentile_nearest(times,.5)
    out['p95_seconds']=percentile_nearest(times,.95)
    return out

def run(archive,folder):
    archive,folder=Path(archive),Path(folder)
    records=load_records(archive,MEMBER);byid={r['chunk_id']:r for r in records}
    gold=read(folder/'dataset_gold_human_reviewed_v1.csv')
    validation=json.loads((folder/'validacion_gold_humano.json').read_text(encoding='utf-8'))
    if validation['errores_detectados'] or len(gold)!=50 or len(records)!=585:
        raise ValueError('Gold humano no validado')
    if hashlib.sha256((folder/'dataset_gold_human_reviewed_v1.csv').read_bytes()).hexdigest()!=validation['gold_humano_sha256']:
        raise ValueError('Hash gold humano incorrecto')
    if any(q['human_reviewed']!='true' or not json.loads(q['relevant_chunk_ids']) for q in gold):
        raise ValueError('Revisión incompleta')
    bm=BM25(records)
    e5=E5Index(records,hashlib.sha256(archive.read_bytes()).hexdigest(),folder/'.cache')
    hybrid=Hybrid(bm,e5,depth=20,constant=60)
    methods=dict(zip(METHODS,(bm,e5,hybrid)))
    for model in methods.values():model.search('¿Qué establece el SGAS del GLF?',limit=5)
    detail=[]
    for name,model in methods.items():
        for q in gold:
            start=time.perf_counter()
            ranked=[r['chunk_id'] for r in model.search(q['question'],limit=5)]
            latency=time.perf_counter()-start
            relevant=set(json.loads(q['relevant_chunk_ids']))
            if len(ranked)!=len(set(ranked)) or not relevant<=set(byid):
                raise ValueError('Ranking o gold incorrecto')
            recalls=[len(set(ranked[:k])&relevant)/len(relevant) for k in (1,3,5)]
            hits=[int(bool(set(ranked[:k])&relevant)) for k in (1,3,5)]
            first=next((i for i,cid in enumerate(ranked,1) if cid in relevant),None)
            detail.append({'method':name,'question_id':q['question_id'],'split':q['split'],
                           'recall_at_1':recalls[0],'recall_at_3':recalls[1],'recall_at_5':recalls[2],
                           'hit_at_1':hits[0],'hit_at_3':hits[1],'hit_at_5':hits[2],
                           'mrr_at_5':0 if first is None else 1/first,
                           'latency_seconds':latency,'retrieved_chunk_ids':json.dumps(ranked,ensure_ascii=False),
                           'approved_relevant_ids':q['relevant_chunk_ids']})
    summary=[aggregate(detail,name,split) for split in ('global',)+SPLITS for name in METHODS]
    csv_write(folder/'resultados_recuperacion_human_v1.csv',list(summary[0]),summary)
    csv_write(folder/'resultados_por_pregunta_human_v1.csv',list(detail[0]),detail)
    payload={'evaluation_date':date.today().isoformat(),
             'corpus_archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
             'documents':len({r['document_id'] for r in records}),'chunks':len(records),
             'gold_file':'dataset_gold_human_reviewed_v1.csv','gold_sha256':validation['gold_humano_sha256'],
             'model_id':MODEL_ID,'model_revision':MODEL_REVISION,
             'bm25':'src.retrieval.BM25 sin cambios; k1=1.5, b=0.75 (fórmula fija)',
             'rrf':{'depth':20,'constant':60},'top_k':5,'e5_windows':len(e5.vectors),
             'e5_cache_hit':e5.cache_hit,'test_used_for_selection':False,
             'metric_definition':'Recall@k=fracción de todos los relevantes aprobados; Hit@k=al menos un relevante; MRR@5=primer relevante.',
             'latency_scope':'Búsqueda local precargada; no es latencia extremo a extremo.',
             'limitations':['Fecha/nombre de revisor sin confirmar si campos vacíos','Negativos no revisados','Gold basado en decisiones suministradas por el usuario','Test informativo y congelado'],
             'versions':{'python':platform.python_version()},'summary':summary}
    (folder/'metricas_recuperacion_human_v1.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    return payload

def compare(folder):
    folder=Path(folder)
    before=read(folder/'resultados_recuperacion.csv')
    after=read(folder/'resultados_recuperacion_human_v1.csv')
    rows=[]
    for name in METHODS:
        old=next(x for x in before if x['method']==name)
        new=next(x for x in after if x['method']==name and x['split']=='global')
        old_detail=[x for x in read(folder/'resultados_por_pregunta.csv') if x['method']==name]
        for metric in ('recall_at_1','recall_at_3','recall_at_5','hit_at_1','hit_at_3','hit_at_5','mrr_at_5'):
            earlier=(sum(float(x['recall_at_'+metric[-1]])>0 for x in old_detail)/50
                     if metric.startswith('hit') else float(old[metric]))
            later=float(new[metric])
            rows.append({'metodo':name,'metrica':metric,'antes_revision':earlier,
                         'despues_revision':later,'diferencia':later-earlier})
    csv_write(folder/'comparacion_ia_vs_humano.csv',list(rows[0]),rows)
    return rows

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--folder',default='evaluacion_rag')
    a=p.parse_args();result=run(a.archive,a.folder);compare(a.folder)
    print(json.dumps(result['summary'],ensure_ascii=False,indent=2))
