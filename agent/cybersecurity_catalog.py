"""Catálogo consultivo de referências de segurança com classificação de risco.

O módulo apenas indexa metadados e descreve limites de uso. Ele não executa
scripts, payloads, scanners de rede ou técnicas do catálogo de origem.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any


class CybersecurityReferenceCatalog:
    """Pesquisa metadados de skills e separa referência defensiva de ação restrita."""

    source_url = "https://github.com/mukul975/anthropic-cybersecurity-skills"
    license_name = "Apache-2.0"
    _restricted_prefixes = (
        "abusing-", "bypassing-", "exploiting-", "cracking-", "post-exploiting-",
        "relaying-", "evading-", "weaponizing-", "deploying-ransomware-",
    )
    _scope_prefixes = (
        "testing-", "performing-", "scanning-", "assessing-", "enumerating-",
        "discovering-", "simulating-", "red-teaming-",
    )

    def __init__(self, index_path: str | Path | None = None):
        self.index_path = Path(index_path) if index_path else Path(__file__).with_name("data") / "anthropic_cybersecurity_index.json"

    @classmethod
    @lru_cache(maxsize=8)
    def _load_index(cls, raw_path: str, modified_ns: int) -> tuple[tuple[tuple[str, str, str, str, str], ...], dict[str, int]]:
        """Carrega e normaliza o índice uma vez por versão do arquivo."""
        try:
            payload = json.loads(Path(raw_path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            payload = {"skills": []}
        skills = payload.get("skills", []) if isinstance(payload, dict) else []
        counts = {"defensiva": 0, "escopo_autorizado": 0, "restrita": 0}
        entries: list[tuple[str, str, str, str, str]] = []
        for item in skills:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", ""))
            description = str(item.get("description", ""))
            path = str(item.get("path", ""))
            classification = cls.classification(name)
            counts[classification] += 1
            entries.append((name, description, path, classification, f"{name} {description}".casefold()))
        return tuple(entries), counts

    def _index(self) -> tuple[tuple[tuple[str, str, str, str, str], ...], dict[str, int]]:
        try:
            modified_ns = self.index_path.stat().st_mtime_ns
        except OSError:
            return (), {"defensiva": 0, "escopo_autorizado": 0, "restrita": 0}
        return self._load_index(str(self.index_path.resolve()), modified_ns)

    @classmethod
    def classification(cls, name: str) -> str:
        lowered = name.casefold()
        if lowered.startswith(cls._restricted_prefixes):
            return "restrita"
        if lowered.startswith(cls._scope_prefixes):
            return "escopo_autorizado"
        return "defensiva"

    def summary(self) -> dict[str, int | str]:
        skills, counts = self._index()
        return {
            "source": self.source_url,
            "license": self.license_name,
            "total": len(skills),
            **counts,
        }

    def search(self, topic: str, include_restricted: bool = False, limit: int = 8) -> dict[str, Any]:
        terms = [term for term in re.findall(r"[\w-]+", topic.casefold()) if len(term) > 2]
        matches: list[dict[str, str]] = []
        for name, description, path, classification, haystack in self._index()[0]:
            if classification == "restrita" and not include_restricted:
                continue
            score = sum(term in haystack for term in terms)
            if score:
                matches.append({
                    "name": name,
                    "description": description[:280],
                    "classification": classification,
                    "path": path,
                    "score": str(score),
                })
        matches.sort(key=lambda entry: (-int(entry["score"]), entry["name"]))
        return {
            "summary": self.summary(),
            "topic": topic,
            "matches": matches[:max(1, min(limit, 20))],
            "rules": (
                "Use referências defensivas para análise, detecção, hardening e resposta. "
                "Referências de escopo autorizado exigem permissão escrita, escopo e regras de engajamento. "
                "Referências restritas não fornecem instruções operacionais nem são executadas automaticamente."
            ),
        }

    def render(self, topic: str, include_restricted: bool = False, limit: int = 8) -> str:
        result = self.search(topic, include_restricted=include_restricted, limit=limit)
        summary = result["summary"]
        lines = [
            "=== Referências de Cibersegurança do Leviatã ===",
            f"Fonte: {summary['source']} ({summary['license']})",
            f"Catálogo: {summary['total']} entradas | defensivas: {summary['defensiva']} | escopo autorizado: {summary['escopo_autorizado']} | restritas: {summary['restrita']}",
            f"Consulta: {topic}",
        ]
        if not result["matches"]:
            lines.append("Nenhuma referência correspondente encontrada no catálogo local.")
        else:
            lines.append("Referências encontradas:")
            for item in result["matches"]:
                lines.append(f"- [{item['classification'].upper()}] {item['name']}: {item['description']}")
        lines.append(f"Limites: {result['rules']}")
        return "\n".join(lines)
