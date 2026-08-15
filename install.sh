#!/usr/bin/env bash
# ╔═══════════════════════════════════════════════════════════════╗
# ║         KAWA-AI - Script de Instalação para Linux            ║
# ║   Uso: curl -fsSL https://raw.githubusercontent.com/         ║
# ║        LEVIATAD21/manus-clone-ai/master/install.sh | bash    ║
# ╚═══════════════════════════════════════════════════════════════╝

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

INSTALL_DIR="$HOME/.kawa-ai"
REPO_URL="https://github.com/LEVIATAD21/manus-clone-ai.git"
REPO_BRANCH="master"

echo -e "${CYAN}${BOLD}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                  KAWA-AI  Instalador                         ║"
echo "║          Agente de IA Autônomo para Terminal Linux            ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Verifica dependências
echo -e "${YELLOW}[1/5] Verificando dependências...${NC}"

check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo -e "${RED}✗ $1 não encontrado. Instalando...${NC}"
        sudo apt-get install -y "$2" 2>/dev/null || true
    else
        echo -e "${GREEN}✓ $1 encontrado${NC}"
    fi
}

check_command "python3" "python3"
check_command "git" "git"

# Clona ou atualiza o repositório
echo -e "\n${YELLOW}[2/5] Baixando KAWA-AI...${NC}"
if [ -d "$INSTALL_DIR/repo" ]; then
    echo "Atualizando repositório existente..."
    cd "$INSTALL_DIR/repo" && git pull --ff-only origin "$REPO_BRANCH"
else
    mkdir -p "$INSTALL_DIR"
    git clone --branch "$REPO_BRANCH" "$REPO_URL" "$INSTALL_DIR/repo"
fi

# Cria ambiente Python isolado e instala dependências do repositório
echo -e "\n${YELLOW}[3/5] Criando ambiente Python isolado...${NC}"
VENV_DIR="$INSTALL_DIR/venv"
if ! python3 -m venv "$VENV_DIR"; then
    echo -e "${RED}Não foi possível criar o ambiente virtual.${NC}"
    echo "Instale o suporte a venv e execute novamente: sudo apt-get install -y python3-venv"
    exit 1
fi
"$VENV_DIR/bin/python" -m pip install --upgrade pip -q
"$VENV_DIR/bin/python" -m pip install -r "$INSTALL_DIR/repo/requirements.txt" -q
echo -e "${GREEN}✓ Ambiente e dependências instalados${NC}"

# Cria o comando global 'kawa'
echo -e "\n${YELLOW}[4/5] Criando comando 'kawa' no sistema...${NC}"
LAUNCHER="$HOME/.local/bin/kawa"
mkdir -p "$HOME/.local/bin"

cat > "$LAUNCHER" << 'EOF'
#!/usr/bin/env bash
exec "$HOME/.kawa-ai/venv/bin/python" "$HOME/.kawa-ai/repo/main.py" "$@"
EOF

chmod +x "$LAUNCHER"

# Adiciona ao PATH se necessário
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    SHELL_RC="$HOME/.bashrc"
    [ -f "$HOME/.zshrc" ] && SHELL_RC="$HOME/.zshrc"
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_RC"
    export PATH="$HOME/.local/bin:$PATH"
    echo -e "${GREEN}✓ PATH atualizado em $SHELL_RC${NC}"
fi

echo -e "${GREEN}✓ Comando 'kawa' criado${NC}"

# Finalização
echo -e "\n${YELLOW}[5/5] Instalação concluída!${NC}"
echo -e "\n${GREEN}${BOLD}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}${BOLD}║  KAWA-AI instalado com sucesso!                               ║${NC}"
echo -e "${GREEN}${BOLD}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo -e "\n${CYAN}Como usar:${NC}"
echo -e "  ${BOLD}kawa${NC}                         # Inicia o chat interativo"
echo -e "  ${BOLD}kawa \"sua tarefa aqui\"${NC}       # Executa uma tarefa direta"
echo -e "  ${BOLD}kawa --provider ollama${NC}       # Usa modelos locais (grátis)"
echo -e "\n${YELLOW}Na primeira execução, o cofre Obsidian será localizado e você poderá configurar o provedor.${NC}"
echo -e "${YELLOW}Para automação de navegador, o KAWA-AI tenta reutilizar Chromium/Chrome já instalado.${NC}"
echo -e "${YELLOW}Reinicie o terminal ou execute: source ~/.bashrc${NC}\n"
