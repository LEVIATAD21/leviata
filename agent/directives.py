"""Leitor técnico do único arquivo de diretrizes do Leviatã."""

from __future__ import annotations

from pathlib import Path


DIRETRIZES_PATH = Path(__file__).resolve().parent.parent / "DIRETRIZES.md"


def load_directives() -> str:
    """Lê DIRETRIZES.md a cada solicitação sem adicionar regras próprias."""
    try:
        return DIRETRIZES_PATH.read_text(encoding="utf-8")
    except OSError:
        return ""
