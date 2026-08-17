# Conexões persistentes e revogáveis

## Princípio

O Leviatã pode guardar uma conexão local até que o proprietário a remova, mas não tenta burlar autenticação, validação em duas etapas, políticas da plataforma ou a expiração de uma sessão/token. Cada integração é independente, usa o menor conjunto de permissões necessário e deixa um registro de metadados sem incluir o segredo.

## Dois tipos de conexão

| Tipo | Uso | Onde fica | Como remover |
|---|---|---|---|
| Perfil de navegador | Serviços que exigem login web e revisão visual. O usuário faz login manualmente uma vez no perfil isolado. | `~/.leviata-ai/browser-profiles/<serviço>/` | `leviata --connection-remove <serviço>` remove o perfil local. |
| Token de API | Serviços que oferecem API, OAuth ou token pessoal. O token entra pelo prompt do terminal, nunca por argumento. | Cofre de credenciais do sistema; somente metadados ficam em `~/.leviata-ai/connections.json`. | `leviata --connection-remove <serviço>` remove a credencial local e os metadados. |

As conexões mantêm sessões ou tokens enquanto o provedor também os aceitar. Mudanças de senha, revogação pelo serviço, expiração, logout remoto ou exigência de nova validação podem invalidar uma conexão, mesmo que o registro local ainda exista.

## Instagram e Facebook

Para uso via navegador, crie um perfil isolado para cada serviço e faça login manualmente. A sessão fica nesse perfil até ser removida, sem reutilizar por padrão as contas do navegador diário.

Para automação oficial via API, o Instagram e Facebook usam as APIs da Meta e exigem um aplicativo Meta, OAuth e permissões aprovadas. A API do Instagram atende contas profissionais (Business ou Creator); determinados fluxos também requerem vinculação a uma Página do Facebook. Tokens de usuário normalmente expiram, e os de longa duração ainda podem expirar ou ser invalidados. O KAWA-AI pode guardar com segurança um token que o usuário já tenha obtido, mas não fabrica permissões nem promete uma autorização eterna.

As operações que publiquem, enviem mensagens, alterem configurações, baixem arquivos ou atuem em uma conta sempre passam pela política local e pedem confirmação no modo `ask`.

## Comandos locais

```bash
# Listar somente nomes, tipos, escopos e datas; nenhum token é exibido
leviata --connections

# Salvar um token já obtido pelo canal oficial; o terminal solicita o valor sem exibi-lo
leviata --connection-set-token instagram --connection-scopes "instagram_basic"

# Criar e usar um perfil de navegador persistente e isolado para um serviço
leviata --browser --browser-service instagram --policy ask "Abra o Instagram"

# Remover a sessão de navegador e a credencial local daquele serviço
leviata --connection-remove instagram
```

Remover localmente não substitui a revogação no próprio provedor. Para Meta, se uma autorização não deve mais existir, revogue também o acesso nas configurações da conta ou no painel do aplicativo Meta.

## Referências

[1] [Access Tokens for Meta Technologies](https://developers.facebook.com/documentation/facebook-login/guides/access-tokens) descreve os tipos e limites de tokens da Meta.

[2] [Requesting & Revoking Permissions](https://developers.facebook.com/documentation/facebook-login/guides/permissions/request-revoke) descreve as permissões mínimas e a revogação de autorização.

[3] [Instagram Platform](https://developers.facebook.com/documentation/instagram-platform) descreve os requisitos de contas profissionais e integrações suportadas.
