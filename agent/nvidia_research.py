"""Consultas consultivas e sequenciais para modelos NVIDIA NIM autorizados."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

from agent.connections import ConnectionStore


class NvidiaResearchError(RuntimeError):
    """Erro seguro sem incluir token, cabeçalhos ou respostas completas do provedor."""


@dataclass(frozen=True)
class ResearchFrame:
    model: str
    response: str


class NvidiaResearch:
    """Faz poucas consultas de leitura e organiza cada resposta como um quadro investigativo."""

    base_url = "https://integrate.api.nvidia.com/v1"

    def __init__(self, connections: ConnectionStore | None = None, http: Any = None):
        self.connections = connections or ConnectionStore()
        self.http = http or requests.Session()

    def _headers(self) -> dict[str, str]:
        token = self.connections.get_token("nvidia")
        if not token:
            raise NvidiaResearchError(
                "Nenhuma chave NVIDIA foi encontrada no cofre local. Use --connection-set-token nvidia sem colocar a chave na linha de comando."
            )
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def list_models(self) -> list[str]:
        try:
            response = self.http.get(f"{self.base_url}/models", headers=self._headers(), timeout=30)
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:
            raise NvidiaResearchError("Não foi possível listar os modelos NVIDIA autorizados.") from exc
        models = [entry.get("id") for entry in payload.get("data", []) if isinstance(entry, dict) and entry.get("id")]
        return sorted(set(models))

    @staticmethod
    def _select_models(available: list[str], requested: list[str] | None, maximum: int) -> list[str]:
        maximum = max(1, min(int(maximum), 4))
        if requested:
            unknown = [model for model in requested if model not in available]
            if unknown:
                raise NvidiaResearchError(f"Modelo(s) não disponível(is) nesta chave: {', '.join(unknown)}")
            return requested[:maximum]
        useful = [model for model in available if any(word in model.lower() for word in ("instruct", "reason", "nemotron", "coder"))]
        return (useful or available)[:maximum]

    def consult(self, question: str, requested_models: list[str] | None = None, maximum: int = 3) -> list[ResearchFrame]:
        question = question.strip()
        if not question:
            raise NvidiaResearchError("A pergunta de pesquisa não pode ficar vazia.")
        if len(question) > 12_000:
            raise NvidiaResearchError("A pergunta ultrapassa 12.000 caracteres. Divida a investigação em partes.")
        models = self._select_models(self.list_models(), requested_models, maximum)
        frames: list[ResearchFrame] = []
        previous = ""
        for index, model in enumerate(models, start=1):
            scope = (
                "Responda como um consultor de pesquisa. Separe fatos, hipóteses, limites e próximos passos. "
                "Não execute ferramentas e não invente fontes."
            )
            if previous:
                scope += f"\nQuadros anteriores resumidos:\n{previous[-4_000:]}\nVerifique e complemente somente o necessário."
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": scope},
                    {"role": "user", "content": f"Quadro {index}/{len(models)} — Pergunta: {question}"},
                ],
                "temperature": 0.2,
                "max_tokens": 1200,
            }
            try:
                response = self.http.post(
                    f"{self.base_url}/chat/completions", headers=self._headers(), json=payload, timeout=90
                )
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"]
            except (requests.RequestException, KeyError, IndexError, TypeError) as exc:
                raise NvidiaResearchError(f"A consulta ao quadro {index} falhou; os quadros anteriores foram preservados localmente.") from exc
            text = str(content).strip()
            frames.append(ResearchFrame(model=model, response=text))
            previous += f"\n[{model}]\n{text}\n"
        return frames

    @staticmethod
    def render(frames: list[ResearchFrame]) -> str:
        parts = ["# Investigação NVIDIA em quadros\n"]
        for index, frame in enumerate(frames, start=1):
            parts.append(f"## Quadro {index} — {frame.model}\n\n{frame.response}\n")
        return "\n".join(parts)
