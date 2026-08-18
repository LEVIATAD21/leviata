"""Orquestração ponta a ponta de tarefas para o Leviatã."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from agent.language import routing_text


@dataclass(frozen=True)
class WorkflowStep:
    """Uma etapa explicável selecionada pelo orquestrador."""

    skill: str
    purpose: str


@dataclass
class WorkflowResult:
    """Resultado auditável de uma execução ponta a ponta."""

    task: str
    steps: list[WorkflowStep]
    answer: str
    record_path: Path | None = None

    def render(self) -> str:
        # A interface mantém a conversa limpa; o plano completo fica no JSON local.
        record = f"\nRegistro local: {self.record_path}" if self.record_path else ""
        return f"{self.answer}{record}"


class TaskOrchestrator:
    """Planeja e acompanha tarefas sem exigir que o usuário chame skills manualmente.

    A seleção é determinística e explicável. A execução continua submetida à política
    de ferramentas do agente, ao workspace e aos limites de iteração já existentes.
    """

    _RULES: tuple[tuple[tuple[str, ...], WorkflowStep], ...] = (
        (("site", "website", "landing", "interface", "frontend", "app", "aplicativo", "dashboard"),
         WorkflowStep("design_brief", "definir arquitetura visual e requisitos antes da implementação")),
        (("site", "website", "landing", "interface", "frontend", "app", "aplicativo", "dashboard", "ux", "ui", "acessibilidade", "design system"),
         WorkflowStep("design_reference", "consultar referências de UX e design systems")),
        (("site", "website", "landing", "interface", "frontend", "app", "aplicativo", "dashboard"),
         WorkflowStep("secure_site_cycle", "executar o ciclo técnico de site local")),
        (("código", "codigo", "python", "typescript", "javascript", "bug", "refator", "teste", "api", "backend"),
         WorkflowStep("quality_audit", "revisar qualidade, dependências e riscos estáticos do código")),
        (("llm", "rag", "prompt", "genai", "segurança de ia", "seguranca de ia", "agente de ia", "modelo de ia", "machine learning", "aprendizado de máquina", "aprendizado de maquina", "adversarial"),
         WorkflowStep("ai_security_reference", "consultar referências verificadas de segurança de IA")),
        (("segurança", "seguranca", "pentest", "vulnerabilidade", "owasp", "hardening", "audit", "mitre"),
         WorkflowStep("cybersecurity_reference", "consultar referências classificadas de cibersegurança")),
        (("segurança", "seguranca", "pentest", "vulnerabilidade", "owasp", "hardening", "audit"),
         WorkflowStep("ethical_pentest", "executar a auditoria estática do escopo configurado")),
        (("ameaça", "ameaca", "mitre", "adversário", "adversario", "threat model"),
         WorkflowStep("adversary_simulate", "executar modelagem de ameaças e hardening")),
        (("vídeo", "video", "áudio", "audio", "transcri", "frame", "quadro", "mídia", "midia"),
         WorkflowStep("media_processing", "processar mídia por quadros ou transcrição")),
        (("pesquise", "pesquisa", "investigue", "compare", "explique", "estude", "aprenda"),
         WorkflowStep("knowledge_inquiry", "investigar fontes e sintetizar contexto")),
        (("supabase", "banco", "memória", "memoria", "conhecimento", "lições", "licoes"),
         WorkflowStep("knowledge_memory", "recuperar e registrar apenas resultados aprovados e não sensíveis")),
        (("livro", "manual", "documentação", "documentacao", "pdf", "epub", "skill", "skills"),
         WorkflowStep("skill_materialize", "estruturar material local em uma skill consultável")),
    )

    _BASE_STEPS = (
        WorkflowStep("task_planning", "entender o objetivo, o workspace e o resultado esperado"),
        WorkflowStep("agent_execution", "selecionar ferramentas registradas e executar etapas compatíveis"),
        WorkflowStep("validation", "verificar resultado, evidências e próximos passos antes de encerrar"),
        WorkflowStep("lesson_record", "registrar contexto e resultado em memória local de forma sanitizada"),
    )
    _COMPILED_RULES = tuple(
        (tuple(re.compile(rf"\b{re.escape(keyword)}") for keyword in keywords), step)
        for keywords, step in _RULES
    )

    def __init__(self, workspace: str | Path, record_dir: str | Path | None = None):
        self.workspace = Path(workspace).expanduser().resolve()
        self.record_dir = Path(record_dir).expanduser().resolve() if record_dir else self.workspace / "leviata-workflows"

    def plan(self, task: str) -> list[WorkflowStep]:
        normalized = routing_text(task)
        selected: list[WorkflowStep] = [self._BASE_STEPS[0]]
        for patterns, step in self._COMPILED_RULES:
            if any(pattern.search(normalized) for pattern in patterns):
                selected.append(step)
        selected.extend(self._BASE_STEPS[1:])
        unique: list[WorkflowStep] = []
        seen: set[str] = set()
        for step in selected:
            if step.skill not in seen:
                unique.append(step)
                seen.add(step.skill)
        return unique

    def _record(self, task: str, steps: Iterable[WorkflowStep], answer: str) -> Path | None:
        try:
            self.record_dir.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            path = self.record_dir / f"workflow-{stamp}.json"
            payload = {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "task": task[:4_000],
                "skills": [{"name": step.skill, "purpose": step.purpose} for step in steps],
                "result_summary": answer[:8_000],
            }
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            return path
        except OSError:
            return None

    def run(self, task: str, agent) -> WorkflowResult:
        steps = self.plan(task)
        plan_text = "\n".join(f"- {step.skill}: {step.purpose}" for step in steps)
        enriched_task = (
            "<runtime_context>\n"
            f"preselected_capabilities:\n{plan_text}\n"
            "</runtime_context>\n\n"
            f"Pedido do usuário:\n{task}"
        )
        answer = agent.run(enriched_task)
        record = self._record(task, steps, answer)
        return WorkflowResult(task=task, steps=steps, answer=answer, record_path=record)
