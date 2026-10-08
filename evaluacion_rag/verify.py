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
    review_path=folder/'revision_humana_gold.csv'
    if review_path.exists():
        review=read_csv(review_path)
        candidate_rows=read_csv(folder/'revision_humana_candidatos.csv')
        priorities=read_csv(folder/'casos_revision_prioritaria.csv')
        diagnostic=json.loads((folder/'diagnostico_particiones.json').read_text(encoding='utf-8'))
        assert len(review)==50 and {r['question_id'] for r in review}=={q['question_id'] for q in gold}
        assert len(priorities)==diagnostic['priority_cases']
        assert sum(p['tipo']=='hard_negative' for p in priorities)==147
        candidate_ids=set()
        for r in review:
            q=next(q for q in gold if q['question_id']==r['question_id'])
            assert r['question']==q['question'] and r['split']==q['split']
            assert json.loads(r['relevant_chunk_ids_propuestos'])==json.loads(q['relevant_chunk_ids'])
            assert r['cita_literal_justificacion']==q['answer_reference']
            assert r['texto_completo_chunk_relevante_propuesto']==byid[json.loads(q['relevant_chunk_ids'])[0]]['text']
            assert all(r[k]=='' for k in ('pregunta_aprobada','chunk_relevante_aprobado',
                'agregar_chunk_ids','eliminar_chunk_ids','observaciones_revisor','nombre_revisor','fecha_revision'))
            candidates=json.loads(r['candidatos_consolidados'])
            ids={c['chunk_id'] for c in candidates}
            assert len(ids)==len(candidates) and set(json.loads(q['relevant_chunk_ids']))<=ids
            for c in candidates:assert c['extracto']==' '.join(byid[c['chunk_id']]['text'].split())[:650]
            candidate_ids.update(ids)
            for key in ('top_10_BM25','top_10_E5_base','top_10_hibrido'):
                ranking=json.loads(r[key])
                assert len(ranking)==10 and [x['posicion'] for x in ranking]==list(range(1,11))
                assert all(x['chunk_id'] in ids and x['documento']==byid[x['chunk_id']]['document_id']
                           and isinstance(x['score'],(int,float)) for x in ranking)
        assert len(candidate_ids)==diagnostic['unique_candidate_chunks']
        assert len(candidate_rows)==sum(len(json.loads(r['candidatos_consolidados'])) for r in review)
        assert all(r['texto_completo']==byid[r['chunk_id']]['text'] and r['relevante_aprobado']==''
                   and r['observaciones_revisor']=='' for r in candidate_rows)
    print('VERIFICADO: 585 fragmentos; 50 preguntas con referencias textuales; 316 pares; 150 consultas medidas; 3 resúmenes consistentes; sin fuga detectada.')

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--folder',default='evaluacion_rag')
    args=p.parse_args();verify(args.archive,args.folder)
