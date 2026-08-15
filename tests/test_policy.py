import tempfile
import unittest
from pathlib import Path

from agent.audit import AuditLogger
from agent.core import SYSTEM_PROMPT
from agent.knowledge import KNOWLEDGE_SYSTEM_PROMPT, KnowledgeBrain
from agent.policy import Decision, ToolPolicy
from agent.router import TaskRoute, TaskRouter


class ToolPolicyTests(unittest.TestCase):
    def setUp(self):
        self.workspace = Path(tempfile.mkdtemp())

    def test_observe_allows_read_but_blocks_writes(self):
        policy = ToolPolicy("observe", self.workspace)
        self.assertEqual(policy.decide("read_file", {"path": "README.md"}).decision, Decision.ALLOW)
        self.assertEqual(policy.decide("write_file", {"path": "note.txt"}).decision, Decision.DENY)

    def test_workspace_allows_internal_write_and_denies_escape(self):
        policy = ToolPolicy("workspace", self.workspace)
        self.assertEqual(policy.decide("write_file", {"path": "notes/today.md"}).decision, Decision.ALLOW)
        self.assertEqual(policy.decide("write_file", {"path": "../outside.txt"}).decision, Decision.DENY)

    def test_ask_mode_requires_confirmation_for_shell(self):
        policy = ToolPolicy("ask", self.workspace)
        self.assertEqual(policy.decide("shell", {"command": "pwd"}).decision, Decision.ASK)

    def test_high_impact_shell_requires_confirmation(self):
        policy = ToolPolicy("workspace", self.workspace)
        self.assertEqual(policy.decide("shell", {"command": "rm -rf build"}).decision, Decision.ASK)

    def test_audit_redacts_secret_fields(self):
        log_file = self.workspace / "actions.jsonl"
        logger = AuditLogger(log_file)
        logger.record("web_fetch", {"api_key": "secret-value", "url": "https://example.com"}, "success", "ok")
        content = log_file.read_text(encoding="utf-8")
        self.assertIn("[redigido]", content)
        self.assertNotIn("secret-value", content)

    def test_knowledge_brain_only_uses_search_and_returns_questions(self):
        class StubProvider:
            def generate(self, system, messages):
                self.system = system
                self.messages = messages
                return "Síntese baseada apenas nas evidências fornecidas."

        queries = []

        def fake_search(query):
            queries.append(query)
            return "Fonte: https://example.org/referencia\nTrecho verificável"

        provider = StubProvider()
        brain = KnowledgeBrain(provider, fake_search)
        report = brain.inquire("sistemas de arquivos")
        self.assertEqual(len(queries), 4)
        self.assertIn("Como funciona sistemas de arquivos?", report)
        self.assertIn("https://example.org/referencia", report)
        self.assertIn("Síntese baseada", report)
        self.assertEqual(provider.system, KNOWLEDGE_SYSTEM_PROMPT)
        self.assertNotEqual(provider.system, SYSTEM_PROMPT)

    def test_knowledge_brain_saves_markdown_only_when_requested(self):
        class StubProvider:
            def generate(self, system, messages):
                return "Síntese local."

        vault = self.workspace / "knowledge"
        brain = KnowledgeBrain(StubProvider(), lambda query: "Fonte: https://example.org", vault_path=vault)
        report = brain.inquire("Memória local", persist=True)
        stored = list(vault.glob("*.md"))
        self.assertEqual(len(stored), 1)
        self.assertIn("Registro local", report)
        self.assertIn("Memória local", stored[0].read_text(encoding="utf-8"))

    def test_router_sends_explanations_to_knowledge_and_actions_to_agent(self):
        router = TaskRouter()
        self.assertEqual(router.route("Como funciona RAG local?"), TaskRoute.KNOWLEDGE)
        self.assertEqual(router.route("Crie um arquivo de notas"), TaskRoute.AGENT)


if __name__ == "__main__":
    unittest.main()
