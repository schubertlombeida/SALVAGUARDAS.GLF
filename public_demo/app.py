import hmac
import io
import json
import os
import re
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import Flask, Response, jsonify, request
from pypdf import PdfReader

from src.retrieval_optimized import OptimizedGLFRetriever


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024

MAX_QUERY_CHARS = 600
HF_TIMEOUT_SECONDS = 35
RATE_LIMIT_PER_HOUR = int(os.getenv("RATE_LIMIT_PER_HOUR", "15"))
GLOBAL_DAILY_LIMIT = int(os.getenv("GLOBAL_DAILY_LIMIT", "60"))
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
_daily_lock = threading.Lock()
_daily_day = None
_daily_count = 0

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
    return bool(supplied) and hmac.compare_digest(supplied, expected)


def _take_global_daily_slot():
    """Reserva una consulta generativa dentro del tope global UTC."""
    global _daily_day, _daily_count
    today = datetime.now(timezone.utc).date().isoformat()
    with _daily_lock:
        if _daily_day != today:
            _daily_day = today
            _daily_count = 0
        if _daily_count >= GLOBAL_DAILY_LIMIT:
            return False, 0
        _daily_count += 1
        return True, max(0, GLOBAL_DAILY_LIMIT - _daily_count)


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

    slot_ok, quota_remaining = _take_global_daily_slot()
    if not slot_ok:
        return jsonify({
            "error": "La demo alcanzó su límite global de consultas de hoy. Inténtalo mañana."
        }), 429

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
            "quota_remaining_today": quota_remaining,
        }
    )


INDEX_HTML = r"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Asistente RAG GLF · Demo pública segura</title>
<style>
:root{
  font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  color:#0f172a;background:#f1f5f9
}
*{box-sizing:border-box}
body{margin:0;background:#f1f5f9}
.topbar{background:#0f172a;color:white;border-bottom:4px solid #0f766e}
.topbar-inner{max-width:1180px;margin:auto;padding:16px 22px;display:flex;justify-content:space-between;align-items:center;gap:16px}
.brand{display:flex;align-items:center;gap:12px}
.mark{width:42px;height:42px;border-radius:12px;background:#0f766e;display:grid;place-items:center;font-weight:900}
.brand-title{font-size:17px;font-weight:850}.brand-sub{font-size:11px;color:#94a3b8;margin-top:2px}
.secure{font-size:11px;background:#dcfce7;color:#166534;border-radius:999px;padding:7px 10px;font-weight:800}
.layout{max-width:1180px;margin:24px auto;padding:0 18px 50px;display:grid;grid-template-columns:220px 1fr;gap:20px}
.sidebar{background:white;border:1px solid #e2e8f0;border-radius:16px;padding:16px;height:max-content;box-shadow:0 8px 22px #0f172a0b}
.nav-title{font-size:10px;color:#64748b;font-weight:900;letter-spacing:.08em;margin-bottom:10px}
.nav-item{padding:10px 11px;border-radius:10px;font-size:12px;color:#475569;margin-bottom:6px}
.nav-item.active{background:#eef2ff;color:#3730a3;font-weight:800}
.main{min-width:0}
.card{background:white;border:1px solid #e2e8f0;border-radius:18px;padding:24px;box-shadow:0 10px 28px #0f172a0c}
.head{display:flex;justify-content:space-between;gap:16px;align-items:flex-start;border-bottom:1px solid #e2e8f0;padding-bottom:16px}
.label{display:inline-flex;background:#e0e7ff;color:#3730a3;border-radius:7px;padding:6px 9px;font-size:10px;font-weight:900;letter-spacing:.05em;text-transform:uppercase}
h1{font-size:23px;margin:10px 0 5px}p{margin:0;line-height:1.55}.muted{color:#64748b;font-size:13px}
.access{min-width:230px}.access input{width:100%;padding:10px 11px;border:1px solid #cbd5e1;border-radius:10px;font-size:12px}
.access button{width:100%;margin-top:7px;padding:9px;border:0;border-radius:9px;background:#0f766e;color:white;font-weight:800;cursor:pointer}
.security-note{margin-top:16px;padding:12px 14px;border:1px solid #a7f3d0;background:#ecfdf5;color:#166534;border-radius:12px;font-size:12px;line-height:1.5}
.query-row{display:flex;gap:9px;margin-top:19px}.query-row input{flex:1;padding:13px 14px;border:1px solid #cbd5e1;border-radius:12px;font-size:14px;outline:none}.query-row input:focus{border-color:#6366f1;box-shadow:0 0 0 3px #e0e7ff}
.query-row button{padding:0 22px;border:0;border-radius:12px;background:#4f46e5;color:white;font-weight:850;cursor:pointer}.query-row button:disabled{opacity:.55;cursor:wait}
.examples{display:flex;gap:7px;flex-wrap:wrap;margin-top:10px}.chip{border:1px solid #cbd5e1;background:#f8fafc;color:#475569;border-radius:999px;padding:7px 10px;font-size:11px;cursor:pointer}
.results{margin-top:18px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:16px;padding:18px}
.result-head{display:flex;justify-content:space-between;align-items:center;gap:12px;border-bottom:1px solid #e2e8f0;padding-bottom:10px;font-size:13px;font-weight:850}
.badge{font-size:10px;font-weight:900;border-radius:999px;padding:5px 8px;background:#dcfce7;color:#166534}.badge.warn{background:#fef3c7;color:#92400e}
.answer{background:#eef2ff;border:1px solid #c7d2fe;border-radius:12px;padding:14px;margin-top:13px;white-space:pre-wrap;line-height:1.58;font-size:13px}
.section-title{font-size:12px;font-weight:850;margin:15px 0 8px}
.sources{display:grid;gap:9px}.source{background:white;border:1px solid #e2e8f0;border-radius:11px;padding:12px}.source-top{display:flex;justify-content:space-between;gap:8px;align-items:flex-start}.source a{color:#3730a3;font-weight:850;text-decoration:none;font-size:11px}.chunk{font-family:ui-monospace,monospace;color:#64748b;font-size:9px}.source p{font-size:11px;color:#64748b;line-height:1.55;margin-top:6px}
.warning{margin-top:13px;background:#fffbeb;border:1px solid #fde68a;color:#92400e;border-radius:11px;padding:11px 12px;font-size:11px;line-height:1.5}
.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:16px}.metric{background:white;border:1px solid #e2e8f0;border-radius:12px;padding:12px}.metric strong{display:block;font-size:16px}.metric span{font-size:10px;color:#64748b}
.error{margin-top:13px;background:#fff1f2;border:1px solid #fecdd3;color:#9f1239;border-radius:11px;padding:12px;font-size:12px}
.loading{color:#4338ca;font-weight:800;font-size:12px}
.foot{margin-top:15px;color:#64748b;font-size:10px;line-height:1.5}
@media(max-width:850px){.layout{grid-template-columns:1fr}.sidebar{display:none}.head{flex-direction:column}.access{width:100%}.metrics{grid-template-columns:repeat(2,1fr)}}
@media(max-width:560px){.query-row{flex-direction:column}.query-row button{height:44px}.metrics{grid-template-columns:1fr 1fr}.topbar-inner{align-items:flex-start}}
</style>
</head>
<body>
<header class="topbar">
  <div class="topbar-inner">
    <div class="brand">
      <div class="mark">GLF</div>
      <div><div class="brand-title">Portal de Salvaguardas · Demo académica</div><div class="brand-sub">Consulta documental pública · RAG</div></div>
    </div>
    <div class="secure">✓ Demo aislada de la PC</div>
  </div>
</header>

<div class="layout">
  <aside class="sidebar">
    <div class="nav-title">PANEL PERSONAL GLF</div>
    <div class="nav-item">1. Inicio Técnico / Dashboard</div>
    <div class="nav-item">2. Convocatorias</div>
    <div class="nav-item">3. Revisión Técnica</div>
    <div class="nav-item active">6. Asistente RAG</div>
    <div class="nav-item">7. Reportes</div>
    <div class="nav-item">8. Auditoría</div>
  </aside>

  <main class="main">
    <section class="card">
      <div class="head">
        <div>
          <span class="label">Asistente RAG GLF · Demo pública segura</span>
          <h1>Consulta Inteligente del Corpus Normativo GLF</h1>
          <p class="muted">Misma experiencia del prototipo local, pero esta versión usa exclusivamente documentos oficiales públicos del GLF y corre fuera de tu computadora.</p>
        </div>
        <div class="access">
          <input id="key" type="password" autocomplete="off" placeholder="Código de acceso">
          <button id="savekey" type="button">Guardar código en esta pestaña</button>
        </div>
      </div>

      <div class="security-note"><strong>Seguridad:</strong> no se permiten archivos, el corpus privado no está en la nube, la aplicación no tiene conexión con tu PC y existe un límite global diario de consultas para evitar abuso económico.</div>

      <div class="metrics">
        <div class="metric"><strong>83,6%</strong><span>Recall@5 desarrollo</span></div>
        <div class="metric"><strong>90,9%</strong><span>Recall@5 validation</span></div>
        <div class="metric"><strong>4,617 s</strong><span>p95 versión local</span></div>
        <div class="metric"><strong>Top 5</strong><span>BM25-heading-authority-v2</span></div>
      </div>

      <div class="query-row">
        <input id="q" maxlength="600" value="¿Cuáles son las actividades no subvencionables según la Lista de Exclusión del GLF?">
        <button id="go">Consultar Corpus</button>
      </div>
      <div class="examples">
        <button class="chip">¿Qué instrumentos ambientales y sociales son obligatorios para todos los proyectos?</button>
        <button class="chip">¿Qué debe hacer el GLF durante la evaluación de la detección?</button>
        <button class="chip">¿Qué diferencia existe entre los proyectos de Categoría B y Categoría C?</button>
      </div>

      <div id="out" class="results">
        <div class="result-head"><span>Asistente RAG conectado</span><span class="badge">Corpus público GLF</span></div>
        <p class="muted" style="margin-top:12px">Escribe una consulta. La respuesta mostrará evidencia, página y enlace al PDF oficial cuando exista soporte documental.</p>
        <div class="warning"><strong>Aviso Técnico:</strong> esta herramienta apoya la consulta documental. No aprueba, rechaza ni determina elegibilidad de postulaciones.</div>
      </div>

      <div class="foot">La demo pública puede tener latencia distinta a la versión local porque la generación se ejecuta mediante un proveedor remoto. Los KPI formales del proyecto corresponden a la versión local evaluada y documentada.</div>
    </section>
  </main>
</div>

<script>
const q=document.getElementById('q'), go=document.getElementById('go'), out=document.getElementById('out');
const key=document.getElementById('key'), savekey=document.getElementById('savekey');
key.value=sessionStorage.getItem('glf_demo_key')||'';
savekey.onclick=()=>{sessionStorage.setItem('glf_demo_key',key.value.trim());savekey.textContent='Código guardado ✓'};
document.querySelectorAll('.chip').forEach(b=>b.onclick=()=>{q.value=b.textContent;q.focus()});
function esc(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
async function ask(){
  const query=q.value.trim();
  if(query.length<3){out.innerHTML='<div class="error">Escribe al menos 3 caracteres.</div>';return}
  const demoKey=(sessionStorage.getItem('glf_demo_key')||key.value||'').trim();
  if(!demoKey){out.innerHTML='<div class="error">Introduce primero el código de acceso de la demo.</div>';return}
  go.disabled=true;go.textContent='Consultando…';
  out.innerHTML='<div class="loading">Buscando evidencia pública y generando respuesta…</div>';
  try{
    const r=await fetch('/api/ask',{
      method:'POST',
      headers:{'Content-Type':'application/json','X-Demo-Key':demoKey},
      body:JSON.stringify({query})
    });
    const d=await r.json();
    if(!r.ok)throw new Error(d.error||('Error HTTP '+r.status));
    const grounded=Boolean(d.generated&&(d.sources||[]).length);
    const total=Number(d.timings?.total_seconds||0).toFixed(2);
    const remaining=Number.isFinite(Number(d.quota_remaining_today))?Number(d.quota_remaining_today):null;
    const evidence=grounded?(d.results||[]).slice(0,4):[];
    const sources=evidence.length?evidence.map((x,i)=>`
      <div class="source">
        <div class="source-top">
          <a href="${esc(x.source_url)}" target="_blank" rel="noopener noreferrer">Fuente ${i+1}: ${esc(x.source_name||x.document_id)} · pág. ${esc(x.page)}</a>
          <span class="chunk">${esc(x.chunk_id)}</span>
        </div>
        <p>${esc((x.text||'').slice(0,700))}${(x.text||'').length>700?'…':''}</p>
      </div>`).join(''):'<p class="muted">No se muestran fragmentos porque el sistema se abstuvo.</p>';
    out.innerHTML=`
      <div class="result-head">
        <span>Respuesta del Asistente RAG</span>
        <div><span class="badge ${grounded?'':'warn'}">${grounded?'Respuesta generada con evidencia':'Abstención segura'}</span> <span class="muted">${total} s</span></div>
      </div>
      <div class="answer">${esc(d.answer)}</div>
      <div class="section-title">${grounded?'Evidencia recuperada':'Evidencia no suficiente'}</div>
      <div class="sources">${sources}</div>
      <div class="warning"><strong>Aviso Técnico:</strong> verifica las fuentes antes de tomar una decisión institucional.${remaining===null?'':' Consultas globales restantes hoy: '+remaining+'.'}</div>`;
  }catch(e){
    out.innerHTML='<div class="error"><strong>No se pudo completar la consulta.</strong><br>'+esc(e.message||'Servicio no disponible')+'</div>';
  }finally{go.disabled=false;go.textContent='Consultar Corpus'}
}
go.onclick=ask;
q.addEventListener('keydown',e=>{if(e.key==='Enter')ask()});
</script>
</body>
</html>"""


if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
