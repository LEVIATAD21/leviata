# KAWA-AI 🤖
> Agente de IA Autônomo para Terminal Linux — Desenvolvido por Kawã Silva

Um agente de IA poderoso que roda diretamente no seu terminal Linux Mint, capaz de executar qualquer tarefa: instalar programas, criar arquivos, navegar na web, escrever código e muito mais. Suporta **qualquer LLM** via API.

---

## ✨ Funcionalidades

- **Multi-LLM**: Troque o "cérebro" da IA quando quiser — OpenAI, Anthropic, Google Gemini, Ollama (local/grátis) ou qualquer API customizada
- **Execução de Shell**: Executa qualquer comando Linux no seu PC
- **Navegação Web**: Acessa URLs e busca informações na internet
- **Leitura/Escrita de Arquivos**: Cria, lê e edita qualquer arquivo
- **Loop Autônomo**: Pensa, age e itera até completar a tarefa (ReAct)
- **Sem limite de contexto**: Gerencia o histórico automaticamente
- **Interface bonita**: Terminal colorido e intuitivo

---

## 🚀 Instalação Rápida

```bash
curl -fsSL https://raw.githubusercontent.com/LEVIATAD21/manus-clone-ai/main/install.sh | bash
```

Depois, reinicie o terminal e use:
```bash
kawa
```

---

## ⚙️ Configuração Manual

Crie o arquivo `~/.kawa-ai/config.json`:

### OpenAI (GPT-4o)
```json
{
  "provider": "openai",
  "api_key": "sk-...",
  "model": "gpt-4o"
}
```

### Anthropic (Claude)
```json
{
  "provider": "anthropic",
  "api_key": "sk-ant-...",
  "model": "claude-3-5-sonnet-20241022"
}
```

### Google Gemini
```json
{
  "provider": "google",
  "api_key": "AIza...",
  "model": "gemini-2.0-flash"
}
```

### Ollama (Local — GRÁTIS)
```bash
# Primeiro instale o Ollama:
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3
```
```json
{
  "provider": "ollama",
  "model": "llama3"
}
```

### API Customizada (qualquer API compatível com OpenAI)
```json
{
  "provider": "custom",
  "api_key": "SUA_CHAVE",
  "base_url": "https://api.sua-ia.com/v1",
  "model": "nome-do-modelo"
}
```

---

## 💬 Como Usar

```bash
# Chat interativo
kawa

# Tarefa direta
kawa "crie um script Python que lista todos os arquivos .mp3 na pasta Downloads"

# Usando um provedor específico
kawa --provider anthropic --model claude-3-5-sonnet-20241022 "sua tarefa"

# Usando Ollama local
kawa --provider ollama --model llama3
```

---

## 🛠️ Ferramentas Disponíveis

| Ferramenta | Descrição |
|---|---|
| `shell` | Executa qualquer comando no terminal Linux |
| `read_file` | Lê o conteúdo de qualquer arquivo |
| `write_file` | Cria ou edita arquivos |
| `web_search` | Busca informações na web (DuckDuckGo) |
| `web_fetch` | Acessa uma URL e retorna o conteúdo |

---

## 🔧 Instalação Manual (sem curl)

```bash
git clone https://github.com/LEVIATAD21/manus-clone-ai.git
cd manus-clone-ai
pip3 install -r requirements.txt
python3 main.py
```

---

## 📁 Estrutura do Projeto

```
manus-clone-ai/
├── main.py              # Ponto de entrada principal (CLI)
├── install.sh           # Script de instalação via curl
├── requirements.txt     # Dependências Python
├── agent/
│   ├── __init__.py
│   └── core.py          # Núcleo do agente (loop ReAct)
├── providers/
│   └── __init__.py      # Provedores de LLM (OpenAI, Anthropic, etc.)
├── tools/
│   └── __init__.py      # Ferramentas (shell, web, arquivos)
└── config/
    └── config.example.json  # Exemplo de configuração
```

---

## 🔒 Privacidade

Este repositório é **privado**. Apenas você tem acesso. Suas chaves de API ficam salvas localmente em `~/.kawa-ai/config.json` e **nunca** são enviadas para o repositório (arquivo ignorado pelo `.gitignore`).

---

*Desenvolvido por Kawã Silva — github.com/leviatad21*
