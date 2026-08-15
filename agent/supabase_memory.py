"""Persistência explícita de resultados aprovados em uma tabela Supabase do proprietário."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

import requests

from agent.connections import ConnectionStore


class SupabaseMemoryError(RuntimeError):
    """Erro de persistência que não expõe a chave do projeto ou conteúdo secreto."""


class SupabaseKnowledgeStore:
    default_table = "kawa_knowledge"

    def __init__(self, connections: ConnectionStore | None = None, http: Any = None):
        self.connections = connections or ConnectionStore()
        self.http = http or requests.Session()

    @staticmethod
    def _clean_text(text: str) -> str:
        patterns = [
            r"(?i)(api[_ -]?key|authorization|bearer|token|password)\s*[:=]\s*[^\s,;]+",
            r"\b(?:sk|nvapi|sbp)_[A-Za-z0-9_\-]+",
        ]
        result = text
        for pattern in patterns:
            result = re.sub(pattern, "[redigido]", result)
        return result

    def save_research(self, title: str, content: str, table: str | None = None) -> None:
        target = (table or self.default_table).strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,62}", target):
            raise SupabaseMemoryError("Nome de tabela inválido.")
        endpoint = self.connections.get_endpoint("supabase")
        token = self.connections.get_token("supabase")
        if not endpoint or not token:
            raise SupabaseMemoryError(
                "Supabase não configurado. Salve endpoint HTTPS e token no cofre local antes de ativar a persistência."
            )
        payload = {
            "title": self._clean_text(title)[:180],
            "content": self._clean_text(content),
            "source": "nvidia_research",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        headers = {"apikey": token, "Authorization": f"Bearer {token}", "Prefer": "return=minimal"}
        try:
            response = self.http.post(f"{endpoint}/rest/v1/{target}", headers=headers, json=payload, timeout=30)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise SupabaseMemoryError("Não foi possível salvar o resultado no Supabase. Verifique tabela, RLS e permissões.") from exc
