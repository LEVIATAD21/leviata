"""Carregador técnico do único arquivo editável de diretrizes do Leviatã."""

from __future__ import annotations

from pathlib import Path


DIRETRIZES_PATH = Path(__file__).resolve().parent.parent / "DIRETRIZES.md"


def load_behavioral_directives() -> str:
    """Lê DIRETRIZES.md a cada solicitação, sem manter uma segunda fonte de regras."""
    try:
        return DIRETRIZES_PATH.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def append_directives(technical_contract: str) -> str:
    """Anexa ao contrato técnico somente o conteúdo do arquivo principal."""
    directives = load_behavioral_directives()
    if not directives:
        return technical_contract
    return f"{technical_contract.rstrip()}\n\n# DIRETRIZES ATIVAS (DIRETRIZES.md)\n{directives}\n"
