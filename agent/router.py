"""Roteamento leve de tarefas para evitar carregar componentes desnecessários."""

from __future__ import annotations

from enum import Enum


class TaskRoute(str, Enum):
    KNOWLEDGE = "knowledge"
    AGENT = "agent"


class TaskRouter:
    """Classificador determinístico e barato para consultas versus tarefas operacionais."""

    knowledge_markers = (
        "o que é", "o que sao", "o que são", "como funciona", "explique", "me explique",
        "pesquise", "pesquisar", "investigue", "entender", "aprenda", "qual a diferença",
        "quais são", "quais sao", "por que", "porque ", "conceito de",
    )

    operational_markers = (
        "crie ", "edite ", "apague ", "instale ", "execute ", "rode ", "corrija ",
        "faça ", "faca ", "publique ", "envie ", "commit", "teste ",
    )

    def route(self, task: str) -> TaskRoute:
        normalized = " ".join(task.lower().split())
        if any(marker in normalized for marker in self.operational_markers):
            return TaskRoute.AGENT
        if any(marker in normalized for marker in self.knowledge_markers):
            return TaskRoute.KNOWLEDGE
        return TaskRoute.AGENT
