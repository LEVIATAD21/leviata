import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent.context import ContextLimits, ContextManager
from agent.image import ImageError, ImageToolkit
from agent.policy import Decision, ToolPolicy
from agent.skills import SkillRegistry
from agent.video import VideoToolkit


class FakeVisionProvider:
    def __init__(self):
        self.calls = []

    def generate_multimodal(self, system, prompt, image_paths):
        self.calls.append((system, prompt, image_paths))
        return "análise visual"


class MultimodalTests(unittest.TestCase):
    def test_context_redacts_and_compacts_history(self):
        manager = ContextManager(ContextLimits(max_history_messages=4, max_history_chars=80, keep_recent_messages=2))
        history = [{"role": "user", "content": "texto antigo " * 20}, {"role": "assistant", "content": "sk-123456789012345"}, {"role": "user", "content": "recente"}, {"role": "assistant", "content": "fim"}]
        fitted = manager.fit(history)
        self.assertLessEqual(len(fitted), 4)
        self.assertTrue(any("conversation_summary" in item["content"] for item in fitted))
        self.assertNotIn("sk-123456789012345", json.dumps(fitted))

    def test_skill_registry_selects_by_keywords(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "skills"
            skill = root / "security" / "SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("---\nname: security\nkeywords: segurança, owasp\n---\nUse SAST.", encoding="utf-8")
            registry = SkillRegistry([root])
            rendered = registry.render_for("faça uma auditoria de segurança OWASP")
            self.assertIn("security", rendered)
            self.assertIn("Use SAST", rendered)

    def test_multimodal_policy_requires_confirmation(self):
        policy = ToolPolicy("proactive", tempfile.mkdtemp())
        result = policy.decide("video_analyze", {"input_path": "video.mp4"})
        self.assertIs(Decision.ASK, result.decision)
        self.assertIs(Decision.ALLOW, policy.decide("browser_screenshot", {}).decision)

    def test_image_toolkit_rejects_outside_workspace(self):
        workspace = Path(tempfile.mkdtemp())
        toolkit = ImageToolkit(workspace, FakeVisionProvider())
        with self.assertRaises(ImageError):
            toolkit.analyze(["/tmp/fora-do-workspace.png"], "descreva")

    def test_image_toolkit_sends_valid_image_to_provider(self):
        workspace = Path(tempfile.mkdtemp())
        image = workspace / "frame.png"
        image.write_bytes(b"fake image")
        provider = FakeVisionProvider()
        result = ImageToolkit(workspace, provider).analyze(["frame.png"], "o que aparece?")
        self.assertEqual(result, "análise visual")
        self.assertEqual(provider.calls[0][2], [str(image.resolve())])

    def test_video_even_sample_is_temporally_spread(self):
        frames = [Path(f"frame-{index:06d}.jpg") for index in range(1, 101)]
        selected = VideoToolkit._even_sample(frames, 5)
        self.assertEqual(len(selected), 5)
        self.assertEqual(selected[0], frames[0])
        self.assertEqual(selected[-1], frames[-1])


if __name__ == "__main__":
    unittest.main()
