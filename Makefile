.PHONY: setup up down restart logs logs-bot logs-admin shell-bot shell-admin migrate seed ps clean update

# ── Setup ──────────────────────────────────────────────────────────────────

setup:
	@bash setup.sh

# ── Docker ─────────────────────────────────────────────────────────────────

up:
	@$(MAKE) _check_env
	docker compose up --build -d
	@echo ""
	@echo "✅  AntonVPN запущен."
	@echo "    Бот:        активен"
	@echo "    Админ:      http://localhost:8000/admin"
	@echo ""
	@echo "    Логи:       make logs"

up-fg:
	@$(MAKE) _check_env
	docker compose up --build

down:
	docker compose down

restart:
	docker compose restart

restart-bot:
	docker compose restart bot

restart-admin:
	docker compose restart admin

# ── Logs ───────────────────────────────────────────────────────────────────

logs:
	docker compose logs -f --tail=100

logs-bot:
	docker compose logs -f --tail=100 bot

logs-admin:
	docker compose logs -f --tail=100 admin

# ── Database ────────────────────────────────────────────────────────────────

migrate:
	docker compose exec admin alembic upgrade head

seed:
	docker compose exec admin python database/seed.py

# ── Shell access ────────────────────────────────────────────────────────────

shell-bot:
	docker compose exec bot bash

shell-admin:
	docker compose exec admin bash

shell-db:
	docker compose exec postgres psql -U antonvpn_user -d antonvpn

# ── Status ──────────────────────────────────────────────────────────────────

ps:
	docker compose ps

# ── Cleanup ─────────────────────────────────────────────────────────────────

clean:
	docker compose down -v --remove-orphans
	@echo "⚠  Контейнеры и тома удалены. БД очищена."

# ── Update ───────────────────────────────────────────────────────────────────

update:
	git pull --ff-only
	docker compose build --no-cache bot admin
	docker compose up -d bot admin
	@echo "✅  Бот и админка обновлены."

# ── Internal ────────────────────────────────────────────────────────────────

_check_env:
	@if [ ! -f "config/.env" ]; then \
		echo ""; \
		echo "❌  Файл config/.env не найден."; \
		echo "    Запустите: make setup"; \
		echo ""; \
		exit 1; \
	fi
