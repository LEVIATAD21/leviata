"""Catálogo consultivo de referências de segurança com classificação de risco.

O módulo apenas indexa metadados e descreve limites de uso. Ele não executa
scripts, payloads, scanners de rede ou técnicas do catálogo de origem.
"""

from __future__ import annotations

import json
import re
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

    def _payload(self) -> dict[str, Any]:
        if not self.index_path.exists():
            return {"total_skills": 0, "skills": []}
        try:
            payload = json.loads(self.index_path.read_text(encoding="utf-8"))
            return payload if isinstance(payload, dict) else {"total_skills": 0, "skills": []}
        except (OSError, json.JSONDecodeError):
            return {"total_skills": 0, "skills": []}

    @classmethod
    def classification(cls, name: str) -> str:
        lowered = name.casefold()
        if lowered.startswith(cls._restricted_prefixes):
            return "restrita"
        if lowered.startswith(cls._scope_prefixes):
            return "escopo_autorizado"
        return "defensiva"

    def summary(self) -> dict[str, int | str]:
        skills = self._payload().get("skills", [])
        counts = {"defensiva": 0, "escopo_autorizado": 0, "restrita": 0}
        for item in skills:
            if isinstance(item, dict):
                counts[self.classification(str(item.get("name", "")))] += 1
        return {
            "source": self.source_url,
            "license": self.license_name,
            "total": len(skills),
            **counts,
        }

    def search(self, topic: str, include_restricted: bool = False, limit: int = 8) -> dict[str, Any]:
        terms = [term for term in re.findall(r"[\w-]+", topic.casefold()) if len(term) > 2]
        matches: list[dict[str, str]] = []
        for item in self._payload().get("skills", []):
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", ""))
            description = str(item.get("description", ""))
            classification = self.classification(name)
            if classification == "restrita" and not include_restricted:
                continue
            haystack = f"{name} {description}".casefold()
            score = sum(term in haystack for term in terms)
            if score:
                matches.append({
                    "name": name,
                    "description": description[:280],
                    "classification": classification,
                    "path": str(item.get("path", "")),
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
            "=== Referências de Cibersegurança do KAWA-AI ===",
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
