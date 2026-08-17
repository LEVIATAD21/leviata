"""Referências verificadas de segurança de IA, somente para consulta e planejamento.

O módulo descreve ferramentas e frameworks; ele não instala pacotes, não envia
requisições a alvos e não executa sondas, ataques ou coleta de dados.
"""

from __future__ import annotations

import re
from typing import Any


class AISecurityReferenceCatalog:
    """Catálogo curado de fontes de segurança de IA com limites de aplicação."""

    references = (
        {
            "name": "MITRE ATLAS",
            "url": "https://atlas.mitre.org/",
            "license": "referência pública",
            "classification": "defensiva",
            "topics": "ameaças ai llm agente modelo mitre atlas modelagem mitigação",
            "use": "Mapear ameaças, contramedidas e cobertura de controles sem executar técnicas adversariais.",
        },
        {
            "name": "OWASP GenAI LLM Top 10 2026",
            "url": "https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/",
            "license": "referência pública",
            "classification": "defensiva",
            "topics": "owasp llm genai prompt injection saída insegura agência cadeia suprimentos",
            "use": "Aplicar checklist de hardening a aplicações LLM, RAG, agentes e integrações.",
        },
        {
            "name": "NVIDIA garak",
            "url": "https://github.com/NVIDIA/garak",
            "license": "Apache-2.0",
            "classification": "escopo_autorizado",
            "topics": "garak llm prompt injection avaliação red team alucinação vazamento",
            "use": "Planejar avaliação de modelos locais ou alvos formalmente autorizados, com conjuntos de sondas defensivas.",
        },
        {
            "name": "Microsoft PyRIT",
            "url": "https://github.com/microsoft/PyRIT",
            "license": "MIT",
            "classification": "escopo_autorizado",
            "topics": "pyrit risco llm genai avaliação segurança red team",
            "use": "Estruturar identificação, documentação e mitigação de riscos em sistemas de IA autorizados.",
        },
        {
            "name": "Promptfoo",
            "url": "https://github.com/promptfoo/promptfoo",
            "license": "MIT",
            "classification": "escopo_autorizado",
            "topics": "promptfoo prompt rag agente avaliação segurança teste cicd",
            "use": "Definir avaliações locais e regressões de segurança para prompts, agentes e fluxos RAG.",
        },
        {
            "name": "Adversarial Robustness Toolbox",
            "url": "https://github.com/Trusted-AI/adversarial-robustness-toolbox",
            "license": "MIT",
            "classification": "laboratorio_autorizado",
            "topics": "art robustez modelo adversarial evasão envenenamento extração inferência defesa",
            "use": "Avaliar e melhorar a robustez de modelos próprios em laboratório controlado e documentado.",
        },
        {
            "name": "CleverHans",
            "url": "https://github.com/cleverhans-lab/cleverhans",
            "license": "MIT",
            "classification": "laboratorio_autorizado",
            "topics": "cleverhans robustez exemplos adversariais benchmark visão machine learning defesa",
            "use": "Realizar benchmark de robustez e validar defesas em modelos próprios de ML.",
        },
        {
            "name": "Picklescan",
            "url": "https://github.com/mmaitre314/picklescan",
            "license": "MIT",
            "classification": "defensiva",
            "topics": "picklescan pickle pytorch modelo artefato serialização supply chain malicioso",
            "use": "Inspecionar preventivamente checkpoints e artefatos Pickle antes de carregamento local.",
        },
    )

    def summary(self) -> dict[str, int]:
        return {
            "total": len(self.references),
            "defensiva": sum(item["classification"] == "defensiva" for item in self.references),
            "escopo_autorizado": sum(item["classification"] == "escopo_autorizado" for item in self.references),
            "laboratorio_autorizado": sum(item["classification"] == "laboratorio_autorizado" for item in self.references),
        }

    def search(self, topic: str, limit: int = 8) -> dict[str, Any]:
        terms = [term for term in re.findall(r"[\w-]+", topic.casefold()) if len(term) > 2]
        matches: list[dict[str, str]] = []
        for reference in self.references:
            haystack = f"{reference['name']} {reference['topics']} {reference['use']}".casefold()
            score = sum(term in haystack for term in terms)
            if score:
                matches.append({**reference, "score": str(score)})
        matches.sort(key=lambda item: (-int(item["score"]), item["name"]))
        return {"topic": topic, "summary": self.summary(), "matches": matches[:max(1, min(limit, 16))]}

    def render(self, topic: str, limit: int = 8) -> str:
        result = self.search(topic, limit)
        summary = result["summary"]
        lines = [
            "=== Referências Verificadas de Segurança de IA ===",
            f"Catálogo: {summary['total']} fontes | defensivas: {summary['defensiva']} | escopo autorizado: {summary['escopo_autorizado']} | laboratório autorizado: {summary['laboratorio_autorizado']}",
            f"Consulta: {topic}",
        ]
        if not result["matches"]:
            lines.append("Nenhuma referência específica encontrada; use OWASP GenAI e MITRE ATLAS como ponto de partida defensivo.")
        for item in result["matches"]:
            lines.append(f"- [{item['classification'].upper()}] {item['name']}: {item['use']} Fonte: {item['url']} ({item['license']}).")
        lines.append("Limites: catálogo somente leitura; não instala ferramentas nem executa sondas. Itens de escopo ou laboratório exigem autorização formal, alvo controlado e registro de evidências.")
        return "\n".join(lines)
