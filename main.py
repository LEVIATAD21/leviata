#!/usr/bin/env python3
"""
KAWA-AI — Agente de IA Autônomo e Sistema Multiagente para Terminal Linux
Suporta modo monoagente (ReAct) e modo equipe multiagente com atraso e transcript compartilhado.
"""
import os
import sys
import json
import argparse
import getpass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agent.core import Agent
from agent.connections import ConnectionError, ConnectionStore
from agent.media import MediaError, MediaToolkit
from agent.design import DesignError, DesignToolkit
from agent.quality import QualityError, QualityToolkit
from agent.pentest import EthicalPentestToolkit, PentestError
from agent.adversary import AdversarySimulation, AdversaryError
from agent.cybersecurity_catalog import CybersecurityReferenceCatalog
from agent.secure_site import SecureSiteCycle, SecureSiteError
from agent.environment import EnvironmentInspector
from agent.skills_catalog import SkillsCatalog
from agent.orchestrator import TaskOrchestrator
from agent.skill_builder import SkillBuilder
from agent.nvidia_research import NvidiaResearch, NvidiaResearchError
from agent.supabase_memory import SupabaseKnowledgeStore, SupabaseMemoryError
from agent.knowledge import KnowledgeBrain
from agent.knowledge_campaign import KnowledgeCampaign, KnowledgeCampaignError
from agent.memory import ObsidianMemory, ObsidianMemoryError
from agent.policy import ToolPolicy
from agent.router import TaskRoute, TaskRouter
from agent.multiagent import MultiAgentOrchestrator
from agent.rag import LocalRag, RagError
from providers import get_provider, OpenAIProvider
from tools import register_all_tools, web_search
from tools.voice import VoiceError, listen, record, speak
from tools.browser import BrowserTool

CONFIG_DIR = Path.home() / ".kawa-ai"
CONFIG_FILE = CONFIG_DIR / "config.json"

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    MAGENTA = '\033[95m'

def load_config():
    config = {
        "provider": "ollama",
        "model": "qwen2.5:1.5b",
        "base_url": "http://localhost:11434",
        "policy_mode": "ask",
        "workspace": str(Path.cwd()),
        "knowledge_vault": str(Path.home() / ".kawa-ai" / "knowledge"),
        "obsidian_vault": None,
        "memory_context_chars": 6_000,
        "browser_profile_dir": str(Path.home() / ".kawa-ai" / "browser-profile"),
        "browser_executable": None,
    }
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config.update(json.load(f))
        except Exception:
            pass
    return config


def save_config(config):
    """Persiste somente a configuração local, com permissão privada quando possível."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    temp_file = CONFIG_FILE.with_suffix(".tmp")
    temp_file.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        temp_file.chmod(0o600)
    except OSError:
        pass
    temp_file.replace(CONFIG_FILE)


def resolve_obsidian_memory(args, config):
    """Reutiliza o cofre salvo ou seleciona um único candidato sem trocar cofre em silêncio."""
    selected = args.obsidian_vault or config.get("obsidian_vault")
    if not selected:
        roots = [Path(args.scan_root).expanduser()] if args.scan_root else ObsidianMemory.default_search_roots()
        candidates = ObsidianMemory.discover_vaults(roots)
        if len(candidates) == 1:
            selected = str(candidates[0])
            config["obsidian_vault"] = selected
            save_config(config)
            print(f"{Colors.GREEN}Cofre Obsidian encontrado: {selected}{Colors.RESET}")
        elif len(candidates) > 1:
            print(f"{Colors.WARNING}Foram encontrados vários cofres Obsidian; nenhum foi selecionado automaticamente:{Colors.RESET}")
            for candidate in candidates:
                print(f"  - {candidate}")
            print("Use --obsidian-vault <caminho> para selecionar somente um deles.")
            return None
        else:
            print(f"{Colors.WARNING}Nenhum cofre Obsidian foi localizado. O KAWA-AI continuará sem memória persistente nesta sessão.{Colors.RESET}")
            return None
    elif args.obsidian_vault:
        selected = str(Path(selected).expanduser().resolve())
        if config.get("obsidian_vault") and config.get("obsidian_vault") != selected:
            print(f"{Colors.WARNING}O cofre persistente só muda por seleção explícita. Atualizando para o caminho informado.{Colors.RESET}")
        config["obsidian_vault"] = selected
        save_config(config)

    try:
        memory = ObsidianMemory(selected, context_chars=int(config.get("memory_context_chars", 6_000)))
        diary = memory.initialize()
        print(f"{Colors.GREEN}Diário Obsidian ativo: {diary}{Colors.RESET}")
        return memory
    except ObsidianMemoryError as exc:
        print(f"{Colors.WARNING}Memória Obsidian não ativada: {exc}{Colors.RESET}")
        return None


def handle_connections(args):
    """Processa as conexões antes de iniciar provedores, modelos ou tarefas."""
    store = ConnectionStore()
    try:
        if args.connections:
            records = store.list_connections()
            if not records:
                print("Nenhuma conexão local registrada.")
                return True
            print(json.dumps(records, ensure_ascii=False, indent=2))
            return True
        if args.connection_set_token:
            service = args.connection_set_token
            token = getpass.getpass(f"Token oficial de {service} (não será exibido): ")
            scopes = [scope.strip() for scope in (args.connection_scopes or "").split(",") if scope.strip()]
            store.set_token(service, token, scopes)
            print(f"Conexão por token registrada para: {store.normalize_service(service)}")
            return True
        if args.connection_remove:
            service = store.normalize_service(args.connection_remove)
            answer = input(f"Remover localmente token e perfil de navegador de '{service}'? [s/N]: ").strip().lower()
            if answer not in {"s", "sim", "y", "yes"}:
                print("Remoção cancelada.")
                return True
            print("Conexão removida." if store.remove(service) else "Nenhuma conexão local encontrada para esse serviço.")
            return True
        if args.connection_set_endpoint:
            if not args.connection_endpoint:
                print("Informe --connection-endpoint https://... junto do serviço.")
                return True
            store.set_endpoint(args.connection_set_endpoint, args.connection_endpoint)
            print(f"Endpoint registrado para: {store.normalize_service(args.connection_set_endpoint)}")
            return True
    except ConnectionError as exc:
        print(f"Erro de conexão: {exc}")
        return True
    return False

def main():
    parser = argparse.ArgumentParser(description="KAWA-AI: Sistema Multiagente de Terminal")
    parser.add_argument("task", nargs="*", help="Tarefa a ser executada")
    parser.add_argument("--multiagent", action="store_true", help="Ativa a equipe multiagente com debate e atraso de 50s")
    parser.add_argument("--delay", type=int, default=50, help="Atraso em segundos entre cada agente no modo multiagente")
    parser.add_argument("--provider", type=str, help="Provedor de LLM")
    parser.add_argument("--model", type=str, help="Modelo")
    parser.add_argument("--api-key", type=str, help="Chave de API")
    parser.add_argument("--workspace", type=str, help="Diretório permitido para edições no modo workspace")
    parser.add_argument("--policy", choices=["observe", "ask", "workspace", "proactive"], help="Política de ferramentas")
    parser.add_argument("--max-iterations", type=int, default=0, help="Máximo de ciclos; 0 segue até resposta final com proteção contra repetição")
    parser.add_argument("--interactive", action="store_true", help="Abre conversa local interativa")
    parser.add_argument("--knowledge", type=str, help="Consulta um assunto pelo módulo de conhecimento")
    parser.add_argument("--knowledge-save", action="store_true", help="Salva a consulta no cofre local Markdown")
    parser.add_argument("--knowledge-campaign-init", action="store_true", help="Inicializa localmente a campanha auditável de conhecimento por lotes")
    parser.add_argument("--knowledge-campaign-status", action="store_true", help="Exibe a cobertura e os lotes válidos da campanha de conhecimento")
    parser.add_argument("--knowledge-campaign-plan", type=str, help="Planeja um lote sem gerar conteúdo, por exemplo ALL ou NAT")
    parser.add_argument("--knowledge-campaign-size", type=int, default=250, help="Tamanho planejado do lote de conhecimento (1 a 1000)")
    parser.add_argument("--knowledge-campaign-root", type=str, help="Pasta local da campanha; padrão ~/.kawa-ai/knowledge-campaign")
    parser.add_argument("--knowledge-vault", type=str, help="Pasta local do cofre de conhecimento")
    parser.add_argument("--auto-route", action="store_true", help="Envia perguntas factuais ao cérebro de conhecimento")
    parser.add_argument("--obsidian-vault", type=str, help="Seleciona explicitamente o único cofre Obsidian")
    parser.add_argument("--scan-vault", action="store_true", help="Procura um cofre Obsidian nos locais locais padrão")
    parser.add_argument("--scan-root", type=str, help="Raiz alternativa para a descoberta de cofre, por exemplo /")
    parser.add_argument("--init-obsidian", action="store_true", help="Inicializa ou verifica o diário Obsidian vazio e sai")
    parser.add_argument("--index-vault", action="store_true", help="Exibe metadados de notas Markdown do cofre selecionado")
    parser.add_argument("--memory-context-chars", type=int, help="Máximo de caracteres recentes recuperados do diário")
    parser.add_argument("--browser", action="store_true", help="Registra ferramentas para controlar um Chromium local isolado")
    parser.add_argument("--browser-headless", action="store_true", help="Executa o Chromium isolado sem janela visível")
    parser.add_argument("--browser-executable", type=str, help="Caminho explícito para Chromium ou Chrome já instalados")
    parser.add_argument("--browser-service", type=str, help="Nome do serviço cujo perfil isolado será preservado")
    parser.add_argument("--connections", action="store_true", help="Lista conexões locais sem mostrar tokens ou cookies")
    parser.add_argument("--connection-set-token", type=str, help="Salva um token oficial no cofre de credenciais do sistema")
    parser.add_argument("--connection-scopes", type=str, help="Escopos separados por vírgula para documentação local")
    parser.add_argument("--connection-remove", type=str, help="Remove uma conexão local e o perfil isolado do serviço")
    parser.add_argument("--connection-set-endpoint", type=str, help="Salva endpoint HTTPS não secreto de uma conexão")
    parser.add_argument("--connection-endpoint", type=str, help="Endpoint HTTPS vinculado a --connection-set-endpoint")
    parser.add_argument("--nvidia-research", type=str, help="Consulta modelos NVIDIA em poucos quadros sequenciais e sai")
    parser.add_argument("--nvidia-models", type=str, help="Lista opcional de IDs NVIDIA separados por vírgula")
    parser.add_argument("--nvidia-max-models", type=int, default=3, help="Máximo de modelos NVIDIA por investigação (1 a 4)")
    parser.add_argument("--supabase-store", action="store_true", help="Persiste explicitamente o resultado NVIDIA aprovado no Supabase")
    parser.add_argument("--supabase-table", type=str, default="kawa_knowledge", help="Tabela Supabase para resultados aprovados")
    parser.add_argument("--supabase-check", action="store_true", help="Verifica endpoint, token e leitura Supabase sem gravar dados")
    parser.add_argument("--supabase-setup", action="store_true", help="Configura endpoint e token Supabase no cofre local por prompt oculto e verifica somente leitura")
    parser.add_argument("--supabase-endpoint", type=str, help="Endpoint HTTPS usado junto de --supabase-setup")
    parser.add_argument("--media", action="store_true", help="Registra análise local de vídeo e transcrição por whisper.cpp")
    parser.add_argument("--extract-frames", type=str, help="Extrai quadros de um vídeo e sai")
    parser.add_argument("--frame-rate", type=float, default=0.2, help="Quadros por segundo na extração local (0,05 a 2)")
    parser.add_argument("--transcribe", type=str, help="Transcreve mídia por whisper.cpp e sai")
    parser.add_argument("--whisper-model", type=str, help="Caminho de modelo ggml para whisper.cpp")
    parser.add_argument("--quality", action="store_true", help="Registra auditoria local de código com ferramentas estáticas")
    parser.add_argument("--quality-audit", type=str, help="Audita arquivo ou diretório dentro da área de trabalho e sai")
    parser.add_argument("--quality-tools", type=str, default="ruff,bandit,semgrep", help="Ferramentas separadas por vírgula: ruff,bandit,semgrep")
    parser.add_argument("--design", action="store_true", help="Registra criação local de briefs e arquiteturas de design")
    parser.add_argument("--design-brief", type=str, help="Cria brief e arquitetura Mermaid para um pedido de design e sai")
    parser.add_argument("--design-medium", type=str, default="produto-digital", help="Meio do design: site, app, apresentação, social ou produto-digital")
    parser.add_argument("--voice-listen", action="store_true", help="Grava e transcreve um comando de voz local (Vosk) e sai")
    parser.add_argument("--voice-duration", type=float, default=8.0, help="Duração da gravação em segundos (padrão 8)")
    parser.add_argument("--voice-say", type=str, help="Fala o texto localmente (Piper) e sai")
    parser.add_argument("--rag", action="store_true", help="Ativa memória semântica local (SQLite + Ollama nomic-embed-text)")
    parser.add_argument("--rag-db", type=str, default="~/.kawa-ai/rag.sqlite3", help="Arquivo SQLite da memória semântica")
    parser.add_argument("--pentest", action="store_true", help="Registra auditoria ética de projetos locais já autorizados")
    parser.add_argument("--pentest-init", type=str, help="Inicializa o escopo ético para um diretório dentro da área de trabalho")
    parser.add_argument("--pentest-audit", type=str, help="Audita um escopo ético já inicializado e salva evidências locais")
    parser.add_argument("--pentest-authorized", action="store_true", help="Confirma que você possui autorização para inicializar o escopo de pentest")
    parser.add_argument("--adversary", action="store_true", help="Registra simulação de adversário e modelagem de ameaças OWASP/MITRE")
    parser.add_argument("--adversary-simulate", type=str, help="Executa modelagem de ameaças e hardening preventivo em um diretório e sai")
    parser.add_argument("--env-check", action="store_true", help="Exibe diagnóstico de ambiente (Mint vs Termux sem root) e sai")
    parser.add_argument("--tor-proxy", type=str, help="Define proxy SOCKS opcional para requisições de pesquisa, ex: socks5h://127.0.0.1:9050")
    parser.add_argument("--skills-catalog", action="store_true", help="Exibe o catálogo versionado de skills e o resumo de cobertura e sai")
    parser.add_argument("--ui", action="store_true", help="Abre a interface conversacional local do KAWA-AI")
    parser.add_argument("--autonomous", action="store_true", help="Planeja e executa a tarefa ponta a ponta, escolhendo skills automaticamente")
    
    args = parser.parse_args()
    config = load_config()

    if handle_connections(args):
        return
    
    if args.provider:
        config["provider"] = args.provider
    if args.model:
        config["model"] = args.model
    if args.api_key:
        config["api_key"] = args.api_key
    if args.workspace:
        config["workspace"] = args.workspace
    if args.policy:
        config["policy_mode"] = args.policy
    if args.knowledge_vault:
        config["knowledge_vault"] = args.knowledge_vault
    if args.memory_context_chars:
        config["memory_context_chars"] = args.memory_context_chars
    if args.browser_executable:
        config["browser_executable"] = args.browser_executable

    print(f"\n{Colors.HEADER}{Colors.BOLD}=== KAWA-AI (Multiagent Terminal System) ==={Colors.RESET}")
    print(f"  Provedor principal: {Colors.CYAN}{config.get('provider', 'nvidia')}{Colors.RESET}")
    print(f"  Modelo:             {Colors.CYAN}{config.get('model', 'padrão')}{Colors.RESET}\n")

    task_str = " ".join(args.task).strip()
    if not task_str and not args.interactive and not args.ui and not args.knowledge and not args.knowledge_campaign_init and not args.knowledge_campaign_status and not args.knowledge_campaign_plan and not args.init_obsidian and not args.index_vault and not args.extract_frames and not args.transcribe and not args.voice_listen and not args.voice_say and not args.nvidia_research and not args.supabase_check and not args.supabase_setup and not args.quality_audit and not args.design_brief and not args.pentest_init and not args.pentest_audit and not args.adversary_simulate and not args.env_check and not args.skills_catalog:
        # A experiência principal é conversacional: `kawa` sem argumentos abre a TUI.
        args.ui = True

    try:
        if args.ui:
            from ui.app import run_ui
            run_ui(config, args.workspace)
            return
        media = MediaToolkit(config.get("workspace", Path.cwd()))
        quality = QualityToolkit(config.get("workspace", Path.cwd()))
        design = DesignToolkit(config.get("workspace", Path.cwd()))
        pentest = EthicalPentestToolkit(config.get("workspace", Path.cwd()), quality=quality)
        adversary = AdversarySimulation(config.get("workspace", Path.cwd()))
        secure_site = SecureSiteCycle(config.get("workspace", Path.cwd()))
        knowledge_campaign = KnowledgeCampaign(args.knowledge_campaign_root)
        if args.extract_frames:
            print(media.extract_frames(args.extract_frames, args.frame_rate))
            return
        if args.transcribe:
            print(media.transcribe(args.transcribe, args.whisper_model))
            return
        if args.voice_say:
            speak(args.voice_say)
            return
        if args.voice_listen:
            print(listen(args.voice_duration))
            return
        if args.supabase_check:
            print(json.dumps(SupabaseKnowledgeStore().check(args.supabase_table), ensure_ascii=False, indent=2))
            return
        if args.supabase_setup:
            endpoint = args.supabase_endpoint or input("Project URL do Supabase (https://...): ").strip()
            token = getpass.getpass("Chave Supabase local (não será exibida): ")
            print(json.dumps(SupabaseKnowledgeStore().configure(endpoint, token, args.supabase_table), ensure_ascii=False, indent=2))
            return
        if args.quality_audit:
            selected_quality_tools = [item.strip() for item in args.quality_tools.split(",") if item.strip()]
            print(quality.audit(args.quality_audit, selected_quality_tools))
            return
        if args.design_brief:
            print(design.create_brief(args.design_brief, args.design_medium))
            return
        if args.pentest_init:
            print(pentest.initialize_scope(args.pentest_init, args.pentest_authorized))
            return
        if args.pentest_audit:
            selected_quality_tools = [item.strip() for item in args.quality_tools.split(",") if item.strip()]
            print(pentest.audit(args.pentest_audit, selected_quality_tools))
            return
        if args.adversary_simulate:
            print(adversary.simulate(args.adversary_simulate))
            return
        if args.env_check:
            print(json.dumps(EnvironmentInspector.inspect(), ensure_ascii=False, indent=2))
            return
        if args.skills_catalog:
            print(SkillsCatalog.render_report())
            return
        if args.knowledge_campaign_init:
            print(json.dumps(knowledge_campaign.initialize(), ensure_ascii=False, indent=2))
            return
        if args.knowledge_campaign_status:
            knowledge_campaign.initialize()
            print(knowledge_campaign.render_status())
            return
        if args.knowledge_campaign_plan:
            knowledge_campaign.initialize()
            print(json.dumps(knowledge_campaign.preview_batch(args.knowledge_campaign_plan, args.knowledge_campaign_size), ensure_ascii=False, indent=2))
            return
        if args.nvidia_research:
            requested = [model.strip() for model in (args.nvidia_models or "").split(",") if model.strip()]
            report = NvidiaResearch().render(
                NvidiaResearch().consult(args.nvidia_research, requested_models=requested or None, maximum=args.nvidia_max_models)
            )
            if args.supabase_store:
                SupabaseKnowledgeStore().save_research(args.nvidia_research, report, args.supabase_table)
                report += "\n\nResultado salvo no Supabase por solicitação explícita."
            print(report)
            return

        memory = resolve_obsidian_memory(args, config)
        if args.init_obsidian:
            if memory:
                print("Diário verificado sem criar uma segunda nota.")
                return
            sys.exit(2)
        if args.index_vault:
            if not memory:
                sys.exit(2)
            print(json.dumps(memory.markdown_index(), ensure_ascii=False, indent=2))
            return

        main_provider = get_provider(config)
        knowledge_brain = KnowledgeBrain(
            main_provider,
            web_search,
            vault_path=config.get("knowledge_vault"),
            memory=memory,
        )

        if args.knowledge:
            print(knowledge_brain.inquire(args.knowledge, persist=args.knowledge_save))
            return

        router = TaskRouter()
        if args.auto_route and router.route(task_str) is TaskRoute.KNOWLEDGE:
            print(knowledge_brain.inquire(task_str, persist=True))
            return

        if args.multiagent:
            # Configura a equipe de especialistas que leem o transcript uns dos outros
            team_config = [
                {"name": "Nexus", "role": "Orquestrador e Analista de Requisitos (Define o escopo e direciona o time)", "provider": main_provider},
                {"name": "SecOps", "role": "Especialista em Cibersegurança e Hardening (Analisa riscos, vulnerabilidades e protege o sistema)", "provider": main_provider},
                {"name": "DevForge", "role": "Arquiteto de Software Full-Stack (Cria código limpo, leve e sem custo de infraestrutura)", "provider": main_provider},
                {"name": "GrowthOps", "role": "Estrategista de Operações e Divulgação (Planeja hospedagem gratuita e tráfego orgânico)", "provider": main_provider}
            ]
            orchestrator = MultiAgentOrchestrator(team_config, delay=args.delay)
            result = orchestrator.run_workflow(task_str)
            print(f"\n{Colors.GREEN}{Colors.BOLD}=== Resultado Final da Equipe ==={Colors.RESET}\n{result}\n")
        else:
            policy = ToolPolicy(mode=config.get("policy_mode", "ask"), workspace=config.get("workspace"))
            rag = LocalRag(args.rag_db) if args.rag else None
            if rag:
                print(f"  {Colors.CYAN}Memória semântica local: {rag.stats()['entries']} trechos indexados{Colors.RESET}")
            agent = Agent(provider=main_provider, max_iterations=args.max_iterations, policy=policy, memory=memory, rag=rag)
            browser_profile = config.get("browser_profile_dir")
            if args.browser_service:
                browser_profile = ConnectionStore().register_browser_profile(args.browser_service)
            browser = BrowserTool(
                browser_profile,
                headless=args.browser_headless,
                executable_path=config.get("browser_executable"),
            ) if args.browser else None
            register_all_tools(agent, knowledge_brain=knowledge_brain, knowledge_campaign=knowledge_campaign, browser=browser, media=media, quality=quality, design=design, pentest=pentest, adversary=adversary, skill_builder=SkillBuilder(config.get("workspace", Path.cwd())), cybersecurity_catalog=CybersecurityReferenceCatalog(), secure_site=secure_site)
            if args.interactive:
                print("Modo interativo. Digite 'sair' para encerrar.")
                while True:
                    prompt = input(f"{Colors.CYAN}você>{Colors.RESET} ").strip()
                    if prompt.lower() in {"sair", "exit", "quit"}:
                        break
                    if not prompt:
                        continue
                    if args.auto_route and router.route(prompt) is TaskRoute.KNOWLEDGE:
                        print(f"\n{Colors.BLUE}{Colors.BOLD}Cérebro de conhecimento:{Colors.RESET}\n"
                              f"{knowledge_brain.inquire(prompt, persist=True)}\n")
                        continue
                    result = TaskOrchestrator(config.get("workspace", Path.cwd())).run(prompt, agent).render() if args.autonomous else agent.run(prompt)
                    print(f"\n{Colors.BLUE}{Colors.BOLD}KAWA-AI:{Colors.RESET}\n{result}\n")
            else:
                result = TaskOrchestrator(config.get("workspace", Path.cwd())).run(task_str, agent).render() if args.autonomous else agent.run(task_str)
                print(f"\n{Colors.BLUE}{Colors.BOLD}Resultado:{Colors.RESET}\n{result}\n")

    except (ConnectionError, NvidiaResearchError, SupabaseMemoryError, MediaError, QualityError, DesignError, PentestError, AdversaryError, SecureSiteError, KnowledgeCampaignError, VoiceError, RagError) as e:
        print(f"{Colors.FAIL}Erro de integração: {str(e)}{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.FAIL}Erro crítico: {str(e)}{Colors.RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()
