"""Conexões locais persistentes, com metadados separados dos segredos."""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ConnectionError(RuntimeError):
    """Falha segura ao gerenciar uma conexão local."""


class ConnectionStore:
    """Guarda tokens no cofre do sistema e somente metadados em arquivo local privado."""

    keyring_service = "KAWA-AI"

    def __init__(self, base_dir: str | Path | None = None, credential_backend=None):
        self.base_dir = Path(base_dir or Path.home() / ".kawa-ai").expanduser()
        self.metadata_path = self.base_dir / "connections.json"
        self.profiles_dir = self.base_dir / "browser-profiles"
        self._credential_backend = credential_backend

    @staticmethod
    def normalize_service(service: str) -> str:
        normalized = re.sub(r"[^a-z0-9_-]+", "-", service.strip().lower()).strip("-")
        if not normalized or len(normalized) > 64:
            raise ConnectionError("Nome de serviço inválido. Use até 64 caracteres: letras, números, _ ou -.")
        return normalized

    def _keyring(self):
        if self._credential_backend is not None:
            return self._credential_backend
        try:
            import keyring
        except ImportError as exc:
            raise ConnectionError(
                "O cofre de credenciais não está disponível. Reinstale as dependências do KAWA-AI."
            ) from exc
        return keyring

    def _read_metadata(self) -> dict[str, Any]:
        if not self.metadata_path.exists():
            return {"schema_version": 1, "connections": {}}
        try:
            data = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ConnectionError("O arquivo de metadados de conexões está inválido.") from exc
        if not isinstance(data.get("connections"), dict):
            raise ConnectionError("O arquivo de metadados de conexões tem formato inválido.")
        return data

    def _write_metadata(self, data: dict[str, Any]) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        temporary = self.metadata_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        try:
            temporary.chmod(0o600)
        except OSError:
            pass
        temporary.replace(self.metadata_path)

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def profile_path(self, service: str) -> Path:
        name = self.normalize_service(service)
        return self.profiles_dir / name

    def list_connections(self) -> list[dict[str, Any]]:
        records = self._read_metadata()["connections"]
        return [
            {"service": name, **metadata}
            for name, metadata in sorted(records.items())
        ]

    def set_token(self, service: str, token: str, scopes: list[str] | None = None) -> None:
        name = self.normalize_service(service)
        if not token.strip():
            raise ConnectionError("Token vazio não pode ser salvo.")
        try:
            self._keyring().set_password(self.keyring_service, name, token)
        except Exception as exc:
            raise ConnectionError(
                "Não foi possível gravar o token no cofre do sistema. Verifique se o chaveiro do Linux está desbloqueado."
            ) from exc
        data = self._read_metadata()
        current = data["connections"].get(name, {})
        data["connections"][name] = {
            **current,
            "kind": "token",
            "scopes": sorted(set(scopes or [])),
            "updated_at": self._now(),
        }
        data["connections"][name].setdefault("created_at", self._now())
        self._write_metadata(data)

    def register_browser_profile(self, service: str) -> Path:
        name = self.normalize_service(service)
        profile = self.profile_path(name)
        profile.mkdir(parents=True, exist_ok=True)
        data = self._read_metadata()
        current = data["connections"].get(name, {})
        data["connections"][name] = {
            **current,
            "kind": "browser_profile",
            "profile_path": str(profile),
            "updated_at": self._now(),
        }
        data["connections"][name].setdefault("created_at", self._now())
        self._write_metadata(data)
        return profile

    def remove(self, service: str) -> bool:
        name = self.normalize_service(service)
        data = self._read_metadata()
        metadata = data["connections"].pop(name, None)
        if not metadata:
            return False
        try:
            self._keyring().delete_password(self.keyring_service, name)
        except Exception:
            pass
        profile = self.profile_path(name)
        if profile.exists():
            shutil.rmtree(profile)
        self._write_metadata(data)
        return True
