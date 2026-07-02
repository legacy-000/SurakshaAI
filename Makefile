.PHONY: install install-backend install-frontend deploy deploy-backend deploy-frontend run-backend run-frontend test lint lint-backend lint-frontend clean catalyst-init catalyst-logs

# ==============================================================================
# SURAKSHA AI - CATALYST DEPLOYMENT MAKEFILE
# ==============================================================================

# --- Installation ---
install: install-backend install-frontend

install-backend:
	pip install -r backend/requirements.txt

install-frontend:
	cd frontend && npm install

# --- Catalyst Development (Local) ---
run-backend:
	cd backend && uvicorn main:app --host 0.0.0.0 --port 8000 --reload

run-frontend:
	cd frontend && npm run dev

# --- Catalyst Deployment ---
deploy-backend:
	@echo "Deploying backend to Catalyst Serverless..."
	zcrun deploy backend/

deploy-frontend:
	@echo "Deploying frontend to Catalyst Web Client Hosting..."
	cd frontend && zcil deploy webclient

deploy: deploy-backend deploy-frontend
	@echo "Deployed all services to Zoho Catalyst!"

# --- Catalyst Initialization & Management ---
catalyst-init:
	@echo "Initializing Catalyst project..."
	zcil login
	zcrun init

catalyst-logs:
	@echo "Fetching Catalyst function logs..."
	zcrun logs

catalyst-status:
	@echo "Checking Catalyst deployment status..."
	zcrun status

# --- Testing & Linting ---
test:
	pytest tests/

lint: lint-backend lint-frontend

lint-backend:
	black --check backend/ ai_engine/
	mypy backend/ ai_engine/
	flake8 backend/ ai_engine/

lint-frontend:
	cd frontend && npm run lint

# --- Cleaning ---
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.py[co]" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf .next/ out/ build/ dist/ *.egg-info
