# Capacidades do KAWA-AI

## Objetivo operacional

O KAWA-AI evolui por módulos locais e conectores autorizados. Cada módulo entrega um artefato verificável — código, relatório, texto, quadro de vídeo, nota no Obsidian ou registro explícito no Supabase — em vez de prometer capacidades ilimitadas.

| Capacidade | Módulo atual ou priorizado | Saída verificável | Limite operacional |
|---|---|---|---|
| Programação | Ferramentas de arquivo, terminal, testes e auditoria estática | Alterações no projeto e relatório local | Escrita limitada ao diretório de trabalho. |
| Segurança autorizada | Ruff, Bandit e Semgrep locais | `kawa-quality/audit-*.json` | Somente análise estática de projetos autorizados; sem exploração de rede. |
| Leitura e pesquisa | Web, cérebro de conhecimento e Obsidian | Síntese com fontes e diário contínuo | Consulta não altera permissões ou identidade do agente. |
| Design técnico | Briefs, diagramas estruturados e artefatos de projeto | Mermaid, especificação visual ou projeto de interface | Imagens e apresentações dependem do meio escolhido e de autorização. |
| Criação de mídia | FFmpeg, whisper.cpp e provedores opcionais | Quadros, transcrição ou mídia gerada | Geração externa depende de conta e chave própria. |
| Memória de conhecimento | Obsidian + Supabase opcional | Diário e registros `kawa_knowledge` | Gravação no Supabase é explícita e dados sensíveis são redigidos. |

## Execução direta

O modo `proactive` permite que tarefas locais rotineiras avancem sem confirmação repetitiva. Ele não altera o fato de que publicar, preencher formulários, remover arquivos, modificar contas ou expor dados requer uma confirmação pontual e registrável.

## Próximos módulos

1. Gerador de brief de design e diagramas estruturados.
2. Auditoria de dependências e relatório de correções sugeridas.
3. Conector Supabase local com chave no cofre do sistema, após a configuração no computador do proprietário.
4. Adaptadores opcionais para voz, imagem e vídeo somente com contas e permissões autorizadas.

## Referências

[1] [Semgrep](https://github.com/semgrep/semgrep) documenta análise estática de múltiplas linguagens e execução local.

[2] [Bandit](https://github.com/PyCQA/bandit) documenta análise de padrões comuns de segurança em Python por AST.

[3] [Ruff](https://github.com/astral-sh/ruff) documenta lint e formatação rápidos para Python.
