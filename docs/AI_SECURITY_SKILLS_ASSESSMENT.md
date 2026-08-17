# Avaliação de Referências de Segurança de IA

## Fontes verificadas

| Referência | Fonte oficial verificada | Uso previsto no Leviatã | Classificação inicial |
|---|---|---|---|
| MITRE ATLAS | [MITRE ATLAS](https://atlas.mitre.org/) | Modelagem de ameaças e priorização de mitigações em sistemas de IA | Referência; exige seleção defensiva |
| OWASP GenAI LLM Top 10 | [OWASP GenAI LLM Top 10 2026](https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/) | Checklist de hardening para agentes, LLMs e integrações | Defensiva |
| garak | [NVIDIA/garak](https://github.com/NVIDIA/garak) | Avaliação local e autorizada de falhas em modelos e interfaces LLM | Escopo autorizado; requer perfil restrito de testes |
| PyRIT | [microsoft/PyRIT](https://github.com/microsoft/PyRIT) | Identificação e documentação de risco em sistemas de IA generativa | Escopo autorizado; verificar projeto canônico antes de integrar |
| Promptfoo | [promptfoo/promptfoo](https://github.com/promptfoo/promptfoo) | Avaliação declarativa e testes de segurança de prompts, agentes e RAG locais | Escopo autorizado |
| ART | [Trusted-AI/adversarial-robustness-toolbox](https://github.com/Trusted-AI/adversarial-robustness-toolbox) | Avaliação de robustez e contramedidas em modelos próprios ou formalmente autorizados | Restrito a laboratório autorizado |
| CleverHans | [cleverhans-lab/cleverhans](https://github.com/cleverhans-lab/cleverhans) | Benchmark de robustez e defesas em modelos próprios de visão ou ML | Restrito a laboratório autorizado |
| Picklescan | [mmaitre314/picklescan](https://github.com/mmaitre314/picklescan) | Inspeção preventiva de artefatos Pickle e checkpoints antes de carregamento | Defensiva |

O MITRE ATLAS declara uma base viva de táticas e técnicas adversariais contra sistemas de IA, incluindo matriz de técnicas e mitigações. [^atlas] A página consultada da OWASP informa que a versão atual é a publicação GenAI LLM Top 10 de 2026 e que a página anterior é histórica. [^owasp] O garak se apresenta como um scanner de vulnerabilidades para LLMs e possui licença Apache-2.0; suas sondas devem ser reduzidas a conjuntos defensivos e executadas somente contra alvos locais ou formalmente autorizados. [^garak] O repositório `Azure/PyRIT` indica mudança para `microsoft/PyRIT`, portanto a integração deverá usar o destino canônico atualizado e confirmar sua documentação e licença. [^pyrit]

O Promptfoo possui licença MIT e declara suporte a avaliações e red teaming de aplicações LLM, incluindo execução local de avaliações. [^promptfoo] ART possui licença MIT e declara suporte tanto a avaliação quanto a defesa contra ameaças adversariais de ML; por isso só será incluído como referência para modelos próprios ou ambientes de laboratório autorizados. [^art] CleverHans também possui licença MIT, mas seu foco em implementações de exemplos adversariais exige a mesma limitação a benchmark e defesa de modelos sob controle do usuário. [^cleverhans]

Picklescan possui licença MIT e declara detectar ações suspeitas em arquivos Python Pickle; sua integração proposta é exclusivamente preventiva, para verificar artefatos de modelos antes do carregamento local. [^picklescan]

[^atlas]: [MITRE ATLAS — AI threat matrix](https://atlas.mitre.org/)
[^owasp]: [OWASP — GenAI LLM Top 10 2026](https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/)
[^garak]: [NVIDIA — garak](https://github.com/NVIDIA/garak)
[^pyrit]: [Microsoft — PyRIT](https://github.com/microsoft/PyRIT)
[^promptfoo]: [Promptfoo — LLM evals & red teaming](https://github.com/promptfoo/promptfoo)
[^art]: [Trusted AI — Adversarial Robustness Toolbox](https://github.com/Trusted-AI/adversarial-robustness-toolbox)
[^cleverhans]: [CleverHans Lab — CleverHans](https://github.com/cleverhans-lab/cleverhans)
[^picklescan]: [Picklescan — scanner de segurança de Pickle](https://github.com/mmaitre314/picklescan)

## Repositórios adicionais recebidos

| Repositório | Evidência verificada | Decisão de integração |
|---|---|---|
| [brinhosa/awesome-ai-security](https://github.com/brinhosa/awesome-ai-security) | Lista CC0-1.0 com ferramentas, padrões e recursos de segurança de IA; combina materiais defensivos com payloads e coleções de jailbreak. | Usar somente como índice de descoberta; incorporar apenas fontes oficiais e defensivas verificadas individualmente. |
| [yueliu1999/Awesome-Jailbreak-on-LLMs](https://github.com/yueliu1999/Awesome-Jailbreak-on-LLMs) | Lista MIT de artigos, códigos e conjuntos de dados para métodos de jailbreak. | Não integrar códigos, payloads, benchmarks ofensivos ou métodos de quebra de alinhamento. Registrar somente a categoria de risco para orientar controles defensivos. |
| [raj77in/awesome-ai-ml-pentesting](https://github.com/raj77in/awesome-ai-ml-pentesting) | Lista recente e de baixa maturidade declarada, com referências úteis e conteúdo ofensivo. | Não usar como autoridade ou instalar ferramentas listadas; aproveitar apenas referências canônicas já verificadas, como OWASP, MITRE e ferramentas aprovadas. |
| [man3kin3ko/awesome-adversarial-machine-learning](https://github.com/man3kin3ko/awesome-adversarial-machine-learning) | Lista CC0-1.0 de recursos AML, incluindo MITRE ATLAS, ART e CleverHans. | Cobertura já representada por MITRE ATLAS, ART e CleverHans; não requer cópia adicional. |

Essas decisões preservam valor de pesquisa sem transformar coleções de payloads ou métodos de quebra de alinhamento em capacidade operacional do agente.

## Fontes canônicas adicionais aprovadas

| Fonte | Uso no Leviatã | Classificação |
|---|---|---|
| [OWASP Top 10 for Agentic Applications 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/) | Modelo de riscos e mitigação para agentes que planejam, agem e tomam decisões em fluxos complexos. | Defensiva |
| [OWASP MCP Top 10](https://owasp.org/www-project-mcp-top-10/) | Hardening de credenciais, escopos, ferramentas, contexto, telemetria e dependências para ambientes MCP. | Defensiva |
| [OWASP AI Agent Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html) | Checklist de menor privilégio, validação de entrada e saída, memória isolada, confirmação de ações de alto impacto e testes adversariais defensivos. | Defensiva |
| [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework) | Governança de riscos ao longo do ciclo de vida, com perfil específico para IA generativa. | Defensiva |

As novas fontes confirmam controles já alinhados à arquitetura do Leviatã: política por ferramenta, confirmação de ações sensíveis, registros de auditoria, retenção local de memória e limites adaptativos de recursos. Elas serão incluídas como referências de prioridade quando a tarefa mencionar agentes, MCP, RAG, contexto, memória, ferramentas ou governança.
