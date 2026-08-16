import tempfile
import unittest
from pathlib import Path

from agent.audit import AuditLogger
from agent.connections import ConnectionStore
from agent.design import DesignToolkit
from agent.media import MediaError, MediaToolkit
from agent.pentest import EthicalPentestToolkit, PentestError
from agent.adversary import AdversarySimulation, AdversaryError
from agent.environment import EnvironmentInspector
from agent.skills_catalog import SkillsCatalog
from ui.service import UICommand
from agent.orchestrator import TaskOrchestrator
from agent.quality import QualityToolkit
from agent.nvidia_research import NvidiaResearch, NvidiaResearchError
from agent.supabase_memory import SupabaseKnowledgeStore
from agent.core import SYSTEM_PROMPT
from agent.knowledge import KNOWLEDGE_SYSTEM_PROMPT, KnowledgeBrain
from agent.memory import ObsidianMemory, ObsidianMemoryError
from agent.policy import Decision, ToolPolicy
from agent.router import TaskRoute, TaskRouter
from tools.browser import BrowserTool


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

    def test_proactive_mode_allows_routine_local_work_but_keeps_high_impact_confirmation(self):
        policy = ToolPolicy("proactive", self.workspace)
        self.assertEqual(policy.decide("write_file", {"path": "notes/plan.md"}).decision, Decision.ALLOW)
        self.assertEqual(policy.decide("shell", {"command": "python3 -m unittest"}).decision, Decision.ALLOW)
        self.assertEqual(policy.decide("shell", {"command": "git push origin master"}).decision, Decision.ASK)
        self.assertEqual(policy.decide("browser_type", {"selector": "input", "text": "valor"}).decision, Decision.ASK)

    def test_proactive_policy_allows_quality_audit(self):
        policy = ToolPolicy("proactive", self.workspace)
        self.assertEqual(policy.decide("quality_audit", {"target_path": "."}).decision, Decision.ALLOW)

    def test_proactive_policy_allows_design_brief(self):
        policy = ToolPolicy("proactive", self.workspace)
        self.assertEqual(policy.decide("design_brief", {"request": "Site de estudos"}).decision, Decision.ALLOW)

    def test_sensitive_files_blocked_even_inside_workspace(self):
        policy = ToolPolicy("proactive", self.workspace)
        self.assertEqual(policy.decide("write_file", {"path": "notes/plan.md"}).decision, Decision.ALLOW)
        self.assertEqual(policy.decide("write_file", {"path": ".bashrc"}).decision, Decision.DENY)
        self.assertEqual(policy.decide("write_file", {"path": ".ssh/authorized_keys"}).decision, Decision.DENY)
        self.assertEqual(policy.decide("write_file", {"path": ".env"}).decision, Decision.DENY)

    def test_proactive_policy_allows_ethical_pentest(self):
        policy = ToolPolicy("proactive", self.workspace)
        self.assertEqual(policy.decide("ethical_pentest", {"target_path": "."}).decision, Decision.ALLOW)

    def test_proactive_policy_allows_adversary_simulate(self):
        policy = ToolPolicy("proactive", self.workspace)
        self.assertEqual(policy.decide("adversary_simulate", {"target_path": "."}).decision, Decision.ALLOW)

    def test_high_impact_shell_requires_confirmation(self):
        policy = ToolPolicy("workspace", self.workspace)
        self.assertEqual(policy.decide("shell", {"command": "rm -rf build"}).decision, Decision.ASK)

    def test_browser_write_actions_require_confirmation(self):
        policy = ToolPolicy("workspace", self.workspace)
        self.assertEqual(policy.decide("browser_navigate", {"url": "https://example.org"}).decision, Decision.ALLOW)
        self.assertEqual(policy.decide("browser_click", {"selector": "button"}).decision, Decision.ASK)
        self.assertEqual(policy.decide("browser_type", {"selector": "input", "text": "valor"}).decision, Decision.ASK)

    def test_audit_redacts_secret_fields(self):
        log_file = self.workspace / "actions.jsonl"
        logger = AuditLogger(log_file)
        logger.record("web_fetch", {"api_key": "secret-value", "url": "https://example.com"}, "success", "ok")
        content = log_file.read_text(encoding="utf-8")
        self.assertIn("[redigido]", content)
        self.assertNotIn("secret-value", content)

    def test_audit_redacts_browser_text(self):
        log_file = self.workspace / "actions.jsonl"
        logger = AuditLogger(log_file)
        logger.record("browser_type", {"selector": "input", "text": "dado-pessoal"}, "success", "ok")
        content = log_file.read_text(encoding="utf-8")
        self.assertIn("[redigido]", content)
        self.assertNotIn("dado-pessoal", content)

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

    def test_obsidian_memory_creates_one_empty_diary_and_reuses_it(self):
        vault = self.workspace / "vault"
        (vault / ".obsidian").mkdir(parents=True)
        memory = ObsidianMemory(vault)
        first = memory.initialize()
        second = memory.initialize()
        self.assertEqual(first, second)
        self.assertEqual(first.read_text(encoding="utf-8"), "")
        self.assertEqual(list((vault / "KAWA-AI").glob("*Reasoning Diary*.md")), [first])

    def test_obsidian_memory_appends_and_recovers_recent_context(self):
        vault = self.workspace / "vault"
        (vault / ".obsidian").mkdir(parents=True)
        memory = ObsidianMemory(vault, context_chars=1_000)
        memory.append_entry("Primeira tarefa", "Resultado A")
        memory.append_entry("Segunda tarefa", "Resultado B")
        diary = memory.diary_path
        content = diary.read_text(encoding="utf-8")
        self.assertIn("Primeira tarefa", content)
        self.assertIn("Segunda tarefa", memory.recent_context())
        self.assertTrue(list(memory.backup_dir.glob("reasoning-diary-*.md")))

    def test_obsidian_memory_refuses_to_create_a_second_diary_without_manifest(self):
        vault = self.workspace / "vault"
        diary = vault / "KAWA-AI" / "Reasoning Diary.md"
        (vault / ".obsidian").mkdir(parents=True)
        diary.parent.mkdir()
        diary.write_text("registro existente", encoding="utf-8")
        with self.assertRaises(ObsidianMemoryError):
            ObsidianMemory(vault).initialize()

    def test_discovery_finds_only_obsidian_markers(self):
        home = self.workspace / "home"
        (home / "Documents" / "Cofre" / ".obsidian").mkdir(parents=True)
        (home / "Documents" / "Cofre" / "nota.md").write_text("não precisa ser lida", encoding="utf-8")
        self.assertEqual(ObsidianMemory.discover_vaults([home]), [(home / "Documents" / "Cofre").resolve()])

    def test_default_discovery_starts_from_root(self):
        self.assertEqual(ObsidianMemory.default_search_roots(), [Path("/")])

    def test_browser_prefers_explicit_local_executable(self):
        executable = self.workspace / "chromium"
        executable.write_text("#!/bin/sh\n", encoding="utf-8")
        executable.chmod(0o755)
        browser = BrowserTool(self.workspace / "profile", executable_path=executable)
        self.assertEqual(browser.executable_path, str(executable.resolve()))

    def test_connection_store_keeps_token_out_of_metadata_and_removes_profile(self):
        class FakeKeyring:
            def __init__(self):
                self.values = {}

            def set_password(self, service, name, token):
                self.values[(service, name)] = token

            def delete_password(self, service, name):
                self.values.pop((service, name), None)

        keyring = FakeKeyring()
        store = ConnectionStore(self.workspace / "connections", credential_backend=keyring)
        store.set_token("Instagram", "token-secreto", ["instagram_basic"])
        profile = store.register_browser_profile("Instagram")
        metadata = store.metadata_path.read_text(encoding="utf-8")
        self.assertNotIn("token-secreto", metadata)
        self.assertIn("instagram", metadata)
        self.assertTrue(profile.exists())
        self.assertTrue(store.remove("instagram"))
        self.assertFalse(profile.exists())
        self.assertNotIn((store.keyring_service, "instagram"), keyring.values)

    def test_media_policy_requires_confirmation_and_tool_rejects_unsafe_rate(self):
        policy = ToolPolicy("workspace", self.workspace)
        self.assertEqual(policy.decide("media_extract_frames", {"input_path": "video.mp4"}).decision, Decision.ASK)
        video = self.workspace / "video.mp4"
        video.write_bytes(b"placeholder")
        with self.assertRaises(MediaError):
            MediaToolkit(self.workspace).extract_frames(str(video), fps=3)

    def test_quality_audit_stays_in_workspace_and_records_missing_tools(self):
        workspace = self.workspace / "quality"
        workspace.mkdir()
        (workspace / "sample.py").write_text("print('ok')\n", encoding="utf-8")
        toolkit = QualityToolkit(workspace, finder=lambda _: None)
        result = toolkit.audit(".", ["ruff", "bandit"])
        self.assertIn("ruff: not_installed", result)
        self.assertIn("bandit: not_installed", result)
        self.assertTrue((workspace / "kawa-quality").exists())

    def test_design_brief_creates_editable_markdown_and_mermaid(self):
        toolkit = DesignToolkit(self.workspace)
        result = toolkit.create_brief("Painel de estudos", "site")
        self.assertIn("Brief criado", result)
        files = list((self.workspace / "kawa-design").rglob("*"))
        self.assertTrue(any(item.name == "design-brief.md" for item in files))
        self.assertTrue(any(item.suffix == ".mmd" for item in files))

    def test_ethical_pentest_requires_scope_and_records_lessons(self):
        target = self.workspace / "authorized-project"
        target.mkdir()
        (target / "app.py").write_text("DEBUG = True\n", encoding="utf-8")
        quality = QualityToolkit(self.workspace, finder=lambda _: None)
        pentest = EthicalPentestToolkit(self.workspace, quality=quality)
        with self.assertRaises(PentestError):
            pentest.audit("authorized-project")
        pentest.initialize_scope("authorized-project", authorized=True)
        result = pentest.audit("authorized-project", ["ruff"])
        self.assertIn("Achados locais: 1", result)
        self.assertTrue((target / "kawa-pentest" / "lessons.jsonl").exists())

    def test_adversary_simulation_generates_report(self):
        target = self.workspace / "sim-project"
        target.mkdir()
        sim = AdversarySimulation(self.workspace)
        result = sim.simulate("sim-project")
        self.assertIn("Simulação de adversário concluída", result)
        self.assertTrue(list((target / "kawa-pentest").glob("adversary-simulation-*.json")))

    def test_environment_inspector_returns_dict(self):
        info = EnvironmentInspector.inspect()
        self.assertIn("platform", info)
        self.assertIn("root_privileges", info)

    def test_skills_catalog_renders_report(self):
        report = SkillsCatalog.render_report()
        self.assertIn("Catálogo de Skills", report)
        self.assertIn("ethical_pentest", report)

    def test_ui_command_parser(self):
        command = UICommand.parse("/skills")
        self.assertEqual(command.name, "skills")
        self.assertIsNone(UICommand.parse("crie um plano"))

    def test_orchestrator_selects_capabilities_from_task(self):
        orchestrator = TaskOrchestrator(self.workspace)
        plan = orchestrator.plan("Crie um site seguro e faça auditoria OWASP do código")
        skills = {step.skill for step in plan}
        self.assertIn("design_brief", skills)
        self.assertIn("quality_audit", skills)
        self.assertIn("ethical_pentest", skills)

    def test_connection_store_returns_token_without_writing_it_to_metadata(self):
        class FakeKeyring:
            def __init__(self):
                self.values = {}
            def set_password(self, service, name, token):
                self.values[(service, name)] = token
            def get_password(self, service, name):
                return self.values.get((service, name))

        store = ConnectionStore(self.workspace / "connections", credential_backend=FakeKeyring())
        store.set_token("nvidia", "segredo")
        self.assertEqual(store.get_token("nvidia"), "segredo")
        self.assertNotIn("segredo", store.metadata_path.read_text(encoding="utf-8"))

    def test_nvidia_research_queries_selected_models_in_sequence(self):
        class FakeConnections:
            def get_token(self, service):
                return "token"
        class Response:
            def __init__(self, payload): self.payload = payload
            def raise_for_status(self): return None
            def json(self): return self.payload
        class FakeHttp:
            def __init__(self): self.calls = []
            def get(self, *args, **kwargs):
                return Response({"data": [{"id": "model-a-instruct"}, {"id": "model-b-reason"}]})
            def post(self, *args, **kwargs):
                self.calls.append(kwargs["json"])
                return Response({"choices": [{"message": {"content": f"resposta-{len(self.calls)}"}}]})

        http = FakeHttp()
        frames = NvidiaResearch(FakeConnections(), http).consult("Como testar?", maximum=2)
        self.assertEqual([frame.model for frame in frames], ["model-a-instruct", "model-b-reason"])
        self.assertIn("resposta-1", http.calls[1]["messages"][0]["content"])

    def test_supabase_payload_redacts_secret_like_text(self):
        class FakeConnections:
            def get_endpoint(self, service): return "https://example.supabase.co"
            def get_token(self, service): return "token"
        class Response:
            def raise_for_status(self): return None
        class FakeHttp:
            def __init__(self): self.payload = None
            def post(self, *args, **kwargs):
                self.payload = kwargs["json"]
                return Response()

        http = FakeHttp()
        SupabaseKnowledgeStore(FakeConnections(), http).save_research("Teste", "api_key=valor-secreto")
        self.assertIn("[redigido]", http.payload["content"])
        self.assertNotIn("valor-secreto", http.payload["content"])

    def test_supabase_check_is_read_only(self):
        class FakeConnections:
            def get_endpoint(self, service): return "https://example.supabase.co"
            def get_token(self, service): return "token"
        class Response:
            status_code = 200
            def raise_for_status(self): return None
        class FakeHttp:
            def __init__(self): self.called = None
            def get(self, *args, **kwargs):
                self.called = {"args": args, "kwargs": kwargs}
                return Response()

        http = FakeHttp()
        result = SupabaseKnowledgeStore(FakeConnections(), http).check()
        self.assertEqual(result["status"], "ok")
        self.assertEqual(http.called["kwargs"]["params"]["limit"], "0")

    def test_supabase_setup_uses_connection_vault_then_runs_read_only_check(self):
        class FakeConnections:
            def __init__(self):
                self.endpoint = None
                self.token = None
            def set_endpoint(self, service, endpoint): self.endpoint = endpoint
            def set_token(self, service, token, scopes): self.token = token
            def get_endpoint(self, service): return self.endpoint
            def get_token(self, service): return self.token
        class Response:
            status_code = 200
            def raise_for_status(self): return None
        class FakeHttp:
            def get(self, *args, **kwargs): return Response()

        connections = FakeConnections()
        result = SupabaseKnowledgeStore(connections, FakeHttp()).configure("https://example.supabase.co", "token-local")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(connections.endpoint, "https://example.supabase.co")
        self.assertEqual(connections.token, "token-local")


if __name__ == "__main__":
    unittest.main()
