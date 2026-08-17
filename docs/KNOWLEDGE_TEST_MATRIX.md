# Matriz Abrangente de Testes de Conhecimento

## Finalidade

Esta matriz organiza a cobertura de conhecimento do KAWA-AI sem tratar volume como sinônimo de qualidade. Cada item de teste deve ter domínio, subdomínio, habilidade, fonte ou base de referência, modalidade, resposta ou critério esperado, resultado, versão e assinatura de deduplicação. Um item só conta para a meta depois de passar pelas verificações de validade estrutural, unicidade e avaliação independente.

> A expressão “todas as áreas” é implementada como uma taxonomia extensível: novos domínios e subdomínios podem ser registrados sem alterar o histórico dos testes já concluídos.

## Estrutura-base

A matriz combina duas classificações de referência. A classificação FORD da OCDE/ONU organiza pesquisa em seis campos amplos e 42 subcampos, enquanto a Library of Congress mantém classes para temas que vão de obras gerais a ciência, tecnologia, direito, artes e recursos de informação. [^ford] [^lcc]

| Código | Domínio | Cobertura inicial de subdomínios |
|---|---|---|
| GEN | Conhecimento geral e interdisciplinar | métodos, história das ideias, cultura geral, relações entre áreas |
| FOR | Sistemas formais e quantitativos | lógica, matemática, estatística, probabilidade, teoria da computação |
| NAT | Ciências naturais | física, química, biologia, astronomia, geociências, ambiente |
| ENG | Engenharia e tecnologia | civil, elétrica, mecânica, materiais, manufatura, energia, robótica |
| CMP | Computação e informação | programação, algoritmos, dados, IA, redes, sistemas, segurança defensiva, UX |
| MED | Medicina e saúde | anatomia, fisiologia, saúde pública, enfermagem, farmacologia, ética clínica |
| AGR | Agricultura, veterinária e alimentos | agronomia, solos, ecologia aplicada, produção animal, alimentos |
| SOC | Ciências sociais | sociologia, antropologia, ciência política, relações internacionais, demografia |
| ECO | Economia, negócios e trabalho | microeconomia, macroeconomia, finanças, contabilidade, gestão, empreendedorismo |
| LAW | Direito, cidadania e políticas públicas | fundamentos jurídicos, direitos, administração pública, políticas e governança |
| HIS | História, patrimônio e arqueologia | história global, regional, historiografia, memória, patrimônio |
| GEO | Geografia, território e urbanismo | geografia física e humana, cartografia, cidades, mobilidade, clima |
| HUM | Filosofia, psicologia, religião e ética | epistemologia, ética, teorias, psicologia, religiões, pensamento crítico |
| LAN | Linguagens, literatura e comunicação | português, línguas estrangeiras, linguística, literatura, escrita e mídia |
| EDU | Educação e aprendizagem | pedagogia, currículo, avaliação, educação inclusiva, didática |
| ART | Artes, design e criação | artes visuais, música, cinema, teatro, design, arquitetura, fotografia |
| COM | Comunicação, jornalismo e informação | jornalismo, publicidade, documentação, biblioteconomia, verificação de fatos |
| SPO | Esporte, lazer e bem-estar | treinamento, regras, recreação, segurança e saúde no esporte |
| PRA | Conhecimentos práticos e profissões | manutenção, culinária, segurança do trabalho, atendimento, operação e ofícios |
| THE | Teorias e campos emergentes | teoria de sistemas, complexidade, sustentabilidade, bioética, tecnologias emergentes |

## Modalidades de teste

| Modalidade | Objetivo | Critério mínimo de aprovação |
|---|---|---|
| Recuperação factual | Confirmar conceitos, definições e relações básicas | Resposta verificável e com fonte associada |
| Aplicação | Resolver situação prática delimitada | Procedimento reproduzível e resultado coerente |
| Raciocínio | Explicar relações, causas, limites e hipóteses | Cadeia lógica verificável e sem salto factual |
| Análise crítica | Comparar evidências, fontes e interpretações | Distingue fato, hipótese, opinião e incerteza |
| Produção técnica | Criar código, texto, cálculo, plano ou artefato | Passa teste automatizado ou rubrica explícita |
| Atualização | Reavaliar conhecimento sensível ao tempo | Fonte datada e revisão programada |

## Regras de qualidade e de escala

1. A geração deve ocorrer em lotes pequenos e versionados; lotes aprovados podem ser ampliados progressivamente.
2. Itens semanticamente equivalentes não podem contar duas vezes, mesmo com redação distinta.
3. A validação deve ser separada da geração. Um avaliador distinto, uma regra determinística ou uma fonte de referência deve confirmar o resultado.
4. Cada domínio precisa ter distribuição entre níveis introdutório, intermediário, avançado e interdisciplinar.
5. Tópicos de alto risco, como saúde, direito, finanças e segurança, devem registrar limites, fonte e contexto em vez de serem tratados como aconselhamento autônomo.
6. A meta de dois milhões por domínio somente é marcada quando houver prova de unicidade, avaliação e rastreabilidade; itens descartados ou duplicados ficam no log, mas não entram no total válido.

## Fontes e protocolo de avaliação

| Nível | Uso permitido | Exemplos de fonte | Regra de aceitação |
|---|---|---|---|
| Primário ou institucional | Fatos oficiais, normas, estatísticas e ciência consolidada | órgãos públicos, universidades, normas e repositórios institucionais | Registrar URL, data de coleta, licença e trecho ou identificador da evidência |
| Educacional aberto | Fundamentos e exercícios em áreas amplas | recursos educacionais abertos, livros com licença aberta e materiais revisados | Confirmar licença e associar capítulo, seção ou versão ao item |
| Dados estruturados abertos | Entidades, relações, terminologia e perguntas factuais | bases estruturadas de licença compatível | Tratar como ponto de partida e validar afirmações sensíveis com fonte adicional |
| Especializado e atualizado | Temas que mudam no tempo | documentação oficial do fornecedor, periódicos e bases setoriais | Registrar data de validade e agendar revisão |

OERs são materiais de ensino, aprendizagem e pesquisa em domínio público ou sob licença aberta que permite acesso, reutilização, adaptação e redistribuição. [^unesco-oer] A OpenStax disponibiliza textos abertos e revisados por pares em áreas como ciência, matemática, ciências sociais, humanidades, computação, enfermagem e negócios. [^openstax] O Wikidata oferece dados estruturados sob CC0, mas seus dumps completos são muito grandes; a ingestão deve usar subconjuntos temáticos ou consultas por lote, nunca baixar a base inteira em máquina limitada. [^wikidata]

| Etapa | Evidência obrigatória | Quando o item é rejeitado |
|---|---|---|
| Geração | Domínio, subdomínio, habilidade, fonte, versão e modalidade | Não há fonte identificável ou a licença é incompatível |
| Normalização | Texto canônico, idioma, nível e assinatura semântica | É duplicata literal ou semanticamente equivalente |
| Avaliação | Gabarito, rubrica ou teste automatizado separado da geração | Resposta não é verificável ou conflita com a fonte |
| Auditoria | Identificador imutável, data, versão do avaliador e log de decisão | Falta trilha de rastreabilidade |
| Atualização | Data de validade para conteúdo volátil | Conteúdo ultrapassa a janela de revisão definida |

[^ford]: [United Nations Statistics Division — Fields of Research and Development classification](https://unstats.un.org/unsd/classifications/Family/Detail/1039)
[^lcc]: [Library of Congress — Classification Outline](https://www.loc.gov/catdir/cpso/lcco/)
[^unesco-oer]: [UNESCO — Open Educational Resources](https://www.unesco.org/en/open-educational-resources)
[^openstax]: [OpenStax — Higher Education](https://openstax.org/higher-education)
[^wikidata]: [Wikidata — Database download](https://www.wikidata.org/wiki/Wikidata:Database_download)
