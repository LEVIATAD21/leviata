# Catálogo de Referências de Cibersegurança

O Leviatã incorpora o índice de metadados do projeto público [Anthropic Cybersecurity Skills](https://github.com/mukul975/anthropic-cybersecurity-skills), distribuído sob a licença Apache License 2.0. A cópia do índice e a atribuição de licença ficam em `agent/data/anthropic_cybersecurity_index.json` e `third_party/anthropic-cybersecurity-skills/`.

O catálogo contém 817 referências. Ele é usado como camada de **conhecimento consultivo**, não como conjunto de scripts executáveis. O Leviatã classifica cada referência de forma determinística antes de apresentá-la ao modelo.

| Classe | Uso no Leviatã |
|---|---|
| `defensiva` | Pode orientar análise, detecção, hardening, resposta a incidentes, forense e conformidade. |
| `escopo_autorizado` | Pode ser citado para planejamento, mas exige autorização escrita, escopo definido e regras de engajamento antes de qualquer teste. |
| `restrita` | Não é executada automaticamente nem convertida em instrução operacional. O agente a trata apenas como sinal de risco que requer contexto defensivo. |

## Regra de operação

Para pedidos de segurança, o orquestrador consulta `cybersecurity_reference` antes de `ethical_pentest` ou `adversary_simulate`. A ferramenta só pesquisa metadados locais; ela não baixa, interpreta ou executa scripts upstream. O pentest integrado ao Leviatã continua restrito ao workspace que possui escopo local autorizado.

## Atribuição

Fonte: <https://github.com/mukul975/anthropic-cybersecurity-skills>.

Licença upstream: Apache License 2.0. A cópia da licença e o aviso de atribuição acompanham o projeto em `third_party/anthropic-cybersecurity-skills/`.
