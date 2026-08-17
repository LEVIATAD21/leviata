# Perfil de desempenho local

O KAWA-AI é direcionado a execução local leve em Linux Mint, inclusive em computadores com memória limitada e sem GPU dedicada. A configuração recomendada continua sendo um modelo Ollama compacto, como `qwen2.5:1.5b`.

## Otimizações aplicadas

| Área | Alteração | Benefício esperado |
|---|---|---|
| Catálogo de cibersegurança | Índice de 817 entradas normalizado e cacheado por versão de arquivo. | Evita reler e reclassificar o JSON a cada consulta dentro do mesmo processo. |
| Roteamento | Regras de linguagem natural compiladas uma vez na classe. | Evita recompilar expressões regulares a cada ordem. |
| Memória | Histórico do agente continua limitado às 24 mensagens mais recentes e contexto RAG permanece limitado por consulta. | Impede crescimento ilimitado de contexto local. |
| Ferramentas | Provedores externos só são inicializados quando escolhidos; o perfil padrão usa Ollama local. | Evita carregar SDKs e conexões desnecessárias no fluxo local padrão. |

## Medição de referência

As medições abaixo foram feitas no ambiente de desenvolvimento em 17/08/2026 e servem para detectar regressões, não como garantia para outro computador.

| Operação | Antes | Depois | Resultado |
|---|---:|---:|---|
| `python3 main.py --skills-catalog` | 0,502 s | 0,494 s | Inicialização permaneceu abaixo de 0,6 s neste ambiente. |
| Suíte unitária | 0,622 s | 0,604 s | Regressão não observada. |
| Cobertura | 64 testes | 65 testes | A validação adicional cobre o roteamento pré-compilado. |

O tempo de geração de respostas depende principalmente do modelo escolhido, da CPU/RAM disponível, do tamanho do contexto e, para APIs externas, da rede e do provedor. O KAWA-AI não promete tempo de resposta fixo para esses componentes.
