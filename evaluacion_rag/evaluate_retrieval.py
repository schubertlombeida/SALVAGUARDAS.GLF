"""Compara BM25, E5-base y RRF sobre el mismo corpus y las mismas preguntas."""
import argparse
import csv
import hashlib
import json
import math
import os
import platform
import time
from pathlib import Path
from collections import Counter
from src.retrieval import BM25
from src.semantic import Hybrid
from src.eda import load_records
from .e5_index import E5Index,MODEL_ID
from .prepare_dataset import MEMBER,csv_write

def load_gold(path,known):
    rows=list(csv.DictReader(Path(path).open(encoding='utf-8-sig',newline='')))
    ids=set()
    for x in rows:
        gold=json.loads(x['relevant_chunk_ids'])
        if not x['question_id'] or x['question_id'] in ids or not x['question'].strip():raise ValueError('Pregunta duplicada o vacía')
        ids.add(x['question_id'])
        if not gold or len(gold)!=len(set(gold)) or not set(gold)<=known:raise ValueError('Referencias inválidas')
        if x['human_reviewed'].lower()!='false' or x['review_status']!='ai_proposed':raise ValueError('Estado de revisión no esperado')
        x['gold']=gold
    if len(rows)!=50:raise ValueError('Se esperaban 50 preguntas')
    return rows

def marks(ranked,gold):
    known=set(gold);r=[]
    for k in (1,3,5):r.append(len(set(ranked[:k])&known)/len(known))
    first=next((i for i,cid in enumerate(ranked[:5],1) if cid in known),None)
    return r[0],r[1],r[2],0.0 if first is None else 1/first

def percentile_nearest(values,p):
    values=sorted(values)
    return values[max(0,math.ceil(p*len(values))-1)]

def run(archive,folder,cache_dir=None):
    archive=Path(archive);folder=Path(folder)
    records=load_records(archive,MEMBER);known={r['chunk_id'] for r in records}
    if len(records)!=585 or len(known)!=585:raise ValueError('Corpus inesperado')
    questions=load_gold(folder/'dataset_gold.csv',known)
    archive_sha=hashlib.sha256(archive.read_bytes()).hexdigest()
    bm=BM25(records);e5=E5Index(records,archive_sha,cache_dir or folder/'.cache')
    hybrid=Hybrid(bm,e5,depth=20,constant=60)
    methods={'BM25':bm,'E5-base':e5,'BM25+E5-RRF':hybrid}
    # Calentamiento excluido de medición: carga, tokenizador y cálculos iniciales.
    for method in methods.values():method.search('¿Qué establece el SGAS del GLF?',limit=5)
    detail=[];summary=[]
    for name,index in methods.items():
        for q in questions:
            start=time.perf_counter()
            ranked=[r['chunk_id'] for r in index.search(q['question'],limit=5)]
            seconds=time.perf_counter()-start
            if len(ranked)!=len(set(ranked)):raise ValueError('Recuperación duplicada')
            r1,r3,r5,mrr=marks(ranked,q['gold'])
            detail.append({'method':name,'question_id':q['question_id'],'split':q['split'],'recall_at_1':r1,
                           'recall_at_3':r3,'recall_at_5':r5,'mrr_at_5':mrr,'latency_seconds':seconds,
                           'retrieved_chunk_ids':json.dumps(ranked,ensure_ascii=False),'known_relevant_ids':json.dumps(q['gold'],ensure_ascii=False)})
        own=[r for r in detail if r['method']==name]
        times=[r['latency_seconds'] for r in own]
        summary.append({'method':name,'questions':len(own),'recall_at_1':sum(r['recall_at_1'] for r in own)/len(own),
                        'recall_at_3':sum(r['recall_at_3'] for r in own)/len(own),
                        'recall_at_5':sum(r['recall_at_5'] for r in own)/len(own),
                        'mrr_at_5':sum(r['mrr_at_5'] for r in own)/len(own),
                        'p50_seconds':percentile_nearest(times,.5),'p95_seconds':percentile_nearest(times,.95),
                        'retrieval_recall_target_met_provisionally':sum(r['recall_at_5'] for r in own)/len(own)>=.8,
                        'retrieval_p95_target_met_provisionally':percentile_nearest(times,.95)<=7})
    csv_write(folder/'resultados_recuperacion.csv',list(summary[0]),summary)
    csv_write(folder/'resultados_por_pregunta.csv',list(detail[0]),detail)
    import sentence_transformers,torch,numpy
    payload={'corpus_archive_sha256':archive_sha,'gold_sha256':hashlib.sha256((folder/'dataset_gold.csv').read_bytes()).hexdigest(),
             'model_id':MODEL_ID,'model_revision':e5.revision,'e5_windows':len(e5.vectors),'e5_cache_hit':e5.cache_hit,
             'rrf':{'depth':20,'constant':60},'questions':50,'known_relevance_only':True,'human_reviewed':False,
             'metric_definition':'Macro Recall@k sobre IDs conocidos por pregunta; MRR@5 primer acierto entre 5.',
             'latency_scope':'Búsqueda local con índice precargado; E5 incluye codificación de consulta y producto vectorial. Híbrido incluye ambas búsquedas y RRF. Excluye descarga, carga de índice, red, interfaz y generación.',
             'versions':{'python':platform.python_version(),'sentence_transformers':sentence_transformers.__version__,'torch':torch.__version__,'numpy':numpy.__version__},
             'summary':summary,
             'by_split':{s:{name:{'questions':len(z),'recall_at_5':sum(x['recall_at_5'] for x in z)/len(z),
                                    'mrr_at_5':sum(x['mrr_at_5'] for x in z)/len(z)}
                            for name in methods for z in [[x for x in detail if x['split']==s and x['method']==name]]}
                         for s in ('train','validation','test')}}
    (folder/'metricas_recuperacion.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    return payload

def main():
    p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--folder',default='evaluacion_rag')
    a=p.parse_args();d=run(a.archive,a.folder);print(json.dumps(d['summary'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
