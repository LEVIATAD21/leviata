# Cofre Obsidian e memória contínua

## Objetivo

O Obsidian será o **único cofre persistente** do KAWA-AI para contexto de trabalho, consultas de conhecimento, decisões e resultados. O sistema não cria notas de conhecimento por consulta e não substitui um cofre já selecionado por outro sem ação explícita do proprietário.

O diário não armazena a cadeia de raciocínio privada do modelo. Ele guarda um **registro de trabalho verificável**: pedido resumido, decisões, ferramentas utilizadas, resultados, fontes e resposta final. Isso permite retomar tarefas sem expor dados desnecessários ou tratar texto gerado como fato.

## Descoberta e seleção do cofre

Na primeira execução com `--scan-vault`, o KAWA-AI procura diretórios `.obsidian` no diretório pessoal, em `~/Documents`, `~/Desktop`, `~/Obsidian`, `~/Notes`, `~/vault`, `~/kawa-ai`, `/mnt` e `/media/<usuário>`. A varredura procura somente a assinatura de um cofre e não lê o conteúdo das notas durante a descoberta.

O caminho selecionado é gravado em `~/.kawa-ai/config.json` como `obsidian_vault`. Em execuções futuras, o caminho salvo é sempre reutilizado. Se houver mais de um cofre candidato na primeira varredura, a ferramenta exibe os caminhos e pede que o proprietário selecione um com `--obsidian-vault`; ela não escolhe silenciosamente um cofre diferente.

Uma varredura a partir de `/` é possível somente mediante `--scan-root /`. Diretórios dinâmicos e privilegiados, como `/proc`, `/sys`, `/dev`, `/run`, `/tmp`, `node_modules` e `.git`, são ignorados para evitar travamentos e exposição desnecessária de dados.

## Diário singleton

Após selecionar o cofre, `--init-obsidian` cria somente estes itens:

```text
<cofre-obsidian>/
└── KAWA-AI/
    ├── Reasoning Diary.md          # criado vazio uma única vez
    ├── .kawa-ai-manifest.json      # identidade, versão e caminho canônico
    └── .backups/                   # cópias de recuperação no próprio cofre
```

O caminho canônico do diário é definido no manifesto. Se ele já existir, o KAWA-AI sempre o reutiliza; se o manifesto e o diário divergirem, a operação é bloqueada para evitar duplicação. As gravações são exclusivamente por acréscimo, com `flush` e `fsync`. Cópias de recuperação rotativas permanecem dentro do mesmo cofre e não substituem o diário principal.

## Retomada de contexto

No início de uma sessão, o agente lê apenas uma janela limitada das entradas mais recentes, configurável por `memory_context_chars`. O texto recuperado é identificado como memória local, não como instrução de sistema. A memória não pode alterar as permissões, a política de ferramentas ou a identidade do KAWA-AI.

Relatórios provenientes do módulo de conhecimento passam a ser acrescentados ao mesmo diário quando a persistência estiver habilitada. O cofre não passa a executar ações: sua função permanece documental e consultiva.

## Terminal e navegador

O terminal continua sendo uma ferramenta local submetida aos modos `observe`, `ask` e `workspace`, com auditoria em JSONL. O navegador será opcional, operando por uma instância Playwright isolada por padrão. Leitura de página, navegação, preenchimento, cliques, downloads e envio de formulários serão ações separadas e registradas.

O modo `ask` solicitará confirmação antes de ações de navegador que alterem estado, enviem dados, baixem arquivos ou atuem em uma conta. O KAWA-AI não utilizará sessões, senhas, cookies ou dados de pagamento sem uma ação explícita do proprietário. A ligação com uma janela do navegador já aberta exigirá uma configuração local específica; caso contrário, será usado um perfil isolado.

## Limites de recursos

O processo de descoberta não indexa todos os arquivos do computador. Ele localiza cofres por diretórios `.obsidian`, com limites de profundidade e exclusões. A indexação de notas, se habilitada, ficará limitada ao cofre selecionado e a arquivos Markdown, com teto de tamanho e de quantidade por execução. Esses limites mantêm a operação compatível com 7,2 GB de RAM e CPU integrada.
