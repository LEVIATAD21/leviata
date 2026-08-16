"""Ferramentas locais de mídia: quadros de vídeo e transcrição por whisper.cpp."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


class MediaError(RuntimeError):
    """Erro seguro de mídia que explica o pré-requisito ausente."""


class MediaToolkit:
    """Executa operações de mídia moderadas dentro de uma pasta de trabalho."""

    def __init__(self, workspace: str | Path, runner: Callable | None = None):
        self.workspace = Path(workspace).expanduser().resolve()
        self.runner = runner or subprocess.run

    def _resolve_source(self, raw_path: str) -> Path:
        path = Path(raw_path).expanduser()
        if not path.is_absolute():
            path = self.workspace / path
        path = path.resolve()
        if not path.is_file():
            raise MediaError(f"Arquivo de mídia não encontrado: {path}")
        return path

    def _output_dir(self, source: Path, kind: str) -> Path:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        directory = self.workspace / "kawa-media" / kind / f"{source.stem}-{stamp}"
        directory.mkdir(parents=True, exist_ok=False)
        return directory

    @staticmethod
    def _require_command(command: str) -> str:
        resolved = shutil.which(command)
        if not resolved:
            raise MediaError(f"'{command}' não está instalado. Instale-o no sistema antes de usar este módulo.")
        return resolved

    def extract_frame_files(self, input_path: str, fps: float = 0.2, max_frames: int = 120) -> tuple[Path, list[Path], Path]:
        """Extrai frames e devolve fonte, arquivos e manifesto para pipelines multimodais."""
        if not 0.05 <= float(fps) <= 2.0:
            raise MediaError("A taxa de quadros deve ficar entre 0,05 e 2 quadros por segundo.")
        if not 1 <= int(max_frames) <= 500:
            raise MediaError("max_frames deve ficar entre 1 e 500.")
        source = self._resolve_source(input_path)
        ffmpeg = self._require_command("ffmpeg")
        output = self._output_dir(source, "frames")
        pattern = output / "frame-%06d.jpg"
        command = [
            ffmpeg, "-hide_banner", "-loglevel", "error", "-i", str(source),
            "-vf", f"fps={float(fps):g}", "-frames:v", str(int(max_frames)), "-q:v", "3", str(pattern),
        ]
        try:
            self.runner(command, check=True, capture_output=True, text=True, timeout=600)
        except subprocess.CalledProcessError as exc:
            raise MediaError(f"FFmpeg não conseguiu extrair quadros: {exc.stderr[-500:]}") from exc
        except subprocess.TimeoutExpired as exc:
            raise MediaError("Extração excedeu 10 minutos; reduza a duração do vídeo ou a taxa de quadros.") from exc
        frames = sorted(output.glob("frame-*.jpg"))
        manifest = {
            "source": str(source),
            "fps": float(fps),
            "max_frames": int(max_frames),
            "frames": [frame.name for frame in frames],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        manifest_path = output / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return source, frames, manifest_path

    def extract_frames(self, input_path: str, fps: float = 0.2) -> str:
        """Extrai poucos quadros por segundo para investigação, evitando explosão de armazenamento."""
        _, frames, manifest = self.extract_frame_files(input_path, fps=fps)
        return f"{len(frames)} quadros extraídos em: {manifest.parent}\nManifesto: {manifest}"

    @staticmethod
    def _whisper_binary() -> str:
        configured = os.environ.get("KAWA_WHISPER_CPP_BIN")
        candidates = [configured, "whisper-cli", "main"]
        for candidate in candidates:
            if not candidate:
                continue
            path = Path(candidate).expanduser()
            if path.is_file() and os.access(path, os.X_OK):
                return str(path)
            resolved = shutil.which(str(candidate))
            if resolved:
                return resolved
        raise MediaError(
            "whisper.cpp não foi encontrado. Configure KAWA_WHISPER_CPP_BIN ou instale um executável 'whisper-cli'."
        )

    def transcribe_file(self, input_path: str, model_path: str | None = None) -> Path:
        source = self._resolve_source(input_path)
        binary = self._whisper_binary()
        model = Path(model_path or os.environ.get("KAWA_WHISPER_MODEL", Path.home() / ".kawa-ai" / "models" / "ggml-base.bin")).expanduser()
        if not model.is_file():
            raise MediaError(
                f"Modelo whisper.cpp não encontrado: {model}. Defina KAWA_WHISPER_MODEL para um arquivo ggml existente."
            )
        output = self._output_dir(source, "transcripts")
        base = output / "transcript"
        command = [binary, "-m", str(model), "-f", str(source), "-otxt", "-of", str(base)]
        try:
            self.runner(command, check=True, capture_output=True, text=True, timeout=1800)
        except subprocess.CalledProcessError as exc:
            raise MediaError(f"whisper.cpp não conseguiu transcrever: {exc.stderr[-500:]}") from exc
        except subprocess.TimeoutExpired as exc:
            raise MediaError("Transcrição excedeu 30 minutos; tente um modelo menor ou arquivo mais curto.") from exc
        transcript = base.with_suffix(".txt")
        if not transcript.exists():
            raise MediaError("whisper.cpp terminou sem produzir o arquivo de transcrição esperado.")
        return transcript

    def transcribe(self, input_path: str, model_path: str | None = None) -> str:
        transcript = self.transcribe_file(input_path, model_path)
        return f"Transcrição salva em: {transcript}"
