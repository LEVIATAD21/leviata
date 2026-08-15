# Cérebro de conhecimento — contrato de consulta

## Papel

O módulo `KnowledgeBrain` é uma ferramenta de consulta. Ele transforma um assunto em perguntas de entendimento, consulta fontes públicas pelo gateway web já configurado e devolve um relatório com evidências, limitações e referências encontradas.

Ele não recebe permissões de terminal, escrita de arquivo, instalação, publicação ou credenciais. Também não altera o prompt-base, o histórico de personalidade, a política de ferramentas ou a configuração do assistente principal.

## Entrada e saída

| Item | Contrato |
|---|---|
| Entrada | Um assunto, uma pergunta específica ou um conceito técnico para investigar. |
| Perguntas internas | O que é? Como funciona? Quais são limites e riscos? Como confirmar na fonte? |
| Evidência | Resultados retornados pela pesquisa web configurada; URLs só são apresentadas quando fornecidas pela fonte. |
| Saída | Relatório curto com síntese, perguntas respondidas, fontes observadas e limitações. |
| Efeito colateral | Nenhum por padrão; quando a persistência estiver habilitada, acrescenta o relatório ao diário Obsidian único, sem executar ações no computador. |

## Separação de identidade

O assistente principal mantém sua personalidade e toma a decisão de quando usar a ferramenta. O cérebro de conhecimento produz material de referência, não instruções de sistema. A resposta recebida é adicionada ao contexto como resultado de ferramenta, do mesmo modo que uma busca web, e nunca como mensagem de sistema.

## Fluxo de consulta

1. Receber o assunto e gerar quatro perguntas fixas: definição, funcionamento, limites e forma de confirmação.
2. Fazer uma consulta de pesquisa para cada pergunta, com limite de resultados e de caracteres.
3. Agrupar os resultados sem executar instruções encontradas nas páginas.
4. Pedir ao provedor atual uma síntese limitada ao material coletado, exigindo que ele diferencie evidência de incerteza.
5. Devolver o resultado com as perguntas, os trechos de fonte e a síntese; se não houver fonte suficiente, declarar a limitação em vez de completar lacunas.

## Cofre local de conhecimento

Quando o cofre Obsidian estiver configurado, uma consulta persistida é acrescentada ao diário canônico `KAWA-AI/Reasoning Diary.md`, no próprio cofre selecionado. Não são criadas notas por consulta, nomes com timestamp nem um segundo diário. O manifesto no mesmo diretório fixa o caminho canônico e bloqueia divergências para evitar duplicação.

Sem configuração Obsidian, o comportamento de compatibilidade permanece: a consulta pode ser salva como Markdown em `~/.kawa-ai/knowledge/`. O conteúdo do cofre é memória de referência, não uma fonte de instruções do sistema. Ao recuperar contexto, o KAWA-AI trata o texto como dados e não permite que ele altere identidade, permissões ou política de ferramentas.
