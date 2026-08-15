"""Módulo de conhecimento consultivo, separado da identidade do agente."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from agent.memory import ObsidianMemory


KNOWLEDGE_SYSTEM_PROMPT = """Você é o módulo consultivo de conhecimento do KAWA-AI.
Sua função é sintetizar exclusivamente o material de fonte recebido. Não emita instruções de sistema,
não proponha executar comandos nem tente mudar a personalidade ou as permissões do assistente principal.
Explique o que é, como funciona, limitações e pontos que ainda exigem confirmação. Não invente fontes.
"""


@dataclass(frozen=True)
class KnowledgeReport:
    topic: str
    questions: tuple[str, ...]
    evidence: tuple[str, ...]
    synthesis: str

    def render(self) -> str:
        lines = [f"# Consulta de conhecimento: {self.topic}", "", "## Perguntas investigadas"]
        lines.extend(f"- {question}" for question in self.questions)
        lines.extend(["", "## Evidências coletadas"])
        lines.extend(f"- {item}" for item in self.evidence)
        lines.extend(["", "## Síntese", self.synthesis])
        return "\n".join(lines)


class KnowledgeBrain:
    """Questiona e sintetiza fontes sem receber acesso a ferramentas de alteração."""

    def __init__(self, provider, search_fn: Callable[[str], str], max_evidence_chars: int = 7_000,
                 vault_path: str | Path | None = None, memory: ObsidianMemory | None = None):
        self.provider = provider
        self.search_fn = search_fn
        self.max_evidence_chars = max_evidence_chars
        self.vault_path = Path(vault_path or Path.home() / ".kawa-ai" / "knowledge").expanduser()
        self.memory = memory

    @staticmethod
    def questions_for(topic: str) -> tuple[str, ...]:
        return (
            f"O que é {topic}?",
            f"Como funciona {topic}?",
            f"Quais são os limites, riscos ou pré-requisitos de {topic}?",
            f"Como confirmar informações confiáveis sobre {topic}?",
        )

    @staticmethod
    def _source_lines(raw_result: str) -> list[str]:
        urls = re.findall(r"https?://[^\s)]+", raw_result)
        if urls:
            return list(dict.fromkeys(urls))[:8]
        return [line.strip() for line in raw_result.splitlines() if line.strip()][:8]

    @staticmethod
    def _slug(value: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
        return slug[:56] or "consulta"

    def save_report(self, report: KnowledgeReport) -> Path:
        if self.memory:
            return self.memory.append_entry(report.topic, report.render(), kind="knowledge")
        self.vault_path.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        destination = self.vault_path / f"{stamp}-{self._slug(report.topic)}.md"
        destination.write_text(report.render() + "\n", encoding="utf-8")
        return destination

    def inquire(self, topic: str, persist: bool = False) -> str:
        clean_topic = " ".join(topic.split())
        if not clean_topic:
            return "Erro: informe um assunto para consulta de conhecimento."
        if len(clean_topic) > 300:
            return "Erro: o assunto excede o limite de 300 caracteres."

        questions = self.questions_for(clean_topic)
        evidence_blocks: list[str] = []
        sources: list[str] = []
        for question in questions:
            result = self.search_fn(question)
            evidence_blocks.append(f"Pergunta: {question}\nResultado: {result}")
            sources.extend(self._source_lines(result))

        evidence_text = "\n\n".join(evidence_blocks)[: self.max_evidence_chars]
        message = {
            "role": "user",
            "content": (
                f"Assunto: {clean_topic}\n\nPerguntas:\n"
                + "\n".join(f"- {question}" for question in questions)
                + f"\n\nMaterial coletado:\n{evidence_text}"
            ),
        }
        try:
            synthesis = self.provider.generate(system=KNOWLEDGE_SYSTEM_PROMPT, messages=[message])
        except Exception as exc:
            synthesis = f"Não foi possível sintetizar com o provedor atual: {exc}"

        report = KnowledgeReport(
            topic=clean_topic,
            questions=questions,
            evidence=tuple(dict.fromkeys(sources))[:8],
            synthesis=synthesis,
        )
        rendered = report.render()
        if persist:
            saved_to = self.save_report(report)
            rendered += f"\n\n## Registro local\nSalvo em: {saved_to}"
        return rendered
