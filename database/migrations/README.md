# Database Migrations (Alembic)

This folder contains the database schema migration history managed using Alembic.

## Commands

### Initialize Alembic
```bash
alembic init database/migrations
```

### Auto-generate Migration
```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply Migrations
```bash
alembic upgrade head
```

### Rollback Migration
```bash
alembic downgrade -1
```
