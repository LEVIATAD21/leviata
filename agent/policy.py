"""Política local e explícita para as ferramentas do KAWA-AI."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class PolicyMode(str, Enum):
    OBSERVE = "observe"
    ASK = "ask"
    WORKSPACE = "workspace"
    PROACTIVE = "proactive"


class Decision(str, Enum):
    ALLOW = "allow"
    ASK = "ask"
    DENY = "deny"


@dataclass(frozen=True)
class PolicyResult:
    decision: Decision
    reason: str


class ToolPolicy:
    """Classifica chamadas de ferramenta antes de elas alcançarem o sistema."""

    _high_impact_shell = re.compile(
        r"(^|\s)(sudo|su|rm\s+-[a-z]*r|dd\s|mkfs|shutdown|reboot|poweroff|"
        r"useradd|userdel|chmod\s+777|chown\s|curl[^\n]*\|\s*(ba)?sh|"
        r"wget[^\n]*\|\s*(ba)?sh|git\s+push|pip\s+install|apt(?:-get)?\s+install)",
        re.IGNORECASE,
    )

    def __init__(self, mode: str = "ask", workspace: str | Path | None = None):
        try:
            self.mode = PolicyMode(mode)
        except ValueError as exc:
            raise ValueError("Modo de política inválido: use observe, ask, workspace ou proactive.") from exc
        self.workspace = Path(workspace or os.getcwd()).expanduser().resolve()

    _sensitive_names = re.compile(
        r"(^|/)(\.bashrc|\.bash_profile|\.profile|\.zshrc|\.ssh(/|$)|authorized_keys|"
        r"crontab|sudoers|shadow|passwd|hosts|fstab|\.[\w-]+rc|env|\.env|\.kawa-ai(/|$))",
        re.IGNORECASE,
    )

    def _sensitive_path(self, raw_path: str) -> bool:
        candidate = Path(raw_path).expanduser()
        return bool(self._sensitive_names.search(str(candidate)))

    def _inside_workspace(self, raw_path: str) -> bool:
        candidate = Path(raw_path).expanduser()
        if not candidate.is_absolute():
            candidate = self.workspace / candidate
        try:
            candidate.resolve(strict=False).relative_to(self.workspace)
            return True
        except ValueError:
            return False

    def decide(self, tool_name: str, tool_input: dict[str, Any]) -> PolicyResult:
        if tool_name in {"web_search", "web_fetch", "read_file", "knowledge_inquiry", "browser_read", "browser_navigate", "browser_close"}:
            return PolicyResult(Decision.ALLOW, "Consulta ou leitura permitida.")

        if tool_name in {"browser_click", "browser_type"}:
            if self.mode is PolicyMode.OBSERVE:
                return PolicyResult(Decision.DENY, "O modo observe bloqueia interações no navegador.")
            return PolicyResult(Decision.ASK, "Interação no navegador pode alterar estado ou enviar dados e requer confirmação.")

        if tool_name in {"media_extract_frames", "media_transcribe"}:
            if self.mode is PolicyMode.OBSERVE:
                return PolicyResult(Decision.DENY, "O modo observe bloqueia processamento local de mídia.")
            if self.mode is PolicyMode.PROACTIVE:
                return PolicyResult(Decision.ALLOW, "Processamento local de mídia permitido no modo proativo.")
            return PolicyResult(Decision.ASK, "Processamento de mídia pode consumir CPU e espaço em disco e requer confirmação.")

        if tool_name == "quality_audit":
            if self.mode is PolicyMode.OBSERVE:
                return PolicyResult(Decision.DENY, "O modo observe bloqueia auditorias locais.")
            if self.mode is PolicyMode.PROACTIVE:
                return PolicyResult(Decision.ALLOW, "Auditoria estática local permitida no modo proativo.")
            return PolicyResult(Decision.ASK, "A auditoria pode consumir CPU e requer confirmação neste modo.")

        if tool_name == "design_brief":
            if self.mode is PolicyMode.OBSERVE:
                return PolicyResult(Decision.DENY, "O modo observe bloqueia criação de artefatos de design.")
            if self.mode is PolicyMode.PROACTIVE:
                return PolicyResult(Decision.ALLOW, "Brief de design local permitido no modo proativo.")
            return PolicyResult(Decision.ASK, "A criação de arquivos de design requer confirmação neste modo.")

        if tool_name in {"ethical_pentest", "adversary_simulate"}:
            if self.mode is PolicyMode.OBSERVE:
                return PolicyResult(Decision.DENY, "O modo observe bloqueia simulação de adversário e pentest.")
            if self.mode is PolicyMode.PROACTIVE:
                return PolicyResult(Decision.ALLOW, "Simulação e pentest ético permitidos no modo proativo.")
            return PolicyResult(Decision.ASK, "A simulação de adversário requer confirmação neste modo.")

        if tool_name == "write_file":
            path = str(tool_input.get("path", ""))
            if not path or not self._inside_workspace(path):
                return PolicyResult(Decision.DENY, "A escrita precisa permanecer dentro do diretório de trabalho.")
            if self._sensitive_path(path):
                return PolicyResult(Decision.DENY, "Arquivos de sistema ou credenciais não podem ser alterados (ex.: .bashrc, .ssh, /etc, crontab).")
            if self.mode is PolicyMode.OBSERVE:
                return PolicyResult(Decision.DENY, "O modo observe bloqueia escrita de arquivos.")
            if self.mode is PolicyMode.ASK:
                return PolicyResult(Decision.ASK, "A escrita de arquivo requer confirmação.")
            return PolicyResult(Decision.ALLOW, "Escrita limitada ao diretório de trabalho.")

        if tool_name == "shell":
            command = str(tool_input.get("command", "")).strip()
            if not command:
                return PolicyResult(Decision.DENY, "Comando vazio.")
            if self.mode is PolicyMode.OBSERVE:
                return PolicyResult(Decision.DENY, "O modo observe bloqueia comandos de terminal.")
            if self._high_impact_shell.search(command):
                return PolicyResult(Decision.ASK, "Comando de alto impacto requer confirmação.")
            if self.mode is PolicyMode.ASK:
                return PolicyResult(Decision.ASK, "O modo ask confirma comandos de terminal.")
            return PolicyResult(Decision.ALLOW, "Comando local rotineiro permitido no modo proativo/workspace.")

        return PolicyResult(Decision.DENY, f"Ferramenta não reconhecida pela política: {tool_name}.")
