"""Auditoría de separaciones y similitud entre fragmentos de pares."""
import csv
import json
from collections import Counter,defaultdict
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def audit(path,threshold=.85):
    rows=list(csv.DictReader(Path(path).open(encoding='utf-8-sig',newline='')))
    if not rows:raise ValueError('Pares vacíos')
    query_splits=defaultdict(set);doc_splits=defaultdict(set);chunk_splits=defaultdict(set);seen=set()
    for r in rows:
        key=(r['question_id'],r['chunk_id'])
        if key in seen:raise ValueError('Par duplicado')
        seen.add(key)
        query_splits[r['question_id']].add(r['split']);doc_splits[r['document_id']].add(r['split']);chunk_splits[r['chunk_id']].add(r['split'])
        if r['human_reviewed']!='false' or r['review_status']!='ai_proposed':raise ValueError('Estado humano falso')
    if any(len(v)>1 for d in (query_splits,doc_splits,chunk_splits) for v in d.values()):raise ValueError('Fuga de grupo')
    unique={r['chunk_id']:r for r in rows};chunks=list(unique.values())
    matrix=TfidfVectorizer(analyzer='char',ngram_range=(3,5),max_features=30000).fit_transform([r['text'] for r in chunks])
    sim=cosine_similarity(matrix);max_cross=0.;near=[]
    for i,a in enumerate(chunks):
        for j in range(i+1,len(chunks)):
            b=chunks[j]
            if a['split']==b['split']:continue
            score=float(sim[i,j]);max_cross=max(max_cross,score)
            if score>=threshold:near.append({'a':a['chunk_id'],'b':b['chunk_id'],'cosine':score})
    if near:raise ValueError(f'Fragmentos casi idénticos entre particiones: {near[:3]}')
    return {'pairs':len(rows),'unique_questions':len(query_splits),'unique_chunks':len(unique),'unique_documents':len(doc_splits),
            'label_counts':dict(Counter(r['label'] for r in rows)),
            'split_counts':dict(Counter(r['split'] for r in rows)),
            'hard_candidate_count':sum(r['negative_type']=='hard_candidate' for r in rows),
            'document_disjoint':True,'chunk_disjoint':True,'query_disjoint':True,
            'near_duplicate_method':'TF-IDF carácter n-gramas 3-5, coseno, comparación entre particiones',
            'near_duplicate_threshold':threshold,'near_duplicate_count':len(near),'max_cross_split_cosine':max_cross,
            'labels_ai_only':True,'hard_negatives_human_verified':False}

if __name__=='__main__':
    value=audit(Path('evaluacion_rag/dataset_pairs.csv'))
    Path('evaluacion_rag/auditoria_pares.json').write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(value,ensure_ascii=False,indent=2))
