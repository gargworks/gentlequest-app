# GentleQuest Makefile
# Common development and deployment commands

.PHONY: help install migrate seed test run deploy rollback clean experiment studio-help

# ═══════════════════════════════════════════════════════════════
# STUDIO OPERATING SYSTEM
# ═══════════════════════════════════════════════════════════════

experiment:
	@if [ -z "$(name)" ]; then \
		echo "Usage: make experiment name=my-idea"; \
		exit 1; \
	fi
	@./scripts/scaffold_experiment.sh $(name)

studio-help:
	@echo "╔════════════════════════════════════════════════════════╗"
	@echo "║         LOKESH STUDIO QUICK COMMANDS                   ║"
	@echo "╠════════════════════════════════════════════════════════╣"
	@echo "║  make experiment name=idea-name  → Create new experiment║"
	@echo "║  make studio-help                → Show this help       ║"
	@echo "║                                                        ║"
	@echo "║  Docs: CONTEXT_HUB.md | STUDIO_MANUAL.md               ║"
	@echo "╚════════════════════════════════════════════════════════╝"

# ═══════════════════════════════════════════════════════════════

help:
	@echo "GentleQuest Development Commands"
	@echo "================================="
	@echo ""
	@echo "📦 STUDIO (Multi-Project):"
	@echo "  make experiment name=X  - Create new experiment"
	@echo "  make studio-help        - Studio quick reference"
	@echo ""
	@echo "🛠️  DEVELOPMENT:"
	@echo "  make install    - Install dependencies"
	@echo "  make migrate    - Run database migrations"
	@echo "  make seed       - Seed initial data"
	@echo "  make test       - Run all tests"
	@echo "  make run        - Run development server"
	@echo ""
	@echo "🚀 DEPLOYMENT:"
	@echo "  make deploy     - Deploy to production"
	@echo "  make rollback   - Rollback last deployment"
	@echo ""
	@echo "🔧 MAINTENANCE:"
	@echo "  make clean      - Clean old data"
	@echo "  make health     - Run health check"
	@echo "  make backup     - Backup database"

install:
	pip install -r requirements.txt
	cd ai_buddy_web && flutter pub get

migrate:
	alembic upgrade head

seed:
	python scripts/seed_quests.py
	python scripts/seed_resources.py
	python scripts/seed_counselors.py

test:
	pytest -v --cov=. --cov-report=term

run:
	python app.py

deploy:
	./scripts/deploy_production.sh

rollback:
	./scripts/rollback_deployment.sh

clean:
	python scripts/cleanup_old_data.py

health:
	python scripts/daily_health_check.py

backup:
	./scripts/backup_database.sh

perf:
	python scripts/performance_analysis.py

security:
	python scripts/security_audit.py

monitor:
	python scripts/monitoring_setup.py

report:
	python scripts/generate_pilot_report.py 1 1

setup: install migrate seed
	@echo "✅ Setup complete"

quickstart: setup run
	@echo "🚀 GentleQuest running at http://localhost:5055"
