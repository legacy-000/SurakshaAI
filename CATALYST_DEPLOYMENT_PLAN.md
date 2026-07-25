# Suraksha AI — Catalyst Deployment Plan

> **Status**: Deployed — phases 0–5, 7, 8, 9 complete; phase 6 deferred  
> **Target**: Zoho Catalyst (Advanced I/O Function + Datastore + GLM 4.7 + QuickML Prophet)  
> **Catalyst CLI**: 1.26.2 · **Python SDK**: zcatalyst_sdk 1.4.0  
> **Created**: 2026-07-24 · **As-built notes added**: 2026-07-25  

---

## As-Built Corrections

Everything below this section is the original plan. Several parts of it describe
APIs and behaviour that turned out not to exist. The phases still read as
written; this section records what was actually true, so the next person does
not re-derive it.

### Phase 3 — the function contract

| Plan says | Reality |
|---|---|
| `handler(request, response)` with CatalystRequest/Response | Python Advanced I/O is **Flask**: `handler(request) -> flask.Response` |
| `execution.main: "index.handler"` | For Python this is a **filename**: `index.py` |
| `deployment.stack: "python"` | Must be a versioned stack, e.g. `python3_13` |
| `catalyst deploy` handles dependencies | The **console upload runs no pip**. Deps must be vendored into the zip as linux/cp313 wheels |

A wrong `execution.main` surfaces as `'NoneType' object has no attribute
'loader'` — `find_spec()` returning `None`, nothing to do with the app code.

`catalyst deploy` was not usable here: the CLI rejects `python3_13` as an
unknown stack (the list is server-side, so a local Python 3.13 install does not
help). Everything ships via console upload instead.

**Function env variables have no console UI**, and the console upload ignores
`deployment.env_variables`. Credentials therefore ride inside the bundle as a
`.env` that `index.py` loads into `os.environ` before `app.config` is imported.
The zip is gitignored and must be treated as a secret. Revisit if CLI deploy
ever becomes viable.

**zcatalyst_sdk needs the request handed to it.** It keeps Catalyst headers in a
thread-local, but FastAPI dispatches sync endpoints to a threadpool worker where
that is empty — every SDK call then fails with "Catalyst headers are empty".
`app/catalyst_ctx.py` carries the headers across; all SDK use goes through it.

### Phase 4 — the LLM is under QuickML, not Zia

`zia.get_glm()` does not exist in any SDK version. Zia offers vision and
text-analytics only. Catalyst serves chat models through **QuickML LLM
serving**, reached by REST:

```
POST https://api.catalyst.zoho.in/quickml/v1/project/<id>/glm/chat
Headers: Authorization: Bearer <token>, CATALYST-ORG: <env id>
Body:    {"model": "crm-di-glm47b_30b_it", "messages": [...], "stream": false,
          "chat_template_kwargs": {"enable_thinking": false}}
```

- The model id is the **serving name**, not `glm-4.7`.
- `CATALYST-ORG` is required; without it the gateway answers `PATTERN_NOT_MATCHED`.
- An OAuth refresh token scoped only for Datastore gets `401 INVALID_OAUTHSCOPE`.
  Inside a function the SDK authenticates as the project and clears this, so no
  token regeneration is needed.
- `enable_thinking` must be **false** or the model streams its reasoning into
  the response body, which makes generated JSON unparseable.

**ZCQL silently returns zero rows** for `GROUP BY`, an aggregate mixed with
plain columns, or `ORDER BY` over an aggregate — it does not error. Narrated,
that reads as "no data", a confidently wrong answer. `nlq._degroup()` rewrites
those to plain row fetches and aggregates in Python, with a widened retry as a
catch-all. A bare `COUNT(...)` is supported and returns one row holding the
total — not one row per match.

### Phase 6 — not trainable at this data volume

The plan's "group by crime_type, district" yields 167 series with a **median of
one monthly point each**; no series reaches six. Prophet would emit confident
numbers backed by nothing. `district` or `crime` grain (~11–16 points) is the
practical ceiling until the archive grows. `app/export_training_data.py` takes a
grain argument and warns when one is too sparse.

QuickML has no `app.quickml()` and no `.model()`. The accessor is `quick_ml()`
and the only call is `predict(endpoint_key, input_data)` against a **published
endpoint**, so the setting is `QUICKML_ENDPOINT_KEY`, not a model id.

### Phase 7 — done, but File Store is deprecating

Uploads go through `app/services/file_store.py` (evidence, witness docs, both
chat paths). Folders carry PII/ePHI. Note the SDK validates for a
`BufferedReader` — a `BytesIO` is rejected.

Function instances have **ephemeral disks**, so the local-disk fallback loses
evidence on recycle. It is a development convenience only.

Catalyst is deprecating File Store in favour of **Stratus** within ~2 years. The
wrapper is three functions, so the swap is contained.

### Datastore writes — the row API takes a list

`POST /table/<t>/row` requires a **list** of rows and answers `INVALID_INPUT` to
a bare object. Until this was fixed every insert failed — including the audit
trail, which swallowed the error and recorded nothing while appearing healthy.

Datastore also rejects ISO-8601 with a `T`, microseconds or an offset;
`CatalystStore._coerce()` normalises datetimes centrally, since one bad field
rejects the whole row.

### Territory access control

Not in the original plan, and it was broken: an SP saw all 261 cases, and case
detail was reachable by id from any district. `Ctx.can_access_district()` and
`Ctx.scope_rows()` are now applied across cases, victims, socio, financial and
the NLQ path. Out-of-territory reads return **404, not 403** — a 403 confirms
the record exists. Scoping fails closed.

### Scripts

`newcrime/backend/scripts/` — `build_function.py` (rebuild the bundle),
`test_function.py`, `test_territory.py`, `test_filestore.py`. Run from
`newcrime/backend`.

---

## Table of Contents

0. [As-Built Corrections](#as-built-corrections)
1. [Current Architecture](#1-current-architecture)
2. [Target Architecture](#2-target-architecture)
3. [Limitations & Manual Steps](#3-limitations--manual-steps)
4. [Phase 0 — Catalyst Project Init](#phase-0--catalyst-project-init)
5. [Phase 1 — Datastore Tables](#phase-1--datastore-tables)
6. [Phase 2 — Data Access Layer](#phase-2--data-access-layer)
7. [Phase 3 — FastAPI → Catalyst Function Adapter](#phase-3--fastapi--catalyst-function-adapter)
8. [Phase 4 — GLM 4.7 Integration (NLQ v2)](#phase-4--glm-47-integration-nlq-v2)
9. [Phase 5 — Router Migration (SQLAlchemy → ZCQL)](#phase-5--router-migration-sqlalchemy--zcql)
10. [Phase 6 — QuickML Prophet Forecasting](#phase-6--quickml-prophet-forecasting)
11. [Phase 7 — File Storage Migration](#phase-7--file-storage-migration)
12. [Phase 8 — Seed Data Migration](#phase-8--seed-data-migration)
13. [Phase 9 — Deployment & Validation](#phase-9--deployment--validation)
14. [File Change Summary](#file-change-summary)
15. [Risk Register](#risk-register)
16. [Appendix A — Full Table Schema](#appendix-a--full-table-schema)
17. [Appendix B — ZCQL Limitations & Workarounds](#appendix-b--zcql-limitations--workarounds)
18. [Appendix C — GLM Prompt Design](#appendix-c--glm-prompt-design)

---

## 1. Current Architecture

```
┌──────────────┐       HTTP        ┌─────────────────────────────┐
│  React 18    │ ──────────────▸   │  FastAPI (port 8077)        │
│  Vite (5173) │                   │  ├─ 14 routers (90+ endpts) │
│  api.ts      │                   │  ├─ SQLAlchemy ORM          │
└──────────────┘                   │  ├─ MockLLM (rule-based NLQ)│
                                   │  ├─ SQLite (crimeintel.db)  │
                                   │  ├─ Local file storage      │
                                   │  └─ RBAC / Audit middleware │
                                   └─────────────────────────────┘
```

| Component | Technology | Status |
|-----------|-----------|--------|
| Frontend | React 18 + Vite + TypeScript | No changes needed |
| Backend | FastAPI + 14 routers | Migrating to Catalyst Function |
| Database | SQLite via SQLAlchemy | → Catalyst Datastore |
| LLM | MockLLM (keyword matching) | → GLM 4.7 |
| Forecasting | Static seed data | → QuickML Prophet |
| File storage | Local disk | → Catalyst File Store |
| Auth | Demo auth (X-User-* headers) | Keep as-is |

### Current File Tree (Backend)

```
newcrime/backend/app/
├── main.py              # FastAPI app, CORS, audit middleware
├── config.py            # Settings (env-based)
├── database.py          # SQLAlchemy engine + SessionLocal
├── models.py            # 24 SQLAlchemy model classes
├── deps.py              # RBAC ROLE_MATRIX + Ctx class
├── schemas.py           # Pydantic models
├── geo.py               # Karnataka geographic data
├── seed.py              # 260 cases, 180 accused, etc.
├── llm/
│   ├── __init__.py
│   └── client.py        # MockLLM / CatalystClient stub / OpenAIClient
├── services/
│   ├── nlq.py           # Rule-based NLQ engine
│   └── fileparse.py     # Document text extraction
└── routers/
    ├── auth.py           # /api/auth/*
    ├── chat.py           # /api/chat/*
    ├── cases.py          # /api/cases/*
    ├── analytics.py      # /api/analytics/*
    ├── network.py        # /api/network/*
    ├── profiling.py      # /api/profiling/*
    ├── socio.py          # /api/socio/*
    ├── forecasting.py    # /api/forecasting/*
    ├── financial.py      # /api/financial/*
    ├── alerts.py         # /api/alerts/*
    ├── dashboards.py     # /api/workspace/* + /api/command/*
    ├── investigation.py  # /api/investigation/*
    ├── victims.py        # /api/victims/*
    └── audit.py          # /api/audit/*
```

### Current Database (24 Tables, 260 Cases Seeded)

| Table | Rows (seeded) | Key Relations |
|-------|--------------|---------------|
| users | 17 | — |
| officers | 40 | — |
| accused | 180 | → behavior_profiles (1:1) |
| victims | 200 | — |
| cases | 260 | → case_accused, case_victim (M:N) |
| case_accused | ~520 | FK → cases, accused |
| case_victim | ~260 | FK → cases, victims |
| associations | ~500 | self-ref accused × accused |
| investigations | 260 | FK → cases, officers (1:1) |
| timeline_events | ~1000 | FK → cases |
| financial_accounts | ~110 | FK → accused (nullable) |
| transactions | variable | FK → accounts, cases |
| crime_patterns | 6 | — |
| predictions | 12 | — |
| behavior_profiles | 180 | FK → accused |
| alerts | 6 | — |
| conversations | variable | FK → users, cases |
| messages | variable | FK → conversations |
| case_notes | variable | FK → cases |
| evidence_documents | variable | FK → cases |
| witnesses | variable | FK → cases |
| audit_logs | variable | — |
| stage_approvals | variable | FK → cases |
| access_requests | variable | FK → cases |

---

## 2. Target Architecture

```
┌──────────────┐       HTTPS       ┌────────────────────────────────────────┐
│  React 18    │ ──────────────▸   │  Catalyst Advanced I/O Function       │
│  (deployed   │                   │  ┌──────────────────────────────────┐  │
│   or local)  │                   │  │ FastAPI (ASGI) via adapter       │  │
└──────────────┘                   │  │  ├─ RBAC / Audit (unchanged)    │  │
                                   │  │  ├─ 14 routers (modified)       │  │
                                   │  │  └─ catalyst_store.py (new DAL) │  │
                                   │  └──────────┬──────┬──────┬────────┘  │
                                   │             │      │      │           │
                                   │    ┌────────▼──┐ ┌─▼────┐ ┌▼────────┐ │
                                   │    │ Datastore │ │GLM   │ │QuickML  │ │
                                   │    │ (24 tbls) │ │4.7   │ │Prophet  │ │
                                   │    └───────────┘ └──────┘ └─────────┘ │
                                   │    ┌───────────┐                      │
                                   │    │File Store │ (evidence uploads)   │
                                   │    └───────────┘                      │
                                   └────────────────────────────────────────┘
```

### What Changes vs. What Stays

| Changes | Stays |
|---------|-------|
| SQLite → Catalyst Datastore (ZCQL) | React frontend (zero changes) |
| MockLLM → GLM 4.7 | API contract (same JSON shapes) |
| Static predictions → Prophet/QuickML | RBAC (15 roles, ROLE_MATRIX) |
| Local files → Catalyst File Store | Audit middleware |
| Local server → Catalyst Function | TBAC (territory-based access) |
| SQLAlchemy ORM → zcatalyst_sdk | i18n (English/Kannada) |
| database.py → catalyst_store.py | deps.py, geo.py, schemas.py |

---

## 3. Limitations & Manual Steps

### Things Claude Cannot Do (You Must Do Manually)

| # | Action | Why | When |
|---|--------|-----|------|
| L1 | `catalyst init` — create Catalyst project | Requires interactive Zoho OAuth browser login | Phase 0 |
| L2 | Create 24 Datastore tables in Catalyst Console | Console-only UI or CLI with interactive prompts | Phase 1 |
| L3 | Enable GLM 4.7 in project settings | Console-only setting | Phase 0 |
| L4 | Upload training data CSV to QuickML | Console-only upload | Phase 6 |
| L5 | Train Prophet model in QuickML | Console-only training pipeline | Phase 6 |
| L6 | Run `catalyst deploy` | CLI command with auth | Phase 9 |
| L7 | Run `pip install` / `npm install` commands | Terminal commands | Phase 0 |
| L8 | Configure environment variables in Catalyst | Console setting | Phase 0 |
| L9 | Run data migration script | Terminal command | Phase 8 |
| L10 | Configure CORS in Catalyst project | Console setting | Phase 9 |

### Things Claude Can Do

| # | Action | Deliverable |
|---|--------|-------------|
| C1 | Write `catalyst_store.py` data access layer | New file |
| C2 | Write Catalyst function adapter (FastAPI → handler) | New file |
| C3 | Implement `CatalystClient` for GLM 4.7 | Modified file |
| C4 | Rewrite NLQ engine for GLM-powered query generation | Modified file |
| C5 | Migrate all 14 routers from SQLAlchemy to ZCQL | Modified files |
| C6 | Write QuickML forecast service | New file |
| C7 | Write seed data migration script | New file |
| C8 | Write Catalyst File Store integration | Modified file |
| C9 | Update config.py for Catalyst settings | Modified file |
| C10 | Generate training data CSV export script | New file |

### ZCQL Constraints (Critical)

Catalyst's ZCQL is NOT full SQL. Key limitations that affect our migration:

| SQL Feature | ZCQL Support | Workaround |
|-------------|-------------|------------|
| `SELECT ... FROM` | ✅ Supported | — |
| `WHERE` with `=`, `!=`, `>`, `<`, `LIKE` | ✅ Supported | — |
| `ORDER BY` | ✅ Supported | — |
| `LIMIT` | ✅ Supported | — |
| `AND`, `OR` | ✅ Supported | — |
| `IN (...)` | ✅ Supported | — |
| `COUNT(*)` | ✅ Supported (single table) | — |
| `GROUP BY` + aggregate | ❌ Not supported | Fetch rows → aggregate in Python |
| `JOIN` (multi-table) | ❌ Not supported | Multiple queries → join in Python |
| `SUM()`, `AVG()` | ❌ Not supported | Compute in Python |
| Subqueries | ❌ Not supported | Sequential queries |
| `strftime()` / date functions | ❌ Not supported | Parse dates in Python |

**Impact**: ~60% of backend endpoints use GROUP BY or JOIN. All must be rewritten to:
1. Fetch raw rows via ZCQL SELECT
2. Aggregate/join in Python using `collections.Counter`, `itertools.groupby`, etc.

---

## Phase 0 — Catalyst Project Init

**Who**: You (manual)  
**Duration**: ~30 minutes  
**Depends on**: Nothing  

### Steps

```bash
# 1. Navigate to project directory
cd C:\Users\Dell\Documents\Suraksha_AI\newcrime\backend

# 2. Initialize Catalyst project (opens browser for Zoho login)
catalyst init

# During init, you'll be asked:
#   - Project name: suraksha-ai
#   - Project type: Select "Advanced I/O"
#   - Language: Python
#   - This creates catalyst.json and functions/ directory

# 3. Verify project structure was created
ls catalyst.json
ls functions/

# 4. Note your Project ID from catalyst.json
cat catalyst.json
# Save the project_id value — needed for all SDK calls

# 5. Enable GLM 4.7:
#    - Go to console.catalyst.zoho.com
#    - Select your project
#    - Navigate to: Zia Services → Large Language Models
#    - Enable GLM 4.7
#    - Note the model ID

# 6. Enable QuickML:
#    - Navigate to: AI → QuickML
#    - Enable it for the project

# 7. Verify Catalyst CLI is authenticated
catalyst whoami
```

### Expected Output

```
newcrime/backend/
├── catalyst.json          # Catalyst project config
├── functions/
│   └── suraksha_api/      # Advanced I/O function directory
│       ├── index.py        # Function entry point (we'll replace this)
│       └── catalyst-config.json
├── app/                   # Existing FastAPI app (stays here)
│   └── ...
└── requirements.txt
```

### Environment Variables to Set

In Catalyst Console → Project Settings → Environment Variables:

| Key | Value | Description |
|-----|-------|-------------|
| `CATALYST_PROJECT_ID` | (from catalyst.json) | Auto-available in Catalyst runtime |
| `LLM_PROVIDER` | `catalyst` | Switches from mock to GLM |
| `GLM_MODEL_ID` | (from GLM settings) | The GLM 4.7 model identifier |
| `QUICKML_MODEL_ID` | (after Phase 6 training) | Prophet model identifier |
| `SECRET_KEY` | (generate a secure key) | For any session/token use |

---

## Phase 1 — Datastore Tables

**Who**: You (manual, in Catalyst Console)  
**Duration**: ~1–2 hours  
**Depends on**: Phase 0  

### Instructions

Go to **Catalyst Console → Datastore → Create Table** for each of the 24 tables listed below.

**Important notes:**
- Catalyst auto-creates `ROWID` (bigint, primary key), `CREATEDTIME`, and `MODIFIEDTIME` for every table
- Do NOT create `id` or `created_at` columns — use `ROWID` and `CREATEDTIME` instead
- Foreign keys are stored as plain `bigint` columns (Catalyst Datastore has no FK constraints — referential integrity is enforced in application code)
- For `text` columns that store JSON (like `behavioral_traits`, `evidence_json`), use `text` type — Catalyst has no native JSON column type

### Table Creation Checklist

See [Appendix A](#appendix-a--full-table-schema) for the complete column-by-column schema for all 24 tables.

- [ ] `users` (11 columns)
- [ ] `officers` (6 columns)
- [ ] `accused` (14 columns)
- [ ] `victims` (8 columns)
- [ ] `cases` (17 columns)
- [ ] `case_accused` (3 columns)
- [ ] `case_victim` (2 columns)
- [ ] `associations` (5 columns)
- [ ] `investigations` (7 columns)
- [ ] `timeline_events` (5 columns)
- [ ] `financial_accounts` (6 columns)
- [ ] `transactions` (8 columns)
- [ ] `crime_patterns` (8 columns)
- [ ] `predictions` (7 columns)
- [ ] `behavior_profiles` (7 columns)
- [ ] `alerts` (7 columns)
- [ ] `conversations` (4 columns)
- [ ] `messages` (9 columns)
- [ ] `case_notes` (5 columns)
- [ ] `evidence_documents` (9 columns)
- [ ] `witnesses` (7 columns)
- [ ] `audit_logs` (17 columns)
- [ ] `stage_approvals` (8 columns)
- [ ] `access_requests` (6 columns)

---

## Phase 2 — Data Access Layer

**Who**: Claude (code)  
**Duration**: ~1 hour  
**Depends on**: Phase 1  

### Goal

Replace `database.py` + SQLAlchemy ORM with a Catalyst Datastore abstraction layer.

### New File: `app/catalyst_store.py`

```
Purpose: Unified data access layer wrapping zcatalyst_sdk
Exposes:
  - CatalystStore class
    - __init__(catalyst_app)  — receives initialized Catalyst app
    - query(zcql: str) → list[dict]
    - insert(table: str, row: dict) → dict (with ROWID)
    - update(table: str, rowid: int, data: dict) → dict
    - delete(table: str, rowid: int) → None
    - get(table: str, rowid: int) → dict | None
    - count(table: str, where: str = "") → int
    - bulk_insert(table: str, rows: list[dict]) → list[dict]
    - aggregate(table: str, group_col: str, where: str = "") → dict[str, int]
      (fetches all rows, groups in Python, returns {value: count})
    - join(left_table, right_table, left_key, right_key, where="") → list[dict]
      (fetches from both tables, joins in Python)
```

### Why This Abstraction

Every router currently does `db.query(Model).filter(...).all()`. We need a single place that:
1. Translates to ZCQL format
2. Handles the GROUP BY limitation (aggregate in Python)
3. Handles the JOIN limitation (multi-query + merge in Python)
4. Provides consistent error handling
5. Makes router migration mechanical (swap ORM calls → store calls)

### Modified File: `app/database.py`

Current `get_db()` FastAPI dependency returns a SQLAlchemy `Session`. After migration:
- `get_db()` → `get_store()` returns a `CatalystStore` instance
- The Catalyst app is initialized once at function startup
- All routers switch from `db: Session = Depends(get_db)` to `store: CatalystStore = Depends(get_store)`

### Migration Pattern for Routers

```python
# BEFORE (SQLAlchemy)
rows = db.query(Case).filter(Case.district == "Mysuru").order_by(Case.created_at.desc()).limit(10).all()

# AFTER (CatalystStore)
rows = store.query("SELECT * FROM cases WHERE district = 'Mysuru' ORDER BY CREATEDTIME DESC LIMIT 10")
```

```python
# BEFORE (SQLAlchemy — GROUP BY)
result = db.query(Case.crime_type, func.count(Case.id)).group_by(Case.crime_type).all()

# AFTER (CatalystStore — aggregate helper)
result = store.aggregate("cases", "crime_type")
# Returns: {"Theft": 45, "Robbery": 23, "Cyber Fraud": 18, ...}
```

```python
# BEFORE (SQLAlchemy — JOIN)
rows = db.query(Accused, BehaviorProfile).join(BehaviorProfile, ...).all()

# AFTER (CatalystStore — join helper)
rows = store.join("accused", "behavior_profiles", "ROWID", "accused_id")
# Returns: [{"accused.full_name": "...", "behavior_profiles.risk_score": 85, ...}]
```

---

## Phase 3 — FastAPI → Catalyst Function Adapter

**Who**: Claude (code)  
**Duration**: ~1 hour  
**Depends on**: Phase 0  

### Goal

Wrap the existing FastAPI ASGI app inside a Catalyst Advanced I/O Function handler so it can be deployed to Catalyst's serverless runtime.

### How It Works

Catalyst Advanced I/O Functions expect a Python entry point:

```python
# functions/suraksha_api/index.py
def handler(request, response):
    # request: CatalystRequest (method, body, params, headers, etc.)
    # response: CatalystResponse (set_status, send, set_content_type, etc.)
    ...
```

We need an **adapter** that converts between Catalyst's request/response format and FastAPI's ASGI protocol. This is similar to how Mangum adapts FastAPI for AWS Lambda.

### New File: `functions/suraksha_api/index.py`

```
Purpose: Catalyst function entry point
Flow:
  1. Receive CatalystRequest
  2. Convert to ASGI scope/receive
  3. Pass through FastAPI app
  4. Collect ASGI response
  5. Convert back to CatalystResponse
  6. Send
```

### New File: `functions/suraksha_api/catalyst_adapter.py`

```
Purpose: ASGI ↔ Catalyst request/response bridge
Class: CatalystASGIAdapter
  - __init__(asgi_app)
  - handle(catalyst_request) → catalyst_response
  - _to_asgi_scope(catalyst_request) → dict
  - _collect_response(asgi_send_events) → (status, headers, body)
```

### Modified File: `app/main.py`

Minimal changes:
- Add a `create_app()` factory function that the adapter calls
- Move the Catalyst SDK initialization to app startup
- Keep all middleware and router registration as-is
- Remove the `uvicorn.run()` block (Catalyst runtime handles serving)

### Local Development

For local development, we keep the ability to run with uvicorn:

```bash
# Local dev (unchanged)
uvicorn app.main:app --port 8077

# Catalyst deployment
catalyst deploy
```

The function entry point imports the same FastAPI `app` — the adapter only activates when running inside Catalyst's runtime.

---

## Phase 4 — GLM 4.7 Integration (NLQ v2)

**Who**: Claude (code)  
**Duration**: ~2 hours  
**Depends on**: Phase 0 (GLM enabled), Phase 2  

### Goal

Replace the rule-based NLQ engine with GLM 4.7-powered natural language understanding.

### Current Flow (Mock — Rule-Based)

```
User: "How many cyber fraud cases in Bengaluru?"
  ↓
_extract(): keyword match → crime="Cyber Fraud", district="Bengaluru City"
  ↓
Intent routing: "how many" → count_cases intent
  ↓
ORM query: db.query(func.count(Case.id)).filter(crime_type="Cyber Fraud", district="Bengaluru City")
  ↓
Template: "There are {n} case(s) matching Cyber Fraud, Bengaluru City."
```

### New Flow (GLM 4.7-Powered)

```
User: "How many cyber fraud cases in Bengaluru?"
  ↓
GLM Call 1 — Query Generation:
  System prompt: schema context + ZCQL rules + few-shot examples
  User prompt: the question
  Response: {
    "intent": "count_cases",
    "zcql": "SELECT * FROM cases WHERE crime_type = 'Cyber Fraud' AND district = 'Bengaluru City'",
    "reasoning": "User wants count of cases filtered by crime type and district"
  }
  ↓
Execute ZCQL against Catalyst Datastore → raw rows
  ↓
Python aggregation: len(rows) = count
  ↓
GLM Call 2 — Answer Synthesis:
  System prompt: analyst persona + language instruction
  User prompt: question + structured findings
  Response: Natural language answer in English/Kannada
  ↓
Return: {answer, sql, evidence, reasoning, grounding}
```

### Modified File: `app/llm/client.py`

Implement `CatalystClient`:

```
CatalystClient(LLMClient):
  provider = "catalyst"
  
  __init__():
    Initialize zcatalyst_sdk
    Get GLM model reference
  
  complete(system, prompt, **kw) → str:
    Call GLM 4.7 chat API via zcatalyst_sdk
    Messages: [{role: "system", content: system}, {role: "user", content: prompt}]
    Return: response text
  
  narrate(question, findings, language) → str:
    System: "You are a police crime-intelligence analyst..."
    GLM rephrases findings in English or Kannada
  
  generate_query(question, schema_context) → dict:
    NEW method — GLM generates ZCQL from natural language
    System: schema + ZCQL rules + few-shot examples
    User: the question
    Returns: {intent, zcql, filters, reasoning}
    Includes validation: only SELECT allowed, table names must match schema
```

### GLM API Call Pattern (zcatalyst_sdk 1.4.0)

```python
import zcatalyst_sdk

app = zcatalyst_sdk.initialize()
# The exact API path depends on the SDK version.
# Likely patterns:
#   app.zia().get_glm().chat(messages=[...])
#   OR: direct REST call to /baas/v1/project/{id}/glm/chat
#
# ⚠ VERIFY: The exact GLM chat API method in zcatalyst_sdk 1.4.0
#   needs to be confirmed after project init. If the SDK doesn't expose
#   GLM directly, we fall back to REST via requests library:
#
#   POST https://{domain}/baas/v1/project/{project_id}/glm/chat
#   Headers: Authorization: Zoho-catalyst ...
#   Body: {model: "glm-4.7", messages: [...]}
```

### Modified File: `app/services/nlq.py`

Major rewrite — replace the keyword-matching `answer_question()` with:

```
answer_question(store, question, language=None) → dict:
  1. Detect language (keep existing _detect_lang)
  2. Call GLM generate_query(question, SCHEMA_CONTEXT)
  3. Validate the generated ZCQL (whitelist tables, block mutations)
  4. Execute ZCQL via store.query()
  5. If intent needs aggregation, aggregate in Python
  6. Build evidence list from raw rows
  7. Call GLM narrate(question, structured_findings, language)
  8. Build grounding + reasoning trace
  9. Return {intent, answer, sql, evidence, data, grounding, reasoning}
```

### SCHEMA_CONTEXT (Injected into GLM System Prompt)

```
You have access to a crime intelligence database with these tables:

TABLE cases: ROWID (id), fir_number, title, description, crime_type, crime_head,
  modus_operandi, status, severity, district, station, location_name, latitude,
  longitude, is_financial, loss_amount, occurrence_date, reported_date, CREATEDTIME

TABLE accused: ROWID (id), full_name, aliases, gender, age, address, district,
  phone_number, occupation, education, socio_economic, urban_rural, migrant,
  previous_convictions, status

TABLE victims: ROWID (id), full_name, gender, age, contact_number, address,
  district, occupation, statement_summary

... (all 24 tables listed with columns)

ZCQL RULES:
- Only SELECT queries allowed
- No GROUP BY — fetch rows and I will aggregate
- No JOINs — I will query each table separately
- Supported: WHERE, ORDER BY, LIMIT, IN, LIKE, AND, OR, COUNT(*)
- Date format: YYYY-MM-DD
- String comparison is case-sensitive — use exact values

CRIME_TYPES: Theft, Burglary, Robbery, Vehicle Theft, Chain Snatching,
  Assault, Murder, Kidnapping, Domestic Violence, Cyber Fraud, Bank Fraud,
  UPI Scam, Extortion, Drug Trafficking, Human Trafficking, Rioting

DISTRICTS: Bengaluru City, Bengaluru Rural, Mysuru, Mangaluru, Hubballi-Dharwad,
  Belagavi, Kalaburagi, Ballari, Vijayapura, Davanagere, Shivamogga, Tumakuru,
  Udupi, Hassan, Mandya

Respond in JSON: {"intent": "...", "zcql": "SELECT ...", "reasoning": "..."}
```

### Safety: Query Validation

Before executing any GLM-generated ZCQL:

```python
def validate_zcql(zcql: str) -> bool:
    # 1. Must start with SELECT (no INSERT/UPDATE/DELETE/DROP)
    # 2. Table names must be in ALLOWED_TABLES set
    # 3. No semicolons (prevent injection of multiple statements)
    # 4. Max length 500 chars
    # 5. No system tables (CATALYSTUSER, etc.)
```

---

## Phase 5 — Router Migration (SQLAlchemy → ZCQL)

**Who**: Claude (code)  
**Duration**: ~4–6 hours  
**Depends on**: Phase 2  

### Goal

Modify all 14 router files to use `CatalystStore` instead of SQLAlchemy ORM.

### Migration Strategy

Every endpoint follows this pattern:

1. Change dependency: `db: Session = Depends(get_db)` → `store = Depends(get_store)`
2. Replace ORM queries with ZCQL via `store.query()`
3. Replace aggregations with `store.aggregate()` or Python-side computation
4. Replace JOINs with `store.join()` or sequential queries + merge
5. Replace `model.attribute` access with `row["column_name"]` dict access
6. Replace `model.id` with `row["ROWID"]`
7. Replace `model.created_at` with `row["CREATEDTIME"]`

### Per-Router Migration Details

#### 5.1 `auth.py` — Low complexity

| Endpoint | Current | After |
|----------|---------|-------|
| POST /login | `db.query(User).filter(username=...)` | `store.query("SELECT * FROM users WHERE username = ...")` |
| GET /users | `db.query(User).all()` | `store.query("SELECT * FROM users")` |

#### 5.2 `cases.py` — High complexity

| Endpoint | Challenge |
|----------|-----------|
| GET /cases | Filter + pagination, straightforward ZCQL |
| GET /cases/filters | 3 DISTINCT queries for dropdowns → aggregate in Python |
| GET /cases/{id} | Needs JOINs: case → case_accused → accused, case → case_victim → victims, case → investigation → officer, case → timeline_events. **Workaround**: 5 sequential queries, merge in Python |
| POST /cases | Insert into cases table, parse multipart form. Auto-generates `fir_number` if blank. Creates `TimelineEvent`. Sets `status=Open`, `reported_date=now`. |
| PUT /cases/{id} | Update row by ROWID. Updatable fields: title, description, crime_type, crime_head, modus_operandi, severity, district, station, location_name, status, loss_amount. |
| POST /cases/{id}/chargesheet | JOIN case_accused, case_victim, witnesses, evidence_documents, investigations — 6 sequential queries. `_infer_sections()` maps crime_type → BNS/IPC sections (hardcoded map for 17 types, must be preserved). Creates a `TimelineEvent` ("Chargesheet Generated"). **Not persisted** — computed on every request. |
| GET /cases/{id}/similar | Filter by crime_type/district, score by MO overlap in Python |

#### 5.3 `analytics.py` — Very High complexity (11 endpoints)

Almost every endpoint uses GROUP BY + COUNT which ZCQL doesn't support.

| Endpoint | Current | After |
|----------|---------|-------|
| GET /overview | 5 aggregate queries | Fetch all cases → compute in Python: total, open count, solved count, clearance rate, etc. |
| GET /by-type | `GROUP BY crime_type` | `store.aggregate("cases", "crime_type")` |
| GET /by-head | `GROUP BY crime_head` | `store.aggregate("cases", "crime_head")` |
| GET /trend | `GROUP BY strftime(month)` | Fetch all → `Counter(row["occurrence_date"][:7] for row in rows)` |
| GET /hotspots | `GROUP BY district` | `store.aggregate("cases", "district")` |
| GET /geo | Simple SELECT with lat/lon | Straightforward ZCQL |
| GET /district-map | Complex: group by district + count + territory scope | Fetch → aggregate → merge with geo centroids |
| GET /temporal | `GROUP BY month-of-year, day-of-week` | Fetch all → extract datetime parts → aggregate |
| GET /patterns | Simple SELECT | Straightforward ZCQL |
| GET /hotspot-dashboard | 4+ aggregate sub-queries | Fetch all → compute all aggregations in one pass |
| GET /crime-category/{type} | 5 sub-dimensions (demo, geo, temporal, behavioral, financial) | Fetch cases of type → compute each dimension in Python |

#### 5.4 `network.py` — High complexity

| Endpoint | Challenge |
|----------|-----------|
| GET /graph | Self-join on associations (source→accused, target→accused). Need 2 queries: all associations + all accused, then build graph in Python |
| GET /gangs | GROUP BY gang_name → `store.aggregate("associations", "gang_name")` |
| GET /accused/{id} | Filter associations by source/target + lookup accused names |

#### 5.5 `profiling.py` — High complexity

| Endpoint | Challenge |
|----------|-----------|
| GET /offenders | JOIN accused + behavior_profiles → 2 queries + merge |
| GET /distribution | GROUP BY risk_band → `store.aggregate("behavior_profiles", "risk_band")` |
| GET /offender/{id} | JOIN accused + profile + case_accused → 3 queries + merge |

#### 5.6 `socio.py` — High complexity (7 endpoints)

All endpoints use GROUP BY on accused demographics.

| Endpoint | Migration |
|----------|-----------|
| GET /gender | `store.aggregate("accused", "gender")` |
| GET /age-bands | Fetch all → bucket ages in Python |
| GET /socio-economic | `store.aggregate("accused", "socio_economic")` |
| GET /education | `store.aggregate("accused", "education")` |
| GET /urban-rural | `store.aggregate("accused", "urban_rural")` |
| GET /risk-factors | JOIN accused + profiles → correlate in Python |
| GET /crime-by-demographic | 3-way data: cases + case_accused + accused → merge + group |

#### 5.7 `forecasting.py` — Low (replaced by QuickML)

| Endpoint | Migration |
|----------|-----------|
| GET /predictions | Replaced by QuickML API call (Phase 6) |

#### 5.8 `financial.py` — Medium complexity

| Endpoint | Challenge |
|----------|-----------|
| GET /summary | Multiple aggregates on transactions |
| GET /graph | JOIN accounts + transactions → 2 queries + build graph |
| GET /suspicious-accounts | Filter + aggregate transaction counts per account |

#### 5.9 `alerts.py` — Low complexity

| Endpoint | Migration |
|----------|-----------|
| GET /alerts | Simple ZCQL SELECT |
| POST /alerts/{id}/resolve | `store.update("alerts", id, {resolved: true})` |

#### 5.10 `dashboards.py` — Very High complexity

Two major endpoints. The Command Center is the most complex in the entire app.

**`GET /workspace/overview`** returns:
- `officer` (from Ctx), `can_command` (boolean)
- `kpis` (4 items, varies by role — analyst vs command vs field)
- `my_cases` (up to 8, territory-scoped)
- `stream` (up to 8 recent timeline events joined with cases)

**`GET /command/overview`** returns ALL of:
- `scope`, `command_level`, `district`, `subdivision`, `range_name`
- `kpis` (10 fields: total_cases, open, clearance_rate, firs_this_month, firs_change, arrests_month, by_status, pending_cases, chargesheet_rate, conviction_rate)
- `stream` (12 events), `alerts` (8), `offenders` (8), `predictions` (8)
- `district_breakdown`, `crime_type_breakdown`
- `ai_insights` (up to 8 — computed by `_ai_insights()`, queries 5+ tables)
- `ai_recommendations` (up to 10 — computed by `_ai_recommendations()`, scope-adaptive rule engine)
- `neighbor_intel` (cross-border intelligence from geo.py neighbors)
- `station_performance`, `investigation_summary`, `district_ranking`, `station_hotspots`
- `forecast_analysis` (crime trend comparison + risk summary)

**Strategy**: Fetch bulk data once per table, compute all sections in Python:
1. Fetch all cases (in scope) → KPIs, trends, district breakdown, crime type breakdown, station performance
2. Fetch predictions → forecast section + forecast analysis
3. Fetch alerts → alert stream
4. Fetch accused + behavior_profiles → top offenders + AI insights
5. Fetch associations → neighbor intelligence
6. Fetch investigations → investigation summary
7. Fetch timeline_events + cases → intelligence stream
8. Run `_ai_insights()` and `_ai_recommendations()` with fetched data

#### 5.11 `investigation.py` — High complexity (28 endpoints)

Mix of CRUD and complex queries. File uploads move to Catalyst File Store (Phase 7).

| Group | Endpoints | Challenge |
|-------|-----------|-----------|
| Investigation bundle | GET /{case_id} | JOIN investigations + officers + cases + counts of notes/evidence/witnesses |
| Stage management | POST /{case_id}/stage | Update investigation row |
| Notes CRUD | GET/POST notes, POST pin, DELETE note | Simple ZCQL, no JOINs |
| Witnesses | GET/POST witnesses, GET document | File upload → File Store. PII masking on list. |
| Victims (case-scoped) | GET/POST/PUT victims, POST link, DELETE unlink | Multi-table: victims + case_victim. PII masking. |
| Evidence | GET/POST evidence, GET download, DELETE | File upload → File Store. `ai_summary` → GLM. |
| Approvals | POST request, GET list, POST review, GET pending | Stage approvals table. APPROVER_ROLES check. |
| Access control | POST request, GET list, POST review, POST emergency | Access requests table. EMERGENCY_ROLES (DSP+) check. |
| Case chat | GET/POST chat | Conversation with case_id set. NLQ engine + file upload. |

#### 5.12 `victims.py` — High complexity (7 endpoints)

| Endpoint | Challenge |
|----------|-----------|
| GET /overview | Multiple aggregates: total, repeat_victims, by_gender, by_age (buckets), by_district. All GROUP BY → Python aggregation. |
| GET /crime-types | JOIN case_victim + cases → aggregate crime_type counts |
| GET /list | Paginated list with case_count per victim. JOIN victims + case_victim + cases. PII masking. |
| GET /vulnerability/assessment | Top 20 by case_count with risk_level and contributing_factors. JOIN victims + case_victim. |
| GET /{id}/intelligence | Cross-table: victim → case_victim → cases → case_accused → accused. Builds case history, district/crime breakdowns, timeline, AI text summary (computed, not stored). |
| GET /{id}/relationships | Graph from 5+ tables: victim, case_victim, cases, case_accused, accused, witnesses, investigations, officers. Builds nodes + edges for relationship visualization. |
| GET /{id} | Victim detail with linked cases via case_victim JOIN. PII masking. |

#### 5.13 `audit.py` — Medium complexity

| Endpoint | Migration |
|----------|-----------|
| GET /logs | Simple ZCQL with WHERE filters |
| GET /summary | Multiple GROUP BY aggregates |

Territory scoping in `_scope_query()` translates to ZCQL WHERE clause with `IN (...)`.

#### 5.14 `chat.py` — Medium complexity

| Endpoint | Migration |
|----------|-----------|
| GET /conversations | Simple ZCQL SELECT, ordered by MODIFIEDTIME DESC |
| GET /conversations/{id} | Fetch conversation + all messages by conversation_id |
| POST /message | Multipart form (message, conversation_id, language, optional file upload). Calls NLQ v2 (Phase 4). Stores user message + assistant response in `messages` table with evidence_json, grounding_json, reasoning_json, sql_text, intent. File uploads → File Store (Phase 7). Entity extraction via `fileparse.py`. |
| DELETE /conversations/{id} | Delete conversation + all associated messages (2 sequential deletes) |

**Note**: Case-scoped chat lives in `investigation.py` (GET/POST `/investigation/{case_id}/chat`), not here. Both use the same NLQ engine and Message model but case chat sets `conversation.case_id`.

---

## Phase 6 — QuickML Prophet Forecasting

**Who**: You (training) + Claude (integration code)  
**Duration**: ~2 hours  
**Depends on**: Phase 1 (tables exist), Phase 8 (data migrated)  

### Step 1: Generate Training Data (Claude writes script, you run it)

**New file**: `app/export_training_data.py`

```
Purpose: Export historical crime data as CSV for QuickML training
Output: training_data.csv with columns:
  - date (YYYY-MM-DD, first of each month)
  - crime_type (string)
  - district (string)
  - case_count (integer)
Aggregated from cases table by month × crime_type × district
```

### Step 2: Upload & Train in QuickML (You — Manual)

```
1. Go to Catalyst Console → AI → QuickML
2. Create new model:
   - Name: crime_forecast_prophet
   - Type: Time Series Forecasting
   - Algorithm: Prophet
3. Upload training_data.csv
4. Configure:
   - Date column: date
   - Target column: case_count
   - Group by: crime_type, district
   - Forecast horizon: 30 days
5. Train the model
6. Note the Model ID after training completes
7. Set QUICKML_MODEL_ID environment variable in Catalyst
```

### Step 3: Integration Code (Claude writes)

**New file**: `app/services/forecast.py`

```
Purpose: Call QuickML Prophet for live predictions
Functions:
  - get_forecast(crime_type, district, horizon_days=30) → list[dict]
    Returns: [{date, predicted_count, lower_bound, upper_bound}, ...]
  - get_risk_assessment(district) → dict
    Calls Prophet for multiple crime types, returns risk summary
```

**Modified file**: `app/routers/forecasting.py`

```
- GET /api/forecasting/predictions
  Before: reads static Prediction rows from database
  After: calls forecast.get_forecast() for live Prophet predictions
  Fallback: if QuickML is unavailable, reads cached predictions from Datastore
```

**Modified file**: `app/routers/dashboards.py`

```
- _forecast_analysis() function
  Before: compares current vs previous 30-day counts
  After: calls Prophet for forward-looking predictions + trend comparison
```

---

## Phase 7 — File Storage Migration

**Who**: Claude (code)  
**Duration**: ~1 hour  
**Depends on**: Phase 0  

### Goal

Move evidence document and witness file uploads from local disk to Catalyst File Store.

### Affected Endpoints (7 total)

| Endpoint | Current | After |
|----------|---------|-------|
| POST /investigation/{id}/evidence | Saves to `uploads/{case_id}/` | Upload to Catalyst File Store `evidence_documents` folder → store file_id in Datastore |
| GET /investigation/evidence/{id}/download | `FileResponse(path)` | Stream from Catalyst File Store |
| DELETE /investigation/evidence/{id} | `os.remove(path)` | Delete from Catalyst File Store |
| POST /investigation/{id}/witnesses | Saves doc to `uploads/{case_id}/witnesses/` | Upload to Catalyst File Store `witness_documents` folder |
| GET /investigation/witnesses/document/{id} | `FileResponse(path)` | Stream from Catalyst File Store |
| POST /chat/message (with file) | Saves to `uploads/global_chat/` | Upload to Catalyst File Store `chat_uploads` folder |
| POST /investigation/{id}/chat (with file) | Saves to `uploads/{case_id}/chat_uploads/` | Upload to Catalyst File Store `chat_uploads` folder |

### Catalyst File Store API Pattern

```python
app = zcatalyst_sdk.initialize()
file_store = app.filestore()
folder = file_store.folder(folder_id)

# Upload
result = folder.upload_file(file_name, file_stream)
file_id = result["id"]

# Download
file_content = folder.download_file(file_id)

# Delete
folder.delete_file(file_id)
```

### File Store Setup (You — Manual)

```
1. Go to Catalyst Console → File Store
2. Create folder: "evidence_documents"
3. Create folder: "witness_documents"
4. Create folder: "chat_uploads"
5. Note the folder IDs
6. Set in environment variables:
   EVIDENCE_FOLDER_ID=<id>
   WITNESS_FOLDER_ID=<id>
   CHAT_UPLOADS_FOLDER_ID=<id>
```

### Evidence AI Summary

Currently `_mock_summary()` in `investigation.py` returns a static template. During migration, replace with a GLM 4.7 call that:
1. Extracts text from the uploaded file (using existing `fileparse.py`)
2. Sends extracted text to GLM with system prompt: "Summarize this evidence document for a police investigation"
3. Stores the GLM-generated summary in `evidence_documents.ai_summary`

---

## Phase 8 — Seed Data Migration

**Who**: Claude (writes script) + You (runs it)  
**Duration**: ~1 hour  
**Depends on**: Phase 1, Phase 2  

### New File: `app/migrate_to_catalyst.py`

```
Purpose: One-time migration script
Flow:
  1. Read existing SQLite database (crimeintel.db)
  2. For each of the 24 tables:
     a. Fetch all rows from SQLite
     b. Transform to Catalyst Datastore format:
        - Remove 'id' (Catalyst assigns ROWID)
        - Remove 'created_at' (Catalyst assigns CREATEDTIME)
        - Convert datetime objects to ISO strings
        - Convert Python booleans to Catalyst booleans
     c. Bulk insert into Catalyst Datastore via SDK
  3. Build a ROWID mapping (old SQLite id → new Catalyst ROWID)
     for maintaining foreign key references
  4. Update FK columns with new ROWIDs
  5. Print migration summary (rows per table, any errors)
```

### Execution

```bash
# You run this after Phase 0 + Phase 1 are complete
cd newcrime/backend
python -m app.migrate_to_catalyst
```

### Foreign Key Re-mapping

Since Catalyst assigns new ROWIDs, the FK references must be updated:

```
Order of migration (respecting FK dependencies):
  1. users, officers (no FKs)
  2. accused, victims (no FKs)
  3. cases (no FKs)
  4. financial_accounts (FK → accused)
  5. investigations (FK → cases, officers)
  6. case_accused (FK → cases, accused)
  7. case_victim (FK → cases, victims)
  8. associations (FK → accused × accused)
  9. behavior_profiles (FK → accused)
  10. timeline_events (FK → cases)
  11. transactions (FK → accounts, cases)
  12. alerts, crime_patterns, predictions (no FKs)
  13. conversations (FK → users, cases)
  14. messages (FK → conversations)
  15. case_notes, witnesses, evidence_documents (FK → cases)
  16. stage_approvals, access_requests (FK → cases)
  17. audit_logs (no FKs — text references only)
```

---

## Phase 9 — Deployment & Validation

**Who**: Both  
**Duration**: ~2 hours  
**Depends on**: All previous phases  

### Step 1: Configure CORS (You — Manual)

In Catalyst Console → Project Settings:
- Add allowed origin: `http://localhost:5173` (dev)
- Add allowed origin: your production frontend URL
- Allow methods: GET, POST, PUT, DELETE, OPTIONS
- Allow headers: Content-Type, X-User-Id, X-User-Name, X-User-Role, X-User-District, X-User-Subdivision, X-User-Range

### Step 2: Deploy (You — Manual)

```bash
cd newcrime/backend
catalyst deploy
```

### Step 3: Update Frontend API Base URL

**Modified file**: `newcrime/frontend/src/api.ts`

```typescript
// Change BASE from localhost to Catalyst function URL
const BASE = "https://<project-domain>.catalyst.zoho.com/baas/v1/project/<project-id>/function/<function-id>";
// OR use environment variable:
const BASE = import.meta.env.VITE_API_BASE || "http://localhost:8077/api";
```

### Step 4: Validation Checklist (30 Tests)

#### Core

| # | Test | Action | Expected |
|---|------|--------|----------|
| 1 | Health check | GET /api/health | `{"status": "ok", "llm_provider": "catalyst"}` |
| 2 | Login (DGP) | POST /api/auth/login dgp_kumar/password | User object with state scope, all screens |
| 3 | Login (constable) | POST /api/auth/login pc_suresh/password | Limited screens, no PII/audit |
| 4 | Demo users | GET /api/auth/users | 17 demo accounts listed |

#### Cases & FIR

| # | Test | Action | Expected |
|---|------|--------|----------|
| 5 | Cases list | GET /api/cases | 260 cases with all fields |
| 6 | Case filters | GET /api/cases/filters | 17 crime types, 15 districts, 5 statuses |
| 7 | Case detail | GET /api/cases/1 | Case with accused[], victims[], investigation, timeline[] |
| 8 | Create FIR | POST /api/cases (title, crime_type, district) | New case with auto-generated fir_number, status=Open |
| 9 | Update case | PUT /api/cases/{id} (status=Chargesheeted) | Updated status |
| 10 | Chargesheet | POST /api/cases/{id}/chargesheet | Draft with accused, victims, witnesses, evidence, applicable_sections (BNS/IPC) |
| 11 | Similar cases | GET /api/cases/{id}/similar | Scored list by crime_type/district/MO |

#### Analytics & Dashboards

| # | Test | Action | Expected |
|---|------|--------|----------|
| 12 | Analytics overview | GET /api/analytics/overview | KPIs: total, open, solved, clearance |
| 13 | Crime trend | GET /api/analytics/trend | Monthly time series |
| 14 | Hotspot dashboard | GET /api/analytics/hotspot-dashboard | State view, district drill-down, trend |
| 15 | Crime category | GET /api/analytics/crime-category/Theft | Demo, geo, temporal, behavioral, financial dims |
| 16 | Workspace | GET /api/workspace/overview | Role-scoped KPIs, my_cases, stream |
| 17 | Command center | GET /api/command/overview (as DGP) | All fields: KPIs, ai_insights, ai_recommendations, neighbor_intel, district_ranking, forecast_analysis |

#### Chat & NLQ

| # | Test | Action | Expected |
|---|------|--------|----------|
| 18 | Global chat | POST /api/chat/message "How many theft cases?" | GLM answer with evidence, reasoning, grounding |
| 19 | Case chat | POST /api/investigation/{id}/chat "Summarize this case" | Case-scoped conversation with case_id set |
| 20 | Chat with file | POST /api/chat/message + PDF upload | Entity extraction + answer |

#### Investigation Workflow

| # | Test | Action | Expected |
|---|------|--------|----------|
| 21 | Add note | POST /api/investigation/{id}/notes | Note created, timeline event logged |
| 22 | Pin note | POST /api/investigation/notes/{id}/pin | Pinned toggled |
| 23 | Add witness | POST /api/investigation/{id}/witnesses + doc | Witness + document uploaded to File Store |
| 24 | Upload evidence | POST /api/investigation/{id}/evidence + file | File in File Store, ai_summary populated by GLM |
| 25 | Stage request | POST /api/investigation/{id}/stage/request | Approval record created |
| 26 | Approve stage | POST /api/investigation/approval/{id}/review (as PI) | Stage approved, investigation updated |

#### Forecasting, Financial, Audit

| # | Test | Action | Expected |
|---|------|--------|----------|
| 27 | Forecasting | GET /api/forecasting/predictions | Prophet-generated predictions with confidence |
| 28 | Money trail | GET /api/financial/graph | Account nodes + transaction edges |
| 29 | Audit trail | GET /api/audit/summary (as PI) | Territory-scoped audit data |

#### RBAC & Territory

| # | Test | Action | Expected |
|---|------|--------|----------|
| 30 | Audit blocked | GET /api/audit/summary (as constable) | 403 Forbidden |
| 31 | Territory scope | GET /api/cases (as SP of Mysuru) | Only Mysuru district cases |
| 32 | Emergency access | POST /api/investigation/{id}/emergency-access (as DSP) | Access granted |
| 33 | Emergency denied | POST /api/investigation/{id}/emergency-access (as SI) | 403 — role too low |

---

## File Change Summary

### New Files (6)

| File | Purpose | Phase |
|------|---------|-------|
| `app/catalyst_store.py` | Data access layer wrapping zcatalyst_sdk | 2 |
| `functions/suraksha_api/index.py` | Catalyst function entry point | 3 |
| `functions/suraksha_api/catalyst_adapter.py` | ASGI ↔ Catalyst bridge | 3 |
| `app/services/forecast.py` | QuickML Prophet integration | 6 |
| `app/export_training_data.py` | CSV export for Prophet training | 6 |
| `app/migrate_to_catalyst.py` | One-time SQLite → Datastore migration | 8 |

### Modified Files (19)

| File | Change | Phase |
|------|--------|-------|
| `app/config.py` | Add Catalyst config fields (project_id, folder IDs, GLM model ID, QuickML model ID) | 2 |
| `app/database.py` | Replace SQLAlchemy with CatalystStore dependency | 2 |
| `app/main.py` | Add create_app() factory, remove uvicorn block, keep audit middleware | 3 |
| `app/llm/client.py` | Implement CatalystClient with GLM 4.7 | 4 |
| `app/services/nlq.py` | Rewrite for GLM-powered NLQ | 4 |
| `app/routers/auth.py` | SQLAlchemy → ZCQL | 5 |
| `app/routers/cases.py` | SQLAlchemy → ZCQL + preserve `_infer_sections()` BNS map | 5 |
| `app/routers/analytics.py` | SQLAlchemy → ZCQL (heaviest — 11 endpoints) | 5 |
| `app/routers/network.py` | SQLAlchemy → ZCQL | 5 |
| `app/routers/profiling.py` | SQLAlchemy → ZCQL | 5 |
| `app/routers/socio.py` | SQLAlchemy → ZCQL | 5 |
| `app/routers/forecasting.py` | Replace with QuickML calls | 5, 6 |
| `app/routers/financial.py` | SQLAlchemy → ZCQL | 5 |
| `app/routers/alerts.py` | SQLAlchemy → ZCQL | 5 |
| `app/routers/dashboards.py` | SQLAlchemy → ZCQL + preserve AI insight/recommendation engines | 5 |
| `app/routers/investigation.py` | SQLAlchemy → ZCQL + File Store + GLM evidence summary | 5, 7 |
| `app/routers/chat.py` | SQLAlchemy → ZCQL + File Store for uploads | 5, 7 |
| `app/routers/victims.py` | SQLAlchemy → ZCQL | 5 |
| `app/routers/audit.py` | SQLAlchemy → ZCQL | 5 |

### Frontend Fix (1 file)

| File | Change | Phase |
|------|--------|-------|
| `frontend/src/api.ts` | Fix `reviewAccessRequest()`: change `fd.append("status", status)` → `fd.append("action", status)`. Also update `BASE` URL for Catalyst. | Pre-migration, 9 |

### Unchanged Files

| File | Why |
|------|-----|
| `app/deps.py` | RBAC matrix + Ctx class — no DB dependency |
| `app/geo.py` | Static geographic data — no DB dependency |
| `app/schemas.py` | Pydantic models — no change needed |
| `app/services/fileparse.py` | File parsing — no DB dependency |
| `app/models.py` | Kept for reference / local dev; not used in Catalyst runtime |
| `app/seed.py` | Kept for reference / local dev; not used in Catalyst runtime |
| All frontend files | API contract unchanged |

### Files No Longer Used in Production

| File | Reason |
|------|--------|
| `app/models.py` | SQLAlchemy models replaced by Datastore tables |
| `app/seed.py` | Replaced by migrate_to_catalyst.py |
| `crimeintel.db` | SQLite database replaced by Catalyst Datastore |

---

## Pre-Migration Bug Fixes

These issues exist in the current codebase and should be fixed before or during the Catalyst migration:

| # | Bug | File | Fix |
|---|-----|------|-----|
| B1 | **`reviewAccessRequest` sends wrong field name** — frontend sends `"status"` but backend expects `"action"`; causes 422 on access request reviews | `frontend/src/api.ts:241` / `investigation.py:532` | Change `fd.append("status", status)` → `fd.append("action", status)` |
| B2 | **`conversations.user_id` never populated** — global and case chats create conversations without setting user_id | `chat.py:75`, `investigation.py:619` | Set `user_id` from `ctx.user_id` on conversation creation |
| B3 | **`audit_logs.prev_value` / `new_value` never populated** — columns exist but audit middleware only logs action, not change data | `main.py` audit middleware | For update/delete actions, capture before-state and include in audit log |
| B4 | **`MyAccess.tsx` missing screens** — ALL_SCREENS constant doesn't include `work` and `victims`, so the displayed access matrix is incomplete | `frontend/src/pages/MyAccess.tsx:12` | Add `"work"` and `"victims"` to ALL_SCREENS |
| B5 | **No witness update/delete endpoints** — witnesses can be added but never edited or removed | `investigation.py` | Add `PUT /investigation/{case_id}/witnesses/{id}` and `DELETE /investigation/witnesses/{id}` |
| B6 | **Case update missing fields** — `occurrence_date`, `latitude`, `longitude`, `is_financial` can't be updated after FIR creation | `cases.py:160` | Add these fields to the updatable set |

---

## Computed Features Preserved During Migration

These features are NOT stored in any table — they are computed in Python from queries across multiple tables. The computation logic in the following functions must be preserved exactly during the router migration (Phase 5):

| Function | File | Produces | Tables Queried |
|----------|------|----------|----------------|
| `_ai_recommendations()` | `dashboards.py:113-285` | Up to 10 action items (action, priority, impact, risk_score, confidence, category) | cases, predictions, accused, behavior_profiles, associations |
| `_ai_insights()` | `dashboards.py:288-411` | Up to 8 intelligence insights (title, detail, severity, category) | cases, accused, behavior_profiles, investigations, transactions |
| `_forecast_analysis()` | `dashboards.py:652-714` | Crime trend comparison + risk summary | cases, predictions |
| `_infer_sections()` | `cases.py:239+` | BNS/IPC applicable sections for chargesheet | Hardcoded map (17 crime types → legal sections) |
| `_mock_summary()` | `investigation.py:354` | Evidence AI summary | Replace with GLM 4.7 call |
| Intelligence stream | `dashboards.py:86,767` | Recent timeline events with case cross-reference | timeline_events, cases |
| Victim intelligence | `victims.py:100-153` | Case history + AI text summary | victims, case_victim, cases, case_accused, accused |
| Victim relationships | `victims.py:170-270` | Graph nodes + edges | 5+ tables |
| Vulnerability assessment | `victims.py:73-97` | Top 20 most-victimized with risk factors | victims, case_victim |

---

## Risk Register

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|------------|
| R1 | ZCQL performance — fetching all rows for Python aggregation is slow on large datasets | Medium | High | Add pagination, cache hot aggregations, use Catalyst Cache for dashboard KPIs |
| R2 | GLM 4.7 generates invalid ZCQL | Medium | Medium | Strict validation layer + fallback to rule-based NLQ if validation fails |
| R3 | GLM 4.7 latency > 3s per query (two LLM calls per NLQ) | High | Medium | Cache schema context, parallelize query gen + narration where possible, show loading UI |
| R4 | QuickML Prophet accuracy is low on small training data (260 cases) | High | Medium | Supplement with synthetic data, use longer forecast windows, show confidence intervals |
| R5 | Catalyst Datastore row limits (free tier) | Medium | High | Monitor row counts, archive old audit_logs periodically |
| R6 | Catalyst function cold start latency | Medium | Low | Use Catalyst's "keep warm" setting if available |
| R7 | File Store upload size limits | Low | Medium | Check Catalyst limits, compress before upload if needed |
| R8 | GLM API format differs from what we scaffold | Medium | Medium | Test with a minimal GLM call before full integration; adjust adapter |
| R9 | CORS not working with Catalyst function URL | Low | High | Test CORS headers early in Phase 9 |
| R10 | Foreign key re-mapping fails during migration | Medium | High | Run migration in dry-run mode first, validate counts |

---

## Appendix A — Full Table Schema

### Table: `users`

| Column | Catalyst Type | Nullable | Notes |
|--------|--------------|----------|-------|
| username | text | No | Unique |
| full_name | text | No | |
| email | text | Yes | |
| password | text | No | Plaintext (demo only) |
| role | text | No | Key into ROLE_MATRIX |
| badge_number | text | Yes | |
| district | text | Yes | |
| subdivision | text | Yes | |
| station | text | Yes | |
| range_name | text | Yes | |
| is_active | boolean | No | Default: true |

### Table: `officers`

| Column | Catalyst Type | Nullable | Notes |
|--------|--------------|----------|-------|
| badge_number | text | No | Unique |
| name | text | No | |
| rank | text | No | |
| posting_station | text | Yes | |
| district | text | Yes | |
| contact_number | text | Yes | |

### Table: `accused`

| Column | Catalyst Type | Nullable | Notes |
|--------|--------------|----------|-------|
| full_name | text | No | |
| aliases | text | Yes | |
| gender | text | Yes | M / F |
| age | int | Yes | |
| address | text | Yes | |
| district | text | Yes | |
| phone_number | text | Yes | PII |
| occupation | text | Yes | |
| education | text | Yes | |
| socio_economic | text | Yes | Lower / Middle / Upper |
| urban_rural | text | Yes | Urban / Rural |
| migrant | boolean | Yes | |
| previous_convictions | int | Yes | Default: 0 |
| status | text | Yes | Suspect / Arrested / etc. |

### Table: `victims`

| Column | Catalyst Type | Nullable | Notes |
|--------|--------------|----------|-------|
| full_name | text | No | |
| gender | text | Yes | |
| age | int | Yes | |
| contact_number | text | Yes | PII |
| address | text | Yes | |
| district | text | Yes | |
| occupation | text | Yes | |
| statement_summary | text | Yes | |

### Table: `cases`

| Column | Catalyst Type | Nullable | Notes |
|--------|--------------|----------|-------|
| fir_number | text | No | Unique |
| title | text | No | |
| description | text | Yes | |
| crime_type | text | No | 17 types |
| crime_head | text | Yes | |
| modus_operandi | text | Yes | |
| status | text | No | Open / Under Investigation / Chargesheeted / Closed / Cold |
| severity | text | Yes | Low / Medium / High / Critical |
| district | text | No | |
| station | text | Yes | |
| location_name | text | Yes | |
| latitude | double | Yes | |
| longitude | double | Yes | |
| is_financial | boolean | Yes | |
| loss_amount | double | Yes | |
| occurrence_date | datetime | Yes | |
| reported_date | datetime | Yes | |

### Table: `case_accused`

| Column | Catalyst Type | Nullable | Notes |
|--------|--------------|----------|-------|
| case_id | bigint | No | Ref → cases.ROWID |
| accused_id | bigint | No | Ref → accused.ROWID |
| role_in_crime | text | Yes | Main / Accomplice / Financier / Handler |

### Table: `case_victim`

| Column | Catalyst Type | Nullable | Notes |
|--------|--------------|----------|-------|
| case_id | bigint | No | Ref → cases.ROWID |
| victim_id | bigint | No | Ref → victims.ROWID |

### Table: `associations`

| Column | Catalyst Type | Nullable | Notes |
|--------|--------------|----------|-------|
| source_accused_id | bigint | No | Ref → accused.ROWID |
| target_accused_id | bigint | No | Ref → accused.ROWID |
| relationship_type | text | Yes | Gang / Associate / Financial |
| gang_name | text | Yes | |
| strength | double | Yes | 0.0 – 1.0 |

### Table: `investigations`

| Column | Catalyst Type | Nullable | Notes |
|--------|--------------|----------|-------|
| case_id | bigint | No | Ref → cases.ROWID (unique) |
| officer_id | bigint | Yes | Ref → officers.ROWID |
| summary | text | Yes | |
| leads_details | text | Yes | |
| status | text | Yes | |
| progress | int | Yes | 0–100 |
| current_stage | text | Yes | 12-stage workflow |

### Table: `timeline_events`

| Column | Catalyst Type | Nullable | Notes |
|--------|--------------|----------|-------|
| case_id | bigint | No | Ref → cases.ROWID |
| event_title | text | No | |
| description | text | Yes | |
| event_type | text | Yes | |
| event_timestamp | datetime | Yes | |

### Table: `financial_accounts`

| Column | Catalyst Type | Nullable | Notes |
|--------|--------------|----------|-------|
| account_number | text | No | |
| holder_name | text | Yes | |
| bank | text | Yes | |
| account_type | text | Yes | Savings / Current / Wallet / Crypto |
| accused_id | bigint | Yes | Ref → accused.ROWID |
| is_suspicious | boolean | Yes | |

### Table: `transactions`

| Column | Catalyst Type | Nullable | Notes |
|--------|--------------|----------|-------|
| from_account_id | bigint | No | Ref → financial_accounts.ROWID |
| to_account_id | bigint | No | Ref → financial_accounts.ROWID |
| amount | double | No | |
| currency | text | Yes | Default: INR |
| channel | text | Yes | UPI / NEFT / IMPS / Crypto |
| case_id | bigint | Yes | Ref → cases.ROWID |
| flagged | boolean | Yes | |
| txn_timestamp | datetime | Yes | |

### Table: `crime_patterns`

| Column | Catalyst Type | Nullable | Notes |
|--------|--------------|----------|-------|
| pattern_name | text | No | |
| description | text | Yes | |
| crime_type | text | Yes | |
| district | text | Yes | |
| temporal_signature | text | Yes | |
| modus_operandi_tags | text | Yes | |
| hotspot_radius_meters | int | Yes | |
| case_count | int | Yes | |

### Table: `predictions`

| Column | Catalyst Type | Nullable | Notes |
|--------|--------------|----------|-------|
| target_area | text | No | |
| crime_type | text | No | |
| probability | double | No | |
| risk_level | text | Yes | Low / Medium / High / Critical |
| forecast_window_start | datetime | Yes | |
| forecast_window_end | datetime | Yes | |
| contributing_factors | text | Yes | |

### Table: `behavior_profiles`

| Column | Catalyst Type | Nullable | Notes |
|--------|--------------|----------|-------|
| accused_id | bigint | No | Ref → accused.ROWID (unique) |
| risk_score | double | Yes | 0–100 |
| risk_band | text | Yes | Low / Medium / High / Critical |
| is_habitual | boolean | Yes | |
| behavioral_traits | text | Yes | |
| propensity_tags | text | Yes | |
| modus_operandi | text | Yes | |

### Table: `alerts`

| Column | Catalyst Type | Nullable | Notes |
|--------|--------------|----------|-------|
| title | text | No | |
| message | text | Yes | |
| severity | text | Yes | |
| alert_type | text | Yes | |
| district | text | Yes | |
| is_read | boolean | Yes | |
| resolved | boolean | Yes | |

### Table: `conversations`

| Column | Catalyst Type | Nullable | Notes |
|--------|--------------|----------|-------|
| title | text | Yes | |
| user_id | bigint | Yes | Ref → users.ROWID |
| case_id | bigint | Yes | Ref → cases.ROWID |
| language | text | Yes | en / kn |

### Table: `messages`

| Column | Catalyst Type | Nullable | Notes |
|--------|--------------|----------|-------|
| conversation_id | bigint | No | Ref → conversations.ROWID |
| role | text | No | user / assistant |
| content | text | No | |
| language | text | Yes | |
| sql_text | text | Yes | |
| evidence_json | text | Yes | JSON string |
| grounding_json | text | Yes | JSON string |
| reasoning_json | text | Yes | JSON string |
| intent | text | Yes | |

### Table: `case_notes`

| Column | Catalyst Type | Nullable | Notes |
|--------|--------------|----------|-------|
| case_id | bigint | No | Ref → cases.ROWID |
| author_name | text | Yes | |
| author_role | text | Yes | |
| content | text | No | |
| pinned | boolean | Yes | |

### Table: `evidence_documents`

| Column | Catalyst Type | Nullable | Notes |
|--------|--------------|----------|-------|
| case_id | bigint | No | Ref → cases.ROWID |
| category | text | Yes | |
| filename | text | No | Catalyst File Store file ID |
| original_name | text | Yes | |
| mime | text | Yes | |
| size | bigint | Yes | |
| uploaded_by | text | Yes | |
| ai_summary | text | Yes | |
| remarks | text | Yes | |

### Table: `witnesses`

| Column | Catalyst Type | Nullable | Notes |
|--------|--------------|----------|-------|
| case_id | bigint | No | Ref → cases.ROWID |
| name | text | No | |
| contact | text | Yes | |
| statement | text | Yes | |
| reliability | text | Yes | |
| document_path | text | Yes | Catalyst File Store file ID |
| document_name | text | Yes | |

### Table: `audit_logs`

| Column | Catalyst Type | Nullable | Notes |
|--------|--------------|----------|-------|
| user_id | text | Yes | |
| user_name | text | Yes | |
| role | text | Yes | |
| action | text | Yes | HTTP method |
| path | text | Yes | Request path |
| resource | text | Yes | Module name |
| status_code | int | Yes | |
| pii_accessed | boolean | Yes | |
| action_type | text | Yes | view/create/update/delete/login/... |
| detail | text | Yes | |
| ip_address | text | Yes | |
| user_agent | text | Yes | |
| session_id | text | Yes | |
| district | text | Yes | |
| prev_value | text | Yes | |
| new_value | text | Yes | |
| log_timestamp | datetime | Yes | Explicit timestamp (supplement CREATEDTIME) |

### Table: `stage_approvals`

| Column | Catalyst Type | Nullable | Notes |
|--------|--------------|----------|-------|
| case_id | bigint | No | Ref → cases.ROWID |
| stage | text | No | |
| action | text | Yes | approve / reject / pending |
| requested_by | text | Yes | |
| requested_role | text | Yes | |
| approved_by | text | Yes | |
| approved_role | text | Yes | |
| comments | text | Yes | |

### Table: `access_requests`

| Column | Catalyst Type | Nullable | Notes |
|--------|--------------|----------|-------|
| case_id | bigint | No | Ref → cases.ROWID |
| requested_by | text | Yes | |
| requested_role | text | Yes | |
| reason | text | Yes | |
| status | text | Yes | pending / approved / rejected |
| reviewed_by | text | Yes | |

---

## Appendix B — ZCQL Limitations & Workarounds

### Limitation 1: No GROUP BY with aggregates

**Current SQLAlchemy:**
```python
db.query(Case.crime_type, func.count(Case.id)).group_by(Case.crime_type).all()
```

**ZCQL workaround:**
```python
rows = store.query("SELECT crime_type FROM cases")
from collections import Counter
result = Counter(r["cases.crime_type"] for r in rows)
# → {"Theft": 45, "Robbery": 23, ...}
```

### Limitation 2: No JOINs

**Current SQLAlchemy:**
```python
db.query(Accused, BehaviorProfile).join(BehaviorProfile, BehaviorProfile.accused_id == Accused.id).all()
```

**ZCQL workaround:**
```python
accused = store.query("SELECT * FROM accused")
profiles = store.query("SELECT * FROM behavior_profiles")
profile_map = {p["behavior_profiles.accused_id"]: p for p in profiles}
merged = [
    {**a, **profile_map.get(a["accused.ROWID"], {})}
    for a in accused
]
```

### Limitation 3: No date functions

**Current SQLAlchemy:**
```python
db.query(func.strftime("%Y-%m", Case.occurrence_date), func.count(Case.id))
  .group_by(func.strftime("%Y-%m", Case.occurrence_date)).all()
```

**ZCQL workaround:**
```python
rows = store.query("SELECT occurrence_date FROM cases")
from collections import Counter
trend = Counter(r["cases.occurrence_date"][:7] for r in rows if r["cases.occurrence_date"])
# → {"2025-01": 12, "2025-02": 15, ...}
```

### Limitation 4: No SUM / AVG

**Current SQLAlchemy:**
```python
db.query(func.sum(Case.loss_amount)).filter(Case.is_financial.is_(True)).scalar()
```

**ZCQL workaround:**
```python
rows = store.query("SELECT loss_amount FROM cases WHERE is_financial = true")
total_loss = sum(float(r["cases.loss_amount"] or 0) for r in rows)
```

### Performance Note

Fetching all rows for Python-side aggregation is fine for our data scale (~260 cases, ~180 accused). For production with thousands of rows, consider:
- **Catalyst Cache**: Cache aggregation results with a TTL
- **Materialized aggregation table**: A scheduled function that pre-computes daily aggregates
- **Pagination**: For list endpoints, always use LIMIT

---

## Appendix C — GLM Prompt Design

### System Prompt for Query Generation

```
You are a ZCQL query generator for a crime intelligence database.

DATABASE SCHEMA:
(full schema from Appendix A inserted here)

ZCQL RULES:
1. Only write SELECT statements — never INSERT, UPDATE, DELETE, DROP
2. No GROUP BY, no aggregate functions (COUNT, SUM, AVG)
3. No JOINs — query only one table at a time
4. Supported operators: =, !=, >, <, >=, <=, LIKE, IN, IS NULL, IS NOT NULL
5. Supported clauses: WHERE, AND, OR, ORDER BY, LIMIT
6. String values are case-sensitive
7. Date format: 'YYYY-MM-DD' or 'YYYY-MM-DD HH:mm:ss'
8. Use ROWID for primary key references

VALID CRIME_TYPES (exact strings):
Theft, Burglary, Robbery, Vehicle Theft, Chain Snatching, Assault, Murder,
Kidnapping, Domestic Violence, Cyber Fraud, Bank Fraud, UPI Scam, Extortion,
Drug Trafficking, Human Trafficking, Rioting

VALID DISTRICTS (exact strings):
Bengaluru City, Bengaluru Rural, Mysuru, Mangaluru, Hubballi-Dharwad, Belagavi,
Kalaburagi, Ballari, Vijayapura, Davanagere, Shivamogga, Tumakuru, Udupi,
Hassan, Mandya

INTENTS (classify into one):
count_cases, list_cases, top_crime_types, crime_trend, hotspots, case_lookup,
accused_lookup, repeat_offenders, financial, network, forecast, socio, help, unknown

RESPONSE FORMAT (strict JSON):
{
  "intent": "<intent>",
  "tables": ["<table1>", "<table2>"],
  "queries": [
    {"table": "<table>", "zcql": "SELECT ..."}
  ],
  "aggregation": "<none|count|group|sum>",
  "group_by_column": "<column or null>",
  "reasoning": "<one sentence explaining your query strategy>"
}

EXAMPLES:

Q: "How many cyber fraud cases in Bengaluru?"
A: {"intent":"count_cases","tables":["cases"],"queries":[{"table":"cases","zcql":"SELECT ROWID FROM cases WHERE crime_type = 'Cyber Fraud' AND district = 'Bengaluru City'"}],"aggregation":"count","group_by_column":null,"reasoning":"Count cases filtered by crime type and district"}

Q: "Show crime trend over time"
A: {"intent":"crime_trend","tables":["cases"],"queries":[{"table":"cases","zcql":"SELECT occurrence_date FROM cases ORDER BY occurrence_date"}],"aggregation":"group","group_by_column":"occurrence_date","reasoning":"Fetch all dates to group by month in application layer"}

Q: "Top repeat offenders"
A: {"intent":"repeat_offenders","tables":["accused","behavior_profiles"],"queries":[{"table":"behavior_profiles","zcql":"SELECT * FROM behavior_profiles ORDER BY risk_score DESC LIMIT 10"},{"table":"accused","zcql":"SELECT * FROM accused"}],"aggregation":"none","group_by_column":null,"reasoning":"Get top-risk profiles then join with accused details in application layer"}
```

### System Prompt for Answer Synthesis

```
You are a police crime-intelligence analyst for Karnataka State Police.

Given the user's question and the structured data findings below, compose a
professional, concise answer.

RULES:
1. Only state facts supported by the data — never invent or assume
2. Use specific numbers from the data
3. If the language is Kannada (kn), respond entirely in Kannada script
4. If the language is English (en), respond in professional English
5. Keep the answer under 3 sentences for simple queries, under 6 for complex ones
6. Reference districts, crime types, and names exactly as they appear in the data
```

---

## Execution Timeline

```
Week 1:
  Day 1-2: Phase 0 (you — project init, GLM enable)
           Phase 1 (you — create 24 tables)
  Day 3:   Phase 2 (Claude — data access layer)
           Phase 3 (Claude — Catalyst function adapter)
  Day 4-5: Phase 5 (Claude — router migration, biggest phase)

Week 2:
  Day 6:   Phase 4 (Claude — GLM integration)
           Phase 8 (Claude writes script, you run migration)
  Day 7:   Phase 6 (you — train Prophet; Claude — integration code)
           Phase 7 (Claude — file storage)
  Day 8:   Phase 9 (both — deploy + validate)
```

**Total estimated effort**: ~8 working days (3 days manual setup + 5 days code)
