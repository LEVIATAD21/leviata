# Pesquisa de integrações — base para o KAWA-AI

## Constatações verificadas

| Serviço ou componente | Forma adequada de integração | Limite ou pré-requisito relevante |
|---|---|---|
| Extração de quadros | FFmpeg local, acionado sob a política de terminal; gera quadros em uma pasta de trabalho. | Não precisa de API, mas consome disco e CPU. O agente deve usar uma taxa de amostragem, não exportar todos os quadros sem necessidade. |
| Transcrição | `whisper.cpp` com modelo pequeno ou base, local e sob demanda. | É adequado a CPU, porém o tempo de transcrição depende da duração do áudio e do modelo. |
| n8n | Instância própria e webhook com autenticação. | Workflows possuem URLs de teste e produção; gatilhos externos exigem uma URL de produção acessível. |
| NotebookLM | Gemini Notebook Enterprise por API, quando houver projeto Google Cloud e licenças compatíveis. | A documentação classifica a API como Preview; o NotebookLM de consumo não deve ser automatizado por meios não oficiais. |
| Supabase | `supabase-py` ou REST, com URL do projeto e chave fornecidas pelo proprietário. | As chaves ficam somente no cofre local; políticas de linha (RLS) continuam obrigatórias no projeto. |
| Nano Banana / Hedra | Hedra oferece esses modelos por API. | A API pública exige assinatura Hedra paga e saldo de créditos; não há integração gratuita sem conta/chave. |
| Hailuo / MiniMax | API oficial para vídeo, imagem, voz e clonagem de voz. | Exige chave de API e plano/créditos; tarefas de vídeo são assíncronas. |
| Photoroom | API oficial de remoção de fundo e edição. | Requer chave API; há planos distintos para remoção de fundo e edição. |
| NVIDIA NIM | API compatível com OpenAI/Anthropic para descoberta de modelos e inferência sob uma chave autorizada. | Há endpoint de modelos; o KAWA-AI deve consultar poucos modelos por tarefa e consolidar respostas, nunca assumir capacidade ou contexto ilimitados. |

## Decisões de arquitetura

1. Cada integração será um adaptador opcional e só será ativada quando a conexão correspondente existir no cofre local.
2. Segredos não serão incluídos no repositório, parâmetros de linha de comando, diário Obsidian ou auditoria.
3. Serviços web podem usar perfil isolado persistente para login manual, mas operações que alteram conteúdo seguem no modo `ask`.
4. Funções locais serão priorizadas para análise de vídeo e transcrição. Geração, avatar, voz comercial e edição por provedores só serão chamadas por APIs oficialmente autorizadas.
5. A consulta NVIDIA será sequencial e consultiva: cada modelo recebe uma pergunta delimitada, o resultado é resumido e somente o material aprovado pode ir para a memória externa. Isso evita multiplicar custo, latência e dados sensíveis.

## Referências

[1] [n8n Webhook node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/) descreve gatilhos e URLs de teste e produção.

[2] [Gemini Notebook Enterprise](https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-notebooks) descreve APIs de notebooks e os pré-requisitos de configuração e licença.

[3] [Hedra API Quickstart](https://www.hedra.com/docs/pages/developer/getting_started/quickstart) descreve a exigência de assinatura paga e créditos para a API.

[4] [MiniMax API Overview](https://platform.minimax.io/docs/api-reference/api-overview) documenta modelos de vídeo, voz, imagem e requisitos de chave.

[5] [Photoroom API Introduction](https://docs.photoroom.com/) descreve recursos de edição, autenticação por chave e planos da API.

[6] [NVIDIA NIM API Reference](https://docs.nvidia.com/nim/large-language-models/latest/api-reference.html) descreve endpoints compatíveis com OpenAI/Anthropic e descoberta de modelos.
