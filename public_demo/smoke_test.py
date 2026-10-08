"""Smoke tests para la demo pública aislada.

No acceden a Internet ni consumen Hugging Face. Se ejecutan durante el build
de Render para detectar errores de sintaxis, autenticación y cuotas.
"""
import os

os.environ.setdefault("DEMO_ACCESS_CODE", "smoke-secret")
os.environ.setdefault("GLOBAL_DAILY_LIMIT", "2")
os.environ.setdefault("RATE_LIMIT_PER_HOUR", "20")

from public_demo import app as demo


ROW = {
    "chunk_id": "GLF_MANUAL_SGAS_PUBLIC::P01C01",
    "document_id": "GLF_MANUAL_SGAS_PUBLIC",
    "text": "El SGAS define procedimientos para manejar riesgos ambientales y sociales.",
    "language": "es",
    "source_name": "Manual SGAS",
    "source_url": "https://galapagoslifefund.org.ec/es/",
    "page": 1,
    "score": 1.0,
}


class FakeIndex:
    def search(self, query, limit=5):
        return [ROW]


def reset_state():
    demo._index = FakeIndex()
    demo._records = [ROW]
    demo._rate.clear()
    demo._daily_day = None
    demo._daily_count = 0
    demo.GLOBAL_DAILY_LIMIT = 2
    demo.RATE_LIMIT_PER_HOUR = 20
    demo._generate_answer = lambda query, rows: (
        "El SGAS maneja riesgos ambientales y sociales. "
        "[GLF_MANUAL_SGAS_PUBLIC::P01C01]",
        [{
            "document_id": ROW["document_id"],
            "chunk_id": ROW["chunk_id"],
            "source_name": ROW["source_name"],
            "source_url": ROW["source_url"],
            "page": ROW["page"],
        }],
    )


def main():
    reset_state()
    client = demo.app.test_client()

    response = client.get("/")
    assert response.status_code == 200
    assert b"Demo p" in response.data

    unauthorized = client.post("/api/ask", json={"query": "hola"})
    assert unauthorized.status_code == 401

    headers = {"X-Demo-Key": "smoke-secret"}
    first = client.post("/api/ask", json={"query": "Que es el SGAS?"}, headers=headers)
    assert first.status_code == 200, first.data
    assert first.get_json()["quota_remaining_today"] == 1

    second = client.post("/api/ask", json={"query": "Que maneja el SGAS?"}, headers=headers)
    assert second.status_code == 200, second.data
    assert second.get_json()["quota_remaining_today"] == 0

    third = client.post("/api/ask", json={"query": "Otra consulta"}, headers=headers)
    assert third.status_code == 429

    assert all(
        item["url"].startswith("https://galapagoslifefund.org.ec/")
        for item in demo.PUBLIC_DOCS
    )

    print("public_demo smoke tests: OK")


if __name__ == "__main__":
    main()
