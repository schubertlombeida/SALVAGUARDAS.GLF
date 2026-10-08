"""Índice E5 de fragmentos GLF con caché validada por corpus y modelo."""
import hashlib
import json
import os
from pathlib import Path
import numpy as np

MODEL_ID = 'intfloat/multilingual-e5-base'
MODEL_REVISION = 'd128750597153bb5987e10b1c3493a34e5a4502a'
WINDOW_ALGORITHM = 'recursive_words_tokenizer_512_v1'


def windows(text, tokenizer):
    words = text.split()
    if not words:
        raise ValueError('Fragmento sin texto')
    result = []
    def visit(w):
        passage = 'passage: ' + ' '.join(w)
        if len(tokenizer.encode(passage, add_special_tokens=True)) <= 512:
            result.append(passage)
        elif len(w) > 1:
            middle = len(w)//2
            visit(w[:middle]); visit(w[middle:])
        else:
            raise ValueError('Token excesivo sin segmentación segura')
    visit(words)
    return result


def load_model():
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(MODEL_ID, revision=MODEL_REVISION, device='cpu', trust_remote_code=False)
    model.max_seq_length = 512
    return model


def model_revision():
    return MODEL_REVISION


class E5Index:
    name = 'E5-base'
    def __init__(self, records, archive_sha, cache_dir, model=None, batch_size=8):
        self.records = records
        self.model = model or load_model()
        self.revision = model_revision()
        self.cache_dir = Path(cache_dir);self.cache_dir.mkdir(parents=True,exist_ok=True)
        text_hash = hashlib.sha256('\n'.join(r['chunk_id']+'\0'+r['text'] for r in records).encode()).hexdigest()
        key = hashlib.sha256(json.dumps({'archive':archive_sha,'text':text_hash,'model':MODEL_ID,'revision':self.revision,'window':WINDOW_ALGORITHM},sort_keys=True).encode()).hexdigest()
        cache=self.cache_dir/(key+'.npz')
        if cache.is_file():
            with np.load(cache,allow_pickle=False) as saved:
                self.owners=saved['owners'].astype(np.int32);self.vectors=saved['vectors'].astype(np.float32)
            if len(self.owners)==len(self.vectors) and np.all(np.isfinite(self.vectors)):
                self.cache_hit=True
                return
            raise ValueError('Caché E5 dañada; retirarla tras revisarla')
        owners=[];texts=[]
        for i,record in enumerate(records):
            parts=windows(record['text'],self.model.tokenizer)
            texts.extend(parts);owners.extend([i]*len(parts))
        self.owners=np.asarray(owners,dtype=np.int32)
        self.vectors=np.asarray(self.model.encode(texts,batch_size=batch_size,normalize_embeddings=True,show_progress_bar=True,convert_to_numpy=True),dtype=np.float32)
        if self.vectors.shape!=(len(texts),768) or not np.all(np.isfinite(self.vectors)):
            raise ValueError('Embeddings E5 inválidos')
        tmp=cache.with_suffix('.tmp')
        with open(tmp,'wb') as f:np.savez_compressed(f,owners=self.owners,vectors=self.vectors)
        os.replace(tmp,cache)
        self.cache_hit=False

    def search(self,query,limit=5):
        if not query.strip():return []
        prefixed='query: '+query.strip()
        if len(self.model.tokenizer.encode(prefixed,add_special_tokens=True))>512:
            raise ValueError('Consulta excede 512 tokens')
        vector=np.asarray(self.model.encode([prefixed],normalize_embeddings=True,show_progress_bar=False,convert_to_numpy=True),dtype=np.float32)[0]
        window_scores=self.vectors@vector
        scores=np.full(len(self.records),-np.inf,dtype=np.float32)
        np.maximum.at(scores,self.owners,window_scores)
        ranked=sorted(range(len(scores)),key=lambda i:(-float(scores[i]),i))[:limit]
        return [dict(self.records[i],score=round(float(scores[i]),6)) for i in ranked]
