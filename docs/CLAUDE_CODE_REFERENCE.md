# Referência: padrões inspirados no free-claude-code

O repositório [free-claude-code](https://github.com/Alishahryar1/free-claude-code), distribuído sob licença MIT, foi avaliado somente como referência de arquitetura. O KAWA-AI não copia suas credenciais, não executa seu instalador e não promete acesso gratuito ou ilimitado a provedores externos.

## Padrões aproveitados

| Padrão observado | Adaptação no KAWA-AI |
|---|---|
| Catálogo de provedores e modelos | Provedor local continua principal; NVIDIA entra somente como pesquisa consultiva opcional. |
| Sessão persistente | Perfil isolado por serviço e cofre local de tokens, com remoção explícita. |
| Respostas em streaming e ferramentas | Loop ReAct local já existente, com política, auditoria e confirmações. |
| Estimativa de contexto | Diário Obsidian, janela limitada de memória e investigação segmentada em quadros. |

## Limite de contexto e uso

Nenhum software pode remover os limites reais de contexto, taxa, orçamento ou política do modelo escolhido. Em vez de prometer "tokens ilimitados", o KAWA-AI reduz perda de contexto com três mecanismos: diário contínuo no Obsidian, recuperação de uma janela recente e pesquisas divididas em quadros curtos. O tamanho máximo de saída NVIDIA está limitado a 1.200 tokens por quadro e cada investigação consulta no máximo quatro modelos; esses limites são deliberados para evitar latência excessiva e respostas repetitivas.

## Crédito

Esta referência reconhece o projeto [Alishahryar1/free-claude-code](https://github.com/Alishahryar1/free-claude-code) e sua licença MIT. A implementação do KAWA-AI permanece independente e orientada pelas permissões locais do proprietário.
