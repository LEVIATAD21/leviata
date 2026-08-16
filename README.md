# KAWA-AI 🤖

![Loop visual do KAWA-AI](assets/kawa-ai-loop.svg)

<p align="center">
  <img src="assets/kawa-ai-hero.png" alt="Ilustração do KAWA-AI como agente modular de terminal" width="100%" />
</p>

> Agente de IA Autônomo para Terminal Linux — Desenvolvido por Kawã Silva

Um assistente local para terminal Linux Mint, capaz de ler e criar arquivos, pesquisar fontes públicas, ajudar com código e executar ferramentas configuradas pelo proprietário. Suporta provedores por API e modelos locais via Ollama.

---

## ✨ Funcionalidades

- **Multi-LLM**: Troque o "cérebro" da IA quando quiser — OpenAI, Anthropic, Google Gemini, Ollama local ou API compatível configurada pelo proprietário
- **Execução de terminal com política local**: registra e confirma ações conforme o modo escolhido
- **Pesquisa web configurável**: usa SearXNG local quando disponível, com fallback público
- **Leitura e escrita de arquivos**: o modo `workspace` limita edições ao caminho definido
- **Loop de ferramentas validado**: planeja, valida as chamadas antes de executá-las e mantém contexto curto
- **Registro de auditoria**: salva ações em `~/.kawa-ai/logs/actions.jsonl`, com segredos redigidos
- **Perfis leves para CPU**: configuração inicial voltada a `qwen2.5:1.5b`
- **Interface bonita**: Terminal colorido e intuitivo

---

## 🚀 Instalação Rápida

```bash
curl -fsSL https://raw.githubusercontent.com/LEVIATAD21/manus-clone-ai/master/install.sh | bash
```

Depois, reinicie o terminal e use:
```bash
kawa
```

---

## ⚙️ Configuração Manual

Crie o arquivo `~/.kawa-ai/config.json`:

### Perfil local recomendado (Ollama)
```json
{
  "provider": "ollama",
  "model": "qwen2.5:1.5b",
  "base_url": "http://localhost:11434",
  "policy_mode": "ask",
  "workspace": "~/Projetos"
}
```

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

O fluxo principal é intencionalmente simples: execute apenas `kawa`. Sem argumentos, ele abre a interface conversacional local. Escreva o que você precisa em linguagem natural; o agente interpreta o objetivo, corrige ruídos leves de digitação, escolhe as capacidades necessárias, executa as etapas e apresenta o resultado.

```bash
kawa
```

Você também pode passar uma ordem diretamente, se preferir: `kawa "crie e teste um site de portfólio"`. A interface é o caminho recomendado; configurações avançadas permanecem opcionais e não são necessárias para conversar com o agente.

---

## 🛠️ Ferramentas Disponíveis

O agente seleciona automaticamente as ferramentas compatíveis com cada pedido, incluindo terminal, arquivos, pesquisa, navegador isolado, mídia, auditoria, design, pentest autorizado, modelagem de ameaças, memória e materialização local de documentação em skills.

Os modos de política são `observe` (somente consulta), `ask` (confirma escrita e comandos), `workspace` (permite edições no diretório definido) e `proactive` (avança em tarefas locais rotineiras, mantendo confirmações para ações externas, irreversíveis ou sensíveis).

`--knowledge` ativa um módulo de consulta separado do assistente principal. Ele pergunta o que é, como funciona, quais são os limites e como confirmar o assunto; em seguida, entrega uma síntese baseada na pesquisa. Com `--knowledge-save`, o relatório é registrado como Markdown em `~/.kawa-ai/knowledge/` (ou na pasta definida por `--knowledge-vault`), sem mudar a identidade ou as permissões do KAWA-AI.

Com `--auto-route`, perguntas explicativas são encaminhadas ao cérebro de conhecimento e salvas no cofre; solicitações operacionais continuam no agente principal e passam pela política local. O roteador é determinístico, não carrega outro modelo e pode ser desativado a qualquer momento.

### Cofre Obsidian persistente

Na primeira execução, o KAWA-AI procura diretórios `.obsidian` em toda a árvore local a partir de `/`, sem ler o conteúdo de notas. Diretórios dinâmicos, caches e dependências pesadas são excluídos. Se localizar somente um, salva o caminho em `~/.kawa-ai/config.json` e cria o arquivo vazio e único `KAWA-AI/Reasoning Diary.md`. A partir daí, a memória é sempre acrescentada no mesmo diário e cópias de recuperação permanecem no mesmo cofre. Caso existam vários cofres, o programa pede o caminho explicitamente em vez de escolher ou criar outro.

Para restringir uma nova procura a uma unidade ou caminho específico, use `--scan-root /caminho`. `--index-vault` mostra somente metadados de arquivos Markdown dentro do cofre escolhido.

### Navegador local controlado

O parâmetro `--browser` habilita um Chromium local com perfil isolado em `~/.kawa-ai/browser-profile`; ele não usa automaticamente os cookies ou sessões do navegador principal. O KAWA-AI procura primeiro `google-chrome`, `chromium` ou `chromium-browser` já instalados no Linux Mint, evitando o download do Playwright quando possível. Se o navegador estiver em outro caminho, use `--browser-executable /caminho/do/executavel` ou a variável `KAWA_BROWSER_EXECUTABLE`.

Se não houver navegador instalado, execute `PLAYWRIGHT_DOWNLOAD_CONNECTION_TIMEOUT=120000 python3 -m playwright install chromium` para aumentar o tempo de conexão do download. Abertura e leitura de páginas são separadas de cliques e preenchimento: no modo padrão `ask`, qualquer clique ou texto digitado exige confirmação e seus dados são redigidos do registro de auditoria. Não habilite o modo sem janela em fluxos que precisem de login manual ou revisão visual.

### Conexões persistentes

Use `--browser-service nome-do-serviço` para manter uma sessão web em um perfil isolado próprio até que seja removida por `--connection-remove nome-do-serviço`. Para APIs, `--connection-set-token` solicita o token sem eco no terminal, tenta guardá-lo no cofre de credenciais do sistema e salva somente nome, tipo, escopos e datas em `~/.kawa-ai/connections.json`. A função não armazena tokens, cookies ou senhas no repositório nem nos logs.

Serviços externos mantêm regras próprias de autorização e expiração. Instagram e Facebook, por exemplo, requerem login, permissões e APIs oficiais da Meta para ações de API; uma conexão local não contorna esses requisitos e pode precisar de renovação ou novo login. Consulte `docs/CONNECTIONS.md` antes de conectar uma conta.

### Mídia local e provedores opcionais

`--extract-frames` usa FFmpeg local para gerar uma amostra de quadros e um manifesto JSON dentro de `kawa-media/frames/` no diretório de trabalho. A taxa padrão é 0,2 fps, suficiente para investigação inicial sem criar milhares de imagens. `--transcribe` usa um executável local de `whisper.cpp` e um modelo ggml configurado em `KAWA_WHISPER_MODEL` ou informado por `--whisper-model`; nenhum áudio é enviado a terceiros nesse fluxo.

Hedra, MiniMax/Hailuo, Photoroom, n8n, NotebookLM Enterprise, Supabase e Remotion são módulos opcionais. As integrações comerciais dependem de conta, chave ou infraestrutura autorizada pelo proprietário; não são substituídas por automação de navegador ou por credenciais inexistentes. Leia `docs/INTEGRATION_RESEARCH.md` antes de ativar um provedor.

### Qualidade, programação e segurança defensiva

`--quality-audit` executa verificações estáticas dentro do diretório de trabalho e grava o relatório em `kawa-quality/`. Ruff verifica qualidade e formatação de Python; Bandit procura padrões comuns de segurança em Python; Semgrep executa regras estáticas para código. O módulo não explora sistemas, não realiza varredura de rede e não opera fora do diretório configurado. Instale apenas as ferramentas que quiser usar no ambiente local: `python3 -m pip install ruff bandit semgrep`.

### Pentest ético aprofundado

`--pentest-init` cria um arquivo de escopo local confirmando que o diretório foi autorizado para auditoria. Depois, `--pentest-audit` combina revisão estática local, evidências por regra, relatórios JSON e um diário de lições em `kawa-pentest/lessons.jsonl`. O módulo não faz exploração, ataques de credenciais, persistência, negação de serviço ou varredura de rede. A profundidade vem de repetir o ciclo **escopo → revisão → evidência → correção → nova revisão**, e não de testes fora da autorização.

### Interface conversacional local

Use `kawa-ui` ou `kawa --ui` para abrir a interface TUI local inspirada em fluxos modernos de agentes de terminal. Ela reúne conversa, modo plano, execução proativa, workspace, memória e catálogo de skills sem abrir servidor externo. `Ctrl+P` alterna entre plano e execução; `Ctrl+L` limpa a sessão; `/skills`, `/status` e `/help` exibem informações locais. A interface usa a biblioteca Python Textual e é instalada pelo `install.sh`.

### Orquestração ponta a ponta

Use `kawa --autonomous "<tarefa>"` para ativar o orquestrador. Ele cria um plano de capacidades, escolhe automaticamente as skills compatíveis com o pedido, pede ao agente que execute e valide as etapas, e grava um registro sanitizado em `kawa-workflows/`. A interface `kawa-ui` já usa esse fluxo por padrão. A seleção automática não ignora política local, escopo de pentest ou confirmações necessárias para operações externas e de alto impacto.

### Design estruturado

`--design-brief` gera um brief Markdown e um diagrama Mermaid editáveis em `kawa-design/`. Ele é uma etapa local de arquitetura e interface antes de iniciar um site, app, apresentação ou arte visual. Para imagens, vídeos e apresentações em provedores externos, o KAWA-AI continua usando apenas contas conectadas e uma solicitação específica do proprietário.

### Pesquisa NVIDIA e memória Supabase

Use `--nvidia-research` para obter poucos pareceres sequenciais de modelos disponíveis na sua conta NVIDIA. Cada resposta é entregue como um quadro de investigação, permitindo que o próximo modelo complemente ou critique o anterior. A chave é lida exclusivamente do cofre local criado por `--connection-set-token nvidia`; ela não aparece no comando, na auditoria, no Obsidian ou no repositório.

`--supabase-setup` é o assistente de conexão local: salva o endpoint HTTPS, pede o token por campo oculto e executa uma verificação somente de leitura. `--supabase-store` é opcional e salva somente o relatório que você acabou de solicitar. A tabela padrão é `kawa_knowledge` e deve aceitar as colunas `title`, `content`, `source` e `created_at`. Conteúdo com padrões de chave, token ou senha é redigido antes do envio.

O esquema reproduzível está em `docs/SUPABASE_SCHEMA.sql`. A tabela é criada com RLS ativo e sem políticas públicas: para este agente local, use uma credencial de servidor limitada ao projeto e guarde-a somente pelo prompt oculto de `--supabase-setup`; ela não deve ser colocada em arquivos `.env`, no Obsidian, no Git ou no chat.

O KAWA-AI não promete tokens ilimitados: cada modelo e serviço mantém limites próprios. Para não perder profundidade, ele usa diário Obsidian contínuo, contexto recente limitado e pesquisa dividida em quadros curtos. Consulte `docs/CLAUDE_CODE_REFERENCE.md` para os padrões de experiência adotados como referência.

### Modo proativo

`--policy proactive` reduz interrupções durante tarefas locais: ele permite escrita dentro do diretório de trabalho, verificações e processamento de mídia sem confirmar cada etapa. O programa continua pedindo confirmação para comandos de alto impacto, cliques e preenchimentos no navegador, publicação em serviços externos e operações que possam remover conteúdo, expor dados ou modificar uma conta. O objetivo é executar com iniciativa, sem tornar as ações opacas ou irreversíveis.

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
