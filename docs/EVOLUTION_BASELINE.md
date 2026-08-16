# KAWA-AI — baseline e matriz de evolução

## Escopo consolidado

Os dois PDFs enviados são cópias do mesmo plano de engenharia e analisam o snapshot `4294524`. Ambos recomendam evoluir por ondas: primeiro estabilizar contratos, política, testes e execução local; depois adicionar runtime servível, eventos, filas, memória estruturada e sandbox; em seguida uma experiência visual e observabilidade; por fim integrações externas e capacidades avançadas apenas em escopo autorizado.

## Requisitos verificáveis selecionados para esta etapa

| Requisito | Decisão desta etapa | Critério de validação |
|---|---|---|
| Entrada natural em um único comando | Manter `kawa` como entrada padrão da TUI | Executar `main.py` sem argumentos entra na interface |
| Interpretação tolerante | Preservar normalização conservadora de abreviações, acentos e erros leves | Testes de normalização e roteamento |
| Execução ponta a ponta | Manter planejamento determinístico, agente e registro local | Teste do workflow e registro JSON |
| Materialização de documentação em skill | Manter pacote local `SKILL.md` com capítulos | Teste de criação dentro do workspace |
| “Sem limitação” | Não prometer limite infinito; reduzir fricção, mas respeitar hardware, provedor, timeouts e política | Documentação explícita e testes de regressão |
| Evolução servível completa | Não ativar API/WebSocket/filas/sandbox nesta alteração sem requisitos de implantação e sem testes próprios | Registrar como próxima onda, não simular conclusão |

## Riscos importantes do plano

O uso de `shell=True`, leitura de arquivos, rede, credenciais e navegador precisa continuar sob política e escopo. Uma execução realmente sem limites seria tecnicamente insegura e também dependeria do provedor, do modelo local, da RAM, da CPU, da rede e de limites de contexto. Por isso, esta etapa valida a experiência e a base local sem remover as barreiras de alto impacto.

## Resultado da referência

- Commit antes da evolução desta etapa: `4294524`.
- `python3 -m unittest discover -s tests -v`: **58 testes aprovados**.
- Compilação sintática de `main.py`, módulos `agent`, `providers`, `tools` e `ui`: **aprovada**.
- `git diff --check`: **aprovado**.

A implementação subsequente deve ser comparada a este baseline e somente consolidada se todos os testes de referência continuarem aprovados.
