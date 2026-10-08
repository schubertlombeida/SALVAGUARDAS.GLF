"""Prepara preguntas y pares propuestos por IA a partir de texto real del ZIP GLF.

Nunca equivale a un gold standard revisado por humanos. Cada ancla textual se valida.
"""
import argparse
import csv
import hashlib
import json
import random
import re
from collections import Counter,defaultdict
from pathlib import Path
from src.eda import load_records
from src.retrieval import BM25, tokens
from .question_specs import DOCS,SPECS

MEMBER='work/GLF_SGAS_Corpus_ES/04_corpus_rag/Corpus_GLF_SGAS_ES.jsonl'
# Documentos primarios disjuntos para el experimento de pares.
SPLIT_BY_ALIAS={**{x:'train' for x in ['M','E','B','F','G','C']},
                **{x:'validation' for x in ['A','D','J']},
                **{x:'test' for x in ['G1','G2','H','I']}}
# Segundo fragmento solo cuando su contenido también sustenta la pregunta.
ADDITIONAL={
    4:[('E',1)],5:[('E',5)],8:[('D',3)],13:[('E',4)],
    20:[('G',6)],21:[('A',4)],23:[('M',3)],26:[('G',5)],
    27:[('M',3)],28:[('G',5)],36:[('E',1)],37:[('M',6)],
    38:[('H',1)],39:[('I',2)],40:[('M',6)],41:[('E',4)],
    44:[('G',4)],46:[('A',4),('D',8)],50:[('G1',3)]}

def csv_write(path,fields,rows):
    with open(path,'w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def chunk_id(alias,num):return f'{DOCS[alias]}::{num:04d}'

def location(record,anchor):
    text=record['text'];pos=text.casefold().find(anchor.casefold())
    if pos<0:raise ValueError(f"Ancla ausente: {record['chunk_id']} | {anchor}")
    heading=list(re.finditer(r'(?m)^#{1,4}\s+(.+)$',text[:pos+len(anchor)]))
    section=heading[-1].group(1).strip() if heading else 'Sección no estructurada en el fragmento'
    pages=[int(x) for x in re.findall(r'<!--\s*page:\s*(\d+)\s*-->',text)]
    return pos,section,('p. '+','.join(map(str,sorted(set(pages)))) if pages else 'página no indicada en el fragmento')

def answer_span(record,anchor):
    text=record['text'];pos,_,_=location(record,anchor)
    after=text[pos:]
    # Usar texto literal de la fuente; conservar hasta 500 caracteres y no sintetizar respuesta.
    result=' '.join(after.split())[:500]
    if len(result)<70:raise ValueError(f"Referencia demasiado corta: {record['chunk_id']} | {anchor}")
    return result

def inventory(records):
    rows=[]
    for doc in sorted({r['document_id'] for r in records}):
        subset=[r for r in records if r['document_id']==doc]
        rows.append({'document_id':doc,'chunks':len(subset), 'language':','.join(sorted({r.get('language','') for r in subset})),
                     'source_type':','.join(sorted({r.get('source_type','') for r in subset})),
                     'normalized_file':subset[0].get('normalized_file',''),
                     'chunks_with_page_marker':sum(bool(re.search(r'<!--\s*page:',r['text'])) for r in subset),
                     'chunks_with_heading':sum(bool(re.search(r'(?m)^#{1,4}\s+',r['text'])) for r in subset),
                     'chunks_missing_core_metadata':sum(not all(r.get(k) for k in ('document_id','chunk_id','text','normalized_file')) for r in subset)})
    return rows

def prepare(archive,output):
    archive=Path(archive);output=Path(output);output.mkdir(parents=True,exist_ok=True)
    records=load_records(archive,MEMBER);byid={r['chunk_id']:r for r in records}
    if len(records)!=585 or len(byid)!=len(records):raise ValueError('Corpus normativo inesperado')
    if set(DOCS)!=set(SPLIT_BY_ALIAS):raise ValueError('Partición documental incompleta')
    inv=inventory(records);csv_write(output/'inventario_corpus.csv',list(inv[0]),inv)
    bm=BM25(records);gold=[];pairs=[];rng=random.Random(20261003)
    for number,(question,alias,num,anchor) in enumerate(SPECS,1):
        primary=chunk_id(alias,num);record=byid[primary];pos,section,page=location(record,anchor)
        if section=='Sección no estructurada en el fragmento' and num>1:
            previous=byid.get(chunk_id(alias,num-1))
            if previous:
                headings=re.findall(r'(?m)^#{1,4}\s+(.+)$',previous['text'])
                if headings:section='Continuación de '+headings[-1].strip()
        positive=[primary]+[chunk_id(a,n) for a,n in ADDITIONAL.get(number,[])]
        for other in positive:
            if other not in byid:raise ValueError(f'Segundo fragmento ausente: {other}')
        split=SPLIT_BY_ALIAS[alias];qid=f'GLF-{number:03d}'
        gold.append({'question_id':qid,'question':question,'relevant_chunk_ids':json.dumps(positive,ensure_ascii=False),
                     'source_document':record['document_id'],'source_section_or_page':section+'; '+page,
                     'answer_reference':answer_span(record,anchor),'human_reviewed':'false','review_status':'ai_proposed',
                     'annotation_source':'ai','split':split,
                     'notes':'Referencia literal del corpus; relevancia adicional propuesta por IA. Conjunto incompleto, revisión humana pendiente.'})
        # Pares de un mismo grupo documental; las fuentes primarias no cruzan particiones.
        pair_positive=[cid for cid in positive if any(byid[cid]['document_id']==DOCS[a] and SPLIT_BY_ALIAS[a]==split for a in DOCS)]
        for cid in pair_positive:
            r=byid[cid]
            pairs.append({'question_id':qid,'question':question,'chunk_id':cid,'document_id':r['document_id'],'text':r['text'],
                          'label':'1','negative_type':'','split':split,'human_reviewed':'false','review_status':'ai_proposed',
                          'notes':'Positivo propuesto por lectura del fragmento; confirmar con especialista.'})
        allowed_docs={DOCS[a] for a,s in SPLIT_BY_ALIAS.items() if s==split}
        ranked=bm.search(question,limit=len(records))
        # Selección de candidatos difíciles: misma consulta, alta puntuación léxica, otra fuente.
        ranked=[r for r in ranked if r['document_id'] in allowed_docs and r['document_id']!=record['document_id'] and r['chunk_id'] not in positive]
        hard=ranked[:3]
        hard_ids={r['chunk_id'] for r in hard}
        easy_pool=[r for r in records if r['document_id'] in allowed_docs and r['chunk_id'] not in positive and r['chunk_id'] not in hard_ids and r['document_id']!=record['document_id']]
        # Fácil: preferir bajo solapamiento; muestreo determinista entre la cola.
        qterms=set(tokens(question));easy_pool.sort(key=lambda r:(len(qterms&set(tokens(r['text']))),r['chunk_id']))
        pool=easy_pool[:max(30,len(easy_pool)//3)]
        easy=rng.sample(pool,k=min(5-len(hard),len(pool)))
        if len(hard)+len(easy)!=5:raise ValueError(f'No hay negativos suficientes: {qid}')
        for r,kind in [(r,'hard_candidate') for r in hard]+[(r,'easy_candidate') for r in easy]:
            pairs.append({'question_id':qid,'question':question,'chunk_id':r['chunk_id'],'document_id':r['document_id'],'text':r['text'],
                          'label':'0','negative_type':kind,'split':split,'human_reviewed':'false','review_status':'ai_proposed',
                          'notes':'Candidato negativo no verificado. Revisar si el fragmento también responde a la pregunta.'})
    assert len(SPECS)==len(gold)==50 and len(pairs)>=300
    assert len({(p['question_id'],p['chunk_id']) for p in pairs})==len(pairs)
    assigned=defaultdict(set)
    for p in pairs:assigned[p['document_id']].add(p['split'])
    assert all(len(v)==1 for v in assigned.values())
    assert all({p['label'] for p in pairs if p['question_id']==q['question_id']}=={'0','1'} for q in gold)
    csv_write(output/'dataset_gold.csv',list(gold[0]),gold)
    csv_write(output/'dataset_pairs.csv',list(pairs[0]),pairs)
    return {'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'corpus_member':MEMBER,'chunks':len(records),
            'documents':len(inv),'questions':len(gold),'pairs':len(pairs),'pairs_by_label':dict(Counter(p['label'] for p in pairs)),
            'pairs_by_split':dict(Counter(p['split'] for p in pairs)), 'documents_by_split':{s:sorted(doc for doc,v in assigned.items() if s in v) for s in ('train','validation','test')},
            'human_reviewed':False,'negative_types':dict(Counter(p['negative_type'] for p in pairs if p['label']=='0'))}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--archive',required=True);ap.add_argument('--output',default=Path('evaluacion_rag'))
    args=ap.parse_args();print(json.dumps(prepare(args.archive,args.output),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
