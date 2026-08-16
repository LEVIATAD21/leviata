"""Pipeline multimodal de compreensão de vídeos locais."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from agent.media import MediaError, MediaToolkit


class VideoError(RuntimeError):
    """Erro controlado no pipeline de vídeo."""


class VideoToolkit:
    """Coordena amostragem temporal, áudio local e análise visual."""

    def __init__(self, workspace: str | Path, provider=None, media: MediaToolkit | None = None):
        self.workspace = Path(workspace).expanduser().resolve()
        self.provider = provider
        self.media = media or MediaToolkit(self.workspace)

    @staticmethod
    def _even_sample(frames: list[Path], maximum: int) -> list[Path]:
        if len(frames) <= maximum:
            return frames
        indexes = [round(index * (len(frames) - 1) / (maximum - 1)) for index in range(maximum)]
        return [frames[index] for index in indexes]

    def analyze(self, input_path: str, prompt: str, fps: float = 0.2, max_frames: int = 12, whisper_model: str | None = None) -> str:
        if not 1 <= int(max_frames) <= 48:
            raise VideoError("max_frames deve ficar entre 1 e 48.")
        if not self.provider or not hasattr(self.provider, "generate_multimodal"):
            raise VideoError("O provider configurado não oferece análise multimodal.")
        try:
            source, frames, manifest_path = self.media.extract_frame_files(input_path, fps=fps, max_frames=max(12, int(max_frames) * 4))
        except MediaError as exc:
            raise VideoError(str(exc)) from exc
        selected = self._even_sample(frames, int(max_frames))
        transcript_path: Path | None = None
        transcript_error = None
        try:
            transcript_path = self.media.transcribe_file(input_path, whisper_model)
        except MediaError as exc:
            transcript_error = str(exc)

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        frames_context = []
        fps_value = float(manifest.get("fps", fps))
        for frame in selected:
            number = int(frame.stem.split("-")[-1])
            frames_context.append({"file": str(frame), "approx_timestamp_seconds": round((number - 1) / fps_value, 2)})
        transcript = transcript_path.read_text(encoding="utf-8", errors="replace")[:24_000] if transcript_path else ""
        analysis_prompt = (
            f"Pedido do usuário: {prompt}\n\n"
            "Analise os frames fornecidos como uma amostra temporal, não como prova de cada instante do vídeo. "
            "Relacione observações aos timestamps aproximados abaixo, descreva mudanças de cena, texto visível, "
            "objetos, ações e possíveis instruções. Separe fatos observados, conteúdo transcrito e inferências.\n"
            f"Manifesto de frames: {json.dumps(frames_context, ensure_ascii=False)}\n"
            f"Transcrição local (pode estar vazia):\n{transcript or '[não disponível]'}\n"
            f"Limitação de áudio: {transcript_error or 'transcrição disponível'}"
        )
        try:
            model_analysis = self.provider.generate_multimodal(
                "Você é um analista multimodal de vídeo. Seja temporalmente preciso, conservador e transparente sobre incertezas.",
                analysis_prompt,
                [str(frame) for frame in selected],
            )
        except Exception as exc:
            raise VideoError(f"Falha na análise multimodal do vídeo: {exc}") from exc

        report = {
            "source": str(source),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "fps": fps_value,
            "frames_sampled": frames_context,
            "transcript": str(transcript_path) if transcript_path else None,
            "transcript_error": transcript_error,
            "request": prompt,
            "analysis": str(model_analysis),
        }
        report_path = manifest_path.parent / "analysis.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return json.dumps({"report": str(report_path), "analysis": str(model_analysis)}, ensure_ascii=False, indent=2)
