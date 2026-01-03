SHELL := /bin/bash

# --------- configurable ----------
CHAIN_NAME ?= tbthree
CHAIN_DIR ?= ./chain/$(CHAIN_NAME)
CHAIN_HOME ?= $(CHAIN_DIR)/.$(CHAIN_NAME)
CHAIN_ID ?= $(CHAIN_NAME)
CHAIN_RPC ?= tcp://127.0.0.1:26657
CHAIN_API ?= http://127.0.0.1:1317

BACKEND_DIR ?= ./backend
FRONTEND_DIR ?= ./frontend

PIDS_DIR ?= ./.pids

export CHAIN_DIR CHAIN_HOME CHAIN_ID CHAIN_RPC CHAIN_API

# --------- default ----------
.PHONY: help
help:
	@echo "Targets:"
	@echo "  make up        - bootstrap(if needed) + start chain/backend/frontend (background)"
	@echo "  make down      - stop chain/backend/frontend"
	@echo "  make init      - init demo accounts + fund + register edges"
	@echo "  make seed      - seed demo data via backend (real tx)"
	@echo "  make demo      - init + seed + auto approve pending proposal (optional)"
	@echo "  make reset     - down + remove chain home + remove backend db"
	@echo "  make logs      - tail logs"

.PHONY: bootstrap
bootstrap:
	@mkdir -p $(PIDS_DIR)
	@./scripts/bootstrap_chain.sh

.PHONY: up
up: bootstrap
	@mkdir -p $(PIDS_DIR)
	@./scripts/run_chain.sh
	@./scripts/run_backend.sh
	@./scripts/run_frontend.sh
	@echo "\n✅ All services started."
	@echo "- Backend: http://localhost:8000/docs"
	@echo "- Frontend: http://localhost:8080"

.PHONY: down
down:
	@./scripts/stop_all.sh || true

.PHONY: init
init:
	@./scripts/init_demo_accounts.sh
	@./scripts/register_edges.sh

.PHONY: seed
seed:
	@echo "Seeding demo data via backend..."
	@curl -s -X POST "http://127.0.0.1:8000/demo/seed" -H 'Content-Type: application/json' -d '{"seed": 42, "tasks_per_region": 15, "days_span": 7, "bad_edge_mode": true}' | python -m json.tool || true

.PHONY: demo
demo:
	@$(MAKE) up
	@$(MAKE) init
	@$(MAKE) seed
	@echo "\nNow open Frontend dashboard and approve proposals in Governance Center if needed."

.PHONY: reset
reset:
	@$(MAKE) down || true
	@echo "Cleaning chain home and backend db..."
	@rm -rf $(CHAIN_HOME) || true
	@rm -rf $(BACKEND_DIR)/data/tbthree.db || true
	@echo "✅ Reset done."

.PHONY: logs
logs:
	@echo "--- chain ---"; tail -n 50 $(PIDS_DIR)/chain.log 2>/dev/null || true
	@echo "--- backend ---"; tail -n 50 $(PIDS_DIR)/backend.log 2>/dev/null || true
	@echo "--- frontend ---"; tail -n 50 $(PIDS_DIR)/frontend.log 2>/dev/null || true
