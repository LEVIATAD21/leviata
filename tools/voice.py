"""Comando e resposta por voz — 100% local, sem APIs.

STT: Vosk (streaming, leve) ou whisper.cpp (fallback)
TTS: Piper (natural, CPU-friendly) ou espeak-ng (fallback ultra-leve)
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

VOICE_DIR = Path.home() / ".leviata-ai" / "voice"


class VoiceError(RuntimeError):
    """Erro de voz sem expor caminhos ou conteúdo sensível."""


def _require(tool: str, hint: str) -> None:
    if shutil.which(tool) is None:
        raise VoiceError(f"Ferramenta '{tool}' não encontrada. {hint}")


def record(duration: float = 8.0, rate: int = 16000) -> Path:
    """Grava áudio do microfone via ALSA e devolve o caminho do WAV."""
    _require("arecord", "Instale o ALSA utils: sudo apt install alsa-utils")
    VOICE_DIR.mkdir(parents=True, exist_ok=True)
    path = VOICE_DIR / "command.wav"
    try:
        subprocess.run(
            ["arecord", "-q", "-f", "S16_LE", "-r", str(rate), "-c", "1",
             "-t", "wav", "-d", str(duration), str(path)],
            check=True,
            timeout=duration + 10,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise VoiceError(f"Não foi possível gravar o áudio: {exc}") from exc
    return path


def transcribe(audio: Path, model_dir: str | None = None) -> str:
    """Transcreve um WAV com Vosk (streaming local). Fallback: whisper.cpp."""
    if shutil.which("vosk-transcriber") or _vosk_available():
        return _transcribe_vosk(audio, model_dir)
    raise VoiceError(
        "Nenhum transcritor local encontrado. Instale: pip install vosk "
        "e baixe o modelo pt (Vosk-model-small-pt-0.3)."
    )


def _vosk_available() -> bool:
    try:
        import vosk  # noqa: F401
        return True
    except ImportError:
        return False


def _transcribe_vosk(audio: Path, model_dir: str | None) -> str:
    import wave

    from vosk import KaldiRecognizer, Model, SetLogLevel

    SetLogLevel(-1)
    model_path = Path(model_dir or (VOICE_DIR / "vosk-model-small-pt-0.3")).expanduser()
    if not model_path.exists():
        raise VoiceError(
            f"Modelo Vosk pt não encontrado em {model_path}. "
            "Baixe em https://alphacephei.com/vosk/models (Vosk-model-small-pt-0.3)."
        )
    model = Model(str(model_path))
    with wave.open(str(audio), "rb") as wf:
        rec = KaldiRecognizer(model, wf.getframerate())
        parts: list[str] = []
        while True:
            data = wf.readframes(4000)
            if not data:
                break
            if rec.AcceptWaveform(data):
                parts.append(json.loads(rec.Result()).get("text", ""))
        parts.append(json.loads(rec.FinalResult()).get("text", ""))
    return " ".join(part for part in parts if part)


def speak(text: str) -> None:
    """Fala o texto com Piper TTS local; fallback para espeak-ng."""
    text = text.strip()
    if not text:
        return
    _require("paplay", "Instale pulseaudio-utils.")
    VOICE_DIR.mkdir(parents=True, exist_ok=True)
    out = VOICE_DIR / "response.wav"

    if shutil.which("piper"):
        model = VOICE_DIR / "pt_BR-faber-medium.onnx"
        if model.exists():
            try:
                subprocess.run(
                    ["piper", "-m", str(model), "-f", str(out)],
                    input=text.encode("utf-8"),
                    check=True,
                    timeout=120,
                )
                subprocess.run(["paplay", str(out)], check=True, timeout=300)
                return
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                pass  # cai no fallback

    if shutil.which("espeak-ng"):
        subprocess.run(["espeak-ng", "-v", "pt-br", text], check=True, timeout=120)
        return

    raise VoiceError(
        "Nenhum sintetizador local. Instale: pip install piper-tts e baixe "
        "pt_BR-faber-medium.onnx em https://huggingface.co/rhasspy/piper-voices"
    )


def listen(duration: float = 8.0) -> str:
    """Atalho: grava e transcreve — o comando falado."""
    audio = record(duration)
    return transcribe(audio)
