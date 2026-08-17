"""Memória semântica local (RAG) — embeddings via Ollama local + SQLite.

Sem nenhuma API externa: vetores gerados por nomic-embed-text em localhost
e armazenados em um banco SQLite próprio do Leviatã.
"""

from __future__ import annotations

import json
import sqlite3
import struct
from datetime import datetime, timezone
from pathlib import Path

try:
    import numpy as np
    _NUMPY = True
except ImportError:  # pragma: no cover - fallback sem numpy
    _NUMPY = False


class RagError(RuntimeError):
    """Erro seguro de memória semântica sem expor conteúdo."""


class LocalRag:
    """Armazena trechos + vetores e recupera por similaridade de cosseno."""

    def __init__(self, db_path: str | Path, embed_model: str = "nomic-embed-text",
                 ollama_base: str = "http://localhost:11434"):
        self.db_path = Path(db_path).expanduser()
        self.embed_model = embed_model
        self.ollama_base = ollama_base.rstrip("/")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(str(self.db_path)) as con:
            con.execute(
                "CREATE TABLE IF NOT EXISTS rag_entries ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                "created_at TEXT NOT NULL,"
                "text TEXT NOT NULL,"
                "vector BLOB NOT NULL,"
                "dim INTEGER NOT NULL)"
            )
            con.execute("CREATE INDEX IF NOT EXISTS idx_rag_created ON rag_entries(created_at)")

    # --- embeddings via Ollama (100% local) ---

    def _embed(self, text: str) -> list[float]:
        try:
            import urllib.request
            payload = json.dumps({"model": self.embed_model, "prompt": text}).encode()
            request = urllib.request.Request(
                f"{self.ollama_base}/api/embeddings", data=payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(request, timeout=30) as response:
                data = json.loads(response.read().decode())
            return list(data["embedding"])
        except Exception as exc:
            raise RagError(
                f"Não foi possível gerar embeddings (modelo local '{self.embed_model}'). "
                "Confirme o Ollama: ollama pull nomic-embed-text"
            ) from exc

    @staticmethod
    def _pack(vector: list[float]) -> bytes:
        return struct.pack(f"<{len(vector)}f", *vector)

    @staticmethod
    def _unpack(blob: bytes) -> list[float]:
        return list(struct.unpack(f"<{len(blob) // 4}f", blob))

    # --- API ---

    def add(self, text: str) -> int:
        """Indexa um trecho com embedding local e devolve o id."""
        text = " ".join(text.split())
        if not text:
            raise RagError("Trecho vazio não pode ser indexado.")
        if len(text) > 12_000:
            raise RagError("Trecho muito longo para indexação (máx. 12k caracteres).")
        vector = self._embed(text)
        stamp = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(str(self.db_path)) as con:
            cursor = con.execute(
                "INSERT INTO rag_entries (created_at, text, vector, dim) VALUES (?,?,?,?)",
                (stamp, text, self._pack(vector), len(vector)),
            )
            return int(cursor.lastrowid)

    def search(self, query: str, top_k: int = 3, min_score: float = 0.25) -> list[dict]:
        """Busca por similaridade de cosseno entre o vetor da consulta e o índice."""
        query_vector = self._embed(query)
        with sqlite3.connect(str(self.db_path)) as con:
            rows = con.execute(
                "SELECT id, created_at, text, vector FROM rag_entries"
            ).fetchall()
        results: list[dict] = []
        for row_id, stamp, text, blob in rows:
            stored = self._unpack(blob)
            score = _cosine(query_vector, stored)
            if score >= min_score:
                results.append({"id": row_id, "created_at": stamp, "text": text, "score": round(float(score), 4)})
        results.sort(key=lambda item: item["score"], reverse=True)
        return results[:top_k]

    def context(self, query: str, top_k: int = 3) -> str:
        """Recupera o contexto semântico formatado para o prompt do agente."""
        matches = self.search(query, top_k=top_k)
        if not matches:
            return ""
        return "\n".join(
            f"[memória {item['created_at'][:19]} · score {item['score']}]\n{item['text']}"
            for item in matches
        )

    def stats(self) -> dict[str, int]:
        with sqlite3.connect(str(self.db_path)) as con:
            count = con.execute("SELECT COUNT(*) FROM rag_entries").fetchone()[0]
        return {"entries": int(count)}


def _cosine(a: list[float], b: list[float]) -> float:
    if not _NUMPY:
        return _cosine_pure(a, b)
    import numpy as np
    va, vb = np.asarray(a, dtype=np.float32), np.asarray(b, dtype=np.float32)
    denom = float(np.linalg.norm(va) * np.linalg.norm(vb))
    if denom == 0:
        return 0.0
    return float(np.dot(va, vb) / denom)


def _cosine_pure(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)
