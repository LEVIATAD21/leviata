"""Base de conhecimento consultiva de segurança web e cibersegurança.

O módulo apenas indexa e apresenta conhecimento curado para consulta. Ele não
executa payloads, scanners de rede, exploração ou qualquer técnica ofensiva.
Cada entrada traz classificação de risco, indicadores de detecção e medidas de
endurecimento, com enquadramento defensivo e de escopo autorizado — em linha
com o catálogo de referências e o pentest ético já existentes no Leviatã.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any


class WebSecurityKnowledgeBase:
    """Pesquisa conhecimento curado de segurança web/cibernética por tópico.

    A base separa conhecimento estritamente defensivo de técnicas que só podem
    ser aplicadas sob autorização formal. Ela responde perguntas, orienta
    detecção e endurecimento, mas não converte nenhuma entrada em instrução
    operacional executável.
    """

    valid_classifications = ("defensiva", "escopo_autorizado", "laboratorio_autorizado")

    def __init__(self, data_path: str | Path | None = None):
        self.data_path = Path(data_path) if data_path else Path(__file__).with_name("data") / "web_security_knowledge.json"

    @classmethod
    @lru_cache(maxsize=8)
    def _load(cls, raw_path: str, modified_ns: int) -> tuple[tuple[dict[str, Any], ...], dict[str, int], tuple[tuple[str, int], ...]]:
        """Carrega e normaliza a base uma única vez por versão do arquivo."""
        try:
            payload = json.loads(Path(raw_path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            payload = {"entries": []}
        raw_entries = payload.get("entries", []) if isinstance(payload, dict) else []
        counts = {classification: 0 for classification in cls.valid_classifications}
        category_counts: dict[str, int] = {}
        entries: list[dict[str, Any]] = []
        for item in raw_entries:
            if not isinstance(item, dict):
                continue
            classification = str(item.get("classification", "defensiva"))
            if classification not in counts:
                classification = "defensiva"
            counts[classification] += 1
            category = str(item.get("category", "Geral"))
            category_counts[category] = category_counts.get(category, 0) + 1
            references = item.get("references", [])
            references = tuple(str(reference) for reference in references) if isinstance(references, list) else ()
            fields = ("name", "slug", "category", "topics", "summary", "how_it_works", "detection", "hardening")
            haystack = " ".join(str(item.get(field, "")) for field in fields).casefold()
            entries.append({
                "name": str(item.get("name", "")),
                "slug": str(item.get("slug", "")),
                "category": category,
                "classification": classification,
                "topics": str(item.get("topics", "")),
                "summary": str(item.get("summary", "")),
                "how_it_works": str(item.get("how_it_works", "")),
                "detection": str(item.get("detection", "")),
                "hardening": str(item.get("hardening", "")),
                "references": references,
                "haystack": haystack,
            })
        ordered_categories = tuple(sorted(category_counts.items(), key=lambda pair: (-pair[1], pair[0])))
        return tuple(entries), counts, ordered_categories

    def _index(self) -> tuple[tuple[dict[str, Any], ...], dict[str, int], tuple[tuple[str, int], ...]]:
        try:
            modified_ns = self.data_path.stat().st_mtime_ns
        except OSError:
            return (), {classification: 0 for classification in self.valid_classifications}, ()
        return self._load(str(self.data_path.resolve()), modified_ns)

    def summary(self) -> dict[str, Any]:
        entries, counts, categories = self._index()
        return {
            "total": len(entries),
            "categorias": len(categories),
            **counts,
        }

    def categories(self) -> list[dict[str, Any]]:
        _, _, categories = self._index()
        return [{"categoria": name, "entradas": count} for name, count in categories]

    def search(self, topic: str, limit: int = 6) -> dict[str, Any]:
        terms = [term for term in re.findall(r"[\w-]+", str(topic).casefold()) if len(term) > 2]
        entries, _, _ = self._index()
        matches: list[dict[str, Any]] = []
        for entry in entries:
            haystack = entry["haystack"]
            score = sum(haystack.count(term) for term in terms) if terms else 0
            if score:
                item = {key: value for key, value in entry.items() if key != "haystack"}
                item["score"] = score
                matches.append(item)
        matches.sort(key=lambda item: (-int(item["score"]), item["name"]))
        return {"topic": str(topic), "summary": self.summary(), "matches": matches[: max(1, min(int(limit or 6), 20))]}

    def render(self, topic: str = "", limit: int = 6) -> str:
        summary = self.summary()
        header = [
            "=== Base de Conhecimento de Segurança Web e Cibernética do Leviatã ===",
            (f"Base: {summary['total']} entradas em {summary['categorias']} categorias | "
             f"defensivas: {summary['defensiva']} | escopo autorizado: {summary['escopo_autorizado']} | "
             f"laboratório autorizado: {summary['laboratorio_autorizado']}"),
        ]
        clean_topic = " ".join(str(topic).split())
        if not clean_topic or clean_topic.casefold() in {"tudo", "overview", "geral", "todos", "indice", "índice", "catalogo", "catálogo"}:
            header.append("Categorias disponíveis (consulte por tópico para aprofundar):")
            for entry in self.categories():
                header.append(f"- {entry['categoria']}: {entry['entradas']} entradas")
            header.append("Limites: base somente leitura; orienta detecção e endurecimento. "
                          "Itens de escopo/laboratório exigem autorização formal, alvo controlado e registro de evidências.")
            return "\n".join(header)

        result = self.search(clean_topic, limit)
        header.append(f"Consulta: {clean_topic}")
        if not result["matches"]:
            header.append("Nenhuma entrada específica encontrada; refine o tópico ou consulte as categorias com o tópico 'índice'.")
            return "\n".join(header)
        for item in result["matches"]:
            references = ", ".join(item["references"][:5])
            header.extend([
                "",
                f"### [{item['classification'].upper()}] {item['name']} — {item['category']}",
                f"O que é: {item['summary']}",
                f"Como funciona: {item['how_it_works']}",
                f"Detecção: {item['detection']}",
                f"Endurecimento: {item['hardening']}",
                f"Referências: {references}" if references else "Referências: —",
            ])
        header.append("")
        header.append("Limites: base somente leitura; não executa payloads nem sondas. "
                      "Itens de escopo/laboratório exigem autorização formal, alvo controlado e registro de evidências.")
        return "\n".join(header)
