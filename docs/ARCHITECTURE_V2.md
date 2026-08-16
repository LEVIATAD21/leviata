# Arquitetura v2 — KAWA-AI local

## Objetivo

O KAWA-AI deve ser um assistente de terminal local, modular e orientado a ferramentas. Ele não promete capacidade ilimitada: cada ação depende do modelo configurado, do hardware disponível, da rede, dos serviços externos e das permissões que o proprietário conceder.

No computador de referência, com 7,2 GB de RAM e GPU Intel integrada, a prioridade é estabilidade por CPU. O perfil padrão é `qwen2.5:1.5b` (986 MB em Q4_K_M) para conversa e planejamento; `qwen2.5-coder:1.5b` é o perfil alternativo para código. O perfil de qualidade `qwen2.5:3b` só deve ser usado quando houver memória livre adicional.

## Componentes

| Componente | Responsabilidade | Persistência |
|---|---|---|
| CLI | Recebe tarefa, escolhe provedor e expõe modos de execução | Nenhuma |
| Provider adapter | Uniformiza Ollama, APIs OpenAI-compatíveis e provedores opcionais | Configuração local sem chaves no repositório |
| Agent loop | Mantém o contexto ativo, valida chamadas de ferramenta e encerra ciclos | Histórico da sessão |
| Context manager | Redige segredos, limita resultados, seleciona contexto e compacta histórico antigo | Configuração local |
| Skill registry | Carrega skills Markdown relevantes ao pedido sem expor todo o catálogo | `skills/` e `~/.kawa-ai/skills/` |
| Tool registry | Expõe pesquisa, leitura, escrita, terminal, navegador e multimodalidade sob schema explícito | Nenhuma |
| Policy guard | Classifica ações em leitura, alteração e risco elevado; solicita confirmação quando configurado | Arquivo de política local |
| Audit log | Registra ferramenta, argumentos redigidos, resultado resumido e status | JSONL local |
| Web gateway | Consulta SearXNG local quando configurado; usa fonte pública de contingência e fetch com timeouts | Cache opcional de consulta |
| Media pipeline | Extrai frames com timestamps, transcreve localmente e envia amostras ao provider somente após confirmação | `kawa-media/` |
| Vision adapter | Analisa imagens e gera assets por provedores compatíveis configurados | Workspace e serviço autorizado |

## Política de ferramentas

As ferramentas não devem executar texto do modelo sem validação. Cada chamada precisa ter nome reconhecido, argumentos no formato esperado e um registro no log. Operações de leitura podem ocorrer automaticamente. Escritas e comandos de alto impacto devem respeitar o modo escolhido pelo proprietário:

| Modo | Leitura e pesquisa | Escrita no projeto | Instalação, rede externa e remoção |
|---|---|---|---|
| `observe` | Permitidas | Bloqueadas | Bloqueadas |
| `ask` | Permitidas | Confirmação no terminal | Confirmação no terminal |
| `workspace` | Permitidas | Permitidas apenas no diretório de trabalho | Confirmação no terminal |
| `proactive` | Permitidas | Permitidas no workspace | Multimodalidade externa, navegador mutável, publicação, remoção e credenciais continuam confirmadas |

O modo padrão será `ask`. Isso não impede automação local; torna cada ação verificável e permite que o proprietário altere a política conscientemente.

## Pesquisa web

SearXNG pode expor uma API HTTP em JSON quando auto-hospedado e configurado para isso. Instâncias públicas podem restringir formatos ou aplicar limites; portanto, o gateway deve tratar falhas e não prometer pesquisa ilimitada. [1]

Ollama expõe a API local padrão em `http://localhost:11434/api` e documenta ciclos de chamadas de ferramenta, que podem substituir o protocolo frágil de tags XML/JSON do núcleo atual. [2] [3]

## Plano de implementação

1. Criar uma política local, log de auditoria e diretório de trabalho explícito.
2. Corrigir o modo interativo prometido pelo README e reduzir o contexto da sessão.
3. Adaptar as ferramentas para validar caminhos, schemas, timeouts e limites de resultado.
4. Adicionar um gateway SearXNG configurável com fallback atual.
5. Criar testes unitários para políticas, caminhos e roteamento de ferramentas.
6. Adicionar skills carregadas seletivamente, compactação de contexto e redaction antes do provider.
7. Integrar análise multimodal de imagens e vídeo local com manifesto, timestamps e transcrição opcional.

## Princípios consolidados das referências

| Princípio | Incorporação no KAWA-AI | Decisão |
|---|---|---|
| Dados sob controle do usuário | Cofre Markdown local para relatórios e fontes | Adotado |
| Componentes substituíveis | Provider adapter para Ollama e APIs opcionais | Adotado |
| Speak → route → remember → repeat | Roteador leve: consulta factual vai ao cérebro de conhecimento; tarefa operacional permanece no agente principal | Adotado |
| Voz local | Futuro módulo opcional, desativado por padrão | Adiado para preservar RAM e CPU |
| Interface HUD | Futuro módulo opcional, sem substituir a CLI | Adiado para preservar simplicidade e recursos |
| Automação de dia inteiro | Não será habilitada automaticamente | Condicionada a regras, permissões e gatilhos explícitos |

## Referências

[1]: https://docs.searxng.org/dev/search_api.html "SearXNG — Search API"
[2]: https://docs.ollama.com/api/introduction "Ollama — API introduction"
[3]: https://docs.ollama.com/capabilities/tool-calling "Ollama — Tool calling"
