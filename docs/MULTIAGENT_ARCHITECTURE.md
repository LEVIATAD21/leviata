# Arquitetura Multiagente KAWA-AI (Cognitive Team)

Este documento descreve a arquitetura de múltiplos agentes especialistas colaborativos implementada no **KAWA-AI**.

---

## 🏛️ Visão Geral do Sistema

Quando o usuário envia uma tarefa complexa (ex: *"Crie uma loja online de custo zero com análise de segurança"*), o sistema não executa comandos cegamente. Ele opera através de um **Pipeline Cognitivo em 4 Etapas**:

1. **Orquestrador (Coordenador Principal)**:
   - Analisa o objetivo do usuário.
   - Identifica se faltam informações (ex: *"O que a loja vai vender?"*).
   - Divide a tarefa em um plano estruturado de ponta a ponta.

2. **Equipe de Especialistas (Diálogo Interno / Debates)**:
   - **Arquiteto de Solução (Front/Back)**: Desenvolve a estrutura técnica, escolhe stack leve e sem custo.
   - **Especialista em Segurança (SecOps)**: Analisa vulnerabilidades, protege contra injeção, verifica dependências e aplica hardening.
   - **Estrategista de Operações & Custo Zero**: Define hospedagem gratuita (Vercel, GitHub Pages, Render, etc.) e estratégia de divulgação orgânica.

3. **Plano de Execução Controlada**:
   - Apresenta o plano completo ao usuário para aprovação.
   - Executa comandos no terminal passo a passo, solicitando confirmação para ações críticas.

4. **Validação e Entrega**:
   - Testa o código gerado, verifica erros e entrega o projeto pronto.

---

## 🔌 Integração com NVIDIA NIM / LLMs Customizadas

O KAWA-AI suporta nativamente a API da NVIDIA (NIM) e qualquer endpoint compatível com OpenAI através do provedor `custom` ou `openai` com `base_url`.

Exemplo de configuração em `~/.kawa-ai/config.json` para usar modelos da NVIDIA:

```json
{
  "provider": "openai",
  "base_url": "https://integrate.api.nvidia.com/v1",
  "api_key": "nvapi-...",
  "model": "meta/llama-3.1-70b-instruct"
}
```
