# Coding Standards and Style Guide

To maintain uniformity across the frontend, backend, and AI codebase, team members must adhere to these guidelines.

## Case Convention Matrix

### 1. Class Naming
- Case: `PascalCase`
- Apply to: Python classes, TypeScript types/interfaces, React components.
- Examples:
  - `class CrimePredictor`
  - `interface UserProfile`
  - `function DashboardCard()`

### 2. Variables
- Case: `camelCase`
- Apply to: TypeScript/JavaScript variables, database entity JSON fields.
- Examples:
  - `const activeAlerts = []`
  - `let totalCasesCount = 10`

### 3. Constants
- Case: `UPPER_CASE` (with underscores)
- Apply to: Global constant variables, environment configurations.
- Examples:
  - `KARNATAKA_SRID = 4326`
  - `const API_TIMEOUT_MS = 5000`

### 4. Functions
- Case: `camelCase`
- Apply to: TypeScript/JavaScript functions, hooks, state setters.
- Examples:
  - `function formatCaseTimestamp(ts)`
  - `const handleMessageSubmit = () => {}`

### 5. API Design
- Case: `snake_case`
- Apply to: FastAPI routes, JSON request/response parameter keys, Python functions.
- Examples:
  - `/api/analytics/case_hotspots`
  - `def query_associated_cases()`
  - Pydantic payload: `{ "session_id": "..." }`
