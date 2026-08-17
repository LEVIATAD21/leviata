"""Briefs e diagramas locais para orientar design de produtos e interfaces."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path


class DesignError(RuntimeError):
    """Erro seguro ao criar artefatos de design dentro da área de trabalho."""


class DesignToolkit:
    """Cria um brief Markdown e uma arquitetura Mermaid editáveis, sem depender de serviço externo."""

    def __init__(self, workspace: str | Path):
        self.workspace = Path(workspace).expanduser().resolve()

    @staticmethod
    def _slug(text: str) -> str:
        value = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
        return value[:48] or "projeto"

    def create_brief(self, request: str, medium: str = "produto-digital") -> str:
        request = request.strip()
        if not request:
            raise DesignError("Descreva o objetivo do design.")
        target = self.workspace / "kawa-design" / f"{self._slug(request)}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
        target.mkdir(parents=True, exist_ok=False)
        brief = target / "design-brief.md"
        diagram = target / "information-architecture.mmd"
        brief.write_text(
            f"# Brief de design\n\n"
            f"**Pedido:** {request}\n\n"
            f"**Meio:** {medium}\n\n"
            "## Objetivo\n\n"
            "Definir uma experiência clara, acessível e verificável antes de construir ou gerar visuais.\n\n"
            "## Público e contexto\n\n"
            "- Usuário principal: a confirmar na tarefa.\n"
            "- Problema a resolver: extraído do pedido acima.\n"
            "- Restrições: desempenho, acessibilidade, privacidade e linguagem devem ser validados antes da publicação.\n\n"
            "## Hierarquia sugerida\n\n"
            "1. Proposta de valor ou objetivo principal.\n"
            "2. Ação prioritária.\n"
            "3. Conteúdo de apoio e estados de erro/carregamento.\n"
            "4. Próximos passos ou ajuda.\n\n"
            "## Contrato de design local\n\n"
            "- Definir tema e intenção visual originais antes de escolher componentes.\n"
            "- Nomear tokens semânticos para cor, espaçamento, raio, elevação e tipografia; não copiar tokens de marcas externas.\n"
            "- Especificar estados padrão, foco, carregamento, vazio, erro, sucesso e indisponibilidade para toda ação principal.\n"
            "- Definir comportamento responsivo, alvo de toque, navegação por teclado e redução de movimento.\n"
            "- Usar animação somente para reforçar hierarquia e feedback, com transições curtas e interrompíveis.\n\n"
            "## Critérios de aceitação\n\n"
            "- Texto legível e contraste adequado.\n"
            "- Navegação por teclado e rótulos claros.\n"
            "- Sem dados pessoais ou credenciais no visual.\n"
            "- Fluxos externos separados de uma prévia revisável.\n",
            encoding="utf-8",
        )
        diagram.write_text(
            "flowchart TD\n"
            "  A[Objetivo] --> B[Ação principal]\n"
            "  A --> C[Conteúdo de apoio]\n"
            "  B --> D[Confirmação ou resultado]\n"
            "  C --> E[Ajuda e estados alternativos]\n",
            encoding="utf-8",
        )
        return f"Brief criado em: {brief}\nArquitetura Mermaid criada em: {diagram}"
