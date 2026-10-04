"""Exporta candidatos completos para revisión; no modifica etiquetas ni métricas."""
import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from difflib import SequenceMatcher

from src.eda import load_records
from src.retrieval import BM25, tokens
from src.semantic import Hybrid
from .e5_index import E5Index, MODEL_ID
from .evaluate_retrieval import load_gold
from .prepare_dataset import MEMBER, csv_write

METHODS = ('BM25', 'E5-base', 'BM25+E5-RRF')
MANUAL = ('pregunta_aprobada', 'chunk_relevante_aprobado', 'agregar_chunk_ids',
          'eliminar_chunk_ids', 'observaciones_revisor', 'nombre_revisor', 'fecha_revision')


def read_csv(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def locate(record):
    text = record['text']
    headings = re.findall(r'(?m)^#{1,4}\s+(.+)$', text)
    pages = re.findall(r'<!--\s*page:\s*(\d+)\s*-->', text)
    label = (headings[-1].strip() if headings else 'sección no indicada')
    label += '; ' + ('p. ' + ','.join(dict.fromkeys(pages)) if pages else 'página no indicada')
    return label


def pack(rankings):
    return json.dumps(rankings, ensure_ascii=False)


def norm(value):
    return ' '.join(tokens(value))


def heading_similarity(question, record):
    headings = re.findall(r'(?m)^#{1,4}\s+(.+)$', record['text'])
    if not headings:
        return 0.0
    q = norm(question)
    return max(SequenceMatcher(None, q, norm(h)).ratio() for h in headings)


def run(archive, folder):
    archive, folder = Path(archive), Path(folder)
    records = load_records(archive, MEMBER)
    by_id = {r['chunk_id']: r for r in records}
    questions = load_gold(folder / 'dataset_gold.csv', set(by_id))
    pairs = read_csv(folder / 'dataset_pairs.csv')
    if len(records) != 585 or len(questions) != 50 or len(pairs) != 316:
        raise ValueError('Entradas distintas de la evaluación registrada')
    if any(p['human_reviewed'] != 'false' or p['review_status'] != 'ai_proposed' for p in pairs):
        raise ValueError('Estado humano inconsistente')
    bm = BM25(records)
    e5 = E5Index(records, hashlib.sha256(archive.read_bytes()).hexdigest(), folder / '.cache')
    hybrid = Hybrid(bm, e5, depth=20, constant=60)
    methods = dict(zip(METHODS, (bm, e5, hybrid)))
    hard = [p for p in pairs if p['negative_type'] == 'hard_candidate']
    if len(hard) != 147 or MODEL_ID != 'intfloat/multilingual-e5-base':
        raise ValueError('Modelo o cantidad de negativos no esperada')
    review = []
    candidate_detail = []
    priorities = []
    diagnostic = defaultdict(list)
    candidate_union = set()
    for q in questions:
        qid, gold = q['question_id'], set(q['gold'])
        ranked = {name: method.search(q['question'], limit=10) for name, method in methods.items()}
        indexes = {name: {r['chunk_id']: i for i, r in enumerate(rows, 1)}
                   for name, rows in ranked.items()}
        union = set(gold) | set().union(*(set(indexes[name]) for name in METHODS))
        candidate_union.update(union)
        candidate_rows = []
        for cid in sorted(union):
            r = by_id[cid]
            candidate_rows.append({
                'chunk_id': cid, 'documento': r['document_id'],
                'seccion_pagina': locate(r),
                'propuesto_relevante': cid in gold,
                'rango_BM25': indexes['BM25'].get(cid, ''),
                'rango_E5': indexes['E5-base'].get(cid, ''),
                'rango_hibrido': indexes['BM25+E5-RRF'].get(cid, ''),
                'extracto': ' '.join(r['text'].split())[:650]})
            candidate_detail.append({
                'question_id':qid, 'question':q['question'], 'split':q['split'],
                'chunk_id':cid, 'documento':r['document_id'], 'seccion_pagina':locate(r),
                'propuesto_relevante':cid in gold,
                'rango_BM25':indexes['BM25'].get(cid, ''),
                'rango_E5':indexes['E5-base'].get(cid, ''),
                'rango_hibrido':indexes['BM25+E5-RRF'].get(cid, ''),
                'texto_completo':r['text'], 'relevante_aprobado':'',
                'observaciones_revisor':'', 'nombre_revisor':'', 'fecha_revision':''})
        def ranking_rows(name):
            return [{
                'posicion': i, 'chunk_id': r['chunk_id'],
                'documento': r['document_id'], 'seccion_pagina': locate(r),
                'extracto': ' '.join(r['text'].split())[:900],
                'score': r['score']}
                for i, r in enumerate(ranked[name], 1)]
        primary = by_id[q['gold'][0]]
        row = {
            'question_id': qid, 'question': q['question'], 'split': q['split'],
            'relevant_chunk_ids_propuestos': json.dumps(q['gold'], ensure_ascii=False),
            'documento_fuente_propuesto': q['source_document'],
            'seccion_pagina_propuesta': q['source_section_or_page'],
            'cita_literal_justificacion': q['answer_reference'],
            'texto_completo_chunk_relevante_propuesto': primary['text'],
            'top_10_BM25': pack(ranking_rows('BM25')),
            'top_10_E5_base': pack(ranking_rows('E5-base')),
            'top_10_hibrido': pack(ranking_rows('BM25+E5-RRF')),
            'candidatos_consolidados': pack(candidate_rows),
            **{field: '' for field in MANUAL},
        }
        review.append(row)
        hits = {name: bool(gold & set(list(indexes[name])[:5])) for name in METHODS}
        # Discrepancia observable, no juicio de pertinencia.
        top_sets = [set(list(indexes[name])[:5]) for name in METHODS]
        common = set.intersection(*top_sets)
        union_top = set.union(*top_sets)
        disagreement = 1 - len(common) / len(union_top)
        head_sim = heading_similarity(q['question'], primary)
        reasons = []
        if not any(hits.values()): reasons.append('fallan_los_tres_top5')
        if disagreement >= .8: reasons.append('rankings_top5_muy_distintos')
        if len(gold) > 1: reasons.append('multiples_relevantes_propuestos')
        if head_sim >= .72: reasons.append('pregunta_similar_a_encabezado')
        for reason in reasons:
            priorities.append({'tipo':'pregunta', 'prioridad': 0 if reason == 'fallan_los_tres_top5' else 1,
                               'question_id':qid, 'split':q['split'], 'motivo':reason,
                               'detalle':f'BM25={hits["BM25"]}; E5={hits["E5-base"]}; híbrido={hits["BM25+E5-RRF"]}; desacuerdo={disagreement:.2f}; similitud_titulo={head_sim:.2f}',
                               'chunk_id': '', 'documento':q['source_document'],
                               'texto_candidato':'', 'revision_humana':''})
        diagnostic[q['split']].append({
            'question_id':qid, 'source_document':q['source_document'],
            'query_words':len(tokens(q['question'])), 'query_characters':len(q['question']),
            'relevant_count':len(gold), 'heading_similarity':round(head_sim, 3),
            'head_like':head_sim >= .72, 'all_miss':not any(hits.values()),
            'bm25_hit':hits['BM25'], 'e5_hit':hits['E5-base'], 'hybrid_hit':hits['BM25+E5-RRF'],
            'top5_disagreement':round(disagreement, 3),
        })
    # Todos los hard negatives necesitan revisión. Ordenar los que entran en E5
    # entre los primeros diez como sospechosos; no afirmar que sean positivos.
    review_by_q = {r['question_id']: r for r in review}
    for p in hard:
        ranking = json.loads(review_by_q[p['question_id']]['top_10_E5_base'])
        e5_rank = next((r['posicion'] for r in ranking if r['chunk_id'] == p['chunk_id']), None)
        priorities.append({
            'tipo':'hard_negative', 'prioridad': 1 if e5_rank else 2,
            'question_id':p['question_id'], 'split':p['split'],
            'motivo':'hard_negative_posible_positivo' if e5_rank else 'hard_negative_sin_verificar',
            'detalle':f'Candidato negativo por BM25; rango E5 top10={e5_rank or "fuera"}; confirmar si responde la pregunta.',
            'chunk_id':p['chunk_id'], 'documento':p['document_id'],
            'texto_candidato':p['text'], 'revision_humana':''})
    priorities.sort(key=lambda p:(p['prioridad'], p['question_id'], p['tipo'], p['chunk_id']))
    csv_write(folder/'revision_humana_gold.csv', list(review[0]), review)
    csv_write(folder/'revision_humana_candidatos.csv', list(candidate_detail[0]), candidate_detail)
    csv_write(folder/'casos_revision_prioritaria.csv', list(priorities[0]), priorities)
    by_split = {}
    for split, rows in diagnostic.items():
        docs = Counter(r['source_document'] for r in rows)
        by_split[split] = {
            'questions':len(rows), 'questions_by_document':dict(docs),
            'mean_query_words':round(sum(r['query_words'] for r in rows)/len(rows), 2),
            'mean_query_characters':round(sum(r['query_characters'] for r in rows)/len(rows), 2),
            'relevant_count_distribution':dict(Counter(r['relevant_count'] for r in rows)),
            'mean_relevant_count':round(sum(r['relevant_count'] for r in rows)/len(rows), 2),
            'head_like_count':sum(r['head_like'] for r in rows),
            'mean_heading_similarity':round(sum(r['heading_similarity'] for r in rows)/len(rows), 3),
            'all_miss_count':sum(r['all_miss'] for r in rows),
            'mean_top5_disagreement':round(sum(r['top5_disagreement'] for r in rows)/len(rows), 3),
            'questions_detail':rows,
        }
    result = {'questions_for_review':len(review), 'unique_candidate_chunks':len(candidate_union),
              'hard_negatives_for_review':len(hard), 'priority_cases':len(priorities),
              'priority_questions':len({p['question_id'] for p in priorities if p['tipo']=='pregunta'}),
              'priority_by_reason':dict(Counter(p['motivo'] for p in priorities)),
              'split_diagnostics':by_split,
              'model_id':MODEL_ID, 'human_reviewed':False,
              'note':'Top 10 regenerados con índices y parámetros congelados; no cambian las métricas registradas.'}
    (folder/'diagnostico_particiones.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--archive',required=True)
    ap.add_argument('--folder',default='evaluacion_rag')
    args = ap.parse_args()
    out = run(args.archive,args.folder)
    print(json.dumps({k:v for k,v in out.items() if k != 'split_diagnostics'},ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
