"""Version the authorized train/validation adjudications without touching v1 or test."""
import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from src.eda import load_records
from .prepare_dataset import MEMBER, SPLIT_BY_ALIAS, csv_write
from .question_specs import DOCS

EXPECTED_HASHES = {
    'dataset_gold_human_reviewed_v1.csv': '8ac3b7596ca45289dbcab509c9995a6ae82fa6f0203762b896ffb5e75d3e3101',
    'dataset_pairs_human_reviewed.csv': '932abcd6ff6005de4bc850b51fc73a8a1c3cc29cd709be60371a94b26f1f4fd2',
    'revision_negativos_pendientes.csv': '6c516b434963e49888835da53b8475b9e313dd2bd355645e6b5bf2de5ac04aa8',
    'GLF_192_candidatos_decisiones_operativas_v1_para_Codex.csv': 'c3b13fdcc7a23dc99ab193e895ef8e488d8c60cef8c8941cc9c5dc02e25d1e1a',
    'GLF_10_dudosos_resueltos_auditoria.csv': 'de228399e42bb0a72111f7caec78c16b4202abcde6d6305bb494b298be6ac372',
}
MAIN = 'GLF_192_candidatos_decisiones_operativas_v1_para_Codex.csv'
AUDIT = 'GLF_10_dudosos_resueltos_auditoria.csv'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def unique(rows, qfield, cfield):
    keys = [(r[qfield], r[cfield]) for r in rows]
    if len(keys) != len(set(keys)):
        raise ValueError('Par pregunta–chunk duplicado')
    return set(keys)


def location(text):
    headings = re.findall(r'(?m)^#{1,4}\s+(.+)$', text)
    pages = sorted(set(re.findall(r'<!--\s*page:\s*(\d+)\s*-->', text)))
    return headings[-1].strip() if headings else 'sección no indicada', 'p. ' + ','.join(pages) if pages else 'página no indicada'


def build(archive, folder):
    folder = Path(folder)
    source = folder / 'private' / 'revision_train_validation_20261004'
    for name, expected in EXPECTED_HASHES.items():
        path = source / name if name.startswith('GLF_') else folder / name
        if digest(path) != expected:
            raise ValueError(f'Hash de entrada inesperado: {name}')
    main, audit = read(source / MAIN), read(source / AUDIT)
    v1, pairs, pending = (read(folder / name) for name in
                          ('dataset_gold_human_reviewed_v1.csv', 'dataset_pairs_human_reviewed.csv',
                           'revision_negativos_pendientes.csv'))
    if len(main) != 192 or len(audit) != 10 or len(v1) != 50 or len(pairs) != 328:
        raise ValueError('Cantidad inesperada de filas en fuente o v1')
    keys = unique(main, 'question_id', 'chunk_id_candidato')
    if keys != {(r['question_id'], r['chunk_id_candidato']) for r in pending if r['split_original'] in ('train', 'validation')}:
        raise ValueError('Las decisiones no coinciden con los 192 candidatos de desarrollo')
    if any(r['split_original'] == 'test' for r in main):
        raise ValueError('El archivo principal contiene test')
    if Counter(r['decision_final_operativa'] for r in main) != {'RELEVANTE': 6, 'NO_RELEVANTE': 186}:
        raise ValueError('Conteo de decisiones inesperado')
    provenance = Counter(r['origen_decision_final'] for r in main)
    if provenance != {'PROPUESTA_CHATGPT_CONFIRMADA_POR_USUARIO': 166,
                      'REVISION_ASISTIDA_DELEGADA_POR_USUARIO': 26}:
        raise ValueError('Conteo de procedencia inesperado')
    if any(r['validacion_humana_individual'] != ('CONFIRMACION_USUARIO' if
           r['origen_decision_final'] == 'PROPUESTA_CHATGPT_CONFIRMADA_POR_USUARIO' else 'NO') for r in main):
        raise ValueError('Procedencia y validación individual contradictorias')
    if any(r['fecha_resolucion_operativa'] != '2026-10-04' for r in main):
        raise ValueError('Fecha operativa inesperada')
    bykey = {(r['question_id'], r['chunk_id_candidato']): r for r in main}
    if len(unique(audit, 'question_id', 'chunk_id_candidato')) != 10:
        raise ValueError('Auditoría de diez casos duplicada')
    for r in audit:
        key = (r['question_id'], r['chunk_id_candidato'])
        if (key not in bykey or r['decision_final_operativa'] != bykey[key]['decision_final_operativa']
                or bykey[key]['origen_decision_final'] != 'REVISION_ASISTIDA_DELEGADA_POR_USUARIO'):
            raise ValueError('Auditoría de diez casos discrepa del CSV principal')
    corpus = {r['chunk_id']: r for r in load_records(archive, MEMBER)}
    questions = {r['question_id']: r for r in v1}
    oldpairs = {(r['question_id'], r['chunk_id']): r for r in pairs}
    pending_bykey = {(r['question_id'], r['chunk_id_candidato']): r for r in pending}
    if len(corpus) != 585 or len(questions) != 50 or len(oldpairs) != len(pairs):
        raise ValueError('Corpus, preguntas o pares incompletos')
    oldpositive = {key for key, row in oldpairs.items() if row['label'] == '1'}
    if len(oldpositive) != 76 or oldpositive & keys:
        raise ValueError('Conflicto con etiquetas positivas v1')
    for key, row in bykey.items():
        qid, cid = key
        chunk = corpus.get(cid)
        prior = pending_bykey[key]
        if qid not in questions or chunk is None or key not in oldpairs:
            raise ValueError(f'ID desconocido: {key}')
        if (row['split_original'] != questions[qid]['split'] or row['split_original'] != prior['split_original']
                or row['pregunta'] != questions[qid]['question'] or row['documento'] != chunk['document_id']
                or row['texto_fragmento'] != chunk['text'] or prior['texto_fragmento'] != chunk['text']):
            raise ValueError(f'Contenido o split discordante: {key}')
    additions = defaultdict(list)
    for (qid, cid), row in bykey.items():
        if row['decision_final_operativa'] == 'RELEVANTE':
            additions[qid].append(cid)
    gold2 = []
    for old in v1:
        row = old.copy()
        approved = json.loads(row['relevant_chunk_ids'])
        evidence = json.loads(row['evidencias_por_chunk'])
        provenance_by_chunk = {cid: 'gold_v1_confirmado_por_usuario_revision_asistida' for cid in approved}
        for cid in additions[row['question_id']]:
            chunk = corpus[cid]
            section, page = location(chunk['text'])
            evidence.append({'chunk_id': cid, 'document_id': chunk['document_id'], 'pagina': page,
                             'seccion': section, 'extracto_literal': chunk['text'][:750]})
            approved.append(cid)
            provenance_by_chunk[cid] = bykey[(row['question_id'], cid)]['origen_decision_final']
        row['relevant_chunk_ids'] = json.dumps(approved, ensure_ascii=False)
        row['evidencias_por_chunk'] = json.dumps(evidence, ensure_ascii=False)
        row['procedencia_por_chunk'] = json.dumps(provenance_by_chunk, ensure_ascii=False)
        row['gold_version'] = 'operational_v2'
        gold2.append(row)
    home = {DOCS[alias]: split for alias, split in SPLIT_BY_ALIAS.items()}
    pairs2 = []
    for old in pairs:
        row = old.copy()
        key = (row['question_id'], row['chunk_id'])
        if key in bykey:
            source_row = bykey[key]
            positive = source_row['decision_final_operativa'] == 'RELEVANTE'
            row['label'] = '1' if positive else '0'
            row['negative_type'] = '' if positive else row['negative_type']
            row['label_status'] = 'operational_positive_v2' if positive else 'operational_negative_v2'
            row['human_reviewed'] = 'true' if source_row['validacion_humana_individual'] == 'CONFIRMACION_USUARIO' else 'false'
            row['notes'] = 'Decisión operativa versionada; consultar procedencia_decision. No implica certificación de especialista.'
            row['provenance_decision'] = source_row['origen_decision_final']
            row['validation_individual'] = source_row['validacion_humana_individual']
            row['decision_recorded_at'] = source_row['fecha_resolucion_operativa']
        else:
            row['provenance_decision'] = 'gold_v1_confirmado_por_usuario_revision_asistida' if row['label'] == '1' else 'pendiente_test'
            row['validation_individual'] = 'CONFIRMACION_USUARIO' if row['label'] == '1' else 'PENDIENTE'
            row['decision_recorded_at'] = '2026-10-03' if row['label'] == '1' else ''
        row['eligible_for_training'] = str(row['label'] == '1' and row['split'] == 'train' and
                                           home.get(row['document_id']) == 'train').lower()
        row['gold_version'] = 'operational_v2'
        pairs2.append(row)
    positive_keys = {(r['question_id'], r['chunk_id']) for r in pairs2 if r['label'] == '1'}
    if positive_keys != oldpositive | {key for key, r in bykey.items() if r['decision_final_operativa'] == 'RELEVANTE'}:
        raise ValueError('Pérdida o duplicación de positivos')
    if sum(len(json.loads(r['relevant_chunk_ids'])) for r in gold2) != 82:
        raise ValueError('El gold v2 no suma 82 positivos')
    if sum(r['label'] == '0' and r['label_status'] == 'operational_negative_v2' for r in pairs2) != 186:
        raise ValueError('Los negativos v2 no suman 186')
    if sum(r['label_status'] == 'negative_candidate_unverified' and r['split'] == 'test' for r in pairs2) != 60:
        raise ValueError('Test fue modificado')
    if any(r['eligible_for_training'] == 'true' and r['split'] != 'train' for r in pairs2):
        raise ValueError('Fuga de etiquetas de validation/test')
    goldpath = folder / 'dataset_gold_operational_v2.csv'
    pairpath = folder / 'dataset_pairs_operational_v2.csv'
    csv_write(goldpath, list(gold2[0]), gold2)
    csv_write(pairpath, list(pairs2[0]), pairs2)
    result = {'version': 'operational_v2', 'source_sha256': {name: digest(source / name) for name in (MAIN, AUDIT,
              'GLF_revision_consolidada_192_y_10_resoluciones.xlsx')}, 'v1_sha256': {name: digest(folder / name) for name in
              ('dataset_gold_human_reviewed_v1.csv', 'dataset_pairs_human_reviewed.csv')},
              'v2_sha256': {goldpath.name: digest(goldpath), pairpath.name: digest(pairpath)},
              'source_decisions': len(main), 'source_splits': dict(Counter(r['split_original'] for r in main)),
              'source_provenance': dict(provenance), 'added_positive_relations': 6,
              'positive_relations_v1': 76, 'positive_relations_v2': 82,
              'approved_negative_relations_v2': 186, 'pending_test_candidates': 60,
              'cross_split_positive_training_exclusions': [
                  {'question_id': r['question_id'], 'chunk_id': r['chunk_id']} for r in pairs2
                  if r['label'] == '1' and ((r['split'] == 'train' and home.get(r['document_id']) != 'train')
                                                or (r['split'] == 'test' and home.get(r['document_id']) is None))],
              'new_positive_ids': [{'question_id': qid, 'chunk_id': cid} for qid, ids in sorted(additions.items()) for cid in ids]}
    (folder / 'validacion_revision_operativa_v2.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--archive', required=True, type=Path)
    parser.add_argument('--folder', type=Path, default=Path('evaluacion_rag'))
    args = parser.parse_args()
    print(json.dumps(build(args.archive, args.folder), ensure_ascii=False, indent=2))
