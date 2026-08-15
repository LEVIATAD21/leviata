# Fluxo de publicação supervisionado

## Objetivo

Quando uma tarefa resultar em um site, apresentação ou texto público, o KAWA-AI prepara os artefatos e apresenta uma prévia. A publicação ou o envio externo é uma etapa separada, que exige confirmação explícita do proprietário a cada vez.

## Roteamento de artefatos

| Artefato | Serviço preferencial | Etapa permitida sem nova confirmação | Etapa que sempre exige confirmação |
|---|---|---|---|
| Site ou aplicação web | Vercel | construir, testar e gerar prévia | implantar em produção, conectar domínio, alterar variáveis ou promover uma prévia |
| Apresentação | Canva | preparar o conteúdo e um PPTX editável; importar ou criar um rascunho quando solicitado | criar/exportar um design na conta ou acessar um Brand Kit específico |
| Texto de divulgação | Copy.ai por perfil de navegador isolado ou API oficial, se conectada | elaborar briefing e rascunho local | enviar conteúdo, aceitar créditos, publicar ou compartilhar em qualquer canal |

## Vercel: prévia antes de produção

O fluxo normal é: testar localmente, criar um deployment de prévia, verificar URL e logs, mostrar o resultado ao proprietário e, somente após a confirmação, promover com `vercel deploy --prod`. A Vercel diferencia ambientes Local, Preview e Production; o KAWA-AI não deve pular da preparação diretamente para Production. [1] [2]

## Canva: apresentação sem retenção indevida

Canva é usado somente para uma solicitação direta de apresentação ou design. O KAWA-AI não indexa, sincroniza ou transfere designs, prompts, templates ou elementos de Brand Kit para Supabase, Obsidian ou modelos externos. Quando houver um Brand Kit, ele permanece dentro do Canva. Cada criação, importação, exportação ou acesso a uma pasta específica é revisado no momento da ação. [3]

## Copy.ai: texto como rascunho, não postagem

Sem um conector oficial ativo, Copy.ai é tratado como uma sessão web isolada iniciada pelo proprietário. O KAWA-AI pode preparar um briefing estruturado e copiar o rascunho para uma página aberta; não pode publicar nem compartilhar material sem confirmação. Se houver uma API oficial e uma chave fornecida pelo proprietário, a chave deve ficar no cofre local e o adaptador será adicionado depois de validar a documentação do serviço.

## Pré-requisitos ainda pendentes

1. A conexão Vercel da sessão está desabilitada e requer autorização específica antes de uso.
2. Canva está disponível, mas nenhuma operação será iniciada sem uma solicitação de design concreta e confirmação.
3. Copy.ai não está configurado na sessão; será necessário login em um perfil isolado ou uma chave de API oficial.

## Referências

[1] [Vercel — Deploy from CLI](https://vercel.com/docs/projects/deploy-from-cli) descreve linkagem, prévia, verificação e implantação de produção.

[2] [Vercel — Deployments](https://vercel.com/docs/deployments) descreve os ambientes Local, Preview e Production.

[3] [Canva MCP Usage Policy](https://www.canva.dev/docs/mcp/usage-policy/) estabelece privacidade, minimização de dados, limites de crédito e uso de Brand Kits.
