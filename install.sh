#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# AntonVPN — One-command installer
#
# Usage (after pushing to GitHub):
#   curl -fsSL https://raw.githubusercontent.com/YOUR/REPO/main/install.sh | bash
#
# Or with sudo (required if you want to install Remnawave Panel):
#   curl -fsSL https://raw.githubusercontent.com/YOUR/REPO/main/install.sh | sudo bash
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

REPO_URL="${ANTONVPN_REPO:-}"   # можно передать через env: ANTONVPN_REPO=... | bash
INSTALL_DIR="${ANTONVPN_DIR:-/opt/antonvpn}"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'; BOLD='\033[1m'

ok()   { echo -e "${GREEN}✓ $*${NC}"; }
err()  { echo -e "${RED}✗ $*${NC}"; exit 1; }
info() { echo -e "  $*"; }
step() { echo -e "\n${CYAN}${BOLD}▶ $*${NC}"; }

echo -e "\n${CYAN}${BOLD}╔══════════════════════════════════════╗"
echo -e "║       AntonVPN Installer             ║"
echo -e "╚══════════════════════════════════════╝${NC}\n"

# ── 1. Git ────────────────────────────────────────────────────────────────────

step "Проверка зависимостей"

if ! command -v git &>/dev/null; then
  info "git не найден — устанавливаю..."
  if command -v apt-get &>/dev/null; then
    apt-get update -qq && apt-get install -y -qq git
  elif command -v yum &>/dev/null; then
    yum install -y -q git
  else
    err "Не удалось установить git. Установите вручную: apt install git"
  fi
fi
ok "git: $(git --version)"

if ! command -v docker &>/dev/null; then
  info "Docker не найден — устанавливаю..."
  curl -fsSL https://get.docker.com | sh
  ok "Docker установлен."
fi
ok "docker: $(docker --version | cut -d' ' -f3 | tr -d ',')"

# ── 2. Repo URL ───────────────────────────────────────────────────────────────

step "Получение репозитория"

if [[ -z "$REPO_URL" ]]; then
  echo -ne "  ${BOLD}URL репозитория${NC} (например https://github.com/you/antonvpn): "
  read -r REPO_URL
  [[ -z "$REPO_URL" ]] && err "URL репозитория обязателен."
fi

# ── 3. Clone or update ────────────────────────────────────────────────────────

if [[ -d "$INSTALL_DIR/.git" ]]; then
  info "Директория $INSTALL_DIR уже существует — обновляю..."
  git -C "$INSTALL_DIR" pull --ff-only
  ok "Репозиторий обновлён."
else
  info "Клонирую в $INSTALL_DIR ..."
  git clone "$REPO_URL" "$INSTALL_DIR"
  ok "Репозиторий склонирован."
fi

cd "$INSTALL_DIR"

# ── 4. Run setup ──────────────────────────────────────────────────────────────

step "Запуск мастера настройки"
chmod +x setup.sh
bash setup.sh

# ── 5. Launch ─────────────────────────────────────────────────────────────────

step "Запуск AntonVPN"
make up

echo ""
echo -e "${GREEN}${BOLD}══════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}  🚀  AntonVPN успешно развёрнут!         ${NC}"
echo -e "${GREEN}${BOLD}══════════════════════════════════════════${NC}"
echo ""
echo -e "  Директория:  ${YELLOW}${INSTALL_DIR}${NC}"
echo -e "  Управление:  ${YELLOW}cd ${INSTALL_DIR} && make <команда>${NC}"
echo -e "  Логи:        ${YELLOW}make logs${NC}"
echo ""
