import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.voice import VoiceError, speak, transcribe


class VoiceToolkitTests(unittest.TestCase):
    def setUp(self):
        self.work = Path(tempfile.mkdtemp())

    def test_transcribe_raises_clear_error_without_local_models(self):
        with mock.patch("tools.voice.shutil.which", return_value=None), \
             mock.patch("tools.voice._vosk_available", return_value=False):
            with self.assertRaises(VoiceError):
                transcribe(self.work / "comando.wav")

    def test_speak_raises_clear_error_without_synthesizer(self):
        with mock.patch("tools.voice.shutil.which", return_value=None):
            with self.assertRaises(VoiceError):
                speak("oi")

    def test_speak_uses_espeak_fallback_when_piper_absent(self):
        calls = []
        def fake_which(tool):
            return tool if tool in {"espeak-ng", "paplay"} else None
        def fake_run(cmd, **kwargs):
            calls.append(cmd)
            return mock.Mock(returncode=0)
        with mock.patch("tools.voice.shutil.which", side_effect=fake_which), \
             mock.patch("tools.voice.subprocess.run", side_effect=fake_run):
            speak("olá")
        self.assertTrue(any("espeak-ng" in cmd for cmd in calls))

    def test_speak_uses_piper_when_model_present(self):
        model_dir = self.work
        model = model_dir / "pt_BR-faber-medium.onnx"
        model.write_bytes(b"modelo")
        calls = []
        def fake_which(tool):
            return tool if tool in {"piper", "paplay"} else None
        def fake_run(cmd, **kwargs):
            calls.append(cmd)
            return mock.Mock(returncode=0)
        with mock.patch("tools.voice.shutil.which", side_effect=fake_which), \
             mock.patch("tools.voice.subprocess.run", side_effect=fake_run), \
             mock.patch("tools.voice.VOICE_DIR", model_dir):
            speak("oi")
        self.assertTrue(any(cmd and "piper" in str(cmd) for cmd in calls))


if __name__ == "__main__":
    unittest.main()