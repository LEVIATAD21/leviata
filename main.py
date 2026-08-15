#!/usr/bin/env python3
"""
KAWA-AI — Agente de IA Autônomo e Sistema Multiagente para Terminal Linux
Suporta modo monoagente (ReAct) e modo equipe multiagente com atraso e transcript compartilhado.
"""
import os
import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agent.core import Agent
from agent.knowledge import KnowledgeBrain
from agent.policy import ToolPolicy
from agent.router import TaskRoute, TaskRouter
from agent.multiagent import MultiAgentOrchestrator
from providers import get_provider, OpenAIProvider
from tools import register_all_tools, web_search

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
    }
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config.update(json.load(f))
        except Exception:
            pass
    return config

def main():
    parser = argparse.ArgumentParser(description="KAWA-AI: Sistema Multiagente de Terminal")
    parser.add_argument("task", nargs="*", help="Tarefa a ser executada")
    parser.add_argument("--multiagent", action="store_true", help="Ativa a equipe multiagente com debate e atraso de 50s")
    parser.add_argument("--delay", type=int, default=50, help="Atraso em segundos entre cada agente no modo multiagente")
    parser.add_argument("--provider", type=str, help="Provedor de LLM")
    parser.add_argument("--model", type=str, help="Modelo")
    parser.add_argument("--api-key", type=str, help="Chave de API")
    parser.add_argument("--workspace", type=str, help="Diretório permitido para edições no modo workspace")
    parser.add_argument("--policy", choices=["observe", "ask", "workspace"], help="Política de ferramentas")
    parser.add_argument("--max-iterations", type=int, default=12, help="Máximo de ciclos por tarefa")
    parser.add_argument("--interactive", action="store_true", help="Abre conversa local interativa")
    parser.add_argument("--knowledge", type=str, help="Consulta um assunto pelo módulo de conhecimento")
    parser.add_argument("--knowledge-save", action="store_true", help="Salva a consulta no cofre local Markdown")
    parser.add_argument("--knowledge-vault", type=str, help="Pasta local do cofre de conhecimento")
    parser.add_argument("--auto-route", action="store_true", help="Envia perguntas factuais ao cérebro de conhecimento")
    
    args = parser.parse_args()
    config = load_config()
    
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

    print(f"\n{Colors.HEADER}{Colors.BOLD}=== KAWA-AI (Multiagent Terminal System) ==={Colors.RESET}")
    print(f"  Provedor principal: {Colors.CYAN}{config.get('provider', 'nvidia')}{Colors.RESET}")
    print(f"  Modelo:             {Colors.CYAN}{config.get('model', 'padrão')}{Colors.RESET}\n")

    task_str = " ".join(args.task).strip()
    if not task_str and not args.interactive and not args.knowledge:
        print(f"{Colors.WARNING}Uso em linha de comando:{Colors.RESET}")
        print(f"  python3 main.py --interactive")
        print(f"  python3 main.py --policy workspace --workspace ~/Projetos \"Revise este projeto\"")
        print(f"  python3 main.py \"Sua tarefa monoagente aqui\"\n")
        sys.exit(0)

    try:
        main_provider = get_provider(config)
        knowledge_brain = KnowledgeBrain(main_provider, web_search, vault_path=config.get("knowledge_vault"))

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
            agent = Agent(provider=main_provider, max_iterations=args.max_iterations, policy=policy)
            register_all_tools(agent, knowledge_brain=knowledge_brain)
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
                    result = agent.run(prompt)
                    print(f"\n{Colors.BLUE}{Colors.BOLD}KAWA-AI:{Colors.RESET}\n{result}\n")
            else:
                result = agent.run(task_str)
                print(f"\n{Colors.BLUE}{Colors.BOLD}Resultado:{Colors.RESET}\n{result}\n")

    except Exception as e:
        print(f"{Colors.FAIL}Erro crítico: {str(e)}{Colors.RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()
