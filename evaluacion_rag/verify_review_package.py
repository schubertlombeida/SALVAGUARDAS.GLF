"""Valida los CSV de adjudicación sin aprobar respuestas automáticamente."""
import csv
import json
from pathlib import Path

def read(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as stream:
        return list(csv.DictReader(stream))

def verify(folder):
    folder=Path(folder)
    gold=read(folder/'dataset_gold_human_reviewed_v1.csv')
    all_rows=read(folder/'revision_negativos_pendientes.csv')
    first=read(folder/'bloque_revision_01.csv')
    test=read(folder/'revision_negativos_test_independiente.csv')
    inventory=read(folder/'inventario_bloques_negativos.csv')
    manifest=json.loads((folder/'inventario_revision_negativos.json').read_text(encoding='utf-8'))
    assert len(gold)==50 and sum(len(json.loads(r['relevant_chunk_ids'])) for r in gold)==76
    assert len(all_rows)==manifest['candidatos']==252
    assert len(first)==manifest['bloque_01']==25
    assert len(test)==manifest['test']==60
    assert sum(r['split_original']=='train' for r in all_rows)==133
    assert sum(r['split_original']=='validation' for r in all_rows)==59
    assert sum(r['split_original']=='test' for r in all_rows)==60
    assert len({(r['question_id'],r['chunk_id_candidato']) for r in all_rows})==252
    assert all(r['estado_revision']=='PENDIENTE' and r['decision_humana']==''
               and r['observaciones']=='' and r['nombre_revisor']=='' for r in all_rows)
    assert all(r['split_original'] in ('train','validation') for r in first)
    assert {(r['question_id'],r['chunk_id_candidato']) for r in first}=={
        (r['question_id'],r['chunk_id_candidato']) for r in all_rows[:25]}
    assert all(r['split_original']=='test' and r['prioridad_revision']=='TEST_INDEPENDIENTE'
               and all(r[k]=='' for k in ('posicion_original_BM25','posicion_original_E5_base','posicion_original_hibrido'))
               for r in test)
    assert len(inventory)==9 and sum(int(r['cantidad']) for r in inventory)==252
    assert all(max(len(v) for v in row.values())<32767 for row in all_rows+first+test)
    approved={(r['question_id'],cid) for r in gold for cid in json.loads(r['relevant_chunk_ids'])}
    assert not {(r['question_id'],r['chunk_id_candidato']) for r in all_rows}&approved
    print('VERIFICADO: 252 negativos pendientes, bloque inicial 25, test ciego 60, 76 positivos preservados, sin decisiones automáticas.')

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--folder',default='evaluacion_rag')
    a=p.parse_args();verify(a.folder)
