"""Memória persistente do KAWA-AI em um único cofre Obsidian."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


class ObsidianMemoryError(RuntimeError):
    """Indica uma inconsistência que poderia criar ou perder um diário."""


class ObsidianMemory:
    """Gerencia um diário único, somente por acréscimo, dentro de um cofre Obsidian."""

    folder_name = "KAWA-AI"
    diary_name = "Reasoning Diary.md"
    manifest_name = ".kawa-ai-manifest.json"
    ignored_dirs = {
        ".git", "node_modules", ".cache", ".local", "__pycache__", ".venv",
        "proc", "sys", "dev", "run", "tmp",
    }

    def __init__(self, vault_path: str | Path, context_chars: int = 6_000, backup_count: int = 5):
        self.vault_path = Path(vault_path).expanduser().resolve()
        self.context_chars = max(1_000, min(context_chars, 20_000))
        self.backup_count = max(1, min(backup_count, 10))

    @property
    def folder(self) -> Path:
        return self.vault_path / self.folder_name

    @property
    def diary_path(self) -> Path:
        return self.folder / self.diary_name

    @property
    def manifest_path(self) -> Path:
        return self.folder / self.manifest_name

    @property
    def backup_dir(self) -> Path:
        return self.folder / ".backups"

    @staticmethod
    def _canonical(path: Path) -> str:
        return str(path.expanduser().resolve())

    @classmethod
    def _walk_candidates(cls, root: Path, max_depth: int) -> Iterable[Path]:
        root = root.expanduser()
        if not root.exists() or not root.is_dir():
            return
        try:
            for current, dirs, _ in os.walk(root, topdown=True, followlinks=False):
                current_path = Path(current)
                try:
                    depth = len(current_path.relative_to(root).parts)
                except ValueError:
                    depth = max_depth + 1
                is_vault = ".obsidian" in dirs
                dirs[:] = [
                    name for name in dirs
                    if name != ".obsidian" and name not in cls.ignored_dirs and not name.startswith(".")
                ]
                if depth > max_depth:
                    dirs[:] = []
                    continue
                if is_vault:
                    yield current_path.resolve()
        except PermissionError:
            return

    @classmethod
    def discover_vaults(cls, roots: Iterable[str | Path], max_depth: int = 6) -> list[Path]:
        """Localiza somente pastas .obsidian, sem abrir arquivos das notas."""
        found: dict[str, Path] = {}
        for root in roots:
            for candidate in cls._walk_candidates(Path(root), max_depth) or ():
                found[cls._canonical(candidate)] = candidate
        return [found[key] for key in sorted(found)]

    @staticmethod
    def default_search_roots(home: str | Path | None = None) -> list[Path]:
        home_path = Path(home or Path.home()).expanduser()
        return [
            home_path,
            Path("/mnt"),
            Path("/media") / home_path.name,
        ]

    def _read_manifest(self) -> dict:
        try:
            return json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ObsidianMemoryError("Manifesto do KAWA-AI inválido ou inacessível.") from exc

    def _validate_manifest(self) -> dict:
        manifest = self._read_manifest()
        expected = self._canonical(self.diary_path)
        if manifest.get("diary_path") != expected:
            raise ObsidianMemoryError(
                "O manifesto aponta para outro diário. Operação interrompida para evitar duplicação."
            )
        return manifest

    def initialize(self) -> Path:
        """Cria apenas o diário canônico vazio; chamadas posteriores apenas o reutilizam."""
        if not (self.vault_path / ".obsidian").is_dir():
            raise ObsidianMemoryError("O caminho selecionado não contém .obsidian e não é um cofre Obsidian válido.")

        if self.manifest_path.exists():
            self._validate_manifest()
            self.restore_if_needed()
            return self.diary_path

        if self.diary_path.exists():
            raise ObsidianMemoryError(
                "Existe um diário sem manifesto. Crie o manifesto manualmente ou escolha o cofre correto; nenhum novo diário foi criado."
            )

        self.folder.mkdir(parents=True, exist_ok=True)
        self.diary_path.touch(exist_ok=False)
        manifest = {
            "schema_version": 1,
            "vault_path": self._canonical(self.vault_path),
            "diary_path": self._canonical(self.diary_path),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "append_only": True,
        }
        self._atomic_write(self.manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        return self.diary_path

    @staticmethod
    def _atomic_write(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
            temporary = Path(handle.name)
        temporary.replace(path)

    def restore_if_needed(self) -> None:
        """Recupera o mesmo arquivo canônico apenas a partir de backup local existente."""
        if self.diary_path.exists():
            return
        backups = sorted(self.backup_dir.glob("reasoning-diary-*.md"), reverse=True)
        if not backups:
            raise ObsidianMemoryError(
                "O diário canônico não existe e não há cópia de recuperação. Nenhum novo diário será criado automaticamente."
            )
        self.diary_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backups[0], self.diary_path)

    def _backup(self) -> None:
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        backup = self.backup_dir / f"reasoning-diary-{stamp}.md"
        shutil.copy2(self.diary_path, backup)
        backups = sorted(self.backup_dir.glob("reasoning-diary-*.md"), reverse=True)
        for stale in backups[self.backup_count:]:
            stale.unlink(missing_ok=True)

    def append_entry(self, title: str, content: str, kind: str = "task") -> Path:
        self.initialize()
        clean_title = " ".join(title.split())[:180] or "Registro"
        clean_content = content.strip()
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
        entry = f"\n## {stamp} — {kind}\n\n### {clean_title}\n\n{clean_content}\n"
        with self.diary_path.open("a", encoding="utf-8") as handle:
            handle.write(entry)
            handle.flush()
            os.fsync(handle.fileno())
        self._backup()
        return self.diary_path

    def record_task(self, request: str, result: str) -> Path:
        content = f"**Pedido resumido:** {request.strip()}\n\n**Resultado final:** {result.strip()}"
        return self.append_entry("Sessão concluída", content, kind="task")

    def recent_context(self, max_chars: int | None = None) -> str:
        self.initialize()
        limit = max_chars or self.context_chars
        content = self.diary_path.read_text(encoding="utf-8")
        return content[-limit:].strip()

    def markdown_index(self, max_files: int = 300, max_file_bytes: int = 1_000_000) -> list[dict[str, str | int]]:
        """Indexa metadados de Markdown apenas do cofre selecionado, sem enviar seu conteúdo."""
        self.initialize()
        entries: list[dict[str, str | int]] = []
        for path in sorted(self.vault_path.rglob("*.md")):
            if any(part in {".obsidian", ".git", "node_modules"} for part in path.parts):
                continue
            try:
                stat = path.stat()
            except OSError:
                continue
            if stat.st_size > max_file_bytes:
                continue
            entries.append({
                "path": str(path.relative_to(self.vault_path)),
                "size_bytes": stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
            })
            if len(entries) >= max_files:
                break
        return entries
