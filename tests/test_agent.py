import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent.audit import AuditLogger
from agent.core import Agent
from agent.policy import PolicyMode, ToolPolicy


class FakeProvider:
    """Provider determinístico: responde sequências de tool_call até o fim."""

    def __init__(self, script):
        self.script = list(script)  # cada item: dict tool_call ou texto final
        self.index = 0
        self.systems = []
        self.messages = []

    def generate(self, system, messages):
        self.systems.append(system)
        self.messages.append(messages)
        step = self.script[min(self.index, len(self.script) - 1)]
        self.index += 1
        if isinstance(step, dict):
            import json as _json
            return f"<tool_call>\n{_json.dumps(step)}\n</tool_call>"
        return step


class FakeTools:
    @staticmethod
    def read_file(**kwargs):
        return "conteúdo do arquivo"

    @staticmethod
    def shell(**kwargs):
        return "saída do comando"


class AgentRunTests(unittest.TestCase):
    def setUp(self):
        self.work = Path(tempfile.mkdtemp())
        self.audit = AuditLogger(self.work / "actions.jsonl")

    def _agent(self, provider, policy_mode="ask"):
        policy = ToolPolicy(policy_mode, self.work)
        return Agent(provider, max_iterations=4, policy=policy, audit_logger=self.audit)

    def test_run_finishes_without_tools(self):
        provider = FakeProvider(["Resposta final sem ferramentas."])
        result = self._agent(provider).run("tarefa simples")
        self.assertIn("Resposta final", result)

    def test_run_executes_tool_and_then_answers(self):
        provider = FakeProvider([
            {"tool": "read_file", "input": {"path": "a.txt"}},
            "Resposta após usar a ferramenta.",
        ])
        agent = self._agent(provider, policy_mode="proactive")
        agent.register_tool("read_file", FakeTools.read_file, "lê arquivo")
        result = agent.run("leia e responda")
        self.assertIn("Resposta após usar", result)
        self.assertEqual(len(agent.history), 4)  # tool_call + tool_result + respostas

    def test_blocked_tool_returns_error_message(self):
        provider = FakeProvider([
            {"tool": "shell", "input": {"command": "sudo rm -rf /"}},
            "Resposta final.",
        ])
        agent = self._agent(provider, policy_mode="proactive")
        agent.register_tool("shell", FakeTools.shell, "shell")
        with mock.patch("builtins.input", return_value="n"):
            agent.run("faça algo")
        history_text = json.dumps(agent.history, ensure_ascii=False)
        self.assertIn("cancelada", history_text)  # alto impacto exige confirmação
        log = self.audit.log_file.read_text(encoding="utf-8")
        self.assertIn("declined", log)

    def test_unknown_tool_reported_as_error(self):
        provider = FakeProvider([{"tool": "ferramenta_inexistente", "input": {}}, "fim"])
        agent = self._agent(provider, policy_mode="proactive")
        agent.run("x")
        history_text = json.dumps(agent.history, ensure_ascii=False)
        self.assertIn("não encontrada", history_text)

    def test_unlimited_mode_stops_only_on_repeated_tool_loop(self):
        provider = FakeProvider([{"tool": "read_file", "input": {"path": "same.txt"}}])
        agent = Agent(provider, max_iterations=0, policy=ToolPolicy("proactive", self.work), audit_logger=self.audit)
        agent.register_tool("read_file", FakeTools.read_file, "lê")
        result = agent.run("continue até concluir")
        self.assertIn("mesma chamada de ferramenta se repetiu", result)
        self.assertGreaterEqual(provider.index, 5)

    def test_max_iterations_hit(self):
        provider = FakeProvider([
            {"tool": "read_file", "input": {"path": "x"}},
            {"tool": "read_file", "input": {"path": "y"}},
            {"tool": "read_file", "input": {"path": "z"}},
            {"tool": "read_file", "input": {"path": "w"}},
            {"tool": "read_file", "input": {"path": "v"}},
        ])
        agent = self._agent(provider, policy_mode="proactive")
        agent.register_tool("read_file", FakeTools.read_file, "lê")
        result = agent.run("loop")
        self.assertIn("Limite de iterações", result)

    def test_ask_mode_requires_confirmation_for_write(self):
        provider = FakeProvider([
            {"tool": "write_file", "input": {"path": "notes.md", "content": "x"}},
            "Resposta final.",
        ])
        agent = self._agent(provider, policy_mode="ask")
        agent.register_tool("write_file", lambda **kwargs: "escrito", "escreve")
        with mock.patch("builtins.input", return_value="n"):
            agent.run("escreva")
        history_text = json.dumps(agent.history, ensure_ascii=False)
        self.assertIn("cancelada", history_text)


if __name__ == "__main__":
    unittest.main()