"""Serviço conversacional que liga a interface TUI ao núcleo do KAWA-AI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agent.adversary import AdversarySimulation
from agent.cybersecurity_catalog import CybersecurityReferenceCatalog
from agent.core import Agent
from agent.design import DesignToolkit
from agent.knowledge import KnowledgeBrain
from agent.media import MediaToolkit
from agent.memory import ObsidianMemory
from agent.pentest import EthicalPentestToolkit
from agent.policy import ToolPolicy
from agent.quality import QualityToolkit
from agent.skills_catalog import SkillsCatalog
from agent.supabase_memory import SupabaseKnowledgeStore
from agent.router import TaskRoute, TaskRouter
from agent.orchestrator import TaskOrchestrator
from agent.language import normalize_user_message
from agent.skill_builder import SkillBuilder
from providers import get_provider
from tools import register_all_tools, web_search


@dataclass(frozen=True)
class UICommand:
    """Comando local da interface, separado das mensagens enviadas ao modelo."""

    name: str
    argument: str = ""

    @classmethod
    def parse(cls, text: str) -> "UICommand | None":
        content = text.strip()
        if not content.startswith("/"):
            return None
        name, _, argument = content[1:].partition(" ")
        return cls(name.lower(), argument.strip())


class ConversationService:
    """Cria agentes de conversa com o mesmo conjunto local de capacidades do CLI."""

    def __init__(self, config: dict, workspace: str | Path | None = None):
        self.config = dict(config)
        if workspace:
            self.config["workspace"] = str(Path(workspace).expanduser().resolve())
        self.workspace = Path(self.config.get("workspace", Path.cwd())).expanduser().resolve()
        self.router = TaskRouter()

    def _memory(self):
        vault = self.config.get("obsidian_vault")
        if not vault:
            return None
        try:
            memory = ObsidianMemory(vault, context_chars=int(self.config.get("memory_context_chars", 6_000)))
            memory.initialize()
            return memory
        except Exception:
            return None

    def _build_agent(self, plan_mode: bool = False):
        provider = get_provider(self.config)
        memory = self._memory()
        policy_name = "observe" if plan_mode else self.config.get("policy_mode", "proactive")
        policy = ToolPolicy(policy_name, self.workspace)
        agent = Agent(provider=provider, max_iterations=0, policy=policy, memory=memory)
        knowledge = KnowledgeBrain(provider, web_search, vault_path=self.config.get("knowledge_vault"), memory=memory)
        quality = QualityToolkit(self.workspace)
        design = DesignToolkit(self.workspace)
        pentest = EthicalPentestToolkit(self.workspace, quality=quality)
        adversary = AdversarySimulation(self.workspace)
        media = MediaToolkit(self.workspace)
        register_all_tools(
            agent,
            knowledge_brain=knowledge,
            media=media,
            quality=quality,
            design=design,
            pentest=pentest,
            adversary=adversary,
            skill_builder=SkillBuilder(self.workspace),
            cybersecurity_catalog=CybersecurityReferenceCatalog(),
        )
        return agent, knowledge

    def run(self, text: str, plan_mode: bool = False) -> str:
        original_message = text.strip()
        message = normalize_user_message(original_message)
        if not message:
            return "Escreva uma tarefa para começar."
        try:
            agent, knowledge = self._build_agent(plan_mode)
            if self.router.route(message) is TaskRoute.KNOWLEDGE:
                return knowledge.inquire(message, persist=True)
            if plan_mode:
                message = (
                    "Você está em MODO PLANO somente leitura. Não execute ferramentas de escrita. "
                    "Entregue um plano claro, riscos, arquivos envolvidos e critérios de validação.\n\n"
                    + message
                )
            return TaskOrchestrator(self.workspace).run(message, agent).render()
        except Exception as exc:
            return f"Erro ao executar a conversa local: {str(exc)}"

    @staticmethod
    def local_command(command: UICommand) -> str | None:
        if command.name == "skills":
            return SkillsCatalog.render_report()
        if command.name == "status":
            return "Interface local ativa. Use /skills, /plan, /build, /clear ou /help."
        if command.name == "help":
            return (
                "Comandos locais:\n"
                "  /plan — alterna para planejamento somente leitura\n"
                "  /build — alterna para execução proativa no workspace\n"
                "  /skills — mostra a cobertura atual de skills\n"
                "  /clear — limpa a conversa desta sessão\n"
                "  /status — mostra o estado local\n"
                "  /help — exibe esta ajuda"
            )
        return None
