# SURAKSHA AI - ZOHO CATALYST VERSION
## System for Unified Research, Analytics and Knowledge-based Support for Holistic Analysis

SURAKSHA AI is an enterprise, AI-powered Crime Intelligence Platform designed for the **Karnataka Police**, now fully migrated to **Zoho Catalyst** for the Hackathon submission.

---

## 🏗️ Catalyst Architecture Overview

The system has been re-architected to leverage Zoho Catalyst services exclusively, replacing all third-party dependencies with Catalyst-native equivalents.

| Layer | Original (Local/Docker) | **Catalyst Version** | Service |
|---|---|---|---|
| **Frontend** | Next.js dev server | **Catalyst Web Client Hosting** (`zcil`) | Static site hosting |
| **Backend API** | FastAPI + Uvicorn | **Catalyst Serverless Functions** (`zcrun`) | Python 3.12 |
| **Database** | PostgreSQL + PostGIS | **Catalyst Data Store** | NoSQL with spatial + full-text |
| **Cache** | Redis container | **Catalyst Cache** | Key-value segments |
| **AI/RAG** | LangChain + OpenAI + FAISS | **Catalyst QuickML** | LLM + RAG knowledge base |
| **OCR/Vision** | External APIs | **Catalyst Zia** | OCR, barcode, object detection |
| **Auth** | JWT/Bcrypt | **Catalyst Authentication** | Zoho Auth |
| **Storage** | Local filesystem | **Catalyst Stratus** | Object storage |
| **Deployment** | Docker Compose | **Catalyst CLI** (`zcil` + `zcrun`) | Managed platform |

---

## 📂 Updated File Structure

### Key New Files (Catalyst-Specific)
```
SurakshaAI/
├── catalyst.json                              ← NEW: Root project manifest
├──
├── backend/
│   ├── catalyst_function_config.json          ← NEW: Serverless function config
│   ├── api_gateway.py                         ← NEW: API Gateway router
│   ├── configuration/
│   │   ├── database.py                        ← UPDATED: Catalyst Data Store
│   │   └── cache_config.py                    ← NEW: Catalyst Cache
│   ├── models/
│   │   └── datastore_models.py                ← NEW: NoSQL models (replaces SQLAlchemy)
│   └── requirements.txt                       ← UPDATED: Removed Postgres/Redis/FAISS/LangChain
│
├── ai_engine/
│   ├── quickml_adapter.py                     ← NEW: QuickML LLM/RAG adapter
│   ├── zia_adapter.py                         ← NEW: Zia OCR/Vision adapter
│   ├── agents/chat_agent.py                   ← UPDATED: Uses QuickML
│   ├── rag/retriever.py                       ← UPDATED: Uses QuickML RAG
│   └── embeddings/generator.py              ← UPDATED: Ready for QuickML
│
├── frontend/
│   ├── catalyst.json                          ← NEW: Web Client Hosting config
│   ├── next.config.mjs                        ← UPDATED: Static export
│   ├── services/api.ts                      ← UPDATED: Catalyst API paths
│   ├── context/auth-context.tsx              ← UPDATED: Catalyst Auth
│   └── package.json                           ← UPDATED: Deploy scripts
│
├── Makefile                                   ← UPDATED: Catalyst CLI commands
├── pyproject.toml                             ← UPDATED: Catalyst SDK deps
└── .env.example                               ← UPDATED: Catalyst variables
```

### Removed/Archived (No Longer Needed)
- `docker/` directory → **Removed** (Catalyst manages runtime)
- `docker-compose.yml` → **Removed**
- `database/migrations/` → **Archived** (Data Store is NoSQL)
- Old SQLAlchemy models → **Replaced** by `datastore_models.py`
- LangChain/FAISS dependencies → **Removed** (use QuickML)
- Redis dependencies → **Removed** (use Catalyst Cache)
- PostgreSQL dependencies → **Removed** (use Data Store)

---

## 🚀 Deployment Commands

### Prerequisites
- Install Zoho Catalyst CLI (`npm install -g zc-cli` or equivalent)
- Login: `zcil login`

### Deploy Backend (Serverless Functions)
```bash
make deploy-backend
# Or manually:
# zcrun deploy backend/
```

### Deploy Frontend (Web Client Hosting)
```bash
make deploy-frontend
# Or manually:
# cd frontend && zcil deploy webclient
```

### Deploy Everything
```bash
make deploy
```

### Check Logs
```bash
make catalyst-logs
# Or: zcrun logs
```

---

## 🔧 Local Development (Without Catalyst)

For local testing without Catalyst SDK:

```bash
# Backend (FastAPI local)
make run-backend

# Frontend (Next.js dev server)
make run-frontend
```

---

## 📊 Service Mapping (Hackathon Compliance)

| Capability | Required Catalyst Service | Used In |
|---|---|---|
| Serverless Backend | **Catalyst Serverless** | `backend/` deployed via `zcrun` |
| Frontend Hosting | **Catalyst Web Client Hosting** | `frontend/` deployed via `zcil` |
| Database | **Catalyst Data Store** | `backend/configuration/database.py` |
| Cache | **Catalyst Cache** | `backend/configuration/cache_config.py` |
| AI/LLM/RAG | **Catalyst QuickML** | `ai_engine/quickml_adapter.py` |
| OCR/Vision | **Catalyst Zia** | `ai_engine/zia_adapter.py` |
| Authentication | **Catalyst Authentication** | `frontend/context/auth-context.tsx` |
| API Gateway | **Catalyst API Gateway** | `backend/api_gateway.py` |
| Storage | **Catalyst Stratus** | Configured in `catalyst.json` |
| Cron Jobs | **Catalyst Cron** | Configured in `catalyst.json` |

---

## ⚠️ Notes for Hackathon Submission

1. **No Docker**: All services are deployed via Catalyst CLI, not Docker containers.
2. **No Third-Party LLMs**: All AI uses Catalyst QuickML (not OpenAI/Anthropic).
3. **No Local Database**: All data uses Catalyst Data Store (not PostgreSQL).
4. **Static Frontend**: Next.js is built with `output: 'export'` for static deployment.
5. **Environment Variables**: Use `.env.example` as reference; populate with your Catalyst project credentials.

---

## Current Status (semifinal-2)

### Deployed
- **Backend**: Catalyst serverless function at `suraksha_ai` endpoint
- **Analytics Cron**: Daily cron job to refresh stats, trends, hotspots, forecasts
- **Frontend**: React dashboard hosted on Catalyst Web Client Hosting

### Analytics Dashboard — What Works
- **Overview tab**: Summary stats load and display
- **Trends tab**: Crime trend charts render from aggregated daily counts
- **Hotspots tab**: Geographic hotspot clusters shown on map
- **Socio-Demographics tab ("All Types")**: Pie charts and bar charts show distribution of victims, accused, complainants across age/gender/occupation correctly
- **Cache busting**: `_v` version parameter forces fresh API data after deploy
- **Debug overlay**: Shows record counts from the API response (victims, accused, complainants, CaseMaster rows, map entries)

### Known Issues

1. **Individual Crime Type Tabs show 0 records on Socio-Demographics**
   - The "All Types" tab correctly shows data, but clicking specific crime type tabs (e.g., Murder, Theft) shows zero records
   - Root cause unknown — likely `CaseMasterID` foreign key in Victim/Accused tables does not match `ROWID` in CaseMaster, or crime_type naming differs between tables
   - Debug output includes `uniq_ids`, `hits`, `miss`, `cm_keys`, and `v_ids` fields to diagnose the mismatch

2. **ZCQL `CaseMasterID` column returns 0 rows**
   - `SELECT CaseMasterID FROM CaseMaster` returns empty result set (column doesn't exist in that table despite being in schema)
   - Workaround: using `ROWID` (Catalyst internal ID) instead. If Victim/Accused records store the DB-generated ID rather than ROWID, the mapping won't match

3. **No caching layer active**
   - `cache_get`/`cache_set` were never imported into `main_handler.py` — every API call does a full re-fetch from Data Store (~7 queries)
   - The `_cached` wrapper catches `NameError` silently, so caching degrades to no-op without errors

4. **LIMIT clause on all queries**
   - Hardcoded LIMIT 300 on main tables, 500 on reference tables — may miss data beyond those counts

