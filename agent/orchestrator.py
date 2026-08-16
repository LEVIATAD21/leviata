"""Orquestração ponta a ponta de tarefas para o KAWA-AI."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


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
        plan = "\n".join(f"  {idx}. {step.skill}: {step.purpose}" for idx, step in enumerate(self.steps, 1))
        record = f"\nRegistro local: {self.record_path}" if self.record_path else ""
        return f"=== Fluxo automático KAWA-AI ===\nSkills selecionadas:\n{plan}\n\nResultado:\n{self.answer}{record}"


class TaskOrchestrator:
    """Planeja e acompanha tarefas sem exigir que o usuário chame skills manualmente.

    A seleção é determinística e explicável. A execução continua submetida à política
    de ferramentas do agente, ao workspace e aos limites de iteração já existentes.
    """

    _RULES: tuple[tuple[tuple[str, ...], WorkflowStep], ...] = (
        (("site", "website", "landing", "interface", "frontend", "app", "aplicativo", "dashboard"),
         WorkflowStep("design_brief", "definir arquitetura visual e requisitos antes da implementação")),
        (("código", "codigo", "python", "typescript", "javascript", "bug", "refator", "teste", "api", "backend"),
         WorkflowStep("quality_audit", "revisar qualidade, dependências e riscos estáticos do código")),
        (("segurança", "seguranca", "pentest", "vulnerabilidade", "owasp", "hardening", "audit"),
         WorkflowStep("ethical_pentest", "validar apenas o workspace autorizado com evidências e reteste")),
        (("ameaça", "ameaca", "mitre", "adversário", "adversario", "threat model"),
         WorkflowStep("adversary_simulate", "modelar ameaças defensivas e priorizar hardening preventivo")),
        (("vídeo", "video", "áudio", "audio", "transcri", "frame", "quadro", "mídia", "midia"),
         WorkflowStep("media_processing", "inspecionar mídia local por quadros ou transcrição sob política")),
        (("pesquise", "pesquisa", "investigue", "compare", "explique", "estude", "aprenda"),
         WorkflowStep("knowledge_inquiry", "investigar fontes, separar fatos de hipóteses e sintetizar contexto")),
        (("supabase", "banco", "memória", "memoria", "conhecimento", "lições", "licoes"),
         WorkflowStep("knowledge_memory", "recuperar e registrar apenas resultados aprovados e não sensíveis")),
    )

    _BASE_STEPS = (
        WorkflowStep("task_planning", "entender o objetivo, o workspace e o resultado esperado"),
        WorkflowStep("agent_execution", "selecionar ferramentas registradas e executar etapas compatíveis"),
        WorkflowStep("validation", "verificar resultado, evidências e próximos passos antes de encerrar"),
        WorkflowStep("lesson_record", "registrar contexto e resultado em memória local de forma sanitizada"),
    )

    def __init__(self, workspace: str | Path, record_dir: str | Path | None = None):
        self.workspace = Path(workspace).expanduser().resolve()
        self.record_dir = Path(record_dir).expanduser().resolve() if record_dir else self.workspace / "kawa-workflows"

    def plan(self, task: str) -> list[WorkflowStep]:
        normalized = task.lower()
        selected: list[WorkflowStep] = [self._BASE_STEPS[0]]
        for keywords, step in self._RULES:
            if any(re.search(rf"\b{re.escape(keyword)}", normalized) for keyword in keywords):
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
            "Execute esta tarefa de ponta a ponta. Selecione e use automaticamente as ferramentas "
            "registradas que forem necessárias; não espere o usuário pedir cada skill. Respeite a política "
            "local, o workspace e as confirmações obrigatórias. Antes de encerrar, valide o que for possível, "
            "relate evidências, limitações concretas e próximos passos.\n\n"
            f"Plano de capacidades pré-selecionado:\n{plan_text}\n\n"
            f"Pedido do usuário:\n{task}"
        )
        answer = agent.run(enriched_task)
        record = self._record(task, steps, answer)
        return WorkflowResult(task=task, steps=steps, answer=answer, record_path=record)
