#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════╗
║           KAWA-AI - Agente de IA Autônomo para Terminal       ║
║           Desenvolvido por Kawã Silva | github.com/leviatad21 ║
╚═══════════════════════════════════════════════════════════════╝

Uso:
    python3 main.py                    # Inicia o chat interativo
    python3 main.py "sua tarefa aqui"  # Executa uma tarefa única
    python3 main.py --config /caminho/config.json
"""
import sys
import os
import json
import argparse
from pathlib import Path

# Cores para o terminal
class Colors:
    CYAN    = '\033[96m'
    GREEN   = '\033[92m'
    YELLOW  = '\033[93m'
    RED     = '\033[91m'
    BOLD    = '\033[1m'
    RESET   = '\033[0m'
    BLUE    = '\033[94m'
    MAGENTA = '\033[95m'

BANNER = f"""
{Colors.CYAN}{Colors.BOLD}
╔═══════════════════════════════════════════════════════════════╗
║                  KAWA-AI  v1.0.0                              ║
║          Agente de IA Autônomo para Terminal Linux            ║
╚═══════════════════════════════════════════════════════════════╝
{Colors.RESET}"""

def load_config(config_path: str = None) -> dict:
    """Carrega a configuração do agente."""
    # Ordem de busca: argumento > ~/.kawa-ai/config.json > ./config/config.json
    paths_to_try = []
    if config_path:
        paths_to_try.append(config_path)
    paths_to_try.append(os.path.expanduser("~/.kawa-ai/config.json"))
    paths_to_try.append(os.path.join(os.path.dirname(__file__), "config", "config.json"))

    for path in paths_to_try:
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)

    # Se não encontrou, pede ao usuário para configurar
    print(f"\n{Colors.YELLOW}⚠ Nenhuma configuração encontrada.{Colors.RESET}")
    print(f"Criando configuração em {Colors.CYAN}~/.kawa-ai/config.json{Colors.RESET}\n")
    
    print("Escolha seu provedor de IA:")
    print("  1. OpenAI (GPT-4o, GPT-4, etc.)")
    print("  2. Anthropic (Claude)")
    print("  3. Google (Gemini)")
    print("  4. Ollama (Modelos locais - GRÁTIS)")
    print("  5. API Customizada (qualquer API compatível com OpenAI)")
    
    choice = input("\nEscolha [1-5]: ").strip()
    
    providers = {"1": "openai", "2": "anthropic", "3": "google", "4": "ollama", "5": "custom"}
    provider = providers.get(choice, "openai")
    
    config = {"provider": provider}
    
    if provider == "ollama":
        model = input("Modelo Ollama [llama3]: ").strip() or "llama3"
        config["model"] = model
        config["base_url"] = "http://localhost:11434"
    elif provider == "custom":
        config["api_key"] = input("API Key: ").strip()
        config["base_url"] = input("Base URL (ex: https://api.exemplo.com/v1): ").strip()
        config["model"] = input("Nome do modelo: ").strip()
    else:
        models = {
            "openai": "gpt-4o",
            "anthropic": "claude-3-5-sonnet-20241022",
            "google": "gemini-2.0-flash"
        }
        config["api_key"] = input(f"API Key ({provider}): ").strip()
        default_model = models.get(provider, "")
        model = input(f"Modelo [{default_model}]: ").strip() or default_model
        config["model"] = model
    
    # Salva a configuração
    config_dir = os.path.expanduser("~/.kawa-ai")
    os.makedirs(config_dir, exist_ok=True)
    config_file = os.path.join(config_dir, "config.json")
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\n{Colors.GREEN}✓ Configuração salva em {config_file}{Colors.RESET}\n")
    return config


def create_agent(config: dict):
    """Cria e configura o agente com provedor e ferramentas."""
    from providers import get_provider
    from agent.core import Agent
    from tools import register_all_tools
    
    provider = get_provider(config)
    agent = Agent(provider=provider)
    register_all_tools(agent)
    return agent


def interactive_mode(agent):
    """Modo de chat interativo no terminal."""
    print(f"\n{Colors.GREEN}✓ Agente pronto! Digite sua tarefa ou 'sair' para encerrar.{Colors.RESET}")
    print(f"{Colors.YELLOW}Dica: Você pode pedir qualquer coisa — instalar programas, criar arquivos, buscar na web, etc.{Colors.RESET}\n")
    
    while True:
        try:
            user_input = input(f"{Colors.BOLD}{Colors.BLUE}Você:{Colors.RESET} ").strip()
            
            if not user_input:
                continue
            if user_input.lower() in ["sair", "exit", "quit", "q"]:
                print(f"\n{Colors.CYAN}Até mais! 👋{Colors.RESET}\n")
                break
            
            print(f"\n{Colors.MAGENTA}Agente:{Colors.RESET} Processando...\n")
            response = agent.run(user_input)
            print(f"\n{Colors.MAGENTA}Agente:{Colors.RESET} {response}\n")
            print(f"{Colors.CYAN}{'─' * 60}{Colors.RESET}")
            
        except KeyboardInterrupt:
            print(f"\n\n{Colors.CYAN}Interrompido. Até mais! 👋{Colors.RESET}\n")
            break
        except Exception as e:
            print(f"\n{Colors.RED}Erro: {str(e)}{Colors.RESET}\n")


def main():
    parser = argparse.ArgumentParser(
        description="KAWA-AI - Agente de IA Autônomo para Terminal Linux"
    )
    parser.add_argument("task", nargs="?", help="Tarefa a executar (opcional)")
    parser.add_argument("--config", help="Caminho para o arquivo de configuração")
    parser.add_argument("--provider", help="Provedor de LLM (openai, anthropic, google, ollama, custom)")
    parser.add_argument("--model", help="Modelo a usar")
    parser.add_argument("--api-key", help="API Key do provedor")
    args = parser.parse_args()
    
    print(BANNER)
    
    # Carrega configuração
    config = load_config(args.config)
    
    # Sobrescreve com argumentos de linha de comando se fornecidos
    if args.provider:
        config["provider"] = args.provider
    if args.model:
        config["model"] = args.model
    if args.api_key:
        config["api_key"] = args.api_key
    
    print(f"  Provedor: {Colors.CYAN}{config.get('provider', 'openai')}{Colors.RESET}")
    print(f"  Modelo:   {Colors.CYAN}{config.get('model', 'padrão')}{Colors.RESET}\n")
    
    # Cria o agente
    agent = create_agent(config)
    
    if args.task:
        # Modo de tarefa única
        print(f"{Colors.MAGENTA}Agente:{Colors.RESET} Processando...\n")
        response = agent.run(args.task)
        print(f"\n{Colors.MAGENTA}Agente:{Colors.RESET} {response}\n")
    else:
        # Modo interativo
        interactive_mode(agent)


if __name__ == "__main__":
    main()
