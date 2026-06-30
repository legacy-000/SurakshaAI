.PHONY: install run-backend run-frontend docker-up docker-down test lint clean

# --- Installation ---
install: install-backend install-frontend

install-backend:
	pip install -r requirements.txt

install-frontend:
	npm install

# --- Running Services ---
run-backend:
	uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

run-frontend:
	npm run dev

# --- Docker Control ---
docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

# --- Testing & Linting ---
test:
	pytest tests/

lint: lint-backend lint-frontend

lint-backend:
	black --check backend/ ai_engine/
	mypy backend/ ai_engine/
	flake8 backend/ ai_engine/

lint-frontend:
	npm run lint

# --- Database ---
db-migrate:
	alembic upgrade head

db-seed:
	python database/seed/seed_data.py

# --- Cleaning ---
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.py[co]" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf .next/ out/ build/ dist/ *.egg-info
