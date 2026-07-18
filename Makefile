.PHONY: lint typecheck test test-backend test-frontend check all

# Lint with flake8
lint:
	cd "C:\Users\anivr\Desktop\SurakshaAI" && python -m flake8 functions/suraksha_ai/ tests/ --config .flake8 --count

# Type-check with mypy
typecheck:
	cd "C:\Users\anivr\Desktop\SurakshaAI" && python -m mypy functions/suraksha_ai/ --config-file pyproject.toml

# Backend tests
test:
	cd "C:\Users\anivr\Desktop\SurakshaAI" && python -m pytest --tb=short

# Frontend tests
test-frontend:
	cd "C:\Users\anivr\Desktop\SurakshaAI\suraksha-dashboard" && npx jest --no-coverage

# Full CI suite
all: lint typecheck test test-frontend
	@echo "=== ALL CHECKS PASSED ==="