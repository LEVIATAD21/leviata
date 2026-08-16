"""Materialização local de documentação em um pacote de skill consultável."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


class SkillBuilderError(RuntimeError):
    pass


class SkillBuilder:
    """Cria um pacote local estruturado a partir de material que o usuário possui."""

    SUPPORTED = {".md", ".markdown", ".txt", ".rst", ".adoc", ".html", ".htm", ".pdf"}

    def __init__(self, workspace: str | Path):
        self.workspace = Path(workspace).expanduser().resolve()

    def _resolve_source(self, source_path: str) -> Path:
        source = Path(source_path).expanduser()
        if not source.is_absolute():
            source = self.workspace / source
        source = source.resolve()
        try:
            source.relative_to(self.workspace)
        except ValueError as exc:
            raise SkillBuilderError("O material precisa estar dentro do workspace autorizado.") from exc
        if not source.is_file():
            raise SkillBuilderError(f"Material não encontrado: {source}")
        if source.suffix.lower() not in self.SUPPORTED:
            raise SkillBuilderError(f"Formato não suportado: {source.suffix}")
        return source

    @staticmethod
    def _slug(value: str) -> str:
        value = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
        return value[:64] or "skill-local"

    def _extract(self, source: Path) -> str:
        if source.suffix.lower() == ".pdf":
            try:
                completed = subprocess.run(
                    ["pdftotext", "-layout", str(source), "-"],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                return completed.stdout
            except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
                raise SkillBuilderError("PDF exige o comando local pdftotext e não pôde ser extraído.") from exc
        return source.read_text(encoding="utf-8", errors="replace")

    @staticmethod
    def _sections(text: str) -> list[tuple[str, str]]:
        lines = text.splitlines()
        sections: list[tuple[str, list[str]]] = []
        current = ("visão-geral", [])
        for line in lines:
            heading = re.match(r"^#{1,6}\s+(.+)$", line.strip())
            if heading:
                if current[1]:
                    sections.append((current[0], current[1]))
                current = (heading.group(1).strip(), [])
            elif line.strip():
                current[1].append(line.rstrip())
        if current[1]:
            sections.append((current[0], current[1]))
        if not sections:
            paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
            sections = [(f"parte-{idx:02d}", paragraph.splitlines()) for idx, paragraph in enumerate(paragraphs, 1)]
        return [(title, "\n".join(body).strip()) for title, body in sections]

    def build(self, source_path: str, skill_name: str | None = None, output_dir: str | None = None) -> str:
        source = self._resolve_source(source_path)
        text = self._extract(source)
        sections = self._sections(text)
        slug = self._slug(skill_name or source.stem)
        root = Path(output_dir).expanduser() if output_dir else self.workspace / "kawa-skills" / slug
        root = root.resolve()
        try:
            root.relative_to(self.workspace)
        except ValueError as exc:
            raise SkillBuilderError("A saída precisa permanecer dentro do workspace autorizado.") from exc
        (root / "chapters").mkdir(parents=True, exist_ok=True)
        index_lines = [
            f"# {skill_name or source.stem}",
            "",
            "> Pacote local estruturado pelo KAWA-AI a partir de material fornecido pelo usuário.",
            "> O conteúdo não é publicado automaticamente; verifique direitos e privacidade antes de compartilhar.",
            "",
            f"Fonte local: `{source}`",
            "",
            "## Índice",
        ]
        for idx, (title, body) in enumerate(sections, 1):
            chapter = f"{idx:02d}-{self._slug(title)}.md"
            (root / "chapters" / chapter).write_text(f"# {title}\n\n{body}\n", encoding="utf-8")
            index_lines.append(f"- [{title}](chapters/{chapter})")
        (root / "SKILL.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
        (root / "README.md").write_text(
            "# Pacote de conhecimento local\n\n"
            "Consulte `SKILL.md` para o índice e os arquivos em `chapters/` para o conteúdo estruturado.\n",
            encoding="utf-8",
        )
        return f"Skill local criada em {root} com {len(sections)} seção(ões)."
