# Leviatã

![Loop visual do Leviatã](assets/leviata-loop.svg)

<p align="center">
  <img src="assets/kawa-ai-reference.jpeg" alt="Painel técnico do Leviatã com núcleo de orquestração e módulos locais" width="100%" />
</p>

> **Agente local para Terminal Linux** · memória, planejamento, auditoria e provedores de LLM configuráveis.

**Leviatã** é uma ferramenta local para Linux Mint e Termux que ajuda a organizar tarefas técnicas em linguagem natural. Ele trabalha dentro de políticas locais, registra ações com dados sensíveis redigidos, usa memória persistente opcional e pode operar com modelos locais via Ollama ou provedores configurados pelo proprietário.

## Capacidades

| Área | O que o Leviatã faz |
|---|---|
| Orquestração | Interpreta pedidos com linguagem informal, seleciona recursos e registra o fluxo local. |
| Código e qualidade | Lê e edita arquivos conforme política, cria briefs e executa revisões estáticas no workspace. |
| Segurança | Mantém referências defensivas, modelagem de ameaças, ciclo seguro para sites locais e auditorias autorizadas. |
| Conhecimento | Integra pesquisa, cofre Obsidian, campanha auditável por lotes e persistência opt-in. |
| Recursos | Ajusta trabalhadores, lotes e contexto à memória disponível sem alterar RAM, swap ou processos externos. |

## Instalação rápida

```bash
curl -fsSL https://raw.githubusercontent.com/LEVIATAD21/leviata/master/install.sh | bash
```

Depois, reinicie o terminal e abra a conversa com:

```bash
leviata
```

O comando `kawa` continua como compatibilidade para instalações anteriores, mas `leviata` é a entrada principal. Em terminais, o nome do comando é sem acento para facilitar a digitação; a identidade do projeto permanece **Leviatã**.

## Uso cotidiano

```bash
leviata
leviata "crie e teste um site de portfólio"
leviata --autonomous "revise este projeto Python"
leviata --memory-budget
```

Sem argumentos, o Leviatã abre a interface conversacional local. A ordem pode ser informal: ele identifica o objetivo, pré-seleciona as capacidades pertinentes e segue as políticas configuradas.

## Configuração local

O arquivo principal fica em `~/.leviata-ai/config.json`. Instalações anteriores em `~/.kawa-ai` são migradas pelo instalador, preservando configuração, memória e conexões locais.

```json
{
  "provider": "ollama",
  "model": "qwen2.5:1.5b",
  "base_url": "http://localhost:11434",
  "policy_mode": "ask",
  "workspace": "~/Projetos"
}
```

Para o computador atual, o perfil local leve com `qwen2.5:1.5b` é o ponto de partida recomendado. O governador de recursos classifica automaticamente máquinas com até 16 GiB como ambiente pessoal e máquinas acima desse limite como servidor, reduzindo somente a carga do Leviatã quando houver pressão de memória.

## Segurança, privacidade e autonomia

O Leviatã separa consultas de ações que alteram arquivos, serviços ou contas. Os modos `observe`, `ask`, `workspace` e `proactive` determinam o que é permitido, confirmado ou bloqueado. Ações externas, irreversíveis ou sensíveis continuam exigindo confirmação.

O projeto inclui o ciclo local de site seguro, referências classificadas de cibersegurança, hardening para LLMs, RAG, agentes e MCP, além de avaliações locais ou de escopo formalmente autorizado. Ele não publica projetos, não abre portas públicas, não executa ataques de rede e não transforma payloads ou métodos de jailbreak em capacidade operacional.

## Memória e conexões

O Leviatã pode localizar um único cofre Obsidian e manter um diário persistente. Tokens oficiais são solicitados em prompt oculto e guardados localmente por meio do cofre de credenciais do sistema quando disponível; não são versionados nem exibidos nos relatórios.

Use `--browser-service nome-do-serviço` para criar um perfil de navegador isolado e persistente. Use `--connection-remove` apenas quando desejar remover explicitamente uma conexão local.

## Projetos e documentação

| Documento | Conteúdo |
|---|---|
| [`DIRETRIZES.md`](DIRETRIZES.md) | Regras locais de comportamento e limites operacionais. |
| [`docs/AI_SECURITY_SKILLS_ASSESSMENT.md`](docs/AI_SECURITY_SKILLS_ASSESSMENT.md) | Referências verificadas de segurança de IA e critérios de uso. |
| [`docs/DESIGN_REFERENCE_ASSESSMENT.md`](docs/DESIGN_REFERENCE_ASSESSMENT.md) | Referências de UX, acessibilidade e design systems. |
| [`docs/MEMORY_GOVERNOR.md`](docs/MEMORY_GOVERNOR.md) | Política adaptativa de recursos. |
| [`docs/SECURE_SITE_CYCLE.md`](docs/SECURE_SITE_CYCLE.md) | Ciclo local de criação e revisão segura de sites. |

## Instalação manual

```bash
git clone https://github.com/LEVIATAD21/leviata.git
cd leviata
pip3 install -r requirements.txt
python3 main.py
```

---

*Desenvolvido por Kawã Silva dos Santos. Projeto privado, mantido com foco em autonomia local, aprendizado contínuo e evolução responsável.*
