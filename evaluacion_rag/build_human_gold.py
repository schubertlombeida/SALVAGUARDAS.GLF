"""Versiona decisiones manuales declaradas por el equipo, sin alterar el gold IA."""
import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

from src.eda import load_records
from .prepare_dataset import MEMBER, csv_write
from .question_specs import DOCS

ORIGINAL_SHA256 = 'c3cdc04cc06a9ed2936491498aa373e22f61bea87e8095bd2e9cbb02abe4fe3b'
NAME = 'dataset_gold_human_reviewed_v1.csv'

def cid(alias, number):
    return f'{DOCS[alias]}::{number:04d}'

def choices():
    # Solo los cambios expresos de la revisión recibida; los demás se conservan.
    return {
        1: {'add':[cid('J',1)]},
        3: {'add':[cid('F',1)]},
        5: {'question':'¿Cómo clasifica el GLF los proyectos en categorías A, B y C según su nivel de riesgo ambiental y social?',
            'remove':[cid('E',5)]},
        7: {'add':[cid('M',6)]},
        8: {'remove':[cid('D',3)]},
        12:{'add':[cid('E',2)]},
        13:{'add':[cid('E',2),cid('E',3)]},
        14:{'add':[cid('E',2)]},
        15:{'add':[cid('E',2)]},
        16:{'add':[cid('E',2)]},
        17:{'add':[cid('M',4)]},
        20:{'add':[cid('D',5)],'remove':[cid('G',6)]},
        21:{'add':[cid('D',3)],'remove':[cid('A',4)]},
        22:{'add':[cid('D',5),cid('D',8)]},
        23:{'remove':[cid('M',3)]},
        26:{'remove':[cid('G',5)]},
        31:{'add':['CREF-03_ES_20210614-ifc-ps-guidance-note-1-es::0052']},
        32:{'add':[cid('G2',2)]},
        36:{'remove':[cid('E',1)]},
        37:{'remove':[cid('M',6)]},
        39:{'remove':[cid('I',2)]},
        40:{'add':[cid('M',5)],'remove':[cid('M',6)]},
        44:{'remove':[cid('G',4)]},
        46:{'remove':[cid('A',4),cid('D',8)]},
        48:{'add':[cid('E',2)]},
        49:{'add':[cid('E',2)]},
    }

def build(archive, folder, reviewer='', review_date=''):
    folder=Path(folder);archive=Path(archive)
    original=folder/'dataset_gold.csv'
    if hashlib.sha256(original.read_bytes()).hexdigest()!=ORIGINAL_SHA256:
        raise ValueError('Gold IA original cambió: preservar y auditar antes de continuar')
    with original.open(encoding='utf-8-sig',newline='') as stream:
        old=list(csv.DictReader(stream))
    records=load_records(archive,MEMBER);byid={r['chunk_id']:r for r in records}
    if len(old)!=50 or len(records)!=585 or len(byid)!=585:
        raise ValueError('Corpus o preguntas inesperados')
    decisions=choices();changed=[];new=[]
    for i,row in enumerate(old,1):
        qid=f'GLF-{i:03d}'
        if row['question_id']!=qid or row['human_reviewed']!='false':
            raise ValueError('Orden o estado IA inesperado')
        before=json.loads(row['relevant_chunk_ids'])
        action=decisions.get(i,{})
        add=action.get('add',[]);remove=action.get('remove',[])
        if len(add)!=len(set(add)) or len(remove)!=len(set(remove)):
            raise ValueError(f'Decisión duplicada: {qid}')
        if set(add)&set(before) or not set(remove)<=set(before):
            raise ValueError(f'Decisión incompatible con original: {qid}')
        after=[x for x in before if x not in remove]+add
        if not after or len(after)!=len(set(after)) or not set(after)<=set(byid):
            raise ValueError(f'Relevantes inválidos: {qid}')
        updated=dict(row)
        updated['question']=action.get('question',row['question'])
        updated['relevant_chunk_ids']=json.dumps(after,ensure_ascii=False)
        updated['human_reviewed']='true'
        updated['review_status']='human_reviewed_per_user_declaration'
        updated['annotation_source']='manual_decisions_supplied_by_user'
        updated['reviewer_name']=reviewer or 'equipo GLF (identidad pendiente)'
        updated['review_date']=review_date
        updated['review_recorded_at']=date.today().isoformat()
        updated['review_date_note']='Fecha real de revisión pendiente de confirmar' if not review_date else 'Fecha declarada por el equipo'
        evidence=[]
        for relevant_id in after:
            source=byid[relevant_id]
            pages=re.findall(r'<!--\s*page:\s*(\d+)\s*-->',source['text'])
            headings=re.findall(r'(?m)^#{1,4}\s+(.+)$',source['text'])
            evidence.append({'chunk_id':relevant_id,'document_id':source['document_id'],
                             'pagina':'p. '+','.join(dict.fromkeys(pages)) if pages else 'no indicada',
                             'seccion':headings[-1].strip() if headings else 'no indicada en este chunk',
                             'extracto_literal':' '.join(source['text'].split())[:600]})
        updated['evidencias_por_chunk']=json.dumps(evidence,ensure_ascii=False)
        updated['notes']=('Decisión manual declarada por el usuario; evidencia textual original conservada. '
                          'Los nuevos relevantes requieren comprobar su cita específica en el corpus.')
        new.append(updated)
        if add or remove or updated['question']!=row['question']:
            changed.append({'question_id':qid,'old_question':row['question'],'new_question':updated['question'],
                            'added':add,'removed':remove,'before':before,'after':after,'split':row['split']})
    fields=list(new[0]);csv_write(folder/NAME,fields,new)
    check=validate(archive,folder,new,old,changed)
    report=['# Cambios de la revisión humana v1','',
            'La revisión de las 50 preguntas fue declarada manualmente por el usuario del proyecto. '
            'Se conserva `dataset_gold.csv` con las etiquetas IA originales; '
            f'no se cambió su SHA-256 `{ORIGINAL_SHA256}`. '
            'La fecha de registro se guarda por separado de la fecha real de revisión.','',
            f"Relaciones IA: {sum(len(json.loads(x['relevant_chunk_ids'])) for x in old)}. "
            f"Relaciones humanas v1: {check['relevantes_total']}. "
            f"Agregadas: {sum(len(x['added']) for x in changed)}. "
            f"Eliminadas: {sum(len(x['removed']) for x in changed)}. "
            f"Preguntas con cambios: {len(changed)}.",'']
    for change in changed:
        report += [f"## {change['question_id']}",'',
                   f"- Split conservado: `{change['split']}`.",
                   f"- Agregados: {', '.join('`'+x+'`' for x in change['added']) or 'ninguno'}.",
                   f"- Eliminados: {', '.join('`'+x+'`' for x in change['removed']) or 'ninguno'}."]
        if change['old_question']!=change['new_question']:
            report += [f"- Pregunta anterior: {change['old_question']}",
                       f"- Pregunta aprobada: {change['new_question']}"]
        report += ['']
    report += ['Las otras 24 preguntas conservan redacción y relaciones IA, pero están incluidas en la '
               'declaración de revisión manual. La revisión de etiquetas negativas no fue suministrada.','']
    (folder/'cambios_revision_humana.md').write_text('\n'.join(report),encoding='utf-8')
    return check

def validate(archive,folder,new,old,changed):
    records=load_records(archive,MEMBER);known={r['chunk_id'] for r in records}
    errors=[]
    ids=[x['question_id'] for x in new]
    if ids!=[f'GLF-{i:03d}' for i in range(1,51)]:errors.append('IDs de pregunta')
    if [x['split'] for x in new]!=[x['split'] for x in old]:errors.append('Split cambiado')
    if any(x['human_reviewed']!='true' for x in new):errors.append('Revisión incompleta')
    if any(x['question']!=y['question'] for x,y in zip(new,old) if x['question_id']!='GLF-005'):
        errors.append('Pregunta no autorizada cambiada')
    counts=Counter();relations=0
    for x in new:
        relevant=json.loads(x['relevant_chunk_ids']);relations+=len(relevant)
        counts[x['split']]+=len(relevant)
        if not relevant or len(relevant)!=len(set(relevant)) or not set(relevant)<=known:
            errors.append(x['question_id']+': relevantes inválidos')
    for change in changed:
        actual=set(json.loads(next(x['relevant_chunk_ids'] for x in new if x['question_id']==change['question_id'])))
        if not set(change['added'])<=actual or set(change['removed'])&actual:
            errors.append(change['question_id']+': decisión mal aplicada')
    path=Path(folder)/NAME
    output={'preguntas_esperadas':50,'preguntas_en_archivo':len(new),
            'relevantes_total':relations,'relevantes_por_split':dict(counts),
            'preguntas_por_cantidad_relevantes':dict(Counter(str(len(json.loads(x['relevant_chunk_ids']))) for x in new)),
            'preguntas_cambiadas':len(changed),'agregados':sum(len(x['added']) for x in changed),
            'eliminados':sum(len(x['removed']) for x in changed),
            'errores_detectados':errors,'gold_humano_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'gold_ia_sha256':ORIGINAL_SHA256,
            'test_question_ids_unchanged':all(x['question_id']==y['question_id'] and x['split']==y['split']
                                                for x,y in zip(new,old) if x['split']=='test'),
            'test_frozen_for_parameter_selection':True}
    (Path(folder)/'validacion_gold_humano.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
    if errors:raise ValueError('; '.join(errors))
    return output

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--archive',required=True);p.add_argument('--folder',default='evaluacion_rag')
    p.add_argument('--reviewer',default='');p.add_argument('--review-date',default='')
    a=p.parse_args()
    print(json.dumps(build(a.archive,a.folder,a.reviewer,a.review_date),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
