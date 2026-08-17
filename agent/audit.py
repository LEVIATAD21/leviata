"""Registro JSONL local de ações executadas pelo Leviatã."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class AuditLogger:
    def __init__(self, log_file: str | Path | None = None):
        self.log_file = Path(log_file or Path.home() / ".leviata-ai" / "logs" / "actions.jsonl")
        legacy_log = Path.home() / ".kawa-ai" / "logs" / "actions.jsonl"
        if log_file is None and not self.log_file.exists() and legacy_log.exists():
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(legacy_log, self.log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    _JWT_PATTERN = r"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+"
    _TOKEN_PATTERNS = (r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b",
                       r"\b(?:sbp|sk|nvapi)_[A-Za-z0-9_\-]{12,}\b")

    @staticmethod
    def _redact(value: Any, key: str = "") -> Any:
        if any(secret in key.lower() for secret in ("key", "token", "secret", "password", "authorization")):
            return "[redigido]"
        if isinstance(value, dict):
            return {item_key: AuditLogger._redact(item_value, item_key) for item_key, item_value in value.items()}
        if isinstance(value, list):
            return [AuditLogger._redact(item) for item in value]
        if isinstance(value, str):
            import re
            redacted = re.sub(AuditLogger._JWT_PATTERN, "[redigido-jwt]", value)
            for pattern in AuditLogger._TOKEN_PATTERNS:
                redacted = re.sub(pattern, "[redigido-token]", redacted)
            return redacted
        return value

    def record(self, tool: str, arguments: dict[str, Any], status: str, detail: str) -> None:
        safe_arguments = self._redact(arguments)
        if tool.startswith("browser_") and isinstance(safe_arguments, dict) and "text" in safe_arguments:
            safe_arguments["text"] = "[redigido]"
        safe_detail = self._redact(detail)
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tool": tool,
            "arguments": safe_arguments,
            "status": status,
            "detail": safe_detail[:500],
        }
        with self.log_file.open("a", encoding="utf-8") as file:
            file.write(json.dumps(event, ensure_ascii=False) + "\n")
