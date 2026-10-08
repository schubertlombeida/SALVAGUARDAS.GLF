"""Organiza negativos candidatos sin aprobar etiquetas ni ajustar el recuperador."""
import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path

from src.retrieval import tokens
from .prepare_dataset import csv_write

FIELDS = [
    'question_id','pregunta','split_original','chunk_id_candidato','documento',
    'seccion_pagina','texto_fragmento','motivo_negativo_original',
    'posicion_original_BM25','posicion_original_E5_base','posicion_original_hibrido',
    'evidencia_textual_para_revision','posible_relevante_por','prioridad_revision',
    'estado_revision','decision_humana','observaciones','nombre_revisor','fecha_revision',
    'nota_posiciones']

def read(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as stream:
        return list(csv.DictReader(stream))

def snippet(text, question, width=950):
    clean=' '.join(text.split())
    terms=[t for t in tokens(question) if len(t)>=4]
    positions=[m.start() for t in terms[:12] for m in [re.search(r'\b'+re.escape(t)+r'\b',clean,re.I)] if m]
    start=max(0,min(positions)-180) if positions else 0
    return clean[start:start+width]

def ranks(review_row, column):
    return {r['chunk_id']:r['posicion'] for r in json.loads(review_row[column])}

def locate_from_review(review_row, cid, text):
    for c in json.loads(review_row['candidatos_consolidados']):
        if c['chunk_id']==cid:return c['seccion_pagina']
    headings=re.findall(r'(?m)^#{1,4}\s+(.+)$',text)
    pages=re.findall(r'<!--\s*page:\s*(\d+)\s*-->',text)
    return ((headings[-1].strip() if headings else 'sección no indicada')+'; '+
            ('p. '+','.join(dict.fromkeys(pages)) if pages else 'página no indicada'))

def make_record(pair, approved, review):
    cid=pair['chunk_id'];qid=pair['question_id'];split=pair['split']
    positions={name:ranks(review,field).get(cid,'') for name,field in
               [('BM25','top_10_BM25'),('E5-base','top_10_E5_base'),
                ('híbrido','top_10_hibrido')]}
    reason=pair['negative_type']
    candidates=[]
    if reason=='removed_positive_needs_negative_review':
        candidates.append('Fue positivo IA y se retiró del gold; falta decidir explícitamente si es negativo.')
    if isinstance(positions['E5-base'],int) and positions['E5-base']<=5:
        candidates.append('E5-base lo ubicó en Top 5; revisar respuesta semántica/paráfrasis.')
    if isinstance(positions['híbrido'],int) and positions['híbrido']<=5:
        candidates.append('Fusión lo ubicó en Top 5; posible respuesta no anotada.')
    if reason=='hard_candidate':
        candidates.append('Candidato difícil por similitud léxica; la no relevancia nunca se confirmó.')
    if not candidates:
        candidates.append('No relevancia no verificada; comprobar con el texto completo.')
    if split=='test':
        priority='TEST_INDEPENDIENTE'
        score=None
    else:
        score=(30 if reason=='removed_positive_needs_negative_review' else 0)
        score+= (22-positions['E5-base'] if isinstance(positions['E5-base'],int) and positions['E5-base']<=10 else 0)
        score+= (16-positions['híbrido'] if isinstance(positions['híbrido'],int) and positions['híbrido']<=10 else 0)
        score+= (12-positions['BM25'] if isinstance(positions['BM25'],int) and positions['BM25']<=10 else 0)
        score+= 6 if reason=='hard_candidate' else 0
        priority='ALTA' if score>=35 else ('MEDIA' if score>=18 else 'BAJA')
    row={
        'question_id':qid,'pregunta':approved[qid]['question'],'split_original':split,
        'chunk_id_candidato':cid,'documento':pair['document_id'],
        'seccion_pagina':locate_from_review(review,cid,pair['text']),'texto_fragmento':pair['text'],
        'motivo_negativo_original':reason,
        'posicion_original_BM25':positions['BM25'],
        'posicion_original_E5_base':positions['E5-base'],
        'posicion_original_hibrido':positions['híbrido'],
        'evidencia_textual_para_revision':snippet(pair['text'],approved[qid]['question']),
        'posible_relevante_por':' '.join(candidates),
        'prioridad_revision':priority,'estado_revision':'PENDIENTE',
        'decision_humana':'','observaciones':'','nombre_revisor':'','fecha_revision':'',
        'nota_posiciones':('Las posiciones provienen del Top 10 histórico, con pregunta IA original; '
                           'GLF-005 fue reformulada después.' if qid=='GLF-005'
                           else 'Top 10 histórico; ausencia significa fuera de Top 10, no score cero.')}
    return row,score

def prepare(folder):
    folder=Path(folder)
    pairs=read(folder/'dataset_pairs_human_reviewed.csv')
    approved={r['question_id']:r for r in read(folder/'dataset_gold_human_reviewed_v1.csv')}
    reviews={r['question_id']:r for r in read(folder/'revision_humana_gold.csv')}
    pending=[p for p in pairs if p['label']=='0' and p['label_status']=='negative_candidate_unverified']
    if len(pending)!=252 or len(approved)!=50 or len(reviews)!=50:raise ValueError('Entradas inesperadas')
    prepared=[make_record(p,approved,reviews[p['question_id']]) for p in pending]
    dev=sorted((x for x in prepared if x[0]['split_original']!='test'),
               key=lambda x:(-x[1],x[0]['split_original']!='validation',x[0]['question_id'],x[0]['chunk_id_candidato']))
    test=sorted((x for x in prepared if x[0]['split_original']=='test'),
                key=lambda x:(x[0]['question_id'],x[0]['chunk_id_candidato']))
    ordered=[x[0] for x in dev+test]
    csv_write(folder/'revision_negativos_pendientes.csv',FIELDS,ordered)
    first=[x[0] for x in dev[:25]]
    if len(first)!=25 or any(r['split_original']=='test' for r in first):
        raise ValueError('Bloque inicial inválido')
    csv_write(folder/'bloque_revision_01.csv',FIELDS,first)
    # Fichero de adjudicación test ciega: sin posiciones ni orden por ranking.
    blind=[]
    for row,_ in test:
        copy=dict(row)
        for key in ('posicion_original_BM25','posicion_original_E5_base','posicion_original_hibrido'):
            copy[key]=''
        copy['posible_relevante_por']='Decidir solo con pregunta y texto; rankings ocultos para revisión independiente.'
        copy['nota_posiciones']='Ocultas intencionalmente durante adjudicación de test.'
        blind.append(copy)
    csv_write(folder/'revision_negativos_test_independiente.csv',FIELDS,blind)
    inventory=[]
    blocks=[first]+[[x[0] for x in dev[i:i+25]] for i in range(25,len(dev),25)]
    for n,rows in enumerate(blocks,1):
        inventory.append({'bloque':f'{n:02d}','estado':'PREPARADO' if n==1 else 'PENDIENTE',
                          'archivo':'bloque_revision_01.csv' if n==1 else 'revision_negativos_pendientes.csv (filtrar por rango)',
                          'cantidad':len(rows),'splits':','.join(sorted(set(r['split_original'] for r in rows))),
                          'primer_question_id':rows[0]['question_id'],'ultimo_question_id':rows[-1]['question_id'],
                          'rango_en_master':f'{(n-1)*25+1}-{(n-1)*25+len(rows)}'})
    inventory.append({'bloque':'TEST','estado':'PENDIENTE_ADJUDICACION_INDEPENDIENTE',
                      'archivo':'revision_negativos_test_independiente.csv','cantidad':len(test),
                      'splits':'test','primer_question_id':blind[0]['question_id'],
                      'ultimo_question_id':blind[-1]['question_id'],
                      'rango_en_master':f'{len(dev)+1}-{len(ordered)}'})
    csv_write(folder/'inventario_bloques_negativos.csv',list(inventory[0]),inventory)
    if len({(r['question_id'],r['chunk_id_candidato']) for r in ordered})!=252:
        raise ValueError('Candidatos duplicados')
    if any(r['decision_humana'] or r['estado_revision']!='PENDIENTE' for r in ordered):
        raise ValueError('Decisiones rellenadas automáticamente')
    result={'candidatos':len(ordered),'train':sum(r['split_original']=='train' for r in ordered),
            'validation':sum(r['split_original']=='validation' for r in ordered),
            'test':len(test),'bloque_01':len(first),'bloques_dev':len(blocks),
            'priority_counts':dict(Counter(r['prioridad_revision'] for r in ordered)),
            'removed_positive_candidates':sum(r['motivo_negativo_original']=='removed_positive_needs_negative_review' for r in ordered),
            'source':'dataset_pairs_human_reviewed.csv y Top 10 histórico; no se recalcularon rankings ni métricas.',
            'test_priority_independent_of_rankings':True,'human_decisions_filled':0}
    (folder/'inventario_revision_negativos.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--folder',default='evaluacion_rag')
    a=p.parse_args();print(json.dumps(prepare(a.folder),ensure_ascii=False,indent=2))
