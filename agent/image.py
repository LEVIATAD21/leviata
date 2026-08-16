"""Ferramentas opcionais de visão e geração de imagens."""
from __future__ import annotations

import base64
import json
import mimetypes
import re
from pathlib import Path
from typing import Iterable


class ImageError(RuntimeError):
    """Erro controlado de visão ou geração de imagem."""


class ImageToolkit:
    """Analisa imagens com o provider configurado e gera assets quando suportado."""

    allowed_extensions = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

    def __init__(self, workspace: str | Path, provider=None):
        self.workspace = Path(workspace).expanduser().resolve()
        self.provider = provider

    def _image_paths(self, raw_paths: Iterable[str]) -> list[Path]:
        paths: list[Path] = []
        for raw in raw_paths:
            candidate = Path(raw).expanduser()
            if not candidate.is_absolute():
                candidate = self.workspace / candidate
            candidate = candidate.resolve()
            try:
                candidate.relative_to(self.workspace)
            except ValueError as exc:
                raise ImageError("A análise de imagens só pode usar arquivos dentro do workspace.") from exc
            if candidate.suffix.lower() not in self.allowed_extensions:
                raise ImageError(f"Formato de imagem não suportado: {candidate.suffix}")
            if not candidate.is_file():
                raise ImageError(f"Imagem não encontrada: {candidate}")
            if candidate.stat().st_size > 15 * 1024 * 1024:
                raise ImageError("Cada imagem precisa ter no máximo 15 MB antes do envio ao provider.")
            paths.append(candidate)
        if not paths:
            raise ImageError("Informe ao menos uma imagem.")
        if len(paths) > 12:
            raise ImageError("Envie no máximo 12 imagens por análise.")
        return paths

    def analyze(self, input_paths: Iterable[str], prompt: str) -> str:
        paths = self._image_paths(input_paths)
        if not self.provider or not hasattr(self.provider, "generate_multimodal"):
            raise ImageError("O provider configurado não oferece análise multimodal.")
        try:
            result = self.provider.generate_multimodal(
                "Você é um analista visual cuidadoso. Descreva somente o que está nas imagens, "
                "separe observação de inferência e inclua incertezas.",
                prompt,
                [str(path) for path in paths],
            )
        except Exception as exc:
            raise ImageError(f"Falha na análise visual: {exc}") from exc
        return str(result)

    def generate(self, prompt: str, output_name: str = "generated-image.png", size: str = "1024x1024") -> str:
        """Gera uma imagem por API compatível quando o provider expõe client.images."""
        if not self.provider or not getattr(self.provider, "client", None) or not hasattr(self.provider.client, "images"):
            raise ImageError("O provider não expõe uma API compatível de geração de imagens.")
        safe_name = re.sub(r"[^A-Za-z0-9._-]+", "-", Path(output_name).name).strip(".-") or "generated-image.png"
        if Path(safe_name).suffix.lower() not in self.allowed_extensions:
            safe_name += ".png"
        output = (self.workspace / "kawa-media" / "images" / safe_name).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        try:
            response = self.provider.client.images.generate(model=getattr(self.provider, "model", None), prompt=prompt, size=size)
            item = response.data[0]
            if getattr(item, "b64_json", None):
                output.write_bytes(base64.b64decode(item.b64_json))
            elif getattr(item, "url", None):
                import requests
                download = requests.get(item.url, timeout=60)
                download.raise_for_status()
                output.write_bytes(download.content)
            else:
                raise ImageError("O provider não retornou dados de imagem.")
        except ImageError:
            raise
        except Exception as exc:
            raise ImageError(f"Falha na geração de imagem: {exc}") from exc
        return json.dumps({"path": str(output), "prompt": prompt, "size": size}, ensure_ascii=False, indent=2)
