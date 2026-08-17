# Ciclo local de site seguro

Para qualquer pedido de criação de site, o KAWA-AI agora planeja a etapa `secure_site_cycle`. Ela cria um site de referência apenas dentro do workspace, executa verificações estáticas, registra evidências JSON e bloqueia a conclusão quando encontra padrões inseguros.

O ciclo verifica arquivos obrigatórios, execução dinâmica (`eval`/`exec`), injeção por `innerHTML`, `shell=True`, ligação pública (`0.0.0.0` ou `::`), segredos embutidos e cabeçalhos de segurança no servidor local. Ele também simula defensivamente classes de abuso de entrada/template, exposição de sessão, transporte/origem e exposição de serviço, detectando armazenamento sensível no navegador, recursos HTTP, CORS permissivo e fluxos sensíveis que exigem contrato de limitação no backend real. O servidor de referência usa apenas `127.0.0.1` e porta efêmera.

O processo não publica o projeto, não abre portas públicas, não realiza varredura de rede e não garante invulnerabilidade absoluta. Para sites reais, autenticação, dependências, infraestrutura, dados e configurações de produção exigem revisão adicional antes de qualquer publicação.
