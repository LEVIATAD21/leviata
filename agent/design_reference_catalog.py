"""Referências verificadas de design para consulta local e planejamento original."""

from __future__ import annotations

import re
from typing import Any


class DesignReferenceCatalog:
    """Catálogo de princípios de UX e design; não reproduz identidades de terceiros."""

    references = (
        {
            "name": "Awesome Design",
            "url": "https://github.com/gztchan/awesome-design",
            "license": "índice comunitário",
            "topics": "cor tipografia ícones prototipação design visual interface",
            "use": "Encontrar referências de cor, tipografia, iconografia, prototipação e testes, validando a licença de cada ativo separadamente.",
        },
        {
            "name": "Awesome UX",
            "url": "https://github.com/uxreview/awesome-ux",
            "license": "índice comunitário",
            "topics": "ux jornada usuário pesquisa usabilidade wireframe fluxo acessibilidade",
            "use": "Estruturar descoberta, jornadas, fluxos, testes de usabilidade e critérios de acessibilidade.",
        },
        {
            "name": "Awesome DESIGN.md",
            "url": "https://github.com/VoltAgent/awesome-design-md",
            "license": "MIT",
            "topics": "design system tokens componentes responsividade motion design markdown agente",
            "use": "Criar um contrato de design original em Markdown com tokens, estados de componentes, responsividade e regras de movimento.",
        },
        {
            "name": "Awesome UI",
            "url": "https://github.com/kevindeasis/awesome-ui",
            "license": "MIT",
            "topics": "ui interface acessibilidade componentes bibliotecas animação layout",
            "use": "Consultar recursos complementares para composição de interface, componentes e acessibilidade.",
        },
    )

    def search(self, topic: str, limit: int = 8) -> dict[str, Any]:
        terms = [term for term in re.findall(r"[\w-]+", topic.casefold()) if len(term) > 2]
        matches = []
        for reference in self.references:
            haystack = f"{reference['name']} {reference['topics']} {reference['use']}".casefold()
            score = sum(term in haystack for term in terms)
            if score:
                matches.append({**reference, "score": str(score)})
        matches.sort(key=lambda item: (-int(item["score"]), item["name"]))
        return {"topic": topic, "total": len(self.references), "matches": matches[:max(1, min(limit, 12))]}

    def render(self, topic: str, limit: int = 8) -> str:
        result = self.search(topic, limit)
        lines = ["=== Referências Verificadas de Design ===", f"Consulta: {topic}"]
        if not result["matches"]:
            lines.append("Use um brief original com hierarquia, contraste, tokens semânticos, estados, responsividade e movimento reduzido.")
        for item in result["matches"]:
            lines.append(f"- {item['name']}: {item['use']} Fonte: {item['url']} ({item['license']}).")
        lines.append("Limite: use princípios e processos; não copie identidade visual, ativos, interface ou conteúdo de terceiros.")
        return "\n".join(lines)
