"""Recalifica positivos; conserva negativos antiguos solo como candidatos pendientes."""
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from src.eda import load_records
from .prepare_dataset import MEMBER,csv_write,SPLIT_BY_ALIAS
from .question_specs import DOCS

def read(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))

def build(archive,folder):
    folder=Path(folder);records=load_records(archive,MEMBER)
    byid={r['chunk_id']:r for r in records}
    gold=read(folder/'dataset_gold_human_reviewed_v1.csv')
    old=read(folder/'dataset_pairs.csv')
    old_by_q=defaultdict(list)
    for p in old:old_by_q[p['question_id']].append(p)
    home={DOCS[alias]:split for alias,split in SPLIT_BY_ALIAS.items()}
    rows=[];converted=0;cross_split=[]
    for q in gold:
        qid=q['question_id'];approved=json.loads(q['relevant_chunk_ids'])
        previous={(p['chunk_id']):p for p in old_by_q[qid]}
        for chunk in approved:
            r=byid[chunk];doc_split=home.get(r['document_id'])
            usable=doc_split==q['split']
            if not usable:cross_split.append({'question_id':qid,'chunk_id':chunk,'question_split':q['split'],
                                                'document_split':doc_split or 'sin_asignacion'})
            if chunk in previous and previous[chunk]['label']=='0':converted+=1
            rows.append({'question_id':qid,'question':q['question'],'chunk_id':chunk,
                         'document_id':r['document_id'],'text':r['text'],'label':'1',
                         'negative_type':'','split':q['split'],'label_status':'human_approved_positive',
                         'human_reviewed':'true','eligible_for_training':str(usable).lower(),
                         'notes':'Positivo aprobado; fuera de entrenamiento si su documento pertenece a otro split o no está asignado.'})
        for p in old_by_q[qid]:
            chunk=p['chunk_id']
            if chunk in approved:continue
            if p['label']=='1':
                # Una etiqueta eliminada no significa que el equipo la haya aprobado como negativo.
                kind='removed_positive_needs_negative_review'
            else:
                kind=p['negative_type']
            r=byid[chunk]
            rows.append({'question_id':qid,'question':q['question'],'chunk_id':chunk,
                         'document_id':r['document_id'],'text':r['text'],'label':'0',
                         'negative_type':kind,'split':q['split'],'label_status':'negative_candidate_unverified',
                         'human_reviewed':'false','eligible_for_training':'false',
                         'notes':'No se aportó decisión humana explícita de no relevancia; no usar para entrenamiento.'})
    if len({(r['question_id'],r['chunk_id']) for r in rows})!=len(rows):
        raise ValueError('Par duplicado')
    csv_write(folder/'dataset_pairs_human_reviewed.csv',list(rows[0]),rows)
    return {'rows':len(rows),'positives':sum(r['label']=='1' for r in rows),
            'negative_candidates':sum(r['label']=='0' for r in rows),
            'old_negatives_promoted_to_positive':converted,
            'positive_cross_split_evaluation_only':cross_split,
            'label_statuses':dict(Counter(r['label_status'] for r in rows))}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--folder',default='evaluacion_rag')
    a=p.parse_args();print(json.dumps(build(a.archive,a.folder),ensure_ascii=False,indent=2))
