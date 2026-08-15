"""Auditoria local de qualidade e segurança defensiva para projetos autorizados."""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable


class QualityError(RuntimeError):
    """Erro localizado de auditoria sem revelar conteúdo sensível do projeto."""


class QualityToolkit:
    """Executa verificações estáticas somente dentro do diretório de trabalho."""

    available_tools = {"ruff", "bandit", "semgrep"}

    def __init__(self, workspace: str | Path, runner: Callable | None = None, finder: Callable | None = None):
        self.workspace = Path(workspace).expanduser().resolve()
        self.runner = runner or subprocess.run
        self.finder = finder or shutil.which

    def _target(self, raw_path: str | None) -> Path:
        candidate = Path(raw_path or self.workspace).expanduser()
        if not candidate.is_absolute():
            candidate = self.workspace / candidate
        target = candidate.resolve()
        try:
            target.relative_to(self.workspace)
        except ValueError as exc:
            raise QualityError("A auditoria só pode analisar arquivos dentro do diretório de trabalho.") from exc
        if not target.exists():
            raise QualityError(f"Diretório ou arquivo não encontrado: {target}")
        return target

    def _output_file(self) -> Path:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        directory = self.workspace / "kawa-quality"
        directory.mkdir(parents=True, exist_ok=True)
        return directory / f"audit-{stamp}.json"

    @staticmethod
    def _commands(tool: str, target: Path) -> list[str]:
        if tool == "ruff":
            return ["ruff", "check", str(target)]
        if tool == "bandit":
            return ["bandit", "-r", str(target), "-f", "json"]
        if tool == "semgrep":
            return ["semgrep", "scan", "--config", "p/security-audit", "--metrics", "off", str(target)]
        raise QualityError(f"Ferramenta não suportada: {tool}")

    def audit(self, target_path: str | None = None, tools: Iterable[str] | None = None) -> str:
        target = self._target(target_path)
        selected = [item.strip().lower() for item in (tools or ["ruff", "bandit", "semgrep"]) if item.strip()]
        unsupported = set(selected) - self.available_tools
        if unsupported:
            raise QualityError(f"Ferramentas inválidas: {', '.join(sorted(unsupported))}")

        findings: list[dict[str, object]] = []
        for tool in selected:
            executable = self.finder(tool)
            if not executable:
                findings.append({"tool": tool, "status": "not_installed", "message": f"{tool} não está instalado."})
                continue
            command = self._commands(tool, target)
            try:
                result = self.runner(command, capture_output=True, text=True, timeout=600, cwd=str(self.workspace))
                output = ((result.stdout or "") + ("\n" + result.stderr if result.stderr else "")).strip()
                findings.append({
                    "tool": tool,
                    "status": "ok" if result.returncode == 0 else "findings",
                    "returncode": result.returncode,
                    "output": output[:12_000],
                })
            except subprocess.TimeoutExpired:
                findings.append({"tool": tool, "status": "timeout", "message": "A auditoria excedeu 10 minutos."})
            except OSError as exc:
                findings.append({"tool": tool, "status": "error", "message": str(exc)[:500]})

        report = {
            "target": str(target),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "tools": findings,
        }
        output_file = self._output_file()
        output_file.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        summary = ", ".join(f"{item['tool']}: {item['status']}" for item in findings)
        return f"Auditoria concluída em {target}. {summary}. Relatório: {output_file}"
