import io
import json
import os
import re
import threading
import time
from collections import defaultdict, deque
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import Flask, Response, jsonify, request
from pypdf import PdfReader

from src.retrieval_optimized import OptimizedGLFRetriever


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024

MAX_QUERY_CHARS = 600
HF_TIMEOUT_SECONDS = 35
RATE_LIMIT_PER_HOUR = int(os.getenv("RATE_LIMIT_PER_HOUR", "30"))
HF_MODEL = os.getenv("HF_MODEL", "Qwen/Qwen2.5-7B-Instruct-1M:fastest")

PUBLIC_DOCS = [
    {
        "document_id": "GLF_MANUAL_SGAS_PUBLIC",
        "name": "Manual SGAS",
        "url": "https://galapagoslifefund.org.ec/es/wp-content/uploads/sites/2/2026/04/A-GLF-Manual-SGAS-sin-Anexos-Oct-2024-final-.pdf",
    },
    {
        "document_id": "GLF_ANEXO_A_PUBLIC",
        "name": "Anexo A - Política Ambiental y Social",
        "url": "https://galapagoslifefund.org.ec/es/wp-content/uploads/sites/2/2025/02/ANEXO-A-Politica-Ambiental-y-Social_Web-Oct-2024.pdf",
    },
    {
        "document_id": "GLF_ANEXO_B_PUBLIC",
        "name": "Anexo B - Lista de Exclusión",
        "url": "https://galapagoslifefund.org.ec/es/wp-content/uploads/sites/2/2025/02/ANEXO-B-Lista-de-Exclusion_Web-Oct-2024.pdf",
    },
    {
        "document_id": "GLF_ANEXO_D_PUBLIC",
        "name": "Anexo D - Marco Legal y Estrategia de Autorización",
        "url": "https://galapagoslifefund.org.ec/es/wp-content/uploads/sites/2/2026/04/ANEXO-D-Marco-Legal-y-Estrategia-de-Autorizacion_Web-Oct-2024.pdf",
    },
    {
        "document_id": "GLF_ANEXO_F_PUBLIC",
        "name": "Anexo F - Cláusulas estándar",
        "url": "https://galapagoslifefund.org.ec/es/wp-content/uploads/sites/2/2025/02/ANEXO-F-Clausulas-Estandar_Web-Oct-2024.pdf",
    },
    {
        "document_id": "GLF_ANEXO_H_PUBLIC",
        "name": "Anexo H - Roles y Responsabilidades",
        "url": "https://galapagoslifefund.org.ec/es/wp-content/uploads/sites/2/2025/02/ANEXO-H-Roles-Responsabilidades_Web-Oct-2024.pdf",
    },
    {
        "document_id": "GLF_ANEXO_J_PUBLIC",
        "name": "Anexo J - Definiciones",
        "url": "https://galapagoslifefund.org.ec/es/wp-content/uploads/sites/2/2025/02/ANEXO-J-Definiciones_Web-Oct-2024.pdf",
    },
]

_records = None
_index = None
_init_error = None
_init_lock = threading.Lock()
_rate = defaultdict(deque)
_rate_lock = threading.Lock()

CHUNK_RE = re.compile(r"\[([A-Z0-9_]+::P\d{2}C\d{2})\]")


def _clean_text(text):
    text = (text or "").replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _chunk_page(text, document_id, page_no, source_name, source_url):
    clean = _clean_text(text)
    if not clean:
        return []

    chunks = []
    target = 1200
    overlap = 180
    start = 0
    idx = 1
    while start < len(clean):
        end = min(len(clean), start + target)
        if end < len(clean):
            boundary = clean.rfind(" ", start + int(target * 0.65), end)
            if boundary > start:
                end = boundary
        piece = clean[start:end].strip()
        if piece:
            chunks.append(
                {
                    "chunk_id": f"{document_id}::P{page_no:02d}C{idx:02d}",
                    "document_id": document_id,
                    "text": piece,
                    "language": "es",
                    "source_name": source_name,
                    "source_url": source_url,
                    "page": page_no,
                }
            )
            idx += 1
        if end >= len(clean):
            break
        start = max(end - overlap, start + 1)
    return chunks


def _download_pdf(url):
    req = Request(
        url,
        headers={
            "User-Agent": "GLF-Academic-Demo/1.0 (+public sources only)",
            "Accept": "application/pdf",
        },
    )
    with urlopen(req, timeout=20) as response:
        data = response.read(20 * 1024 * 1024)
    if not data.startswith(b"%PDF"):
        raise ValueError("La fuente pública no devolvió un PDF válido.")
    return data


def _build_public_corpus():
    rows = []
    for doc in PUBLIC_DOCS:
        pdf = _download_pdf(doc["url"])
        reader = PdfReader(io.BytesIO(pdf))
        for page_no, page in enumerate(reader.pages, start=1):
            rows.extend(
                _chunk_page(
                    page.extract_text() or "",
                    doc["document_id"],
                    page_no,
                    doc["name"],
                    doc["url"],
                )
            )
    if len(rows) < 30:
        raise RuntimeError("No se pudo construir un corpus público suficiente.")
    return rows


def _ensure_index():
    global _records, _index, _init_error
    if _index is not None:
        return
    with _init_lock:
        if _index is not None:
            return
        try:
            rows = _build_public_corpus()
            _records = rows
            _index = OptimizedGLFRetriever(rows)
            _init_error = None
        except Exception as exc:
            _init_error = str(exc)
            raise


def _client_ip():
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def _rate_limited():
    now = time.time()
    cutoff = now - 3600
    key = _client_ip()
    with _rate_lock:
        bucket = _rate[key]
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= RATE_LIMIT_PER_HOUR:
            return True
        bucket.append(now)
    return False


def _authorized():
    expected = os.getenv("DEMO_ACCESS_CODE", "").strip()
    if not expected:
        return False
    supplied = request.headers.get("X-Demo-Key", "").strip()
    return supplied == expected


def _safe_query():
    payload = request.get_json(silent=True) or {}
    query = str(payload.get("query", "")).strip()
    if not query:
        return None, ("Escribe una pregunta.", 400)
    if len(query) > MAX_QUERY_CHARS:
        return None, (f"La pregunta supera {MAX_QUERY_CHARS} caracteres.", 400)
    if any(ord(c) < 9 for c in query):
        return None, ("La pregunta contiene caracteres no permitidos.", 400)
    return query, None


def _hf_chat(prompt):
    token = os.getenv("HF_TOKEN", "").strip()
    if not token:
        raise RuntimeError("La demo pública no tiene configurado HF_TOKEN.")

    body = json.dumps(
        {
            "model": HF_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Eres un asistente documental del Galápagos Life Fund. "
                        "Responde solo con la evidencia suministrada. No inventes requisitos."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0,
            "max_tokens": 320,
            "stream": False,
        }
    ).encode("utf-8")

    req = Request(
        "https://router.huggingface.co/v1/chat/completions",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urlopen(req, timeout=HF_TIMEOUT_SECONDS) as response:
            data = json.load(response)
        return data["choices"][0]["message"]["content"].strip()
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, KeyError) as exc:
        raise RuntimeError("El generador público no está disponible en este momento.") from exc


def _generate_answer(query, rows):
    context_blocks = []
    allowed = set()
    by_id = {}
    for row in rows[:4]:
        chunk_id = row["chunk_id"]
        allowed.add(chunk_id)
        by_id[chunk_id] = row
        context_blocks.append(
            f"CHUNK_ID: {chunk_id}\n"
            f"FUENTE: {row['source_name']} · página {row['page']}\n"
            f"TEXTO:\n{row['text'][:1500]}"
        )

    prompt = (
        "CONTEXTO DOCUMENTAL PÚBLICO DEL GLF:\n\n"
        + "\n\n".join(context_blocks)
        + f"\n\nPREGUNTA: {query}\n\n"
        + "Responde en español, de forma breve y concreta, usando exclusivamente el contexto. "
          "Cada afirmación debe terminar con uno de los CHUNK_ID exactos entre corchetes. "
          "Nunca cites un identificador que no aparezca en el contexto. "
          "Si el contexto no permite responder con seguridad, responde exactamente: "
          "'La documentación pública recuperada es insuficiente para responder esta pregunta.'"
    )

    answer = _hf_chat(prompt)
    if "documentación pública recuperada es insuficiente" in answer.casefold():
        return "La documentación pública recuperada es insuficiente para responder esta pregunta.", []

    cited = set(CHUNK_RE.findall(answer))
    if not cited or cited - allowed:
        return "La documentación pública recuperada es insuficiente para responder esta pregunta.", []

    sources = [
        {
            "document_id": by_id[cid]["document_id"],
            "chunk_id": cid,
            "source_name": by_id[cid]["source_name"],
            "source_url": by_id[cid]["source_url"],
            "page": by_id[cid]["page"],
        }
        for cid in sorted(cited)
    ]
    return answer, sources


@app.after_request
def _security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "script-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'none'; form-action 'self'"
    )
    return response


@app.get("/")
def home():
    return Response(INDEX_HTML, mimetype="text/html")


@app.get("/robots.txt")
def robots():
    return Response("User-agent: *\nDisallow: /\n", mimetype="text/plain")


@app.get("/healthz")
def healthz():
    try:
        _ensure_index()
    except Exception:
        return jsonify({"ok": False, "public_demo": True}), 503
    return jsonify(
        {
            "ok": True,
            "public_demo": True,
            "documents": len(PUBLIC_DOCS),
            "chunks": len(_records or []),
            "retriever": "BM25-heading-authority-v2",
        }
    )


@app.post("/api/search")
def api_search():
    if _rate_limited():
        return jsonify({"error": "Límite temporal de consultas alcanzado."}), 429
    if not _authorized():
        return jsonify({"error": "Código de acceso inválido."}), 401
        return jsonify({"error": "Límite temporal de consultas alcanzado."}), 429
    query, error = _safe_query()
    if error:
        message, status = error
        return jsonify({"error": message}), status
    try:
        _ensure_index()
        rows = _index.search(query, limit=5)
    except Exception:
        return jsonify({"error": "No se pudo cargar el corpus público del GLF."}), 503

    return jsonify(
        {
            "results": [
                {
                    "chunk_id": row["chunk_id"],
                    "document_id": row["document_id"],
                    "source_name": row.get("source_name"),
                    "source_url": row.get("source_url"),
                    "page": row.get("page"),
                    "text": row["text"],
                    "score": row.get("score", 0),
                }
                for row in rows
            ]
        }
    )


@app.post("/api/ask")
def api_ask():
    if _rate_limited():
        return jsonify({"error": "Límite temporal de consultas alcanzado."}), 429
    if not _authorized():
        return jsonify({"error": "Código de acceso inválido."}), 401

    query, error = _safe_query()
    if error:
        message, status = error
        return jsonify({"error": message}), status

    started = time.perf_counter()
    try:
        _ensure_index()
        r0 = time.perf_counter()
        rows = _index.search(query, limit=5)
        retrieval_seconds = time.perf_counter() - r0

        g0 = time.perf_counter()
        answer, sources = _generate_answer(query, rows)
        generation_seconds = time.perf_counter() - g0
    except Exception as exc:
        return jsonify(
            {
                "error": "La demo pública no está disponible temporalmente.",
                "detail": type(exc).__name__,
            }
        ), 503

    insufficient = not sources
    return jsonify(
        {
            "generated": not insufficient,
            "answer": answer,
            "sources": sources,
            "results": [
                {
                    "chunk_id": row["chunk_id"],
                    "document_id": row["document_id"],
                    "source_name": row.get("source_name"),
                    "source_url": row.get("source_url"),
                    "page": row.get("page"),
                    "text": row["text"],
                    "score": row.get("score", 0),
                }
                for row in rows
                if not insufficient
            ],
            "timings": {
                "retrieval_seconds": retrieval_seconds,
                "generation_seconds": generation_seconds,
                "total_seconds": time.perf_counter() - started,
            },
            "public_demo": True,
        }
    )


INDEX_HTML = r"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Demo pública · Asistente RAG GLF</title>
<style>
:root{font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#172033;background:#f5f7fb}
*{box-sizing:border-box}body{margin:0}.wrap{max-width:980px;margin:0 auto;padding:28px 18px 60px}
.banner{background:#102038;color:white;border-radius:20px;padding:26px 28px;margin-bottom:18px;box-shadow:0 14px 35px #1d2a3d22}
.kicker{font-size:12px;letter-spacing:.08em;font-weight:800;color:#72e6d0}.banner h1{margin:6px 0 8px;font-size:30px}.banner p{margin:0;color:#d7e1ef;line-height:1.55}
.notice{background:#e9fff6;border:1px solid #99ebc7;border-radius:14px;padding:14px 16px;margin-bottom:18px;color:#175b45}
.card{background:white;border:1px solid #dfe6ef;border-radius:18px;padding:22px;box-shadow:0 10px 28px #1d2a3d12}
.row{display:flex;gap:10px}.row input{flex:1;padding:13px 14px;border:1px solid #bfcadd;border-radius:12px;font-size:15px}.row button{border:0;border-radius:12px;background:#4f46e5;color:white;font-weight:800;padding:0 20px;cursor:pointer}.row button:disabled{opacity:.55;cursor:wait}
.examples{display:flex;gap:8px;flex-wrap:wrap;margin:13px 0 0}.chip{border:1px solid #d9e0ec;background:#f8fafc;color:#334155;border-radius:999px;padding:7px 10px;font-size:12px;cursor:pointer}
.result{margin-top:18px;border-top:1px solid #e6ebf2;padding-top:18px}.status{display:flex;justify-content:space-between;gap:12px;align-items:center}.badge{font-size:12px;font-weight:800;border-radius:999px;padding:5px 9px;background:#dcfce7;color:#166534}.badge.warn{background:#fff7d6;color:#8a5700}
.answer{background:#eef2ff;border:1px solid #c7d2fe;border-radius:14px;padding:16px;margin-top:12px;white-space:pre-wrap;line-height:1.58}
.sources{display:grid;gap:10px;margin-top:14px}.source{border:1px solid #dfe6ef;border-radius:12px;padding:13px;background:#fbfcfe}.source a{color:#3730a3;font-weight:800;text-decoration:none}.source p{font-size:13px;color:#475569;line-height:1.55;margin:7px 0 0}.footer{margin-top:15px;font-size:12px;color:#64748b}.error{background:#fff1f2;border:1px solid #fecdd3;color:#9f1239;border-radius:12px;padding:12px;margin-top:14px}
@media(max-width:680px){.row{flex-direction:column}.row button{height:44px}.banner h1{font-size:25px}}
</style>
</head>
<body>
<div class="wrap">
  <section class="banner">
    <div class="kicker">DEMO PÚBLICA SEGURA · PROYECTO ACADÉMICO</div>
    <h1>Asistente RAG de Salvaguardas GLF</h1>
    <p>Consulta únicamente documentos oficiales publicados por el Galápagos Life Fund. Esta demo corre en infraestructura aislada y no tiene acceso a la computadora, discos ni archivos privados del equipo.</p>
  </section>
  <div class="notice"><strong>Privacidad:</strong> no se permiten cargas de archivos, no se expone el corpus privado y las consultas no se guardan en la aplicación. Las respuestas son asistencia documental y deben verificarse en la fuente original.</div>
  <section class="card">
    <div class="row">
      <input id="q" maxlength="600" placeholder="Escribe una pregunta sobre el SGAS del GLF">
      <button id="go">Consultar</button>
    </div>
    <div class="row" style="margin-top:10px">
      <input id="key" type="password" autocomplete="off" placeholder="Código de acceso de la demo">
      <button id="savekey" type="button" style="background:#0f766e">Guardar código</button>
    </div>
    <div class="examples">
      <button class="chip">¿Qué instrumentos ambientales y sociales son obligatorios para todos los proyectos?</button>
      <button class="chip">¿Qué debe hacer el GLF durante la evaluación de la detección?</button>
      <button class="chip">¿Qué diferencia existe entre proyectos de Categoría B y C?</button>
    </div>
    <div id="out"></div>
    <div class="footer">Fuentes: documentos públicos oficiales del GLF descargados desde galapagoslifefund.org.ec al iniciar el servicio. Generación mediante Hugging Face Inference Providers. Límite de consultas para evitar abuso.</div>
  </section>
</div>
<script>
const q=document.getElementById('q'), go=document.getElementById('go'), out=document.getElementById('out');
const key=document.getElementById('key'), savekey=document.getElementById('savekey');
key.value=sessionStorage.getItem('glf_demo_key')||'';
savekey.onclick=()=>{sessionStorage.setItem('glf_demo_key',key.value.trim());savekey.textContent='Guardado'};
document.querySelectorAll('.chip').forEach(b=>b.onclick=()=>{q.value=b.textContent;q.focus()});
function esc(s){return String(s||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
async function ask(){
  const query=q.value.trim(); if(!query)return;
  go.disabled=true; go.textContent='Consultando…'; out.innerHTML='';
  try{
    const demoKey=(sessionStorage.getItem('glf_demo_key')||key.value||'').trim();
    const r=await fetch('/api/ask',{method:'POST',headers:{'Content-Type':'application/json','X-Demo-Key':demoKey},body:JSON.stringify({query})});
    const d=await r.json(); if(!r.ok)throw new Error(d.error||'Error');
    const ok=d.generated && (d.sources||[]).length>0;
    const ms=((d.timings||{}).total_seconds||0).toFixed(2);
    let html='<div class="result"><div class="status"><strong>Respuesta</strong><span class="badge '+(ok?'':'warn')+'">'+(ok?'Con evidencia':'Abstención segura')+' · '+ms+' s</span></div>';
    html+='<div class="answer">'+esc(d.answer)+'</div>';
    if(ok){
      html+='<div class="sources">';
      (d.results||[]).slice(0,4).forEach(x=>{
        html+='<div class="source"><a target="_blank" rel="noopener noreferrer" href="'+esc(x.source_url)+'">'+esc(x.source_name||x.document_id)+'</a> · pág. '+esc(x.page)+'<p>'+esc((x.text||'').slice(0,520))+'</p></div>'
      });
      html+='</div>';
    }
    html+='</div>'; out.innerHTML=html;
  }catch(e){out.innerHTML='<div class="error">'+esc(e.message||'No disponible')+'</div>'}
  finally{go.disabled=false;go.textContent='Consultar'}
}
go.onclick=ask;q.addEventListener('keydown',e=>{if(e.key==='Enter')ask()});
</script>
</body>
</html>"""


if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
