"""Registro JSONL local de ações executadas pelo KAWA-AI."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class AuditLogger:
    def __init__(self, log_file: str | Path | None = None):
        self.log_file = Path(log_file or Path.home() / ".kawa-ai" / "logs" / "actions.jsonl")
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _redact(value: Any, key: str = "") -> Any:
        if any(secret in key.lower() for secret in ("key", "token", "secret", "password", "authorization")):
            return "[redigido]"
        if isinstance(value, dict):
            return {item_key: AuditLogger._redact(item_value, item_key) for item_key, item_value in value.items()}
        if isinstance(value, list):
            return [AuditLogger._redact(item) for item in value]
        return value

    def record(self, tool: str, arguments: dict[str, Any], status: str, detail: str) -> None:
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tool": tool,
            "arguments": self._redact(arguments),
            "status": status,
            "detail": detail[:500],
        }
        with self.log_file.open("a", encoding="utf-8") as file:
            file.write(json.dumps(event, ensure_ascii=False) + "\n")
