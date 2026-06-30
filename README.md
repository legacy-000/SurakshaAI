# SURAKSHA AI 
### System for Unified Research, Analytics and Knowledge-based Support for Holistic Analysis

SURAKSHA AI is an enterprise, AI-powered Crime Intelligence Platform designed specifically for the **Karnataka Police**. The platform empowers command center analysts and precinct investigators to correlate criminal records, perform geospatial hotspot mapping, trace suspect-case association networks, run predictive forecasting analytics, and query documentation using a Retrieval-Augmented Generation (RAG) agent.

---

## 🏛️ Architecture Overview

The system implements a strictly **Layered Modular Architecture** ensuring clear separation of concerns, high maintainability, and clean dependency boundaries. 

No layer may skip another layer. The propagation flow is strictly defined as:

```
┌────────────────────────────────────────────────────────┐
│             Presentation Layer (Next.js Front)         │
└───────────────────────────┬────────────────────────────┘
                            │ (REST HTTP / WebSocket)
                            ▼
┌────────────────────────────────────────────────────────┐
│            Controller Layer (FastAPI Router)           │
└───────────────────────────┬────────────────────────────┘
                            │ (Request validation / Response structuring)
                            ▼
┌────────────────────────────────────────────────────────┐
│             Service Layer (Business Logic)             │
└───────────────────────────┬────────────────────────────┘
                            │ (Orchestration / Transaction coordination)
                            ▼
┌────────────────────────────────────────────────────────┐
│            AI Layer (LangChain / Agents / Graphs)      │
└───────────────────────────┬────────────────────────────┘
                            │ (Context mapping / AI logic queries)
                            ▼
┌────────────────────────────────────────────────────────┐
│           Repository Layer (SQLAlchemy CRUD)           │
└───────────────────────────┬────────────────────────────┘
                            │ (Database-agnostic query interface)
                            ▼
┌────────────────────────────────────────────────────────┐
│           Database Layer (PostgreSQL + PostGIS)        │
└────────────────────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

| Layer | Technology / Tool | Purpose |
|---|---|---|
| **Frontend** | Next.js (App Router), React, TypeScript | Core framework & typing security |
| | TailwindCSS, ShadCN UI | Styling, responsive UI design & web aesthetics |
| | Framer Motion | Smooth UI micro-animations and transitions |
| | React Flow | Suspect-Case association link network maps |
| | Leaflet | Open-source geospatial mapping & coordinate rendering |
| | Recharts | Crime trend dashboards & bar/line visualization |
| | Axios | REST API service client with token interceptors |
| **Backend** | FastAPI, Python 3.10 | High performance, async REST API server |
| | SQLAlchemy | Object Relational Mapper (ORM) |
| | Pydantic | Schema data verification and JSON serialization |
| | PyJWT, bcrypt | Police officer authentication credentials encryption |
| | Uvicorn | High speed ASGI server runner |
| **AI Engine** | LangChain, LangGraph | LLM agents workflow state orchestration |
| | FAISS | Vector database for localized document embeddings |
| | Sentence Transformers | Local semantic vector generation (e.g. `all-MiniLM-L6-v2`) |
| | NetworkX | Centrality scoring and cluster association analysis |
| | Redis | Cache storage, lock coordinator, and agent state store |
| **Database** | PostgreSQL | Relational transactional database |
| | PostGIS | Geographic/spatial indices (beats, station boundaries) |
| | Redis | Speed cache and memory storage |

---

## 📂 Folder Explanation

```
SURAKSHA-AI/
├── ai_engine/               # AI Layer: Agent structures, workflows and vector searches
│   ├── agents/              # LangChain execution agents (e.g. ChatAgent)
│   ├── workflow/            # LangGraph state machine orchestrators
│   ├── rag/                 # Retrieval-Augmented Generation configurations
│   ├── embeddings/          # Sentence Transformers vector models
│   ├── graph/               # NetworkX suspect association algorithms
│   ├── forecasting/         # Crime prediction metrics models
│   ├── profiling/           # Offender MO behavioral profiling
│   ├── sql_generator/       # Natural Language to SQL compiler interfaces
│   ├── prompts/             # Prompt text templates
│   └── explainability/      # SHAP / justification models
│
├── backend/                 # API Server Layer
│   ├── configuration/       # DB engines and system config
│   ├── controllers/         # Controller Layer: Request mapping & standard responses
│   ├── services/            # Service Layer: Business transactions
│   ├── repositories/        # Repository Layer: SQLAlchemy data operations
│   ├── models/              # Declarative database entities
│   ├── schemas/             # Pydantic schemas (e.g. APIResponse)
│   ├── routes/              # FastAPI router mappings (/api/chat, /api/auth)
│   ├── middleware/          # Request tracing and logging middleware
│   ├── authentication/      # JWT crypt tokens handlers
│   └── utilities/           # Module loggers (ChatLogger, AnalyticsLogger, etc.)
│
├── database/                # Relational Schema Design
│   ├── schemas/             # Geographic metadata and PostGIS structures
│   ├── sql/                 # Schema outline scripts
│   ├── migrations/          # Alembic database revision history
│   ├── seed/                # Mock seeding scripts for testing
│   └── backups/             # Database backups folder
│
├── frontend/                # Next.js Front App
│   ├── app/                 # Next.js App Router (layout, pages)
│   ├── pages/               # Pages Router fallback tracking
│   ├── layouts/             # Dashboard layouts
│   ├── components/          # Reusable React UI blocks (cards, charts, maps, graph)
│   ├── services/            # Axios API endpoint connectors
│   ├── hooks/               # Custom hooks (e.g. useAuth)
│   ├── context/             # Global Auth providers
│   ├── models/              # TypeScript interface schemas
│   ├── utils/               # Render helpers
│   ├── assets/              # Raw design assets (logos, icons)
│   └── public/              # Served static files (favicons)
│
├── docs/                    # Architecture and API specs
├── docker/                  # Backend/Frontend Docker container builds
├── reports/                 # Dynamic PDF output templates
├── tests/                   # Test suite (frontend, backend, AI)
└── logs/                    # Rotating log files (chat.log, prediction.log)
```

---

## 🚀 Installation & Running

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL + PostGIS (if running outside Docker)

### Environment Configuration
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Populate the required LLM API keys and database credentials in `.env`.

### Running with Docker (Recommended)
Compile and launch all containers (Database, Redis, Backend, Frontend) concurrently:
```bash
make docker-up
```
Stop services:
```bash
make docker-down
```

### Running Locally (Manual)

#### 1. Running the FastAPI Backend
1. Create a virtual environment and install packages:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Start development server using Makefile:
   ```bash
   make run-backend
   ```
   *The backend will be available at `http://localhost:8000`. Swagger API docs can be accessed at `http://localhost:8000/docs`.*

#### 2. Running the Next.js Frontend
1. Install node dependencies:
   ```bash
   npm install
   ```
2. Launch dev portal:
   ```bash
   make run-frontend
   ```
   *The frontend will run at `http://localhost:3000`.*

---

## 🌿 Git Strategy (Git Flow)

This project strictly adheres to **Git Flow** branching models:

* **`main`**: Production release state. Only stable, signed-off versions exist here.
* **`develop`**: Primary integration branch. All feature branches merge into develop first.
* **`feature/chat`**: Implementation of RAG-powered chatbot conversations.
* **`feature/network`**: Development of React Flow & NetworkX suspect association maps.
* **`feature/analytics`**: Implementation of predictive hotspot and forecasting graphs.
* **`feature/maps`**: Construction of Leaflet GIS and geographic precinct mapping layers.
* **`feature/reports`**: Automated creation of precinct PDF reports.

### Workflow:
1. Branch off `develop`: `git checkout -b feature/analytics develop`
2. Implement feature tasks adhering to Coding Standards.
3. Submit a Pull Request (PR) to merge back to `develop` for integration testing.

---

## 📝 Coding Standards

To ensure code readability and type safety across our full-stack engineering team, strictly follow the case convention matrix below:

| Type | Style | Example | Language |
|---|---|---|---|
| **Class Naming** | `PascalCase` | `class CrimePredictor:` | Python / TS |
| **Variables** | `camelCase` | `const activeAlerts = ...` | TypeScript |
| **Constants** | `UPPER_CASE` | `KARNATAKA_SRID = 4326` | Python / TS |
| **Functions** | `camelCase` | `function parseTimelineEvents()` | TypeScript |
| **API Endpoints** | `snake_case` | `/api/chat/session_id` | HTTP REST |

---

## 🤝 Contribution Guide

1. **Fork the repository** and clone features branches.
2. **Setup pre-commit hooks** and verify styles using Makefile checkers:
   ```bash
   make lint
   ```
3. **Write tests** under `tests/` directory verifying components and service layers. Run tests locally:
   ```bash
   make test
   ```
4. **Open a Pull Request** describing structural changes, linking relevant JIRA/Issue tickets.
