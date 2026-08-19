# Base de Conhecimento de Segurança Web e Cibernética

> **Referência de conhecimento consultável, não fonte de diretrizes.** As diretrizes comportamentais, operacionais e éticas do Leviatã estão **apenas** em [`DIRETRIZES.md`](../DIRETRIZES.md). Este documento e o índice em `agent/data/web_security_knowledge.json` são conhecimento técnico consumido pela ferramenta consultiva `web_security_knowledge` — somente leitura, sem execução.

A base reúne **192 entradas** em **13 categorias**, cada uma classificada por nível de aplicação e descrita por *o que é*, *como funciona*, *detecção*, *endurecimento* e *referências*.

| Classificação | Significado |
|---|---|
| `defensiva` (172) | Análise, detecção, endurecimento e resposta. |
| `escopo_autorizado` (15) | Técnicas de teste/avaliação que exigem autorização escrita, escopo e regras de engajamento. |
| `laboratorio_autorizado` (5) | Experimentos apenas em sistemas próprios ou laboratório controlado. |

## Categorias

- [Injeção e Processamento de Entrada](#injecao-e-processamento-de-entrada) — 18 entradas
- [Cliente, Navegador e Cross-Site](#cliente-navegador-e-cross-site) — 19 entradas
- [Controle de Acesso e Lógica de Autorização](#controle-de-acesso-e-logica-de-autorizacao) — 16 entradas
- [Autenticação, Sessão e Identidade Federada](#autenticacao-sessao-e-identidade-federada) — 13 entradas
- [Segurança de APIs](#seguranca-de-apis) — 11 entradas
- [Transporte, TLS, Cabeçalhos e DNS](#transporte-tls-cabecalhos-e-dns) — 14 entradas
- [Criptografia Aplicada e Segredos](#criptografia-aplicada-e-segredos) — 15 entradas
- [Rede, Perímetro e Infraestrutura](#rede-perimetro-e-infraestrutura) — 14 entradas
- [Segurança em Nuvem](#seguranca-em-nuvem) — 14 entradas
- [Contêineres, Orquestração e Cadeia de Suprimentos](#conteineres-orquestracao-e-cadeia-de-suprimentos) — 15 entradas
- [Modelagem de Ameaças e Frameworks](#modelagem-de-ameacas-e-frameworks) — 15 entradas
- [Defesa, Detecção, Resposta e Forense](#defesa-deteccao-resposta-e-forense) — 14 entradas
- [Identidade Corporativa e Endpoint](#identidade-corporativa-e-endpoint) — 14 entradas

## Injeção e Processamento de Entrada

### Atribuição em Massa (Mass Assignment / Auto-Binding)

**Classificação:** `defensiva`

**O que é:** Vinculação automática de campos de entrada a atributos internos de um objeto, permitindo que o cliente defina propriedades sensíveis que não deveriam ser editáveis.

**Como funciona:** Frameworks que fazem binding automático mapeiam cada campo do corpo da requisição para uma propriedade do modelo; se não há restrição de quais campos são aceitos, o cliente pode incluir propriedades não previstas (como papel/role, saldo, flags de administrador, IDs de proprietário) e alterá-las junto com os campos legítimos. É a versão de entrada da autorização a nível de propriedade quebrada: o problema não é sintaxe de consulta, mas a fronteira ausente entre campos editáveis pelo cliente e campos internos. O impacto vai de escalonamento de privilégio a adulteração de dados de outros tenants. A raiz é confiar na forma do objeto de entrada para popular o modelo persistido.

**Detecção:** No código, procure binding direto de req.body a entidades (ORM save de objeto inteiro, model.update(req.body), construtores que recebem o payload cru) sem DTO/allow-list. Em logs, observe requisições com campos extras inesperados e mudanças em atributos privilegiados. Ferramentas: SAST, revisão de camada de controllers/serializers, e testes de over-posting em endpoints de criação/atualização.

**Endurecimento:** Use allow-list explícita de campos aceitos por operação (DTOs, serializers com campos permitidos, strong parameters, @JsonIgnore/read-only em atributos sensíveis). Separe modelos de entrada dos modelos de domínio/persistência, aplique autorização a nível de propriedade, e valide o esquema. Nunca vincule o payload inteiro diretamente à entidade; defina explicitamente o que o cliente pode escrever.

**Referências:**
- CWE-915: Improperly Controlled Modification of Dynamically-Determined Object Attributes: https://cwe.mitre.org/data/definitions/915.html
- OWASP API Security Top 10 2023 - API3:2023 Broken Object Property Level Authorization: https://owasp.org/API-Security/editions/2023/en/0xa3-broken-object-property-level-authorization/
- OWASP Mass Assignment Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Mass_Assignment_Cheat_Sheet.html
- OWASP Top 10 2021 A08:2021 - Software and Data Integrity Failures: https://owasp.org/Top10/A08_2021-Software_and_Data_Integrity_Failures/

### Contrabando de Requisições HTTP / Dessincronização (HTTP Request Smuggling / Desync)

**Classificação:** `escopo_autorizado`

**O que é:** Exploração de discordância entre front-end e back-end sobre onde uma requisição HTTP termina, permitindo injetar uma requisição contrabandeada no fluxo.

**Como funciona:** Quando um proxy/front-end e o servidor de back-end interpretam de forma diferente os delimitadores de comprimento de mensagem (cabeçalhos Content-Length e Transfer-Encoding: chunked), parte de uma requisição pode ser tratada por um deles como o início da próxima requisição na mesma conexão persistente. Essa dessincronização (variantes CL.TE, TE.CL, TE.TE, além de desync via downgrade de HTTP/2) permite anexar uma requisição maliciosa que será prefixada à requisição de outro usuário, viabilizando bypass de controles do front-end, envenenamento de cache, captura de requisições e sequestro de sessão. O mecanismo é ambiguidade no enquadramento de mensagens entre dois parsers em cadeia. Testar isso é intrusivo e afeta outros usuários, exigindo autorização escrita e janela controlada.

**Detecção:** Em tráfego/logs, procure requisições com Content-Length e Transfer-Encoding simultâneos, valores de chunked malformados, respostas atribuídas ao usuário errado, e anomalias temporais de resposta. Ferramentas: scanners específicos (HTTP Request Smuggler do Burp) em ambiente autorizado, monitoramento de proxies/CDN, e validação de conformidade dos servidores da cadeia. Alertas para cabeçalhos de enquadramento conflitantes ajudam a detecção passiva.

**Endurecimento:** Normalize e rejeite mensagens ambíguas: proíba requisições com Content-Length e Transfer-Encoding simultâneos, garanta que todos os saltos da cadeia usem o mesmo servidor/versão com parsing consistente, e prefira HTTP/2 fim a fim sem downgrade para HTTP/1.1 no back-end. Use servidores/proxies atualizados que fecham conexões em enquadramento inválido, desabilite reuso de conexão quando arriscado, e mantenha configuração uniforme entre CDN, WAF e origem.

**Referências:**
- CWE-444: Inconsistent Interpretation of HTTP Requests (HTTP Request Smuggling): https://cwe.mitre.org/data/definitions/444.html
- OWASP WSTG - Testing for HTTP Request Smuggling: https://owasp.org/www-project-web-security-testing-guide/
- RFC 9112 - HTTP/1.1 Message Syntax and Routing: https://www.rfc-editor.org/rfc/rfc9112
- RFC 7230 - HTTP/1.1 Message Syntax (Content-Length/Transfer-Encoding): https://www.rfc-editor.org/rfc/rfc7230

### Deserialização Insegura de Dados de Entrada (Insecure Deserialization)

**Classificação:** `defensiva`

**O que é:** Reconstrução de objetos a partir de dados serializados não confiáveis, permitindo adulteração de estado ou execução de código via cadeias de gadgets.

**Como funciona:** Deserializar transforma um fluxo de bytes/texto de volta em objetos; quando o fluxo vem de fonte não confiável e o mecanismo permite instanciar tipos arbitrários e executar lógica durante a reconstrução, o atacante pode adulterar propriedades ou encadear classes existentes (gadgets) cujos efeitos colaterais durante a deserialização culminam em execução de código, SSRF ou negação de serviço. Formatos binários com metadados de tipo (serialização nativa de Java/.NET, pickle de Python) são especialmente perigosos porque carregam a identidade das classes a reconstruir. O mecanismo central é permitir que o dado escolha qual código (tipo) será materializado. A raiz é aceitar objetos serializados de fronteiras não confiáveis.

**Detecção:** No código, procure uso de deserializadores nativos sobre entrada externa (ObjectInputStream.readObject, pickle.loads, BinaryFormatter, yaml.load inseguro) e ausência de checagem de tipo/assinatura. Em logs/tráfego, observe assinaturas de payloads serializados (magic bytes de Java, cookies/tokens com objetos serializados) e exceções de deserialização. Ferramentas: SAST, inspeção de endpoints que recebem blobs, e monitoramento de EDR para processos filhos após deserialização.

**Endurecimento:** Evite deserializar dados não confiáveis; prefira formatos de dados puros (JSON) com desserialização em estruturas simples e sem resolução de tipos arbitrários. Se necessário, use allow-list de classes permitidas (ObjectInputFilter no Java, SafeLoader no YAML, safe unpicklers), verifique integridade com assinatura/HMAC, e execute com isolamento e privilégio mínimo. Mantenha bibliotecas atualizadas e remova gadgets desnecessários do classpath.

**Referências:**
- CWE-502: Deserialization of Untrusted Data: https://cwe.mitre.org/data/definitions/502.html
- OWASP Top 10 2021 A08:2021 - Software and Data Integrity Failures: https://owasp.org/Top10/A08_2021-Software_and_Data_Integrity_Failures/
- OWASP Deserialization Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Deserialization_Cheat_Sheet.html
- MITRE ATT&CK T1190 - Exploit Public-Facing Application: https://attack.mitre.org/techniques/T1190/

### Entidade Externa de XML (XML External Entity / XXE)

**Classificação:** `defensiva`

**O que é:** Abuso de processadores XML que resolvem entidades externas definidas em DTD, permitindo leitura de arquivos locais, SSRF e negação de serviço.

**Como funciona:** Documentos XML podem declarar entidades em uma DTD que referenciam recursos externos; quando o parser está configurado para resolver essas entidades, uma entrada XML maliciosa pode fazer o servidor ler arquivos do sistema, abrir conexões para URLs internas (SSRF) ou expandir entidades recursivamente para exaurir memória (billion laughs). O mecanismo depende inteiramente da configuração do parser: por padrão inseguro, ele busca e insere o conteúdo da entidade externa no documento processado. Formatos que embutem XML (SOAP, SAML, SVG, documentos office, feeds) ampliam a superfície. A raiz é a resolução de entidades e DTDs vindas de fonte não confiável.

**Detecção:** No código, procure parsers XML instanciados sem desabilitar DTD/entidades externas (DocumentBuilderFactory, SAXParser, XMLReader, libxml, lxml sem hardening). Em logs/tráfego, observe requisições XML contendo DOCTYPE/ENTITY, conexões de saída inesperadas do servidor ao processar upload, e leituras de arquivos de sistema. Ferramentas: SAST (regras de configuração de parser), DAST, e revisão de endpoints que aceitam XML/SVG/documentos.

**Endurecimento:** Desabilite completamente DTDs e resolução de entidades externas no parser (disallow-doctype-decl, external-general-entities e external-parameter-entities em false, XMLConstants.FEATURE_SECURE_PROCESSING; resolve_entities=False e no_network no lxml). Prefira formatos mais simples (JSON) quando possível, valide contra XSD sem processar entidades, e restrinja egress de rede do servidor. Mantenha bibliotecas de parsing atualizadas com defaults seguros.

**Referências:**
- CWE-611: Improper Restriction of XML External Entity Reference: https://cwe.mitre.org/data/definitions/611.html
- OWASP XML External Entity Prevention Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/XML_External_Entity_Prevention_Cheat_Sheet.html
- OWASP Top 10 2021 A05:2021 - Security Misconfiguration: https://owasp.org/Top10/A05_2021-Security_Misconfiguration/
- MITRE ATT&CK T1190 - Exploit Public-Facing Application: https://attack.mitre.org/techniques/T1190/

### Injeção de Cabeçalho HTTP / CRLF (HTTP Header / CRLF Injection)

**Classificação:** `defensiva`

**O que é:** Inserção de sequências CR/LF em entrada refletida em cabeçalhos HTTP, permitindo forjar cabeçalhos adicionais ou dividir a resposta.

**Como funciona:** O protocolo HTTP separa cabeçalhos por sequências de retorno de carro e nova linha (CRLF); quando entrada não confiável é colocada em um cabeçalho de resposta (por exemplo Location, Set-Cookie) sem remover esses caracteres, o atacante pode encerrar o cabeçalho corrente e injetar novos, ou até um corpo de resposta inteiro (response splitting). Isso habilita fixação/injeção de cookies, redirecionamentos forjados, e em cenários com cache intermediário, envenenamento de cache. O mecanismo é a interpretação de CR/LF como delimitadores estruturais do protocolo dentro de um valor que deveria ser opaco. A causa raiz é a falta de neutralização de caracteres de controle antes de escrever no cabeçalho.

**Detecção:** No código, procure escrita direta de entrada em APIs de cabeçalho de resposta e em redirecionamentos. Em logs/tráfego, observe valores de cabeçalho contendo %0d%0a/CRLF codificados, respostas com cabeçalhos duplicados inesperados, e anomalias de cache. Ferramentas: DAST (ZAP/Burp), WAF com regras de CRLF, e revisão de endpoints que refletem entrada em cabeçalhos.

**Endurecimento:** Remova/rejeite CR, LF e caracteres de controle de qualquer valor destinado a cabeçalhos; use APIs de framework que já validam nomes/valores de cabeçalho (a maioria dos servidores modernos bloqueia CRLF por padrão). Para redirecionamentos, use allow-list de destinos em vez de refletir entrada. Codifique/valide dados por contexto, evite construir respostas manualmente, e mantenha o servidor/framework atualizado.

**Referências:**
- CWE-93: Improper Neutralization of CRLF Sequences (CRLF Injection): https://cwe.mitre.org/data/definitions/93.html
- CWE-113: Improper Neutralization of CRLF Sequences in HTTP Headers: https://cwe.mitre.org/data/definitions/113.html
- OWASP HTTP Response Splitting: https://owasp.org/www-community/attacks/HTTP_Response_Splitting
- RFC 9110 - HTTP Semantics: https://www.rfc-editor.org/rfc/rfc9110

### Injeção de Comando de SO (OS Command Injection)

**Classificação:** `defensiva`

**O que é:** Execução de comandos arbitrários no sistema operacional quando entrada não confiável é passada a um shell ou a uma chamada de execução de processo.

**Como funciona:** A aplicação constrói uma linha de comando concatenando entrada do usuário e a entrega a um interpretador de shell, que trata metacaracteres (;, |, &, $(), backticks, quebras de linha) como separadores/operadores de comando, permitindo encadear comandos adicionais. Mesmo sem shell, a passagem de entrada como argumento pode sofrer argument injection, em que flags maliciosas alteram o comportamento do binário chamado. O mecanismo central é a fronteira ausente entre o programa pretendido e os operadores de controle do shell. O impacto típico é execução remota de código no contexto do processo da aplicação.

**Detecção:** No código, sinalize chamadas a APIs de execução com shell habilitado e string única (system, popen, os.system, child_process.exec, Runtime.exec com string) contendo variáveis. Em logs/EDR, procure processos filhos inesperados a partir do processo web (sh, cmd, powershell), execução de utilitários de rede/enumeração, e conexões de saída anômalas. Ferramentas: SAST/CodeQL, EDR com árvore de processos, monitoramento de criação de processos (Sysmon Event ID 1).

**Endurecimento:** Evite invocar o shell: use APIs que recebem o executável e um array de argumentos separados (execFile, subprocess com lista e shell=False), sem interpolação. Prefira bibliotecas nativas às chamadas de sistema. Aplique allow-list rígida de comandos/argumentos permitidos, valide entrada por tipo, execute com privilégio mínimo e isolamento (containers, seccomp), e nunca passe entrada como parte de uma string de shell.

**Referências:**
- CWE-78: Improper Neutralization of Special Elements used in an OS Command: https://cwe.mitre.org/data/definitions/78.html
- OWASP Top 10 2021 A03:2021 - Injection: https://owasp.org/Top10/A03_2021-Injection/
- OWASP OS Command Injection Defense Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html
- MITRE ATT&CK T1059 - Command and Scripting Interpreter: https://attack.mitre.org/techniques/T1059/

### Injeção de LDAP (LDAP Injection)

**Classificação:** `defensiva`

**O que é:** Manipulação de filtros de busca ou DNs de diretórios LDAP pela injeção de metacaracteres, alterando a lógica de consulta ou o alvo da operação.

**Como funciona:** Consultas LDAP usam filtros com sintaxe própria (parênteses, operadores lógicos &, |, !, curingas *) e DNs com caracteres especiais; quando entrada não confiável é inserida sem escape, o atacante altera a estrutura do filtro. Por exemplo, injetar curingas ou operadores lógicos pode transformar uma condição restritiva em uma que retorna todos os objetos ou que ignora a verificação de senha, resultando em bypass de autenticação ou vazamento de atributos do diretório. O mecanismo é o mesmo padrão de mistura de código e dado, aplicado à gramática de filtros e DNs do LDAP.

**Detecção:** No código, procure construção de filtros por concatenação de strings (ex.: (uid=<entrada>)) e montagem de DN com entrada não escapada. Em logs do diretório, observe filtros com curingas/operadores inesperados, buscas que retornam volumes anômalos de objetos, e tentativas de bind com padrões atípicos. Ferramentas: SAST, revisão de código de módulos de autenticação e logs do servidor de diretório (AD/OpenLDAP).

**Endurecimento:** Escape entrada conforme as regras do RFC 4515 (filtros) e RFC 4514 (DNs) usando bibliotecas do provedor (ex.: rotinas de escape do JNDI/LDAP), ou APIs que separam valores da estrutura do filtro. Aplique allow-list de caracteres para campos como usuário, use contas de serviço com privilégio mínimo, e nunca use a resposta do filtro como única prova de autenticação sem verificar credenciais via bind adequado.

**Referências:**
- CWE-90: Improper Neutralization of Special Elements used in an LDAP Query: https://cwe.mitre.org/data/definitions/90.html
- OWASP LDAP Injection Prevention Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/LDAP_Injection_Prevention_Cheat_Sheet.html
- OWASP Top 10 2021 A03:2021 - Injection: https://owasp.org/Top10/A03_2021-Injection/
- RFC 4515 - LDAP String Representation of Search Filters: https://www.rfc-editor.org/rfc/rfc4515

### Injeção de Logs (Log Injection / Forjamento de Log)

**Classificação:** `defensiva`

**O que é:** Manipulação de registros de log pela inserção de caracteres de controle ou conteúdo enganoso quando entrada não confiável é gravada sem neutralização.

**Como funciona:** Aplicações registram entrada do usuário nos logs; se caracteres de nova linha e controle não forem tratados, o atacante pode injetar linhas de log forjadas (falsear eventos, esconder rastros) ou quebrar o parsing por ferramentas de análise, comprometendo a integridade da trilha de auditoria. Em cenários mais graves, se os logs são renderizados em painéis web sem escape, há risco de XSS armazenado no visualizador, e se são interpretados por componentes de log com resolução de expressões, há risco de execução (como no caso Log4Shell). O mecanismo é a gravação de dados não confiáveis em um meio que também carrega estrutura/semântica. A raiz é confiar na entrada ao compor a linha de log.

**Detecção:** No código, procure concatenação de entrada crua em mensagens de log e ausência de encoding. Em logs, observe linhas com CRLF embutido, timestamps/níveis fora de padrão no meio de um campo, e caracteres de controle. Ferramentas: revisão do framework de logging, regras de SIEM para detectar linhas malformadas, e verificação de que o visualizador de logs escapa conteúdo.

**Endurecimento:** Neutralize CR/LF e caracteres de controle antes de logar, prefira logging estruturado (JSON) que separa campos de valores, e nunca interprete conteúdo de log como formato/expressão (desabilite lookups de expressão como no Log4j). Escape ao renderizar logs em interfaces web, aplique validação de entrada, e proteja a integridade dos logs com armazenamento append-only e coleta centralizada.

**Referências:**
- CWE-117: Improper Output Neutralization for Logs: https://cwe.mitre.org/data/definitions/117.html
- OWASP Top 10 2021 A09:2021 - Security Logging and Monitoring Failures: https://owasp.org/Top10/A09_2021-Security_Logging_and_Monitoring_Failures/
- OWASP Logging Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html
- NIST SP 800-92 - Guide to Computer Security Log Management: https://csrc.nist.gov/pubs/sp/800/92/final

### Injeção de NoSQL (NoSQL Injection)

**Classificação:** `defensiva`

**O que é:** Manipulação de consultas em bancos NoSQL (documento, chave-valor) injetando operadores ou expressões que alteram a lógica de filtragem ou executam código no motor de consulta.

**Como funciona:** Bancos NoSQL frequentemente aceitam consultas como estruturas de dados (objetos JSON/BSON) em vez de strings, então a injeção ocorre quando entrada não confiável vira parte do objeto de consulta e introduz operadores lógicos (como comparadores de desigualdade ou de correspondência) que subvertem o filtro pretendido. Um campo esperado como string pode chegar como objeto contendo operadores, transformando uma comparação de igualdade em uma condição sempre verdadeira e permitindo bypass de autenticação. Alguns motores permitem cláusulas com avaliação de expressões server-side (JavaScript em MongoDB), abrindo caminho para injeção de código no próprio banco. A raiz é a coerção de tipo e a aceitação de estruturas ricas onde se esperava um valor escalar.

**Detecção:** No código, procure passagem direta de req.body/req.query para filtros de consulta sem checagem de tipo, e uso de $where/mapReduce com strings dinâmicas. Em logs, observe parâmetros que chegam como objetos onde se esperavam strings, e consultas com operadores inesperados. Ferramentas: SAST específico para Node/Mongo, validadores de esquema, e inspeção de tráfego para payloads JSON aninhados anômalos.

**Endurecimento:** Valide e coaja tipos estritamente (garanta que campos escalares sejam strings/números, rejeitando objetos), usando validação de esquema (JSON Schema, Joi, Zod, Mongoose com strict). Desabilite avaliação server-side de JavaScript ($where, mapReduce) quando não necessária. Aplique allow-list de operadores permitidos, sanitize chaves que iniciem com caracteres de operador, e siga privilégio mínimo no usuário do banco.

**Referências:**
- CWE-943: Improper Neutralization of Special Elements in Data Query Logic: https://cwe.mitre.org/data/definitions/943.html
- OWASP Top 10 2021 A03:2021 - Injection: https://owasp.org/Top10/A03_2021-Injection/
- OWASP Testing Guide - Testing for NoSQL Injection: https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/07-Input_Validation_Testing/05.6-Testing_for_NoSQL_Injection
- MongoDB Security Checklist: https://www.mongodb.com/docs/manual/administration/security-checklist/

### Injeção de SQL (SQL Injection / SQLi)

**Classificação:** `defensiva`

**O que é:** Falha em que dados de entrada não confiáveis são concatenados a uma consulta SQL, permitindo que o atacante altere a estrutura da query executada pelo banco.

**Como funciona:** A aplicação constrói a instrução SQL concatenando strings vindas do usuário sem separar código de dados, de modo que caracteres de controle (aspas, comentários, operadores lógicos, UNION) passam a ser interpretados como parte da sintaxe SQL em vez de valor literal. Na variante clássica in-band, o resultado é devolvido no mesmo canal da resposta: a baseada em UNION anexa colunas de outras tabelas ao conjunto de resultados, e a baseada em erro extrai dados através de mensagens de exceção do SGBD. Conceitualmente, o problema é a ausência de fronteira entre a árvore sintática da consulta e o dado, o que o parser do banco resolve a favor da estrutura injetada. A raiz é sempre a mistura de plano de código e dado no mesmo buffer textual.

**Detecção:** No código, procure concatenação/interpolação de variáveis em strings SQL (ex.: f-strings, template literals, string builders) em vez de parâmetros ligados (bind). Em runtime, monitore erros de sintaxe SQL nos logs do SGBD, picos de consultas anômalas, uso inesperado de UNION/comentários (--, /*), e tempos de resposta atípicos. Ferramentas: SAST (Semgrep, CodeQL), DAST (OWASP ZAP), WAF com regras CRS do OWASP, e revisão de logs de banco/APM; instrumente também alertas para exceções de driver de banco expostas ao usuário.

**Endurecimento:** Use consultas parametrizadas/prepared statements ou ORMs que façam bind de parâmetros por padrão; nunca concatene entrada em SQL. Para identificadores dinâmicos (nomes de tabela/coluna), use allow-list em vez de interpolar entrada. Aplique privilégio mínimo à conta de banco da aplicação, desabilite mensagens de erro detalhadas para o usuário final, valide/normalize entrada por tipo, e adote defesa em profundidade com WAF. Prefira stored procedures apenas se também usarem parâmetros ligados internamente.

**Referências:**
- OWASP Top 10 2021 A03:2021 - Injection: https://owasp.org/Top10/A03_2021-Injection/
- CWE-89: Improper Neutralization of Special Elements used in an SQL Command: https://cwe.mitre.org/data/definitions/89.html
- OWASP SQL Injection Prevention Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html
- OWASP WSTG - Testing for SQL Injection: https://owasp.org/www-project-web-security-testing-guide/
- MITRE ATT&CK T1190 - Exploit Public-Facing Application: https://attack.mitre.org/techniques/T1190/

### Injeção de SQL Cega e Out-of-Band (Blind / OOB SQLi)

**Classificação:** `escopo_autorizado`

**O que é:** Variantes de SQLi em que o resultado não retorna diretamente na resposta, exigindo inferência por comportamento (booleano, tempo) ou por canais externos (DNS/HTTP).

**Como funciona:** Quando a aplicação não devolve os dados nem os erros do banco, a informação é inferida indiretamente. Na variante booleana, condições verdadeiras/falsas produzem diferenças observáveis na resposta (conteúdo, status, tamanho), permitindo reconstruir dados bit a bit. Na variante baseada em tempo, funções de atraso condicional fazem a resposta demorar quando uma condição é verdadeira. Na out-of-band, a consulta induz o SGBD a iniciar uma requisição externa (por exemplo resolução DNS) que carrega o dado exfiltrado para um servidor controlado, útil quando não há canal in-band. A avaliação dessas variantes exige autorização escrita e regras de engajamento, pois envolve testes ativos contra o alvo.

**Detecção:** Detecte pela telemetria: consultas com funções de atraso (SLEEP/WAITFOR/pg_sleep) nos logs do SGBD, padrões de requisições que variam apenas em um caractere por vez (força bruta de inferência), e conexões de saída inesperadas do servidor de banco (DNS/HTTP) que indicam OOB. Correlacione latências anômalas por rota no APM e ative alertas para egress do host de banco. WAFs e DAST autenticados ajudam a reproduzir o comportamento em ambiente controlado.

**Endurecimento:** As mesmas defesas do SQLi clássico eliminam também as variantes cegas e OOB: parametrização estrita, allow-list para identificadores, privilégio mínimo. Adicionalmente, bloqueie egress de rede a partir do servidor de banco (sem DNS/HTTP arbitrário de saída) para cortar canais out-of-band, padronize tempos de resposta e mensagens genéricas de erro, e aplique rate limiting para dificultar a inferência iterativa.

**Referências:**
- OWASP Top 10 2021 A03:2021 - Injection: https://owasp.org/Top10/A03_2021-Injection/
- CWE-89: SQL Injection: https://cwe.mitre.org/data/definitions/89.html
- OWASP WSTG-INPV-05 - Testing for SQL Injection: https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/07-Input_Validation_Testing/05-Testing_for_SQL_Injection
- OWASP SQL Injection Prevention Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html

### Injeção de Template do Lado do Servidor (Server-Side Template Injection / SSTI)

**Classificação:** `escopo_autorizado`

**O que é:** Falha em que entrada não confiável é interpretada como sintaxe de um motor de templates no servidor, permitindo avaliar expressões e frequentemente escalar para execução de código.

**Como funciona:** Ocorre quando a aplicação concatena entrada do usuário dentro do próprio texto do template (em vez de passá-la como dado ao contexto de renderização), fazendo o motor avaliar as construções de template embutidas na entrada. Como muitos motores expõem acesso a objetos, atributos e métodos da linguagem hospedeira, uma expressão avaliada pode navegar até funções perigosas e, dependendo do sandbox do motor, alcançar execução de código no servidor. A distinção conceitual chave é template como código versus dados: a variável deve entrar no contexto, nunca na string do template. A confirmação e a avaliação de impacto exigem autorização escrita, pois são testes ativos que podem levar a RCE.

**Detecção:** No código, procure renderização com template construído dinamicamente a partir de entrada (ex.: render_template_string, new Template(userInput)) em vez de templates estáticos com contexto. Em runtime, avaliação de expressões matemáticas simples que retornam resultado computado na resposta é um indicador clássico; monitore erros de sintaxe do motor de template nos logs. Ferramentas: SAST focado no framework de template, DAST/burp com detecção de SSTI, revisão de camadas de view.

**Endurecimento:** Nunca construa o corpo do template com entrada do usuário; passe dados exclusivamente pelo contexto de variáveis. Use motores com auto-escaping e sandbox habilitado, e prefira lógica de apresentação sem avaliação de expressões arbitrárias. Aplique allow-list para qualquer seleção dinâmica de template (nome de arquivo), execute a renderização com privilégio mínimo/isolamento, e valide/normalize entrada exibida.

**Referências:**
- CWE-1336: Improper Neutralization of Special Elements Used in a Template Engine: https://cwe.mitre.org/data/definitions/1336.html
- CWE-94: Improper Control of Generation of Code (Code Injection): https://cwe.mitre.org/data/definitions/94.html
- OWASP Top 10 2021 A03:2021 - Injection: https://owasp.org/Top10/A03_2021-Injection/
- OWASP WSTG - Testing for Server-Side Template Injection: https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/07-Input_Validation_Testing/18-Testing_for_Server-side_Template_Injection

### Injeção de XPath e XQuery (XPath Injection)

**Classificação:** `defensiva`

**O que é:** Alteração de expressões XPath/XQuery usadas para consultar documentos XML pela injeção de operadores e aspas, subvertendo a lógica de seleção de nós.

**Como funciona:** Aplicações que armazenam ou consultam dados em XML montam expressões XPath concatenando entrada do usuário; caracteres como aspas, colchetes e operadores lógicos (or, and) permitem reescrever o predicado da expressão. Ao injetar uma condição sempre verdadeira em um predicado de login, o atacante faz a expressão selecionar nós que não deveria, resultando em bypass de autenticação ou leitura de todo o documento. Diferente do SQL, XPath não tem controle de privilégios por nó, então a exposição costuma abranger o documento inteiro. A causa raiz é novamente a fronteira ausente entre a gramática da consulta e o dado.

**Detecção:** No código, sinalize construção de expressões XPath por concatenação (ex.: //user[name/text()='<entrada>']) e uso de avaliadores XPath com strings dinâmicas. Observe respostas que retornam mais nós do que o esperado e erros de parsing XPath nos logs. Ferramentas: SAST, revisão de camadas de acesso a dados XML e testes DAST em campos que alimentam consultas XML.

**Endurecimento:** Use consultas XPath parametrizadas (variáveis pré-compiladas via XPathExpression/variable resolver) em vez de concatenar entrada; quando indisponível, escape aspas e metacaracteres com biblioteca dedicada. Aplique validação por allow-list, prefira migrar dados sensíveis de autenticação para armazenamento com controle de acesso adequado, e trate documentos XML com privilégio mínimo de leitura.

**Referências:**
- CWE-643: Improper Neutralization of Data within XPath Expressions: https://cwe.mitre.org/data/definitions/643.html
- OWASP XPath Injection: https://owasp.org/www-community/attacks/XPATH_Injection
- OWASP Top 10 2021 A03:2021 - Injection: https://owasp.org/Top10/A03_2021-Injection/
- OWASP WSTG - Testing for XPath Injection: https://owasp.org/www-project-web-security-testing-guide/

### Negação de Serviço por Expressão Regular (ReDoS)

**Classificação:** `defensiva`

**O que é:** Certas expressões regulares exibem retrocesso catastrófico: uma entrada relativamente curta e cuidadosamente construída faz o tempo de correspondência crescer exponencialmente, consumindo CPU e travando o processo. É um vetor de negação de serviço algorítmica frequentemente esquecido em validações de entrada.

**Como funciona:** Motores de regex baseados em retrocesso exploram múltiplos caminhos de correspondência. Padrões com quantificadores aninhados ou alternativas sobrepostas (por exemplo, grupos repetidos que podem casar a mesma entrada de várias formas) podem forçar o motor a testar um número exponencial de combinações quando a entrada quase casa mas falha no final. O atacante não precisa de acesso privilegiado: basta enviar a string que dispara o pior caso em um campo validado por uma regex vulnerável, esgotando um núcleo de CPU por requisição. Como a validação de entrada é onipresente, o mesmo padrão vulnerável pode aparecer em muitos pontos. A mitigação envolve escrever padrões lineares, usar motores sem retrocesso exponencial e limitar tempo e tamanho da entrada avaliada.

**Detecção:** Monitore uso de CPU por requisição e alerte para picos correlacionados a endpoints que fazem correspondência de padrões sobre entrada do usuário. Analise estaticamente as expressões regulares do código em busca de quantificadores aninhados e alternâncias ambíguas (existem linters específicos para ReDoS). Registre timeouts de processamento e entradas anormalmente longas. Testes de fuzzing direcionados a campos validados por regex ajudam a revelar padrões vulneráveis.

**Endurecimento:** Prefira motores de regex com garantia de tempo linear (por exemplo, implementações baseadas em autômatos como RE2) para entrada não confiável. Reescreva padrões para evitar quantificadores aninhados e sobreposição de alternativas; ancore e limite o escopo. Imponha limite de tamanho à entrada antes da correspondência e aplique timeout à execução da regex. Onde possível, substitua validações complexas por parsing determinístico. Inclua análise de ReDoS na revisão de código e na esteira de CI.

**Referências:**
- OWASP: Regular Expression Denial of Service - ReDoS
- OWASP Cheat Sheet Series: Denial of Service
- CWE-1333: Inefficient Regular Expression Complexity
- CWE-400: Uncontrolled Resource Consumption

### Poluição de Parâmetros HTTP (HTTP Parameter Pollution / HPP)

**Classificação:** `defensiva`

**O que é:** A Poluição de Parâmetros HTTP explora o fato de que servidores, frameworks e componentes intermediários tratam parâmetros duplicados de formas diferentes (primeiro valor, último valor, concatenação ou array). Essa divergência permite contornar validações, filtros ou controles que inspecionam apenas uma das ocorrências.

**Como funciona:** Quando uma requisição inclui o mesmo nome de parâmetro mais de uma vez, não há comportamento universal: um WAF pode avaliar o primeiro valor, o servidor de aplicação usar o último, e um serviço downstream concatenar ambos. O atacante aproveita essa dessincronização para que a camada de segurança veja um valor benigno enquanto a lógica sensível processa outro, contornando validações ou injetando dados em consultas construídas dinamicamente. O problema é uma classe de discrepância de parsing entre componentes, análoga em espírito ao contrabando de requisições. A defesa é normalizar como parâmetros duplicados são tratados de ponta a ponta e validar de forma consistente na mesma camada que os consome.

**Detecção:** Registre e alerte para requisições com nomes de parâmetro repetidos, especialmente em endpoints sensíveis. Compare como diferentes camadas (proxy, WAF, aplicação) interpretam os mesmos parâmetros em testes controlados para revelar divergências. Monitore anomalias em consultas ou chamadas geradas a partir de entrada com parâmetros duplicados.

**Endurecimento:** Adote um comportamento único e explícito para parâmetros duplicados em toda a pilha e rejeite ou canonicalize duplicatas inesperadas na borda. Valide a entrada na mesma camada que efetivamente a utiliza, após a normalização. Use bibliotecas de parsing que exponham claramente múltiplos valores e trate-os deliberadamente. Combine com validação de esquema estrita (allowlist de parâmetros esperados) e consultas parametrizadas para eliminar o impacto de valores injetados.

**Referências:**
- OWASP Web Security Testing Guide: Testing for HTTP Parameter Pollution
- OWASP: HTTP Parameter Pollution
- CWE-235: Improper Handling of Extra Parameters
- PortSwigger Web Security Academy: Server-side parameter pollution

### Segurança de Aplicações LLM e Injeção de Prompt (LLM / Prompt Injection Defense)

**Classificação:** `defensiva`

**O que é:** Aplicações que integram modelos de linguagem misturam instruções confiáveis do desenvolvedor com conteúdo não confiável (entrada do usuário ou dados recuperados) no mesmo contexto. A injeção de prompt explora essa ausência de separação para redirecionar o comportamento do modelo, exfiltrar dados ou abusar de ferramentas conectadas.

**Como funciona:** Um LLM não distingue de forma robusta entre a instrução do sistema e o texto que processa: ambos chegam como linguagem natural no mesmo contexto. Na injeção direta, o usuário insere instruções que sobrepõem as regras pretendidas. Na injeção indireta, instruções maliciosas ficam embutidas em conteúdo que o modelo consome (uma página, um documento, um e-mail recuperado por um agente), acionando comportamento não autorizado sem interação direta do atacante. O impacto cresce quando o modelo tem acesso a ferramentas ou dados sensíveis: exfiltração, ações indevidas via ferramentas, ou manipulação de saídas exibidas a outros usuários (que podem conter XSS). Como não há solução única e determinística, a defesa é em camadas: reduzir privilégios do modelo, isolar e marcar conteúdo não confiável, validar entradas e saídas, e exigir confirmação humana para ações sensíveis.

**Detecção:** Registre prompts, conteúdo recuperado e chamadas de ferramentas para auditoria, e monitore padrões de instrução suspeitos no conteúdo consumido (tentativas de sobrepor regras, pedidos de exfiltração). Alerte para ações de ferramenta fora do comportamento esperado, acessos anômalos a dados e saídas que contenham marcações potencialmente executáveis. Use conjuntos de testes adversariais (red teaming de prompts) para avaliar robustez continuamente.

**Endurecimento:** Aplique menor privilégio ao modelo e às ferramentas que ele pode invocar, com autorização verificada no backend para cada ação sensível e confirmação humana quando o impacto for alto. Trate todo conteúdo externo como não confiável: isole-o de instruções, delimite-o claramente e não permita que ele redefina as regras do sistema. Valide e restrinja entradas e sanitize/codifique as saídas antes de renderizá-las (prevenindo XSS derivado). Limite o acesso do modelo a dados sensíveis, imponha limites de taxa e adote guardrails, alinhando o programa a frameworks reconhecidos de risco de IA.

**Referências:**
- OWASP Top 10 for Large Language Model Applications: LLM01 Prompt Injection
- MITRE ATLAS: Adversarial Threat Landscape for AI Systems
- NIST AI Risk Management Framework (AI RMF 1.0)
- OWASP: LLM Applications Cybersecurity and Governance Checklist

### Upload Inseguro de Arquivos (Unrestricted File Upload)

**Classificação:** `defensiva`

**O que é:** Falhas na validação de arquivos enviados por usuários permitem gravar conteúdo perigoso (scripts executáveis, conteúdo malicioso, arquivos que sobrescrevem caminhos) no servidor ou entregá-lo a outros usuários. A defesa combina validação de tipo, isolamento de armazenamento e ausência de execução.

**Como funciona:** O risco surge quando a aplicação confia em atributos controlados pelo cliente (nome do arquivo, extensão, cabeçalho Content-Type) para decidir onde e como armazenar o conteúdo. Sem verificação do tipo real (magic bytes) e sem normalização do caminho de destino, um arquivo pode ser gravado em local servido diretamente, receber extensão executável pelo servidor de aplicação, ou usar sequências de travessia no nome para escapar do diretório previsto. Conceitualmente, o problema é a mesma cadeia de outras injeções: entrada não confiável influenciando uma operação sensível (persistência e posterior interpretação/execução). A mitigação segue defesa em profundidade: validar formato e tamanho, gerar nome de arquivo do lado do servidor, armazenar fora da raiz web (idealmente em bucket/objeto sem execução), e servir via handler controlado com Content-Type e Content-Disposition corretos.

**Detecção:** Monitore criações de arquivos em diretórios de upload com extensões inesperadas (scripts, arquivos de configuração) e acessos subsequentes a esses caminhos; alerte quando um arquivo enviado é requisitado como recurso executável. Registre metadados de upload (usuário, hash, tipo detectado vs. declarado) e compare divergências entre extensão, Content-Type e magic bytes. Integre varredura antimalware nos arquivos recebidos e revise logs do servidor web por requisições POST de grande volume ou repetidas ao endpoint de upload.

**Endurecimento:** Valide o tipo real por magic bytes e use allowlist de formatos permitidos, nunca blocklist de extensões. Gere nomes de arquivo aleatórios no servidor e descarte o nome original; normalize e ancore o caminho de destino. Armazene uploads fora do diretório servido pela aplicação, preferencialmente em armazenamento de objetos dedicado com execução desabilitada. Sirva downloads por um handler que force Content-Disposition: attachment e X-Content-Type-Options: nosniff. Imponha limites de tamanho, verifique novamente após transformação (ex.: reprocessar imagens), execute varredura antivírus e isole o processamento em sandbox.

**Referências:**
- OWASP Cheat Sheet Series: File Upload
- OWASP Web Security Testing Guide: Testing Upload Functionality
- CWE-434: Unrestricted Upload of File with Dangerous Type
- CWE-616: Incomplete Identification of Uploaded File Variables

### Validação de Entrada e Consultas Parametrizadas (Input Validation & Parameterized Queries)

**Classificação:** `defensiva`

**O que é:** Conjunto de controles fundamentais que separam código de dados e garantem que a entrada seja bem formada, prevenindo toda a classe de vulnerabilidades de injeção.

**Como funciona:** A defesa primária contra injeção é a separação estrutural entre código e dado: consultas parametrizadas enviam a instrução e os valores por canais distintos, de modo que o valor nunca é interpretado como sintaxe pelo interpretador (SQL, LDAP, XPath, comando). Complementarmente, a validação de entrada por allow-list restringe cada campo ao formato, tipo, tamanho e faixa esperados, rejeitando o que não se conforma, enquanto a canonicalização normaliza a entrada antes da checagem para evitar bypass por codificações alternativas. Como nem todo contexto suporta parametrização (identificadores, HTML, shell), aplica-se codificação/escape específico do contexto de saída como camada adicional. O princípio é tratar toda entrada como não confiável e nunca deixar o dado escolher a estrutura ou o código executado.

**Detecção:** No código, verifique se toda camada de acesso a interpretadores usa parâmetros ligados e se há validação centralizada por esquema na fronteira. Meça cobertura com SAST (regras de taint que rastreiam entrada até sinks perigosos), revisão de contratos de API, e testes automatizados com entradas malformadas (fuzzing). A ausência de validação ou o uso de blacklist frágil são indicadores de risco.

**Endurecimento:** Adote parametrização/ORM por padrão em todos os interpretadores; valide por allow-list (tipo, formato, comprimento, faixa) na entrada, canonicalizando antes de validar; aplique codificação de saída conforme o contexto (HTML, atributo, URL, JS, SQL identifier). Combine validação sintática e semântica, use bibliotecas de validação de esquema (Zod, Joi, Bean Validation, Pydantic), rejeite em vez de tentar sanitizar quando possível, e adote defesa em profundidade (WAF, privilégio mínimo, CSP). Trate validação como controle de qualidade e de segurança simultaneamente.

**Referências:**
- CWE-20: Improper Input Validation: https://cwe.mitre.org/data/definitions/20.html
- OWASP Input Validation Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html
- OWASP Injection Prevention Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Injection_Prevention_Cheat_Sheet.html
- OWASP Top 10 2021 A03:2021 - Injection: https://owasp.org/Top10/A03_2021-Injection/
- NIST SP 800-53 Rev.5 SI-10 - Information Input Validation: https://csrc.nist.gov/projects/risk-management/sp800-53-controls/release-search#!/control?version=5.1&number=SI-10

## Cliente, Navegador e Cross-Site

### Abuso de postMessage (postMessage Origin Validation)

**Classificação:** `defensiva`

**O que é:** Falhas na comunicacao cross-window via postMessage em que a origem/destino das mensagens nao e validada, permitindo vazamento de dados ou injecao de payloads no handler receptor.

**Como funciona:** A API postMessage permite troca de mensagens entre janelas/iframes de origens diferentes. Dois erros comuns surgem: no envio, usar targetOrigin curinga (*) expoe a mensagem a qualquer origem que controle a janela de destino; na recepcao, um handler que nao verifica event.origin (e event.source quando aplicavel) aceita mensagens de qualquer emissor. Se o handler ainda repassa o conteudo da mensagem a um sink perigoso do DOM, surge DOM-based XSS; se apenas confia nos dados, pode haver bypass de autorizacao ou vazamento. O problema esta na ausencia de validacao de origem e de esquema do payload.

**Detecção:** Localizar todos os addEventListener('message', ...) e verificar se checam event.origin contra lista de permissao e validam a estrutura da mensagem antes de usa-la. Buscar chamadas postMessage com targetOrigin '*'. Rastrear se dados da mensagem alcancam innerHTML, eval ou navegacao. Ferramentas: analise estatica de JS, DOM Invader e revisao manual dos handlers.

**Endurecimento:** No receptor, validar event.origin por comparacao exata contra origens confiaveis e rejeitar o restante; validar o formato/esquema do payload e nunca passar dados de mensagem diretamente a sinks perigosos. No emissor, especificar targetOrigin exato em vez de '*'. Tratar dados de mensagens como entrada nao confiavel, aplicando sanitizacao/codificacao e Trusted Types. Minimizar a superficie de mensagens entre origens e documentar o contrato de cada canal.

**Referências:**
- MDN Window.postMessage() - https://developer.mozilla.org/en-US/docs/Web/API/Window/postMessage
- OWASP HTML5 Security Cheat Sheet (Web Messaging) - https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html
- CWE-345: Insufficient Verification of Data Authenticity - https://cwe.mitre.org/data/definitions/345.html
- CWE-346: Origin Validation Error - https://cwe.mitre.org/data/definitions/346.html

### Armazenamento Seguro no Cliente (Client-Side Storage / Token Storage)

**Classificação:** `defensiva`

**O que é:** Armazenar tokens de sessão ou dados sensíveis em localStorage, sessionStorage ou IndexedDB os expõe a qualquer script executado na página, tornando-os alvo direto de XSS. Escolher o mecanismo de armazenamento correto e minimizar o que persiste no cliente é uma decisão de segurança, não apenas de conveniência.

**Como funciona:** O armazenamento web (localStorage, sessionStorage, IndexedDB) é acessível por JavaScript da mesma origem, sem proteção equivalente ao atributo HttpOnly dos cookies. Se a aplicação sofre XSS, qualquer segredo guardado nesses locais — tokens de acesso, dados pessoais — pode ser lido e exfiltrado imediatamente. Cookies marcados como HttpOnly, ao contrário, não são acessíveis por script, embora exijam defesas anti-CSRF. Além do vetor de XSS, dados persistem além da sessão, podem vazar em dispositivos compartilhados e não têm expiração automática. A decisão defensiva envolve não persistir segredos de longa duração no cliente, preferir cookies HttpOnly+Secure+SameSite para credenciais de sessão, e limitar o que fica armazenado ao mínimo não sensível.

**Detecção:** Revise o código de front-end em busca de gravação de tokens ou dados pessoais em localStorage/sessionStorage/IndexedDB. Use CSP com relatórios para detectar tentativas de exfiltração. Em testes, verifique o conteúdo do armazenamento do navegador após autenticação. Monitore vazamentos de tokens (por exemplo, tokens válidos aparecendo em contextos inesperados) que indiquem roubo via script.

**Endurecimento:** Guarde credenciais de sessão em cookies com HttpOnly, Secure e SameSite, e não em armazenamento acessível por JavaScript. Se tokens precisarem estar no cliente, mantenha-os apenas em memória durante a sessão, com curta duração e rotação. Não persista dados pessoais sensíveis no navegador; quando necessário, minimize e limpe ao encerrar a sessão. Combine com uma CSP forte e defesas anti-XSS robustas, já que a integridade do armazenamento depende de nenhum script malicioso executar na origem.

**Referências:**
- OWASP Cheat Sheet Series: HTML5 Security (Web Storage)
- OWASP Cheat Sheet Series: Session Management
- MDN Web Docs: Web Storage API
- CWE-922: Insecure Storage of Sensitive Information

### Codificacao de Saida por Contexto (Context-aware Output Encoding)

**Classificação:** `defensiva`

**O que é:** Pratica de codificar dados nao confiaveis de acordo com o contexto exato de renderizacao (HTML, atributo, JavaScript, URL, CSS) para impedir que sejam interpretados como codigo.

**Como funciona:** Cada contexto de saida possui um conjunto proprio de metacaracteres que mudam o significado da marcacao; o mesmo dado seguro em um contexto pode ser perigoso em outro. Codificacao por contexto aplica a transformacao correta — entidades HTML para corpo, escaping de atributo entre aspas, escaping de string JavaScript, codificacao percentual para componentes de URL e escaping de CSS — no momento da renderizacao. Contextos aninhados (por exemplo, um valor em JavaScript dentro de um atributo de evento HTML) exigem multiplas camadas na ordem correta. A ausencia ou a codificacao errada para o contexto e a causa raiz da maioria dos XSS refletidos e armazenados.

**Detecção:** Mapear cada ponto de renderizacao e o contexto correspondente, verificando se a codificacao aplicada corresponde ao contexto real. Procurar interpolacao de dados em contextos perigosos como blocos de script inline, manipuladores de evento, href/src e URLs. Ferramentas: analise estatica com regras de taint (CodeQL, Semgrep), revisao de templates e testes com metacaracteres marcados por contexto.

**Endurecimento:** Usar frameworks e template engines com auto-escaping sensivel a contexto e evitar construir HTML por concatenacao manual. Nao inserir dados nao confiaveis em contextos de alto risco (dentro de <script>, em manipuladores de evento ou em URLs com esquema arbitrario); quando inevitavel, aplicar a codificacao especifica com bibliotecas confiaveis. Validar formato por lista de permissao como camada adicional e complementar com CSP, Trusted Types e sanitizacao para HTML rico.

**Referências:**
- OWASP Cross Site Scripting Prevention Cheat Sheet - https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html
- OWASP Injection Prevention Cheat Sheet - https://cheatsheetseries.owasp.org/cheatsheets/Injection_Prevention_Cheat_Sheet.html
- CWE-116: Improper Encoding or Escaping of Output - https://cwe.mitre.org/data/definitions/116.html
- CWE-79: Improper Neutralization of Input During Web Page Generation - https://cwe.mitre.org/data/definitions/79.html

### Cross-Site Scripting Armazenado (Stored XSS)

**Classificação:** `defensiva`

**O que é:** Variante de XSS em que o payload malicioso e persistido pela aplicacao (banco, cache, arquivos) e servido posteriormente a outros usuarios, executando script sem interacao direta com o atacante.

**Como funciona:** A entrada nao confiavel e gravada em armazenamento durvel — comentarios, nomes de perfil, campos de metadados, logs exibidos em painel — e depois renderizada em respostas para outras vitimas sem codificacao adequada ao contexto. Por ser persistente, o gatilho independe de um link enviado a vitima: qualquer usuario que visualize o recurso afetado dispara a execucao. O impacto tende a ser maior que o refletido porque pode atingir muitos usuarios e ate contas administrativas que visualizam conteudo gerado por terceiros. A execucao ocorre na origem da aplicacao, permitindo roubo de sessao, acoes autenticadas e propagacao.

**Detecção:** Rastrear o fluxo de dados desde os pontos de gravacao (formularios, APIs, importacoes) ate os pontos de renderizacao, verificando se a codificacao ocorre na saida e nao apenas na entrada. Revisar campos exibidos em contextos privilegiados (paineis administrativos, e-mails HTML, relatorios). Ferramentas: analise de taint (CodeQL, Semgrep), DAST com payloads marcados e monitoramento de relatorios de CSP e de anomalias em logs de renderizacao.

**Endurecimento:** Codificar na saida conforme o contexto e, para conteudo que deve permitir HTML rico, sanitizar com DOMPurify ou biblioteca equivalente com politica restritiva. Nunca confiar em sanitizacao apenas no cliente para dados exibidos a terceiros; validar e normalizar tambem no servidor. Adotar CSP com nonce, Trusted Types e isolamento de renderizacao de conteudo de usuario. Segregar contexto de exibicao de conteudo gerado por usuario (sandboxed iframes) quando apropriado.

**Referências:**
- OWASP Cross Site Scripting Prevention Cheat Sheet - https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html
- CWE-79: Improper Neutralization of Input During Web Page Generation - https://cwe.mitre.org/data/definitions/79.html
- OWASP Top 10 2021 A03 Injection - https://owasp.org/Top10/A03_2021-Injection/
- OWASP HTML Sanitization / DOMPurify - https://github.com/cure53/DOMPurify

### Cross-Site Scripting Baseado em DOM (DOM-based XSS)

**Classificação:** `defensiva`

**O que é:** XSS em que a vulnerabilidade esta inteiramente no codigo JavaScript do cliente, que le uma fonte controlavel e a escreve em um sink perigoso do DOM sem sanitizacao.

**Como funciona:** O codigo do cliente le uma source influenciavel pelo atacante — como location.hash, location.search, document.referrer, window.name ou dados de postMessage — e a passa para um sink que interpreta marcacao ou codigo, como innerHTML, outerHTML, document.write, eval, setTimeout com string ou atribuicao a src/href de scripts. A carga muitas vezes nunca chega ao servidor (o fragmento apos # nao e enviado), tornando a deteccao no lado servidor ineficaz. O fluxo source-para-sink acontece em tempo de execucao no navegador, por isso a analise precisa considerar a arvore DOM e o JavaScript. Frameworks SPA aumentam a superficie por manipularem o DOM dinamicamente.

**Detecção:** Mapear todas as sources e sinks no JavaScript e verificar o fluxo entre elas; buscar por atribuicoes a innerHTML/document.write e uso de eval a partir de dados de URL, mensagens ou storage. Ferramentas: analise estatica de JS (CodeQL, Semgrep), auditoria com DOM Invader (Burp), e violacoes reportadas por Trusted Types em modo report-only. Revisar bibliotecas de terceiros que escrevem no DOM a partir de parametros.

**Endurecimento:** Substituir sinks perigosos por APIs seguras (textContent, setAttribute com validacao, createElement) e evitar innerHTML com dados dinamicos. Habilitar Trusted Types (require-trusted-types-for 'script') para forcar que valores atribuidos a sinks passem por politicas revisadas. Sanitizar com DOMPurify antes de qualquer escrita de HTML e validar dados de URL/mensagens por lista de permissao. Manter CSP restritiva como defesa em profundidade.

**Referências:**
- OWASP DOM based XSS Prevention Cheat Sheet - https://cheatsheetseries.owasp.org/cheatsheets/DOM_based_XSS_Prevention_Cheat_Sheet.html
- CWE-79: Improper Neutralization of Input During Web Page Generation - https://cwe.mitre.org/data/definitions/79.html
- W3C Trusted Types - https://www.w3.org/TR/trusted-types/
- MDN DOM-based XSS mitigation with Trusted Types - https://developer.mozilla.org/en-US/docs/Web/API/Trusted_Types_API

### Cross-Site Scripting Refletido (Reflected XSS)

**Classificação:** `defensiva`

**O que é:** Falha em que dados controlados pelo atacante presentes na requisicao sao refletidos de imediato na resposta HTML sem codificacao adequada, executando script no navegador da vitima.

**Como funciona:** O servidor (ou o codigo do lado do cliente) recebe um valor da requisicao — tipicamente um parametro de query, fragmento ou cabecalho — e o insere na resposta sem aplicar a codificacao correta para o contexto de saida. Como o dado nao e persistido, a exploracao normalmente depende de induzir a vitima a abrir um link preparado. Quando o valor cai em um contexto HTML, de atributo, de JavaScript, de URL ou de CSS sem escaping apropriado, o navegador interpreta parte do conteudo como marcacao ou codigo executavel. A execucao ocorre na origem da aplicacao, herdando cookies de sessao, tokens e permissoes daquela origem.

**Detecção:** No codigo, buscar por concatenacao de entrada da requisicao diretamente em respostas (sinks como innerHTML, document.write, template sem auto-escape ou APIs de resposta do servidor). Em revisao dinamica, testar refletores em cada contexto e observar se metacaracteres (<, >, aspas) chegam sem codificacao. Ferramentas: DAST (OWASP ZAP, Burp Suite), analise estatica (Semgrep, CodeQL) e relatorios de violacao de CSP via endpoint report-to/report-uri, que sinalizam scripts inline bloqueados.

**Endurecimento:** Aplicar codificacao de saida sensivel ao contexto (HTML entity encoding, atributo, JavaScript string, URL e CSS) usando bibliotecas testadas em vez de escaping manual. Preferir frameworks com auto-escape (React, Angular, template engines com escape por padrao) e evitar sinks perigosos. Implementar Content Security Policy restritiva baseada em nonce/hash, desabilitando inline e eval. Validar entrada por lista de permissao quando o formato e conhecido e habilitar Trusted Types onde suportado.

**Referências:**
- OWASP Cross Site Scripting Prevention Cheat Sheet - https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html
- CWE-79: Improper Neutralization of Input During Web Page Generation - https://cwe.mitre.org/data/definitions/79.html
- OWASP Top 10 2021 A03 Injection - https://owasp.org/Top10/A03_2021-Injection/
- MDN Content Security Policy (CSP) - https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP

### DNS Rebinding

**Classificação:** `defensiva`

**O que é:** O DNS Rebinding abusa da diferença entre a origem baseada em nome que a Same-Origin Policy usa e o endereço IP para onde esse nome resolve. Ao trocar o IP de um domínio após o carregamento inicial, um site malicioso faz o navegador da vítima enviar requisições a serviços da rede interna como se fossem de mesma origem.

**Como funciona:** A Same-Origin Policy trata a origem pelo nome do host, não pelo IP. Um atacante hospeda um domínio com TTL de DNS muito curto: no primeiro acesso, o nome resolve para o servidor do atacante e entrega o script; logo depois, o mesmo nome é reresolvido para um endereço interno (por exemplo, um serviço em rede local ou um endpoint de metadados). Como o navegador considera a origem inalterada (mesmo nome), o script passa a interagir com o serviço interno no contexto da rede da vítima, contornando o isolamento pretendido. Serviços internos que confiam apenas na origem de rede — sem autenticação nem validação de Host — são os mais expostos. A defesa combina autenticação forte em serviços internos, validação do cabeçalho Host e defesas de rede.

**Detecção:** Monitore serviços internos por requisições cujo cabeçalho Host não corresponda aos nomes esperados e por padrões de acesso originados de navegadores. Registre resoluções de DNS com TTL anormalmente baixo em resolvers corporativos. Alerte para acessos a interfaces administrativas locais vindos de contextos web externos. Ferramentas de proteção de DNS podem sinalizar rebinding para faixas privadas.

**Endurecimento:** Exija autenticação e autorização em todo serviço interno, nunca confiando apenas na origem de rede. Valide o cabeçalho Host contra uma allowlist e rejeite hosts desconhecidos. Aplique proteção contra rebinding no resolver (bloquear respostas públicas que apontam para faixas privadas). Use TLS com certificados válidos em serviços internos para que o rebinding por IP falhe na verificação de nome. Segmente a rede e restrinja quais dispositivos podem alcançar interfaces administrativas.

**Referências:**
- OWASP: DNS Rebinding
- OWASP Cheat Sheet Series: Server Side Request Forgery Prevention
- CWE-350: Reliance on Reverse DNS Resolution for a Security-Sensitive Action
- PortSwigger Research: DNS Rebinding

### DOM Clobbering

**Classificação:** `defensiva`

**O que é:** Tecnica que usa marcacao HTML injetavel (sem script) para sobrescrever variaveis e propriedades globais do JavaScript por meio de elementos nomeados, desviando a logica da aplicacao.

**Como funciona:** Navegadores expoem elementos com atributos id ou name como propriedades no objeto window/document (named access). Quando um atacante consegue injetar HTML mesmo sem scripts — por exemplo em conteudo que passou por sanitizacao que remove <script> mas permite outras tags — ele pode criar elementos cujos nomes colidem com variaveis globais ou propriedades que o codigo espera. Assim, referencias como uma configuracao, uma URL de script ou uma flag de seguranca passam a apontar para o elemento controlado em vez do valor legitimo, alterando o comportamento e podendo encadear ate um sink de XSS. E um vetor eficaz contra sanitizadores que bloqueiam JavaScript mas nao consideram colisao de nomes.

**Detecção:** Revisar o codigo que le propriedades globais/DOM por nome (window.X, document.X, variaveis implicitas) e avaliar se poderiam ser sobrescritas por markup injetado. Verificar a configuracao do sanitizador quanto a atributos id/name em conteudo de usuario. Ferramentas: analise manual de gadgets, DOMPurify em modo restritivo e testes com elementos nomeados em ambiente controlado.

**Endurecimento:** Sanitizar HTML com DOMPurify habilitando protecoes contra clobbering (SANITIZE_DOM e bloqueio/namespacing de atributos id/name em conteudo nao confiavel). Declarar variaveis explicitamente (const/let) e nao depender de globais implicitas nem de acesso a elementos por nome; validar tipos antes de usar valores lidos do DOM. Usar 'use strict', verificar instanceof/typeof em referencias sensiveis e aplicar CSP e Trusted Types como defesa adicional.

**Referências:**
- OWASP DOM Clobbering Prevention Cheat Sheet - https://cheatsheetseries.owasp.org/cheatsheets/DOM_Clobbering_Prevention_Cheat_Sheet.html
- CWE-79: Improper Neutralization of Input During Web Page Generation - https://cwe.mitre.org/data/definitions/79.html
- DOMPurify documentation - https://github.com/cure53/DOMPurify
- HTML Standard - Named access on the Window object - https://html.spec.whatwg.org/multipage/nav-history-apis.html#named-access-on-the-window-object

### Envenenamento e Enganação de Cache Web (Web Cache Poisoning / Deception)

**Classificação:** `escopo_autorizado`

**O que é:** O cache web pode ser induzido a armazenar uma resposta prejudicial e servi-la a outros usuários (envenenamento) ou a guardar conteúdo dinâmico sensível em uma URL aparentemente estática que o atacante depois acessa (enganação). Ambos derivam de discrepâncias entre o que a origem processa e o que o cache usa como chave.

**Como funciona:** Um cache decide reutilizar respostas com base em uma chave (tipicamente método e URL). Quando a origem varia a resposta a partir de entradas não incluídas nessa chave — certos cabeçalhos, parâmetros ou o cabeçalho Host — um atacante pode enviar um valor que faz a origem gerar uma resposta prejudicial que o cache então armazena e serve a vítimas subsequentes com a mesma chave. Na enganação de cache, o atacante engana o cache para tratar uma página autenticada como recurso estático cacheável (por sufixos ou tipos de conteúdo), fazendo-o armazenar dados privados que podem ser recuperados. A causa raiz é a divergência entre a lógica de variação da origem e a chave efetiva do cache. Avaliar esses cenários exige autorização explícita, pois a exploração afeta terceiros.

**Detecção:** Analise a configuração de cache (Cache-Control, Vary, chaves da CDN) e identifique entradas que influenciam a resposta mas não a chave. Monitore respostas cacheadas contendo dados específicos de usuário ou refletindo cabeçalhos de entrada. Alerte para variações inesperadas de conteúdo servido a partir da mesma URL e para recursos autenticados aparecendo com diretivas de cache público. Revise logs da CDN por padrões de HIT em caminhos que deveriam ser privados.

**Endurecimento:** Inclua na chave de cache todas as entradas que afetam a resposta, ou normalize/remova entradas não confiáveis antes do processamento. Defina Cache-Control adequado (no-store/private) para respostas autenticadas ou personalizadas e use Vary corretamente. Não deduza a origem canônica a partir de cabeçalhos controláveis pelo cliente. Configure a CDN para não cachear com base em sufixos de caminho ambíguos e valide o tipo de conteúdo. Teste, sob autorização, cenários de envenenamento e enganação em ambiente controlado antes de produção.

**Referências:**
- PortSwigger Web Security Academy: Web Cache Poisoning
- OWASP: Web Cache Deception
- CWE-524: Use of Cache Containing Sensitive Information
- CWE-436: Interpretation Conflict

### Falsificacao de Requisicao Entre Sites (CSRF)

**Classificação:** `defensiva`

**O que é:** Ataque que induz o navegador autenticado da vitima a enviar uma requisicao de mudanca de estado nao intencional para uma aplicacao onde ela possui sessao valida.

**Como funciona:** Como o navegador anexa automaticamente credenciais de ambiente (cookies de sessao, autenticacao HTTP) a requisicoes para uma origem, uma pagina maliciosa pode emitir uma requisicao cross-site para a aplicacao alvo aproveitando a sessao ja existente. Se a aplicacao autoriza a acao apenas com base no cookie e nao verifica a intencao da requisicao, a acao e executada com a identidade da vitima. Requisicoes que causam efeito colateral (transferencias, alteracao de e-mail/senha, mudanca de permissoes) sao os alvos tipicos. O atacante nao le a resposta; explora a execucao da acao em si.

**Detecção:** Verificar se endpoints que alteram estado exigem um token anti-CSRF imprevisivel e vinculado a sessao, e nao apenas o cookie. Auditar formularios e chamadas de API sensiveis quanto a ausencia de protecao e conferir atributos SameSite dos cookies de sessao. Ferramentas: Burp/ZAP para testar remocao do token, revisao de codigo dos middlewares de protecao e inspecao de cabecalhos de resposta (Set-Cookie).

**Endurecimento:** Adotar cookies de sessao com SameSite=Lax ou Strict e tokens anti-CSRF (padrao synchronizer token ou double-submit) validados no servidor para toda acao de mudanca de estado. Exigir cabecalhos personalizados/verificacao de Origin e Referer em APIs, e usar cookies __Host- com Secure e HttpOnly. Reautenticar ou solicitar confirmacao em operacoes criticas. Nao depender de metodo HTTP como unica barreira e evitar aceitar GET para acoes com efeito colateral.

**Referências:**
- OWASP Cross-Site Request Forgery Prevention Cheat Sheet - https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html
- CWE-352: Cross-Site Request Forgery - https://cwe.mitre.org/data/definitions/352.html
- OWASP Top 10 2021 A01 Broken Access Control - https://owasp.org/Top10/A01_2021-Broken_Access_Control/
- RFC 6265bis / SameSite cookies - https://datatracker.ietf.org/doc/html/draft-ietf-httpbis-rfc6265bis

### Integridade de Sub-recursos e Scripts de Terceiros (SRI / Defesa contra Magecart)

**Classificação:** `defensiva`

**O que é:** Páginas que carregam scripts de terceiros (CDNs, tags de marketing, widgets) ficam expostas ao comprometimento desses provedores: um script alterado executa no contexto da aplicação e pode roubar dados de formulários (skimming/Magecart). A Integridade de Sub-recursos (SRI) e o controle de origens reduzem esse risco.

**Como funciona:** O navegador executa scripts de terceiros com os mesmos privilégios do código próprio da página, incluindo acesso ao DOM, cookies acessíveis e campos de formulário. Se o provedor externo é comprometido ou serve conteúdo alterado, o código malicioso passa a rodar em todos os visitantes sem tocar no servidor da aplicação — a essência dos ataques de skimming em páginas de pagamento. A Subresource Integrity permite declarar um hash criptográfico esperado do recurso: o navegador só o executa se o conteúdo baixado corresponder ao hash, bloqueando substituições silenciosas. Combinada com uma política de origens permitidas, reduz a superfície de cadeia de suprimentos no lado do cliente. A defesa completa exige inventariar, minimizar e monitorar todos os scripts externos.

**Detecção:** Mantenha inventário de todos os recursos externos carregados e monitore alterações em seus hashes ou origens. Use CSP em modo de relatório para descobrir scripts inesperados e violações. Monitore, quando possível, exfiltração para domínios não autorizados a partir de páginas sensíveis. Alerte para adição de tags de terceiros fora do processo de mudança e para recursos servidos sem atributo integrity.

**Endurecimento:** Aplique o atributo integrity com hash (SRI) e crossorigin em scripts e folhas de estilo de terceiros com URL estável. Prefira hospedar/versionar bibliotecas críticas em vez de referenciar versões mutáveis. Restrinja origens de script via Content-Security-Policy e limite conexões de saída de páginas sensíveis. Minimize a quantidade de terceiros, isole widgets em iframes quando viável, e trate cada dependência de front-end sob o mesmo rigor de governança da cadeia de suprimentos, com revisão de mudanças e monitoramento contínuo.

**Referências:**
- W3C: Subresource Integrity
- MDN Web Docs: Subresource Integrity
- OWASP Cheat Sheet Series: Third Party JavaScript Management
- CWE-353: Missing Support for Integrity Check

### Misconfiguracao de CORS (CORS Misconfiguration)

**Classificação:** `defensiva`

**O que é:** Configuracao incorreta do Cross-Origin Resource Sharing que relaxa a politica de mesma origem e permite que sites nao confiaveis leiam respostas autenticadas da aplicacao.

**Como funciona:** O CORS instrui o navegador a liberar leitura cross-origin com base em cabecalhos de resposta como Access-Control-Allow-Origin e Access-Control-Allow-Credentials. Configuracoes inseguras incluem refletir dinamicamente o cabecalho Origin da requisicao, confiar em correspondencias de substring/sufixo fraceis, permitir null como origem, ou combinar allow-credentials true com origem ampla. Quando credenciais sao permitidas e a origem e refletida sem validacao rigorosa, um site malicioso pode fazer o navegador da vitima autenticada emitir requisicoes e ler as respostas, expondo dados sensiveis. O erro esta na politica do servidor, nao no navegador, que apenas aplica os cabecalhos recebidos.

**Detecção:** Enviar requisicoes com diferentes valores de Origin e observar se o servidor reflete a origem, aceita null ou usa correspondencia parcial, especialmente junto com Access-Control-Allow-Credentials: true. Revisar o codigo/middleware de CORS quanto a listas dinamicas construidas a partir da requisicao. Ferramentas: Burp/ZAP, scripts de teste de cabecalhos CORS e analise de logs de preflight (OPTIONS).

**Endurecimento:** Usar lista de permissao explicita e exata de origens confiaveis, validando o cabecalho Origin por igualdade completa; nunca refletir origem arbitraria nem usar wildcard com credenciais. Evitar aceitar a origem null e correspondencias por substring. Conceder o minimo em Allow-Methods e Allow-Headers, e centralizar a politica de CORS. Proteger endpoints sensiveis com autenticacao que nao dependa apenas de cookies de ambiente e revisar a configuracao em cada ambiente.

**Referências:**
- OWASP HTML5 Security / CORS - https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html
- CWE-942: Permissive Cross-domain Policy with Untrusted Domains - https://cwe.mitre.org/data/definitions/942.html
- CWE-346: Origin Validation Error - https://cwe.mitre.org/data/definitions/346.html
- MDN Cross-Origin Resource Sharing (CORS) - https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS
- Fetch Standard (CORS protocol) - https://fetch.spec.whatwg.org/

### Poluicao de Prototipo no Cliente (Client-side Prototype Pollution)

**Classificação:** `defensiva`

**O que é:** Vulnerabilidade em que o atacante consegue injetar propriedades em Object.prototype no JavaScript do cliente, afetando o comportamento de toda a aplicacao e habilitando cadeias de gadgets.

**Como funciona:** Funcoes inseguras de merge recursivo, clone profundo ou parsing de parametros que copiam chaves controlaveis (como __proto__, constructor, prototype) sem filtragem podem escrever no prototipo compartilhado de Object. Como quase todos os objetos herdam desse prototipo, propriedades poluidas passam a existir globalmente, alterando valores padrao que o codigo assume seguros. Quando existe um gadget — trecho que le uma propriedade herdada e a usa em um sink (por exemplo, definindo src de script, opcoes de sanitizacao ou HTML) — a poluicao pode escalar para DOM XSS ou bypass de controles. A raiz e a manipulacao insegura de chaves dinamicas.

**Detecção:** Revisar funcoes de merge/extend/clone e roteadores de parametros de query quanto a tratamento de __proto__, constructor e prototype. Testar se atribuir tais chaves altera propriedades de objetos nao relacionados. Ferramentas: extensao/scanner DOM Invader com deteccao de prototype pollution, analise estatica (CodeQL, Semgrep) e auditoria de dependencias (npm audit) para libs vulneraveis.

**Endurecimento:** Bloquear chaves perigosas nas operacoes de merge/clone e evitar recursao ingenua sobre objetos controlados pelo usuario. Usar Object.create(null) para mapas, Map em vez de objetos literais, e Object.freeze(Object.prototype) quando viavel. Preferir bibliotecas atualizadas e resistentes a poluicao e validar entrada por esquema. Combinar com CSP e Trusted Types para dificultar a exploracao de gadgets ate sinks de XSS.

**Referências:**
- CWE-1321: Improperly Controlled Modification of Object Prototype Attributes - https://cwe.mitre.org/data/definitions/1321.html
- OWASP Prototype Pollution Prevention Cheat Sheet - https://cheatsheetseries.owasp.org/cheatsheets/Prototype_Pollution_Prevention_Cheat_Sheet.html
- PortSwigger Web Security Academy - Prototype Pollution - https://portswigger.net/web-security/prototype-pollution
- MDN Object.prototype - https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object

### Redirecionamento Aberto (Open Redirect)

**Classificação:** `defensiva`

**O que é:** Falha em que a aplicacao redireciona o navegador para uma URL controlada por parametro sem validar o destino, permitindo abuso em phishing e, as vezes, roubo de tokens.

**Como funciona:** Endpoints de redirecionamento (parametros como return, next, redirect_uri, url) leem um destino da requisicao e o usam em uma resposta 3xx ou em navegacao no cliente sem verificar se pertence a um conjunto confiavel. Um atacante monta um link na origem legitima que redireciona para um site externo controlado, aproveitando a confianca no dominio original para phishing convincente. Em fluxos OAuth/SSO, um redirect_uri mal validado pode vazar codigos ou tokens. Tambem existem variantes baseadas em DOM que usam location para navegar a partir de dados nao confiaveis.

**Detecção:** Identificar todos os pontos que definem Location ou manipulam window.location a partir de parametros e verificar se ha validacao do destino. Testar valores absolutos, esquemas alternativos, barras invertidas e ofuscacoes de host. Ferramentas: DAST, analise estatica de sinks de navegacao e revisao especifica dos redirect_uri registrados em provedores de identidade.

**Endurecimento:** Preferir destinos internos fixos ou referenciados por identificador em vez de URL crua; quando URLs forem necessarias, validar contra lista de permissao de hosts/paths e aceitar apenas caminhos relativos quando possivel. Em OAuth, exigir correspondencia exata de redirect_uri pre-registrado. Exibir pagina intersticial de aviso para redirecionamentos externos e normalizar/parsear a URL com API robusta antes de decidir. Aplicar as mesmas checagens nos sinks de navegacao do cliente.

**Referências:**
- OWASP Unvalidated Redirects and Forwards Cheat Sheet - https://cheatsheetseries.owasp.org/cheatsheets/Unvalidated_Redirects_and_Forwards_Cheat_Sheet.html
- CWE-601: URL Redirection to Untrusted Site (Open Redirect) - https://cwe.mitre.org/data/definitions/601.html
- OWASP Top 10 2021 A01 Broken Access Control - https://owasp.org/Top10/A01_2021-Broken_Access_Control/
- RFC 6749 OAuth 2.0 (redirect_uri validation) - https://datatracker.ietf.org/doc/html/rfc6749

### Reverse Tabnabbing (window.opener)

**Classificação:** `defensiva`

**O que é:** Ataque em que uma pagina aberta em nova aba a partir de um link externo usa a referencia window.opener para redirecionar a aba original para um site de phishing.

**Como funciona:** Ao abrir um link com target=_blank sem protecao, a nova pagina recebe uma referencia window.opener para a pagina de origem. Mesmo sem acesso ao conteudo por causa da mesma origem, a pagina de destino pode alterar a localizacao da aba original via window.opener.location, redirecionando a vitima para uma pagina falsa quando ela retornar. Como a aba original ja era confiavel, o usuario tende a nao perceber a troca e pode inserir credenciais na pagina forjada. O vetor depende do vazamento da referencia opener para conteudo nao confiavel.

**Detecção:** Auditar links e chamadas window.open que abrem destinos externos em nova aba/janela verificando a ausencia de rel=noopener e a exposicao de window.opener. Revisar componentes que geram links dinamicos a partir de conteudo de usuario. Ferramentas: linters de HTML/JS, revisao de codigo e varredura por target=_blank sem rel adequado.

**Endurecimento:** Adicionar rel="noopener noreferrer" a todos os links target=_blank e passar 'noopener' em window.open para destinos nao confiaveis. Lembrar que navegadores modernos ja aplicam noopener por padrao em target=_blank, mas manter a diretiva explicita para compatibilidade e defesa em profundidade. Para conteudo gerado por usuario, sanitizar atributos de link e considerar rel=nofollow. Padronizar um helper de criacao de links seguros no front-end.

**Referências:**
- OWASP HTML5 Security Cheat Sheet (Tabnabbing) - https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html
- CWE-1022: Use of Web Link to Untrusted Target with window.opener Access - https://cwe.mitre.org/data/definitions/1022.html
- MDN rel=noopener - https://developer.mozilla.org/en-US/docs/Web/HTML/Attributes/rel/noopener
- web.dev - Links to cross-origin destinations are unsafe - https://web.dev/articles/external-anchors-use-rel-noopener

### SameSite e Defesas Anti-CSRF em Cookies (SameSite & Cookie Hardening)

**Classificação:** `defensiva`

**O que é:** Conjunto de atributos e prefixos de cookie, com destaque para SameSite, que reduzem o envio de credenciais em requisicoes cross-site e reforcam as defesas contra CSRF e sequestro de sessao.

**Como funciona:** O atributo SameSite controla se o cookie acompanha requisicoes originadas de outros sites: Strict nao envia em nenhuma navegacao cross-site, Lax envia apenas em navegacoes de nivel superior por GET, e None (que exige Secure) permite envio cross-site. Como o CSRF depende do envio automatico de cookies em requisicoes cross-site, SameSite Lax/Strict corta boa parte desse vetor. Atributos complementares — Secure (so em HTTPS), HttpOnly (inacessivel a JavaScript, limitando roubo via XSS) e o prefixo __Host- (fixa path e proibe Domain) — endurecem o cookie de sessao. Ainda assim, SameSite nao substitui totalmente tokens anti-CSRF, pois excecoes de navegacao e configuracoes None deixam brechas.

**Detecção:** Inspecionar os cabecalhos Set-Cookie dos cookies de sessao e autenticacao quanto a SameSite, Secure, HttpOnly e prefixos. Verificar se cookies sensiveis usam SameSite=None sem justificativa e se ha token anti-CSRF nas acoes de mudanca de estado. Ferramentas: DevTools do navegador, scanners de cabecalhos, ZAP/Burp e revisao da configuracao de sessao no servidor.

**Endurecimento:** Definir cookies de sessao com HttpOnly, Secure e SameSite=Lax (ou Strict quando o fluxo permitir) e usar o prefixo __Host- para fixar escopo. Manter tokens anti-CSRF (synchronizer ou double-submit) para operacoes de estado como defesa em profundidade, sem depender apenas de SameSite. Reservar SameSite=None+Secure somente para casos cross-site legitimos e revisar cada um. Combinar com verificacao de Origin/Referer e reautenticacao em acoes criticas.

**Referências:**
- OWASP Cross-Site Request Forgery Prevention Cheat Sheet - https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html
- OWASP Session Management Cheat Sheet - https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html
- RFC 6265bis (SameSite / cookie prefixes) - https://datatracker.ietf.org/doc/html/draft-ietf-httpbis-rfc6265bis
- MDN Set-Cookie SameSite - https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie/SameSite
- CWE-1275: Sensitive Cookie with Improper SameSite Attribute - https://cwe.mitre.org/data/definitions/1275.html

### Sanitizacao de HTML e Trusted Types (HTML Sanitization / Trusted Types)

**Classificação:** `defensiva`

**O que é:** Conjunto de controles defensivos que neutralizam HTML nao confiavel antes da insercao no DOM e restringem quais valores podem alcancar sinks perigosos.

**Como funciona:** Sanitizadores como o DOMPurify analisam o HTML de entrada e removem elementos, atributos e URLs perigosos com base em uma politica de lista de permissao, retornando marcacao segura para renderizacao. Trusted Types e um mecanismo do navegador, ativado via CSP (require-trusted-types-for 'script'), que impede a atribuicao de strings cruas a sinks sensiveis (innerHTML, script src, eval), exigindo que os valores passem por politicas explicitas e revisadas. Juntos, movem a seguranca de escaping ad hoc espalhado para pontos centrais e auditaveis: o sanitizador limpa o conteudo e o Trusted Types garante que nenhum caminho escreva HTML/script sem passar pela politica. Isso reduz drasticamente a superficie de DOM XSS.

**Detecção:** Verificar se toda escrita de HTML dinamico passa por um sanitizador com configuracao restritiva e se Trusted Types esta ativo (ao menos em report-only) coletando violacoes. Auditar politicas do DOMPurify quanto a permissoes excessivas (tags/atributos perigosos, hooks inseguros). Ferramentas: relatorios de violacao de CSP/Trusted Types, analise estatica de sinks e revisao das configuracoes do sanitizador.

**Endurecimento:** Centralizar a renderizacao de HTML nao confiavel em um sanitizador testado (DOMPurify) com politica minima e revisar customizacoes. Ativar Trusted Types em producao com politicas nomeadas e minimas, tratando cada excecao como decisao de seguranca. Manter as bibliotecas atualizadas, preferir textContent quando HTML rico nao e necessario e combinar com CSP restritiva. Escrever testes que garantam que payloads conhecidos sao neutralizados e monitorar regressoes.

**Referências:**
- OWASP Cross Site Scripting Prevention Cheat Sheet - https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html
- W3C Trusted Types - https://www.w3.org/TR/trusted-types/
- DOMPurify - https://github.com/cure53/DOMPurify
- CWE-116: Improper Encoding or Escaping of Output - https://cwe.mitre.org/data/definitions/116.html
- web.dev - Prevent DOM-based XSS with Trusted Types - https://web.dev/articles/trusted-types

### Segurança de WebSockets (WebSocket Security / CSWSH)

**Classificação:** `defensiva`

**O que é:** Conexões WebSocket não herdam automaticamente as proteções de mesma-origem e anti-CSRF do HTTP tradicional. Sem validação de Origin e autenticação do handshake, um site malicioso pode abrir um canal autenticado em nome da vítima (Cross-Site WebSocket Hijacking) e as mensagens trocadas continuam sendo entrada não confiável.

**Como funciona:** O handshake WebSocket começa como uma requisição HTTP de upgrade que carrega cookies da vítima, mas não é restringido pela Same-Origin Policy nem exige token anti-CSRF por padrão. Se o servidor autentica a conexão apenas por cookie de sessão e não verifica o cabeçalho Origin, uma página de terceiros pode iniciar a conexão e ler/enviar dados no contexto autenticado da vítima — o análogo do CSRF para canais persistentes. Após estabelecido, cada mensagem recebida é dado não confiável e deve ser validada e codificada conforme o contexto de destino (evitando XSS ao renderizar, ou injeção ao processar). O canal bidirecional e de longa duração também amplia superfície para consumo excessivo de recursos.

**Detecção:** Registre e monitore handshakes com Origin ausente ou não pertencente à allowlist e conexões de origens inesperadas. Acompanhe métricas por conexão (mensagens por segundo, tamanho de payload, tempo de vida) para identificar abuso ou flood. Correlacione conexões WebSocket autenticadas com sessões válidas e alerte quando um mesmo token abre canais simultâneos anômalos. Inspecione mensagens malformadas ou fora do protocolo de aplicação esperado.

**Endurecimento:** Valide explicitamente o cabeçalho Origin contra uma allowlist no handshake e rejeite o restante. Não dependa apenas do cookie de sessão: exija um token de autenticação vinculado ao canal (por exemplo, token de curta duração emitido pela aplicação e verificado no upgrade). Use sempre wss:// (TLS). Trate cada mensagem como entrada não confiável com validação de esquema e codificação de saída por contexto no cliente. Aplique limites de taxa, tamanho de mensagem e número de conexões por usuário, e encerre canais ociosos ou após expiração da sessão.

**Referências:**
- OWASP Cheat Sheet Series: WebSocket Security
- PortSwigger Web Security Academy: WebSockets
- RFC 6455: The WebSocket Protocol
- CWE-1385: Missing Origin Validation in WebSockets

### Sequestro de Cliques (Clickjacking)

**Classificação:** `defensiva`

**O que é:** Ataque de redirecionamento de interface em que a aplicacao alvo e carregada em um frame transparente sobre conteudo isca, fazendo a vitima clicar em acoes que nao pretendia.

**Como funciona:** O atacante embute a pagina alvo em um iframe com opacidade reduzida ou posicionamento sobreposto e alinha elementos de uma pagina isca para que os cliques da vitima recaiam sobre botoes sensiveis da aplicacao enquadrada. Como a vitima esta autenticada na origem alvo, os cliques disparam acoes legitimas (curtir, autorizar, alterar configuracoes, confirmar transacoes) sem que ela perceba. Variacoes incluem manipulacao de arrastar-e-soltar e captura de digitacao. A defesa central e impedir que a aplicacao seja enquadrada por origens nao confiaveis.

**Detecção:** Verificar a presenca e o valor dos cabecalhos de resposta que controlam enquadramento (Content-Security-Policy frame-ancestors e o legado X-Frame-Options) em todas as paginas sensiveis. Testar se a pagina pode ser carregada em iframe de outra origem. Ferramentas: scanners de cabecalhos de seguranca (securityheaders, ZAP) e revisao de configuracao de servidor/proxy.

**Endurecimento:** Definir Content-Security-Policy: frame-ancestors 'self' (ou lista explicita de origens confiaveis) e manter X-Frame-Options: DENY/SAMEORIGIN para navegadores legados. Aplicar os cabecalhos globalmente, inclusive em erros e paginas de autenticacao. Usar cookies SameSite para reduzir impacto de acoes enquadradas e, em fluxos criticos, exigir confirmacao explicita ou reautenticacao que resista a UI redress.

**Referências:**
- OWASP Clickjacking Defense Cheat Sheet - https://cheatsheetseries.owasp.org/cheatsheets/Clickjacking_Defense_Cheat_Sheet.html
- CWE-1021: Improper Restriction of Rendered UI Layers or Frames - https://cwe.mitre.org/data/definitions/1021.html
- MDN CSP frame-ancestors - https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy/frame-ancestors
- MDN X-Frame-Options - https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Frame-Options

## Controle de Acesso e Lógica de Autorização

### Atribuição em Massa de Campos de Autorização (Mass Assignment)

**Classificação:** `defensiva`

**O que é:** Falha em que o binding automático de campos da requisição para objetos internos permite ao cliente definir atributos sensíveis, como papel ou dono, escalando privilégio ou alterando autorização.

**Como funciona:** Frameworks que vinculam automaticamente os campos do corpo da requisição às propriedades de um objeto de domínio podem incluir campos que o usuário não deveria controlar (por exemplo, papel, is_admin, owner_id, status de verificação). Se não houver restrição explícita de quais campos são aceitos, o cliente pode enviar atributos extras e sobrescrever propriedades de autorização. O resultado é escalonamento de privilégio ou mudança de propriedade por manipulação de payload. A causa raiz é a exposição excessiva de propriedades sem controle de quais campos são graváveis por qual papel (autorização em nível de propriedade de objeto).

**Detecção:** Revisão de endpoints que usam binding automático e verificação de allowlist de campos graváveis; testes enviando campos sensíveis extras (role, owner) em ambiente autorizado. Em logs: alteração de campos de privilégio fora do fluxo esperado, contas mudando de papel após atualização de perfil. Ferramentas: SAST para binders automáticos, revisão de DTOs/serializers, testes de propriedade de objeto.

**Endurecimento:** Usar allowlist explícita de campos graváveis (DTOs específicos por operação) e nunca vincular diretamente objetos de domínio à entrada; separar campos de autorização em fluxos protegidos. Ignorar/rejeitar propriedades não esperadas, aplicar autorização em nível de propriedade e diferenciar campos editáveis por papel. Cobrir com testes que tentam gravar atributos sensíveis via payload.

**Referências:**
- OWASP API Security Top 10 2023 API6/API3: Broken Object Property Level Authorization - https://owasp.org/API-Security/editions/2023/en/0xa3-broken-object-property-level-authorization/
- CWE-915: Improperly Controlled Modification of Dynamically-Determined Object Attributes - https://cwe.mitre.org/data/definitions/915.html
- OWASP Mass Assignment Cheat Sheet - https://cheatsheetseries.owasp.org/cheatsheets/Mass_Assignment_Cheat_Sheet.html
- OWASP Top 10 2021 A01: Broken Access Control - https://owasp.org/Top10/A01_2021-Broken_Access_Control/

### Autorização Quebrada em Nível de Função (BFLA)

**Classificação:** `defensiva`

**O que é:** Falha em que uma API não restringe corretamente quais papéis podem invocar funções ou verbos administrativos, permitindo que usuários comuns executem operações privilegiadas.

**Como funciona:** Diferente do BOLA (nível de objeto), o BFLA é sobre autorização de funções/ações: endpoints administrativos ou verbos sensíveis (DELETE, PUT, ações de gestão) ficam acessíveis a papéis que não deveriam invocá-los. Ocorre quando a checagem de papel está ausente, é inconsistente entre rotas, ou depende de convenções (por exemplo, presumir que só o front-end de admin chama /admin/...). Estruturas de rotas previsíveis e a facilidade de trocar o verbo HTTP tornam funções privilegiadas descobríveis. A raiz é a falta de mapeamento explícito de qual papel pode executar cada função, aplicado no servidor.

**Detecção:** Enumerar todos os endpoints e verbos e confrontar com uma matriz de papel-função; testar com conta de baixo privilégio chamando rotas administrativas. Em logs: chamadas bem-sucedidas a rotas de gestão por contas não administrativas, uso de verbos inesperados. Ferramentas: inventário de rotas/OpenAPI, testes de autorização por papel, revisão de middlewares de autorização por grupo de rotas.

**Endurecimento:** Negar por padrão e exigir declaração explícita do papel autorizado em cada função/rota, preferencialmente por decorator/middleware baseado no papel da sessão do servidor. Segregar rotas administrativas com autorização reforçada e revisar consistência entre todos os verbos de um recurso. Manter e testar automaticamente a matriz papel-função; evitar depender da UI para ocultar funções.

**Referências:**
- OWASP API Security Top 10 2023 API5: Broken Function Level Authorization - https://owasp.org/API-Security/editions/2023/en/0xa5-broken-function-level-authorization/
- CWE-285: Improper Authorization - https://cwe.mitre.org/data/definitions/285.html
- CWE-862: Missing Authorization - https://cwe.mitre.org/data/definitions/862.html
- OWASP Authorization Cheat Sheet - https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html

### Autorização Quebrada em Nível de Objeto (BOLA)

**Classificação:** `defensiva`

**O que é:** Manifestação de IDOR no contexto de APIs, o item nº 1 do OWASP API Security Top 10, em que endpoints não validam se o chamador pode acessar o objeto identificado pelo parâmetro da requisição.

**Como funciona:** APIs REST/GraphQL frequentemente expõem identificadores de objetos em rotas e corpos (por exemplo, /api/pedidos/{id}); o BOLA ocorre quando o backend recupera o objeto pelo ID fornecido sem confrontar a identidade autenticada com a propriedade/escopo do objeto. Por serem previsíveis e a superfície de endpoints ser ampla, APIs amplificam o problema: cada operação sobre objeto é um ponto de decisão de autorização. A causa é a ausência de verificação consistente de nível de objeto em cada handler, muitas vezes agravada por autorização feita apenas no gateway (nível de rota) e não no recurso. GraphQL adiciona risco por resolvers que carregam objetos sem checar escopo.

**Detecção:** Testes automatizados por dois usuários do mesmo papel tentando acessar objetos um do outro; inventário de endpoints que aceitam IDs e verificação de que cada um aplica checagem de escopo. Em observabilidade: taxas anômalas de acesso a IDs distintos por token, respostas 200 para objetos de outro tenant. Ferramentas: testes de contrato de API, scanners de autorização de API com múltiplas contas, revisão de resolvers GraphQL.

**Endurecimento:** Implementar checagem de autorização por objeto em cada resolver/handler, sempre derivando o escopo da identidade autenticada (token) e nunca do parâmetro do cliente. Usar uma função central de autorização (can(user, action, object)) invocada antes de retornar ou modificar qualquer objeto; isolar por tenant nas consultas. Adotar identificadores não adivinháveis como defesa complementar e cobrir com testes de segregação de tenants.

**Referências:**
- OWASP API Security Top 10 2023 API1: Broken Object Level Authorization - https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/
- CWE-639: Authorization Bypass Through User-Controlled Key - https://cwe.mitre.org/data/definitions/639.html
- CWE-284: Improper Access Control - https://cwe.mitre.org/data/definitions/284.html
- OWASP Authorization Cheat Sheet - https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html

### Condições de Corrida e TOCTOU (Race Conditions / TOCTOU)

**Classificação:** `defensiva`

**O que é:** Condições de corrida ocorrem quando o resultado de uma operação depende do momento de requisições concorrentes. Em TOCTOU (time-of-check to time-of-use), um valor validado muda entre a verificação e o uso, permitindo ultrapassar limites, resgatar recursos mais de uma vez ou contornar checagens.

**Como funciona:** Muitos fluxos verificam uma condição (saldo suficiente, cupom não usado, limite não atingido) e depois agem sobre ela em passos separados e não atômicos. Se várias requisições chegam quase simultaneamente, todas podem passar pela verificação antes que qualquer uma atualize o estado, produzindo efeitos além do permitido — gasto duplo, resgate múltiplo do mesmo item, ou ultrapassar limites de taxa. A janela entre checagem e uso é a vulnerabilidade. A correção conceitual é tornar a sequência checar-e-agir atômica: usar transações com o nível de isolamento adequado, bloqueios (pessimistas ou otimistas com versão), operações condicionais no armazenamento, ou chaves de idempotência que garantem que uma requisição repetida não produza efeito adicional.

**Detecção:** Monitore rajadas de requisições quase simultâneas ao mesmo recurso ou operação sensível vindas do mesmo usuário/token. Alerte para inconsistências detectadas por reconciliação (saldos negativos, contagens que excedem limites, itens de uso único consumidos mais de uma vez). Registre chaves de idempotência e sinalize colisões. Testes de carga concorrente direcionados a endpoints de escrita ajudam a expor janelas antes da produção.

**Endurecimento:** Torne operações críticas atômicas com transações de banco e o isolamento apropriado, ou use atualizações condicionais (compare-and-set) e restrições de unicidade que o armazenamento imponha. Aplique bloqueio otimista com número de versão ou pessimista com locks de linha em recursos disputados. Exija chaves de idempotência em operações não repetíveis (pagamentos, resgates). Centralize a contagem de limites em um armazenamento consistente, e evite validar em um serviço e agir em outro sem coordenação transacional.

**Referências:**
- PortSwigger Web Security Academy: Race Conditions
- OWASP: Testing for Race Conditions
- CWE-362: Concurrent Execution using Shared Resource with Improper Synchronization
- CWE-367: Time-of-check Time-of-use (TOCTOU) Race Condition

### Controle de Acesso Baseado em Atributo (ABAC)

**Classificação:** `defensiva`

**O que é:** Modelo de autorização em que decisões são tomadas avaliando atributos do sujeito, do recurso, da ação e do ambiente contra políticas, permitindo controle contextual e granular.

**Como funciona:** No ABAC, a decisão de acesso é o resultado de uma política que avalia atributos: quem é o sujeito (departamento, nível), qual o recurso (classificação, dono), qual a ação e qual o contexto (horário, localização, risco). A arquitetura separa o ponto de decisão de política (PDP), que avalia as regras, do ponto de imposição (PEP), que as aplica na requisição, alimentados por informações de atributos. Isso oferece granularidade e adaptação a contexto que o RBAC puro não expressa, ao custo de maior complexidade de gestão e teste de políticas. A confiabilidade depende da integridade e da fonte dos atributos usados na decisão.

**Detecção:** Revisar políticas quanto a conflitos, regras permissivas por padrão e atributos de fonte não confiável; testar decisões com combinações de atributos limítrofes. Em logs: decisões de autorização com o motivo/política aplicada, mudanças de atributo que alteram acesso. Ferramentas: engines de política (motor de decisão externo), testes de política, análise de cobertura de regras.

**Endurecimento:** Adotar arquitetura PDP/PEP com negação por padrão, garantindo que atributos venham de fontes confiáveis e íntegras; versionar e testar políticas como código. Minimizar a superfície de atributos controláveis pelo usuário, registrar a política e os atributos que fundamentaram cada decisão, e revisar regras periodicamente. Combinar com RBAC (papéis como atributo) para equilibrar simplicidade e contexto.

**Referências:**
- NIST SP 800-162: Guide to Attribute Based Access Control (ABAC) - https://csrc.nist.gov/publications/detail/sp/800-162/final
- NIST SP 800-207 Zero Trust Architecture - https://csrc.nist.gov/publications/detail/sp/800-207/final
- OASIS XACML - https://www.oasis-open.org/committees/xacml/
- OWASP Authorization Cheat Sheet - https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html

### Controle de Acesso Baseado em Função (RBAC)

**Classificação:** `defensiva`

**O que é:** Modelo de autorização em que permissões são atribuídas a papéis e usuários recebem papéis, simplificando a gestão de acesso e a aplicação do menor privilégio.

**Como funciona:** No RBAC, permissões (ações sobre recursos) são agrupadas em papéis, e usuários herdam permissões ao serem associados a papéis; a decisão de acesso consiste em verificar se algum papel do usuário concede a permissão requerida. Modelos formais incluem hierarquia de papéis (herança) e restrições de separação de deveres para impedir combinações perigosas. O RBAC é eficiente quando os direitos se alinham a funções organizacionais estáveis, mas pode sofrer explosão de papéis quando a granularidade exige muitas variações contextuais. A decisão deve sempre ser imposta no servidor, com papéis vindos de fonte confiável.

**Detecção:** Revisar a matriz papel-permissão versus a implementação; identificar papéis excessivamente amplos, permissões órfãs e usuários com papéis acumulados (creep de privilégio). Em logs: uso de permissões raramente exercidas, atribuições fora de processo. Ferramentas: revisão periódica de acesso (access review/recertification), análise de papéis, testes de autorização por papel.

**Endurecimento:** Definir papéis por menor privilégio, aplicar separação de deveres e evitar papéis-coringa; centralizar a decisão em um mecanismo de autorização imposto no servidor. Derivar papéis de fonte confiável (não do cliente), revisar e recertificar acessos periodicamente, e remover papéis ao mudar de função. Complementar com ABAC quando decisões dependerem de contexto que o RBAC puro não expressa bem.

**Referências:**
- NIST RBAC / INCITS 359 - https://csrc.nist.gov/projects/role-based-access-control
- NIST SP 800-207 Zero Trust Architecture - https://csrc.nist.gov/publications/detail/sp/800-207/final
- OWASP Authorization Cheat Sheet - https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html
- CWE-269: Improper Privilege Management - https://cwe.mitre.org/data/definitions/269.html

### Controle de Acesso Quebrado (Broken Access Control)

**Classificação:** `defensiva`

**O que é:** Falha em que a aplicação não impõe corretamente as restrições sobre o que um usuário autenticado pode ver ou fazer, permitindo acesso a dados ou funções fora de sua permissão.

**Como funciona:** A autorização é a etapa que decide se um sujeito (usuário, sessão, token) pode executar uma ação sobre um recurso; o controle de acesso quebra quando essa verificação está ausente, é feita apenas no cliente (front-end) ou depende de dados manipuláveis pelo requisitante. Mecanismos comuns de falha incluem confiar em parâmetros de URL/corpo para determinar identidade ou papel, ocultar funções apenas na interface (security through obscurity), e ausência de verificação por objeto no lado servidor. O modelo correto trata autenticação (quem é) e autorização (o que pode) como camadas distintas, negando por padrão e exigindo checagem explícita a cada requisição. A causa raiz normalmente é lógica de negócio dispersa e não centralizada, sem um ponto único de decisão de política.

**Detecção:** Revisão de código buscando endpoints/handlers sem verificação de permissão antes de operações sensíveis; testes com contas de papéis distintos comparando respostas; matriz de acesso (papel x recurso x ação) confrontada com o comportamento real. Em logs, indicadores são altas taxas de 403 concentradas por conta (enumeração), acessos bem-sucedidos a IDs sequenciais, e uso de verbos HTTP não esperados. Ferramentas: linters de autorização, testes de integração de autorização, ferramentas de análise de superfície de API (Burp Suite/ZAP com contas múltiplas) em ambiente autorizado.

**Endurecimento:** Negar por padrão (deny-by-default) e exigir decisão explícita de autorização em todo endpoint; centralizar a política em um único mecanismo (middleware/policy engine) em vez de espalhar ifs. Aplicar o princípio do menor privilégio, validar autorização no servidor a cada requisição usando a identidade da sessão/token (nunca IDs vindos do cliente), e cobrir a matriz de acesso com testes automatizados. Registrar decisões de acesso negado e revisar periodicamente papéis e permissões.

**Referências:**
- OWASP Top 10 2021 A01: Broken Access Control - https://owasp.org/Top10/A01_2021-Broken_Access_Control/
- CWE-284: Improper Access Control - https://cwe.mitre.org/data/definitions/284.html
- CWE-862: Missing Authorization - https://cwe.mitre.org/data/definitions/862.html
- CWE-863: Incorrect Authorization - https://cwe.mitre.org/data/definitions/863.html
- OWASP Authorization Cheat Sheet - https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html
- NIST SP 800-162 (ABAC) - https://csrc.nist.gov/publications/detail/sp/800-162/final

### Escalonamento Horizontal de Privilégio (Horizontal Privilege Escalation)

**Classificação:** `defensiva`

**O que é:** Situação em que um usuário acessa dados ou recursos de outro usuário de mesmo nível de privilégio, atravessando a fronteira de propriedade sem elevar o papel.

**Como funciona:** No escalonamento horizontal o papel não muda; o que falha é o isolamento entre pares (usuário A acessa recursos de B, ou tenant X acessa dados de Y). Está intimamente ligado a IDOR/BOLA: o servidor recupera recursos pelo identificador fornecido sem filtrar pelo dono/tenant da sessão. Também ocorre em fluxos que confiam em um identificador de conta enviado pelo cliente para escolher o contexto. A causa raiz é a ausência de checagem de propriedade/escopo do recurso vinculada à identidade autenticada.

**Detecção:** Testes entre duas contas do mesmo papel acessando recursos uma da outra; revisão de consultas que não incluem filtro de dono/tenant. Em logs: acesso a IDs pertencentes a outras contas, respostas 200 esperadas como 403/404, padrões de enumeração por sessão. Ferramentas: testes de segregação de tenant, scanners de autorização multiconta, análise das cláusulas de escopo nas consultas.

**Endurecimento:** Vincular toda leitura/gravação ao dono ou tenant derivado da sessão, aplicando filtro de escopo em nível de consulta e, quando possível, isolamento no banco (row-level security). Nunca selecionar o contexto de conta a partir de parâmetro do cliente; centralizar a checagem de propriedade. Cobrir com testes automatizados de acesso cruzado e monitorar tentativas de acesso fora de escopo.

**Referências:**
- CWE-639: Authorization Bypass Through User-Controlled Key - https://cwe.mitre.org/data/definitions/639.html
- CWE-284: Improper Access Control - https://cwe.mitre.org/data/definitions/284.html
- OWASP Top 10 2021 A01: Broken Access Control - https://owasp.org/Top10/A01_2021-Broken_Access_Control/
- OWASP Authorization Cheat Sheet - https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html

### Escalonamento Vertical de Privilégio (Vertical Privilege Escalation)

**Classificação:** `defensiva`

**O que é:** Situação em que um usuário obtém permissões de um papel superior (por exemplo, de usuário comum para administrador), executando ações reservadas a níveis mais altos.

**Como funciona:** O escalonamento vertical acontece quando a fronteira entre papéis não é imposta no servidor: campos de papel manipuláveis, funções administrativas sem checagem de papel, ou fluxos de atribuição de permissão que confiam em entrada do cliente. Um vetor comum é a aplicação derivar o papel de um valor controlável (cookie, campo do perfil, parâmetro) em vez da fonte de verdade do lado servidor. Outro é a existência de funções privilegiadas alcançáveis por qualquer sessão autenticada. A causa raiz é a gestão incorreta de privilégios e a ausência de verificação de papel antes de ações sensíveis.

**Detecção:** Revisão de onde o papel/permissão é lido e se pode ser influenciado pelo cliente; testes com conta comum tentando ações administrativas. Em logs: mudança de papel de uma conta, ações administrativas por contas recém-criadas, atribuição de permissões fora do fluxo esperado. Ferramentas: análise de fluxo de dados sobre atributos de autorização, testes de autorização por papel, monitoramento de alterações de privilégio.

**Endurecimento:** Armazenar papel/permissões apenas em fonte confiável do servidor (sessão/registro), nunca aceitar papel vindo do cliente; validar papel antes de cada ação privilegiada. Aplicar menor privilégio, separação de deveres e aprovação para elevação; proteger endpoints de gestão de papéis com autorização reforçada e auditoria. Registrar e alertar sobre mudanças de privilégio e revisar periodicamente as atribuições.

**Referências:**
- CWE-269: Improper Privilege Management - https://cwe.mitre.org/data/definitions/269.html
- CWE-266: Incorrect Privilege Assignment - https://cwe.mitre.org/data/definitions/266.html
- OWASP Top 10 2021 A01: Broken Access Control - https://owasp.org/Top10/A01_2021-Broken_Access_Control/
- MITRE ATT&CK T1068: Exploitation for Privilege Escalation - https://attack.mitre.org/techniques/T1068/

### Falhas de Lógica de Negócio (Business Logic Vulnerabilities)

**Classificação:** `defensiva`

**O que é:** Falhas de lógica de negócio surgem quando a aplicação assume que os usuários seguirão o fluxo pretendido, permitindo pular etapas, repetir operações ou fornecer valores válidos em formato mas inválidos em regra. Não há um payload universal: cada falha explora uma suposição específica do domínio.

**Como funciona:** Diferente de injeções, essas falhas não violam a sintaxe da entrada, e sim as regras e invariantes do negócio. Exemplos conceituais incluem: concluir uma compra sem passar pela etapa de pagamento, aplicar um desconto além do limite permitido, informar quantidade negativa que inverte um cálculo, reutilizar um cupom de uso único, ou manipular a ordem de uma máquina de estados (checkout, aprovação, transferência) para atingir um estado impossível pelo caminho legítimo. A causa raiz é a validação incompleta de invariantes no servidor e a confiança em controles apenas do lado do cliente. A defesa exige modelar explicitamente os estados válidos, transições permitidas e limites de cada operação, aplicando-os de forma autoritativa no backend.

**Detecção:** Instrumente eventos de negócio (pedidos, transferências, resgates, mudanças de estado) e defina alertas para sequências impossíveis ou fora de ordem, valores fora de faixa, e repetições além do limite (ex.: mesmo cupom aplicado múltiplas vezes). Reconcilie totais e saldos periodicamente para detectar inconsistências. Analise trilhas de auditoria buscando transições de estado que não correspondam ao fluxo esperado e picos anômalos por usuário em fluxos sensíveis.

**Endurecimento:** Modele cada fluxo sensível como máquina de estados com transições explícitas e verifique-as no servidor a cada passo. Valide invariantes de domínio (faixas de valor, unicidade, propriedade do recurso, idempotência) no backend, independentemente do cliente. Reavalie autorização e regras a cada etapa, não apenas na entrada do fluxo. Use tokens de continuidade para garantir que etapas ocorram na ordem correta, aplique limites e cotas por operação, e escreva testes de abuso que tentem pular, repetir e inverter etapas.

**Referências:**
- OWASP Web Security Testing Guide: Business Logic Testing
- OWASP Cheat Sheet Series: Abuse Case
- PortSwigger Web Security Academy: Business Logic Vulnerabilities
- CWE-840: Business Logic Errors

### Falsificação de Requisição do Lado do Servidor (SSRF)

**Classificação:** `defensiva`

**O que é:** Vulnerabilidade em que um atacante induz o servidor a realizar requisições a destinos escolhidos por ele, alcançando serviços internos e endpoints de metadados normalmente inacessíveis de fora.

**Como funciona:** A aplicação faz uma requisição de rede a uma URL/host derivado de entrada do usuário (por exemplo, buscar uma imagem por URL, webhooks, importadores); no SSRF o atacante direciona essa requisição para alvos internos como serviços de rede privada ou o endpoint de metadados da nuvem. Como a requisição parte do servidor, ela herda a posição de rede e a confiança da aplicação, contornando controles de perímetro. Endpoints de metadados de provedores de nuvem são alvo crítico por poderem expor credenciais temporárias de instância. A causa raiz é a falta de validação/segmentação sobre quais destinos o servidor pode alcançar a partir de entrada externa.

**Detecção:** Revisão de todo cliente HTTP/URL fetcher que aceita destino do usuário e verificação de allowlist e bloqueio de faixas internas; testes apontando para hosts internos em ambiente autorizado. Em logs/tráfego: conexões de saída do servidor para faixas privadas ou para o IP de metadados, resoluções DNS anômalas, redirecionamentos para destinos internos. Ferramentas: monitoramento de egress, SAST/DAST para SSRF, egress firewall.

**Endurecimento:** Validar destinos por allowlist de domínios/hosts, resolver o DNS e verificar o IP final contra faixas privadas/link-local (bloqueando o endpoint de metadados), reavaliando após redirecionamentos para evitar rebind/TOCTOU. Aplicar o IMDSv2 (metadados exigindo token) e negar por padrão o egress, segmentando a rede da aplicação. Desabilitar protocolos/redirecionamentos desnecessários no cliente HTTP e isolar componentes que fazem fetch de URLs externas.

**Referências:**
- OWASP Top 10 2021 A10: Server-Side Request Forgery - https://owasp.org/Top10/A10_2021-Server-Side_Request_Forgery_%28SSRF%29/
- CWE-918: Server-Side Request Forgery (SSRF) - https://cwe.mitre.org/data/definitions/918.html
- OWASP SSRF Prevention Cheat Sheet - https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html
- OWASP API Security Top 10 2023 API7: Server Side Request Forgery - https://owasp.org/API-Security/editions/2023/en/0xa7-server-side-request-forgery/
- AWS IMDSv2 documentation - https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html

### Inclusão de Arquivo Local e Remoto (LFI/RFI)

**Classificação:** `defensiva`

**O que é:** Classe de falhas em que a aplicação inclui ou carrega dinamicamente um arquivo cujo caminho ou URL é influenciado pelo usuário, expondo arquivos locais (LFI) ou carregando recursos remotos (RFI).

**Como funciona:** Ocorre quando um mecanismo de include/require ou carregamento dinâmico de recurso usa entrada do usuário para determinar o arquivo a carregar; no LFI o alvo é um arquivo local (frequentemente combinado com travessia de diretório), no RFI é uma URL externa. Se o recurso incluído for interpretado como código, a leitura pode evoluir para execução no servidor; mesmo sem execução, há exposição de arquivos sensíveis. A causa raiz é o controle externo do nome do arquivo em função de include e a falta de restrição a um conjunto seguro. Configurações que permitem incluir URLs remotas ampliam a superfície do RFI.

**Detecção:** Revisão de usos de include/require dinâmico e carregadores de template/recurso com entrada do usuário; verificar se o alvo é restrito a uma allowlist. Em logs: parâmetros com caminhos ou URLs, sequências de travessia, referências a wrappers/protocolos incomuns. Ferramentas: SAST para funções de inclusão dinâmica, WAF, monitoramento de saída de rede do servidor (para RFI).

**Endurecimento:** Nunca derivar o alvo de include diretamente da entrada do usuário; mapear para uma allowlist fixa de recursos permitidos. Desabilitar inclusão de URLs remotas na configuração do runtime, restringir permissões de leitura do processo e separar código de dados. Validar e canonicalizar caminhos, aplicar defesa em profundidade com WAF e revisar dependências de template engines quanto a carregamento dinâmico.

**Referências:**
- CWE-98: PHP Remote File Inclusion - https://cwe.mitre.org/data/definitions/98.html
- CWE-73: External Control of File Name or Path - https://cwe.mitre.org/data/definitions/73.html
- OWASP Testing Guide: Testing for Local/Remote File Inclusion - https://owasp.org/www-project-web-security-testing-guide/
- OWASP Top 10 2021 A03: Injection - https://owasp.org/Top10/A03_2021-Injection/

### Navegação Forçada (Forced Browsing)

**Classificação:** `escopo_autorizado`

**O que é:** Técnica em que recursos não vinculados na interface, mas existentes no servidor, são acessados por requisição direta, revelando falhas quando dependem apenas de obscuridade para proteção.

**Como funciona:** Muitas aplicações possuem endpoints, arquivos e funções que não estão referenciados na navegação normal (páginas de administração, backups, versões antigas, arquivos temporários); a navegação forçada consiste em requisitá-los diretamente por caminhos previsíveis. O risco surge quando esses recursos não têm controle de acesso próprio e contam apenas com não estarem linkados (segurança por obscuridade). Também expõe funções privilegiadas alcançáveis sem passar pela interface esperada. A avaliação legítima dessa exposição exige autorização escrita e regras de engajamento, pois envolve enumeração ativa de superfície. A raiz do problema é a ausência de autorização por recurso, não a existência do recurso.

**Detecção:** Inventariar rotas/arquivos publicados versus os efetivamente protegidos; revisar se recursos sensíveis exigem autorização independente de estarem linkados. Em logs/WAF: rajadas de 404/403 com nomes de dicionário, acessos a caminhos administrativos ou de backup, varreduras de diretório. Ferramentas: análise de configuração do servidor web, detecção de força bruta de conteúdo, revisão de artefatos publicados por engano.

**Endurecimento:** Aplicar autorização a todo recurso independentemente de estar referenciado na UI (deny-by-default); remover do servidor arquivos de backup, temporários e páginas obsoletas. Desabilitar listagem de diretórios, segregar áreas administrativas com autenticação/autorização reforçadas, e monitorar/limitar enumeração de conteúdo. Tratar obscuridade apenas como camada adicional, nunca como controle único.

**Referências:**
- CWE-425: Direct Request (Forced Browsing) - https://cwe.mitre.org/data/definitions/425.html
- OWASP Forced Browsing - https://owasp.org/www-community/attacks/Forced_browsing
- OWASP Top 10 2021 A01: Broken Access Control - https://owasp.org/Top10/A01_2021-Broken_Access_Control/
- OWASP Web Security Testing Guide: Review Old Backup and Unreferenced Files - https://owasp.org/www-project-web-security-testing-guide/

### Referência Insegura Direta a Objeto (IDOR)

**Classificação:** `defensiva`

**O que é:** Vulnerabilidade em que o identificador de um objeto exposto ao usuário (ID, nome de arquivo, chave) é usado para acessar recursos sem verificar se o solicitante tem permissão sobre aquele objeto específico.

**Como funciona:** A aplicação recebe uma referência a um objeto (por exemplo, um identificador em /faturas/1024) e realiza a operação apenas confirmando que o usuário está autenticado, sem checar a propriedade ou permissão sobre aquele objeto. Quando os identificadores são previsíveis (sequenciais) ou enumeráveis, um usuário legítimo pode alterar a referência e alcançar recursos de outros usuários. A falha é de autorização em nível de objeto: a verificação de escopo (este objeto pertence a este tenant/usuário?) não é executada no servidor. Substituir IDs por valores aleatórios reduz a enumeração, mas não corrige a causa raiz, que é a ausência da checagem de propriedade.

**Detecção:** Revisão de código em torno de consultas que usam ID do cliente sem cláusula de escopo (por exemplo, WHERE id = ? sem AND owner_id = sessao.user); testes comparando acesso entre duas contas do mesmo papel a objetos uma da outra. Em logs/tráfego: acessos bem-sucedidos a sequências de IDs, variação de IDs por sessão, respostas 200 onde se esperaria 403/404. Ferramentas: scanners de autorização com múltiplas identidades, testes automatizados de propriedade de objeto.

**Endurecimento:** Verificar a autorização em nível de objeto no servidor a cada acesso, filtrando sempre pelo dono/tenant da sessão (WHERE resource.owner = current_user). Preferir referências indiretas por sessão ou escopo do tenant e usar identificadores não sequenciais (UUID) como defesa em profundidade, não como controle único. Centralizar a checagem de propriedade em uma camada de acesso a dados e cobrir com testes de autorização por objeto.

**Referências:**
- CWE-639: Authorization Bypass Through User-Controlled Key - https://cwe.mitre.org/data/definitions/639.html
- OWASP Insecure Direct Object Reference Prevention Cheat Sheet - https://cheatsheetseries.owasp.org/cheatsheets/Insecure_Direct_Object_Reference_Prevention_Cheat_Sheet.html
- OWASP Top 10 2021 A01: Broken Access Control - https://owasp.org/Top10/A01_2021-Broken_Access_Control/
- OWASP API Security Top 10 2023 API1 (BOLA) - https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/

### Travessia de Diretório (Path/Directory Traversal)

**Classificação:** `defensiva`

**O que é:** Vulnerabilidade em que entrada controlada pelo usuário é usada para compor caminhos de arquivo, permitindo referenciar arquivos fora do diretório pretendido e burlar restrições de acesso.

**Como funciona:** A aplicação concatena entrada do usuário a um caminho base para acessar arquivos; sequências de travessia (como referências ao diretório pai) fazem o caminho resolvido escapar do diretório permitido. O problema decorre de usar o nome recebido sem canonicalizar (resolver o caminho absoluto real) e sem validar que o resultado permanece dentro da raiz autorizada. Codificações alternativas, barras invertidas e caracteres nulos podem contornar filtros ingênuos baseados em correspondência de texto. A raiz é limitação inadequada de nome de caminho a um diretório restrito.

**Detecção:** Revisão de todo ponto que recebe nome de arquivo/caminho do usuário e verifica canonicalização e confinamento à raiz; testes com sequências de travessia em ambiente autorizado. Em logs/WAF: presença de sequências de subida de diretório, tentativas de acesso a arquivos de sistema, respostas com conteúdo de arquivos sensíveis. Ferramentas: análise estática (SAST) para fluxo de dados até APIs de arquivo, WAF com regras de traversal, testes dinâmicos.

**Endurecimento:** Evitar usar entrada do usuário em caminhos; quando necessário, canonicalizar o caminho resolvido e verificar que começa dentro do diretório base autorizado antes de abrir. Preferir mapear a entrada para um conjunto conhecido (allowlist) ou identificadores indiretos, e executar o serviço com privilégios mínimos de sistema de arquivos. Rejeitar bytes nulos e normalizar codificações; isolar armazenamento de arquivos do restante do sistema.

**Referências:**
- CWE-22: Improper Limitation of a Pathname to a Restricted Directory - https://cwe.mitre.org/data/definitions/22.html
- CWE-23: Relative Path Traversal - https://cwe.mitre.org/data/definitions/23.html
- OWASP Path Traversal - https://owasp.org/www-community/attacks/Path_Traversal
- OWASP Input Validation Cheat Sheet - https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html
- MITRE ATT&CK T1083: File and Directory Discovery - https://attack.mitre.org/techniques/T1083/

### Verificação de Autorização no Lado do Servidor (Server-Side Authorization)

**Classificação:** `defensiva`

**O que é:** Princípio de que toda decisão de autorização deve ser tomada e imposta no servidor, com identidade e permissões de fonte confiável, nunca delegada ao cliente.

**Como funciona:** Controles no cliente (ocultar botões, validar no navegador, confiar em campos enviados) melhoram usabilidade mas não impõem segurança, pois o cliente é totalmente manipulável; a autorização real precisa ocorrer no servidor a cada requisição. A identidade deve vir da sessão/token validado pelo servidor, e as permissões da fonte de verdade do backend, não de valores enviados pelo requisitante. Falhas surgem quando a aplicação assume que o front-end restringiu a ação ou quando a checagem está dispersa e inconsistente entre endpoints. O padrão robusto centraliza a decisão em um ponto de imposição, negando por padrão.

**Detecção:** Revisão de código para confirmar que cada endpoint executa checagem de autorização no servidor e não confia em flags/papéis do cliente; testes replay de requisições contornando a UI. Em logs: ações sensíveis sem registro de decisão de autorização, aceitação de requisições que a UI não permitiria. Ferramentas: testes de integração de autorização, proxy para replay em ambiente autorizado, revisão de middlewares.

**Endurecimento:** Impor autorização no servidor em todas as requisições, derivando identidade e permissões de fontes confiáveis do backend e negando por padrão. Centralizar a lógica em um ponto de imposição (middleware/serviço de política) para consistência, e nunca confiar em validações ou papéis vindos do cliente. Tratar controles de cliente apenas como usabilidade e cobrir a autorização com testes automatizados e auditoria.

**Referências:**
- CWE-602: Client-Side Enforcement of Server-Side Security - https://cwe.mitre.org/data/definitions/602.html
- CWE-863: Incorrect Authorization - https://cwe.mitre.org/data/definitions/863.html
- OWASP Top 10 2021 A01: Broken Access Control - https://owasp.org/Top10/A01_2021-Broken_Access_Control/
- OWASP Authorization Cheat Sheet - https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html
- NIST SP 800-207 Zero Trust Architecture - https://csrc.nist.gov/publications/detail/sp/800-207/final

## Autenticação, Sessão e Identidade Federada

### Armazenamento Seguro de Senhas: bcrypt, scrypt, Argon2, Salt e Pepper (Password Storage)

**Classificação:** `defensiva`

**O que é:** Uso de funções de derivação de chave lentas e específicas para senhas, com salt único por usuário, para tornar inviável a recuperação em massa das senhas mesmo com o banco vazado.

**Como funciona:** Senhas nunca devem ser guardadas em texto claro nem com hash rápido de propósito geral (MD5/SHA-1/SHA-256 simples), pois GPUs testam bilhões de candidatos por segundo. KDFs de senha (Argon2id, scrypt, bcrypt, PBKDF2) são deliberadamente custosos em tempo e, no caso de Argon2/scrypt, em memória, elevando o custo por tentativa e frustrando ataques de dicionário/força bruta offline. Um salt aleatório e único por credencial impede tabelas pré-computadas (rainbow tables) e que hashes iguais revelem senhas iguais. Um pepper (segredo global mantido fora do banco, ex.: em HSM/variável de ambiente) adiciona uma camada que o atacante não obtém só com o dump do banco. Parâmetros mal calibrados ou algoritmos rápidos anulam a proteção.

**Detecção:** Auditar o esquema de armazenamento: identificar hashes de algoritmos rápidos, ausência de salt, salt fixo/global ou senhas em claro. Revisar código de cadastro/login para a função usada e seus parâmetros (fator de custo/memória/iterações). Verificar se há atualização/rehash quando parâmetros mudam ou no login. Ferramentas: scanners SAST, revisão de migrações de banco, e verificação do formato do hash armazenado (prefixos como $argon2id$, $2b$).

**Endurecimento:** Preferir Argon2id (com memória, iterações e paralelismo calibrados às recomendações OWASP), ou scrypt/bcrypt/PBKDF2 quando exigido, sempre com salt aleatório único por usuário. Adicionar pepper via HMAC com chave em cofre/HSM, separada do banco. Recalibrar custo periodicamente e rehash transparente no login; comparar hashes em tempo constante. Limitar tamanho de entrada para evitar DoS, aplicar rate limiting no login e nunca logar senhas. Combinar com políticas NIST 800-63B e verificação contra senhas vazadas.

**Referências:**
- OWASP Password Storage Cheat Sheet (https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
- NIST SP 800-63B: Digital Identity Guidelines
- CWE-916: Use of Password Hash With Insufficient Computational Effort
- CWE-759: Use of a One-Way Hash without a Salt; CWE-760: Predictable Salt
- RFC 9106: Argon2 Memory-Hard Function; Argon2 (PHC winner)
- OWASP Top 10 2021 A02:2021 Cryptographic Failures / A07:2021

### Autenticação Multifator: TOTP, WebAuthn/FIDO2 e Passkeys (MFA/2FA)

**Classificação:** `defensiva`

**O que é:** Uso de um segundo fator de autenticação, priorizando métodos resistentes a phishing (WebAuthn/FIDO2/passkeys) sobre OTP, para reduzir o impacto do roubo de senha.

**Como funciona:** TOTP (RFC 6238) deriva um código de curta duração de um segredo compartilhado e do tempo atual (baseado no HOTP, RFC 4226); é melhor que só senha, mas o código pode ser capturado por phishing em tempo real e reutilizado se não invalidado. WebAuthn/FIDO2 usa criptografia de chave pública: o autenticador gera um par de chaves ligado à origem (domínio) e assina um desafio, de modo que a assinatura só é válida para o site legítimo — resistindo a phishing por vinculação de origem. Passkeys são credenciais WebAuthn descobríveis, sincronizáveis entre dispositivos, substituindo a senha. Ataques contra MFA fraca incluem MFA fatigue/push bombing, interceptação de OTP por proxy de phishing, SIM swap (SMS) e engenharia social de reset.

**Detecção:** Inventariar métodos de MFA por conta e cobertura (usuários sem segundo fator, uso de SMS). Em logs, detectar rajadas de solicitações de push (MFA fatigue), múltiplas falhas de OTP, aprovações a partir de geolocalização anômala e resets que desabilitam MFA. Verificar no código se o OTP é de uso único e com janela curta, e se WebAuthn valida origin/RP ID e o sinal de user verification. Ferramentas: SIEM com regras de anomalia de MFA, relatórios do IdP.

**Endurecimento:** Priorizar MFA resistente a phishing (WebAuthn/FIDO2/passkeys) para contas sensíveis e administrativas; evitar SMS como fator primário. Para TOTP, impor uso único, janela estreita, limite de tentativas e proteção do segredo. Mitigar MFA fatigue com number matching, limite de prompts e alertas. Exigir MFA na elevação de privilégio e em mudanças de recuperação; proteger o fluxo de enrollment/reset (não permitir bypass por senha apenas). Seguir níveis AAL do NIST SP 800-63B.

**Referências:**
- RFC 6238: TOTP; RFC 4226: HOTP
- W3C Web Authentication (WebAuthn) Level 2/3; FIDO2/CTAP (FIDO Alliance)
- NIST SP 800-63B: Authentication and Lifecycle Management (AAL)
- CWE-308: Use of Single-factor Authentication
- MITRE ATT&CK T1621: Multi-Factor Authentication Request Generation
- OWASP Multifactor Authentication Cheat Sheet
- OWASP Top 10 2021 A07:2021 Identification and Authentication Failures

### Defesa contra Credential Stuffing, Força Bruta e Password Spraying

**Classificação:** `defensiva`

**O que é:** Conjunto de controles para detectar e conter tentativas automatizadas de autenticação usando credenciais vazadas, adivinhação exaustiva ou poucas senhas comuns contra muitas contas.

**Como funciona:** Credential stuffing reutiliza pares usuário:senha vazados de outros serviços contra o alvo, apostando na reutilização de senhas (T1110.004). Força bruta tenta muitas senhas contra uma conta; password spraying (T1110.003) inverte a lógica, testando poucas senhas muito comuns contra muitas contas para evitar bloqueio por conta. Ataques modernos distribuem requisições por botnets/proxies residenciais para driblar limites por IP e imitam navegadores reais. A defesa combina limitação de taxa inteligente, detecção de anomalia comportamental, MFA e verificação contra listas de senhas comprometidas, dado que apenas bloquear por IP ou por conta é insuficiente isoladamente.

**Detecção:** Em logs de autenticação, procurar alto volume de falhas, muitas contas atingidas por poucas senhas (spraying), sucessos após muitas falhas, distribuição por muitos IPs/ASNs, User-Agents repetidos e ausência de fluxo típico (sem carregar recursos da página). Monitorar taxa de falha por conta e global, uso de credenciais em listas de breach e picos vindos de proxies/data centers. Ferramentas: WAF/bot management, SIEM com regras de spraying/stuffing, análise de reputação de IP e detecção de impossible travel.

**Endurecimento:** Rate limiting em múltiplas dimensões (IP, conta, ASN, dispositivo) com backoff exponencial e bloqueio temporário resistente a CGNAT; CAPTCHA/prova de trabalho adaptativos e desafios progressivos. MFA (preferencialmente resistente a phishing) reduz drasticamente o valor de credenciais válidas. Verificar novas senhas e logins contra listas de senhas vazadas (k-anonymity), impedir senhas comuns, alertar o usuário sobre acessos anômalos. Respostas de login uniformes (anti-enumeração), bot management, e monitoramento contínuo conforme NIST 800-63B (throttling e blocklist).

**Referências:**
- CWE-307: Improper Restriction of Excessive Authentication Attempts; CWE-799: Improper Control of Interaction Frequency
- OWASP Credential Stuffing Prevention Cheat Sheet
- MITRE ATT&CK T1110: Brute Force (T1110.003 Password Spraying, T1110.004 Credential Stuffing)
- NIST SP 800-63B: Digital Identity Guidelines (rate limiting, compromised password check)
- OWASP Top 10 2021 A07:2021 Identification and Authentication Failures
- OWASP Automated Threats to Web Applications (OAT-008 Credential Stuffing)

### Enumeração de Usuários e Oráculos de Tempo em Autenticação (User Enumeration)

**Classificação:** `escopo_autorizado`

**O que é:** Avaliação autorizada de discrepâncias em respostas, códigos de status ou tempos que permitem a um atacante descobrir quais identificadores de conta existem no sistema.

**Como funciona:** Fluxos de login, cadastro e recuperação podem revelar a existência de uma conta por diferenças observáveis: mensagens distintas ('usuário não encontrado' vs 'senha inválida'), códigos de status/redirecionamento divergentes, presença/ausência de campos, ou tempo de resposta diferente (ex.: senha só é submetida ao hash custoso quando o usuário existe, criando um oráculo temporal). Um avaliador autorizado compara respostas para identificadores válidos e inválidos e mede latências para inferir contas reais. Listas de usuários válidos ampliam ataques subsequentes como password spraying e engenharia social. Este trabalho exige autorização escrita e regras de engajamento por gerar tráfego e sondar contas.

**Detecção:** Comparar sistematicamente respostas (corpo, status, cabeçalhos, tempo) para entradas válidas e inválidas em login/registro/reset; medir tempos com múltiplas amostras para detectar diferença estatística. Revisar código em busca de ramos que só executam operações caras (hashing) quando a conta existe, e mensagens específicas por caso. Em logs, monitorar varreduras de muitos identificadores com respostas correlacionadas. Ferramentas de teste autorizado: OWASP ZAP/Burp com análise de resposta e scripts de timing.

**Endurecimento:** Mensagens genéricas e idênticas em login, cadastro e recuperação ('se a conta existir, enviaremos instruções'); mesmos status/redirecionamentos independentemente da existência. Uniformizar tempo de resposta (executar trabalho equivalente para contas inexistentes, comparação em tempo constante) para eliminar oráculos temporais. Aplicar rate limiting e CAPTCHA anti-automação, evitar expor existência em cadastro (confirmação por e-mail neutra) e registrar tentativas de enumeração. Combinar com MFA e monitoramento.

**Referências:**
- CWE-204: Observable Response Discrepancy; CWE-203: Observable Discrepancy
- OWASP WSTG-IDNT-04: Testing for Account Enumeration and Guessable User Account
- OWASP Authentication Cheat Sheet (Authentication and Error Messages)
- NIST SP 800-63B: Digital Identity Guidelines
- OWASP Top 10 2021 A07:2021 Identification and Authentication Failures

### Fixação de Sessão (Session Fixation)

**Classificação:** `defensiva`

**O que é:** Ataque em que o adversário força a vítima a usar um identificador de sessão conhecido por ele antes do login, herdando a sessão autenticada quando a vítima se autentica.

**Como funciona:** O atacante obtém ou define um valor de session ID (por exemplo, aceitando um ID emitido pelo servidor ou injetando um via parâmetro/cookie) e induz a vítima a autenticar-se usando esse mesmo identificador. Se a aplicação reaproveita o mesmo ID de antes para depois da autenticação, sem regenerá-lo, a sessão agora autenticada fica ligada ao valor que o atacante já conhece, permitindo o acesso. É viabilizado por aplicações que aceitam IDs fornecidos pelo cliente, que transportam o ID em URL, ou que não emitem um novo ID no momento exato da elevação de privilégio.

**Detecção:** No código, procurar ausência de chamada de regeneração de ID no login (ex.: session.regenerate, session_regenerate_id, renovação do token no framework). Verificar se a aplicação aceita session IDs vindos do cliente ou de query string. Em testes autorizados, observar se o cookie de sessão permanece idêntico antes e depois do login. Em logs, um mesmo ID transitando de estado não autenticado para autenticado sem troca é indicador.

**Endurecimento:** Regenerar sempre o identificador de sessão imediatamente após autenticação bem-sucedida e a cada mudança de nível de privilégio, invalidando o valor anterior. Nunca aceitar session IDs fornecidos pelo cliente (rejeitar IDs desconhecidos e emitir um novo). Vincular cookies com HttpOnly/Secure/SameSite, evitar sessão em URL e aplicar expiração. Em SSO/federação, garantir troca de sessão local após o retorno do IdP.

**Referências:**
- CWE-384: Session Fixation
- OWASP Top 10 2021 A07:2021 Identification and Authentication Failures
- OWASP Session Management Cheat Sheet
- OWASP WSTG-SESS-03: Testing for Session Fixation
- NIST SP 800-63B: Digital Identity Guidelines - Authentication and Lifecycle Management

### Gerenciamento de Sessão e Cookies Seguros (Secure Session Management)

**Classificação:** `defensiva`

**O que é:** Conjunto de práticas para gerar, transmitir, armazenar e invalidar identificadores de sessão de forma que não possam ser previstos, interceptados ou reutilizados por um atacante.

**Como funciona:** Após a autenticação o servidor cria um identificador de sessão (session ID) opaco e de alta entropia associado ao estado do usuário no lado servidor, ou um cookie assinado/criptografado com estado. Esse identificador é transportado em um cookie e vale como prova de autenticação em cada requisição subsequente. A segurança depende de imprevisibilidade (>=128 bits de entropia de CSPRNG), confidencialidade em trânsito (TLS + atributo Secure), isolamento do JavaScript (HttpOnly), restrição de contexto cross-site (SameSite) e ciclo de vida controlado (expiração absoluta e por inatividade, rotação e revogação no logout). Falhas surgem quando o ID é previsível, exposto em URL, transmitido em texto claro, sem expiração ou não invalidado no servidor após logout.

**Detecção:** Revisar código/config de framework para atributos de cookie ausentes (Secure, HttpOnly, SameSite) e para IDs derivados de dados previsíveis (timestamp, contador, hash de e-mail). Interceptar tráfego com proxy (Burp/ZAP) e inspecionar Set-Cookie; usar analisadores como testssl.sh e OWASP ZAP para flags de cookie. Em logs, procurar reuso do mesmo session ID a partir de múltiplos IPs/User-Agents, sessões que sobrevivem ao logout e ausência de eventos de invalidação server-side.

**Endurecimento:** Gerar IDs com CSPRNG (>=128 bits); nunca colocar sessão em URL. Emitir cookies com Secure, HttpOnly, SameSite=Lax/Strict e prefixo __Host- quando possível. Regenerar o ID na elevação de privilégio e no login; manter store de sessão server-side com revogação real no logout e expiração absoluta + inatividade. Implementar logout que apaga a sessão no servidor (não só o cookie do cliente), binding opcional a atributos estáveis, e proteção anti-CSRF (tokens sincronizados/double-submit) já que cookies são enviados automaticamente.

**Referências:**
- OWASP Top 10 2021 A07:2021 Identification and Authentication Failures
- OWASP Session Management Cheat Sheet (https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
- CWE-614: Sensitive Cookie in HTTPS Session Without 'Secure' Attribute
- CWE-1004: Sensitive Cookie Without 'HttpOnly' Flag
- CWE-1275: Sensitive Cookie with Improper SameSite Attribute
- RFC 6265 / RFC 6265bis: HTTP State Management Mechanism
- MITRE ATT&CK T1539: Steal Web Session Cookie

### OAuth 2.0/2.1 com PKCE e Validação de redirect_uri (Authorization Code + PKCE)

**Classificação:** `defensiva`

**O que é:** Uso do fluxo Authorization Code com PKCE e validação rígida de redirect_uri e state para autorização delegada segura, evitando interceptação de código e redirecionamento aberto.

**Como funciona:** No Authorization Code, o cliente redireciona o usuário ao servidor de autorização, recebe um código de curta duração no redirect_uri e o troca por tokens no back-channel. PKCE protege esse código: o cliente gera um code_verifier aleatório e envia seu hash (code_challenge) na autorização; o servidor só troca o código se o verifier corresponder, neutralizando interceptação do código por apps públicos. Ataques exploram redirect_uri frouxo (correspondência parcial/curinga leva à exfiltração do código para domínio do atacante), ausência do parâmetro state (CSRF de autorização/login), fluxo Implicit legado que expõe tokens na URL e mistura de código entre clientes. OAuth 2.1 consolida as boas práticas: PKCE obrigatório, Implicit e ROPC removidos, correspondência exata de redirect_uri.

**Detecção:** Revisar registro de clientes quanto a redirect_uris com curingas, http, ou correspondência por prefixo; verificar se state/nonce são gerados, ligados à sessão e conferidos no retorno. Confirmar presença de PKCE (S256) para clientes públicos e SPA/mobile. Em tráfego autorizado, observar respostas de autorização com token na URL (Implicit), ausência de code_challenge e Location apontando para hosts inesperados. Logs do IdP: erros de mismatch de redirect_uri e reuso de código.

**Endurecimento:** Usar Authorization Code + PKCE (S256) em todos os clientes, inclusive confidenciais; abolir Implicit e ROPC. Exigir correspondência exata e pré-registrada de redirect_uri (sem curingas). Gerar e validar state (anti-CSRF) e nonce (OIDC) ligados à sessão; códigos de uso único e vida curta. Autenticar clientes confidenciais, restringir escopos, aplicar rotação de refresh token e sender-constrained tokens (DPoP/mTLS) quando possível. Seguir o OAuth 2.0 Security BCP (RFC 9700) e RFC 8252 para apps nativos.

**Referências:**
- RFC 6749: The OAuth 2.0 Authorization Framework; RFC 6750: Bearer Token Usage
- RFC 7636: Proof Key for Code Exchange (PKCE)
- RFC 9700: Best Current Practice for OAuth 2.0 Security
- OAuth 2.1 Authorization Framework (draft IETF)
- RFC 8252: OAuth 2.0 for Native Apps
- CWE-601: URL Redirection to Untrusted Site (Open Redirect); CWE-352: CSRF
- OWASP Top 10 2021 A07:2021 Identification and Authentication Failures

### OpenID Connect e Validação de id_token (OIDC)

**Classificação:** `defensiva`

**O que é:** Camada de identidade sobre OAuth 2.0 que emite um id_token (JWT) sobre a autenticação do usuário, cuja validação correta é essencial para SSO seguro.

**Como funciona:** O OIDC adiciona ao OAuth um id_token assinado pelo provedor de identidade (IdP) contendo claims sobre o evento de autenticação (sub, iss, aud, exp, iat, nonce, auth_time). O Relying Party (RP) deve verificar a assinatura com as chaves publicadas no JWKS do IdP e validar iss (emissor esperado), aud/azp (destinado a este cliente), exp/iat (frescor) e nonce (liga o token à requisição, previne replay). Vulnerabilidades surgem quando o RP aceita id_tokens de emissores não confiáveis, ignora aud (token cunhado para outro cliente é aceito), não verifica assinatura ou nonce, ou confia em claims de e-mail não verificado para vincular contas (permitindo account takeover por federação).

**Detecção:** Revisar o RP: validação obrigatória de assinatura via JWKS do issuer esperado, e de iss, aud, exp, nonce; confirmar que o discovery/issuer é fixo e confiável. Verificar se a vinculação de conta usa sub estável do IdP e não e-mail não verificado. Em testes autorizados, observar aceitação de tokens com aud incorreta ou emissor divergente. Monitorar logs de login federado por múltiplos IdPs mapeando para a mesma conta.

**Endurecimento:** Validar integralmente o id_token (assinatura, iss, aud/azp, exp, iat, nonce, auth_time quando aplicável); usar JWKS com rotação e cache controlado. Vincular contas por identificador estável (iss+sub), exigindo e-mail verificado pelo IdP e verificação adicional ao ligar provedores. Usar PKCE/state, aplicar max_age/prompt para reautenticação sensível e considerar logout federado (RP-/OP-initiated). Restringir a lista de IdPs confiáveis e seguir NIST SP 800-63C para federação e asserções.

**Referências:**
- OpenID Connect Core 1.0 (https://openid.net/specs/openid-connect-core-1_0.html)
- NIST SP 800-63C: Digital Identity Guidelines - Federation and Assertions
- CWE-287: Improper Authentication; CWE-347: Improper Verification of Cryptographic Signature
- RFC 7519: JSON Web Token; RFC 8725: JWT BCP
- OWASP Top 10 2021 A07:2021 Identification and Authentication Failures

### Políticas de Senha conforme NIST SP 800-63B (Password Policy)

**Classificação:** `defensiva`

**O que é:** Diretrizes modernas de senha do NIST que priorizam comprimento e verificação contra senhas comprometidas em vez de regras de composição e expiração periódica.

**Como funciona:** O NIST SP 800-63B trata a senha como um dos fatores (memorized secret) e recomenda otimizar segurança e usabilidade simultaneamente. As orientações centrais: permitir comprimento mínimo generoso (ao menos 8, idealmente mais) e máximos altos (>=64) aceitando frases e todos os caracteres imprimíveis/Unicode; não impor regras arbitrárias de composição (obrigar símbolos/números) nem expiração periódica sem motivo, pois empurram usuários a padrões previsíveis. Em vez disso, comparar a senha escolhida contra listas de senhas comprometidas, dicionário e valores contextuais, rejeitando as fracas no cadastro. Isso reduz o espaço de senhas realmente adivinháveis sem prejudicar a memorização.

**Detecção:** Auditar a política implementada: comprimento mínimo/máximo, bloqueio de senhas comuns/vazadas, ausência de expiração forçada arbitrária e de regras de composição contraproducentes. Revisar se há truncamento silencioso ou restrição de caracteres. Verificar integração com verificação de breach (ex.: consulta k-anonymity) e feedback de força ao usuário. Testar (autorizado) se senhas notoriamente fracas são aceitas.

**Endurecimento:** Definir comprimento mínimo robusto e máximo elevado, aceitando espaços/Unicode e não truncando; oferecer medidor de força e permitir colar (favorece gerenciadores). Bloquear senhas em listas de comprometidas, comuns e contextuais; não exigir composição obrigatória nem trocas periódicas sem indício de comprometimento. Forçar troca apenas quando houver evidência de comprometimento. Combinar com hashing forte, MFA, rate limiting e notificações; alinhar ao nível AAL desejado do NIST 800-63B.

**Referências:**
- NIST SP 800-63B: Digital Identity Guidelines - Authentication and Lifecycle Management
- OWASP Authentication Cheat Sheet - Password Policy
- CWE-521: Weak Password Requirements
- OWASP Top 10 2021 A07:2021 Identification and Authentication Failures
- OWASP Password Storage Cheat Sheet

### Recuperação Segura de Conta e Redefinição de Senha (Secure Account Recovery)

**Classificação:** `defensiva`

**O que é:** Fluxo de redefinição/recuperação de credenciais projetado para não se tornar um caminho mais fraco que o próprio login, evitando tomada de conta.

**Como funciona:** A recuperação normalmente envia ao canal verificado do usuário (e-mail/telefone) um token de redefinição de uso único e curta duração; ao apresentá-lo, o usuário define nova senha. Fraquezas transformam esse fluxo em vetor de account takeover: tokens previsíveis ou longos demais, sem expiração ou reutilizáveis; construção do link a partir de cabeçalho Host controlável pelo atacante (host header poisoning) que exfiltra o token; perguntas de segurança com respostas adivinháveis/públicas; resposta que revela existência da conta (enumeração); e reset que não invalida sessões nem exige revalidação de MFA. O objetivo do atacante é redefinir a credencial de terceiros sem posse do fator legítimo.

**Detecção:** Revisar código: geração de token com CSPRNG, uso único, expiração curta, associação estrita ao usuário e invalidação após uso ou nova solicitação. Verificar se a URL do link é construída a partir de configuração fixa e não do Host recebido. Testar (autorizado) por respostas que diferenciam contas existentes e por reset que não encerra sessões. Em logs, detectar muitas solicitações de reset por conta/IP, tokens reutilizados e resets seguidos de mudança de e-mail/MFA.

**Endurecimento:** Tokens aleatórios (CSPRNG), curtos em validade, de uso único, invalidados ao gerar novo ou concluir; nunca expor o token em logs/Referer. Construir URLs a partir de origem confiável configurada (ignorar Host não confiável). Abandonar perguntas de segurança; usar canais verificados e, para contas sensíveis, exigir reautenticação/MFA e passos adicionais. Mensagens neutras e uniformes (anti-enumeração), rate limiting no pedido de reset, notificar o usuário e invalidar todas as sessões e reavaliar MFA após a troca. Seguir NIST 800-63B.

**Referências:**
- CWE-640: Weak Password Recovery Mechanism for Forgotten Password; CWE-620: Unverified Password Change
- OWASP Forgot Password Cheat Sheet (https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html)
- OWASP Host Header Injection / Web Security Testing Guide
- NIST SP 800-63B: Digital Identity Guidelines
- OWASP Top 10 2021 A07:2021 Identification and Authentication Failures

### Segurança de JSON Web Tokens (JWT Security)

**Classificação:** `defensiva`

**O que é:** Práticas corretas de verificação e validação de tokens JWT para impedir falsificação por manipulação do cabeçalho, do algoritmo ou das claims.

**Como funciona:** Um JWT é composto por cabeçalho, payload e assinatura codificados em Base64URL; a confiança vem da verificação criptográfica da assinatura e das claims. Falhas clássicas: aceitar alg=none (token sem assinatura tratado como válido), confusão de algoritmo (servidor que espera RS256 mas aceita HS256, permitindo assinar com a chave pública como se fosse segredo HMAC), não validar iss/aud/exp/nbf, confiar em parâmetros de cabeçalho controláveis pelo atacante (kid, jku, x5u) para carregar chaves, e usar segredos HMAC fracos suscetíveis a quebra offline. A raiz do problema é delegar decisões de confiança a campos que o próprio emissor do token controla.

**Detecção:** Revisar o código: garantir que o algoritmo é fixado explicitamente na verificação (allowlist), nunca derivado do cabeçalho do token; verificar validação de exp, nbf, iss e aud. Procurar uso de bibliotecas desatualizadas com decodificação sem verificação (decode em vez de verify). Em tráfego, decodificar tokens (parte não sensível) e observar alg=none, algoritmos inesperados, ausência de exp ou aud incorreta. Testar em ambiente autorizado com ferramentas como jwt_tool contra sistemas próprios.

**Endurecimento:** Fixar algoritmos permitidos no verificador (allowlist), rejeitar alg=none e mismatches. Usar chaves assimétricas (RS256/ES256/EdDSA) com validação estrita, ou segredos HMAC de alta entropia guardados em cofre. Validar todas as claims: exp, nbf, iat, iss, aud e sub; impor expiração curta. Não confiar em jku/x5u/kid arbitrários (restringir a fontes conhecidas). Preferir tokens de acesso de vida curta com refresh, considerar revogação (lista de bloqueio/rotação de chave) e não colocar dados sensíveis no payload.

**Referências:**
- RFC 7519: JSON Web Token (JWT)
- RFC 7515: JSON Web Signature (JWS); RFC 7518: JSON Web Algorithms (JWA)
- RFC 8725: JSON Web Token Best Current Practices
- CWE-347: Improper Verification of Cryptographic Signature
- OWASP JSON Web Token for Java Cheat Sheet / OWASP API Security Top 10 2023 API2:2023 Broken Authentication
- OWASP Top 10 2021 A07:2021 Identification and Authentication Failures

### Segurança de SAML e Federação (SAML Security)

**Classificação:** `defensiva`

**O que é:** Práticas de validação de asserções SAML entre Identity Provider e Service Provider para impedir falsificação, replay e manipulação de assinatura XML.

**Como funciona:** No SSO SAML, o IdP emite uma asserção XML assinada afirmando a identidade do usuário, que o SP consome para autenticar. A confiança depende de validar corretamente a assinatura XML sobre o elemento certo e as condições (NotBefore/NotOnOrAfter, Audience, Destination, InResponseTo). Ataques exploram XML Signature Wrapping (XSW), onde o atacante reestrutura o documento para que a assinatura valide um elemento benigno enquanto o SP processa um elemento forjado; comment injection em NameID; ausência de verificação de Audience/Destination (replay para outro SP); e comprometimento da chave de assinatura do IdP (Golden SAML), que permite forjar qualquer asserção. Fraquezas comuns incluem aceitar asserções não assinadas ou validar assinatura de forma frouxa.

**Detecção:** Revisar a configuração do SP: assinatura obrigatória da Response e/ou Assertion, verificação por referência correta (evitar bibliotecas suscetíveis a XSW), validação de Conditions, Audience, Destination, InResponseTo e janela temporal. Em testes autorizados, inspecionar respostas SAML por múltiplas Assertions/Signatures ou elementos duplicados. Monitorar emissão anômala de asserções, uso de certificados de assinatura fora do esperado e logins SAML sem InResponseTo correspondente (proteção anti-replay).

**Endurecimento:** Usar bibliotecas SAML mantidas e resistentes a XSW; exigir asserções assinadas (e idealmente criptografadas), validar assinatura sobre o elemento correto e rejeitar documentos com estrutura inesperada. Validar Audience, Destination, NotBefore/NotOnOrAfter, InResponseTo e uso único; sincronizar relógios. Proteger a chave privada do IdP em HSM/cofre com rotação e monitoramento (defesa contra Golden SAML). Restringir metadados/certificados confiáveis, aplicar tempo de vida curto e seguir NIST SP 800-63C.

**Referências:**
- OASIS SAML 2.0 Core and Security and Privacy Considerations
- OWASP SAML Security Cheat Sheet (https://cheatsheetseries.owasp.org/cheatsheets/SAML_Security_Cheat_Sheet.html)
- CWE-347: Improper Verification of Cryptographic Signature
- MITRE ATT&CK T1606.002: Forge Web Credentials - SAML Tokens (Golden SAML)
- NIST SP 800-63C: Federation and Assertions
- XML Signature Wrapping - referências acadêmicas / OWASP WSTG

### Sequestro de Sessão (Session Hijacking)

**Classificação:** `defensiva`

**O que é:** Apropriação de uma sessão já autenticada de outro usuário pela obtenção e reutilização do seu identificador de sessão ou token.

**Como funciona:** O atacante captura um session ID/token válido por vias como XSS (leitura de cookie sem HttpOnly ou de tokens em storage do navegador), interceptação de tráfego não cifrado, malware no endpoint, logs que vazam o token ou Referer/URL. De posse do identificador, ele o injeta em suas próprias requisições e é tratado como o usuário legítimo, pois o servidor confia unicamente no valor apresentado. O impacto aumenta quando não há expiração curta, revogação, nem detecção de anomalia de contexto (mudança abrupta de IP/dispositivo).

**Detecção:** Correlacionar em logs de sessão o mesmo token usado simultaneamente por IPs, geolocalizações ou User-Agents divergentes; picos de uso e sessões concorrentes anômalas. Monitorar tentativas de leitura de cookie via XSS (relatórios de CSP, WAF). Revisar se tokens aparecem em logs, URLs ou armazenamento acessível a JS. Ferramentas: SIEM com regras de sessão impossível-viagem, detecção de anomalias e alertas de CSP report-uri.

**Endurecimento:** TLS obrigatório (HSTS), cookies HttpOnly/Secure/SameSite e mitigação de XSS (CSP, saída codificada). Expiração curta com renovação, revogação server-side e logout global; opcionalmente binding da sessão a atributos estáveis do cliente. Tokens de curta duração + refresh rotativo, reautenticação para ações sensíveis e painel de sessões ativas com capacidade de encerrar remotamente. Detecção de anomalia e reemissão/rotação ao detectar mudança de contexto.

**Referências:**
- CWE-613: Insufficient Session Expiration
- CWE-539: Use of Persistent Cookies Containing Sensitive Information
- OWASP Top 10 2021 A07:2021 Identification and Authentication Failures
- MITRE ATT&CK T1539: Steal Web Session Cookie
- MITRE ATT&CK T1550.004: Use Alternate Authentication Material - Web Session Cookie
- OWASP Session Management Cheat Sheet

## Segurança de APIs

### Acesso Irrestrito a Fluxos de Negócio Sensíveis (Unrestricted Access to Sensitive Business Flows)

**Classificação:** `escopo_autorizado`

**O que é:** Exposição de fluxos de negócio (compra, cadastro, resgate, reserva) sem proteção contra automação excessiva, permitindo abuso em escala mesmo sem uma falha técnica de autorização.

**Como funciona:** O fluxo funciona como projetado, mas não considera o risco de ser executado de forma automatizada e massiva. Bots podem comprar todo o estoque (scalping), criar contas em massa para abusar de promoções, inflar métricas ou reservar recursos limitados para revenda. A ausência de detecção de automação, limites por identidade e verificação de intenção humana torna o abuso lucrativo. A avaliação exige entender o modelo de negócio e exercitar o fluxo de forma controlada, portanto requer autorização escrita e regras de engajamento.

**Detecção:** Modelar quais fluxos têm valor de negócio e medir taxa de execução por conta/dispositivo/IP e velocidade entre etapas. Indicadores: cadência sobre-humana, muitas contas com fingerprints semelhantes, alta taxa de conclusão sem comportamento de navegação. Ferramentas: detecção de bots/fingerprinting de dispositivo, análise comportamental, e monitoramento de conversão anômala. Testes de abuso devem ocorrer apenas dentro do escopo autorizado e em ambiente combinado.

**Endurecimento:** Aplicar defesas antiautomação proporcionais ao risco: limites por identidade/dispositivo, desafios adaptativos (CAPTCHA/prova de trabalho), device fingerprinting e detecção de headless. Adicionar controles de negócio (limite por cliente, filas justas, atrasos, verificação de identidade em ações críticas). Combinar com rate limiting e WAF/bot management, monitorando padrões e ajustando continuamente. Evitar depender só de CAPTCHA; usar defesa em camadas.

**Referências:**
- https://owasp.org/API-Security/editions/2023/en/0xa6-unrestricted-access-to-sensitive-business-flows/
- https://cwe.mitre.org/data/definitions/799.html
- https://owasp.org/www-project-automated-threats-to-web-applications/
- https://cheatsheetseries.owasp.org/cheatsheets/Credential_Stuffing_Prevention_Cheat_Sheet.html

### Autenticação Quebrada em APIs (Broken Authentication)

**Classificação:** `defensiva`

**O que é:** Conjunto de falhas nos mecanismos de autenticação da API que permitem assumir a identidade de outros usuários, incluindo tokens mal validados, endpoints de login sem proteção e recuperação de conta fraca.

**Como funciona:** Ocorre quando endpoints de autenticação (login, refresh, reset de senha, OTP) não têm limitação de tentativas, permitindo credential stuffing e força bruta. Também surge de validação incorreta de JWT: aceitar alg=none, não verificar a assinatura, não validar iss/aud/exp, ou usar segredos HMAC fracos/hardcoded. Fluxos de recuperação com tokens previsíveis, OTP sem expiração e ausência de rotação/invalidação de tokens após logout ampliam o impacto. O atacante obtém um token válido ou forja um, passando a agir como a vítima.

**Detecção:** Em código, verificar bibliotecas de JWT configuradas com algoritmo explícito na whitelist e validação de claims; caçar segredos hardcoded (gitleaks, trufflehog). Em logs, monitorar picos de 401/403 por IP/conta, muitas contas por IP, e uso de tokens expirados/revogados. Tráfego: tokens sem expiração curta, ausência de binding de dispositivo. Ferramentas: jwt_tool para inspeção defensiva de tokens em lab próprio, SIEM com regras de brute force/credential stuffing, e testes que enviam alg=none e assinaturas inválidas contra ambiente de teste.

**Endurecimento:** Validar assinatura com algoritmo fixo e chaves geridas (JWKS rotacionado), exigir exp curto e refresh tokens rotacionados com detecção de reuso. Aplicar MFA, rate limiting e lockout progressivo nos endpoints de autenticação, e proteção contra credential stuffing (senhas vazadas, CAPTCHA adaptativo). Padronizar a autenticação num serviço central em vez de reimplementar por rota; invalidar sessões/tokens no logout e na troca de senha. Seguir NIST SP 800-63B para políticas de credencial.

**Referências:**
- https://owasp.org/API-Security/editions/2023/en/0xa2-broken-authentication/
- https://cwe.mitre.org/data/definitions/287.html
- https://cwe.mitre.org/data/definitions/307.html
- https://pages.nist.gov/800-63-3/sp800-63b.html
- https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html
- https://datatracker.ietf.org/doc/html/rfc8725

### Autorização Quebrada em Nível de Propriedade do Objeto (BOPLA)

**Classificação:** `defensiva`

**O que é:** Falha em que a API autoriza acesso ao objeto mas não controla quais propriedades desse objeto podem ser lidas ou escritas, combinando exposição excessiva de dados e mass assignment.

**Como funciona:** No lado de leitura (excessive data exposure), o endpoint serializa o objeto inteiro do banco confiando que o cliente filtrará, vazando campos sensíveis como is_admin, saldo interno ou dados de outros contextos. No lado de escrita (mass assignment), frameworks que fazem auto-binding do corpo JSON diretamente no modelo permitem que o cliente inclua propriedades não previstas (ex.: role=admin, verified=true) e escale privilégios. Em ambos os casos a autorização por objeto pode estar correta, mas o controle por propriedade está ausente.

**Detecção:** Revisar serializers e DTOs: procurar retorno de entidades ORM cru em vez de projeções explícitas. Caçar auto-binding sem allowlist (ex.: Object.assign(model, req.body), model.update(req.body), @ModelAttribute sem whitelist). Diferenciar respostas por papel para ver se campos sensíveis aparecem. Ferramentas: Semgrep/CodeQL para padrões de mass assignment, revisão de contratos OpenAPI comparando schema exposto x dados reais, e testes que injetam propriedades extras no payload em ambiente de teste.

**Endurecimento:** Usar DTOs/esquemas de entrada e saída explícitos com allowlist de campos por operação e por papel; nunca serializar a entidade de persistência diretamente. Desabilitar auto-binding permissivo e adotar binding somente de campos declarados. Validar payloads contra JSON Schema/OpenAPI rejeitando propriedades adicionais (additionalProperties:false). Aplicar mascaramento/redação de campos sensíveis na camada de resposta e testes de contrato no CI.

**Referências:**
- https://owasp.org/API-Security/editions/2023/en/0xa3-broken-object-property-level-authorization/
- https://cwe.mitre.org/data/definitions/915.html
- https://cwe.mitre.org/data/definitions/213.html
- https://cheatsheetseries.owasp.org/cheatsheets/Mass_Assignment_Cheat_Sheet.html
- https://json-schema.org/understanding-json-schema/reference/object

### Chaves de API, Escopos e Tokens OAuth (API Keys e Scopes)

**Classificação:** `defensiva`

**O que é:** Gestão segura de credenciais de API (chaves e tokens OAuth) com escopos mínimos, armazenamento protegido, rotação e revogação para limitar o impacto de vazamentos.

**Como funciona:** Chaves de API identificam e autenticam um cliente/aplicação, enquanto OAuth 2.0/OIDC emite tokens de acesso com escopos que delimitam o que o token pode fazer. Sem escopos granulares, uma única credencial vazada dá acesso amplo; chaves de longa duração sem rotação ampliam a janela de abuso. Segredos costumam vazar em repositórios, logs, URLs (query string), apps móveis e front-end. Confundir autenticação (quem é) com autorização (o que pode) leva a chaves que autenticam mas não restringem privilégios. Tokens sem expiração e sem revogação permanecem válidos após comprometimento.

**Detecção:** Fazer varredura de segredos em código, histórico git, logs e artefatos (gitleaks, trufflehog); revisar se chaves aparecem em URLs. Verificar escopos atribuídos x necessários e prazos de validade. Em logs, monitorar uso de chave a partir de origens/geografias anômalas e chamadas fora do escopo esperado. Ferramentas: secret scanning no CI, gerenciadores de segredos com auditoria, e detecção de push de segredos.

**Endurecimento:** Atribuir o menor escopo/privilégio possível por credencial e separar chaves por ambiente e por integração. Armazenar segredos em cofre (vault/secret manager), nunca no código ou em URLs; transmitir tokens em cabeçalho Authorization sobre TLS. Definir expiração curta para tokens, rotação periódica de chaves e revogação imediata; preferir OAuth2 com escopos a chaves estáticas quando aplicável. Registrar e monitorar uso, e implementar processo de resposta a vazamento (revogar e rotacionar).

**Referências:**
- https://datatracker.ietf.org/doc/html/rfc6749
- https://datatracker.ietf.org/doc/html/rfc6750
- https://cwe.mitre.org/data/definitions/798.html
- https://cwe.mitre.org/data/definitions/522.html
- https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html
- https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html

### Configuração Incorreta de Segurança em APIs (Security Misconfiguration)

**Classificação:** `defensiva`

**O que é:** Falhas decorrentes de configurações inseguras ou incompletas em qualquer camada da API, como CORS permissivo, cabeçalhos ausentes, TLS fraco, mensagens de erro verbosas e recursos de depuração ativos.

**Como funciona:** A superfície de configuração de uma API é ampla: servidor, framework, gateway, nuvem e a própria aplicação. Erros comuns incluem CORS com Access-Control-Allow-Origin: * junto de credenciais, ausência de cabeçalhos de segurança, TLS desatualizado, métodos HTTP não usados habilitados, stack traces detalhados em erros, e ambientes de depuração expostos em produção. Cada configuração fraca oferece informação ou vetor extra ao atacante, muitas vezes combinando-se com outras falhas. Padrões inseguros de fábrica e drift de configuração agravam o problema.

**Detecção:** Escanear cabeçalhos de resposta e política CORS; verificar versões de TLS/ciphers; provocar erros para checar verbosidade. Ferramentas: scanners de configuração (nikto, testssl.sh, scanners de nuvem/CIS benchmarks), linters de IaC, e revisão de OpenAPI x implementação real. Em logs, detectar acesso a rotas de debug e respostas com detalhes internos.

**Endurecimento:** Adotar baseline de configuração endurecida e repetível (IaC + benchmarks CIS), com processo de hardening automatizado por ambiente. Restringir CORS a origens específicas, desabilitar métodos e recursos de debug não usados, e retornar erros genéricos sem detalhes internos. Forçar TLS moderno e cabeçalhos de segurança apropriados; manter dependências atualizadas. Verificar configuração continuamente com scans automatizados e detecção de drift.

**Referências:**
- https://owasp.org/API-Security/editions/2023/en/0xa8-security-misconfiguration/
- https://owasp.org/Top10/A05_2021-Security_Misconfiguration/
- https://cwe.mitre.org/data/definitions/16.html
- https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html
- https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html

### Consumo Inseguro de APIs (Unsafe Consumption of APIs)

**Classificação:** `defensiva`

**O que é:** Confiança excessiva nos dados recebidos de APIs de terceiros ou upstream, tratando-os com menos rigor do que a entrada direta do usuário e propagando falhas para dentro do sistema.

**Como funciona:** Ao integrar com serviços externos, desenvolvedores frequentemente assumem que os dados de retorno são confiáveis e os processam sem validação, sanitização ou limites. Se o terceiro for comprometido, malicioso ou simplesmente inconsistente, respostas manipuladas podem causar injeção, desserialização insegura, SSRF via redirecionamentos, ou consumo excessivo de recursos no consumidor. Canais inseguros (TLS ausente), seguir redirecionamentos cegamente e ausência de timeouts ampliam o risco. A falha desloca a confiança para fora do perímetro de controle.

**Detecção:** Revisar todo cliente de API externa para verificar validação de esquema da resposta, tratamento de erros e limites. Indicadores: parsing direto de JSON externo em objetos, redirecionamentos seguidos automaticamente, ausência de timeout/limite de tamanho. Ferramentas: análise estática de clientes HTTP, testes com respostas maliciosas simuladas (mock/servidor de teste próprio), e monitoramento de tráfego para integrações.

**Endurecimento:** Validar e sanitizar dados de terceiros com o mesmo rigor da entrada do usuário (JSON Schema, allowlists, limites de tamanho). Usar TLS e verificação de certificado, não seguir redirecionamentos para hosts não confiáveis, e aplicar timeouts e circuit breakers. Isolar integrações, aplicar menor privilégio às credenciais e evitar desserialização insegura. Avaliar a postura de segurança dos fornecedores e tratar o pipeline como cadeia de suprimento.

**Referências:**
- https://owasp.org/API-Security/editions/2023/en/0xaa-unsafe-consumption-of-apis/
- https://cwe.mitre.org/data/definitions/20.html
- https://cwe.mitre.org/data/definitions/502.html
- https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html
- https://cheatsheetseries.owasp.org/cheatsheets/Deserialization_Cheat_Sheet.html

### Consumo Irrestrito de Recursos (Unrestricted Resource Consumption)

**Classificação:** `defensiva`

**O que é:** Falta de limites sobre CPU, memória, banda, chamadas a terceiros ou custo financeiro que uma requisição pode consumir, permitindo negação de serviço ou explosão de custos.

**Como funciona:** A API não impõe cotas por cliente nem limita o custo de operações individuais. Requisições podem pedir paginação com page_size gigante, uploads sem limite de tamanho, expansões aninhadas caras, ou disparar operações que chamam serviços pagos (SMS, e-mail, IA) sem teto. Sem rate limiting e sem timeouts, um único cliente satura threads, conexões de banco ou orçamento de terceiros. O impacto vai de indisponibilidade a prejuízo financeiro direto (denial of wallet).

**Detecção:** Auditar endpoints buscando parâmetros de tamanho/limite sem validação de máximo, ausência de timeouts e de limites de payload. Em logs/métricas, observar latência crescente, uso anômalo de CPU/memória por cliente, e volume de chamadas a APIs pagas. Ferramentas: APM (traços de latência), rate limiter com métricas expostas, alertas de custo no provedor de nuvem/terceiros, e teste de carga controlado em ambiente próprio para medir limites.

**Endurecimento:** Impor rate limiting e cotas por API key/usuário/IP com algoritmos de token bucket/sliding window num ponto compartilhado (gateway/Redis), não por instância. Definir limites máximos de page_size, profundidade de query, tamanho de upload e tempo de execução; aplicar timeouts e circuit breakers em dependências. Estabelecer tetos de gasto e alertas em serviços pagos, além de backpressure e filas. Testar limites em carga e degradar graciosamente (429 com Retry-After).

**Referências:**
- https://owasp.org/API-Security/editions/2023/en/0xa4-unrestricted-resource-consumption/
- https://cwe.mitre.org/data/definitions/770.html
- https://cwe.mitre.org/data/definitions/400.html
- https://datatracker.ietf.org/doc/html/rfc6585
- https://cheatsheetseries.owasp.org/cheatsheets/Denial_of_Service_Cheat_Sheet.html

### Gestão Inadequada de Inventário (Improper Inventory Management)

**Classificação:** `defensiva`

**O que é:** Falta de visibilidade e controle sobre todos os hosts, versões e endpoints da API, deixando versões antigas, ambientes de teste e endpoints não documentados expostos.

**Como funciona:** Organizações publicam múltiplas versões e ambientes (v1, v2, staging, beta) e, sem inventário rigoroso, versões antigas ('zombie APIs') e endpoints não documentados ('shadow APIs') permanecem acessíveis. Versões descontinuadas frequentemente não recebem patches e carregam falhas já corrigidas na versão atual. Ambientes de teste com dados reais ou controles relaxados ficam expostos à internet. O atacante enumera hosts e versões e escolhe a superfície mais fraca para atacar.

**Detecção:** Manter e comparar um inventário automatizado de hosts/endpoints/versões (descoberta ativa e passiva de tráfego) contra o que deveria existir. Indicadores: subdomínios e paths esquecidos, respostas de versões antigas, docs desatualizadas. Ferramentas: descoberta de API (gateways com catálogo, scanners de subdomínio, análise de tráfego norte-sul), diffing de especificações OpenAPI, e monitoramento de superfície de ataque externa (ASM).

**Endurecimento:** Manter um inventário centralizado e vivo de todas as APIs, versões e ambientes, integrado ao ciclo de deploy (registro obrigatório no gateway). Definir política de versionamento e depreciação com sunset planejado e desativação efetiva de versões antigas. Segregar e proteger ambientes não produtivos, sem dados reais, e documentar toda a superfície. Automatizar descoberta contínua para detectar shadow/zombie APIs.

**Referências:**
- https://owasp.org/API-Security/editions/2023/en/0xa9-improper-inventory-management/
- https://cwe.mitre.org/data/definitions/1059.html
- https://datatracker.ietf.org/doc/html/rfc8594
- https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html

### Limitação de Taxa e Cotas (Rate Limiting e Quotas)

**Classificação:** `defensiva`

**O que é:** Controle que limita a frequência e o volume de requisições por cliente para proteger disponibilidade, conter abuso e mitigar força bruta e negação de serviço.

**Como funciona:** Um limitador de taxa contabiliza requisições por chave (API key, usuário, IP, tenant) numa janela de tempo usando algoritmos como token bucket, leaky bucket, fixed window ou sliding window log/counter. Ao exceder o limite, a API responde 429 com Retry-After. Cotas de longo prazo (diárias/mensais) complementam os limites de curto prazo. Em serviços distribuídos, o estado do contador precisa ser compartilhado (ex.: Redis) ou as réplicas contam separadamente, tornando o limite real N vezes maior e explorável. Chaves mal escolhidas (só por IP atrás de CGNAT/proxy) causam falsos positivos ou evasão.

**Detecção:** Confirmar onde o contador reside: por instância (frágil) ou em store compartilhado. Testar com carga controlada para medir o limite efetivo por réplica. Indicadores em logs: ausência de 429 sob rajada, ou limites que escalam com o número de instâncias. Ferramentas: dashboards do gateway/limitador, métricas de 429, e testes de carga próprios comparando limite configurado x observado.

**Endurecimento:** Centralizar o rate limiting no gateway ou em store distribuído (Redis) para valer globalmente entre réplicas; escolher a chave por identidade autenticada e não só por IP. Combinar limites de curto prazo com cotas e usar sliding window para suavidade. Retornar 429 com Retry-After e cabeçalhos de limite; aplicar limites mais estritos em endpoints sensíveis (login, reset). Validar o IP do cliente de forma confiável atrás de proxies (cabeçalho confiável definido pela borda).

**Referências:**
- https://datatracker.ietf.org/doc/html/rfc6585
- https://datatracker.ietf.org/doc/html/draft-ietf-httpapi-ratelimit-headers
- https://cwe.mitre.org/data/definitions/770.html
- https://owasp.org/API-Security/editions/2023/en/0xa4-unrestricted-resource-consumption/
- https://cheatsheetseries.owasp.org/cheatsheets/Denial_of_Service_Cheat_Sheet.html

### Segurança de GraphQL (Introspecção, Batching e Limite de Profundidade)

**Classificação:** `defensiva`

**O que é:** Conjunto de riscos específicos de GraphQL decorrentes de consultas flexíveis do cliente, incluindo exposição de esquema por introspecção e negação de serviço por consultas profundas, aliasing e batching.

**Como funciona:** GraphQL expõe um único endpoint onde o cliente monta a forma da consulta, o que amplifica riscos de custo. A introspecção habilitada revela todo o esquema, incluindo campos internos e depreciados. Consultas profundamente aninhadas ou com ciclos, muitos aliases do mesmo campo caro, e batching de múltiplas operações numa única requisição podem multiplicar o trabalho do servidor e causar DoS. Além disso, a autorização precisa ser aplicada por campo/resolver, e resolvers ingênuos geram problemas N+1 e vazamento de dados. Erros verbosos e a natureza dinâmica dificultam rate limiting simples por rota.

**Detecção:** Verificar se introspecção está ativa em produção e se há limites de profundidade/complexidade configurados. Em tráfego, detectar consultas com aninhamento profundo, muitos aliases ou arrays grandes de operações batched. Ferramentas: análise de complexidade de consulta, logging de custo por operação, GraphQL Armor/inspetores de esquema, e testes de profundidade em ambiente controlado. Revisar resolvers quanto a checagens de autorização por campo.

**Endurecimento:** Desabilitar introspecção e sugestões de campo em produção; impor limites de profundidade, de complexidade/custo e de número de aliases, além de desabilitar ou limitar batching. Aplicar rate limiting baseado em custo, timeouts e paginação obrigatória; usar dataloaders para evitar N+1. Autorizar por campo/resolver e usar consultas persistidas (allowlist) quando possível. Padronizar erros sem detalhes internos.

**Referências:**
- https://cheatsheetseries.owasp.org/cheatsheets/GraphQL_Cheat_Sheet.html
- https://cwe.mitre.org/data/definitions/770.html
- https://cwe.mitre.org/data/definitions/400.html
- https://graphql.org/learn/security/
- https://owasp.org/API-Security/editions/2023/en/0xa4-unrestricted-resource-consumption/

### Segurança de Webhooks (Assinatura, Verificação e Anti-Replay)

**Classificação:** `defensiva`

**O que é:** Práticas para receber e enviar webhooks com segurança, garantindo autenticidade, integridade e proteção contra repetição e falsificação de origem.

**Como funciona:** Webhooks são callbacks HTTP que um serviço envia a um endpoint do cliente ao ocorrer um evento. Como o endpoint receptor é público, sem verificação qualquer um pode forjar eventos (ex.: 'pagamento aprovado'). A prática padrão é o emissor assinar o corpo com HMAC usando um segredo compartilhado e enviar a assinatura num cabeçalho; o receptor recomputa e compara em tempo constante. Um timestamp assinado com janela de tolerância evita replay. No lado do emissor, permitir URLs arbitrárias de destino cria risco de SSRF e de uso como proxy.

**Detecção:** Verificar se o handler de webhook valida assinatura HMAC, timestamp e idempotência antes de processar. Indicadores de risco: processamento sem verificação, comparação de assinatura não constante, ausência de janela de tempo. Ferramentas: revisão de código do receptor, logs de assinaturas inválidas/eventos duplicados, e testes enviando payloads sem assinatura em ambiente próprio.

**Endurecimento:** No receptor: verificar HMAC do corpo bruto com comparação em tempo constante, validar timestamp com janela curta, rejeitar duplicatas por ID de evento (idempotência) e responder rápido processando de forma assíncrona. Usar HTTPS e, quando possível, mTLS ou allowlist de IPs de origem. No emissor: validar destinos com allowlist (mitigar SSRF), assinar payloads, aplicar retries com backoff e rotacionar segredos. Nunca confiar em campos do corpo sem verificar a assinatura.

**Referências:**
- https://cwe.mitre.org/data/definitions/345.html
- https://cwe.mitre.org/data/definitions/347.html
- https://datatracker.ietf.org/doc/html/rfc2104
- https://www.rfc-editor.org/rfc/rfc9421.html
- https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html

## Transporte, TLS, Cabeçalhos e DNS

### Ataques ao Cabeçalho Host (Host Header Injection / Poisoning)

**Classificação:** `defensiva`

**O que é:** Aplicações que confiam no cabeçalho Host (ou em X-Forwarded-Host) para construir URLs absolutas, links de redefinição de senha ou chaves de cache podem ser induzidas a gerar conteúdo apontando para um domínio controlado pelo atacante, resultando em envenenamento de e-mails de recuperação, de cache ou de redirecionamentos.

**Como funciona:** O cabeçalho Host é fornecido pelo cliente e, em muitas arquiteturas, também há cabeçalhos como X-Forwarded-Host inseridos por proxies. Se a aplicação usa esse valor sem validação para montar URLs absolutas — por exemplo, o link em um e-mail de redefinição de senha — um atacante pode definir um Host arbitrário e fazer o sistema gerar um link que aponta para seu próprio servidor, capturando o token quando a vítima clicar. O mesmo valor não validado pode contaminar chaves de cache ou alimentar redirecionamentos. A raiz é confiar em um cabeçalho controlável pelo cliente como se fosse a identidade canônica do servidor. A defesa é derivar o host de uma configuração confiável e validar o cabeçalho recebido contra uma allowlist.

**Detecção:** Monitore valores de Host e X-Forwarded-Host fora dos domínios esperados e alerte quando aparecerem em requisições a endpoints sensíveis (recuperação de conta, geração de links). Inspecione e-mails transacionais gerados para confirmar que apontam sempre para o domínio canônico. Correlacione tokens de redefinição usados a partir de origens/hosts anômalos.

**Endurecimento:** Defina o domínio canônico a partir de configuração do servidor, não do cabeçalho da requisição, ao construir URLs absolutas e links. Valide o Host recebido contra uma allowlist estrita e rejeite ou normalize o restante; trate X-Forwarded-Host como não confiável a menos que venha de um proxy sob seu controle. Configure o servidor web com host virtual padrão que recuse hosts desconhecidos. Inclua o Host correto na chave de cache apenas quando validado. Use tokens de redefinição de curta duração, de uso único e vinculados à conta para reduzir o impacto residual.

**Referências:**
- PortSwigger Web Security Academy: HTTP Host header attacks
- OWASP: Host Header Injection
- OWASP Cheat Sheet Series: Forgot Password
- CWE-644: Improper Neutralization of HTTP Headers for Scripting Syntax

### Autenticação de e-mail (SPF, DKIM, DMARC)

**Classificação:** `defensiva`

**O que é:** Trio de controles baseados em DNS que autenticam a origem de e-mails e reduzem falsificação de domínio e phishing.

**Como funciona:** SPF publica no DNS quais servidores estão autorizados a enviar e-mail pelo domínio, validando o endereço de envelope (MAIL FROM). DKIM adiciona uma assinatura criptográfica ao cabeçalho da mensagem, cuja chave pública fica no DNS, garantindo integridade e origem. DMARC amarra SPF e DKIM ao domínio visível (cabeçalho From) via alinhamento, define a política para mensagens não autenticadas (none/quarantine/reject) e habilita relatórios agregados. Sem esses controles, atacantes podem falsificar o remetente para phishing e comprometimento de e-mail corporativo (BEC).

**Detecção:** Consultar registros com dig TXT (v=spf1, _dmarc, seletor._domainkey) e validadores como MXToolbox; analisar relatórios agregados DMARC (RUA) para identificar fontes de envio e falhas de alinhamento. Monitorar cabeçalhos Authentication-Results nos e-mails recebidos e alertar sobre volume de falhas. Verificar limite de 10 lookups do SPF e registros duplicados.

**Endurecimento:** Publicar SPF preciso terminando em -all (hardfail), habilitar DKIM com chaves >=2048 bits e rotação, e implantar DMARC progredindo de p=none para p=quarantine e p=reject com alinhamento estrito. Configurar endereços RUA/RUF para receber relatórios e monitorar continuamente; considerar BIMI e MTA-STS/TLS-RPT para reforçar transporte seguro entre servidores. Manter inventário de todos os remetentes legítimos (ferramentas de marketing, ERPs) antes de endurecer a política.

**Referências:**
- https://datatracker.ietf.org/doc/html/rfc7208
- https://datatracker.ietf.org/doc/html/rfc6376
- https://datatracker.ietf.org/doc/html/rfc7489
- https://cwe.mitre.org/data/definitions/290.html
- https://attack.mitre.org/techniques/T1656/
- https://www.cisa.gov/resources-tools/resources/trustworthy-email-nist-sp-800-177

### Avaliação de configuração TLS e cabeçalhos de segurança (varredura autorizada)

**Classificação:** `escopo_autorizado`

**O que é:** Processo autorizado de enumerar e avaliar a postura de TLS, certificados e cabeçalhos HTTP de um alvo dentro de escopo definido.

**Como funciona:** A avaliação envia handshakes TLS e requisições HTTP para inventariar versões de protocolo, cipher suites, propriedades do certificado, suporte a PFS e presença/valor de cabeçalhos de segurança, comparando os resultados com baselines (Mozilla SSL, NIST SP 800-52r2). Ferramentas de fingerprinting revelam pilhas obsoletas, cifras fracas, HSTS ausente e políticas CSP permissivas. Trata-se de reconhecimento não intrusivo, mas mesmo varreduras devem respeitar autorização escrita, escopo e regras de engajamento para evitar impacto e questões legais. O objetivo é priorizar correções, não explorar.

**Detecção:** Do lado defensivo, correlacionar picos de handshakes e requisições de enumeração em WAF/IDS e diferenciar varreduras autorizadas (janelas e IPs acordados) de atividade não autorizada. Manter os próprios relatórios de baseline em CI para detectar regressões de configuração. Registrar e revisar mudanças na postura TLS/cabeçalhos ao longo do tempo.

**Endurecimento:** Integrar varreduras (testssl.sh, sslyze, nmap ssl-enum-ciphers, securityheaders) em pipelines para impor baselines antes de produção. Corrigir achados priorizando protocolos/cifras obsoletos, cadeia incompleta, expiração e cabeçalhos ausentes; padronizar configuração via infraestrutura como código. Documentar escopo e autorização de qualquer avaliação e reexecutar após mudanças de configuração ou renovação de certificados.

**Referências:**
- https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Protection_Cheat_Sheet.html
- https://github.com/drwetter/testssl.sh
- https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-52r2.pdf
- https://owasp.org/www-project-web-security-testing-guide/
- https://ssl-config.mozilla.org/
- https://owasp.org/Top10/A05_2021-Security_Misconfiguration/

### Cabeçalhos de segurança HTTP complementares (X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy)

**Classificação:** `defensiva`

**O que é:** Conjunto de cabeçalhos de resposta que endurecem o comportamento do navegador contra sniffing de MIME, enquadramento malicioso, vazamento de referer e abuso de APIs.

**Como funciona:** X-Content-Type-Options: nosniff impede o navegador de adivinhar o tipo de conteúdo, bloqueando execução de recursos com MIME incorreto. X-Frame-Options (DENY/SAMEORIGIN) e o moderno frame-ancestors do CSP impedem que a página seja embutida em iframes de terceiros, mitigando clickjacking. Referrer-Policy controla quanto da URL de origem é enviado em navegações e requisições, reduzindo vazamento de dados sensíveis em query strings. Permissions-Policy (antiga Feature-Policy) restringe quais APIs poderosas (câmera, geolocalização, microfone) podem ser usadas pela página e por iframes embutidos.

**Detecção:** Scanners como securityheaders.com, Mozilla Observatory e nikto reportam ausência desses cabeçalhos. Inspecionar respostas com curl -I e revisar a configuração do servidor/proxy/framework centralizadamente. Testar clickjacking com uma página de prova em iframe apenas em ambiente autorizado.

**Endurecimento:** Definir X-Content-Type-Options: nosniff em todas as respostas; usar frame-ancestors no CSP (mantendo X-Frame-Options: DENY/SAMEORIGIN para navegadores antigos). Aplicar Referrer-Policy restritiva como strict-origin-when-cross-origin ou no-referrer para páginas sensíveis, e Permissions-Policy negando por padrão APIs não usadas. Centralizar esses cabeçalhos em middleware/gateway para consistência e considerar COOP/COEP quando aplicável.

**Referências:**
- https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html
- https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Content-Type-Options
- https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Referrer-Policy
- https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Permissions-Policy
- https://cwe.mitre.org/data/definitions/1021.html
- https://owasp.org/Top10/A05_2021-Security_Misconfiguration/

### Certificados X.509 e cadeia de confiança (PKI)

**Classificação:** `defensiva`

**O que é:** Estrutura de certificados digitais e sua validação encadeada até uma âncora de confiança que autentica a identidade do servidor TLS.

**Como funciona:** Um certificado X.509 vincula uma chave pública a uma identidade (hostname no SubjectAltName) e é assinado por uma CA; o cliente valida a assinatura subindo a cadeia até uma raiz confiável no seu truststore. A validação correta exige verificar assinatura, período de validade, correspondência de hostname (SAN, não apenas CN), status de revogação (OCSP/CRL) e restrições de uso. Falhas comuns são certificados autoassinados aceitos, validação de hostname desativada, cadeia incompleta enviada pelo servidor e confiança em CAs comprometidas. Certificate Transparency (CT) registra emissões em logs públicos auditáveis, permitindo detectar emissões indevidas para um domínio.

**Detecção:** Monitorar logs de Certificate Transparency (crt.sh, ferramentas de CT monitoring) para emissões inesperadas do seu domínio. Auditar validade e cadeia com openssl s_client, testssl.sh e verificadores de expiração; alertar sobre certificados a expirar. Em código, revisar clientes HTTP que desabilitam verificação (verify=False, TrustManager que aceita tudo, InsecureSkipVerify) e detectar via SAST.

**Endurecimento:** Automatizar emissão e renovação via ACME (ex.: Let's Encrypt/certbot) para evitar expiração; enviar a cadeia intermediária completa. Nunca desabilitar validação de certificado ou de hostname em clientes; usar truststores mínimos e atualizados. Habilitar CAA no DNS para restringir quais CAs podem emitir, monitorar CT logs e considerar OCSP stapling para checagem de revogação eficiente.

**Referências:**
- https://datatracker.ietf.org/doc/html/rfc5280
- https://cwe.mitre.org/data/definitions/295.html
- https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Security_Cheat_Sheet.html
- https://datatracker.ietf.org/doc/html/rfc6962
- https://datatracker.ietf.org/doc/html/rfc8659
- https://letsencrypt.org/docs/
- https://owasp.org/Top10/A02_2021-Cryptographic_Failures/

### Content-Security-Policy (CSP)

**Classificação:** `defensiva`

**O que é:** Cabeçalho que define uma política de origens permitidas para scripts, estilos e demais recursos, mitigando XSS e injeção de conteúdo.

**Como funciona:** O navegador aplica a política declarada em Content-Security-Policy restringindo de quais origens cada tipo de recurso pode ser carregado e se scripts inline/eval podem executar. Uma política forte usa nonces ou hashes por script e 'strict-dynamic', bloqueando a execução de scripts injetados por um atacante mesmo que ele consiga inserir markup. Diretivas como frame-ancestors controlam enquadramento (anti-clickjacking) e report-to/report-uri enviam violações para monitoramento. Políticas fracas com 'unsafe-inline' ou curingas amplos (*) reduzem drasticamente a proteção contra XSS.

**Detecção:** Validar a política com Google CSP Evaluator, Mozilla Observatory e securityheaders.com para identificar 'unsafe-inline', 'unsafe-eval' e curingas. Usar modo Content-Security-Policy-Report-Only para coletar violações sem quebrar a aplicação e analisar relatórios. Revisar no código a geração de nonces por requisição e a ausência de scripts inline sem nonce.

**Endurecimento:** Adotar CSP baseada em nonce/hash com 'strict-dynamic', definir default-src 'none' ou 'self' e listar explicitamente origens; evitar 'unsafe-inline' e 'unsafe-eval'. Incluir frame-ancestors 'none'/'self' para anti-clickjacking, object-src 'none', base-uri 'self' e habilitar relatórios via report-to. Implantar primeiro em Report-Only, refinar a partir das violações e então impor; regenerar nonce a cada resposta.

**Referências:**
- https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html
- https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy
- https://csp-evaluator.withgoogle.com/
- https://www.w3.org/TR/CSP3/
- https://cwe.mitre.org/data/definitions/79.html
- https://owasp.org/Top10/A03_2021-Injection/

### Conteúdo misto (Mixed Content)

**Classificação:** `defensiva`

**O que é:** Situação em que uma página carregada por HTTPS inclui sub-recursos via HTTP, expondo parte do tráfego a interceptação e manipulação.

**Como funciona:** Quando uma página segura (HTTPS) referencia recursos por http://, esses sub-recursos trafegam em texto claro e podem ser lidos ou alterados por um atacante no caminho. Conteúdo misto ativo (scripts, iframes, CSS, XHR/fetch) é o mais perigoso pois permite execução de código e comprometimento total da página, sendo por isso bloqueado por padrão pelos navegadores modernos. Conteúdo misto passivo (imagens, mídia) é geralmente permitido mas ainda vaza informação e pode ser adulterado. A presença de mixed content quebra as garantias do HTTPS e do HSTS para aquela porção do carregamento.

**Detecção:** Console do navegador registra avisos/bloqueios de mixed content; scanners e crawlers detectam URLs http em páginas https. Usar CSP em modo report para receber violações de recursos inseguros e revisar o código/templates por links http:// codificados. Monitorar recursos de terceiros que possam servir http.

**Endurecimento:** Servir todos os recursos por HTTPS e usar URLs relativas ao protocolo ou absolutas https. Aplicar a diretiva CSP upgrade-insecure-requests para reescrever automaticamente requisições e block-all-mixed-content como defesa adicional. Combinar com HSTS, corrigir links legados em conteúdo/banco de dados e garantir que integrações e CDNs suportem HTTPS.

**Referências:**
- https://developer.mozilla.org/en-US/docs/Web/Security/Mixed_content
- https://www.w3.org/TR/mixed-content/
- https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Security_Cheat_Sheet.html
- https://cwe.mitre.org/data/definitions/319.html
- https://owasp.org/Top10/A02_2021-Cryptographic_Failures/

### Cookies seguros (Secure, HttpOnly, SameSite)

**Classificação:** `defensiva`

**O que é:** Atributos de cookies que restringem sua transmissão a canais seguros, seu acesso por scripts e seu envio em requisições cross-site.

**Como funciona:** O atributo Secure garante que o cookie só seja enviado sobre HTTPS, evitando interceptação em texto claro. HttpOnly impede leitura via JavaScript (document.cookie), reduzindo o impacto de XSS no roubo de sessão. SameSite (Lax/Strict/None) controla se o cookie é enviado em requisições originadas de outros sites, mitigando CSRF; SameSite=None exige Secure. Os prefixos __Host- e __Secure- impõem restrições adicionais (Secure obrigatório, sem Domain amplo, Path=/) que dificultam fixação e sobrescrita por subdomínios.

**Detecção:** Inspecionar Set-Cookie em respostas via DevTools/curl e verificar flags ausentes; ferramentas como ZAP e Burp sinalizam cookies de sessão sem Secure/HttpOnly/SameSite. Revisar a configuração de sessão do framework e o código que emite cookies. Auditar em logs/proxy cookies de autenticação transmitidos sem Secure.

**Endurecimento:** Marcar todos os cookies de sessão/autenticação com Secure e HttpOnly e definir SameSite=Lax (ou Strict para operações sensíveis); usar SameSite=None+Secure só quando cross-site for necessário. Aplicar o prefixo __Host- em cookies de sessão, escopo de Path e Domain mínimo e expiração curta. Combinar com tokens anti-CSRF, pois SameSite não substitui totalmente a proteção CSRF em todos os navegadores/fluxos.

**Referências:**
- https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html
- https://datatracker.ietf.org/doc/html/draft-ietf-httpbis-rfc6265bis
- https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie
- https://cwe.mitre.org/data/definitions/614.html
- https://cwe.mitre.org/data/definitions/1004.html
- https://owasp.org/Top10/A05_2021-Security_Misconfiguration/

### Downgrade de TLS e interceptação no transporte (TLS stripping / MITM)

**Classificação:** `laboratorio_autorizado`

**O que é:** Classe de ataques em que um adversário na rede rebaixa ou intercepta a conexão TLS para observar ou alterar o tráfego, estudada apenas em laboratório próprio.

**Como funciona:** Um atacante posicionado no caminho (via ARP spoofing, ponto de acesso malicioso ou DNS forjado) intercepta a conexão e força o cliente a comunicar em HTTP ou com parâmetros TLS mais fracos, retransmitindo o tráfego ao servidor real. No TLS stripping, a primeira requisição em texto claro é convertida para manter o usuário em HTTP enquanto o atacante fala HTTPS com o servidor. Também se enquadram ataques de downgrade de versão/cifra que exploram fallback inseguro. Compreender esse mecanismo é essencial para validar defesas; a reprodução deve ocorrer exclusivamente em redes e sistemas próprios de laboratório controlado, nunca contra terceiros.

**Detecção:** Em laboratório, comparar a versão TLS e o certificado observados no cliente com o esperado; alertar quando conexões que deveriam ser HTTPS chegam em HTTP. No lado servidor/rede, monitorar tabelas ARP anômalas, certificados inesperados e falhas de HSTS/validação. Ferramentas de análise de tráfego (Wireshark) ajudam a inspecionar handshakes e downgrades em ambiente autorizado.

**Endurecimento:** Impor HSTS com preload e includeSubDomains para eliminar a janela HTTP inicial, desabilitar fallback para versões antigas e usar TLS 1.3 (que remove muitos vetores de downgrade). Habilitar TLS_FALLBACK_SCSV, validar rigorosamente certificados e hostname nos clientes e aplicar pinning onde apropriado. Em redes, usar segmentação, detecção de ARP spoofing/rogue AP, 802.1X e DNSSEC/DoH para reduzir a superfície de interceptação.

**Referências:**
- https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Security_Cheat_Sheet.html
- https://attack.mitre.org/techniques/T1557/
- https://cwe.mitre.org/data/definitions/319.html
- https://datatracker.ietf.org/doc/html/rfc7507
- https://owasp.org/Top10/A02_2021-Cryptographic_Failures/

### Fixação de certificado (Certificate/Public Key Pinning)

**Classificação:** `defensiva`

**O que é:** Técnica em que o cliente valida que o certificado ou a chave pública do servidor corresponde a um conjunto pré-definido, reduzindo o risco de CAs comprometidas.

**Como funciona:** Em vez de confiar em qualquer certificado assinado por uma CA do truststore, o cliente 'fixa' o hash da chave pública (SPKI) ou do certificado esperado e recusa conexões que não correspondam, mesmo que sejam tecnicamente válidas. Isso protege contra CAs mal-intencionadas ou comprometidas e contra interceptação por proxies TLS não autorizados, sendo comum em aplicativos móveis. Requer pinos de backup e um plano de rotação, pois um pino incorreto ou expirado sem backup pode inutilizar o aplicativo (self-DoS). O antigo HPKP baseado em cabeçalho HTTP foi depreciado nos navegadores por seus riscos; o pinning permanece relevante em apps móveis e clientes controlados.

**Detecção:** Revisar o código do cliente/app por implementações de pinning (TrustManager customizado, configuração de network security, bibliotecas de pinning) e validar presença de pinos de backup. Testar rotação em ambiente controlado e monitorar falhas de conexão pós-troca de certificado. Em avaliações de app autorizadas, verificar robustez do pinning e ausência de bypass trivial.

**Endurecimento:** Fixar a chave pública (SPKI) em vez do certificado folha para sobreviver a renovações, sempre com ao menos um pino de backup e monitoramento de expiração. Documentar e automatizar o processo de rotação, alinhando com o ciclo de emissão de certificados. Para web, preferir HSTS + Certificate Transparency + CAA em vez do HPKP depreciado; em apps móveis, seguir OWASP MASVS/MASTG para configuração segura de rede.

**Referências:**
- https://cheatsheetseries.owasp.org/cheatsheets/Pinning_Cheat_Sheet.html
- https://owasp.org/www-project-mobile-app-security/
- https://cwe.mitre.org/data/definitions/295.html
- https://developer.android.com/privacy-and-security/security-config
- https://datatracker.ietf.org/doc/html/rfc7469

### HTTP Strict Transport Security (HSTS)

**Classificação:** `defensiva`

**O que é:** Cabeçalho de resposta que instrui o navegador a acessar um domínio exclusivamente por HTTPS por um período definido.

**Como funciona:** O servidor envia o cabeçalho Strict-Transport-Security com uma diretiva max-age; o navegador passa a converter automaticamente qualquer requisição http:// para https:// e a bloquear cliques de contorno de erros de certificado para aquele host. Isso mitiga ataques de TLS/SSL stripping, em que um atacante na rede rebaixa a primeira conexão em texto claro. A diretiva includeSubDomains estende a política a todos os subdomínios e preload permite embutir o domínio na lista pré-carregada dos navegadores, protegendo até a primeira visita. Sem HSTS, a janela da primeira requisição HTTP ou de links http permanece explorável por interceptação ativa.

**Detecção:** Inspecionar respostas HTTP com curl -I ou DevTools verificando presença, max-age e includeSubDomains; scanners como Mozilla Observatory, securityheaders.com e testssl.sh reportam ausência ou max-age baixo. Auditar se há redirecionamentos http->https corretos e se recursos são servidos por HTTP. Verificar elegibilidade e inscrição em hstspreload.org.

**Endurecimento:** Definir Strict-Transport-Security com max-age de pelo menos 31536000 (1 ano), incluir includeSubDomains e, quando todos os subdomínios forem HTTPS, adicionar preload e submeter em hstspreload.org. Servir o cabeçalho apenas sobre HTTPS e garantir redirecionamento 301 de http para https. Testar includeSubDomains cuidadosamente para não quebrar subdomínios que dependem de HTTP antes de ativar preload (que é difícil de reverter).

**Referências:**
- https://datatracker.ietf.org/doc/html/rfc6797
- https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Strict_Transport_Security_Cheat_Sheet.html
- https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Strict-Transport-Security
- https://hstspreload.org/
- https://cwe.mitre.org/data/definitions/319.html
- https://owasp.org/Top10/A05_2021-Security_Misconfiguration/

### Segurança de DNS e DNSSEC

**Classificação:** `defensiva`

**O que é:** Conjunto de mecanismos para proteger a resolução de nomes contra falsificação e envenenamento, incluindo assinatura criptográfica das respostas via DNSSEC.

**Como funciona:** O DNS tradicional usa UDP sem autenticação, permitindo spoofing de respostas e envenenamento de cache em que um atacante injeta registros falsos para redirecionar tráfego. DNSSEC adiciona assinaturas (RRSIG) e uma cadeia de confiança (registros DS/DNSKEY) da raiz até a zona, permitindo que resolvers validem a integridade e autenticidade das respostas, embora não forneça confidencialidade. DNS over TLS (DoT) e DNS over HTTPS (DoH) criptografam o transporte entre cliente e resolver, protegendo contra observação e manipulação no caminho. A validação DNSSEC no resolver rejeita respostas com assinatura inválida, mitigando redirecionamentos maliciosos.

**Detecção:** Verificar assinatura e cadeia com dig +dnssec, delv e ferramentas como DNSViz/Verisign DNSSEC Debugger. Monitorar mudanças inesperadas de registros e discrepâncias entre resolvers; alertar sobre falhas de validação DNSSEC (SERVFAIL). Registrar consultas DNS de saída para detectar tunneling e resoluções anômalas.

**Endurecimento:** Assinar zonas autoritativas com DNSSEC e publicar registros DS na zona pai; usar resolvers validadores e algoritmos modernos (ECDSA P-256). Habilitar DoT/DoH para clientes e resolvers, restringir transferências de zona (AXFR) e aplicar rate limiting/response rate limiting nos servidores autoritativos. Usar registros CAA, monitorar integridade dos registros e proteger as credenciais da conta de registro/gestão de DNS com MFA para evitar sequestro de domínio.

**Referências:**
- https://datatracker.ietf.org/doc/html/rfc4033
- https://datatracker.ietf.org/doc/html/rfc9364
- https://csrc.nist.gov/pubs/sp/800/81/r2/upd1/final
- https://cwe.mitre.org/data/definitions/345.html
- https://attack.mitre.org/techniques/T1584/002/
- https://www.cloudflare.com/learning/dns/dns-security/

### Segurança do TLS/HTTPS: versões de protocolo e cipher suites

**Classificação:** `defensiva`

**O que é:** Conjunto de versões de protocolo TLS e cipher suites negociadas no handshake que determinam a força criptográfica da conexão HTTPS.

**Como funciona:** No handshake TLS o cliente envia as versões e cipher suites suportadas e o servidor seleciona uma combinação; versões antigas (SSLv3, TLS 1.0/1.1) e suites fracas (RC4, 3DES, export, cifras sem forward secrecy, MD5/SHA-1) permitem quebra criptográfica ou downgrade. O TLS 1.3 remove renegociação, cifras RSA de troca de chave estática e algoritmos legados, exigindo AEAD (AES-GCM, ChaCha20-Poly1305) e ECDHE, o que garante Perfect Forward Secrecy. Ataques como POODLE, BEAST, SWEET32 e Logjam exploram cifras/versões obsoletas ou parâmetros DH fracos. A ausência de PFS significa que a captura de tráfego mais o comprometimento futuro da chave privada permite decifrar sessões passadas.

**Detecção:** Varredura de configuração com testssl.sh, sslyze, Qualys SSL Labs e nmap --script ssl-enum-ciphers; inventariar endpoints que ainda aceitam TLS 1.0/1.1 ou cifras CBC/RC4/3DES. Monitorar logs do balanceador/servidor para versões negociadas e alertar sobre handshakes em protocolos depreciados. Verificar em pipeline (CI) a configuração do servidor contra baselines Mozilla SSL (perfil 'modern'/'intermediate').

**Endurecimento:** Desabilitar SSLv2/SSLv3/TLS 1.0/1.1; habilitar apenas TLS 1.2 e 1.3 com suites AEAD e ECDHE (forward secrecy). Preferir a ordenação de cifras do servidor no TLS 1.2, usar curvas fortes (X25519, secp256r1), parâmetros DH >= 2048 bits e desabilitar renegociação insegura e compressão TLS (evitar CRIME). Adotar os geradores de configuração Mozilla SSL Config e revisar periodicamente conforme novas depreciações.

**Referências:**
- https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Security_Cheat_Sheet.html
- https://datatracker.ietf.org/doc/html/rfc8446
- https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-52r2.pdf
- https://cwe.mitre.org/data/definitions/327.html
- https://cwe.mitre.org/data/definitions/326.html
- https://ssl-config.mozilla.org/
- https://owasp.org/Top10/A02_2021-Cryptographic_Failures/

### Tomada de subdomínio (Subdomain Takeover)

**Classificação:** `escopo_autorizado`

**O que é:** Assunção do controle de um subdomínio cujo registro DNS aponta para um recurso de terceiros que foi desprovisionado e pode ser reivindicado por outra pessoa.

**Como funciona:** Quando um subdomínio mantém um registro DNS (tipicamente CNAME) apontando para um serviço externo (bucket, plataforma de hosting, CDN) que foi removido ou nunca reivindicado, o registro fica 'pendurado' (dangling). Um terceiro pode então criar um recurso com o mesmo nome no provedor e passar a servir conteúdo sob o subdomínio legítimo da organização. Isso permite phishing convincente, roubo de cookies com Domain amplo, contorno de CSP baseado em domínio e emissão de certificados válidos para o subdomínio. A avaliação envolve identificar registros que resolvem para páginas de erro características de provedores (fingerprints). Só deve ser conduzida sob autorização escrita e regras de engajamento.

**Detecção:** Inventariar continuamente registros DNS (CNAME/A/NS) e checar se apontam para serviços desativados usando ferramentas como subjack, nuclei (templates de takeover) e can-i-take-over-xyz como referência de fingerprints. Monitorar respostas de erro de provedores e emissões de certificado em CT logs para subdomínios. Alertar quando um registro passa a retornar NXDOMAIN no destino ou páginas de 'no such bucket/app'.

**Endurecimento:** Remover registros DNS imediatamente ao desprovisionar qualquer serviço externo (processo de decommission). Manter inventário autoritativo de subdomínios e integrações de terceiros, evitando CNAMEs órfãos. Reivindicar/reservar nomes em provedores antes de publicá-los no DNS e restringir escopo de cookies e CORS para não confiar cegamente em qualquer subdomínio; usar registros CAA para limitar emissão de certificados.

**Referências:**
- https://owasp.org/www-community/attacks/Subdomain_takeover
- https://cheatsheetseries.owasp.org/cheatsheets/Attack_Surface_Analysis_Cheat_Sheet.html
- https://github.com/EdOverflow/can-i-take-over-xyz
- https://cwe.mitre.org/data/definitions/350.html
- https://owasp.org/Top10/A05_2021-Security_Misconfiguration/

## Criptografia Aplicada e Segredos

### Códigos de Autenticação de Mensagem (HMAC / MAC)

**Classificação:** `defensiva`

**O que é:** Mecanismo que combina uma chave secreta com uma função de hash (HMAC) para garantir integridade e autenticidade de mensagens entre partes que compartilham a chave.

**Como funciona:** HMAC processa a mensagem com uma chave secreta em duas passagens de hash (padrões ipad/opad), produzindo uma tag que só quem possui a chave consegue gerar ou verificar, garantindo que a mensagem não foi alterada e veio de parte autorizada. Diferente de um hash simples, um MAC depende de segredo, o que impede um atacante sem a chave de forjar a tag mesmo alterando o conteúdo. É amplamente usado em assinatura de webhooks, tokens JWT HS256, cookies assinados e verificação de integridade em protocolos. A verificação DEVE usar comparação em tempo constante para não vazar informação por timing, e a chave deve ter entropia suficiente e ser separada de chaves de cifragem.

**Detecção:** Revise verificações de MAC que usam == comum (vulnerável a timing) em vez de hmac.compare_digest / crypto.timingSafeEqual; procure verificação de assinatura de webhook ausente ou opcional. Sinalize JWT com algoritmo none aceito ou confusão de algoritmo (HS256 vs RS256). Em logs, monitore falhas de verificação de assinatura e reprocessamento. Ferramentas: SAST, revisão de integrações de webhook, testes de fuzzing de assinatura.

**Endurecimento:** Use HMAC-SHA-256 (ou SHA-512) com chave aleatória forte e dedicada; compare tags em tempo constante. Para webhooks, exija assinatura e inclua timestamp/nonce contra replay. Para JWT, fixe o algoritmo esperado no verificador e rejeite alg none e troca de algoritmo. Rotacione chaves de MAC e mantenha-as em KMS/segredos, nunca no código. Considere MAC autenticado embutido em AEAD (AES-GCM, ChaCha20-Poly1305) quando também houver cifragem.

**Referências:**
- RFC 2104 HMAC — https://www.rfc-editor.org/rfc/rfc2104
- NIST FIPS 198-1 The Keyed-Hash Message Authentication Code — https://csrc.nist.gov/pubs/fips/198-1/final
- CWE-347: Improper Verification of Cryptographic Signature — https://cwe.mitre.org/data/definitions/347.html
- OWASP JWT / JSON Web Token Cheat Sheet — https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html
- RFC 7518 JSON Web Algorithms — https://www.rfc-editor.org/rfc/rfc7518

### Criptografia Assimétrica (RSA e Criptografia de Curvas Elípticas / ECC)

**Classificação:** `defensiva`

**O que é:** Esquema com par de chaves pública/privada usado para cifragem, assinatura digital e troca de chaves, com RSA e curvas elípticas (Ed25519, ECDSA) como principais famílias.

**Como funciona:** Na criptografia assimétrica a chave pública e a privada são matematicamente relacionadas, mas derivar a privada da pública é inviável (fatoração de inteiros para RSA; logaritmo discreto em curvas para ECC). A chave pública cifra ou verifica assinaturas e a privada decifra ou assina, permitindo confidencialidade e autenticidade sem segredo compartilhado prévio. ECC oferece a mesma segurança que RSA com chaves muito menores (uma curva de 256 bits ~ RSA de 3072 bits), sendo mais eficiente. O padding importa: RSA deve usar OAEP para cifragem e PSS para assinatura — PKCS#1 v1.5 tem fragilidades históricas (Bleichenbacher). Na prática, criptografia assimétrica cifra apenas chaves simétricas ou pequenos dados; volumes grandes usam cifragem híbrida.

**Detecção:** Sinalize chaves RSA < 2048 bits, curvas não padronizadas ou fracas, uso de PKCS#1 v1.5 para novas cifragens, e ECDSA com nonce não aleatório. Procure chaves privadas commitadas no repositório, permissões frouxas em arquivos .pem/.key, e reuso de chaves entre ambientes. Ferramentas: testssl.sh, sslyze, scanners de segredo (gitleaks, trufflehog), SAST de cripto.

**Endurecimento:** Use RSA >=2048 (preferir 3072/4096) com OAEP (cifragem) e PSS (assinatura), ou ECC com curvas aprovadas (P-256/P-384, Ed25519, X25519). Gere chaves via CSPRNG em HSM/KMS quando possível e proteja a chave privada com controle de acesso e cifragem em repouso. Adote cifragem híbrida (assimétrica só para a chave de sessão). Planeje agilidade e transição para criptografia pós-quântica (ML-KEM/ML-DSA) em dados de longa validade. Rotacione e revogue chaves comprometidas.

**Referências:**
- NIST SP 800-56B Rev.2 RSA Key Establishment — https://csrc.nist.gov/pubs/sp/800/56/b/r2/final
- NIST FIPS 186-5 Digital Signature Standard — https://csrc.nist.gov/pubs/fips/186-5/final
- NIST SP 800-57 Part 1 Rev.5 Key Management — https://csrc.nist.gov/pubs/sp/800/57/pt1/r5/final
- RFC 8017 PKCS#1 v2.2 (RSA OAEP/PSS) — https://www.rfc-editor.org/rfc/rfc8017
- RFC 8032 EdDSA (Ed25519) — https://www.rfc-editor.org/rfc/rfc8032
- CWE-327: Use of a Broken or Risky Cryptographic Algorithm — https://cwe.mitre.org/data/definitions/327.html

### Criptografia em Repouso (Encryption at Rest)

**Classificação:** `defensiva`

**O que é:** Proteção de dados armazenados (bancos, discos, backups, objetos) por cifragem, limitando exposição em caso de acesso físico ou vazamento de armazenamento.

**Como funciona:** A cifragem em repouso pode ocorrer em camadas: disco/volume (LUKS, cifragem de disco da nuvem), banco de dados (TDE — Transparent Data Encryption), ou aplicação/campo (cifrar campos sensíveis antes de persistir). Cifragem de disco protege contra roubo físico mas não contra um app comprometido que já tem acesso lógico; cifragem em nível de aplicação/campo protege dados específicos mesmo de quem acessa o banco, ao custo de complexidade e impacto em busca/índice. Normalmente usa-se AES-256-GCM com cifragem por envelope: DEKs cifram dados e são protegidas por uma KEK em KMS/HSM, viabilizando rotação sem recifrar tudo. Backups e réplicas também precisam ser cifrados e as chaves separadas dos dados.

**Detecção:** Verifique se volumes, buckets e bancos têm cifragem habilitada (CSPM/Config rules); confira se backups e snapshots são cifrados. Revise se dados altamente sensíveis (PII, cartões, saúde) têm proteção em nível de campo além do disco. Detecte chaves armazenadas junto aos dados. Ferramentas: CSPM (Prowler, ScoutSuite), auditoria de KMS, revisão de esquema/migrations.

**Endurecimento:** Cifre discos/volumes e bancos (TDE) e adicione cifragem em nível de aplicação/campo para os dados mais sensíveis, usando AES-256-GCM. Gerencie chaves em KMS/HSM com envelope encryption, separando KEK dos dados e habilitando rotação. Cifre backups, snapshots e réplicas; controle acesso por least privilege e audite. Considere tokenização/pseudonimização para reduzir superfície. Combine com cifragem em trânsito e minimização de dados. Teste restauração de backups cifrados.

**Referências:**
- OWASP Cryptographic Storage Cheat Sheet — https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html
- CWE-311: Missing Encryption of Sensitive Data — https://cwe.mitre.org/data/definitions/311.html
- CWE-312: Cleartext Storage of Sensitive Information — https://cwe.mitre.org/data/definitions/312.html
- NIST SP 800-111 Guide to Storage Encryption Technologies — https://csrc.nist.gov/pubs/sp/800/111/final
- NIST SP 800-57 Part 1 Rev.5 Key Management — https://csrc.nist.gov/pubs/sp/800/57/pt1/r5/final
- PCI DSS v4.0 Requirement 3 (Protect Stored Account Data) — https://www.pcisecuritystandards.org/

### Criptografia em Trânsito (Encryption in Transit / TLS)

**Classificação:** `defensiva`

**O que é:** Proteção de dados enquanto trafegam pela rede usando TLS moderno, evitando interceptação, adulteração e downgrade.

**Como funciona:** O TLS estabelece um canal autenticado e cifrado: as partes negociam versão e suite, autenticam via certificado, derivam chaves de sessão por troca efêmera e então cifram os dados com AEAD, garantindo confidencialidade e integridade em trânsito. Sem TLS (ou com TLS mal configurado) um atacante na rede pode ler ou alterar dados, ou forçar downgrade para protocolos/cifras fracas. HSTS instrui o navegador a só usar HTTPS, mitigando SSL stripping; mTLS adiciona autenticação do cliente para serviços internos. A segurança depende de versões atuais (TLS 1.2+/1.3), cifras fortes, forward secrecy e validação correta de certificados nas duas pontas.

**Detecção:** Scanners de TLS (testssl.sh, sslyze, SSL Labs) para versões/cifras obsoletas, ausência de forward secrecy, certificados inválidos e falta de HSTS. Procure endpoints HTTP, misturas HTTP/HTTPS (mixed content), redirecionamentos ausentes, e clientes com validação desabilitada. Monitore em rede tráfego não cifrado para portas sensíveis. Ferramentas: DAST/ZAP, CSPM, inspeção de config de LB/ingress.

**Endurecimento:** Force TLS 1.2+/1.3 com cifras AEAD e ECDHE (forward secrecy); desative SSLv3/TLS 1.0/1.1 e cifras fracas. Redirecione todo HTTP para HTTPS e habilite HSTS (com preload quando apropriado). Valide certificados corretamente em clientes (sem skip verify), use OCSP stapling e considere mTLS para tráfego serviço-a-serviço. Automatize renovação de certificados e siga o perfil intermediário/moderno da Mozilla. Cifre também tráfego interno (leste-oeste).

**Referências:**
- RFC 8446 TLS 1.3 — https://www.rfc-editor.org/rfc/rfc8446
- OWASP Transport Layer Security Cheat Sheet — https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Security_Cheat_Sheet.html
- CWE-319: Cleartext Transmission of Sensitive Information — https://cwe.mitre.org/data/definitions/319.html
- NIST SP 800-52 Rev.2 Guidelines for TLS — https://csrc.nist.gov/pubs/sp/800/52/r2/final
- Mozilla TLS Configuration Guidelines — https://wiki.mozilla.org/Security/Server_Side_TLS
- OWASP HTTP Strict Transport Security Cheat Sheet — https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Strict_Transport_Security_Cheat_Sheet.html

### Criptografia Simétrica Autenticada: AES-GCM vs Modos Inseguros (AES-GCM vs ECB)

**Classificação:** `defensiva`

**O que é:** Cifragem com chave única compartilhada; modos AEAD como AES-GCM/ChaCha20-Poly1305 provêm confidencialidade e autenticidade, enquanto ECB e CBC sem MAC são inseguros.

**Como funciona:** Cifras de bloco como AES operam em blocos de tamanho fixo e precisam de um modo de operação para cifrar dados maiores. O modo ECB cifra cada bloco independentemente, então blocos de texto claro idênticos geram blocos cifrados idênticos, vazando padrões estruturais (o clássico exemplo da imagem do pinguim ainda visível). Modos AEAD (AES-GCM, AES-CCM, ChaCha20-Poly1305) combinam confidencialidade e uma tag de autenticação que detecta adulteração, sendo a recomendação atual; eles exigem um nonce/IV único por operação sob a mesma chave — reuso de nonce em GCM é catastrófico e permite recuperar a chave de autenticação. CBC provê confidencialidade mas não integridade, exigindo MAC separado (encrypt-then-MAC) e é sujeito a padding oracle se malformado.

**Detecção:** SAST para Cipher.getInstance("AES") sem modo (default ECB em Java), AES/ECB, ou IV estático/nulo; procure IV derivado de contador previsível ou reuso. Analise dados cifrados em repouso: padrões repetidos indicam ECB. Verifique ausência de verificação de tag de autenticação. Ferramentas: CodeQL/Semgrep com regras de cripto, revisão de KMS, inspeção de blobs cifrados.

**Endurecimento:** Prefira AEAD: AES-256-GCM ou ChaCha20-Poly1305; gere nonce único por mensagem via CSPRNG (ou contador estritamente monotônico controlado) e NUNCA reutilize nonce+chave. Bane ECB. Use bibliotecas de alto nível que dificultam erro (libsodium, Tink, AWS Encryption SDK) em vez de montar primitivas manualmente. Sempre verifique a tag antes de usar o texto decifrado. Rotacione chaves e limite o volume cifrado por chave conforme limites do modo.

**Referências:**
- OWASP Cryptographic Storage Cheat Sheet — https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html
- NIST SP 800-38D GCM — https://csrc.nist.gov/pubs/sp/800/38/d/final
- NIST SP 800-38A Block Cipher Modes — https://csrc.nist.gov/pubs/sp/800/38/a/final
- CWE-327: Use of a Broken or Risky Cryptographic Algorithm — https://cwe.mitre.org/data/definitions/327.html
- RFC 8439 ChaCha20-Poly1305 — https://www.rfc-editor.org/rfc/rfc8439
- Google Tink — https://developers.google.com/tink

### Falhas Criptográficas (OWASP A02:2021 Cryptographic Failures)

**Classificação:** `defensiva`

**O que é:** Categoria guarda-chuva do OWASP Top 10 que agrupa proteção inadequada de dados sensíveis por cifragem ausente, fraca ou mal aplicada, em repouso e em trânsito.

**Como funciona:** A falha decorre de não classificar corretamente dados sensíveis e, então, não os proteger: transmitir em texto claro (HTTP, protocolos sem TLS), armazenar sem cifragem, ou usar algoritmos/modos/parâmetros fracos ou obsoletos. Também inclui gestão deficiente de chaves (chaves hardcoded, reuso, ausência de rotação), IV/nonce previsíveis, verificação de certificado desabilitada e uso de hash simples para senhas. O efeito é exposição de dados (PII, credenciais, financeiro, saúde) a interceptação ou vazamento de banco. O foco defensivo é decidir o que precisa de proteção, aplicar primitivas fortes corretamente e proteger o material de chave — muitas subfalhas específicas têm entradas próprias nesta base.

**Detecção:** Inventário e classificação de dados; varredura por HTTP sem TLS, TLS obsoleto (SSLv3/TLS 1.0/1.1), cifras fracas, cabeçalhos sem HSTS. SAST/SCA por algoritmos quebrados, chaves hardcoded, IV estático, verificação desabilitada. DAST e inspeção de tráfego. Ferramentas: testssl.sh, sslyze, gitleaks, CodeQL/Semgrep, ZAP, scanners de config.

**Endurecimento:** Classifique dados e aplique cifragem forte em repouso (AES-256-GCM) e em trânsito (TLS 1.2+/1.3, HSTS); minimize e descarte dados sensíveis que não precisa reter. Use primitivas AEAD e KDFs corretos, CSPRNG para IV/nonce/sais, e KMS/HSM para chaves com rotação. Desabilite protocolos/cifras legados, force HTTPS e valide certificados. Adote agilidade criptográfica e revisão de cripto no SDLC. Nunca registre dados sensíveis em logs.

**Referências:**
- OWASP Top 10 2021 A02:2021 Cryptographic Failures — https://owasp.org/Top10/A02_2021-Cryptographic_Failures/
- CWE-311: Missing Encryption of Sensitive Data — https://cwe.mitre.org/data/definitions/311.html
- CWE-319: Cleartext Transmission of Sensitive Information — https://cwe.mitre.org/data/definitions/319.html
- CWE-326: Inadequate Encryption Strength — https://cwe.mitre.org/data/definitions/326.html
- OWASP Cryptographic Storage Cheat Sheet — https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html
- NIST SP 800-175B Rev.1 Guideline for Using Cryptographic Standards — https://csrc.nist.gov/pubs/sp/800/175/b/r1/final

### Funções de Hash Criptográfico e Integridade (Cryptographic Hash Functions)

**Classificação:** `defensiva`

**O que é:** Funções que mapeiam dados de tamanho arbitrário para um valor de comprimento fixo (digest), usadas para verificar integridade e como primitiva em assinaturas, HMAC e derivação de chaves.

**Como funciona:** Uma função de hash criptográfica deve oferecer resistência a pré-imagem, segunda pré-imagem e colisão, de modo que seja inviável achar entradas distintas com o mesmo digest ou reverter o digest para a entrada. MD5 e SHA-1 estão quebrados quanto à resistência a colisão (ataques de colisão práticos como SHAttered contra SHA-1), o que os torna inseguros para assinaturas e certificados. Para integridade e assinaturas use SHA-256/SHA-512 (SHA-2), SHA-3 ou BLAKE2/BLAKE3. É crucial entender que hash simples NÃO é adequado para armazenar senhas, pois é rápido e sem sal — para senhas usa-se funções de derivação de chave dedicadas (ver entrada de hashing de senha).

**Detecção:** Faça varredura estática (Semgrep, CodeQL) por chamadas a MD5/SHA-1 em contextos de assinatura, TLS ou verificação de integridade; inspecione dependências e formatos de certificado com algoritmo de assinatura fraco (sha1WithRSAEncryption). Em código, procure MessageDigest.getInstance("MD5"), hashlib.md5, crypto.createHash('sha1'). Em logs de TLS/PKI, sinalize certificados ou artefatos assinados com SHA-1. Ferramentas: testssl.sh, sslyze, linters de cripto, SCA.

**Endurecimento:** Padronize SHA-256 ou superior (SHA-2/SHA-3/BLAKE2) para integridade e assinaturas; bane MD5 e SHA-1 via política e regras de lint que falham o build. Para comparação de digests sensíveis (tokens, MACs) use comparação de tempo constante. Não use hash puro para senhas nem para pseudonimização de dados de baixa entropia (é reversível por força bruta/dicionário). Prefira HMAC quando precisar de integridade com chave. Mantenha agilidade criptográfica para migrar algoritmos.

**Referências:**
- OWASP Top 10 2021 A02:2021 Cryptographic Failures — https://owasp.org/Top10/A02_2021-Cryptographic_Failures/
- CWE-327: Use of a Broken or Risky Cryptographic Algorithm — https://cwe.mitre.org/data/definitions/327.html
- CWE-328: Use of Weak Hash — https://cwe.mitre.org/data/definitions/328.html
- NIST FIPS 180-4 Secure Hash Standard — https://csrc.nist.gov/pubs/fips/180-4/final
- NIST FIPS 202 SHA-3 Standard — https://csrc.nist.gov/pubs/fips/202/final
- NIST SP 800-131A Rev.2 Transitions — https://csrc.nist.gov/pubs/sp/800/131/a/r2/final

### Geração Segura de Aleatoriedade (CSPRNG)

**Classificação:** `defensiva`

**O que é:** Uso de geradores pseudoaleatórios criptograficamente seguros (CSPRNG) para produzir chaves, tokens, sais, nonces e IVs imprevisíveis.

**Como funciona:** Um CSPRNG é semeado por fontes de entropia do sistema operacional e produz saídas das quais é inviável prever valores futuros ou reconstruir estado interno, ao contrário de PRNGs estatísticos (Math.random, rand(), Mersenne Twister) que são previsíveis e reversíveis a partir de poucas saídas. Segredos gerados com PRNG fraco — tokens de sessão, reset de senha, chaves, nonces — podem ser antecipados por um atacante, comprometendo autenticação e cifragem. A qualidade depende de entropia suficiente na inicialização; ambientes recém-criados (VMs, contêineres, embarcados no boot) podem ter entropia baixa. Deve-se sempre usar a API criptográfica dedicada da plataforma.

**Detecção:** SAST para Math.random(), java.util.Random, rand()/srand(), mt_rand() usados em contexto de segurança; sinalize sementes fixas ou baseadas em tempo. Verifique tokens curtos ou com padrão observável, colisões de nonce, e IDs sequenciais em fluxos sensíveis. Ferramentas: CodeQL/Semgrep, análise de entropia de tokens, testes estatísticos, revisão de bibliotecas.

**Endurecimento:** Use CSPRNG da plataforma: crypto.randomBytes / crypto.getRandomValues (Node/Web), secrets (Python), java.security.SecureRandom, getrandom(2)/urandom. Gere tokens com >=128 bits de entropia. Garanta entropia adequada no boot de VMs/contêineres (virtio-rng, semear o pool). Nunca semeie CSPRNG manualmente com valores previsíveis. Centralize geração de segredos em utilitários revisados e proíba PRNGs estatísticos para fins de segurança via lint.

**Referências:**
- CWE-330: Use of Insufficiently Random Values — https://cwe.mitre.org/data/definitions/330.html
- CWE-338: Use of Cryptographically Weak PRNG — https://cwe.mitre.org/data/definitions/338.html
- NIST SP 800-90A Rev.1 Deterministic RBGs — https://csrc.nist.gov/pubs/sp/800/90/a/r1/final
- NIST SP 800-90B Entropy Sources — https://csrc.nist.gov/pubs/sp/800/90/b/final
- OWASP Cryptographic Storage Cheat Sheet — https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html

### Gestão de Chaves com KMS e HSM (Key Management / KMS / HSM)

**Classificação:** `defensiva`

**O que é:** Disciplina e infraestrutura (KMS/HSM) para gerar, armazenar, distribuir, rotacionar e destruir chaves criptográficas com controle de acesso e auditoria.

**Como funciona:** Um KMS centraliza o ciclo de vida das chaves e normalmente aplica cifragem por envelope: uma chave de dados (DEK) cifra os dados e é ela mesma cifrada por uma chave mestra (KEK) que nunca deixa o KMS/HSM, reduzindo exposição do material sensível. Um HSM é um módulo de hardware resistente a violação que gera e usa chaves sem exportar a chave privada, oferecendo operações criptográficas dentro de uma fronteira certificada (FIPS 140-2/3). A hierarquia de chaves, o controle de acesso baseado em identidade e a auditoria de cada operação permitem rotação, revogação e separação de funções sem reprocessar dados massivamente (rotaciona-se a KEK e recifra-se apenas as DEKs). Chaves embutidas em código ou config são o antipadrão que essa disciplina elimina.

**Detecção:** Scanners de segredo (gitleaks, trufflehog, detect-secrets) para chaves hardcoded; revise IAM/políticas do KMS por acesso excessivo e ausência de separação entre quem administra e quem usa chaves. Verifique logs do KMS (ex.: CloudTrail) para uso anômalo de Decrypt/GenerateDataKey. Confirme rotação habilitada e idade das chaves. Ferramentas: CSPM, revisão de políticas, auditoria de KMS.

**Endurecimento:** Guarde chaves mestras em KMS/HSM (FIPS 140-2/3), nunca em código ou variáveis simples; use envelope encryption com DEKs por objeto/tenant. Aplique least privilege e separação de funções nas políticas, com grants temporários e condições. Habilite rotação automática de KEK e logging/auditoria de todas as operações. Restrinja exportação de chaves e prefira operações dentro do HSM. Tenha procedimentos de revogação e recuperação (key ceremony, backup seguro de KEK).

**Referências:**
- NIST SP 800-57 Part 1 Rev.5 Key Management — https://csrc.nist.gov/pubs/sp/800/57/pt1/r5/final
- NIST SP 800-130 Framework for Key Management Systems — https://csrc.nist.gov/pubs/sp/800/130/final
- NIST FIPS 140-3 Security Requirements for Cryptographic Modules — https://csrc.nist.gov/pubs/fips/140-3/final
- CWE-798: Use of Hard-coded Credentials — https://cwe.mitre.org/data/definitions/798.html
- CWE-321: Use of Hard-coded Cryptographic Key — https://cwe.mitre.org/data/definitions/321.html
- OWASP Cryptographic Storage Cheat Sheet — https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html

### Gestão de Segredos e Vault (Secrets Management)

**Classificação:** `defensiva`

**O que é:** Práticas e ferramentas (Vault, cofres de nuvem) para armazenar, distribuir, rotacionar e auditar segredos de aplicação sem expô-los em código ou configuração.

**Como funciona:** Um cofre de segredos centraliza credenciais, chaves de API, tokens e strings de conexão, entregando-os às aplicações em tempo de execução via identidade autenticada em vez de arquivos estáticos, com cifragem em repouso e auditoria de acesso. Recursos avançados incluem segredos dinâmicos de vida curta (ex.: credenciais de banco geradas sob demanda e revogadas após TTL), reduzindo a janela de exposição e o esforço de rotação. O antipadrão combatido é o secret sprawl: segredos espalhados em código, .env commitados, imagens de contêiner, variáveis de CI e logs, que vazam e persistem no histórico do Git. O acesso é governado por least privilege, leasing e trilhas de auditoria.

**Detecção:** Scanners de segredo no repositório e histórico (gitleaks, trufflehog, detect-secrets) e no CI/CD; hooks de pré-commit. Verifique .env versionado, segredos em Dockerfile/args, em logs e em variáveis de ambiente expostas. Audite acessos ao cofre e detecte credenciais de longa vida. Ferramentas: GitHub secret scanning, CSPM, revisão de pipelines.

**Endurecimento:** Nunca hardcode segredos; use um cofre (HashiCorp Vault, cloud secret managers) com acesso por identidade e least privilege. Prefira segredos dinâmicos de curta duração e rotação automática; defina TTL e revogação. Injete segredos em runtime (não no build), mantenha-os fora de logs e imagens, e adote pré-commit + secret scanning no CI. Rotacione imediatamente qualquer segredo vazado e purgue do histórico. Segregue segredos por ambiente e aplique cifragem em repouso e auditoria.

**Referências:**
- OWASP Secrets Management Cheat Sheet — https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html
- CWE-798: Use of Hard-coded Credentials — https://cwe.mitre.org/data/definitions/798.html
- CWE-522: Insufficiently Protected Credentials — https://cwe.mitre.org/data/definitions/522.html
- OWASP Top 10 2021 A05:2021 Security Misconfiguration — https://owasp.org/Top10/A05_2021-Security_Misconfiguration/
- NIST SP 800-57 Part 1 Rev.5 Key Management — https://csrc.nist.gov/pubs/sp/800/57/pt1/r5/final
- The Twelve-Factor App: Config — https://12factor.net/config

### Hashing de Senha e Derivação de Chave (Password Hashing / KDF)

**Classificação:** `defensiva`

**O que é:** Técnica de armazenar senhas como digests de funções lentas, salgadas e com custo ajustável (Argon2, scrypt, bcrypt, PBKDF2) para resistir a força bruta offline.

**Como funciona:** Ao contrário de hashes rápidos, uma função de hashing de senha aplica um fator de trabalho (iterações, memória e paralelismo) que torna cada tentativa cara, encarecendo ataques offline após vazamento do banco. Um sal único e aleatório por usuário impede rainbow tables e evita que senhas iguais gerem o mesmo digest; um pepper (segredo global guardado fora do banco, ex.: em KMS) adiciona defesa se apenas o banco vazar. Argon2id é o padrão atual recomendado por resistir a ataques com GPU/ASIC via custo de memória; bcrypt e scrypt são alternativas aceitáveis e PBKDF2 é usado quando exige-se conformidade FIPS. O parâmetro de custo deve ser recalibrado periodicamente conforme o hardware evolui, e o rehash pode ocorrer no login quando o fator estiver defasado.

**Detecção:** Procure no código por armazenamento de senha via SHA/MD5 puro, ausência de sal, sal fixo/global ou fator de custo baixo; em Argon2/bcrypt verifique parâmetros. Sinais de incidente: picos de tentativas de login (credential stuffing), muitos resets, uso de listas de senhas vazadas. Ferramentas: revisão estática, testes de configuração, comparação com OWASP Password Storage Cheat Sheet; monitore autenticação em SIEM.

**Endurecimento:** Use Argon2id (parâmetros de referência OWASP, ex.: memória de 19 MiB+, iterações e paralelismo calibrados para ~500ms–1s no seu hardware) ou bcrypt (cost >=10-12), scrypt, ou PBKDF2-HMAC-SHA256 com iterações altas quando exigido FIPS. Sal aleatório por usuário via CSPRNG; considere pepper em KMS/HSM. Faça rehash transparente no login ao detectar parâmetros fracos. Combine com MFA, bloqueio/rate limiting e detecção de credential stuffing. Nunca registre senhas em logs.

**Referências:**
- OWASP Password Storage Cheat Sheet — https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html
- OWASP Top 10 2021 A07:2021 Identification and Authentication Failures — https://owasp.org/Top10/A07_2021-Identification_and_Authentication_Failures/
- CWE-916: Use of Password Hash With Insufficient Computational Effort — https://cwe.mitre.org/data/definitions/916.html
- CWE-759: Use of a One-Way Hash without a Salt — https://cwe.mitre.org/data/definitions/759.html
- NIST SP 800-63B Digital Identity Guidelines — https://pages.nist.gov/800-63-3/sp800-63b.html
- RFC 9106 Argon2 — https://www.rfc-editor.org/rfc/rfc9106
- OWASP ASVS v4 V2 Authentication — https://owasp.org/www-project-application-security-verification-standard/

### Padding Oracle e Reuso de IV/Nonce (Padding Oracle & IV/Nonce Reuse)

**Classificação:** `laboratorio_autorizado`

**O que é:** Classes de falha em cifragem simétrica: oráculos de padding em CBC sem MAC e reuso de IV/nonce, que quebram confidencialidade e integridade.

**Como funciona:** Um padding oracle ocorre quando um sistema em CBC revela, por mensagens de erro, tempo ou comportamento, se o preenchimento (padding) de um texto decifrado é válido; essa distinção observável, de forma conceitual, permite recuperar o texto claro byte a byte sem conhecer a chave, porque CBC é maleável e não autenticado. O reuso de IV em CBC vaza igualdade de prefixos entre mensagens; já o reuso de nonce em AES-GCM é catastrófico: com dois textos cifrados sob o mesmo nonce e chave é possível recuperar o keystream e, pior, a subchave de autenticação, permitindo forjar tags. A raiz comum é cifrar sem autenticação adequada e/ou gerenciar mal IV/nonce. Este item é laboratorial: valide apenas em sistemas próprios para entender o mecanismo e corrigir.

**Detecção:** Revise código por CBC sem MAC (falta de encrypt-then-MAC), erros distintos para padding vs autenticação, e diferenças de timing na verificação. Procure IV/nonce constante, derivado de contador reiniciável, ou reutilizado entre mensagens. Em GCM, sinalize geração de nonce sem CSPRNG ou sem garantia de unicidade. Ferramentas: SAST de cripto, revisão manual, testes em laboratório controlado, análise de blobs cifrados.

**Endurecimento:** Use AEAD (AES-GCM, ChaCha20-Poly1305) e sempre verifique a tag antes de processar; se usar CBC, aplique encrypt-then-MAC com HMAC e comparação em tempo constante. Garanta IV/nonce único por operação via CSPRNG ou contador estritamente monotônico controlado; nunca reutilize nonce+chave e respeite limites de volume por chave. Retorne erros genéricos e uniformes (sem distinguir padding de autenticação). Prefira bibliotecas de alto nível (libsodium, Tink) que evitam esses erros por construção.

**Referências:**
- CWE-329: Generation of Predictable IV with CBC Mode — https://cwe.mitre.org/data/definitions/329.html
- CWE-323: Reusing a Nonce, Key Pair in Encryption — https://cwe.mitre.org/data/definitions/323.html
- NIST SP 800-38D GCM (uniqueness of IV) — https://csrc.nist.gov/pubs/sp/800/38/d/final
- OWASP Cryptographic Storage Cheat Sheet — https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html
- NIST SP 800-38A Block Cipher Modes — https://csrc.nist.gov/pubs/sp/800/38/a/final

### PKI, Certificados e Rotação (Public Key Infrastructure / Certificate Management)

**Classificação:** `defensiva`

**O que é:** Infraestrutura de chaves públicas que emite, valida, revoga e renova certificados X.509 estabelecendo cadeias de confiança para TLS, assinatura de código e mTLS.

**Como funciona:** Uma Autoridade Certificadora (CA) assina certificados que vinculam uma identidade a uma chave pública; clientes confiam nesse vínculo verificando a cadeia até uma CA raiz confiável, junto com validade, uso da chave e nome (hostname). A validação inclui checar expiração e status de revogação via CRL ou OCSP, pois chaves comprometidas precisam ser invalidadas antes do vencimento. Certificados têm ciclo de vida curto e finito, o que exige rotação/renovação automatizada (ACME) para evitar interrupções e reduzir janela de exposição. Falhas comuns são não validar a cadeia, aceitar certificados autoassinados, ignorar hostname ou revogação, e não rotacionar chaves de CA/intermediárias.

**Detecção:** Monitore expiração de certificados (alertas com antecedência), inventário via CT logs, e verifique se clientes validam cadeia/hostname/revogação (procure verify=false, InsecureSkipVerify, TrustAllCerts). Sinalize CAs internas com chave frágil e certificados com SHA-1. Ferramentas: testssl.sh, sslyze, crt.sh/CT monitoring, scanners de config TLS, gerenciadores de certificado (cert-manager).

**Endurecimento:** Automatize emissão e rotação (ACME/cert-manager) com validade curta; nunca desabilite validação de cadeia, hostname ou revogação em produção. Proteja chaves de CA em HSM e limite CAs intermediárias. Use OCSP stapling e monitore CT logs para emissões não autorizadas. Considere mTLS e, com cautela, pinning para conexões críticas com plano de rotação. Mantenha inventário e alarme de expiração; tenha processo de revogação rápida em incidente.

**Referências:**
- RFC 5280 X.509 PKI Certificate and CRL Profile — https://www.rfc-editor.org/rfc/rfc5280
- RFC 8555 ACME — https://www.rfc-editor.org/rfc/rfc8555
- CWE-295: Improper Certificate Validation — https://cwe.mitre.org/data/definitions/295.html
- NIST SP 800-57 Part 1 Rev.5 Key Management — https://csrc.nist.gov/pubs/sp/800/57/pt1/r5/final
- OWASP Transport Layer Security Cheat Sheet — https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Security_Cheat_Sheet.html
- CA/Browser Forum Baseline Requirements — https://cabforum.org/baseline-requirements-documents/

### Segredos Embutidos em Código e Histórico (Hardcoded Secrets / Secret Sprawl)

**Classificação:** `defensiva`

**O que é:** Credenciais, chaves de API e tokens escritos diretamente no código-fonte ou em arquivos de configuração versionados vazam com facilidade — em repositórios, histórico do Git, imagens de contêiner e logs de build — e permanecem válidos até serem revogados. A varredura de segredos e a externalização de credenciais mitigam o risco.

**Como funciona:** Um segredo comprometido concede acesso direto ao recurso que protege, sem necessidade de explorar outra falha. Quando embutido no código, ele se propaga por clones, forks, backups e, sobretudo, pelo histórico do Git: mesmo removido do estado atual, continua recuperável em commits anteriores até que o segredo seja de fato rotacionado. O mesmo ocorre com arquivos de configuração e variáveis embutidas em imagens de contêiner. A causa raiz é tratar segredos como parte do código em vez de configuração externa gerenciada. A defesa combina prevenção (não commitar segredos, varredura antes do push), detecção (scanning contínuo de repositórios e histórico) e resposta (revogar e rotacionar imediatamente qualquer segredo exposto, pois removê-lo do código não o invalida).

**Detecção:** Habilite varredura de segredos em repositórios, pull requests e no histórico completo, além de proteção de push que bloqueia commits com padrões de credenciais. Verifique imagens de contêiner e artefatos de build por segredos embutidos. Monitore uso anômalo de credenciais que possam ter vazado. Trate qualquer correspondência confirmada como incidente que exige rotação, não apenas remoção.

**Endurecimento:** Externalize segredos para um gerenciador dedicado (cofre/secret manager) e injete-os em tempo de execução; nunca versione credenciais. Adicione varredura de segredos e push protection na esteira e nos hooks locais. Use credenciais de curta duração e rotação automática sempre que possível. Ao detectar exposição, revogue e rotacione imediatamente o segredo — assumir que ele foi comprometido — e só então limpe o histórico. Restrinja o escopo e os privilégios de cada credencial para limitar o impacto de um vazamento.

**Referências:**
- OWASP Cheat Sheet Series: Secrets Management
- CWE-798: Use of Hard-coded Credentials
- CWE-540: Inclusion of Sensitive Information in Source Code
- NIST SP 800-57: Recommendation for Key Management

### Troca de Chaves e Sigilo Encaminhado (Key Exchange / Forward Secrecy)

**Classificação:** `defensiva`

**O que é:** Protocolos como (EC)DHE que permitem duas partes derivarem uma chave de sessão compartilhada sobre canal público, garantindo sigilo encaminhado quando efêmeros.

**Como funciona:** No Diffie-Hellman cada parte gera um par efêmero e troca apenas os valores públicos; combinando o próprio segredo privado com o público do outro, ambas derivam o mesmo segredo compartilhado sem transmiti-lo. O sigilo encaminhado (forward secrecy) vem do uso de chaves efêmeras (ECDHE/DHE) descartadas após a sessão: mesmo que a chave privada de longo prazo do servidor vaze no futuro, sessões passadas capturadas não podem ser decifradas. TLS 1.3 torna a troca efêmera obrigatória e remove trocas estáticas RSA que não davam forward secrecy. A autenticidade das partes ainda depende de assinaturas/certificados para evitar man-in-the-middle no canal de troca.

**Detecção:** Verifique se o TLS negocia suites com ECDHE/DHE e se cifras estáticas RSA estão desabilitadas; TLS 1.3 já garante FS. Sinalize parâmetros DH fracos (grupos < 2048 bits, grupos customizados), reuso de chave efêmera entre muitas conexões e ausência de FS. Ferramentas: testssl.sh, sslyze, SSL Labs, análise de configuração de servidores e balanceadores.

**Endurecimento:** Habilite TLS 1.3 e, em TLS 1.2, restrinja a suites ECDHE com curvas fortes (X25519, P-256); desative troca RSA estática e grupos DH fracos. Use parâmetros/grupos nomeados padronizados. Gere chaves efêmeras por handshake e não as reutilize excessivamente. Considere suites híbridas pós-quânticas (ex.: X25519+ML-KEM) para proteção contra colheita agora, decifragem depois em dados sensíveis de longa vida. Mantenha bibliotecas TLS atualizadas.

**Referências:**
- RFC 8446 TLS 1.3 — https://www.rfc-editor.org/rfc/rfc8446
- RFC 7919 Negotiated FFDHE Parameters — https://www.rfc-editor.org/rfc/rfc7919
- NIST SP 800-56A Rev.3 Key Establishment (DH/ECDH) — https://csrc.nist.gov/pubs/sp/800/56/a/r3/final
- OWASP Transport Layer Security Cheat Sheet — https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Security_Cheat_Sheet.html
- Mozilla TLS Configuration Guidelines — https://wiki.mozilla.org/Security/Server_Side_TLS

## Rede, Perímetro e Infraestrutura

### Arquitetura Zero Trust e Defesa em Profundidade (Zero Trust / Defense in Depth)

**Classificação:** `defensiva`

**O que é:** Modelo em que nenhum ator/dispositivo é confiável por localização de rede: cada acesso é autenticado, autorizado e avaliado continuamente, sustentado por múltiplas camadas independentes de controle.

**Como funciona:** No Zero Trust, decisões de acesso migram do perímetro de rede para um plano de política (Policy Decision Point) que avalia identidade, postura do dispositivo, contexto e risco a cada requisição, aplicadas por Policy Enforcement Points próximos ao recurso. Isso substitui o modelo 'castelo e fosso' (perímetro rígido, interior confiável), que falha porque um único ponto comprometido expõe tudo. Defesa em profundidade complementa: várias camadas independentes (rede, host, aplicação, dados, identidade) de modo que a falha de um controle não signifique comprometimento total. Juntos reduzem o raio de explosão e forçam o atacante a vencer múltiplos controles heterogêneos.

**Detecção:** Instrumente cada camada para telemetria: logs de autenticação/autorização do PDP, decisões de acesso negadas, mudanças de postura de dispositivo e anomalias de sessão. A ausência de logs em uma camada é, por si, um gap de detecção. Ferramentas: SIEM/UEBA correlacionando identidade + rede + endpoint, e avaliação periódica contra o CISA Zero Trust Maturity Model.

**Endurecimento:** Implemente autenticação forte (MFA resistente a phishing) e autorização por least privilege e por sessão, com reavaliação contínua. Adote microssegmentação e ZTNA (acesso por aplicação, não por rede), verificação de postura de dispositivo e cifragem fim a fim. Garanta camadas independentes (não dependa só do perímetro ou só do WAF), com pontos de negação padrão e failover seguro (fail closed). Trate identidade como novo perímetro e mantenha inventário de ativos/fluxos como base das políticas.

**Referências:**
- NIST SP 800-207 Zero Trust Architecture — https://doi.org/10.6028/NIST.SP.800-207
- CISA Zero Trust Maturity Model v2.0 — https://www.cisa.gov/zero-trust-maturity-model
- NIST SP 800-215 Guide to a Secure Enterprise Network Landscape — https://doi.org/10.6028/NIST.SP.800-215
- DoD Zero Trust Reference Architecture — https://dodcio.defense.gov/
- OWASP Defense in Depth — https://owasp.org/www-community/Defense_in_Depth

### Controle de Acesso à Rede (Network Access Control - NAC)

**Classificação:** `defensiva`

**O que é:** Controle que autentica e avalia dispositivos antes de conceder acesso à rede, atribuindo dinamicamente autorização e isolando os não conformes.

**Como funciona:** O NAC exige que um dispositivo se autentique (tipicamente via IEEE 802.1X com EAP e RADIUS) antes que a porta de switch/AP libere acesso além da autenticação. Após autenticar, políticas avaliam identidade e postura (patch, antivírus, conformidade) e atribuem dinamicamente VLAN/ACL — acesso pleno, restrito ou quarentena. Isso impede que dispositivos desconhecidos/rogue se conectem à rede corporativa e reduz o risco de hardware não autorizado (implantes) e de máquinas fora de conformidade. Fraquezas incluem MAB (autenticação só por MAC, falsificável) e ausência de suplicante em dispositivos legados/IoT, que exigem tratamento por perfilamento e segmentação.

**Detecção:** Monitore eventos do servidor RADIUS/NAC: falhas de autenticação 802.1X, dispositivos em quarentena, e endpoints usando MAB. Alerte sobre novos MACs/dispositivos em portas, mudanças de perfil e tentativas de spoofing de MAC. Ferramentas: logs NAC/RADIUS no SIEM, perfilamento de dispositivos (DHCP/fingerprint), e correlação com inventário de ativos.

**Endurecimento:** Implemente 802.1X com EAP-TLS (certificados de máquina/usuário) como método preferencial, minimizando MAB e restringindo-o a VLANs isoladas. Aplique avaliação de postura com quarentena/remediação para não conformes e segmente IoT/OT/convidados em VLANs próprias. Combine com port security, segmentação e least privilege; mantenha inventário confiável de ativos e trate o NAC como uma camada dentro de Zero Trust, não controle único.

**Referências:**
- IEEE 802.1X Port-Based Network Access Control — https://1.ieee802.org/security/802-1x/
- RFC 2865 Remote Authentication Dial In User Service (RADIUS) — https://www.rfc-editor.org/rfc/rfc2865
- RFC 3748 Extensible Authentication Protocol (EAP) — https://www.rfc-editor.org/rfc/rfc3748
- MITRE ATT&CK T1200 Hardware Additions — https://attack.mitre.org/techniques/T1200/
- NIST SP 800-207 Zero Trust Architecture — https://doi.org/10.6028/NIST.SP.800-207

### Defesa contra DDoS (Distributed Denial of Service)

**Classificação:** `defensiva`

**O que é:** Conjunto de controles para absorver, filtrar e mitigar ataques distribuídos que buscam esgotar largura de banda, estado de conexão ou recursos de aplicação.

**Como funciona:** Ataques DDoS saturam recursos por três vetores principais: volumétrico (esgotar banda, muitas vezes via amplificação/reflexão de UDP como DNS/NTP/SNMP), de protocolo/estado (ex.: SYN flood esgotando tabelas de conexão) e de camada de aplicação (requisições HTTP custosas que exaurem CPU/backends com baixo volume). A defesa combina capacidade de absorção (anycast, scrubbing na nuvem), filtragem de tráfego malicioso e proteção de recursos de aplicação. Amplificação depende de serviços abertos abusados como refletores e de spoofing de origem, mitigável por higiene de rede (BCP38). O objetivo é manter disponibilidade dos serviços legítimos sob carga hostil.

**Detecção:** Monitore métricas de baseline: pps/bps, novas conexões/s, taxa de erros 5xx e latência; desvios abruptos indicam ataque. Distinga L7 (muitos requests de poucas fontes, padrões de URL) de volumétrico (banda saturada, muitas fontes/spoofing). Ferramentas: telemetria NetFlow/IPFIX, dashboards de CDN/scrubbing, alertas de anomalia, e correlação com feeds de botnets.

**Endurecimento:** Contrate proteção DDoS/CDN com scrubbing e capacidade anycast, e mantenha runbook de mitigação (contatos, thresholds, failover). Aplique rate limiting, SYN cookies, connection limits, caching e proteção de camada 7 (WAF/bot mitigation) para endpoints custosos. Não seja parte do problema: feche serviços UDP abertos (DNS/NTP/SNMP/memcached) e implemente anti-spoofing (BCP38/uRPF). Faça autoscaling/degradação graciosa e teste o plano de resposta.

**Referências:**
- MITRE ATT&CK T1498 Network Denial of Service — https://attack.mitre.org/techniques/T1498/
- MITRE ATT&CK T1499 Endpoint Denial of Service — https://attack.mitre.org/techniques/T1499/
- CWE-400: Uncontrolled Resource Consumption — https://cwe.mitre.org/data/definitions/400.html
- BCP 38 / RFC 2827 Network Ingress Filtering — https://www.rfc-editor.org/rfc/rfc2827
- CISA Understanding and Responding to DDoS Attacks — https://www.cisa.gov/
- OWASP Denial of Service Cheat Sheet — https://cheatsheetseries.owasp.org/cheatsheets/Denial_of_Service_Cheat_Sheet.html

### Detecção e Prevenção de Intrusão (IDS/IPS)

**Classificação:** `defensiva`

**O que é:** Sistemas que inspecionam tráfego/eventos para detectar (IDS) ou bloquear ativamente (IPS) atividade maliciosa com base em assinaturas e/ou anomalias.

**Como funciona:** IDS/IPS de rede analisam pacotes/fluxos em um ponto de inspeção (SPAN/TAP para IDS; inline para IPS) comparando contra assinaturas conhecidas e/ou modelos de comportamento normal. IPS pode descartar ou reiniciar conexões maliciosas em tempo real, enquanto IDS apenas alerta. Detecção por assinatura é precisa para ameaças conhecidas mas cega a novidades; detecção por anomalia cobre desconhecidos ao custo de falsos positivos. A eficácia depende de posicionamento (ver tráfego relevante, inclusive leste-oeste), visibilidade de TLS e curadoria contínua de regras.

**Detecção:** O próprio IDS/IPS é fonte de detecção: correlacione seus alertas no SIEM com contexto de host (EDR) e ativos. Priorize alertas de reconhecimento (varredura), exploração de serviços, C2 e exfiltração; ajuste thresholds para reduzir ruído. Ferramentas: Suricata/Snort (assinaturas), Zeek (metadados e scripts de detecção), NDR comercial, e feeds de regras (ex.: Emerging Threats).

**Endurecimento:** Posicione sensores em ingress/egress e em segmentos internos críticos (visibilidade leste-oeste), com regras atualizadas e afinadas ao ambiente. Use IPS inline apenas com regras validadas para evitar bloqueio de tráfego legítimo; combine com decrypt/inspeção TLS onde permitido. Integre com resposta (SOAR/EDR) para conter hosts, mantenha baselines de comportamento e revise periodicamente cobertura versus a matriz ATT&CK.

**Referências:**
- NIST SP 800-94 Guide to Intrusion Detection and Prevention Systems — https://doi.org/10.6028/NIST.SP.800-94
- MITRE ATT&CK T1046 Network Service Discovery — https://attack.mitre.org/techniques/T1046/
- Suricata Documentation — https://docs.suricata.io/
- Zeek Documentation — https://docs.zeek.org/
- MITRE ATT&CK Enterprise Matrix — https://attack.mitre.org/matrices/enterprise/

### Firewall de Rede e Filtragem de Pacotes (Network Firewall / NGFW)

**Classificação:** `defensiva`

**O que é:** Controle que inspeciona e filtra tráfego entre redes com base em política, aplicando permissão/negação por endereço, porta, estado de conexão e, em NGFW, por aplicação e identidade.

**Como funciona:** Firewalls stateful mantêm tabela de conexões e decidem por fluxo (não só por pacote isolado), permitindo respostas apenas de sessões estabelecidas legítimas. NGFWs adicionam inspeção de camada 7 (identificação de aplicação, usuário, TLS inspection, IPS integrado) para políticas por app em vez de apenas porta. A avaliação segue ordem das regras com ação final default-deny; regras amplas (any-any) ou permissivas de saída anulam a proteção. A eficácia depende tanto da postura de entrada (ingress) quanto de saída (egress), esta última crítica para conter exfiltração e C2.

**Detecção:** Centralize logs de firewall no SIEM e alerte sobre regras any-any, mudanças não autorizadas de política e picos de negações/permissões incomuns. Indicadores: conexões de saída para destinos raros/reputação ruim, tráfego em portas não padrão, e sessões longas de baixo volume (possível C2). Ferramentas: análise de regras (firewall analyzers), revisão de baseline de ruleset, correlação com feeds de threat intel.

**Endurecimento:** Aplique default-deny em ingress e egress, com allowlist mínima e regras documentadas e datadas (com dono e justificativa). Faça revisões periódicas para remover regras obsoletas/sombreadas e reduzir escopo de origem/destino. Habilite logging em todas as regras relevantes, segmente a interface de gerência (out-of-band), aplique change management e teste a política com validação de alcançabilidade. Em NGFW, use políticas por aplicação/identidade e inspeção TLS onde legalmente permitido.

**Referências:**
- NIST SP 800-41 Rev.1 Guidelines on Firewalls and Firewall Policy — https://doi.org/10.6028/NIST.SP.800-41r1
- MITRE ATT&CK T1190 Exploit Public-Facing Application — https://attack.mitre.org/techniques/T1190/
- CWE-693: Protection Mechanism Failure — https://cwe.mitre.org/data/definitions/693.html
- CIS Benchmarks (Firewall/Network Devices) — https://www.cisecurity.org/cis-benchmarks
- MITRE ATT&CK T1071 Application Layer Protocol — https://attack.mitre.org/techniques/T1071/

### Proxy Reverso e Balanceadores de Carga (Reverse Proxy / Load Balancer)

**Classificação:** `defensiva`

**O que é:** Intermediário que recebe conexões de clientes e as distribui a servidores de backend, oferecendo terminação TLS, balanceamento e um ponto central de política — e novos riscos como request smuggling e exposição de origem.

**Como funciona:** O proxy reverso/balanceador termina conexões dos clientes e as encaminha a um pool de backends, com balanceamento (L4/L7), health checks, terminação/reencriptação TLS e, muitas vezes, WAF e rate limiting integrados. Como fica na fronteira, concentra decisões de roteamento e cabeçalhos: discrepâncias de interpretação de HTTP entre proxy e backend permitem HTTP Request Smuggling (CWE-444), envenenando filas de requisições. Confiança indevida em cabeçalhos como X-Forwarded-For pode falsificar IP de cliente e burlar controles; e se a origem for acessível diretamente (fora do proxy/CDN), os controles de borda são contornados. Também é ponto sensível para SSRF quando encaminha requisições a destinos internos.

**Detecção:** Monitore anomalias de HTTP (Content-Length vs Transfer-Encoding conflitantes, requisições malformadas) que indicam tentativas de smuggling. Verifique se a origem responde a conexões diretas (bypass de CDN/WAF) e alerte sobre cabeçalhos de encaminhamento inconsistentes. Ferramentas: logs de proxy no SIEM, testes de configuração HTTP, varredura de exposição da origem e revisão de regras de roteamento.

**Endurecimento:** Normalize e valide HTTP consistentemente entre proxy e backend; use servidores que rejeitem requisições ambíguas (TE/CL) para prevenir smuggling. Restrinja a origem a aceitar tráfego apenas do proxy/CDN (allowlist de IP, mTLS ou tokens), evitando bypass. Sobrescreva X-Forwarded-For no edge (não confie no valor do cliente), aplique TLS forte fim a fim, rate limiting e timeouts. Endureça o proxy (versões suportadas, patch), limite métodos/tamanhos e valide destinos para mitigar SSRF.

**Referências:**
- CWE-444: HTTP Request/Response Smuggling — https://cwe.mitre.org/data/definitions/444.html
- OWASP HTTP Request Smuggling — https://owasp.org/www-community/attacks/HTTP_Request_Smuggling
- OWASP Top 10 2021 A10 Server-Side Request Forgery (SSRF) — https://owasp.org/Top10/A10_2021-Server-Side_Request_Forgery_%28SSRF%29/
- OWASP Secure Headers / Proxy configuration — https://owasp.org/www-project-secure-headers/
- MITRE ATT&CK T1190 Exploit Public-Facing Application — https://attack.mitre.org/techniques/T1190/

### Reconhecimento e Enumeração de Rede em Escopo Autorizado (Network Reconnaissance / Enumeration)

**Classificação:** `escopo_autorizado`

**O que é:** Fase de levantamento de ativos, serviços e superfície de ataque que, do lado ofensivo autorizado, exige autorização escrita e regras de engajamento, e do lado defensivo serve para conhecer e reduzir a própria exposição.

**Como funciona:** O reconhecimento coleta informações sobre a organização-alvo de forma passiva (OSINT, DNS, certificados, registros públicos) e ativa (varredura de portas/serviços, fingerprinting de versões, enumeração de hosts e serviços expostos). O objetivo é mapear a superfície de ataque: quais IPs/portas/serviços estão vivos, versões, e possíveis pontos fracos, insumo para priorizar avaliação. Em contexto autorizado (pentest/bug bounty), é a primeira fase e deve respeitar estritamente escopo, janelas e intensidade acordados; varredura fora de escopo ou agressiva pode causar indisponibilidade e violar contrato/lei. Defensivamente, o mesmo mapeamento (attack surface management) revela exposição indevida a ser corrigida.

**Detecção:** Do lado defensivo, detecte varredura por muitas conexões a portas variadas de uma mesma origem, conexões a portas fechadas, e fingerprinting; use IDS/IPS e NDR para assinaturas de scanning (ex.: SYN scan, sweeps). Correlacione com feeds de scanners conhecidos e alerte sobre enumeração interna (possível pós-comprometimento). Ferramentas: Suricata/Zeek, honeypots/honeytokens, e logs de firewall com contagem de negações.

**Endurecimento:** Reduza a superfície: exponha apenas o necessário, feche portas/serviços não usados e use default-deny no perímetro. Faça Attack Surface Management contínuo (inventário externo, varredura autorizada própria) para achar exposição antes do atacante. Para atividades ofensivas, exija autorização escrita, escopo e regras de engajamento documentadas (NIST SP 800-115/PTES), limites de intensidade, janelas e contatos de emergência. Implemente rate limiting, banners mínimos e detecção de scanning.

**Referências:**
- NIST SP 800-115 Technical Guide to Information Security Testing and Assessment — https://doi.org/10.6028/NIST.SP.800-115
- MITRE ATT&CK TA0043 Reconnaissance — https://attack.mitre.org/tactics/TA0043/
- MITRE ATT&CK T1595 Active Scanning — https://attack.mitre.org/techniques/T1595/
- MITRE ATT&CK T1046 Network Service Discovery — https://attack.mitre.org/techniques/T1046/
- PTES Technical Guidelines — http://www.pentest-standard.org/
- OWASP Testing Guide — Information Gathering — https://owasp.org/www-project-web-security-testing-guide/

### Segmentação de Rede e Microssegmentação (Network Segmentation / Microsegmentation)

**Classificação:** `defensiva`

**O que é:** Prática de dividir a rede em zonas isoladas com políticas de comunicação explícitas para conter o movimento lateral de um atacante que comprometa um único host.

**Como funciona:** A segmentação impõe fronteiras de controle (VLANs, sub-redes, VRFs, security groups, firewalls internos) entre grupos de ativos, permitindo apenas os fluxos estritamente necessários entre zonas. A microssegmentação leva o conceito ao nível de carga de trabalho/host, aplicando políticas por identidade e por fluxo (leste-oeste) em vez de apenas no perímetro norte-sul. Sem segmentação, um único host comprometido oferece caminho livre (rede plana) para reconhecimento e pivoteamento até ativos críticos. O objetivo defensivo é reduzir o raio de explosão e criar pontos de inspeção e negação padrão (default-deny).

**Detecção:** Mapeie fluxos reais com NetFlow/IPFIX, sFlow e logs de firewall para identificar comunicações leste-oeste anômalas ou não previstas na política. Alertas de EDR/NDR sobre varredura interna, SMB/RDP entre segmentos que não deveriam se comunicar e conexões cruzando zonas indicam falha de contenção. Ferramentas: Zeek/Suricata para visibilidade leste-oeste, coletores NetFlow (nfdump, ntopng), CSPM/CNAPP para regras de security group em nuvem, e revisão periódica de matriz de fluxos.

**Endurecimento:** Adote default-deny entre zonas e libere apenas fluxos justificados (allowlist por porta/serviço/identidade). Separe ambientes (produção, homologação, gestão/OOB, IoT/OT, convidados) e coloque serviços expostos em DMZ. Em nuvem, use security groups/NSGs restritivos e políticas de identidade; on-prem, use 802.1X, private VLANs e firewalls internos. Valide a eficácia da segmentação com testes de alcançabilidade periódicos e mantenha a matriz de fluxos como documento vivo.

**Referências:**
- NIST SP 800-207 Zero Trust Architecture — https://doi.org/10.6028/NIST.SP.800-207
- NIST SP 800-125B Secure Virtual Network Configuration — https://doi.org/10.6028/NIST.SP.800-125B
- CWE-923: Improper Restriction of Communication Channel to Intended Endpoints — https://cwe.mitre.org/data/definitions/923.html
- MITRE ATT&CK T1210 Exploitation of Remote Services — https://attack.mitre.org/techniques/T1210/
- PCI DSS v4.0 Requirement 1 / Network Segmentation Guidance — https://www.pcisecuritystandards.org/

### Segurança de DNS (DNS Security)

**Classificação:** `defensiva`

**O que é:** Conjunto de riscos e controles do sistema de nomes: envenenamento de cache, spoofing, uso de DNS para C2/exfiltração e a proteção de integridade via DNSSEC e transporte cifrado.

**Como funciona:** O DNS resolve nomes em endereços via consultas UDP/TCP 53; sem autenticação de origem, respostas forjadas podem envenenar caches (spoofing) e redirecionar vítimas. DNSSEC adiciona assinaturas que permitem validar a integridade/autenticidade dos registros, mitigando adulteração (mas não confidencialidade). Atacantes também abusam do DNS como canal encoberto: DNS tunneling codifica dados em subdomínios/registros para exfiltração e C2, geralmente contornando controles que confiam cegamente em tráfego 53. DoH/DoT cifram o transporte da consulta, protegendo privacidade, mas podem cegar inspeção se não centralizados.

**Detecção:** Analise volume e entropia de consultas por host: muitos subdomínios únicos, nomes longos/aleatórios e registros TXT/NULL anômalos sugerem tunneling/exfiltração. Monitore respostas inconsistentes (possível spoofing), consultas a domínios recém-registrados/DGA e uso de resolvers externos não autorizados. Ferramentas: Zeek (logs DNS), Suricata, sinkholing de domínios maliciosos, e análise de logs de resolver recursivo no SIEM.

**Endurecimento:** Implante DNSSEC (validação nos resolvers e assinatura de zonas próprias) e force o uso de resolvers internos controlados, bloqueando DNS externo (53/DoH) não autorizado no perímetro. Aplique DNS filtering/RPZ e threat intel para bloquear domínios maliciosos, e limite/alerta sobre tunneling. Segmente e endureça servidores DNS, use rate limiting (RRL) em autoritativos e habilite logging completo para detecção. Prefira DoT/DoH terminado em resolver corporativo que preserve visibilidade.

**Referências:**
- RFC 4033 DNS Security Introduction and Requirements (DNSSEC) — https://www.rfc-editor.org/rfc/rfc4033
- RFC 7858 DNS over TLS — https://www.rfc-editor.org/rfc/rfc7858
- RFC 8484 DNS Queries over HTTPS (DoH) — https://www.rfc-editor.org/rfc/rfc8484
- MITRE ATT&CK T1071.004 Application Layer Protocol: DNS — https://attack.mitre.org/techniques/T1071/004/
- MITRE ATT&CK T1568 Dynamic Resolution — https://attack.mitre.org/techniques/T1568/
- CWE-350: Reliance on Reverse DNS Resolution — https://cwe.mitre.org/data/definitions/350.html

### Segurança do Protocolo RDP (Remote Desktop Protocol)

**Classificação:** `defensiva`

**O que é:** Protocolo de área de trabalho remota do Windows (porta 3389) que, quando exposto e sem controles, é um dos principais vetores de acesso inicial e ransomware.

**Como funciona:** O RDP fornece sessão gráfica remota autenticada; exposto à internet, torna-se alvo de força bruta e password spraying massivos contra credenciais fracas ou reutilizadas. Sem Network Level Authentication (NLA), a autenticação ocorre tarde no fluxo, ampliando exposição a vulnerabilidades pré-autenticação (ex.: BlueKeep/CVE-2019-0708, wormable). Credenciais válidas dão sessão interativa completa, facilitando persistência e implantação de ransomware. O risco decorre de exposição direta, ausência de MFA e de NLA, e host sem patch.

**Detecção:** Alerte sobre 3389 exposto externamente e sobre picos de autenticações RDP falhas/sucesso de origens incomuns (eventos 4625/4624, logon type 10). Monitore geolocalização impossível, uso de contas administrativas e novas conexões RDP entre segmentos. Ferramentas: SIEM com eventos de logon, Zeek/Suricata para 3389, e varredura interna de exposição.

**Endurecimento:** Nunca exponha RDP diretamente à internet: use gateway RDP/bastião atrás de VPN/ZTNA com MFA. Habilite NLA, aplique patches (BlueKeep e correlatos), imponha senhas fortes com bloqueio de conta e restrinja quem pode fazer RDP (least privilege, contas dedicadas). Considere restrição por IP de origem, session timeouts, e monitoramento de acesso privilegiado. Segmente estações de administração (PAW/jump hosts).

**Referências:**
- MITRE ATT&CK T1021.001 Remote Desktop Protocol — https://attack.mitre.org/techniques/T1021/001/
- Microsoft CVE-2019-0708 (BlueKeep) Guidance — https://msrc.microsoft.com/update-guide/vulnerability/CVE-2019-0708
- CISA Alert: Securing Remote Access / RDP — https://www.cisa.gov/
- CWE-307: Improper Restriction of Excessive Authentication Attempts — https://cwe.mitre.org/data/definitions/307.html
- NIST SP 800-46 Guide to Enterprise Telework and Remote Access — https://doi.org/10.6028/NIST.SP.800-46r2

### Segurança do Protocolo SMB (Server Message Block)

**Classificação:** `defensiva`

**O que é:** Protocolo de compartilhamento de arquivos/impressão do Windows cujas versões legadas e configurações fracas são vetor histórico de propagação de ransomware e movimento lateral.

**Como funciona:** O SMB (porta 445) provê acesso a arquivos, impressoras e IPC entre hosts; SMBv1 é obsoleto e vulnerável (ex.: MS17-010/EternalBlue), e a falta de assinatura (SMB signing) permite ataques de relay NTLM. Autenticação NTLM legada e compartilhamentos administrativos expostos habilitam movimento lateral com credenciais válidas ou hashes. Exposição do 445 à internet ou entre segmentos sem necessidade amplia drasticamente a superfície. O risco central é a combinação de versão insegura, ausência de assinatura/cifragem e credenciais reutilizáveis.

**Detecção:** Monitore tráfego SMB na borda (445/139 nunca deveria sair/entrar da internet) e entre segmentos que não precisam se comunicar. Alerte sobre uso de SMBv1, autenticações NTLM anômalas, acesso a compartilhamentos administrativos (ADMIN$, C$) e picos de operações de arquivo (possível ransomware). Ferramentas: Zeek (logs SMB/DCE-RPC), Suricata, EDR para acesso a shares, e auditoria de eventos 5140/5145 do Windows.

**Endurecimento:** Desative SMBv1 em todo o parque e exija SMB signing e cifragem (SMBv3). Bloqueie 139/445 no perímetro e restrinja SMB entre segmentos por least privilege. Aplique patches (MS17-010 e posteriores), reduza uso de NTLM (preferir Kerberos), habilite proteções contra relay (assinatura + EPA) e implemente credenciais administrativas segmentadas (tiering, LAPS). Restrinja e audite permissões de compartilhamentos.

**Referências:**
- MITRE ATT&CK T1021.002 SMB/Windows Admin Shares — https://attack.mitre.org/techniques/T1021/002/
- CWE-306: Missing Authentication for Critical Function — https://cwe.mitre.org/data/definitions/306.html
- Microsoft MS17-010 Security Update — https://learn.microsoft.com/security-updates/
- Microsoft: Detect, enable and disable SMBv1/v2/v3 — https://learn.microsoft.com/windows-server/storage/file-server/
- MITRE ATT&CK T1210 Exploitation of Remote Services — https://attack.mitre.org/techniques/T1210/

### Segurança do Protocolo SNMP (Simple Network Management Protocol)

**Classificação:** `defensiva`

**O que é:** Protocolo de gerência de rede cujas versões legadas (v1/v2c) usam community strings em texto claro, expondo informações de infraestrutura e servindo a reconhecimento e amplificação DDoS.

**Como funciona:** SNMP (UDP 161/162) permite consultar e alterar variáveis de gerência (MIB) em dispositivos de rede. Nas versões v1/v2c, a autenticação é apenas uma community string transmitida sem cifragem, frequentemente deixada nos padrões 'public'/'private', permitindo leitura de topologia, interfaces, ARP e configuração — insumo valioso para reconhecimento. Community de escrita insegura pode permitir alteração de configuração. Serviços SNMP abertos também são abusados como refletores/amplificadores em ataques DDoS. O risco é a combinação de versão insegura, credenciais padrão e exposição.

**Detecção:** Verifique dispositivos respondendo a SNMP com communities padrão e exposição de 161/162 além do necessário. Monitore consultas SNMP de origens não autorizadas e volume anômalo (possível reflexão/amplificação). Ferramentas: varredura de configuração/exposição interna, logs de dispositivos de rede, e NDR para tráfego SNMP fora da estação de gerência.

**Endurecimento:** Prefira SNMPv3 com autenticação e cifragem (authPriv); desative v1/v2c onde possível. Troque todas as community strings padrão, restrinja SNMP à rede/gerência out-of-band via ACL e ao mínimo de hosts (allowlist de NMS). Use somente leitura quando escrita não for necessária, filtre 161/162 no perímetro e monitore/rotacione credenciais. Desabilite SNMP em dispositivos que não o utilizam.

**Referências:**
- RFC 3411 An Architecture for SNMP Management Frameworks — https://www.rfc-editor.org/rfc/rfc3411
- CWE-1188: Insecure Default Initialization of Resource — https://cwe.mitre.org/data/definitions/1188.html
- CWE-319: Cleartext Transmission of Sensitive Information — https://cwe.mitre.org/data/definitions/319.html
- MITRE ATT&CK T1046 Network Service Discovery — https://attack.mitre.org/techniques/T1046/
- CISA Alert TA14-017A UDP-Based Amplification Attacks — https://www.cisa.gov/news-events/alerts/2014/01/17/udp-based-amplification-attacks

### VPN e Acesso Remoto Seguro (VPN / Remote Access)

**Classificação:** `defensiva`

**O que é:** Túnel criptografado que estende o acesso a recursos internos por redes não confiáveis, e um dos alvos preferenciais para acesso inicial quando mal configurado ou desatualizado.

**Como funciona:** A VPN estabelece um túnel autenticado e cifrado (IPsec/IKEv2, TLS, WireGuard) entre cliente e gateway, protegendo confidencialidade e integridade em trânsito. O gateway autentica o usuário/dispositivo e aplica políticas de acesso; falhas comuns são autenticação de fator único, appliances sem patch (CVEs frequentes em concentradores) e split tunneling mal governado. Como serviço de acesso remoto exposto, concentra risco: credenciais válidas ou uma vulnerabilidade no gateway podem render acesso inicial à rede interna. Modelos ZTNA substituem o acesso amplo de rede por acesso por aplicação, baseado em identidade e postura.

**Detecção:** Monitore autenticações de VPN por geolocalização impossível, horários atípicos, força bruta/password spraying e uso de contas de serviço. Vigie versões/patch level dos concentradores e correlacione com boletins de fornecedores e CISA KEV. Ferramentas: logs RADIUS/gateway no SIEM, alertas de UEBA, e verificação de exposição externa dos endpoints de gerência.

**Endurecimento:** Exija MFA resistente a phishing em todo acesso remoto e aplique patches de gateway com prioridade máxima (fazem parte do KEV frequentemente). Restrinja o que a VPN alcança (segmentação + least privilege), evite full-tunnel excessivo ou split tunnel sem controle e verifique postura do dispositivo. Considere migrar para ZTNA (acesso por aplicação, não por rede). Desative protocolos/cifras legados, proteja a interface de administração (OOB) e monitore/rotacione credenciais de serviço.

**Referências:**
- NIST SP 800-77 Rev.1 Guide to IPsec VPNs — https://doi.org/10.6028/NIST.SP.800-77r1
- NIST SP 800-113 Guide to SSL VPNs — https://doi.org/10.6028/NIST.SP.800-113
- MITRE ATT&CK T1133 External Remote Services — https://attack.mitre.org/techniques/T1133/
- CWE-319: Cleartext Transmission of Sensitive Information — https://cwe.mitre.org/data/definitions/319.html
- CISA Known Exploited Vulnerabilities Catalog — https://www.cisa.gov/known-exploited-vulnerabilities-catalog
- RFC 4301 Security Architecture for the Internet Protocol — https://www.rfc-editor.org/rfc/rfc4301

### Web Application Firewall (WAF)

**Classificação:** `defensiva`

**O que é:** Filtro de camada 7 que inspeciona requisições HTTP/S para bloquear ataques a aplicações web e servir como camada compensatória (virtual patching).

**Como funciona:** O WAF analisa requisições/respostas HTTP contra assinaturas e regras (ex.: OWASP Core Rule Set) e/ou modelos de anomalia, pontuando e bloqueando padrões associados a injeção, XSS, path traversal e outros. Pode operar em modo negativo (bloquear o malicioso conhecido) ou positivo (permitir apenas o esperado por schema). Funciona como controle compensatório: reduz janela de exposição de vulnerabilidades enquanto o código é corrigido (virtual patching), mas não substitui código seguro. Bypass é possível via ofuscação, encoding e falhas de normalização, por isso é uma camada, não a defesa única.

**Detecção:** Monitore logs do WAF para picos de bloqueios, tentativas repetidas do mesmo IP/ASN e assinaturas de SQLi/XSS/LFI. Correlacione eventos do WAF com logs da aplicação para distinguir ataque real de falso positivo. Ferramentas: ModSecurity + OWASP CRS, WAFs de nuvem (com logs para SIEM), e dashboards de taxa de bloqueio por regra/URI.

**Endurecimento:** Implante em modo de bloqueio (após período de tuning em detecção) com OWASP CRS atualizado e paranoia level ajustado ao risco. Combine com modelo positivo por schema (validação de API/OpenAPI), rate limiting e mitigação de bots. Garanta que o WAF veja o IP real do cliente (cabeçalhos de proxy confiáveis) e que a origem não seja acessível fora do WAF/CDN. Trate o WAF como defesa em profundidade sobre validação/escape no código, nunca como substituto.

**Referências:**
- OWASP Top 10 2021 A03 Injection — https://owasp.org/Top10/A03_2021-Injection/
- OWASP ModSecurity Core Rule Set — https://coreruleset.org/
- CWE-693: Protection Mechanism Failure — https://cwe.mitre.org/data/definitions/693.html
- MITRE ATT&CK T1190 Exploit Public-Facing Application — https://attack.mitre.org/techniques/T1190/
- OWASP Web Application Firewall — https://owasp.org/www-community/Web_Application_Firewall

## Segurança em Nuvem

### Credenciais Temporárias e Roles Assumidas (STS / Temporary Credentials)

**Classificação:** `defensiva`

**O que é:** Uso de credenciais de curta duração emitidas por serviços de token de segurança (AWS STS, GCP/Azure workload identity federation) em vez de chaves estáticas, reduzindo a janela de exposição de credenciais.

**Como funciona:** Um serviço de token emite credenciais temporárias com escopo e expiração curta quando uma identidade assume uma role, mediante uma trust policy que define quem pode assumi-la e sob quais condições. A federação por OIDC/SAML e workload identity permite que cargas fora da nuvem ou de outros provedores obtenham tokens sem chaves de longa duração armazenadas. O risco do 'confused deputy' surge quando uma trust policy é ampla demais (permite assunção por terceiros sem validar contexto), permitindo que outra conta induza a role a agir em seu nome; a condição ExternalId e restrições de source account mitigam isso. Como as credenciais expiram, o impacto de um vazamento é limitado no tempo, mas trust policies mal configuradas transferem o risco para o controle de quem pode assumir.

**Detecção:** Auditar trust policies por Principal amplo (contas externas, curingas) e ausência de condições (ExternalId, aws:SourceAccount, sub/aud em OIDC). Monitorar CloudTrail por eventos AssumeRole/AssumeRoleWithWebIdentity anômalos: assunções de contas desconhecidas, de regiões incomuns ou fora do horário. Verificar ainda a existência de chaves de longa duração que deveriam ter sido substituídas por federação, via credential reports.

**Endurecimento:** Preferir credenciais temporárias e federação de identidade de workload a chaves estáticas em todos os cenários. Restringir trust policies ao Principal mínimo com condições explícitas (ExternalId para acesso de terceiros, restrição de conta/organização, claims OIDC específicos). Definir duração de sessão mínima necessária e aplicar menor privilégio na role assumida. Monitorar e alertar sobre uso das credenciais fora do contexto esperado (IP, geografia, serviço de origem).

**Referências:**
- CWE-441 Unintended Proxy or Intermediary (Confused Deputy) - https://cwe.mitre.org/data/definitions/441.html
- CWE-863 Incorrect Authorization - https://cwe.mitre.org/data/definitions/863.html
- AWS STS and the Confused Deputy Problem - https://docs.aws.amazon.com/IAM/latest/UserGuide/confused-deputy.html
- NIST SP 800-63C Federation and Assertions - https://pages.nist.gov/800-63-3/sp800-63c.html
- Google Cloud Workload Identity Federation - https://cloud.google.com/iam/docs/workload-identity-federation
- MITRE ATT&CK T1550 Use Alternate Authentication Material - https://attack.mitre.org/techniques/T1550/

### Criptografia de Dados e Gestão de Chaves na Nuvem (Encryption & KMS)

**Classificação:** `defensiva`

**O que é:** Proteção de dados em repouso e em trânsito por criptografia e o gerenciamento seguro de chaves em serviços gerenciados (AWS KMS, Cloud KMS, Azure Key Vault), incluindo controle de acesso e rotação de chaves.

**Como funciona:** Serviços de KMS gerenciam chaves de criptografia e implementam envelope encryption, onde uma chave de dados criptografa o conteúdo e é ela própria criptografada por uma chave mestra (CMK) protegida por HSM. O controle de acesso à chave (key policy + IAM) é o verdadeiro perímetro de segurança: quem pode usar a CMK pode descriptografar os dados, independentemente de permissões no recurso de armazenamento. Chaves gerenciadas pelo cliente (CMK) oferecem controle de política, rotação e auditoria de uso, ao contrário de chaves gerenciadas pelo provedor. Falhas comuns incluem criptografia desativada, uso de algoritmos/protocolos fracos, TLS não obrigatório em trânsito e políticas de chave permissivas que anulam o benefício da criptografia.

**Detecção:** CSPM sinaliza recursos sem criptografia em repouso, ausência de rotação de chave e key policies excessivas. Monitorar logs de uso de KMS (CloudTrail Decrypt/Encrypt/GenerateDataKey) por acessos anômalos e tentativas de descriptografia negadas. Verificar via análise de configuração se TLS é obrigatório (políticas aws:SecureTransport, HTTPS-only) e escanear por algoritmos/protocolos obsoletos (TLS 1.0/1.1, SSLv3) em endpoints.

**Endurecimento:** Habilitar criptografia em repouso por padrão em todos os serviços de dados usando CMK com rotação anual automática. Aplicar menor privilégio em key policies separando quem administra a chave de quem a usa; exigir grants explícitos. Forçar TLS 1.2+ em trânsito e negar tráfego não criptografado por política de bucket/serviço. Considerar chaves com material importado/HSM dedicado para dados de alta sensibilidade e registrar todo uso de chave para auditoria.

**Referências:**
- OWASP Top 10 2021 A02 Cryptographic Failures - https://owasp.org/Top10/A02_2021-Cryptographic_Failures/
- CWE-311 Missing Encryption of Sensitive Data - https://cwe.mitre.org/data/definitions/311.html
- CWE-326 Inadequate Encryption Strength - https://cwe.mitre.org/data/definitions/326.html
- CWE-327 Use of a Broken or Risky Cryptographic Algorithm - https://cwe.mitre.org/data/definitions/327.html
- NIST SP 800-57 Recommendation for Key Management - https://csrc.nist.gov/pubs/sp/800/57/pt1/r5/final
- AWS KMS Best Practices - https://docs.aws.amazon.com/kms/latest/developerguide/best-practices.html

### Enumeração e Avaliação de Ativos de Nuvem (Cloud Asset Enumeration)

**Classificação:** `escopo_autorizado`

**O que é:** Levantamento autorizado de recursos, identidades e permissões de um ambiente de nuvem para mapear a superfície de ataque durante avaliação de segurança contratada, exigindo autorização escrita e regras de engajamento.

**Como funciona:** A enumeração consulta as APIs do provedor (com credenciais fornecidas ou obtidas no escopo do teste) para inventariar recursos, políticas IAM, buckets, funções, redes e relações de confiança, construindo um mapa da superfície de ataque e de possíveis caminhos de escalada. Ferramentas de avaliação (ScoutSuite, Prowler, PMapper, CloudMapper) automatizam a coleta e destacam misconfigurações e privilégios excessivos a partir do estado observado. O objetivo defensivo é identificar exposições antes de um atacante, sempre dentro de um escopo autorizado por escrito com regras de engajamento definidas (contas, janelas de tempo, ações permitidas). Sem autorização explícita e delimitação de escopo, a mesma atividade constitui acesso não autorizado; a distinção é legal e contratual, não técnica.

**Detecção:** Do lado defensivo, detectar enumeração massiva via CloudTrail/Audit Logs: alto volume de chamadas Describe/List/Get em curto intervalo, especialmente de uma identidade nova ou de IP incomum. GuardDuty e SCC possuem detecções de reconnaissance (ex.: Discovery:IAMUser/AnomalousBehavior). Correlacionar rajadas de chamadas somente-leitura de IAM/enumeração de recursos com a linha de base de comportamento da identidade.

**Endurecimento:** Exigir autorização escrita, escopo e regras de engajamento antes de qualquer enumeração; usar contas de teste dedicadas com permissões mínimas e logging integral. Aplicar rate limiting e detecção de anomalias para reconhecimento não autorizado; restringir permissões de Describe/List por menor privilégio. Documentar e time-box a atividade e coordenar com equipes de detecção para evitar falsos incidentes. Após a avaliação, remediar as exposições identificadas e revogar credenciais de teste.

**Referências:**
- MITRE ATT&CK T1580 Cloud Infrastructure Discovery - https://attack.mitre.org/techniques/T1580/
- MITRE ATT&CK TA0007 Discovery - https://attack.mitre.org/tactics/TA0007/
- NIST SP 800-115 Technical Guide to Information Security Testing and Assessment - https://csrc.nist.gov/pubs/sp/800/115/final
- OWASP Web Security Testing Guide - https://owasp.org/www-project-web-security-testing-guide/
- PTES Technical Guidelines - http://www.pentest-standard.org/index.php/PTES_Technical_Guidelines

### Escalada de Privilégios e Movimentação Lateral no IAM da Nuvem (IAM Privilege Escalation)

**Classificação:** `laboratorio_autorizado`

**O que é:** Cadeias de permissões IAM aparentemente inócuas que permitem a uma identidade de baixo privilégio elevar-se a administrador ou pivotar entre recursos, estudadas em laboratório próprio para entender e fechar esses caminhos.

**Como funciona:** Certas permissões, embora individualmente limitadas, formam cadeias de escalada quando combinadas: por exemplo, poder criar uma nova versão de política (iam:CreatePolicyVersion), anexar políticas a si mesmo, ou passar uma role privilegiada a um recurso que a identidade controla (iam:PassRole com ec2:RunInstances/lambda:CreateFunction). A movimentação lateral explora relações de confiança e credenciais herdadas: assumir roles encadeadas (role chaining), abusar de service accounts com escopo amplo, ou usar credenciais de uma instância comprometida para acessar outros serviços. O modelo mental de grafo de identidades revela caminhos onde nós de baixo privilégio alcançam nós administrativos através de arestas de permissão. Estudar essas cadeias em um ambiente controlado permite mapear e eliminar as arestas perigosas antes que sejam exploradas em produção.

**Detecção:** Modelar permissões como grafo com ferramentas de análise de caminho (PMapper, Cloudsplaining, AWS IAM Access Analyzer) para descobrir rotas de escalada existentes. Monitorar CloudTrail por sequências indicativas: CreatePolicyVersion seguido de AttachRolePolicy, PassRole com criação de recurso, ou AssumeRole encadeados. Alertar sobre mudanças em políticas de identidades não administrativas e sobre roles assumindo roles em cadeia.

**Endurecimento:** Aplicar permission boundaries e SCPs que impeçam identidades de modificar suas próprias permissões ou passar roles privilegiadas. Restringir iam:PassRole por condição a roles específicas e negar as ações de auto-elevação (CreatePolicyVersion, AttachUserPolicy) a identidades não administrativas. Executar análise de caminho de privilégio periodicamente e remediar arestas perigosas; separar deveres administrativos. Realizar tais experimentos apenas em contas de laboratório próprias e isoladas, nunca em produção ou ambientes de terceiros.

**Referências:**
- CWE-269 Improper Privilege Management - https://cwe.mitre.org/data/definitions/269.html
- CWE-266 Incorrect Privilege Assignment - https://cwe.mitre.org/data/definitions/266.html
- MITRE ATT&CK T1548 Abuse Elevation Control Mechanism - https://attack.mitre.org/techniques/T1548/
- MITRE ATT&CK T1078.004 Valid Accounts: Cloud Accounts - https://attack.mitre.org/techniques/T1078/004/
- NIST SP 800-53 Rev.5 AC-6 Least Privilege - https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final
- AWS IAM Access Analyzer - https://docs.aws.amazon.com/IAM/latest/UserGuide/what-is-access-analyzer.html

### Exposição Pública de Recursos e Superfície de Ataque (Public Resource Exposure)

**Classificação:** `defensiva`

**O que é:** Recursos de computação, banco de dados e rede tornados alcançáveis pela internet aberta por regras de firewall/security group permissivas, ampliando desnecessariamente a superfície de ataque.

**Como funciona:** Security groups, NSGs e regras de firewall controlam o tráfego de entrada e saída; regras que abrem portas administrativas (SSH 22, RDP 3389) ou de banco de dados (3306, 5432, 27017, 6379) para 0.0.0.0/0 expõem serviços diretamente à internet. Bancos de dados gerenciados, clusters e painéis de administração configurados com endpoint público e sem restrição de origem ficam sujeitos a força bruta, exploração de CVEs e acesso não autenticado quando a autenticação também é fraca. Atacantes varrem continuamente faixas de IP de provedores de nuvem em busca desses serviços expostos, de modo que a exposição resulta em tentativas de comprometimento em minutos. A ausência de segmentação faz com que qualquer serviço exposto sirva de porta de entrada para movimentação lateral na VPC.

**Detecção:** CSPM e ferramentas de rede (AWS Config rules, GCP SCC, Prowler, ScoutSuite) sinalizam security groups/NSGs com 0.0.0.0/0 em portas sensíveis e recursos com IP público. Usar AWS Network Access Analyzer / VPC Reachability Analyzer para validar caminhos de rede efetivos. Monitorar logs de fluxo (VPC Flow Logs) por conexões de entrada de IPs externos a portas administrativas e correlacionar com tentativas de autenticação falhas.

**Endurecimento:** Fechar portas administrativas à internet e acessá-las apenas via bastion host, VPN ou serviços de acesso sem exposição (SSM Session Manager, IAP, Bastion). Restringir origens por allowlist de IP e usar grupos de segurança referenciando outros grupos em vez de CIDRs amplos. Manter bancos de dados em subnets privadas sem endpoint público; aplicar segmentação de rede e egress filtering. Usar guardrails preventivos (SCP/Azure Policy) que impeçam a criação de regras 0.0.0.0/0 em portas críticas.

**Referências:**
- OWASP Top 10 2021 A05 Security Misconfiguration - https://owasp.org/Top10/A05_2021-Security_Misconfiguration/
- CWE-668 Exposure of Resource to Wrong Sphere - https://cwe.mitre.org/data/definitions/668.html
- CWE-284 Improper Access Control - https://cwe.mitre.org/data/definitions/284.html
- NIST SP 800-41 Rev.1 Guidelines on Firewalls - https://csrc.nist.gov/pubs/sp/800/41/r1/final
- MITRE ATT&CK T1133 External Remote Services - https://attack.mitre.org/techniques/T1133/
- CIS Amazon Web Services Foundations Benchmark - https://www.cisecurity.org/benchmark/amazon_web_services

### Gestão de Postura de Segurança na Nuvem (CSPM)

**Classificação:** `defensiva`

**O que é:** Disciplina e ferramentas que avaliam continuamente configurações de recursos de nuvem contra benchmarks de segurança para detectar e remediar misconfigurações e desvios de conformidade.

**Como funciona:** CSPM coleta o estado de configuração via APIs do provedor e o avalia contra regras derivadas de benchmarks (CIS, boas práticas do provedor, requisitos regulatórios), identificando recursos públicos, criptografia ausente, logging desativado e IAM excessivo. A avaliação é contínua e detecta 'drift' — quando um recurso se desvia do estado seguro esperado após mudanças manuais ou por automação. Ferramentas correlacionam achados em um inventário unificado e priorizam por severidade e exposição, alguns com remediação automatizada. O valor está em cobrir a superfície ampla e dinâmica da nuvem, onde mudanças frequentes tornam auditorias pontuais insuficientes.

**Detecção:** Este é essencialmente o mecanismo de detecção: rodar AWS Config + Security Hub, GCP Security Command Center, Microsoft Defender for Cloud, ou ferramentas open-source (Prowler, ScoutSuite, CloudSploit, Steampipe) contra benchmarks CIS. Integrar achados a SIEM e ticketing; medir cobertura por conta/projeto/subscription e acompanhar tendência de misconfigurações ao longo do tempo. Alertar sobre criação de recursos que violem baseline em tempo quase real via eventos de mudança.

**Endurecimento:** Definir uma baseline de segurança versionada e aplicá-la via Infrastructure as Code com scanning pré-deploy (Checkov, tfsec, Terrascan) para prevenir misconfigurações antes de chegarem à produção. Usar guardrails preventivos (SCPs, Azure Policy, GCP Organization Policies) que impeçam configurações inseguras, complementando a detecção. Automatizar remediação de desvios de baixo risco e exigir aprovação para exceções documentadas. Integrar CSPM ao ciclo de vida de mudanças para que cada novo recurso já nasça avaliado.

**Referências:**
- OWASP Top 10 2021 A05 Security Misconfiguration - https://owasp.org/Top10/A05_2021-Security_Misconfiguration/
- CIS Benchmarks - https://www.cisecurity.org/cis-benchmarks
- NIST SP 800-53 Rev.5 CM-6 Configuration Settings - https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final
- Prowler - https://github.com/prowler-cloud/prowler
- Google Cloud Security Command Center - https://cloud.google.com/security-command-center/docs

### Gestão de Segredos na Nuvem (Cloud Secrets Management)

**Classificação:** `defensiva`

**O que é:** Práticas e serviços para armazenar, distribuir, rotacionar e auditar credenciais, chaves de API e tokens de forma segura, evitando segredos embutidos em código e configurações.

**Como funciona:** Segredos embutidos em código-fonte, imagens de contêiner, variáveis de ambiente em texto claro ou repositórios Git ficam expostos a qualquer um com acesso de leitura e persistem no histórico de commits mesmo após remoção. Serviços gerenciados (AWS Secrets Manager, GCP Secret Manager, Azure Key Vault, HashiCorp Vault) armazenam segredos criptografados, controlam acesso via IAM, registram cada acesso em auditoria e suportam rotação automática. A entrega segura em runtime usa a identidade da carga (IAM role, workload identity) para buscar o segredo sob demanda, evitando persistência do valor. Chaves de acesso de longa duração são o maior risco porque não expiram sozinhas; segredos vazados em repositórios públicos são varridos e abusados em minutos por bots.

**Detecção:** Executar varredura de segredos no código e histórico (gitleaks, trufflehog, detect-secrets, GitHub secret scanning/push protection) em CI/CD e pre-commit. Monitorar logs de acesso ao cofre de segredos por leituras anômalas e alertar sobre segredos que nunca rotacionam. Detectar chaves de acesso de longa duração via IAM credential reports e sinalizar credenciais em variáveis de ambiente de funções/contêineres.

**Endurecimento:** Nunca versionar segredos: usar um cofre gerenciado e injetar via identidade de workload em runtime. Habilitar rotação automática e curta expiração; preferir credenciais temporárias (STS/OIDC federation) a chaves estáticas. Aplicar menor privilégio nas políticas de acesso ao cofre, criptografia com KMS gerenciada pelo cliente e auditoria de acesso. Adicionar push protection e scanning no pipeline; se um segredo vazar, tratar como comprometido e rotacionar imediatamente, não apenas remover do histórico.

**Referências:**
- CWE-798 Use of Hard-coded Credentials - https://cwe.mitre.org/data/definitions/798.html
- CWE-522 Insufficiently Protected Credentials - https://cwe.mitre.org/data/definitions/522.html
- OWASP Top 10 2021 A07 Identification and Authentication Failures - https://owasp.org/Top10/A07_2021-Identification_and_Authentication_Failures/
- OWASP Secrets Management Cheat Sheet - https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html
- NIST SP 800-57 Key Management - https://csrc.nist.gov/pubs/sp/800/57/pt1/r5/final
- MITRE ATT&CK T1552 Unsecured Credentials - https://attack.mitre.org/techniques/T1552/

### IAM e Princípio do Menor Privilégio (Least Privilege)

**Classificação:** `defensiva`

**O que é:** Prática de conceder a cada identidade (usuário, role, service account) apenas as permissões estritamente necessárias para sua função, minimizando o raio de impacto de credenciais comprometidas.

**Como funciona:** Políticas de IAM na nuvem são avaliadas combinando permissões explícitas (allow) e negações (deny), com deny sempre prevalecendo; políticas excessivamente amplas usam curingas como Action: '*' ou Resource: '*' que concedem acesso muito além do necessário. Identidades super-permissionadas ampliam o raio de impacto: se uma credencial vaza ou uma função serverless é comprometida, o atacante herda todas as permissões da role. Permissões de escalada perigosas (ex.: iam:PassRole combinada com criação de recursos, iam:CreatePolicyVersion, sts:AssumeRole irrestrito) permitem que uma identidade de baixo privilégio se eleve a administrador. O acúmulo de permissões não utilizadas ao longo do tempo ('permission creep') e roles amplas usadas por conveniência são as causas mais comuns de exposição.

**Detecção:** Analisar políticas com ferramentas de análise de acesso (AWS IAM Access Analyzer, Access Advisor para permissões não usadas, GCP Policy Analyzer, Azure Entra Permissions Management/CIEM); sinalizar curingas em Action/Resource e ausência de condições. Revisar CloudTrail/Cloud Audit Logs para comparar permissões concedidas versus efetivamente usadas. Ferramentas como Prowler, ScoutSuite, PMapper e Cloudsplaining detectam políticas com potencial de escalada de privilégios e caminhos de ataque de identidade.

**Endurecimento:** Começar com política de negação por padrão e conceder incrementalmente com base no uso real observado. Substituir curingas por ações e ARNs específicos, adicionar condições (aws:SourceIp, aws:PrincipalOrgID, MFA) e usar permission boundaries e SCPs (Service Control Policies) como teto de permissões. Preferir roles temporárias e federação a chaves de acesso de longa duração; rotacionar e revisar acessos periodicamente removendo permissões ociosas. Segregar deveres para que nenhuma identidade única possa alterar suas próprias permissões ou desativar logging.

**Referências:**
- OWASP Top 10 2021 A01 Broken Access Control - https://owasp.org/Top10/A01_2021-Broken_Access_Control/
- CWE-250 Execution with Unnecessary Privileges - https://cwe.mitre.org/data/definitions/250.html
- CWE-269 Improper Privilege Management - https://cwe.mitre.org/data/definitions/269.html
- NIST SP 800-53 Rev.5 AC-6 Least Privilege - https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final
- AWS IAM Best Practices - https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html
- MITRE ATT&CK T1078 Valid Accounts - https://attack.mitre.org/techniques/T1078/

### Logging e Trilha de Auditoria na Nuvem (CloudTrail, Cloud Audit Logs)

**Classificação:** `defensiva`

**O que é:** Registro imutável e centralizado de todas as chamadas de API e eventos administrativos na conta de nuvem, base para detecção de ameaças, resposta a incidentes e forense.

**Como funciona:** Serviços de trilha de auditoria (AWS CloudTrail, GCP Cloud Audit Logs, Azure Monitor/Activity Log) registram quem fez qual chamada de API, quando, de onde e com qual resultado, distinguindo eventos de gerenciamento (mudanças de configuração) de eventos de dados (acesso a objetos/registros). Sem logging habilitado em todas as regiões e contas, ações maliciosas ficam invisíveis; atacantes frequentemente desativam ou apagam trilhas como técnica anti-forense. A imutabilidade e a centralização em uma conta de log dedicada com acesso restrito impedem adulteração e garantem que a evidência sobreviva ao comprometimento da conta de produção. A ausência de eventos de dados deixa lacunas para acessos a S3/storage e outras leituras sensíveis.

**Detecção:** Verificar que trilhas estão habilitadas em todas as regiões e contas da organização, com validação de integridade de arquivo de log ativada. Alertar sobre eventos de alto risco: StopLogging/DeleteTrail, mudanças em políticas IAM, criação de usuários/chaves, desativação de GuardDuty/Security Hub, e acessos root. Correlacionar em SIEM (detecção via GuardDuty, Security Command Center, Sentinel) e monitorar a própria continuidade do log — gaps de ingestão são indicador de adulteração.

**Endurecimento:** Habilitar trilha organizacional multi-região e eventos de dados para recursos sensíveis; enviar logs para uma conta de arquivamento dedicada com bucket protegido por Object Lock/retenção WORM e políticas negando exclusão. Ativar validação de integridade de log e criptografia com KMS. Restringir por SCP a capacidade de desativar logging; reter logs conforme requisitos regulatórios e forenses. Definir alertas em tempo quase real para eventos que sinalizem tentativa de encobrir rastros.

**Referências:**
- OWASP Top 10 2021 A09 Security Logging and Monitoring Failures - https://owasp.org/Top10/A09_2021-Security_Logging_and_Monitoring_Failures/
- CWE-778 Insufficient Logging - https://cwe.mitre.org/data/definitions/778.html
- CWE-223 Omission of Security-relevant Information - https://cwe.mitre.org/data/definitions/223.html
- NIST SP 800-92 Guide to Computer Security Log Management - https://csrc.nist.gov/pubs/sp/800/92/final
- AWS CloudTrail Security Best Practices - https://docs.aws.amazon.com/awscloudtrail/latest/userguide/best-practices-security.html
- MITRE ATT&CK T1562.008 Impair Defenses: Disable Cloud Logs - https://attack.mitre.org/techniques/T1562/008/

### Misconfiguração e Exposição de Buckets de Armazenamento (Public Bucket Misconfiguration)

**Classificação:** `defensiva`

**O que é:** Configuração incorreta de permissões de armazenamento de objetos (S3, GCS, Azure Blob) que torna dados sensíveis legíveis ou graváveis publicamente pela internet.

**Como funciona:** O acesso a objetos é controlado por camadas combinadas: ACLs por objeto, políticas de bucket, block public access e IAM; a exposição ocorre quando qualquer camada concede leitura/escrita a 'AllUsers' (público) ou 'AuthenticatedUsers' (qualquer conta autenticada do provedor). Concessões como AllUsers e AuthenticatedUsers no GCS/S3 são frequentemente confundidas: 'authenticated' não significa 'da minha organização', mas sim qualquer titular de conta do provedor. Buckets graváveis publicamente permitem envenenamento de conteúdo, hospedagem de malware e defacement, enquanto buckets legíveis vazam backups, PII e segredos. A enumeração externa por atacantes se dá por adivinhação de nomes previsíveis de bucket e indexação em motores de busca, sem necessidade de credenciais.

**Detecção:** Habilitar e monitorar políticas de bloqueio de acesso público (S3 Block Public Access, GCS Public Access Prevention, Azure 'Allow Blob public access' desabilitado). CSPM e ferramentas como AWS Access Analyzer for S3, Prowler, ScoutSuite e o Security Command Center sinalizam buckets com concessões públicas. Monitorar logs de acesso a objetos (S3 Server Access Logs, CloudTrail data events, GCS audit logs) para leituras anônimas e picos de download; alertar sobre criação de buckets sem criptografia ou com ACL pública.

**Endurecimento:** Ativar bloqueio de acesso público no nível da conta/organização como controle preventivo global, não apenas por bucket. Preferir acesso uniforme por IAM em vez de ACLs por objeto; usar URLs pré-assinadas de curta duração para compartilhamento controlado em vez de tornar objetos públicos. Habilitar criptografia em repouso (SSE-KMS), versionamento e políticas que exigem TLS (aws:SecureTransport) e negam Principal: '*'. Classificar dados e aplicar SCPs/organization policies que impeçam a criação de recursos públicos por padrão.

**Referências:**
- OWASP Top 10 2021 A05 Security Misconfiguration - https://owasp.org/Top10/A05_2021-Security_Misconfiguration/
- CWE-732 Incorrect Permission Assignment for Critical Resource - https://cwe.mitre.org/data/definitions/732.html
- CWE-284 Improper Access Control - https://cwe.mitre.org/data/definitions/284.html
- AWS S3 Block Public Access - https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html
- Google Cloud Storage Public Access Prevention - https://cloud.google.com/storage/docs/public-access-prevention
- MITRE ATT&CK T1530 Data from Cloud Storage - https://attack.mitre.org/techniques/T1530/

### Modelo de Responsabilidade Compartilhada (Shared Responsibility Model)

**Classificação:** `defensiva`

**O que é:** Framework conceitual que divide as obrigações de segurança entre o provedor de nuvem (segurança DA nuvem) e o cliente (segurança NA nuvem), variando conforme o modelo de serviço (IaaS/PaaS/SaaS).

**Como funciona:** O provedor é responsável pela segurança física dos data centers, hipervisor, hardware e infraestrutura de rede subjacente, enquanto o cliente é responsável por configuração, dados, IAM, controle de acesso, criptografia no nível da aplicação e patching do que gerencia. A fronteira da responsabilidade desliza conforme o modelo: em IaaS o cliente gerencia SO, runtime e aplicação; em PaaS o provedor assume o SO e runtime; em SaaS o cliente basicamente gerencia identidades, dados e configurações de compartilhamento. A maioria dos incidentes de nuvem decorre de erro do cliente (misconfiguração, credenciais expostas) e não de falha do provedor, pois clientes frequentemente presumem que o provedor cobre camadas que na verdade são de responsabilidade deles. Entender essa fronteira é pré-requisito para desenhar controles corretos e evitar lacunas de cobertura.

**Detecção:** Auditar a matriz de responsabilidade documentada de cada serviço utilizado contra os controles efetivamente implementados; identificar 'zonas cinzentas' onde nenhuma das partes assumiu um controle. Ferramentas de CSPM (AWS Config, GCP Security Command Center, Azure Defender for Cloud, Prowler, ScoutSuite) revelam configurações sob responsabilidade do cliente que estão inseguras. Revisar contratos, SLAs e documentação do provedor para mapear explicitamente as fronteiras por serviço.

**Endurecimento:** Documentar uma matriz RACI de segurança por serviço de nuvem consumido; nunca presumir que o provedor cobre patching de SO em IaaS ou controle de acesso a dados em SaaS. Implementar controles compensatórios nas camadas do cliente: criptografia gerenciada pelo cliente, MFA, políticas IAM restritivas e logging. Treinar equipes para reconhecer que configuração e dados são quase sempre responsabilidade do cliente. Revisar a matriz sempre que adotar um novo serviço, pois o ponto da fronteira muda entre IaaS, PaaS e SaaS.

**Referências:**
- CSA Cloud Controls Matrix (CCM) v4 - https://cloudsecurityalliance.org/research/cloud-controls-matrix
- NIST SP 800-145 The NIST Definition of Cloud Computing - https://csrc.nist.gov/pubs/sp/800/145/final
- NIST SP 800-144 Guidelines on Security and Privacy in Public Cloud Computing - https://csrc.nist.gov/pubs/sp/800/144/final
- AWS Shared Responsibility Model - https://aws.amazon.com/compliance/shared-responsibility-model/
- Microsoft Azure Shared Responsibility - https://learn.microsoft.com/azure/security/fundamentals/shared-responsibility

### Segurança de Contêineres e Orquestração Gerenciada na Nuvem (Kubernetes/EKS/GKE/AKS)

**Classificação:** `defensiva`

**O que é:** Controles de segurança para cargas conteinerizadas e clusters Kubernetes gerenciados na nuvem, cobrindo RBAC do cluster, identidade de workload, imagens, admissão e isolamento de rede.

**Como funciona:** Clusters Kubernetes gerenciados integram o RBAC do cluster com o IAM do provedor via mapeamento de identidade (IRSA na AWS, Workload Identity no GKE/AKS), de modo que um pod pode assumir permissões de nuvem; bindings excessivos concedem a pods acesso amplo à conta. O plano de controle exposto, service accounts com token montado por padrão e permissões cluster-admin amplas ampliam o impacto de um pod comprometido. Imagens de contêiner carregam dependências e potenciais vulnerabilidades e segredos embutidos, formando vetor de supply chain; sem controle de admissão, imagens não confiáveis executam livremente. A falta de network policies deixa o tráfego pod-a-pod totalmente aberto, facilitando movimentação lateral dentro do cluster após um comprometimento inicial.

**Detecção:** Escanear imagens por vulnerabilidades e segredos (Trivy, Grype, Clair) em CI/CD e no registro. Auditar RBAC por bindings cluster-admin e service accounts super-permissionadas (kube-bench, kubeaudit, Polaris); verificar exposição do API server. Habilitar audit logs do Kubernetes e detecção de runtime (Falco, GKE/Defender for Containers) para comportamento anômalo de pods; validar mapeamentos IRSA/Workload Identity por privilégio excessivo.

**Endurecimento:** Aplicar menor privilégio no RBAC do cluster e no IAM mapeado por workload; desabilitar automount de token de service account quando não necessário. Impor controle de admissão (OPA Gatekeeper, Kyverno, Pod Security Admission) exigindo imagens assinadas de registros confiáveis, non-root e sem privilégios elevados. Definir network policies default-deny e segmentar namespaces; manter o plano de controle privado e o cluster atualizado. Escanear imagens antes do deploy e usar runtime security para detectar escapes e execução anômala.

**Referências:**
- NIST SP 800-190 Application Container Security Guide - https://csrc.nist.gov/pubs/sp/800/190/final
- OWASP Kubernetes Security Cheat Sheet - https://cheatsheetseries.owasp.org/cheatsheets/Kubernetes_Security_Cheat_Sheet.html
- CIS Kubernetes Benchmark - https://www.cisecurity.org/benchmark/kubernetes
- MITRE ATT&CK Containers Matrix - https://attack.mitre.org/matrices/enterprise/containers/
- CWE-732 Incorrect Permission Assignment for Critical Resource - https://cwe.mitre.org/data/definitions/732.html
- Kubernetes RBAC Good Practices - https://kubernetes.io/docs/concepts/security/rbac-good-practices/

### Segurança Serverless e de Funções (Serverless / FaaS Security)

**Classificação:** `defensiva`

**O que é:** Conjunto de riscos e controles específicos de funções serverless (Lambda, Cloud Functions, Azure Functions), onde superfícies de gatilho por eventos, roles de execução e dependências dominam o modelo de ameaça.

**Como funciona:** Funções serverless são disparadas por eventos de múltiplas fontes (HTTP, filas, uploads em storage, streams), e cada fonte é um vetor de injeção onde entrada não confiável chega à função com estruturas variadas e difíceis de validar uniformemente. Cada função executa com uma role de execução; roles super-permissionadas tornam uma função comprometida um pivô para a conta inteira. Segredos em variáveis de ambiente da função ficam legíveis por quem tiver acesso à configuração ou a um comprometimento de runtime. Dependências de terceiros ampliam a superfície de supply chain, e a natureza efêmera dificulta a instrumentação de segurança tradicional baseada em host.

**Detecção:** Escanear código e dependências de funções (SCA como OWASP Dependency-Check, npm/pip audit, Snyk) em CI/CD; revisar as roles de execução por permissões excessivas com IAM Access Analyzer. Monitorar logs de invocação (CloudWatch, Cloud Logging) por erros, timeouts anômalos e padrões de invocação incomuns. Verificar variáveis de ambiente por segredos em texto claro e usar CSPM para funções com configuração insegura (URLs públicas, ausência de autenticação no gateway).

**Endurecimento:** Atribuir uma role de execução mínima e distinta por função (uma role por função, não compartilhada). Validar e sanitizar rigorosamente cada evento de entrada conforme seu schema; tratar todo trigger como não confiável. Buscar segredos de um cofre em runtime em vez de variáveis de ambiente; fixar e verificar dependências, com atualização contínua. Definir timeouts e limites de concorrência mínimos necessários, autenticar gateways de API na frente das funções e habilitar tracing para observabilidade.

**Referências:**
- OWASP Serverless Top 10 - https://owasp.org/www-project-serverless-top-10/
- CWE-829 Inclusion of Functionality from Untrusted Control Sphere - https://cwe.mitre.org/data/definitions/829.html
- CWE-20 Improper Input Validation - https://cwe.mitre.org/data/definitions/20.html
- AWS Lambda Security Best Practices - https://docs.aws.amazon.com/lambda/latest/dg/lambda-security.html
- NIST SP 800-204 Security Strategies for Microservices - https://csrc.nist.gov/pubs/sp/800/204/final

### SSRF contra Endpoint de Metadata da Instância (IMDS/IMDSv2)

**Classificação:** `defensiva`

**O que é:** Abuso de uma falha de SSRF na aplicação para fazer o servidor consultar o endpoint de metadata da instância (169.254.169.254) e roubar as credenciais temporárias da role anexada.

**Como funciona:** Instâncias de computação expõem um serviço de metadados no endereço link-local 169.254.169.254 (ou metadata.google.internal) que fornece dados da instância e, crucialmente, credenciais temporárias da role IAM associada. Se a aplicação possui SSRF — busca uma URL fornecida pelo usuário sem validação — o atacante induz o servidor a requisitar o caminho de credenciais do IMDS e exfiltra as chaves temporárias, herdando as permissões da role. O IMDSv1 é vulnerável por responder a qualquer GET simples, enquanto o IMDSv2 exige um fluxo de sessão orientado a token (PUT para obter token, com header e limite de TTL/hop count) que a maioria dos vetores de SSRF cegos não consegue completar. O risco é ampliado quando a role da instância é super-permissionada, transformando um SSRF em comprometimento amplo da conta.

**Detecção:** Inspecionar código por chamadas HTTP a URLs controladas pelo usuário sem validação de destino (fetch/curl/http client com host dinâmico). Monitorar logs de aplicação e de rede por requisições de saída ao 169.254.169.254 ou ao caminho de credenciais, e correlacionar uso das credenciais da instância a partir de IPs externos incomuns via CloudTrail (chamadas de API com credenciais de role de instância originadas fora da VPC). GuardDuty possui detecção específica (UnauthorizedAccess:IAMUser/InstanceCredentialExfiltration) para credenciais de instância usadas de fora.

**Endurecimento:** Exigir IMDSv2 e desabilitar IMDSv1 (HttpTokens=required); definir hop limit=1 para impedir que contêineres/proxies alcancem o metadata. Corrigir a causa raiz do SSRF: validar e usar allowlist de destinos, bloquear ranges link-local/privados (169.254.0.0/16, RFC 1918) e resolver DNS antes de conectar para evitar rebinding. Aplicar menor privilégio nas roles de instância para limitar o impacto de um vazamento, e usar egress filtering/network policies bloqueando acesso ao IMDS por cargas que não precisem dele.

**Referências:**
- CWE-918 Server-Side Request Forgery (SSRF) - https://cwe.mitre.org/data/definitions/918.html
- OWASP Top 10 2021 A10 Server-Side Request Forgery - https://owasp.org/Top10/A10_2021-Server-Side_Request_Forgery_(SSRF)/
- AWS Use IMDSv2 - https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html
- OWASP SSRF Prevention Cheat Sheet - https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html
- MITRE ATT&CK T1552.005 Cloud Instance Metadata API - https://attack.mitre.org/techniques/T1552/005/
- Google Cloud Metadata Server Security - https://cloud.google.com/compute/docs/metadata/overview

## Contêineres, Orquestração e Cadeia de Suprimentos

### Ataques de cadeia de suprimentos: dependências maliciosas, typosquatting e dependency confusion

**Classificação:** `defensiva`

**O que é:** Família de ataques em que código malicioso entra na aplicação por meio de pacotes de terceiros falsos, comprometidos ou resolvidos incorretamente do registro público.

**Como funciona:** Typosquatting publica pacotes com nomes parecidos com bibliotecas populares, contando com erros de digitação. Dependency confusion explora gerenciadores que preferem a versão mais nova entre registros público e privado: um atacante publica no registro público um pacote com o mesmo nome de um pacote interno e uma versão maior, fazendo o build puxar o malicioso. Pacotes também podem ser comprometidos por sequestro de conta do mantenedor ou commits maliciosos. O código malicioso costuma executar em scripts de instalação (postinstall) ou no import, exfiltrando segredos e variáveis de ambiente do build.

**Detecção:** Use SCA (Snyk, Dependabot, OSV-Scanner, Socket) para detectar dependências novas, comportamentos suspeitos (scripts de install, acesso a rede/FS), e nomes semelhantes. Revise lockfiles em cada PR; monitore avisos OSV/GitHub Advisory. Alerte para pacotes internos que apareçam no registro público e para saltos de versão anômalos; inspecione tráfego de rede durante builds.

**Endurecimento:** Fixe versões e use lockfiles com verificação de integridade (hash); configure scoping/namespaces e resolução que priorize o registro privado, bloqueando pacotes públicos com nomes internos. Use um registro proxy/allowlist (Artifactory, GitHub Packages) e --ignore-scripts quando viável; verifique assinaturas/proveniência quando disponíveis. Revise novas dependências, limite segredos disponíveis no build e execute builds em ambiente isolado com egress restrito.

**Referências:**
- OWASP Top 10 2021 A08 Software and Data Integrity Failures — https://owasp.org/Top10/A08_2021-Software_and_Data_Integrity_Failures/
- CWE-1357 Reliance on Insufficiently Trustworthy Component — https://cwe.mitre.org/data/definitions/1357.html
- CWE-829 Inclusion of Functionality from Untrusted Control Sphere — https://cwe.mitre.org/data/definitions/829.html
- OWASP Dependency Confusion — https://owasp.org/www-community/attacks/
- OSV Scanner — https://google.github.io/osv-scanner/
- MITRE ATT&CK T1195 Supply Chain Compromise — https://attack.mitre.org/techniques/T1195/

### Componentes Vulneráveis e Desatualizados (SCA / Vulnerable and Outdated Components)

**Classificação:** `defensiva`

**O que é:** Aplicações herdam as vulnerabilidades das bibliotecas e frameworks que utilizam, incluindo dependências transitivas. Sem inventário e monitoramento contínuo (Análise de Composição de Software), componentes com falhas conhecidas permanecem em produção e tornam-se um dos vetores mais explorados.

**Como funciona:** O código moderno é majoritariamente composto por dependências de terceiros, muitas delas transitivas e invisíveis sem ferramentas. Quando uma vulnerabilidade conhecida (CVE) é publicada para um componente, todas as aplicações que o usam em versão afetada ficam expostas, mesmo que o código próprio esteja correto. O problema não é uma falha nova, e sim a falta de visibilidade e de um processo para descobrir, priorizar e atualizar componentes afetados. A Análise de Composição de Software (SCA) inventaria dependências (diretas e transitivas), correlaciona com bases de vulnerabilidades e sinaliza versões afetadas. Priorização eficaz combina severidade (CVSS), exploração conhecida (KEV) e probabilidade (EPSS) com o contexto de uso real do componente.

**Detecção:** Execute SCA continuamente na esteira e sobre artefatos em produção, gerando e mantendo um SBOM. Correlacione o inventário com feeds de CVE/KEV e priorize por severidade, exploração ativa e alcançabilidade do componente no código. Monitore o surgimento de novas CVEs para dependências já em uso, não apenas no momento do build. Alerte para componentes sem manutenção ou fora de suporte.

**Endurecimento:** Mantenha um inventário autoritativo (SBOM) de dependências diretas e transitivas e integre SCA como gate na pipeline. Fixe versões e use lockfiles para builds reprodutíveis; atualize regularmente com processo de teste. Remova dependências não utilizadas e prefira componentes mantidos e de fontes confiáveis. Estabeleça SLAs de correção baseados em risco (severidade, KEV, EPSS, exposição) e um processo de resposta para CVEs críticas. Combine com verificação de integridade/proveniência para evitar componentes adulterados.

**Referências:**
- OWASP Top 10 A06:2021 Vulnerable and Outdated Components
- OWASP Dependency-Check
- CWE-1104: Use of Unmaintained Third Party Components
- CISA Known Exploited Vulnerabilities (KEV) Catalog

### Controle de acesso baseado em papéis do Kubernetes (RBAC)

**Classificação:** `defensiva`

**O que é:** Modelo de autorização do Kubernetes que concede permissões a usuários e ServiceAccounts sobre recursos da API, cujo excesso permite escalonamento de privilégio no cluster.

**Como funciona:** O API server autoriza cada requisição avaliando Roles/ClusterRoles (verbos sobre recursos) vinculados por RoleBindings/ClusterRoleBindings a sujeitos. Concessões amplas criam caminhos de escalonamento: 'get/list' em secrets expõe credenciais; 'create pods' permite montar tokens e hostPath; 'pods/exec' dá shell em cargas privilegiadas; 'escalate/bind', 'impersonate' e curingas (*) permitem herdar ou forjar permissões. ServiceAccounts têm tokens montados por padrão nos Pods, então um Pod comprometido herda seus direitos, tornando o mínimo privilégio crítico.

**Detecção:** Audite bindings com kubectl-who-can, rbac-tool, KubiScan, rakkess e Kubescape; procure ClusterRoleBindings para cluster-admin, curingas em verbos/recursos, acesso a secrets, exec e impersonate. Habilite audit logging do API server e alerte para uso de verbos sensíveis, criação de bindings privilegiados e uso de tokens de ServiceAccount fora do cluster. Revise ServiceAccounts default com permissões.

**Endurecimento:** Aplique privilégio mínimo: Roles namespaced específicas, sem curingas, sem cluster-admin para cargas. Desabilite automountServiceAccountToken quando não necessário e use tokens de curta duração (projected/bound tokens). Separe deveres, revise periodicamente, use namespaces por equipe/ambiente. Restrinja verbos perigosos (escalate, bind, impersonate, exec, portforward); integre admission control e OIDC para usuários humanos em vez de tokens estáticos.

**Referências:**
- Kubernetes RBAC Authorization — https://kubernetes.io/docs/reference/access-authn-authz/rbac/
- OWASP Kubernetes Top 10 K03 Overly Permissive RBAC — https://owasp.org/www-project-kubernetes-top-ten/
- CWE-269 Improper Privilege Management — https://cwe.mitre.org/data/definitions/269.html
- CWE-266 Incorrect Privilege Assignment — https://cwe.mitre.org/data/definitions/266.html
- NSA/CISA Kubernetes Hardening Guide — https://media.defense.gov/2022/Aug/29/2003066362/-1/-1/0/CTR_KUBERNETES_HARDENING_GUIDANCE_1.2_20220829.PDF

### Escaneamento de vulnerabilidades em imagens de contêiner (Image Scanning)

**Classificação:** `defensiva`

**O que é:** Análise estática de imagens de contêiner para identificar pacotes de SO e dependências de aplicação com vulnerabilidades conhecidas (CVEs) antes e depois da publicação.

**Como funciona:** O scanner extrai o manifesto e cada camada (layer) da imagem, inventaria os pacotes instalados (gerenciadores de SO como apk/apt/rpm e ecossistemas como npm, pip, Maven) e correlaciona versões contra bancos de vulnerabilidades (NVD, GitHub Advisory, avisos de distros). A profundidade depende da qualidade dos metadados: imagens 'distroless' ou construídas do zero têm menos ruído, enquanto imagens gordas herdam CVEs de camadas-base desatualizadas. Vulnerabilidades também surgem de binários copiados fora do gerenciador de pacotes, que muitos scanners só detectam por análise de artefato ou SBOM. O resultado é priorizado por severidade, exploitabilidade (EPSS/KEV) e se há correção disponível (fixed version).

**Detecção:** Integre scanners como Trivy, Grype, Clair, Snyk ou Docker Scout no build e em varredura contínua do registro; falhe o pipeline por política de severidade. Indicadores: imagens sem digest imutável, tags 'latest', camadas-base antigas, alto volume de CVEs críticos com fix disponível, pacotes fora do gerenciador. Reescaneie periodicamente imagens já publicadas, pois novos CVEs surgem após o build; monitore CISA KEV e EPSS para priorização.

**Endurecimento:** Use imagens-base mínimas (distroless, Alpine, scratch) e multi-stage builds; fixe imagens por digest sha256 e não por tag mutável. Atualize camadas-base regularmente e rebuild automatizado. Aplique gate de admissão que bloqueie imagens com CVE crítico sem exceção justificada; mantenha inventário/SBOM por imagem; remova ferramentas de build e segredos da imagem final; assine e verifique proveniência.

**Referências:**
- OWASP Top 10 2021 A06 Vulnerable and Outdated Components — https://owasp.org/Top10/A06_2021-Vulnerable_and_Outdated_Components/
- CWE-1104 Use of Unmaintained Third Party Components — https://cwe.mitre.org/data/definitions/1104.html
- NIST SP 800-190 Application Container Security Guide — https://csrc.nist.gov/pubs/sp/800/190/final
- CIS Docker Benchmark — https://www.cisecurity.org/benchmark/docker
- Trivy documentation — https://trivy.dev/latest/docs/

### Exposição do daemon e socket do Docker (Docker Socket / Daemon Exposure)

**Classificação:** `defensiva`

**O que é:** Configuração insegura em que o socket ou a API TCP do Docker fica acessível sem autenticação, concedendo controle equivalente a root no host.

**Como funciona:** O daemon Docker roda como root e sua API (socket unix /var/run/docker.sock ou TCP 2375/2376) permite criar contêineres com montagens e privilégios arbitrários. Quem acessa o socket pode iniciar um contêiner que monta o filesystem do host e obtém controle total, tornando o acesso ao socket equivalente a root. Riscos surgem ao montar o socket dentro de contêineres (comum em ferramentas de CI/build), ao expor a API TCP sem TLS/autenticação na rede, ou ao adicionar usuários ao grupo docker. Um serviço comprometido com acesso ao socket escala imediatamente para o host.

**Detecção:** Verifique bind mounts de docker.sock em contêineres e portas 2375/2376 expostas (sem mTLS); escaneie com Docker Bench for Security. Monitore acesso ao socket e criação de contêineres privilegiados/com hostPath; audite membros do grupo docker. Alerte para chamadas à API a partir de cargas de trabalho e para daemon escutando em 0.0.0.0.

**Endurecimento:** Não monte docker.sock em contêineres de aplicação; para builds use alternativas sem daemon privilegiado (BuildKit rootless, Kaniko, Buildah). Não exponha a API TCP; se necessário, use TLS mútuo e restrição de rede. Prefira modo rootless do Docker/Podman; limite o grupo docker; use socket proxies com allowlist de endpoints para ferramentas que precisem de acesso restrito. Aplique controles de host (firewall, RBAC) e monitoramento em runtime.

**Referências:**
- Docker Daemon Security — https://docs.docker.com/engine/security/protect-access/
- CWE-306 Missing Authentication for Critical Function — https://cwe.mitre.org/data/definitions/306.html
- CWE-419 Unprotected Primary Channel — https://cwe.mitre.org/data/definitions/419.html
- MITRE ATT&CK T1610 Deploy Container — https://attack.mitre.org/techniques/T1610/
- CIS Docker Benchmark — https://www.cisecurity.org/benchmark/docker
- Docker Rootless mode — https://docs.docker.com/engine/security/rootless/

### Fuga de contêiner (Container Escape)

**Classificação:** `laboratorio_autorizado`

**O que é:** Classe de ataques em que um processo dentro do contêiner rompe o isolamento e obtém execução ou acesso ao host subjacente.

**Como funciona:** O isolamento de contêiner é lógico (namespaces, cgroups, capabilities, LSM) sobre um kernel compartilhado; configurações fracas ou bugs no runtime quebram essa fronteira. Vetores conceituais incluem contêiner privileged, montagem do socket do Docker (/var/run/docker.sock), hostPath sensível, CAP_SYS_ADMIN permitindo mounts/cgroup release_agent, e falhas em runc/containerd (ex.: CVE-2019-5736 sobrescrevendo o binário runc, CVE-2024-21626 via file descriptor vazado). Vulnerabilidades de kernel (ex.: Dirty Pipe) também elevam privilégio no host. O estudo em laboratório serve para entender pré-condições e validar controles, não para uso contra terceiros.

**Detecção:** Runtime security (Falco, Tetragon, Tracee) alertando para: mount de sistemas de arquivos, escrita em release_agent de cgroup, acesso a /var/run/docker.sock de dentro de um pod, spawn de shell a partir de processos inesperados, ptrace cross-namespace e uso anômalo de syscalls. Verifique auditd/kernel logs no host; correlacione com eventos do Kubernetes API. Escaneie configuração para privileged, hostPath, capabilities perigosas.

**Endurecimento:** Nunca rode privileged nem monte o docker.sock em cargas de trabalho; drop de capabilities; seccomp/AppArmor; user namespaces; rootfs read-only. Mantenha runtime (runc/containerd) e kernel atualizados; considere sandboxes de isolamento reforçado (gVisor, Kata Containers) para cargas não confiáveis. Restrinja hostPath/hostPID/hostNetwork via admission control; aplique Pod Security Standard 'restricted' e monitoramento em runtime.

**Referências:**
- MITRE ATT&CK T1611 Escape to Host — https://attack.mitre.org/techniques/T1611/
- CWE-693 Protection Mechanism Failure — https://cwe.mitre.org/data/definitions/693.html
- CVE-2019-5736 runc — https://nvd.nist.gov/vuln/detail/CVE-2019-5736
- CVE-2024-21626 runc leaked fd — https://nvd.nist.gov/vuln/detail/CVE-2024-21626
- NIST SP 800-190 — https://csrc.nist.gov/pubs/sp/800/190/final
- gVisor — https://gvisor.dev/docs/

### Gestão de segredos no Kubernetes (Secrets Management)

**Classificação:** `defensiva`

**O que é:** Práticas para armazenar, distribuir e proteger credenciais no Kubernetes, cujo padrão nativo oferece apenas codificação base64, não criptografia.

**Como funciona:** Objetos Secret são armazenados no etcd e apenas codificados em base64, legíveis por qualquer sujeito com 'get secrets' via RBAC e visíveis em texto claro se o etcd não estiver criptografado em repouso. Secrets montados como variáveis de ambiente vazam facilmente em logs, dumps de processo e crash reports, e ficam expostos a qualquer processo do contêiner. Sem criptografia via KMS provider e sem RBAC restrito, um comprometimento de nó, backup de etcd ou ServiceAccount amplo expõe todas as credenciais. Soluções externas (Vault, cloud secret managers) injetam segredos de curta duração sob demanda.

**Detecção:** Verifique se EncryptionConfiguration com KMS está habilitada no API server; audite RBAC de 'get/list secrets'. Escaneie manifestos e repositórios por segredos hardcoded e base64 com gitleaks, trufflehog, Checkov. Monitore acesso a secrets no audit log e detecte segredos passados como env em specs. Alerte para backups de etcd sem criptografia.

**Endurecimento:** Habilite encryption-at-rest com KMS provider; restrinja RBAC de secrets ao mínimo e por namespace. Prefira montagem como arquivo (tmpfs) a variável de ambiente; use External Secrets Operator, HashiCorp Vault, Sealed Secrets ou secret managers da cloud com rotação e tokens de curta duração. Nunca comite segredos em Git; use CSI Secret Store; audite e rotacione credenciais; desabilite automount de token onde não usado.

**Referências:**
- Kubernetes Secrets — https://kubernetes.io/docs/concepts/configuration/secret/
- Kubernetes Encrypting Secret Data at Rest — https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/
- OWASP Top 10 2021 A02 Cryptographic Failures — https://owasp.org/Top10/A02_2021-Cryptographic_Failures/
- CWE-312 Cleartext Storage of Sensitive Information — https://cwe.mitre.org/data/definitions/312.html
- CWE-798 Use of Hard-coded Credentials — https://cwe.mitre.org/data/definitions/798.html

### Hardening de contêiner: usuário não-root, capabilities e seccomp

**Classificação:** `defensiva`

**O que é:** Conjunto de controles do runtime que reduz a superfície de ataque e o impacto de comprometimento executando o processo com o mínimo de privilégios do kernel.

**Como funciona:** Contêineres compartilham o kernel do host; privilégios excessivos ampliam o raio de impacto de uma falha na aplicação. Rodar como root dentro do contêiner mapeia (sem user namespaces) para root no host, e Linux capabilities concedem poderes específicos (ex.: CAP_SYS_ADMIN, CAP_NET_RAW) que podem viabilizar fuga ou abuso. Perfis seccomp filtram chamadas de sistema (syscalls) permitidas, e LSMs como AppArmor/SELinux confinam acessos a arquivos, rede e recursos. A combinação de usuário não-root, drop de capabilities, no-new-privileges e rootfs somente-leitura implementa privilégio mínimo em profundidade.

**Detecção:** Audite manifestos e Dockerfiles: ausência de instrução USER, containers com privileged=true, cap_add amplos, seccomp=unconfined, sem readOnlyRootFilesystem. Ferramentas: Docker Bench for Security, kube-bench, Trivy misconfig, Checkov, Kubescape. Em runtime, alerte com Falco para processos rodando como uid 0, tentativas de mount, ou uso de syscalls sensíveis; verifique securityContext ausente nos Pods.

**Endurecimento:** Defina USER não-root no Dockerfile e runAsNonRoot/runAsUser no securityContext; faça cap_drop ALL e adicione apenas as capabilities necessárias. Aplique perfil seccomp RuntimeDefault, AppArmor/SELinux, allowPrivilegeEscalation=false, readOnlyRootFilesystem=true e volumes emptyDir para escrita temporária. Evite privileged e hostPID/hostNetwork/hostPath; habilite user namespaces quando possível; imponha via Pod Security Admission ou política (Kyverno/OPA Gatekeeper).

**Referências:**
- NIST SP 800-190 — https://csrc.nist.gov/pubs/sp/800/190/final
- CWE-250 Execution with Unnecessary Privileges — https://cwe.mitre.org/data/definitions/250.html
- CWE-269 Improper Privilege Management — https://cwe.mitre.org/data/definitions/269.html
- Docker seccomp security profiles — https://docs.docker.com/engine/security/seccomp/
- Kubernetes Security Context — https://kubernetes.io/docs/tasks/configure-pod-container/security-context/
- MITRE ATT&CK T1611 Escape to Host — https://attack.mitre.org/techniques/T1611/

### Padrões de segurança de Pod e controle de admissão (Pod Security Standards / Admission Control)

**Classificação:** `defensiva`

**O que é:** Mecanismos que validam ou mutam objetos na entrada da API do Kubernetes para impor configurações seguras de Pod antes que sejam criados.

**Como funciona:** O API server passa cada objeto por admission controllers (validating/mutating) antes de persistir. O Pod Security Admission embutido aplica os Pod Security Standards em três níveis (privileged, baseline, restricted) por namespace, bloqueando ou avisando sobre Pods com privileged, hostPath, hostNetwork, escalonamento de privilégio, etc. Ferramentas de policy-as-code (Kyverno, OPA Gatekeeper) estendem isso com regras arbitrárias, verificação de proveniência/assinatura de imagens, labels obrigatórios e mutações de securityContext. A PodSecurityPolicy legada foi removida no Kubernetes 1.25, substituída por PSA e admission externos.

**Detecção:** Confirme que PodSecurityAdmission está habilitado e que namespaces têm labels enforce/audit/warn adequados; sem enforcement, cargas inseguras passam. Audite com Kubescape, kube-bench, Polaris. Revise logs de admissão para violações e exceções; verifique webhooks de admissão com failurePolicy e timeouts que possam falhar aberto. Alerte para namespaces em nível 'privileged'.

**Endurecimento:** Aplique nível 'restricted' por padrão nos namespaces de aplicação e 'baseline' no mínimo; use exceções controladas apenas onde justificado. Adote Kyverno/Gatekeeper para bloquear imagens não assinadas, forçar securityContext, limites de recursos e registries permitidos. Configure webhooks com failurePolicy=Fail para regras críticas, com alta disponibilidade; versione políticas em Git (GitOps) e teste em modo audit antes de enforce.

**Referências:**
- Kubernetes Pod Security Standards — https://kubernetes.io/docs/concepts/security/pod-security-standards/
- Kubernetes Pod Security Admission — https://kubernetes.io/docs/concepts/security/pod-security-admission/
- OWASP Kubernetes Top 10 — https://owasp.org/www-project-kubernetes-top-ten/
- CWE-1188 Insecure Default Initialization of Resource — https://cwe.mitre.org/data/definitions/1188.html
- Kyverno Policies — https://kyverno.io/policies/
- OPA Gatekeeper — https://open-policy-agent.github.io/gatekeeper/website/docs/

### Políticas de rede do Kubernetes (Network Policies)

**Classificação:** `defensiva`

**O que é:** Recurso que define regras de firewall L3/L4 entre Pods e namespaces, limitando comunicação e movimento lateral dentro do cluster.

**Como funciona:** Por padrão, todo Pod pode se comunicar com qualquer outro no cluster (modelo flat), o que facilita movimento lateral após um comprometimento inicial. NetworkPolicies, aplicadas por um CNI compatível (Calico, Cilium, Weave), selecionam Pods por labels e definem ingress/egress permitidos por pod, namespace ou bloco CIDR e porta. Sem uma política de negação padrão, adicionar policies a alguns Pods deixa os demais abertos; e sem CNI compatível, o objeto é aceito mas não aplicado. Políticas de egress são essenciais para conter exfiltração e callbacks de C2.

**Detecção:** Verifique se o CNI aplica NetworkPolicy (nem todos aplicam); audite namespaces sem policy default-deny com Kubescape, kube-bench, Netpol tools ou Cilium Hubble. Use observabilidade de fluxo (Hubble, Calico flow logs) para mapear comunicação real e detectar conexões laterais inesperadas e egress para destinos externos suspeitos. Alerte para Pods sem seletor coberto por qualquer policy.

**Endurecimento:** Adote default-deny de ingress e egress por namespace e permita explicitamente apenas fluxos necessários (allowlist). Segmente por ambiente/tier usando labels e namespaces; restrinja egress para a internet e para o metadata endpoint da cloud. Considere CNI com identidade (Cilium) para políticas L7 e mTLS via service mesh. Combine com Pod Security e RBAC para defesa em profundidade e revise policies em cada deploy.

**Referências:**
- Kubernetes Network Policies — https://kubernetes.io/docs/concepts/services-networking/network-policies/
- OWASP Kubernetes Top 10 K07 Missing Network Segmentation Controls — https://owasp.org/www-project-kubernetes-top-ten/
- CWE-668 Exposure of Resource to Wrong Sphere — https://cwe.mitre.org/data/definitions/668.html
- MITRE ATT&CK T1021 Remote Services / Lateral Movement — https://attack.mitre.org/tactics/TA0008/
- NSA/CISA Kubernetes Hardening Guide — https://media.defense.gov/2022/Aug/29/2003066362/-1/-1/0/CTR_KUBERNETES_HARDENING_GUIDANCE_1.2_20220829.PDF

### SBOM e assinatura de artefatos (Sigstore/Cosign)

**Classificação:** `defensiva`

**O que é:** Práticas de gerar inventário verificável de componentes de software (SBOM) e assinar/verificar imagens e artefatos criptograficamente para garantir integridade e proveniência.

**Como funciona:** Um SBOM (formatos CycloneDX ou SPDX) lista todos os componentes, versões e licenças de um artefato, permitindo responder rapidamente a novos CVEs (ex.: Log4Shell) e detectar dependências indevidas. A assinatura com Sigstore/Cosign associa a imagem (por digest) a uma identidade: o modo keyless usa OIDC para emitir um certificado efêmero (Fulcio) e registra a assinatura/atestação em um log de transparência imutável (Rekor), eliminando a gestão de chaves de longa duração. Verificadores no cluster (Kyverno, policy-controller) só admitem imagens com assinatura e proveniência válidas, quebrando ataques que substituem artefatos.

**Detecção:** Gere SBOM no build (Syft, Trivy) e armazene como atestação; verifique presença e validade de assinaturas com cosign verify. Audite se o admission control exige assinatura; monitore o log de transparência (Rekor) para entradas inesperadas. Alerte para imagens sem SBOM/atestação ou com assinatura de identidade não autorizada; consulte o SBOM ao surgir um novo CVE.

**Endurecimento:** Assine todas as imagens e atestações (SBOM, provenance SLSA) com Cosign keyless via OIDC do CI; imponha verificação de assinatura e proveniência no admission control (Kyverno/policy-controller) restringindo identidades e emissores permitidos. Fixe imagens por digest; publique e versione SBOMs; adote política de que artefatos não assinados são rejeitados. Integre com verificação de vulnerabilidade contínua alimentada pelo SBOM.

**Referências:**
- Sigstore / Cosign — https://docs.sigstore.dev/
- CycloneDX SBOM — https://cyclonedx.org/
- SPDX — https://spdx.dev/
- NIST SP 800-218 Secure Software Development Framework (SSDF) — https://csrc.nist.gov/pubs/sp/800/218/final
- CWE-347 Improper Verification of Cryptographic Signature — https://cwe.mitre.org/data/definitions/347.html
- CISA/NTIA SBOM — https://www.cisa.gov/sbom

### Segurança de CI/CD e pipelines

**Classificação:** `defensiva`

**O que é:** Proteção do sistema de build e entrega, cujo comprometimento permite injetar código malicioso em todos os artefatos produzidos com alta confiança implícita.

**Como funciona:** Pipelines executam código com credenciais poderosas (registries, cloud, deploy), tornando-os alvo de alto valor. Poisoned Pipeline Execution (PPE) ocorre quando um atacante influencia a definição do pipeline ou scripts executados (ex.: workflows GitHub Actions com pull_request_target combinando checkout de PR não confiável com segredos, ou Makefile/npm scripts controláveis por PR). Runners self-hosted reutilizados, segredos de longa duração expostos em logs, e dependências de ações de terceiros não fixadas (por tag mutável) ampliam o risco. Um build comprometido assina e distribui artefatos maliciosos como se fossem legítimos.

**Detecção:** Escaneie workflows por triggers perigosos (pull_request_target com checkout de código não confiável), segredos hardcoded e ações não fixadas por SHA. Ferramentas: OWASP CICD-SEC, StepSecurity Harden-Runner, Checkov, zizmor, gitleaks. Monitore logs do CI para exfiltração e acesso anômalo; audite permissões de tokens e uso de OIDC. Alerte para runners self-hosted em repositórios públicos.

**Endurecimento:** Aplique privilégio mínimo aos tokens (permissions no GitHub Actions), prefira OIDC de curta duração a segredos estáticos; fixe ações de terceiros por SHA completo. Isole runners (efêmeros, sem reuso), restrinja egress (Harden-Runner) e separe pipelines por ambiente. Exija revisão para mudanças em workflows; não exponha segredos a builds de PR não confiáveis; gere proveniência SLSA e assine artefatos; use branch protection e ambientes protegidos com aprovação.

**Referências:**
- OWASP Top 10 CI/CD Security Risks — https://owasp.org/www-project-top-10-ci-cd-security-risks/
- NIST SP 800-204D (CI/CD supply chain) — https://csrc.nist.gov/pubs/sp/800/204/d/final
- CWE-732 Incorrect Permission Assignment for Critical Resource — https://cwe.mitre.org/data/definitions/732.html
- GitHub Actions Security Hardening — https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions
- MITRE ATT&CK T1195 Supply Chain Compromise — https://attack.mitre.org/techniques/T1195/

### Segurança de Infraestrutura como Código (IaC Security — Terraform)

**Classificação:** `defensiva`

**O que é:** Análise e hardening de definições declarativas de infraestrutura para evitar que configurações inseguras sejam provisionadas em escala.

**Como funciona:** Terraform provisiona recursos de nuvem a partir de código; um erro de configuração se replica em toda a frota e persiste até correção. Problemas comuns incluem buckets/armazenamento públicos, security groups abertos (0.0.0.0/0), criptografia desabilitada, IAM excessivamente permissivo e logging ausente. O arquivo de state armazena valores em texto claro (inclusive segredos) e, se exposto ou versionado sem proteção, vaza credenciais. Módulos de terceiros e provedores não fixados introduzem risco de cadeia de suprimentos, e drift entre estado e realidade cria brechas silenciosas.

**Detecção:** Rode scanners de misconfiguration no CI: Checkov, tfsec/Trivy, Terrascan, KICS; falhe o build por política. Analise o plan antes do apply; verifique state remoto criptografado e sem segredos versionados. Detecte drift periodicamente; escaneie por segredos no código (gitleaks) e por provedores/módulos não fixados. Audite regras que exponham recursos à internet.

**Endurecimento:** Adote policy-as-code (OPA/Conftest, Sentinel) para bloquear recursos públicos, criptografia off e IAM amplo; use módulos revisados e fixados por versão/hash. Armazene state em backend remoto criptografado com controle de acesso e bloqueio; nunca comite segredos, use variáveis sensíveis e secret managers. Aplique least privilege no IAM do provisionador, revisão obrigatória de PRs de IaC e varredura contínua; habilite logging e criptografia por padrão.

**Referências:**
- OWASP Infrastructure as Code Security Cheat Sheet — https://cheatsheetseries.owasp.org/cheatsheets/Infrastructure_as_Code_Security_Cheat_Sheet.html
- CWE-1188 Insecure Default Initialization — https://cwe.mitre.org/data/definitions/1188.html
- CWE-732 Incorrect Permission Assignment for Critical Resource — https://cwe.mitre.org/data/definitions/732.html
- Checkov — https://www.checkov.io/
- Terraform State Sensitive Data — https://developer.hashicorp.com/terraform/language/state/sensitive-data
- CIS Benchmarks (cloud) — https://www.cisecurity.org/cis-benchmarks

### Segurança de runtime de contêiner (Runtime Security)

**Classificação:** `defensiva`

**O que é:** Detecção e resposta em tempo de execução a comportamentos anômalos ou maliciosos dentro de contêineres e no host, complementando controles estáticos.

**Como funciona:** Controles de build e configuração não cobrem ataques que ocorrem em execução (webshell, reverse shell, cryptomining, exploração de dependência). Ferramentas de runtime instrumentam o kernel via eBPF ou o módulo de auditoria para observar syscalls, execuções de processo, conexões de rede, escritas em arquivos e mudanças de privilégio, comparando com regras (Falco) ou políticas de comportamento esperado (drift/allowlist). Um contêiner imutável não deveria, por exemplo, spawnar um shell interativo, baixar binários ou escrever no rootfs; desvios geram alertas ou bloqueio (enforcement inline com Tetragon).

**Detecção:** Implante Falco, Tetragon, Tracee ou soluções CNAPP/EDR de contêiner; regras para: shell dentro de contêiner, conexões de saída inesperadas, leitura de secrets/tokens, escrita em diretórios sensíveis, novos binários executados, mineração. Correlacione com logs de API do Kubernetes e do host. Baseie-se em perfis de comportamento por workload e reduza falso-positivo com allowlists.

**Endurecimento:** Use imagens imutáveis e rootfs read-only para tornar drift detectável; aplique seccomp/AppArmor para reduzir syscalls disponíveis. Combine runtime security com admission control, network egress restrito e resposta automatizada (kill pod, isolar nó). Centralize alertas no SIEM, defina playbooks de resposta a incidentes e teste as regras periodicamente contra cenários conhecidos em laboratório.

**Referências:**
- Falco — https://falco.org/docs/
- MITRE ATT&CK Containers Matrix — https://attack.mitre.org/matrices/enterprise/containers/
- CWE-506 Embedded Malicious Code — https://cwe.mitre.org/data/definitions/506.html
- NIST SP 800-190 — https://csrc.nist.gov/pubs/sp/800/190/final
- Cilium Tetragon — https://tetragon.io/docs/

### Verificação de integridade e proveniência de artefatos (SLSA / In-toto)

**Classificação:** `defensiva`

**O que é:** Frameworks e atestações que comprovam como e onde um artefato foi construído, permitindo verificar sua integridade e origem antes do deploy.

**Como funciona:** Ataques de cadeia de suprimentos frequentemente adulteram o artefato entre o código-fonte e o consumo. SLSA (Supply-chain Levels for Software Artifacts) define níveis crescentes de garantia: geração de proveniência assinada pelo builder, builds em plataforma isolada e não falsificável, e eventualmente builds herméticos/reproduzíveis. A proveniência (formato in-toto attestation) declara commit-fonte, parâmetros de build e o builder, assinada de modo que o consumidor possa verificar que o artefato veio do pipeline esperado a partir do fonte esperado. Verificadores no deploy rejeitam artefatos sem proveniência válida ou construídos fora do processo aprovado.

**Detecção:** Verifique existência e validade de atestações de proveniência (cosign verify-attestation, slsa-verifier); confirme que builder, fonte e materiais correspondem ao esperado. Audite se o admission control exige proveniência mínima (SLSA nível alvo). Alerte para artefatos sem atestação, com builder inesperado ou digest divergente do registrado.

**Endurecimento:** Gere proveniência SLSA no CI (ex.: geradores oficiais do GitHub Actions) e assine com Sigstore; imponha verificação com slsa-verifier ou Kyverno no deploy, restringindo builders e fontes confiáveis. Busque builds isolados e, quando possível, herméticos/reproduzíveis; fixe artefatos por digest. Combine com SBOM assinado, verificação de assinatura e registro em log de transparência para integridade fim-a-fim.

**Referências:**
- SLSA Framework — https://slsa.dev/spec/v1.0/
- in-toto Attestation Framework — https://in-toto.io/
- OWASP Top 10 2021 A08 Software and Data Integrity Failures — https://owasp.org/Top10/A08_2021-Software_and_Data_Integrity_Failures/
- CWE-345 Insufficient Verification of Data Authenticity — https://cwe.mitre.org/data/definitions/345.html
- NIST SP 800-218 SSDF — https://csrc.nist.gov/pubs/sp/800/218/final
- slsa-verifier — https://github.com/slsa-framework/slsa-verifier

## Modelagem de Ameaças e Frameworks

### CVE e Catálogo KEV (Common Vulnerabilities and Exposures / Known Exploited Vulnerabilities)

**Classificação:** `defensiva`

**O que é:** CVE é o esquema padronizado de identificadores para vulnerabilidades públicas, e o KEV da CISA é o catálogo de CVEs com exploração ativa comprovada.

**Como funciona:** Cada vulnerabilidade divulgada recebe um identificador único CVE-AAAA-NNNN, atribuído por uma CNA (CVE Numbering Authority) sob coordenação da MITRE, criando uma referência comum entre fornecedores, scanners e bancos como o NVD (que adiciona CVSS e mapeamento CWE). O catálogo KEV (Known Exploited Vulnerabilities) da CISA lista o subconjunto de CVEs para as quais há evidência confiável de exploração ativa em ambiente real, cada uma com prazo de remediação. Como só uma fração das CVEs é de fato explorada, KEV e EPSS (probabilidade de exploração) transformam o volume de CVEs em priorização baseada em ameaça real, e não apenas em severidade teórica.

**Detecção:** Correlacione o inventário de ativos e SBOM com feeds de CVE/NVD via scanners (SCA/VM) para saber o que é afetado; monitore diariamente adições ao KEV. Alertar quando um CVE do KEV corresponder a um componente em uso é um indicador de alta prioridade. Enriqueça com EPSS para estimar urgência.

**Endurecimento:** Trate CVEs do KEV como prioridade máxima com SLAs curtos de remediação (patch, upgrade ou mitigação compensatória) alinhados aos prazos da CISA. Mantenha um processo de vulnerability management com SBOM atualizado, priorização por KEV + EPSS + CVSS Environmental e verificação pós-correção. Estabeleça exceções documentadas e controles compensatórios quando o patch for inviável.

**Referências:**
- https://www.cve.org/
- https://nvd.nist.gov/
- https://www.cisa.gov/known-exploited-vulnerabilities-catalog
- https://www.first.org/epss/
- https://csrc.nist.gov/pubs/sp/800/40/r4/final

### CVSS (Common Vulnerability Scoring System)

**Classificação:** `defensiva`

**O que é:** Padrão aberto do FIRST para pontuar a severidade técnica de vulnerabilidades numa escala de 0 a 10 por meio de métricas estruturadas.

**Como funciona:** O CVSS deriva uma pontuação de um vetor de métricas em grupos. O grupo Base captura características intrínsecas e imutáveis (ex.: Attack Vector, Attack Complexity, Privileges Required, User Interaction, Scope e impactos em Confidencialidade, Integridade e Disponibilidade) e produz a nota mais divulgada. O grupo Temporal (chamado Threat no CVSS v4.0) ajusta pela maturidade do exploit e disponibilidade de correção ao longo do tempo. O grupo Environmental permite recalcular considerando o contexto do ativo (importância dos requisitos de C/I/A e controles compensatórios locais). A Base isolada mede severidade, não risco: sem Temporal/Environmental e sem exploração real, ela superestima ou subestima a prioridade no ambiente concreto.

**Detecção:** Consuma scores Base de fontes como NVD e de fornecedores; calcule Environmental por ativo em ferramentas de gestão de vulnerabilidades. Registre o vetor completo (string CVSS) para auditoria e recomputação. Cruze com exploração observada para priorização realista.

**Endurecimento:** Não priorize remediação apenas pela nota Base: combine CVSS com o catálogo KEV (exploração ativa), com o EPSS (probabilidade de exploração) e com a criticidade do ativo via métricas Environmental. Defina SLAs de correção por faixa de severidade e ajuste com contexto de negócio. Prefira CVSS v3.1/v4.0 e documente o vetor usado.

**Referências:**
- https://www.first.org/cvss/
- https://www.first.org/cvss/v3.1/specification-document
- https://www.first.org/cvss/v4.0/specification-document
- https://nvd.nist.gov/vuln-metrics/cvss
- https://www.first.org/epss/

### CWE (Common Weakness Enumeration)

**Classificação:** `defensiva`

**O que é:** Taxonomia comunitária da MITRE que cataloga tipos de fraquezas de software e hardware que podem levar a vulnerabilidades exploráveis.

**Como funciona:** CWE nomeia e organiza classes de fraquezas (a causa-raiz) — por exemplo CWE-79 Cross-site Scripting, CWE-89 SQL Injection, CWE-787 Out-of-bounds Write, CWE-22 Path Traversal — em uma hierarquia com relações de abstração (pillar, class, base, variant). Enquanto uma CVE identifica uma instância concreta de vulnerabilidade num produto, a CWE descreve o tipo de defeito subjacente, o que permite agregar e comparar causas. A MITRE publica o CWE Top 25 Most Dangerous Software Weaknesses, calculado a partir de dados de CVE/KEV, para orientar priorização. CWEs conectam frameworks: são referenciadas pelo OWASP Top 10 e por CVSS/NVD.

**Detecção:** Ferramentas SAST/DAST e SCA classificam achados por CWE, permitindo tendências por causa-raiz no código. Mapeie findings de pentest a CWEs para métricas consistentes e para relacionar a controles. Use o CWE Top 25 como filtro de priorização em revisões.

**Endurecimento:** Trate a fraqueza na causa-raiz recomendada por cada CWE (páginas trazem Potential Mitigations), por exemplo output encoding contextual para CWE-79 e consultas parametrizadas para CWE-89. Defina padrões de codificação segura e gates de CI mapeados às CWEs mais relevantes ao seu stack. Acompanhe redução de densidade por CWE ao longo do tempo.

**Referências:**
- https://cwe.mitre.org/
- https://cwe.mitre.org/top25/
- https://cwe.mitre.org/data/definitions/79.html
- https://cwe.mitre.org/data/definitions/89.html
- https://nvd.nist.gov/

### Cyber Kill Chain (Cadeia de Destruição Cibernética)

**Classificação:** `defensiva`

**O que é:** Modelo da Lockheed Martin que descreve uma intrusão dirigida como uma sequência de sete fases, permitindo interromper o ataque em qualquer elo.

**Como funciona:** A cadeia descreve fases sequenciais: Reconnaissance (coleta de informações do alvo), Weaponization (preparação do artefato de entrega), Delivery (envio ao alvo, ex.: e-mail, web), Exploitation (execução ao explorar uma falha), Installation (estabelecimento de persistência), Command and Control (canal remoto de controle) e Actions on Objectives (execução do objetivo, como exfiltração). A premissa defensiva é que o adversário precisa completar toda a cadeia, então detectar e romper qualquer elo aborta a operação; cada fase sugere onde posicionar controles. É mais adequado a intrusões externas dirigidas e é frequentemente complementado por ATT&CK (mais granular) e pela Unified Kill Chain.

**Detecção:** Alinhe fontes de telemetria por fase: inteligência e sensores externos (Recon), gateways de e-mail/web e sandbox (Delivery/Exploitation), EDR e monitoração de persistência (Installation), detecção de C2 por análise de rede/DNS/beaconing e proxies (Command and Control) e DLP/monitoração de saída (Actions on Objectives). Mapeie alertas à fase para medir profundidade defensiva.

**Endurecimento:** Distribua controles em profundidade por fase: redução de exposição e higiene de OSINT (Recon), filtragem e conscientização anti-phishing (Delivery), patching e hardening/EDR (Exploitation/Installation), bloqueio de C2 por egress filtering e DNS seguro, e segmentação com DLP para conter Actions on Objectives. O objetivo é aumentar o custo do atacante e criar múltiplas oportunidades de detecção.

**Referências:**
- https://www.lockheedmartin.com/en-us/capabilities/cyber/cyber-kill-chain.html
- https://attack.mitre.org/
- https://www.unifiedkillchain.com/
- https://csrc.nist.gov/glossary/term/cyber_kill_chain

### DREAD e PASTA (metodologias de priorização e processo de ameaças)

**Classificação:** `defensiva`

**O que é:** DREAD é um esquema de pontuação de risco por cinco fatores e PASTA é um processo de sete estágios de modelagem de ameaças centrado em risco de negócio.

**Como funciona:** DREAD estima o risco de uma ameaça pela média de cinco fatores: Damage (impacto), Reproducibility (facilidade de reproduzir), Exploitability (esforço de exploração), Affected Users (abrangência) e Discoverability (facilidade de descobrir). Por depender de julgamento subjetivo, é usado para ranquear ameaças relativas dentro de um mesmo contexto, muitas vezes com rubricas fixas para reduzir inconsistência. PASTA (Process for Attack Simulation and Threat Analysis) é um processo de sete estágios — definir objetivos, definir escopo técnico, decompor a aplicação, análise de ameaças, análise de vulnerabilidades/fraquezas, modelagem de ataques e análise de risco/impacto — que alinha ameaças técnicas a objetivos de negócio e simula ataques para priorizar mitigação com base em risco.

**Detecção:** São metodologias de avaliação em design-time; seu produto são ameaças priorizadas e requisitos de teste, não indicadores de runtime. Documente as pontuações e o racional para permitir revisão e reprodutibilidade. Reavalie as pontuações quando surgirem novos exploits ou mudanças de exposição.

**Endurecimento:** Use o ranking para direcionar orçamento de mitigação às ameaças de maior risco primeiro; combine DREAD/PASTA com CVSS para calibrar severidade técnica e com dados de exploração reais (KEV) para ajustar probabilidade. Prefira rubricas objetivas e revisão por pares para reduzir viés. Integre o resultado ao backlog de segurança com controles rastreáveis.

**Referências:**
- https://owasp.org/www-community/Threat_Modeling_Process
- https://en.wikipedia.org/wiki/DREAD_(risk_assessment_model)
- https://versprite.com/blog/what-is-pasta-threat-modeling/
- https://www.microsoft.com/en-us/securityengineering/sdl/threatmodeling

### MITRE ATLAS (Adversarial Threat Landscape for AI Systems)

**Classificação:** `defensiva`

**O que é:** Base de conhecimento da MITRE, estruturada como o ATT&CK, que cataloga táticas e técnicas de adversários contra sistemas de IA e machine learning.

**Como funciona:** ATLAS estende o paradigma tática/técnica para o ciclo de vida de ML, cobrindo desde reconhecimento e acesso ao modelo até envenenamento de dados de treino (data poisoning), evasão do modelo com entradas adversariais, extração/roubo de modelo, inferência de pertencimento e ataques à cadeia de suprimentos de ML. Para sistemas com LLMs inclui técnicas como prompt injection (direta e indireta) e exfiltração via saída do modelo. As técnicas vêm acompanhadas de estudos de caso reais e mapeamentos, complementando o OWASP Top 10 para LLM e o NIST AI RMF.

**Detecção:** Monitore prompts e saídas para padrões de injeção e vazamento; registre proveniência de dados de treino e artefatos de modelo; detecte anomalias em distribuição de entradas (possível evasão/poisoning) e picos de consultas (possível extração de modelo). Use avaliações adversariais e red teaming de IA, guardrails e classificadores de conteúdo como sensores.

**Endurecimento:** Isole e valide fontes de dados de treino, assine e verifique artefatos de modelo, aplique rate limiting e monitore consultas para dificultar extração, e trate toda entrada e conteúdo recuperado (RAG) como não confiável para conter prompt injection. Restrinja privilégios das ferramentas/plugins acionados pelo LLM (menor privilégio) e valide/sanitize as saídas antes de usá-las em ações sensíveis. Combine com o OWASP Top 10 para Aplicações LLM e controles do NIST AI RMF.

**Referências:**
- https://atlas.mitre.org/
- https://atlas.mitre.org/techniques
- https://genai.owasp.org/llm-top-10/
- https://www.nist.gov/itl/ai-risk-management-framework
- https://attack.mitre.org/

### MITRE ATT&CK (Adversarial Tactics, Techniques and Common Knowledge)

**Classificação:** `defensiva`

**O que é:** Base de conhecimento curada da MITRE que cataloga táticas, técnicas e procedimentos (TTPs) reais de adversários, organizados em matrizes por plataforma.

**Como funciona:** ATT&CK modela o comportamento do atacante em táticas (o objetivo, ex.: Initial Access, Persistence, Lateral Movement, Exfiltration) e técnicas/sub-técnicas (o como, ex.: T1566 Phishing) observadas em incidentes reais. Cada técnica traz descrição, exemplos de grupos e software, fontes de dados de detecção e mitigações associadas. Existem matrizes Enterprise, Mobile e ICS, e ao mapear detecções e controles às técnicas obtém-se uma visão de cobertura defensiva. O framework é descritivo (baseado em observação empírica), não uma sequência linear obrigatória.

**Detecção:** Mapeie regras de detecção (SIEM/EDR), fontes de log (Data Sources / Data Components) e caça a ameaças às técnicas relevantes; use ATT&CK Navigator para heatmaps de cobertura e gaps. Correlacione alertas a técnicas para enriquecer contexto e priorizar. Projetos como Sigma, MITRE CAR e Atomic Red Team ajudam a instrumentar e validar detecções por técnica.

**Endurecimento:** Priorize mitigações do próprio ATT&CK (série M, ex.: MFA, application isolation, segmentação) contra as técnicas mais prováveis para o seu ambiente e setor. Use threat intelligence para focar nos grupos que visam seu segmento e feche lacunas de detecção mapeadas. Complemente com MITRE D3FEND para relacionar contramedidas defensivas às técnicas ofensivas.

**Referências:**
- https://attack.mitre.org/
- https://attack.mitre.org/resources/
- https://d3fend.mitre.org/
- https://car.mitre.org/
- https://github.com/redcanaryco/atomic-red-team

### OWASP API Security Top 10 2023 (API Security Top 10)

**Classificação:** `defensiva`

**O que é:** Lista da OWASP com os dez riscos de segurança mais críticos específicos de APIs web (REST, GraphQL), distintos dos riscos genéricos de aplicações.

**Como funciona:** APIs expõem lógica de negócio e objetos diretamente, tornando falhas de autorização o risco dominante. A edição 2023 traz API1 Broken Object Level Authorization (BOLA/IDOR), API2 Broken Authentication, API3 Broken Object Property Level Authorization (une mass assignment e excessive data exposure), API4 Unrestricted Resource Consumption, API5 Broken Function Level Authorization (BFLA), API6 Unrestricted Access to Sensitive Business Flows, API7 Server-Side Request Forgery, API8 Security Misconfiguration, API9 Improper Inventory Management (APIs sombra e versões antigas) e API10 Unsafe Consumption of APIs. O mecanismo central é que o servidor confia em identificadores ou propriedades vindos do cliente sem revalidar autorização por objeto, por função e por propriedade a cada requisição.

**Detecção:** Teste autorização com múltiplos usuários trocando IDs e verbos (deteta BOLA/BFLA); compare campos aceitos no request com o modelo (mass assignment); inspecione respostas que retornam mais dados do que a UI usa. Ferramentas: gateways com logging por rota, OWASP ZAP, testes de contrato/OpenAPI, monitoração de rate e anomalias. Mantenha inventário de endpoints (API9) via descoberta e catálogo OpenAPI.

**Endurecimento:** Aplique verificação de autorização por objeto no lado servidor usando a identidade da sessão, nunca o ID enviado pelo cliente; use allowlist explícita de propriedades no binding (evita mass assignment) e serialização controlada de saída; imponha rate limiting, quotas e limites de payload; valide esquemas OpenAPI; desative endpoints e versões obsoletas; e trate respostas de APIs upstream como não confiáveis. Adote autenticação forte e escopos OAuth 2.0 mínimos.

**Referências:**
- https://owasp.org/API-Security/editions/2023/en/0x00-header/
- https://owasp.org/API-Security/
- https://cwe.mitre.org/data/definitions/639.html
- https://cwe.mitre.org/data/definitions/915.html
- https://owasp.org/www-project-web-security-testing-guide/

### OWASP Top 10 2021 (OWASP Top Ten)

**Classificação:** `defensiva`

**O que é:** Documento de conscientização da OWASP que lista as dez categorias de risco mais críticas em aplicações web, agregando dezenas de CWEs por categoria.

**Como funciona:** O Top 10 2021 consolida dados de mais de 400 mil aplicações e uma pesquisa da comunidade, mapeando cada categoria a um conjunto de CWEs relacionados e a fatores como exploitabilidade e prevalência. As categorias são A01 Broken Access Control, A02 Cryptographic Failures, A03 Injection (que passou a incluir XSS), A04 Insecure Design (categoria nova focada em falhas de projeto), A05 Security Misconfiguration, A06 Vulnerable and Outdated Components, A07 Identification and Authentication Failures, A08 Software and Data Integrity Failures (inclui insecure deserialization e ataques a pipeline/supply chain), A09 Security Logging and Monitoring Failures e A10 Server-Side Request Forgery (SSRF). Não é um padrão de certificação nem um checklist exaustivo, e sim uma referência de priorização para elevar a maturidade de AppSec. Cada categoria descreve descrição, exemplos de cenário de ataque e orientações de prevenção.

**Detecção:** Use a taxonomia para organizar achados de SAST/DAST/SCA e pentests, mapeando cada finding à categoria correspondente. ASVS e OWASP Testing Guide (WSTG) fornecem casos de teste verificáveis; ferramentas como OWASP ZAP, Semgrep e dependency scanners cobrem várias categorias. Métricas de cobertura por categoria ajudam a identificar lacunas de detecção (ex.: A09 aponta ausência de logging/monitoramento).

**Endurecimento:** Adote controles alinhados por categoria: controle de acesso negado por padrão (A01), criptografia moderna em trânsito e repouso (A02), consultas parametrizadas e validação/encoding (A03), threat modeling e padrões de projeto seguros (A04), baselines de configuração e hardening (A05), gestão de dependências e patching (A06), MFA e gestão de sessão robusta (A07), verificação de integridade e assinatura de artefatos (A08), logging estruturado e monitoramento (A09) e allowlist de destinos com bloqueio de metadata para SSRF (A10). Integre ASVS como requisito de segurança verificável no SDLC.

**Referências:**
- https://owasp.org/Top10/
- https://owasp.org/www-project-top-ten/
- https://owasp.org/www-project-application-security-verification-standard/
- https://owasp.org/www-project-web-security-testing-guide/
- https://cwe.mitre.org/

### Processo de Modelagem de Ameaças (Threat Modeling Process)

**Classificação:** `defensiva`

**O que é:** Atividade estruturada de análise em fase de projeto que identifica ameaças, vulnerabilidades e contramedidas antes de o código ser escrito.

**Como funciona:** O processo responde às quatro perguntas de Shostack: o que estamos construindo, o que pode dar errado, o que faremos a respeito e fizemos um bom trabalho. Normalmente começa modelando o sistema em um diagrama de fluxo de dados (DFD) com processos, armazenamentos, fluxos, entidades externas e fronteiras de confiança; em seguida enumeram-se ameaças (com apoio de STRIDE, ATT&CK ou árvores de ataque), priorizam-se por risco (CVSS/DREAD/PASTA) e definem-se mitigações rastreáveis. É iterativo e deve ser revisitado a cada mudança relevante de arquitetura, praticando security by design (shift-left). O foco em fronteiras de confiança evita gastar esforço onde não há mudança de nível de privilégio.

**Detecção:** É uma técnica de design-time cujo produto (lista de ameaças e requisitos) deve virar casos de teste e requisitos de monitoramento verificáveis. Ferramentas como OWASP Threat Dragon e Microsoft Threat Modeling Tool documentam DFDs e ameaças; rastreie cada ameaça até um controle e um teste. Meça cobertura de mitigações implementadas versus ameaças levantadas.

**Endurecimento:** Institucionalize a modelagem no SDLC com critérios de gatilho (novos serviços, mudanças de fronteira de confiança, dados sensíveis), templates e revisão por pares. Converta ameaças em requisitos de segurança (ex.: ASVS), backlog priorizado e testes automatizados. Mantenha os modelos como artefatos vivos, versionados junto ao código.

**Referências:**
- https://owasp.org/www-community/Threat_Modeling_Process
- https://www.threatmodelingmanifesto.org/
- https://owasp.org/www-project-threat-dragon/
- https://owasp.org/www-project-application-security-verification-standard/
- https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool

### Purple Teaming (colaboração ofensiva-defensiva)

**Classificação:** `escopo_autorizado`

**O que é:** Prática colaborativa em que time ofensivo (red) e defensivo (blue) trabalham juntos para emular TTPs conhecidos e validar e melhorar detecção e resposta.

**Como funciona:** Em vez de um teste adversarial cego, o purple teaming executa técnicas mapeadas ao MITRE ATT&CK de forma controlada e comunicada, enquanto o time defensivo observa se cada técnica gera telemetria, alerta e resposta adequados. O ciclo é emular uma técnica, verificar a detecção, ajustar regras/telemetria e reexecutar até fechar a lacuna, produzindo melhoria mensurável de cobertura por técnica. Ferramentas de adversary emulation e Breach and Attack Simulation automatizam a execução dos TTPs. Por envolver execução de técnicas ofensivas, mesmo que controladas, requer autorização formal, escopo e regras de engajamento definidos.

**Detecção:** O próprio exercício é um teste de detecção: para cada técnica, mede-se se houve log na fonte esperada, se a regra disparou e o tempo até detecção/resposta. Registre resultados em uma matriz de cobertura (ex.: ATT&CK Navigator) distinguindo detectado, parcialmente detectado e não detectado. Use os gaps para engenharia de detecção.

**Endurecimento:** Converta cada lacuna em melhoria concreta: nova fonte de log, regra de detecção (ex.: Sigma), tuning para reduzir falso positivo ou controle preventivo. Formalize um programa recorrente com escopo e ROE, priorizando as técnicas mais relevantes por inteligência de ameaças. Documente e reteste para evitar regressão de cobertura.

**Referências:**
- https://attack.mitre.org/resources/adversary-emulation-plans/
- https://github.com/redcanaryco/atomic-red-team
- https://github.com/mitre/caldera
- https://github.com/SigmaHQ/sigma
- https://mitre-attack.github.io/attack-navigator/

### SDLC Seguro e DevSecOps (Secure SDLC / DevSecOps)

**Classificação:** `defensiva`

**O que é:** O SDLC Seguro integra atividades de segurança em todas as fases do desenvolvimento — requisitos, projeto, codificação, teste e operação — em vez de tratá-las como uma verificação final. DevSecOps operacionaliza essa integração de forma automatizada e contínua na esteira de entrega.

**Como funciona:** Corrigir falhas tarde é caro e arriscado; o SDLC Seguro antecipa a segurança (shift left) para reduzir defeitos que chegam à produção. Conceitualmente, cada fase ganha atividades próprias: requisitos de segurança e casos de abuso na concepção; modelagem de ameaças e princípios de projeto seguro no design; padrões de codificação segura e revisão na implementação; análise estática (SAST), análise de composição (SCA), testes dinâmicos (DAST) e testes de abuso na fase de teste; hardening, monitoramento e resposta em operação. DevSecOps automatiza esses controles como gates na pipeline, tornando-os repetíveis e mensuráveis. Frameworks de maturidade (OWASP SAMM, NIST SSDF, BSIMM) ajudam a avaliar e evoluir o programa em vez de aplicar controles isolados.

**Detecção:** Meça cobertura e eficácia dos controles: percentual de componentes com modelagem de ameaças, densidade e tempo de correção de achados de SAST/SCA/DAST, e vulnerabilidades encontradas em produção que deveriam ter sido barradas antes. Monitore a pipeline para gates ignorados ou desabilitados. Use métricas de maturidade (SAMM/SSDF) periodicamente para identificar lacunas por fase.

**Endurecimento:** Defina requisitos de segurança e critérios de aceitação desde o início e incorpore modelagem de ameaças no design. Padronize codificação segura e revisão por pares. Automatize SAST, SCA, verificação de segredos e DAST na esteira com gates que bloqueiam builds em achados críticos, evitando falsos positivos que erodam a confiança. Gerencie dependências e proveniência de artefatos. Feche o ciclo com monitoramento, resposta a incidentes e retroalimentação dos aprendizados para as fases iniciais. Guie a evolução por um framework de maturidade reconhecido.

**Referências:**
- OWASP SAMM: Software Assurance Maturity Model
- NIST SP 800-218: Secure Software Development Framework (SSDF)
- Microsoft Security Development Lifecycle (SDL)
- OWASP: DevSecOps Guideline

### Security by Design e Princípios de Projeto Seguro (Secure Design Principles)

**Classificação:** `defensiva`

**O que é:** Abordagem que integra a segurança desde a concepção do sistema, guiada por princípios de projeto consolidados que reduzem risco por construção.

**Como funciona:** Security by design trata a segurança como requisito de arquitetura, não como camada adicionada ao final. Baseia-se em princípios clássicos (Saltzer e Schroeder e derivados): menor privilégio (cada componente recebe apenas os direitos mínimos necessários), defesa em profundidade (múltiplas camadas independentes de controle para que a falha de uma não comprometa o todo), fail secure/fail-safe defaults (na dúvida ou em falha, negar acesso), economia de mecanismo (simplicidade), mediação completa (verificar autorização em todo acesso), separação de privilégios e responsabilidades, e minimização da superfície de ataque. Aplicá-los desde o projeto reduz a densidade de vulnerabilidades e o custo de correção, conectando-se ao Insecure Design (A04) do OWASP Top 10.

**Detecção:** Verifique aderência via revisões de arquitetura, threat modeling e checklists (ASVS, secure design reviews) que testam se cada princípio está presente. Auditorias de IAM detectam violações de menor privilégio; testes de comportamento em falha verificam fail secure. Ausência de camadas redundantes ou de negação por padrão são indicadores de fraqueza de projeto.

**Endurecimento:** Codifique os princípios em padrões e guardrails: negar por padrão em controle de acesso, RBAC/ABAC com privilégio mínimo e revisão periódica, múltiplas camadas de controle preventivo e detectivo, tratamento de erro que falha fechado, secure defaults em configuração e redução ativa da superfície. Formalize secure design reviews como gate no SDLC e alinhe a modelos como o CISA Secure by Design e o NIST SSDF.

**Referências:**
- https://www.cisa.gov/securebydesign
- https://owasp.org/www-project-proactive-controls/
- https://csrc.nist.gov/pubs/sp/800/218/final
- https://cheatsheetseries.owasp.org/cheatsheets/Secure_Product_Design_Cheat_Sheet.html
- https://www.nist.gov/publications/protection-information-computer-systems

### STRIDE (modelo de categorização de ameaças)

**Classificação:** `defensiva`

**O que é:** Mnemônico da Microsoft que categoriza ameaças em seis classes, cada uma violando uma propriedade de segurança específica.

**Como funciona:** STRIDE é o inverso das propriedades desejadas: Spoofing viola autenticação, Tampering viola integridade, Repudiation viola não repúdio, Information Disclosure viola confidencialidade, Denial of Service viola disponibilidade e Elevation of Privilege viola autorização. Aplica-se sobre um diagrama de fluxo de dados (DFD): para cada elemento (processo, armazenamento, fluxo, entidade externa) e cada travessia de fronteira de confiança, enumeram-se as ameaças STRIDE aplicáveis. O resultado é uma lista estruturada de ameaças que orienta a definição de contramedidas por propriedade violada.

**Detecção:** STRIDE é uma técnica de análise em design-time, não de detecção em runtime; seus resultados alimentam requisitos de teste e de monitoramento. Ferramentas como o Microsoft Threat Modeling Tool e OWASP Threat Dragon geram ameaças a partir do DFD. Rastreie cada ameaça até um teste ou controle verificável.

**Endurecimento:** Associe contramedidas por categoria: autenticação forte e MFA (S), assinaturas/hashes e validação de integridade (T), logging assinado e auditoria (R), criptografia e controle de acesso (I), rate limiting, quotas e redundância (D) e menor privilégio com verificação de autorização (E). Priorize ameaças em fronteiras de confiança e reavalie o modelo a cada mudança de arquitetura.

**Referências:**
- https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-threats
- https://owasp.org/www-community/Threat_Modeling_Process
- https://owasp.org/www-project-threat-dragon/
- https://www.microsoft.com/en-us/securityengineering/sdl/threatmodeling

### Superfície de Ataque (Attack Surface)

**Classificação:** `escopo_autorizado`

**O que é:** Conjunto de todos os pontos de entrada e recursos expostos por onde um adversário pode tentar interagir com ou extrair dados de um sistema.

**Como funciona:** A superfície de ataque agrega os canais e ativos alcançáveis por um atacante: endpoints de rede e portas, APIs, aplicações web, interfaces de administração, contas e credenciais, integrações de terceiros, dados expostos e a superfície humana (engenharia social). Distingue-se superfície externa (internet-facing) da interna, e cada ponto acrescenta risco proporcional à sua exposição e privilégio. Attack Surface Management (ASM) descobre e inventaria continuamente esses ativos — incluindo shadow IT e ativos esquecidos — porque o que não se conhece não se protege. Enumerar e mapear a superfície de terceiros exige autorização escrita e regras de engajamento; sobre ativos próprios é atividade defensiva legítima.

**Detecção:** Mantenha descoberta contínua de ativos (varredura externa, análise de DNS/certificados, inventário de nuvem) e reconcilie com o inventário oficial para achar ativos não gerenciados. Monitore mudanças de exposição (novas portas/serviços/subdomínios) como indicadores. Ferramentas de ASM, scanners de rede e catálogos de API apoiam essa visibilidade — em ativos próprios ou dentro do escopo autorizado.

**Endurecimento:** Aplique Attack Surface Reduction: desative serviços, portas e recursos não usados; minimize interfaces de administração e restrinja-as por rede; aplique egress/ingress filtering e segmentação; e reduza dados e integrações expostos ao mínimo necessário (menor privilégio). Trate cada novo ponto de exposição via change management com revisão de segurança. Consolide e retire ativos legados e shadow IT.

**Referências:**
- https://owasp.org/www-community/Attack_Surface_Analysis_Cheat_Sheet
- https://csrc.nist.gov/glossary/term/attack_surface
- https://attack.mitre.org/
- https://cheatsheetseries.owasp.org/cheatsheets/Attack_Surface_Analysis_Cheat_Sheet.html

## Defesa, Detecção, Resposta e Forense

### Análise Defensiva de Malware Estática e Dinâmica (Static & Dynamic Malware Analysis)

**Classificação:** `laboratorio_autorizado`

**O que é:** Estudo de artefatos maliciosos — sem executar ou executando em ambiente isolado — para extrair indicadores, entender capacidades e produzir detecções, feito exclusivamente em laboratório controlado.

**Como funciona:** Na análise estática, o artefato é examinado sem execução: hashes, strings, cabeçalhos PE/ELF, imports, entropia (indício de packing) e assinaturas YARA revelam capacidades e família prováveis. Na análise dinâmica, a amostra é detonada numa sandbox isolada (rede simulada, snapshots) enquanto se observa comportamento: criação de processos, chamadas de API, alterações de registro/arquivo, persistência e tentativas de comunicação C2. O objetivo defensivo é derivar IOCs (hashes, domínios, IPs) e IOAs (comportamentos), mapear técnicas em ATT&CK e escrever detecções (Sigma/YARA) — não recriar o malware. O isolamento é crítico porque a amostra é código hostil vivo; deve rodar em ambiente descartável, sem acesso à rede de produção, e ser tratada como material perigoso.

**Detecção:** Produtos desta análise alimentam detecção: assinaturas YARA para arquivos/memória, regras Sigma para comportamento, IOCs em feeds de threat intel, e regras EDR para técnicas observadas. Indicadores incluem entropia alta, seções PE anômalas, imports suspeitos (APIs de injeção), beaconing periódico e mutexes conhecidos.

**Endurecimento:** Conduza somente em lab autorizado e isolado (VM descartável/air-gapped ou sandbox dedicada), com snapshots e rede controlada; nunca em máquina de produção ou pessoal; trate amostras com criptografia e cofre; siga a política de manuseio de malware da organização. Para defesa da frota: EDR com bloqueio comportamental, controle de aplicação (allowlisting), e ingestão de IOCs/YARA nos controles.

**Referências:**
- YARA Documentation - https://yara.readthedocs.io/
- MITRE ATT&CK - https://attack.mitre.org/
- NIST SP 800-83 Rev. 1 Guide to Malware Incident Prevention and Handling - https://csrc.nist.gov/pubs/sp/800/83/r1/final
- MITRE Malware Attribute Enumeration and Characterization (MAEC) - https://maecproject.github.io/
- Practical Malware Analysis (Sikorski & Honig) - No Starch Press
- CWE-506: Embedded Malicious Code - https://cwe.mitre.org/data/definitions/506.html

### Análise e Correlação de Logs para Detecção de Intrusão (Log Analysis for Intrusion Detection)

**Classificação:** `defensiva`

**O que é:** Examinar e correlacionar registros de autenticação, sistema, rede e aplicação para identificar padrões de comprometimento como força bruta, sequestro de conta e movimento lateral.

**Como funciona:** Eventos de log carregam sinais de ataque quando interpretados em contexto: muitas falhas de login seguidas de sucesso sugerem força bruta ou password spraying; logins de geografias impossíveis em curto intervalo indicam account takeover; execução de processos incomuns por contas de serviço sugere movimento lateral. A detecção combina regras determinísticas (limiares, sequências), correlação entre fontes (VPN + endpoint + aplicação) e análise comportamental (UEBA) que compara atividade contra uma linha de base por usuário/entidade. A precisão depende de logs completos, tempo sincronizado e enriquecimento (identidade, ativo, geolocalização). Ruído e falsos-positivos são gerenciados por tuning contínuo e por priorizar detecções de alto valor mapeadas a ATT&CK.

**Detecção:** Padrões-chave: brute force/spraying (muitas falhas, poucas contas ou muitas contas), impossible travel, uso de credencial fora de horário, novos privilégios, criação de contas, e limpeza de logs (event log cleared — sinal forte de anti-forense). Ferramentas: SIEM com regras de correlação, UEBA, e regras Sigma para eventos de autenticação.

**Endurecimento:** Garanta logging de autenticação e autorização em todas as camadas, sincronize relógios, proteja logs contra adulteração, e implemente detecções para os padrões acima com resposta (bloqueio, MFA step-up). Reduza a superfície com MFA, lockout/rate limiting inteligente e mínimo privilégio, tornando os sinais mais nítidos. Faça tuning para manter alta fidelidade.

**Referências:**
- OWASP Top 10 2021 A09:2021 Security Logging and Monitoring Failures - https://owasp.org/Top10/A09_2021-Security_Logging_and_Monitoring_Failures/
- MITRE ATT&CK T1110 Brute Force - https://attack.mitre.org/techniques/T1110/
- MITRE ATT&CK T1070 Indicator Removal (Clear Logs) - https://attack.mitre.org/techniques/T1070/
- NIST SP 800-92 Guide to Computer Security Log Management - https://csrc.nist.gov/pubs/sp/800/92/final
- CWE-778 Insufficient Logging - https://cwe.mitre.org/data/definitions/778.html
- OWASP Cheat Sheet: Logging - https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html

### Ciclo de Resposta a Incidentes NIST (Incident Response Lifecycle - NIST SP 800-61)

**Classificação:** `defensiva`

**O que é:** Framework de quatro fases (preparação; detecção e análise; contenção, erradicação e recuperação; atividade pós-incidente) que estrutura como uma organização lida com incidentes de segurança de forma repetível.

**Como funciona:** Na preparação, a organização estabelece o CSIRT, ferramentas, canais de comunicação, playbooks e treinamento antes de qualquer incidente. Na detecção e análise, alertas e precursores são triados, o escopo e a severidade são determinados e o incidente é declarado e documentado com timeline. A contenção limita o alcance (isolamento de rede, revogação de credenciais) preservando evidências, a erradicação remove a causa raiz (malware, contas maliciosas, vulnerabilidade explorada) e a recuperação restaura serviços com monitoramento reforçado até confiança na normalidade. A atividade pós-incidente conduz lições aprendidas, atualiza controles e alimenta a preparação, fechando o ciclo. Decisões-chave incluem quando conter vs. observar, retenção de evidências para forense e obrigações de notificação.

**Detecção:** A fase de detecção usa SIEM, EDR, alertas de usuários e threat intel; indicadores de maturidade incluem existência de runbooks por tipo de incidente, matriz de severidade, RACI de comunicação e métricas MTTD/MTTR/MTTC. Ausência de timeline documentada ou de critério de declaração de incidente é sinal de imaturidade.

**Endurecimento:** Mantenha um plano de IR escrito e testado por tabletop exercises e simulações; defina papéis, autoridade de decisão e contatos (jurídico, comunicação, terceiros); padronize evidence handling e cadeia de custódia; pré-autorize ações de contenção; integre com continuidade de negócio/DR e com requisitos regulatórios de notificação (ex.: LGPD/ANPD, GDPR 72h).

**Referências:**
- NIST SP 800-61 Rev. 2 Computer Security Incident Handling Guide - https://csrc.nist.gov/pubs/sp/800/61/r2/final
- NIST SP 800-61 Rev. 3 (Incident Response Recommendations) - https://csrc.nist.gov/pubs/sp/800/61/r3/final
- SANS Incident Handler's Handbook - https://www.sans.org/white-papers/33901/
- NIST SP 800-184 Guide for Cybersecurity Event Recovery - https://csrc.nist.gov/pubs/sp/800/184/final
- ISO/IEC 27035 Information security incident management
- MITRE ATT&CK - https://attack.mitre.org/

### Conscientização de Segurança e Defesa contra Phishing (Security Awareness)

**Classificação:** `defensiva`

**O que é:** Programa que reduz o risco humano por meio de educação, cultura, simulações e controles técnicos que dificultam o sucesso de phishing e engenharia social.

**Como funciona:** Ataques de engenharia social (phishing, spear phishing, BEC) exploram confiança, urgência e autoridade para induzir usuários a clicar, fornecer credenciais ou autorizar ações. Um programa de conscientização combina treinamento contínuo baseado em papéis, simulações controladas e mensuradas, e um canal fácil de reporte que transforma o usuário em sensor de detecção. No plano técnico, autenticação de e-mail (SPF, DKIM, DMARC) reduz spoofing de domínio, e filtros/sandbox de anexos e URLs bloqueiam grande parte das campanhas antes de chegarem ao usuário. A métrica não é apenas taxa de clique, mas taxa de reporte e tempo até o reporte, que aceleram a resposta a campanhas reais.

**Detecção:** Indicadores: aumento de e-mails reportados, falhas de DMARC de domínios parceiros, domínios lookalike recém-registrados, anomalias de login pós-phishing (impossible travel, novos dispositivos), e regras de encaminhamento automático maliciosas em caixas comprometidas. Integre reportes ao SOC para correlação.

**Endurecimento:** Implante MFA resistente a phishing (FIDO2/WebAuthn) para neutralizar roubo de credencial; configure SPF/DKIM/DMARC em enforcement (p=reject); use filtros de e-mail com detonação de URL/anexo; forneça botão de reporte de phishing; treine com simulações éticas e feedback construtivo (não punitivo); proteja fluxos de aprovação financeira com verificação fora de banda contra BEC.

**Referências:**
- MITRE ATT&CK T1566 Phishing - https://attack.mitre.org/techniques/T1566/
- NIST SP 800-50 Building an Information Technology Security Awareness Program - https://csrc.nist.gov/pubs/sp/800/50/final
- RFC 7489 DMARC - https://www.rfc-editor.org/rfc/rfc7489
- RFC 7208 SPF - https://www.rfc-editor.org/rfc/rfc7208
- RFC 6376 DKIM - https://www.rfc-editor.org/rfc/rfc6376
- CISA Phishing Guidance: Stopping the Attack Cycle at Phase One - https://www.cisa.gov/resources-tools/resources/phishing-guidance-stopping-attack-cycle-phase-one
- NIST SP 800-63B (Phishing-resistant authentication) - https://pages.nist.gov/800-63-3/sp800-63b.html

### Contenção, Erradicação e Recuperação de Incidentes (Containment, Eradication & Recovery)

**Classificação:** `defensiva`

**O que é:** Fase operacional da resposta a incidentes que limita o alcance do comprometimento, remove a presença do adversário e restaura serviços de forma segura e monitorada.

**Como funciona:** A contenção interrompe a propagação e o dano — isolando hosts, bloqueando C2, desabilitando contas e revogando/rotacionando credenciais e tokens — equilibrando a necessidade de preservar evidências forenses e evitar alertar prematuramente o adversário. A erradicação remove a causa raiz e todos os pontos de apoio: malware, contas maliciosas, mecanismos de persistência, e corrige a vulnerabilidade explorada; uma erradicação parcial permite reentrada. A recuperação reconstrói sistemas a partir de imagens confiáveis (golden images) ou backups limpos, valida integridade, e retorna à produção sob monitoramento reforçado até haver confiança de que o adversário foi expulso (eviction). Em comprometimentos amplos de identidade, pode ser necessária uma expulsão coordenada e simultânea para evitar que o atacante se reestabeleça.

**Detecção:** Durante e após, monitore reaparecimento de IOCs/IOAs, novos mecanismos de persistência, tentativas de reautenticação com credenciais rotacionadas e sinais de reentrada. Métricas: dwell time, tempo de contenção (MTTC) e recorrência. Valide erradicação com hunting direcionado antes de declarar encerrado.

**Endurecimento:** Pré-autorize e automatize ações de contenção (playbooks, SOAR); mantenha golden images e backups limpos testados; padronize rotação de credenciais/segredos e revisão de persistência (tarefas agendadas, chaves, tokens OAuth); planeje eviction coordenada para incidentes de identidade; conduza monitoramento pós-recuperação e lições aprendidas. Alinhe com NIST SP 800-61 e 800-184.

**Referências:**
- NIST SP 800-61 Rev. 2 Computer Security Incident Handling Guide - https://csrc.nist.gov/pubs/sp/800/61/r2/final
- NIST SP 800-184 Guide for Cybersecurity Event Recovery - https://csrc.nist.gov/pubs/sp/800/184/final
- MITRE ATT&CK Persistence Tactic TA0003 - https://attack.mitre.org/tactics/TA0003/
- SANS Incident Handler's Handbook - https://www.sans.org/white-papers/33901/
- CISA Incident Response Playbooks - https://www.cisa.gov/resources-tools/resources/federal-government-cybersecurity-incident-and-vulnerability-response-playbooks
- NIST Cybersecurity Framework 2.0 (Respond/Recover) - https://www.nist.gov/cyberframework

### Cyber Threat Intelligence e IOCs (Threat Intelligence & Indicators of Compromise)

**Classificação:** `defensiva`

**O que é:** Coleta, análise e operacionalização de conhecimento sobre adversários — suas motivações, TTPs e indicadores — para orientar detecção, priorização e defesa.

**Como funciona:** CTI transforma dados brutos sobre ameaças em inteligência acionável em três níveis: estratégico (tendências e risco para decisões de negócio), operacional (campanhas e TTPs de atores) e tático (IOCs consumíveis por controles). Indicadores são compartilhados em formatos estruturados como STIX/TAXII e plataformas como MISP, e modelos como Cyber Kill Chain e Diamond Model estruturam a análise de intrusões. IOCs (hashes, domínios, IPs) são fáceis de bloquear mas voláteis; TTPs mapeados a ATT&CK são mais duráveis e valiosos (topo da Pyramid of Pain). A inteligência alimenta engenharia de detecção, threat hunting e resposta, e deve ser avaliada por relevância, confiança e prazo de validade para evitar falsos-positivos por indicadores obsoletos.

**Detecção:** IOCs enriquecem SIEM/EDR/NDR para casar com atividade conhecida; TTPs orientam hunts e detecções comportamentais. Cuidado com decaimento de indicadores (IPs reciclados geram falsos-positivos) e com confiança/fonte. Meça cobertura por atores relevantes ao setor.

**Endurecimento:** Estabeleça um programa de CTI com requisitos de inteligência (PIR) alinhados ao negócio; consuma feeds confiáveis via STIX/TAXII/MISP com scoring de confiança e expiração; converta TTPs em detecções mapeadas a ATT&CK; compartilhe inteligência com pares (ISAC/ISAO) de forma responsável; evite bloquear cegamente indicadores sem contexto.

**Referências:**
- MITRE ATT&CK - https://attack.mitre.org/
- OASIS STIX/TAXII - https://oasis-open.github.io/cti-documentation/
- MISP Threat Sharing - https://www.misp-project.org/
- Lockheed Martin Cyber Kill Chain - https://www.lockheedmartin.com/en-us/capabilities/cyber/cyber-kill-chain.html
- The Diamond Model of Intrusion Analysis - https://www.activeresponse.org/wp-content/uploads/2013/07/diamond.pdf
- The Pyramid of Pain - David Bianco - https://detect-respond.blogspot.com/2013/03/the-pyramid-of-pain.html
- NIST SP 800-150 Guide to Cyber Threat Information Sharing - https://csrc.nist.gov/pubs/sp/800/150/final

### EDR e XDR (Endpoint / Extended Detection and Response)

**Classificação:** `defensiva`

**O que é:** Tecnologias que coletam telemetria detalhada de endpoints (EDR) ou correlacionam múltiplos domínios de telemetria — endpoint, rede, e-mail, nuvem, identidade (XDR) — para detectar, investigar e responder a ameaças.

**Como funciona:** Um agente EDR instrumenta o endpoint capturando eventos de processo, arquivo, registro, rede e chamadas de API em tempo quase real, aplicando detecções comportamentais locais e enviando telemetria a um backend para análise e caça. Ao detectar atividade maliciosa, permite resposta: isolar o host da rede, matar processos, colocar arquivos em quarentena e coletar artefatos forenses remotamente. XDR estende isso correlacionando sinais de endpoint com identidade, e-mail, rede e nuvem numa única história de ataque, reduzindo alertas fragmentados e acelerando a investigação. A eficácia depende de cobertura de agentes, proteção anti-tamper do próprio agente e mapeamento de detecções a ATT&CK.

**Detecção:** O EDR/XDR é a fonte primária de detecção de endpoint; monitore saúde da frota (agentes offline/desatualizados = pontos cegos), tentativas de desabilitar/tamper do agente (técnica de defense evasion), e árvores de processo anômalas. Alertas devem ser triados com contexto de linha de comando e linhagem de processo.

**Endurecimento:** Implante agentes em 100% dos endpoints e servidores, ative proteção anti-tamper e modo de bloqueio comportamental, integre com SIEM/SOAR para resposta orquestrada, mantenha allowlisting de aplicações onde viável, e teste a cobertura de detecção com emulação adversária em lab. Restrinja quem pode isolar hosts e revise essas ações. Complemente com NDR para tráfego e com gestão de identidade.

**Referências:**
- MITRE ATT&CK Evaluations - https://attackevals.mitre-engenuity.org/
- MITRE ATT&CK - https://attack.mitre.org/
- NIST SP 800-137 Information Security Continuous Monitoring (ISCM) - https://csrc.nist.gov/pubs/sp/800/137/final
- MITRE ATT&CK Data Sources - https://attack.mitre.org/datasources/
- CISA Endpoint Detection and Response guidance - https://www.cisa.gov/
- Gartner Market Guide for EDR/XDR (conceitual)

### Engenharia de Detecção e Regras Sigma (Detection Engineering / Sigma Rules)

**Classificação:** `defensiva`

**O que é:** Disciplina de projetar, testar, versionar e manter regras de detecção — frequentemente escritas no formato aberto Sigma — para transformar comportamento malicioso conhecido em alertas de alta fidelidade.

**Como funciona:** Sigma é um formato YAML agnóstico de SIEM que descreve uma lógica de detecção (logsource + detection com seletores e condição) que é traduzida por conversores (pySigma/sigmac) para a linguagem de consulta do backend alvo (SPL, KQL, Lucene, etc.). O engenheiro de detecção parte de uma hipótese ou técnica ATT&CK, identifica a telemetria necessária, escreve a lógica que casa com o comportamento (ex.: processo pai/filho suspeito, flag de linha de comando) e a avalia por fidelidade contra dados reais e conjuntos de teste. Detecção-como-código coloca as regras em controle de versão com revisão, testes automatizados e CI, medindo cobertura contra a matriz ATT&CK e taxa de falso-positivo. O objetivo é robustez contra evasão (detectar a técnica, não um artefato frágil) e manutenção contínua conforme o ambiente muda.

**Detecção:** Este é o próprio processo de detecção; meça sua saúde por métricas: cobertura ATT&CK, taxa de falso-positivo/negativo, tempo médio de triagem, e regras que nunca dispararam (possivelmente quebradas). Use conjuntos de emulação adversária (Atomic Red Team, Caldera) em laboratório autorizado para validar se as regras disparam.

**Endurecimento:** Versione regras em Git com peer review; documente cada regra com técnica ATT&CK, fonte de log exigida e falsos-positivos conhecidos; use pipeline de teste automatizado; prefira detecções comportamentais a assinaturas frágeis; mantenha um backlog de detecção priorizado por risco. Adote o repositório oficial SigmaHQ como base e o modelo de maturidade (detection maturity).

**Referências:**
- SigmaHQ Sigma Specification - https://github.com/SigmaHQ/sigma-specification
- SigmaHQ Rules Repository - https://github.com/SigmaHQ/sigma
- MITRE ATT&CK Matrix for Enterprise - https://attack.mitre.org/matrices/enterprise/
- MITRE Atomic Red Team - https://github.com/redcanaryco/atomic-red-team
- MITRE Caldera - https://caldera.mitre.org/
- The DML (Detection Maturity Level) Model - Ryan Stillions

### Forense Digital e Cadeia de Custódia (Digital Forensics & Chain of Custody)

**Classificação:** `defensiva`

**O que é:** Processo de identificar, adquirir, preservar, analisar e apresentar evidências digitais de forma que sua integridade e proveniência sejam demonstráveis e defensáveis.

**Como funciona:** A aquisição segue a ordem de volatilidade (memória, conexões de rede, processos e cache antes de disco e mídia removível) para não perder dados voláteis, usando write-blockers e ferramentas de imagem bit-a-bit para criar cópias forenses. Cada evidência recebe um hash criptográfico (SHA-256) no momento da coleta, e o mesmo hash é reverificado antes de cada análise para provar que nada foi alterado. A cadeia de custódia documenta, de forma contínua e datada, quem coletou, transportou, armazenou e acessou cada item, com controle de acesso físico/lógico, garantindo admissibilidade. A análise ocorre sempre sobre a cópia, nunca sobre o original, preservando o artefato-mestre lacrado.

**Detecção:** Não é uma detecção em si, mas apoia a investigação: artefatos forenses incluem timeline de sistema de arquivos (MFT, journaling), registro do Windows, prefetch/amcache, logs de eventos, memória (via Volatility) e artefatos de navegador. Sinais de manipulação incluem hashes divergentes, timestamps inconsistentes e gaps na cadeia de custódia.

**Endurecimento:** Padronize procedimentos de aquisição e formulários de cadeia de custódia; use write-blockers validados; registre dois hashes independentes; armazene evidências em cofre com controle de acesso e logs; treine responders; minimize a interação com o sistema-alvo (evite desligar precipitadamente perdendo RAM); envolva jurídico cedo. Alinhe com NIST SP 800-86 e ISO/IEC 27037.

**Referências:**
- NIST SP 800-86 Guide to Integrating Forensic Techniques into Incident Response - https://csrc.nist.gov/pubs/sp/800/86/final
- ISO/IEC 27037 Guidelines for identification, collection, acquisition and preservation of digital evidence
- RFC 3227 Guidelines for Evidence Collection and Archiving - https://www.rfc-editor.org/rfc/rfc3227
- SWGDE Best Practices for Digital Evidence - https://www.swgde.org/
- Volatility Framework - https://www.volatilityfoundation.org/
- NIST Computer Forensics Tool Testing (CFTT) - https://www.nist.gov/itl/ssd/software-quality-group/computer-forensics-tool-testing-program-cftt

### Gestão de Vulnerabilidades e Patching (Vulnerability Management)

**Classificação:** `defensiva`

**O que é:** Processo contínuo de identificar, avaliar, priorizar e remediar vulnerabilidades em ativos e software, reduzindo a janela de exposição a exploração.

**Como funciona:** O ciclo começa com um inventário de ativos e software (incluindo SBOM para dependências) e varredura contínua (autenticada e não autenticada) que descobre vulnerabilidades identificadas por CVE. A priorização combina severidade técnica (CVSS), probabilidade de exploração (EPSS), exploração ativa conhecida (CISA KEV) e criticidade/contexto do ativo, porque remediar tudo é inviável — foca-se no que realmente reduz risco. A remediação aplica patches, mitigações ou controles compensatórios dentro de SLAs por severidade, seguida de verificação. Vulnerabilidades em componentes de terceiros (OWASP A06:2021) exigem atenção especial via gestão de dependências e SCA, pois herdam-se falhas sem código próprio.

**Detecção:** Fontes: scanners (rede, host, container, SCA), feeds NVD/vendor, CISA KEV e alertas de SBOM. Indicadores de programa fraco: ativos não inventariados/não escaneados, backlog crescente, SLAs vencidos, e software fora de suporte. Correlacione exposição externa com exploração ativa para priorizar.

**Endurecimento:** Mantenha inventário e SBOM atualizados; automatize varredura e correlação com KEV/EPSS; defina SLAs por risco (ex.: KEV em dias); teste patches em staging e tenha janela de emergência; use controles compensatórios (WAF/virtual patching, segmentação) quando patch imediato é inviável; elimine software sem suporte. Alinhe com SSVC/CISA para decisão de priorização.

**Referências:**
- OWASP Top 10 2021 A06:2021 Vulnerable and Outdated Components - https://owasp.org/Top10/A06_2021-Vulnerable_and_Outdated_Components/
- NIST SP 800-40 Rev. 4 Guide to Enterprise Patch Management Planning - https://csrc.nist.gov/pubs/sp/800/40/r4/final
- CISA Known Exploited Vulnerabilities (KEV) Catalog - https://www.cisa.gov/known-exploited-vulnerabilities-catalog
- FIRST EPSS Exploit Prediction Scoring System - https://www.first.org/epss/
- FIRST CVSS v4.0 - https://www.first.org/cvss/
- NIST National Vulnerability Database - https://nvd.nist.gov/
- CISA SSVC (Stakeholder-Specific Vulnerability Categorization) - https://www.cisa.gov/ssvc

### Logging Centralizado e SIEM (Security Information and Event Management)

**Classificação:** `defensiva`

**O que é:** Prática de coletar, normalizar, armazenar e correlacionar eventos de segurança de múltiplas fontes em uma plataforma central para detecção, investigação e retenção auditável.

**Como funciona:** Fontes heterogêneas (sistemas operacionais, aplicações, firewalls, IdP, EDR, nuvem) emitem logs que são coletados por agentes ou coletores (syslog, Windows Event Forwarding, agentes Beats/Fluentd), enviados a um pipeline que faz parsing, normalização em um schema comum e enriquecimento (GeoIP, threat intel). O SIEM indexa esses eventos e aplica regras de correlação e detecções (por assinatura, limiar, sequência temporal ou baseline estatístico) que geram alertas. A qualidade da detecção depende de cobertura de fontes, sincronização de tempo (NTP), integridade dos logs e uma taxonomia consistente. Falhas comuns são logging insuficiente, ausência de logs de eventos de segurança (login, autorização negada, alteração de privilégio) e retenção curta demais para investigar incidentes tardios.

**Detecção:** Meça cobertura: verifique se autenticação, autorização, mudanças de configuração e acesso a dados sensíveis geram eventos. Monitore lacunas de ingestão (fontes que pararam de enviar logs — sinal de tampering ou falha), dessincronização de relógio e volume anômalo. Use frameworks como MITRE ATT&CK para mapear cobertura de detecção (detection engineering coverage) e ferramentas como Sigma para regras portáveis, Wazuh/Elastic/Splunk/Microsoft Sentinel para correlação.

**Endurecimento:** Defina uma política de logging (o que registrar, sem PII/segredos em claro), sincronize relógios via NTP autenticado, envie logs para armazenamento append-only/WORM fora do host de origem, aplique controle de acesso e assinatura/hashing para integridade, e retenha conforme requisitos legais (ex.: 90-365 dias online, mais em arquivo frio). Nunca registre senhas, tokens ou dados de cartão; use mascaramento. Alinhe com OWASP ASVS V7 (logging) e NIST SP 800-92.

**Referências:**
- OWASP Top 10 2021 A09:2021 - Security Logging and Monitoring Failures - https://owasp.org/Top10/A09_2021-Security_Logging_and_Monitoring_Failures/
- NIST SP 800-92 Guide to Computer Security Log Management - https://csrc.nist.gov/pubs/sp/800/92/final
- CWE-778: Insufficient Logging - https://cwe.mitre.org/data/definitions/778.html
- CWE-117: Improper Output Neutralization for Logs - https://cwe.mitre.org/data/definitions/117.html
- OWASP ASVS v4 V7 Error Handling and Logging - https://owasp.org/www-project-application-security-verification-standard/
- MITRE ATT&CK - https://attack.mitre.org/

### Proteção de Dados Sensíveis em Logs (Sensitive Data in Logs / PII)

**Classificação:** `defensiva`

**O que é:** Registrar senhas, tokens, números de cartão, dados pessoais ou segredos em logs transforma a trilha de auditoria — muitas vezes amplamente acessível e retida por longos períodos — em uma fonte secundária de vazamento. O logging seguro equilibra rastreabilidade com minimização e mascaramento de dados sensíveis.

**Como funciona:** Logs são copiados para múltiplos destinos (arquivos, agregadores, SIEM, backups) e frequentemente acessíveis a mais pessoas do que os dados de produção. Quando a aplicação registra o corpo completo de requisições, cabeçalhos de autorização, parâmetros de formulário ou exceções com contexto, dados sensíveis acabam persistidos fora dos controles do sistema principal. O risco é agravado por retenção longa e por logs enviados a terceiros. A prática defensiva parte da minimização — não registrar o que não é necessário — combinada com mascaramento/redação de campos sensíveis na origem, controle de acesso aos logs e políticas de retenção. Também é importante registrar o suficiente para detecção e forense (quem, quando, o quê) sem expor o conteúdo sensível em si.

**Detecção:** Execute varreduras periódicas nos logs por padrões de dados sensíveis (formatos de cartão, tokens, cabeçalhos de autorização, campos de senha) e alerte para ocorrências. Instrumente a camada de logging para sinalizar campos marcados como sensíveis. Revise, em code review, chamadas de log que serializam objetos inteiros ou corpos de requisição. Monitore acessos e exportações dos repositórios de log.

**Endurecimento:** Adote minimização: registre identificadores e metadados de evento em vez de conteúdo bruto. Aplique mascaramento/redação de campos sensíveis na origem, antes da escrita, usando uma lista de campos protegidos. Nunca registre senhas, segredos, tokens completos ou credenciais; trunque ou faça hash quando um identificador for necessário. Restrinja e audite o acesso aos logs, cifre em trânsito e em repouso, e defina retenção proporcional. Alinhe as práticas às exigências de privacidade aplicáveis e teste que dados sensíveis não apareçam nos destinos de log.

**Referências:**
- OWASP Cheat Sheet Series: Logging
- OWASP Top 10 A09:2021 Security Logging and Monitoring Failures
- CWE-532: Insertion of Sensitive Information into Log File
- NIST SP 800-92: Guide to Computer Security Log Management

### Resiliência a Ransomware e Backups (Regra 3-2-1)

**Classificação:** `defensiva`

**O que é:** Conjunto de práticas de backup e recuperação — notavelmente a regra 3-2-1 e backups imutáveis/isolados — que garante restauração confiável após ransomware sem pagar resgate.

**Como funciona:** Ransomware criptografa dados e frequentemente exfiltra antes (double extortion), buscando também destruir backups acessíveis (shadow copies, snapshots, repositórios em rede) para forçar o pagamento. A regra 3-2-1 mantém 3 cópias dos dados, em 2 mídias diferentes, com 1 cópia off-site; variantes modernas (3-2-1-1-0) acrescentam 1 cópia imutável/air-gapped e 0 erros de restauração verificados. Backups imutáveis (WORM, object lock) e isolados por credenciais separadas impedem que o atacante, mesmo com acesso de domínio, apague ou cifre as cópias. A recuperação depende de RPO (perda máxima aceitável) e RTO (tempo de restauração) definidos, e de restaurações testadas regularmente, pois um backup nunca testado é uma suposição.

**Detecção:** Sinais precoces: exclusão em massa de shadow copies (vssadmin delete shadows), desativação de serviços de backup, picos de renomeação/escrita de arquivos, entropia crescente em arquivos, e alertas do EDR sobre ferramentas de criptografia. Monitore falhas e alterações inesperadas nos jobs de backup e acessos anômalos ao repositório de backup.

**Endurecimento:** Implemente 3-2-1(-1-0) com pelo menos uma cópia imutável/air-gapped e credenciais isoladas; teste restaurações periodicamente e meça RTO/RPO reais; segmente e proteja a infraestrutura de backup como ativo crítico; combine com MFA, segmentação de rede, patching, allowlisting e EDR; tenha um playbook de recuperação de ransomware. Siga o CISA #StopRansomware e NIST SP 1800-11/1800-25/1800-26.

**Referências:**
- CISA #StopRansomware Guide - https://www.cisa.gov/stopransomware
- NIST SP 1800-11 Data Integrity: Recovering from Ransomware - https://www.nccoe.nist.gov/data-integrity-recovering-ransomware-and-other-destructive-events
- NIST SP 800-184 Guide for Cybersecurity Event Recovery - https://csrc.nist.gov/pubs/sp/800/184/final
- MITRE ATT&CK T1486 Data Encrypted for Impact - https://attack.mitre.org/techniques/T1486/
- MITRE ATT&CK T1490 Inhibit System Recovery - https://attack.mitre.org/techniques/T1490/
- NIST Cybersecurity Framework 2.0 (Recover) - https://www.nist.gov/cyberframework

### Threat Hunting (Caça Proativa a Ameaças)

**Classificação:** `defensiva`

**O que é:** Busca proativa e iterativa por ameaças que evadiram controles automáticos, guiada por hipóteses baseadas em TTPs de adversários e no conhecimento do ambiente.

**Como funciona:** O hunter formula uma hipótese (ex.: um adversário estaria usando uma técnica ATT&CK específica de persistência), identifica a telemetria necessária e consulta os dados buscando evidências, ausência de evidências ou anomalias em relação a uma linha de base conhecida. Técnicas incluem stack counting/frequency analysis (o raro é suspeito), clustering e enriquecimento com threat intel. Descobertas viram novas detecções automatizadas (fechando a lacuna) ou incidentes; achados nulos aumentam a confiança e refinam a hipótese. A caça foca nos comportamentos difíceis de mudar do adversário (topo da Pyramid of Pain — TTPs) em vez de indicadores frágeis, e prioriza os ativos críticos (crown jewels).

**Detecção:** Threat hunting complementa detecção automática; sua saída são novas regras Sigma/EDR, IOCs e melhorias de telemetria. Métricas incluem número de hunts, detecções geradas, tempo de permanência (dwell time) reduzido e cobertura ATT&CK aumentada. Requer dados ricos e retidos por tempo suficiente.

**Endurecimento:** Estabeleça um programa de hunting com cadência, biblioteca de hipóteses mapeadas a ATT&CK, e feedback loop para detecção-como-código; garanta telemetria abrangente e retida; treine analistas; use modelos como o TaHiTI e o Hunting Maturity Model. Documente cada hunt para reprodutibilidade.

**Referências:**
- MITRE ATT&CK - https://attack.mitre.org/
- The Pyramid of Pain - David Bianco - https://detect-respond.blogspot.com/2013/03/the-pyramid-of-pain.html
- Sqrrl Hunting Maturity Model / Threat Hunting Loop
- TaHiTI Threat Hunting Methodology - https://www.betaalvereniging.nl/en/safety/tahiti/
- MITRE ATT&CK Data Sources - https://attack.mitre.org/datasources/
- NIST SP 800-137 ISCM - https://csrc.nist.gov/pubs/sp/800/137/final

## Identidade Corporativa e Endpoint

### Abuso de Delegação Kerberos e Tickets Forjados (Kerberos Delegation / Golden Ticket)

**Classificação:** `defensiva`

**O que é:** Conjunto de abusos de configurações de delegação Kerberos e de forja de tickets (Golden/Silver) que concedem personificação e persistência no domínio.

**Como funciona:** A delegação Kerberos permite que um serviço aja em nome de um usuário; quando mal configurada (delegação irrestrita, restrita com proteção fraca ou delegação restrita baseada em recurso - RBCD), um serviço comprometido pode personificar usuários privilegiados. Já os tickets forjados exploram o comprometimento de chaves: com o hash da conta krbtgt, um atacante cria um Golden Ticket (TGT arbitrário e persistente); com a chave de uma conta de serviço, cria um Silver Ticket (TGS para um serviço específico). Esses tickets são aceitos como legítimos porque o KDC/serviço confia na assinatura derivada da chave comprometida. Representam persistência e escalada, geralmente após comprometimento prévio.

**Detecção:** Audite atributos de delegação (msDS-AllowedToDelegateTo, TrustedForDelegation, msDS-AllowedToActOnBehalfOfOtherIdentity). Monitore Eventos 4769/4768 com anomalias (tickets com tempo de vida excessivo, contas inexistentes, cifras inconsistentes). Microsoft Defender for Identity detecta Golden Ticket e delegação suspeita. Ferramentas defensivas: BloodHound para mapear caminhos de delegação; PingCastle/Purple Knight para higiene de AD.

**Endurecimento:** Elimine delegação irrestrita; prefira delegação restrita com 'Protocol Transition' desabilitado quando possível. Marque contas sensíveis como 'Account is sensitive and cannot be delegated' e coloque-as em Protected Users. Rotacione a senha da krbtgt duas vezes periodicamente e após qualquer suspeita de comprometimento. Restrinja quem pode configurar RBCD e monitore alterações. Aplique Authentication Policies e Silos.

**Referências:**
- MITRE ATT&CK T1558.001 Golden Ticket - https://attack.mitre.org/techniques/T1558/001/
- MITRE ATT&CK T1558.002 Silver Ticket - https://attack.mitre.org/techniques/T1558/002/
- Microsoft - Kerberos Constrained Delegation Overview - https://learn.microsoft.com/windows-server/security/kerberos/kerberos-constrained-delegation-overview
- Microsoft - KRBTGT account maintenance - https://learn.microsoft.com/defender-for-identity/
- RFC 4120 - The Kerberos Network Authentication Service (V5) - https://datatracker.ietf.org/doc/html/rfc4120

### AS-REP Roasting (AS-REP Roasting)

**Classificação:** `escopo_autorizado`

**O que é:** Técnica que explora contas com pré-autenticação Kerberos desabilitada para obter uma resposta AS-REP cifrada e quebrar a senha offline.

**Como funciona:** Quando uma conta tem o atributo 'Do not require Kerberos preauthentication' (flag UAC DONT_REQ_PREAUTH) ativado, o KDC responde a uma solicitação AS-REQ com um AS-REP contendo dados cifrados com a chave derivada da senha do usuário, sem exigir prova prévia de conhecimento da senha. Isso permite que qualquer um solicite essa resposta para a conta e tente quebrar a senha offline, de forma análoga ao Kerberoasting, mas sem sequer precisar de credenciais válidas no domínio. Contas legadas ou de aplicações antigas às vezes têm esse flag por compatibilidade, criando exposição desnecessária.

**Detecção:** Enumere periodicamente contas com userAccountControl contendo o bit 0x400000 (DONT_REQ_PREAUTH) via consultas LDAP/PowerShell. Monitore o Evento 4768 (AS-REQ/TGT) com pré-autenticação ausente (Pre-Authentication Type 0) e tipo de cifra RC4. Regras Sigma e SIEM podem alertar sobre padrões de solicitação em massa de TGTs sem pré-autenticação.

**Endurecimento:** Remova o flag DONT_REQ_PREAUTH de todas as contas, salvo justificativa documentada e compensada. Force AES em vez de RC4, aplique senhas longas e rotacionadas, e audite regularmente o atributo userAccountControl. Aplique Authentication Policies para contas privilegiadas.

**Referências:**
- MITRE ATT&CK T1558.004 AS-REP Roasting - https://attack.mitre.org/techniques/T1558/004/
- RFC 4120 - The Kerberos Network Authentication Service (V5) - https://datatracker.ietf.org/doc/html/rfc4120
- Microsoft - userAccountControl flags - https://learn.microsoft.com/troubleshoot/windows-server/active-directory/useraccountcontrol-manipulate-account-properties
- CWE-521 Weak Password Requirements - https://cwe.mitre.org/data/definitions/521.html

### Coerção de Autenticação e Retransmissão NTLM (NTLM Relay)

**Classificação:** `defensiva`

**O que é:** Ataque em que a autenticação NTLM de uma vítima é retransmitida para um serviço-alvo, autenticando o atacante como a vítima sem quebrar a senha.

**Como funciona:** O NTLM é um protocolo de desafio-resposta que não vincula, por padrão, a autenticação ao canal ou ao servidor de destino. Um atacante posicionado no meio (ou que coage um host a autenticar-se contra ele, via mecanismos como MS-EFSRPC ou o bug do spooler) pode encaminhar o desafio-resposta para outro serviço (SMB, LDAP, HTTP/AD CS) e assumir a sessão autenticada da vítima. Se o serviço-alvo não exige assinatura (signing) ou channel binding, o atacante executa ações com o privilégio da conta coagida — por exemplo, requisitar um certificado em uma AC vulnerável (ESC8). É uma falha de vinculação de autenticação, não de senha.

**Detecção:** Monitore coerção via Eventos de acesso a pipes MS-EFSRPC/spooler, logons NTLM inesperados de contas de máquina (conta$), e requisições anômalas ao AD CS (Eventos 4886/4887). Sysmon e regras Sigma detectam ferramentas de relay. Microsoft Defender for Identity sinaliza relay e coerção. Audite endpoints de AD CS expostos por HTTP.

**Endurecimento:** Exija SMB signing e LDAP signing + LDAP channel binding em todo o ambiente. Habilite Extended Protection for Authentication (EPA) nos serviços web, incluindo AD CS. Desabilite NTLM onde possível e restrinja com políticas de segurança. Bloqueie/filtre coerção (patch para PetitPotam, desabilitar o serviço Print Spooler onde não necessário). Reforce AD CS (remover HTTP, exigir EPA, mitigar ESC1-ESC8).

**Referências:**
- MITRE ATT&CK T1557.001 Adversary-in-the-Middle: LLMNR/NBT-NS Poisoning and SMB Relay - https://attack.mitre.org/techniques/T1557/001/
- Microsoft KB5005413 - Mitigating NTLM Relay Attacks on Active Directory Certificate Services - https://support.microsoft.com/topic/kb5005413
- Microsoft - Network security: Restrict NTLM - https://learn.microsoft.com/windows/security/threat-protection/security-policy-settings/network-security-restrict-ntlm-in-this-domain
- CWE-287 Improper Authentication - https://cwe.mitre.org/data/definitions/287.html
- CWE-290 Authentication Bypass by Spoofing - https://cwe.mitre.org/data/definitions/290.html

### Defesa contra Phishing e Engenharia Social (Phishing and Social Engineering Defense)

**Classificação:** `defensiva`

**O que é:** Conjunto de controles técnicos e humanos para prevenir, detectar e responder a ataques que manipulam usuários para roubar credenciais ou executar código.

**Como funciona:** A engenharia social explora a confiança e a urgência humanas para induzir a vítima a clicar em links maliciosos, abrir anexos, fornecer credenciais/OTP ou aprovar solicitações fraudulentas (BEC, fadiga de MFA, phishing adversary-in-the-middle que rouba tokens de sessão). Ataques modernos contornam MFA capturando o cookie de sessão em tempo real via proxies reversos. A defesa combina controles técnicos (filtragem de e-mail, autenticação de domínio, MFA resistente a phishing) com fatores humanos (treinamento, cultura de reporte) e processos de verificação para transações sensíveis. Nenhuma camada é suficiente isoladamente.

**Detecção:** Monitore ganhos de sinal de gateways de e-mail seguros e relatórios DMARC (falhas de SPF/DKIM), URLs e anexos detonados em sandbox, e logins anômalos (impossible travel, novos dispositivos). Facilite o reporte de phishing pelos usuários (botão de report) e meça taxa de clique/report em simulações. Defender for Office 365/UEBA sinalizam AiTM e BEC.

**Endurecimento:** Implemente MFA resistente a phishing (FIDO2/WebAuthn, passkeys) e number matching para evitar fadiga de MFA. Configure SPF, DKIM e DMARC em p=reject; use gateway de e-mail seguro com detonação de anexos/URLs. Aplique número matching, políticas de acesso condicional, e processos de verificação fora de banda para transferências financeiras. Realize treinamento contínuo e simulações de phishing com métricas.

**Referências:**
- MITRE ATT&CK T1566 Phishing - https://attack.mitre.org/techniques/T1566/
- NIST SP 800-50r1 Building a Cybersecurity and Privacy Learning Program - https://csrc.nist.gov/pubs/sp/800/50/r1/final
- CISA - Phishing Guidance: Stopping the Attack Cycle at Phase One - https://www.cisa.gov/resources-tools/resources/phishing-guidance-stopping-attack-cycle-phase-one
- DMARC - RFC 7489 - https://datatracker.ietf.org/doc/html/rfc7489
- FIDO Alliance - Passkeys / WebAuthn - https://fidoalliance.org/

### Detecção e Resposta em Endpoint e Endpoint Hardening (EDR/XDR)

**Classificação:** `defensiva`

**O que é:** Uso de EDR/XDR e endurecimento de endpoint para coletar telemetria, detectar comportamento malicioso e responder a incidentes em estações e servidores.

**Como funciona:** EDR instala um sensor no endpoint que coleta telemetria rica (criação de processos, injeção, acesso a memória, rede, registro, arquivos) e a correlaciona com heurísticas comportamentais e IOCs para detectar atividade maliciosa que evade antivírus baseado em assinatura. A plataforma permite investigação, contenção (isolar host, matar processo) e resposta remota, muitas vezes mapeando alertas ao MITRE ATT&CK. XDR estende a correlação para identidade, e-mail, nuvem e rede. A eficácia depende de cobertura completa da frota, proteção contra desativação (tamper protection) e ajuste para reduzir falsos positivos.

**Detecção:** O próprio EDR é o mecanismo de detecção; complemente com Sysmon (config tipo SwiftOnSecurity) para telemetria detalhada, encaminhando para SIEM. Monitore tentativas de desabilitar o sensor, lacunas de cobertura (hosts sem agente) e alertas mapeados a técnicas ATT&CK. Valide detecção com exercícios de emulação de adversário (Atomic Red Team) em ambiente autorizado.

**Endurecimento:** Implante EDR em 100% dos endpoints e servidores com tamper protection habilitado e credenciais de console protegidas por MFA. Habilite regras ASR, bloqueio de PUA, proteção em nuvem e resposta automatizada. Integre com SIEM/SOAR para playbooks de resposta. Mantenha o sensor atualizado e monitore cobertura e saúde dos agentes continuamente.

**Referências:**
- MITRE ATT&CK - Enterprise Matrix - https://attack.mitre.org/matrices/enterprise/
- NIST SP 800-61r2 Computer Security Incident Handling Guide - https://csrc.nist.gov/pubs/sp/800/61/r2/final
- Microsoft Defender for Endpoint documentation - https://learn.microsoft.com/defender-endpoint/
- MITRE Engenuity - Atomic Red Team - https://github.com/redcanaryco/atomic-red-team
- NIST SP 800-137 Information Security Continuous Monitoring - https://csrc.nist.gov/pubs/sp/800/137/final

### Gestão de Acesso Privilegiado e Tiering (PAM and Administrative Tiering)

**Classificação:** `defensiva`

**O que é:** Modelo e ferramentas para isolar, controlar e auditar contas administrativas, limitando onde e quando credenciais privilegiadas podem ser usadas.

**Como funciona:** Credenciais privilegiadas são o alvo principal de atacantes; o modelo de tiering (Tier 0 = identidade/controladores de domínio, Tier 1 = servidores, Tier 2 = estações) impede que credenciais de nível superior sejam expostas em hosts de nível inferior, cortando caminhos de escalada. Soluções de PAM adicionam cofre de senhas (vaulting), acesso just-in-time (JIT) com elevação temporária e aprovada, gravação de sessão e rotação automática de segredos. Estações administrativas dedicadas (PAW) e contas administrativas separadas garantem que tarefas privilegiadas ocorram em superfícies confiáveis. O objetivo é reduzir a exposição temporal e espacial das credenciais.

**Detecção:** Monitore uso de contas privilegiadas fora do fluxo PAM (bypass do cofre), elevações JIT e aprovações, e logons de contas Tier 0 em hosts de tiers inferiores (violação de tiering). Audite gravações de sessão e alertas de acesso emergencial (break-glass). Ferramentas: Entra PIM, soluções PAM (CyberArk, Delinea) e Defender for Identity para caminhos de ataque.

**Endurecimento:** Implemente tiering com Authentication Policies/Silos e Protected Users. Use PAM com JIT, aprovação, cofre e rotação; adote PAWs para administração de Tier 0. Aplique menor privilégio, remova admins permanentes (standing access), exija MFA para elevação e registre/grave sessões privilegiadas. Estabeleça contas break-glass monitoradas.

**Referências:**
- Microsoft - Enterprise access model / Privileged access strategy - https://learn.microsoft.com/security/privileged-access-workstations/privileged-access-access-model
- Microsoft Entra Privileged Identity Management (PIM) - https://learn.microsoft.com/entra/id-governance/privileged-identity-management/
- NIST SP 800-53r5 AC-6 Least Privilege - https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final
- MITRE ATT&CK T1078 Valid Accounts - https://attack.mitre.org/techniques/T1078/
- CISA - Zero Trust Maturity Model - https://www.cisa.gov/zero-trust-maturity-model

### Gestão de Patches e Vulnerabilidades (Patch and Vulnerability Management)

**Classificação:** `defensiva`

**O que é:** Processo contínuo de identificar, priorizar e aplicar correções de segurança para reduzir a janela de exposição a vulnerabilidades conhecidas.

**Como funciona:** Vulnerabilidades conhecidas (identificadas por CVE) são publicadas continuamente e frequentemente exploradas pouco após a divulgação; a gestão de patches reduz a janela entre a disponibilização da correção e sua aplicação. O processo envolve inventário de ativos, varredura de vulnerabilidades, priorização por risco (CVSS, presença no catálogo KEV da CISA, exposição e criticidade do ativo), testes e implantação controlada com janelas de manutenção e rollback. Métricas como tempo médio de remediação (MTTR) e conformidade de patch medem a eficácia. A priorização baseada em risco evita tratar todas as CVEs igualmente.

**Detecção:** Use scanners de vulnerabilidade (Nessus/Tenable, Qualys, OpenVAS, Defender Vulnerability Management) e inventário de ativos para identificar sistemas sem patch. Correlacione com o CISA KEV e feeds de inteligência para priorizar. Relatórios de conformidade de patch (WSUS/SCCM/Intune) e dashboards de exposição indicam pendências e drift.

**Endurecimento:** Estabeleça política de patch com SLAs por severidade (ex.: crítico/KEV em prazo curto) e cobertura de SO, firmware e aplicações de terceiros. Automatize a distribuição (Intune/SCCM/WSUS, gerenciadores de pacotes) com anéis de implantação e testes. Mantenha inventário preciso, aplique mitigação compensatória quando patch não for possível e meça MTTR e conformidade.

**Referências:**
- NIST SP 800-40r4 Guide to Enterprise Patch Management Planning - https://csrc.nist.gov/pubs/sp/800/40/r4/final
- CISA Known Exploited Vulnerabilities (KEV) Catalog - https://www.cisa.gov/known-exploited-vulnerabilities-catalog
- FIRST CVSS - Common Vulnerability Scoring System - https://www.first.org/cvss/
- CWE-1104 Use of Unmaintained Third Party Components - https://cwe.mitre.org/data/definitions/1104.html
- MITRE ATT&CK T1190 Exploit Public-Facing Application - https://attack.mitre.org/techniques/T1190/

### Gestão de Senhas de Administrador Local (LAPS / Windows LAPS)

**Classificação:** `defensiva`

**O que é:** Solução que gera, rotaciona e armazena com segurança senhas únicas e aleatórias de administrador local para cada máquina, mitigando reutilização de credenciais.

**Como funciona:** O reuso da mesma senha de administrador local em muitas máquinas permite que o comprometimento de uma leve ao comprometimento de toda a frota via Pass-the-Hash. O LAPS (e o Windows LAPS moderno) gera uma senha aleatória e única por dispositivo, rotaciona-a automaticamente e a armazena em atributos protegidos no Active Directory ou no Entra ID, com controle de acesso por ACL a quem pode lê-la. Cada leitura pode disparar rotação, e o histórico e a expiração são gerenciados centralmente. Isso remove um caminho comum de movimento lateral sem impedir o uso legítimo emergencial.

**Detecção:** Audite leituras de senha LAPS (Eventos de acesso ao atributo ms-Mcs-AdmPwd / atributos do Windows LAPS, Evento 4662) e alertas para leituras anômalas. Verifique cobertura: máquinas sem LAPS aplicado, senhas expiradas ou não rotacionando. Confirme ACLs restritas nos atributos e ausência de contas locais compartilhadas fora do LAPS.

**Endurecimento:** Implante Windows LAPS em toda a frota com rotação frequente e senhas longas/complexas. Restrinja por ACL quem pode ler as senhas e habilite auditoria de acesso. Considere criptografia de senha (Windows LAPS suporta criptografia no AD) e integração com Entra ID. Combine com desativação/renomeação de contas locais desnecessárias e modelo de tiering.

**Referências:**
- Microsoft - Windows LAPS overview - https://learn.microsoft.com/windows-server/identity/laps/laps-overview
- Microsoft - Mitigating Pass-the-Hash Attacks - https://www.microsoft.com/en-us/download/details.aspx?id=36036
- CWE-798 Use of Hard-coded Credentials - https://cwe.mitre.org/data/definitions/798.html
- CWE-521 Weak Password Requirements - https://cwe.mitre.org/data/definitions/521.html
- MITRE ATT&CK T1078.003 Valid Accounts: Local Accounts - https://attack.mitre.org/techniques/T1078/003/

### Hardening de Linux e Baselines CIS (Linux Hardening / CIS Benchmarks)

**Classificação:** `defensiva`

**O que é:** Aplicação de baselines de configuração segura em hosts Linux, reduzindo serviços, endurecendo kernel, autenticação e controle de acesso mandatório.

**Como funciona:** Distribuições Linux instalam serviços e permissões voltados à usabilidade, deixando portas abertas, montagens permissivas, parâmetros de kernel padrão e SSH com configurações amplas. Baselines CIS/STIG definem um conjunto verificável de controles: desativação de serviços desnecessários, políticas de senha e sudo, parâmetros sysctl de rede/kernel, permissões de arquivos sensíveis, e controle de acesso mandatório (SELinux/AppArmor). Auditoria (auditd) e integridade de arquivos (AIDE) fornecem telemetria e detecção de manipulação. A conformidade é medida e o drift, corrigido continuamente.

**Detecção:** Avalie conformidade com OpenSCAP/SCAP Security Guide, CIS-CAT, Lynis e ferramentas de gestão (Ansible/Chef com perfis de hardening). Monitore logs do auditd, integridade com AIDE/Tripwire, e desvios de configuração via automação. Verifique SSH endurecido e ausência de serviços legados abertos (ss/nmap em escopo autorizado).

**Endurecimento:** Aplique um perfil CIS/STIG via automação idempotente. Habilite SELinux (enforcing) ou AppArmor, endureça SSH (sem root login, chaves em vez de senha, MFA), restrinja sudo com menor privilégio, configure sysctl seguro, monte partições com noexec/nosuid/nodev onde aplicável, habilite firewall (nftables/firewalld) e auditd. Remova pacotes/serviços não usados e gerencie drift continuamente.

**Referências:**
- CIS Linux Benchmarks - https://www.cisecurity.org/benchmark/distribution_independent_linux
- SCAP Security Guide / OpenSCAP - https://www.open-scap.org/security-policies/scap-security-guide/
- DISA STIGs (Linux) - https://public.cyber.mil/stigs/
- NIST SP 800-123 Guide to General Server Security - https://csrc.nist.gov/pubs/sp/800/123/final
- SELinux Project Documentation - https://github.com/SELinuxProject

### Hardening de Windows e Baselines CIS (Windows Hardening / CIS Benchmarks)

**Classificação:** `defensiva`

**O que é:** Aplicação de baselines de configuração segura (CIS, Microsoft Security Baselines, DISA STIG) para reduzir a superfície de ataque em endpoints e servidores Windows.

**Como funciona:** Sistemas operacionais vêm com padrões voltados à compatibilidade, não à segurança máxima, deixando recursos legados, protocolos fracos e permissões amplas habilitados. Baselines como CIS Benchmarks e Microsoft Security Baselines definem centenas de configurações endurecidas (políticas de senha, auditoria, desativação de protocolos inseguros, controle de contas, regras ASR) aplicadas via GPO, Intune ou ferramentas de configuração. O objetivo é reduzir a superfície de ataque e habilitar telemetria de segurança de forma consistente e mensurável em toda a frota. A conformidade é verificada continuamente contra o baseline para detectar desvios (drift).

**Detecção:** Use ferramentas de avaliação de conformidade: Microsoft Security Compliance Toolkit (Policy Analyzer), CIS-CAT, SCAP/OpenSCAP, Intune compliance policies e Microsoft Defender for Endpoint (Configuration Score / Exposure). Detecte drift comparando o estado atual com o baseline exportado; audite alterações de GPO (Eventos 5136/4739).

**Endurecimento:** Adote um baseline (CIS Level 1/2 ou Microsoft Security Baseline) e aplique via GPO/Intune com exceções documentadas. Habilite regras ASR (Attack Surface Reduction), controle de aplicações (WDAC/AppLocker), Credential Guard, BitLocker, auditoria avançada e desative SMBv1/LLMNR/NBT-NS. Gerencie desvios com processo formal e reavalie a cada ciclo de patch/versão.

**Referências:**
- CIS Microsoft Windows Benchmarks - https://www.cisecurity.org/benchmark/microsoft_windows_desktop
- Microsoft Security Baselines / Security Compliance Toolkit - https://learn.microsoft.com/windows/security/operating-system-security/device-management/windows-security-configuration-framework/security-compliance-toolkit-10
- DISA STIGs - https://public.cyber.mil/stigs/
- NIST SP 800-123 Guide to General Server Security - https://csrc.nist.gov/pubs/sp/800/123/final
- Microsoft - Attack Surface Reduction rules - https://learn.microsoft.com/defender-endpoint/attack-surface-reduction

### Kerberoasting (Kerberoasting)

**Classificação:** `escopo_autorizado`

**O que é:** Técnica que abusa do Kerberos para obter tickets de serviço (TGS) cifrados com a senha de contas de serviço e quebrá-los offline por força bruta.

**Como funciona:** No Kerberos, qualquer usuário autenticado do domínio pode solicitar um ticket de serviço (TGS-REP) para qualquer conta com um SPN (Service Principal Name) registrado, sem que o serviço precise estar acessível. Parte desse ticket é cifrada com a chave derivada da senha da conta de serviço, então um atacante que capture o TGS pode tentar quebrar a senha offline sem gerar tráfego adicional no domínio. Contas de serviço frequentemente têm senhas fracas, antigas e sem rotação, e o uso do tipo de cifra RC4 (etype 23) facilita a quebra em comparação com AES. O ataque é atraente por ser silencioso: a solicitação do ticket é uma operação legítima e comum no protocolo.

**Detecção:** Monitore o Evento de Segurança do Windows 4769 (solicitação de TGS) com Ticket Encryption Type 0x17 (RC4) e Ticket Options anômalas, especialmente picos de solicitações de muitos SPNs distintos por uma única conta em curto intervalo. Correlacione com ferramentas de SIEM/UEBA e regras Sigma para 'kerberoasting'. Contas honeypot (decoy) com SPN e senha longa detectam solicitações suspeitas. Ferramentas como Microsoft Defender for Identity e BloodHound (para mapear a superfície de SPNs) apoiam a análise defensiva.

**Endurecimento:** Use gMSA/dMSA (Group/Delegated Managed Service Accounts) com senhas de 120+ caracteres rotacionadas automaticamente. Desabilite RC4 e force AES nas contas de serviço (msDS-SupportedEncryptionTypes). Aplique senhas longas e aleatórias (25+ caracteres) para contas de serviço legadas e rotacione-as. Reduza o número de contas com SPN, aplique menor privilégio a essas contas e monitore-as continuamente. Considere Authentication Policies e Silos para contas sensíveis.

**Referências:**
- MITRE ATT&CK T1558.003 Steal or Forge Kerberos Tickets: Kerberoasting - https://attack.mitre.org/techniques/T1558/003/
- Microsoft - Managed Service Accounts / gMSA - https://learn.microsoft.com/windows-server/security/group-managed-service-accounts/group-managed-service-accounts-overview
- RFC 4120 - The Kerberos Network Authentication Service (V5) - https://datatracker.ietf.org/doc/html/rfc4120
- Microsoft - Detecting Kerberoasting activity - https://techcommunity.microsoft.com/
- CWE-522 Insufficiently Protected Credentials - https://cwe.mitre.org/data/definitions/522.html

### Menor Privilégio no Endpoint (Endpoint Least Privilege)

**Classificação:** `defensiva`

**O que é:** Remoção de direitos administrativos locais desnecessários e controle de aplicações para limitar o impacto de comprometimentos no endpoint.

**Como funciona:** Usuários operando com direitos de administrador local ampliam drasticamente o impacto de malware e phishing, pois código executado herda privilégios elevados para desabilitar defesas, instalar persistência e roubar credenciais. O menor privilégio remove admin local padrão, concedendo elevação apenas quando necessário e de forma controlada (elevação por aplicação/tarefa via EPM - Endpoint Privilege Management). Complementarmente, o controle de aplicações (allowlisting via WDAC/AppLocker) impede a execução de binários não autorizados. Juntas, essas medidas contêm a maioria das técnicas de execução e escalada no host. É a aplicação do princípio de menor privilégio na camada de endpoint.

**Detecção:** Enumere contas com admin local por máquina (drift de membros do grupo Administradores), solicitações de elevação (UAC) e execuções bloqueadas/permitidas pelo controle de aplicações (Eventos AppLocker/WDAC). Monitore instalações de software fora do processo autorizado e ferramentas de EPM para pedidos de elevação anômalos.

**Endurecimento:** Remova admin local dos usuários padrão e use EPM para elevação por aplicação com aprovação/política. Implemente allowlisting (WDAC em enforcement, AppLocker) e regras ASR. Mantenha UAC no nível máximo, separe contas administrativas, e aplique menor privilégio também a serviços e tarefas agendadas. Audite continuamente membros de grupos privilegiados.

**Referências:**
- CWE-250 Execution with Unnecessary Privileges - https://cwe.mitre.org/data/definitions/250.html
- CWE-269 Improper Privilege Management - https://cwe.mitre.org/data/definitions/269.html
- NIST SP 800-53r5 AC-6 Least Privilege - https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final
- Microsoft - Windows Defender Application Control (WDAC) - https://learn.microsoft.com/windows/security/application-security/application-control/windows-defender-application-control/
- MITRE ATT&CK T1548 Abuse Elevation Control Mechanism - https://attack.mitre.org/techniques/T1548/

### MFA Corporativo e SSO (Corporate MFA and Single Sign-On)

**Classificação:** `defensiva`

**O que é:** Autenticação multifator e logon único federado para reforçar a verificação de identidade e centralizar o controle de acesso corporativo.

**Como funciona:** SSO federa a autenticação em um provedor de identidade central (via SAML ou OpenID Connect/OAuth 2.0), reduzindo a proliferação de senhas e permitindo políticas centralizadas. O MFA adiciona fatores além da senha (posse, biometria), mas nem todo MFA é igual: OTP e push simples são vulneráveis a phishing AiTM e fadiga de MFA, enquanto FIDO2/WebAuthn e passkeys vinculam a autenticação à origem (origin binding), resistindo a phishing. Acesso condicional avalia risco (dispositivo, localização, sinal de risco) para exigir mais fatores ou bloquear. A robustez depende de escolher fatores resistentes a phishing e de proteger o próprio IdP.

**Detecção:** Monitore logins com falha de MFA, padrões de fadiga (muitos pushes), autenticações legadas que ignoram MFA (protocolos legacy), e sinais de AiTM (reuso de token/sessão de IP incomum). Relatórios de risco do IdP (Entra ID Protection), impossible travel e concessões OAuth suspeitas. Audite aplicações federadas e consentimentos.

**Endurecimento:** Exija MFA resistente a phishing (FIDO2/WebAuthn, passkeys, certificados) para contas privilegiadas e, idealmente, para todos. Bloqueie protocolos de autenticação legados, aplique acesso condicional baseado em risco e conformidade de dispositivo, e habilite number matching. Proteja o IdP como Tier 0, monitore consentimentos OAuth e aplique tokens de curta duração com revogação.

**Referências:**
- NIST SP 800-63B Digital Identity Guidelines: Authentication - https://pages.nist.gov/800-63-3/sp800-63b.html
- OWASP Authentication Cheat Sheet - https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html
- FIDO Alliance - FIDO2 / WebAuthn - https://fidoalliance.org/fido2/
- CISA - Implementing Phishing-Resistant MFA - https://www.cisa.gov/resources-tools/resources/implementing-phishing-resistant-mfa
- OWASP API Security Top 10 2023 - API2:2023 Broken Authentication - https://owasp.org/API-Security/editions/2023/en/0xa2-broken-authentication/

### Pass-the-Hash (PtH)

**Classificação:** `defensiva`

**O que é:** Técnica de movimento lateral em que o hash NTLM de um usuário é reutilizado para autenticar sem conhecer a senha em texto claro.

**Como funciona:** A autenticação NTLM prova o conhecimento da senha usando o hash NT diretamente, sem que a senha em texto claro seja necessária no fluxo. Se um atacante obtém o hash NT (por exemplo, da memória do processo LSASS ou de bancos de credenciais em cache), ele pode apresentá-lo a serviços que aceitam NTLM e autenticar como o usuário, movendo-se lateralmente. O problema é agravado quando a mesma senha de administrador local é reutilizada em muitas máquinas, permitindo comprometer toda a frota a partir de um único host. É uma técnica de reutilização de credenciais, não de quebra de senha.

**Detecção:** Monitore logons NTLM anômalos (Evento 4624 com Logon Type 3 e pacote de autenticação NTLM) entre estações, especialmente de contas administrativas locais. Correlacione acesso a LSASS (Sysmon Event ID 10, handles para lsass.exe) com ferramentas de dump. Microsoft Defender for Identity detecta padrões de PtH; UEBA/SIEM identificam uso da mesma conta em múltiplos hosts em curto intervalo.

**Endurecimento:** Elimine senhas de administrador local reutilizadas com LAPS/Windows LAPS. Implemente modelo de tiering (tier 0/1/2) para impedir que credenciais privilegiadas toquem estações menos confiáveis. Habilite Credential Guard, Protected Users group, Restricted Admin/RDP e restrinja NTLM (preferindo Kerberos). Aplique menor privilégio, remova direitos de admin local desnecessários e use contas administrativas dedicadas por tier.

**Referências:**
- MITRE ATT&CK T1550.002 Use Alternate Authentication Material: Pass the Hash - https://attack.mitre.org/techniques/T1550/002/
- Microsoft - Mitigating Pass-the-Hash and Other Credential Theft - https://www.microsoft.com/en-us/download/details.aspx?id=36036
- Microsoft - Windows Defender Credential Guard - https://learn.microsoft.com/windows/security/identity-protection/credential-guard/
- CWE-522 Insufficiently Protected Credentials - https://cwe.mitre.org/data/definitions/522.html
- NIST SP 800-63B Digital Identity Guidelines - https://pages.nist.gov/800-63-3/sp800-63b.html

