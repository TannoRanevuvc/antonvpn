#!/usr/bin/env bash
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
BOLD='\033[1m'

REMNAWAVE_DIR="/opt/remnawave"

# ── Helpers ──────────────────────────────────────────────────────────────────

print_header() {
  echo -e "\n${CYAN}${BOLD}╔══════════════════════════════════════╗"
  echo -e "║         AntonVPN Setup Wizard        ║"
  echo -e "╚══════════════════════════════════════╝${NC}\n"
}

step() { echo -e "\n${CYAN}▶ $*${NC}"; }
ok()   { echo -e "${GREEN}✓ $*${NC}"; }
warn() { echo -e "${YELLOW}⚠  $*${NC}"; }
err()  { echo -e "${RED}✗ $*${NC}"; }
info() { echo -e "  $*"; }

ask() {
  local prompt="$1" default="${2:-}" var_name="$3" secret="${4:-no}"
  local value=""
  while [[ -z "$value" ]]; do
    if [[ -n "$default" ]]; then
      echo -ne "  ${BOLD}${prompt}${NC} [${YELLOW}${default}${NC}]: "
    else
      echo -ne "  ${BOLD}${prompt}${NC}: "
    fi
    if [[ "$secret" == "yes" ]]; then
      read -rs value; echo
    else
      read -r value
    fi
    value="${value:-$default}"
    [[ -z "$value" ]] && err "Это поле обязательно."
  done
  eval "$var_name='$value'"
}

ask_optional() {
  local prompt="$1" default="${2:-}" var_name="$3"
  echo -ne "  ${BOLD}${prompt}${NC}"
  [[ -n "$default" ]] && echo -ne " [${YELLOW}${default}${NC}]"
  echo -ne ": "
  read -r value
  eval "$var_name='${value:-$default}'"
}

ask_yn() {
  local prompt="$1" default="${2:-n}" var_name="$3"
  local hint="y/N"; [[ "${default,,}" == "y" ]] && hint="Y/n"
  echo -ne "  ${BOLD}${prompt}${NC} [${hint}]: "
  read -r yn
  yn="${yn:-$default}"
  [[ "${yn,,}" == "y" || "${yn,,}" == "yes" ]] \
    && eval "$var_name=true" || eval "$var_name=false"
}

generate_secret() {
  openssl rand -hex 32 2>/dev/null \
    || python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null \
    || head -c 32 /dev/urandom | xxd -p
}

generate_password() {
  openssl rand -base64 18 2>/dev/null | tr -d '/+=' \
    || python3 -c "import secrets,string; print(''.join(secrets.choice(string.ascii_letters+string.digits) for _ in range(20)))" 2>/dev/null \
    || echo "Vpn$(date +%s)Pw"
}

require_root() {
  if [[ $EUID -ne 0 ]]; then
    err "Для установки Remnawave Panel нужны права root (sudo)."
    info "Запустите: sudo ./setup.sh"
    exit 1
  fi
}

# ── Remnawave Panel installer ─────────────────────────────────────────────────

install_remnawave_panel() {
  step "Установка Remnawave Panel"

  # 1. Docker
  if ! command -v docker &>/dev/null; then
    info "Docker не найден — устанавливаю..."
    curl -fsSL https://get.docker.com | sh
    ok "Docker установлен."
  else
    ok "Docker уже установлен: $(docker --version | cut -d' ' -f3 | tr -d ',')"
  fi

  # 2. Создаём директорию
  mkdir -p "$REMNAWAVE_DIR"
  cd "$REMNAWAVE_DIR"
  info "Рабочая директория: $REMNAWAVE_DIR"

  # 3. Скачиваем docker-compose.yml и .env
  if [[ -f "$REMNAWAVE_DIR/docker-compose.yml" ]]; then
    warn "Файлы Remnawave уже существуют в $REMNAWAVE_DIR."
    ask_yn "Перескачать (overwrite)?" "n" RW_OVERWRITE
    if [[ "$RW_OVERWRITE" == "true" ]]; then
      curl -fsSL -o docker-compose.yml \
        https://raw.githubusercontent.com/remnawave/backend/refs/heads/main/docker-compose-prod.yml
      curl -fsSL -o .env \
        https://raw.githubusercontent.com/remnawave/backend/refs/heads/main/.env.sample
      ok "Файлы обновлены."
    fi
  else
    info "Скачиваю docker-compose.yml и .env..."
    curl -fsSL -o docker-compose.yml \
      https://raw.githubusercontent.com/remnawave/backend/refs/heads/main/docker-compose-prod.yml
    curl -fsSL -o .env \
      https://raw.githubusercontent.com/remnawave/backend/refs/heads/main/.env.sample
    ok "Файлы загружены."
  fi

  # 4. Генерируем ключи безопасности
  info "Генерирую ключи безопасности..."
  sed -i "s/^APP_SECRET=.*/APP_SECRET=$(openssl rand -hex 64)/" .env
  sed -i "s/^METRICS_PASS=.*/METRICS_PASS=$(openssl rand -hex 64)/" .env
  sed -i "s/^WEBHOOK_SECRET_HEADER=.*/WEBHOOK_SECRET_HEADER=$(openssl rand -hex 64)/" .env
  ok "Ключи сгенерированы."

  # 5. Генерируем пароль PostgreSQL
  local rw_pg_pass
  rw_pg_pass=$(openssl rand -hex 24)
  sed -i "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$rw_pg_pass/" .env
  sed -i "s|^\(DATABASE_URL=\"postgresql://postgres:\)[^\@]*\(@.*\)|\1$rw_pg_pass\2|" .env
  ok "Пароль PostgreSQL сгенерирован."

  # 6. Домен панели
  echo ""
  info "${YELLOW}Укажите домены для панели Remnawave.${NC}"
  info "Домен должен быть уже направлен на IP этого сервера."
  ask "Домен панели (FRONT_END_DOMAIN)" "" RW_PANEL_DOMAIN
  ask_optional "Домен подписки (SUB_PUBLIC_DOMAIN)" "${RW_PANEL_DOMAIN}/api/sub" RW_SUB_DOMAIN

  sed -i "s|^FRONT_END_DOMAIN=.*|FRONT_END_DOMAIN=${RW_PANEL_DOMAIN}|" .env
  sed -i "s|^SUB_PUBLIC_DOMAIN=.*|SUB_PUBLIC_DOMAIN=${RW_SUB_DOMAIN}|" .env
  ok "Домены настроены."

  # 7. Запускаем
  info "Запускаю контейнеры Remnawave..."
  docker compose up -d
  ok "Remnawave Panel запущена!"

  # 8. Выводим данные для бота
  echo ""
  echo -e "  ${CYAN}${BOLD}━━━ Данные для AntonVPN бота ━━━${NC}"
  echo -e "  REMNAWAVE_PANEL_URL=${YELLOW}https://${RW_PANEL_DOMAIN}${NC}"
  echo -e "  ${YELLOW}Bearer token получите в интерфейсе панели:${NC}"
  echo -e "  https://${RW_PANEL_DOMAIN} → Settings → API Tokens"
  echo ""

  # Сохраняем URL панели для следующего шага
  DETECTED_REMNAWAVE_URL="https://${RW_PANEL_DOMAIN}"

  cd - > /dev/null
}

# ── Main ─────────────────────────────────────────────────────────────────────

print_header

ENV_FILE="config/.env"
DETECTED_REMNAWAVE_URL=""

# ── Шаг 0: установка Remnawave Panel ─────────────────────────────────────────

step "Remnawave Panel"
ask_yn "Установить Remnawave Panel на этот сервер?" "y" INSTALL_PANEL

if [[ "$INSTALL_PANEL" == "true" ]]; then
  require_root
  install_remnawave_panel

  echo ""
  warn "Откройте https://${RW_PANEL_DOMAIN} в браузере, создайте API-токен"
  warn "и введите его ниже."
  echo ""
fi

# ── Шаг 1: проверка существующего .env ───────────────────────────────────────

mkdir -p config

if [[ -f "$ENV_FILE" ]]; then
  warn "Файл $ENV_FILE уже существует."
  ask_yn "Перезаписать?" "n" OVERWRITE
  if [[ "$OVERWRITE" != "true" ]]; then
    ok "Установка пропущена. Запустите: make up"
    exit 0
  fi
fi

# ── Шаг 2: Telegram Bot ───────────────────────────────────────────────────────

step "Telegram Bot"
ask "Токен бота (от @BotFather)" "" BOT_TOKEN
ask "Username бота (например @MyVPNBot)" "" BOT_USERNAME
BOT_LINK="https://t.me/${BOT_USERNAME#@}"

# ── Шаг 3: Remnawave ─────────────────────────────────────────────────────────

step "Remnawave VPN Panel — подключение"
ask "URL панели" "${DETECTED_REMNAWAVE_URL}" REMNAWAVE_URL
ask "Bearer token (API токен из панели)" "" REMNAWAVE_TOKEN secret

# ── Шаг 4: Robokassa ─────────────────────────────────────────────────────────

step "Robokassa (платёжный провайдер)"
info "${YELLOW}Оставьте пустым, если хотите настроить позже.${NC}"
ask_optional "Merchant Login (SHOP_IND)" "" SHOP_IND
ask_optional "Пароль #1 (PASS1)" "" PASS1
ask_optional "Пароль #2 (PASS2)" "" PASS2
ask_yn "Тестовый режим Robokassa?" "y" ROBOKASSA_TEST

# ── Шаг 5: Админ-панель ──────────────────────────────────────────────────────

step "Админ-панель AntonVPN"
ask "Логин администратора" "admin" ADMIN_USER
DEFAULT_PASS=$(generate_password)
ask "Пароль администратора" "$DEFAULT_PASS" ADMIN_PASSWORD secret

# ── Шаг 6: Дополнительно ─────────────────────────────────────────────────────

step "Дополнительно"
ask_optional "ID Telegram-канала для обязательной подписки (0 = выкл)" "0" CHANNEL_ID
ask_optional "Публичный URL для AdminPanel" "http://localhost:8000" PUBLIC_URL
info "${YELLOW}Если сервер в России — укажите SOCKS5-прокси для доступа к Telegram.${NC}"
ask_optional "SOCKS5 прокси (например socks5://user:pass@host:port, пусто = нет)" "" PROXY_URL

# ── Генерируем секреты ────────────────────────────────────────────────────────

DB_PASS=$(generate_password)
JWT_SECRET=$(generate_secret)

step "Генерация конфигурации..."

cat > "$ENV_FILE" << EOF
# ──────────────────────────────────────────
# AntonVPN Configuration
# Создан: $(date '+%Y-%m-%d %H:%M')
# ──────────────────────────────────────────

# Database
DATABASE_URL=postgresql+asyncpg://antonvpn_user:${DB_PASS}@postgres:5432/antonvpn
REDIS_URL=redis://redis:6379/0
POSTGRES_PASSWORD=${DB_PASS}

# Telegram bot
TOKEN_BOT_TG=${BOT_TOKEN}
BOT_LINK=${BOT_LINK}

# Remnawave VPN panel
REMNAWAVE_PANEL_URL=${REMNAWAVE_URL}
REMNAWAVE_TOKEN=${REMNAWAVE_TOKEN}

# Robokassa
SHOP_IND=${SHOP_IND}
PASS1=${PASS1}
PASS2=${PASS2}
ROBOKASSA_IS_TEST=${ROBOKASSA_TEST}

# Admin panel
ADMIN_USER=${ADMIN_USER}
ADMIN_PASSWORD=${ADMIN_PASSWORD}
BASE_ADMIN_URL=/admin
ADMIN_PUBLIC_BASE_URL=${PUBLIC_URL}
JWT_SECRET_KEY=${JWT_SECRET}
JWT_ALGORITHM=HS256

# Channel gate (0 = disabled)
CHANNEL_ID=${CHANNEL_ID}

# Proxy for Telegram API (leave empty if not needed)
SOCKS5_PROXY_URL=${PROXY_URL}
EOF

ok "Файл ${ENV_FILE} создан."

# ── Docker network ────────────────────────────────────────────────────────────

step "Настройка Docker сети"
if ! docker network inspect remnawave-network &>/dev/null; then
  docker network create remnawave-network
  ok "Сеть remnawave-network создана."
else
  ok "Сеть remnawave-network уже существует."
fi

# ── Итог ─────────────────────────────────────────────────────────────────────

echo ""
echo -e "${GREEN}${BOLD}══════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}  ✅  Настройка завершена!                ${NC}"
echo -e "${GREEN}${BOLD}══════════════════════════════════════════${NC}"
echo ""
echo -e "  Запустите бота:"
echo -e "  ${CYAN}${BOLD}  make up${NC}"
echo ""
if [[ -n "$DETECTED_REMNAWAVE_URL" ]]; then
  echo -e "  Remnawave Panel:  ${YELLOW}${DETECTED_REMNAWAVE_URL}${NC}"
fi
echo -e "  AntonVPN Admin:   ${YELLOW}${PUBLIC_URL}/admin${NC}"
echo -e "  Логин:            ${YELLOW}${ADMIN_USER}${NC}"
echo -e "  Пароль:           ${YELLOW}${ADMIN_PASSWORD}${NC}"
echo ""
