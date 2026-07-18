# SURAKSHA AI — CATALYST-COMPATIBLE DEPLOYMENT & CLEAN ARCHITECTURE GUIDE

**Purpose:** Make sure everything proposed in the 100% implementation plan actually *deploys* on Zoho Catalyst without runtime/timeout errors, and refactor the code to follow SOLID and GRASP principles so the codebase stays maintainable as it grows.

---

## PART A — HARD CATALYST CONSTRAINTS (Read First)

These are platform facts, not suggestions — violating them is what causes deploy-time or runtime failures.

| Constraint | Value | Why it matters for your modules |
|---|---|---|
| Advanced I/O / Basic I/O function timeout | **30 seconds max** | Prophet forecasting, DBSCAN clustering, fuzzy entity resolution over hundreds of rows, and GLM calls can all individually approach or exceed this inside a single chat/analytics request. |
| Cron / Event function timeout | **15 minutes** | This is where heavy compute belongs — see Part B. |
| Dependencies location | Installed **inside each function's own directory** (`functions/<name>/requirements.txt`), not shared globally | Each of your functions (`suraksha_ai`, `chatbot`) needs its own `requirements.txt` with only what it actually imports — don't assume one global environment. |
| Config file placement | `catalyst-config.json` and `requirements.txt` must sit in the **root of the function's own folder** | A stray `common/requirements.txt` won't be picked up — dependencies belong at `functions/suraksha_ai/requirements.txt`. |
| Concurrency | Functions have a **concurrency limit** — invoking the same function beyond it throws `CONCURRENCY_LIMIT_REACHED` | Don't fire off multiple parallel sub-queries to the *same* function from your Commander's `ThreadPoolExecutor` — fan out to different functions/actions or serialize where needed. |
| Statelessness | Every Advanced I/O invocation is a **fresh, stateless execution** | Anything in a Python dict/list at module level is not guaranteed to survive between invocations — this is exactly why in-memory `InvestigationManager`/`Governance` registries lose data, and why the persistence migration in the 100% plan is non-negotiable, not optional polish. |
| Local testing | Catalyst CLI supports a **functions shell** and **local serve** before deploy | Always run `catalyst serve` / the functions shell locally against a test payload before `catalyst deploy` — never deploy the first run of new code straight to production. |

### A.1 The One Rule That Prevents Most Timeout Errors

**Never run Prophet, DBSCAN, fuzzy entity resolution, or any multi-second computation inside the same request that answers a chat/dashboard call.** Split every heavy module into a **compute phase** (Cron function, runs on a schedule, writes results to Data Store/Cache) and a **serve phase** (Advanced I/O function, just reads the precomputed result). This single change is what keeps you inside the 30-second ceiling regardless of how much data grows.

---

## PART B — REVISED ARCHITECTURE: COMPUTE/SERVE SEPARATION

```
                     ┌─────────────────────────────┐
   Cron Function     │  nightly_analytics_job       │
   (15-min budget)   │  - TrendAnalyzer.compute()   │
                      │  - HotspotDetector.compute() │
                      │  - Forecaster.compute()      │
                      │  - EntityResolver.resolve_all()│
                      │  - IPSScorer.score_all()      │
                      └──────────────┬───────────────┘
                                     │ writes
                                     ▼
                      ┌─────────────────────────────┐
                      │   Data Store (precomputed)   │
                      │   TrendSnapshot, Hotspot,     │
                      │   ForecastResult, IPSScore,   │
                      │   ResolvedEntity              │
                      └──────────────┬───────────────┘
                                     │ reads (fast, <1s)
                                     ▼
   Advanced I/O        ┌─────────────────────────────┐
   Function            │  suraksha_ai/main.py         │
   (30-sec budget)     │  get_trends() -> SELECT only │
                        │  get_hotspots() -> SELECT only│
                        └─────────────────────────────┘
```

**What stays synchronous (safe within 30s):**
- Chat/NL query (single GLM call + 1-4 ZCQL round-trips) — already fits comfortably.
- RBAC checks, audit logging, CRUD on Investigation/Comms — all fast Data Store operations.
- Reading precomputed trend/hotspot/forecast/IPS results — just a `SELECT`.

**What moves to Cron (needs the 15-min budget):**
- Prophet/ARIMA forecasting
- DBSCAN hotspot clustering
- Entity resolution across the full Accused table
- IPS scoring across all offenders
- MO clustering (KMeans over embeddings)
- Financial structuring detection across all transactions
- Community detection for organized-crime groups

### B.1 Cron Function Setup

```bash
catalyst init  # choose "Cron Function", Python 3.9
```
```python
# functions/analytics_cron/main.py
def handler(event, context):
    app = initialize()
    TrendAnalyzer(app).compute_and_store()
    HotspotDetector(app).compute_and_store()
    Forecaster(app).compute_and_store()
    EntityResolver(app).resolve_all_and_store()
    IPSScorer(app).score_all_and_store()
    context.close()
```
Schedule it (nightly, or hourly if your dataset is small enough that a run comfortably finishes well inside 15 minutes):
```bash
catalyst functions:cron:schedule analytics_cron --cron "0 2 * * *"
```

### B.2 Fallback for On-Demand Freshness

If a user needs a forecast recomputed right now rather than waiting for the nightly run, expose a separate **manual-trigger Cron/Event function** the frontend can invoke ("Refresh Analytics" button), rather than doing it inline inside a 30-second Advanced I/O call.

---

## PART C — CORRECT FUNCTION DIRECTORY STRUCTURE

```
Suraksha_AI/
├── catalyst.json
├── functions/
│   ├── suraksha_ai/                  <- Advanced I/O (serve phase)
│   │   ├── main.py
│   │   ├── catalyst-config.json
│   │   ├── requirements.txt          <- ONLY what suraksha_ai imports
│   │   └── common/                   <- your business logic modules
│   │       ├── chat/
│   │       ├── analytics/
│   │       ├── network/
│   │       ├── offender/
│   │       ├── financial/
│   │       ├── sociology/
│   │       ├── forecast/
│   │       ├── security/
│   │       └── ...
│   ├── analytics_cron/               <- Cron (compute phase)
│   │   ├── main.py
│   │   ├── catalyst-config.json
│   │   └── requirements.txt          <- prophet, scikit-learn, networkx, rapidfuzz live HERE only
│   └── chatbot/                      <- Node function (if kept separate)
│       ├── index.js
│       └── package.json
└── suraksha-dashboard/
    └── ...
```

**Critical detail:** put heavy ML dependencies (`prophet`, `scikit-learn`, `networkx`, `rapidfuzz`) only in `analytics_cron/requirements.txt`, not in `suraksha_ai/requirements.txt`. Your chat-serving function should stay light and fast; only the Cron function needs the heavy libraries, and keeping them separated avoids inflating and slowing down the function that has the tightest timeout.

---

## PART D — PRE-DEPLOY LOCAL VALIDATION (Do This Every Time)

```bash
# 1. Install deps inside the specific function folder
cd functions/suraksha_ai
pip install -r requirements.txt -t .

# 2. Test locally before touching the cloud
catalyst serve
# or, for a single invocation test:
catalyst functions:shell suraksha_ai

# 3. Only once local test passes, deploy that function alone first
catalyst deploy --only functions/suraksha_ai

# 4. Watch logs live to catch runtime errors immediately
catalyst logs --function suraksha_ai --tail
```

Do this **per function**, not just once for the whole project — a change to `analytics_cron` doesn't need you to redeploy `suraksha_ai`, and testing them separately isolates which one breaks.

### D.1 Common Deploy/Runtime Errors and Fixes

| Error | Cause | Fix |
|---|---|---|
| Timeout at 30s | Heavy compute inside Advanced I/O function | Move to Cron per Part B |
| `ModuleNotFoundError` on deploy | Dependency missing from that function's own `requirements.txt` | Add it to the specific function's requirements file, not a shared one |
| `CONCURRENCY_LIMIT_REACHED` | Commander's `ThreadPoolExecutor` firing too many parallel calls at one function | Cap thread pool size; spread calls across distinct actions/functions |
| Data "resets" after redeploy | In-memory dict used for state | Persist to Data Store (see 100% plan Section 6/10) |
| ZCQL parse error | JOIN/subquery/LIKE used | Use multi-step `IN (...)` pattern (see prior guide) |
| Function works locally, fails in cloud | Local Python version mismatch | Confirm Python 3.9 runtime match; test inside `catalyst serve`, not just plain local `python main.py` |
| Cron never fires | Schedule not registered | Confirm with `catalyst functions:cron:list` after deploying |

---

## PART E — SOLID PRINCIPLES APPLIED TO THE CODEBASE

### E.1 Single Responsibility Principle (SRP)

Each class does **one** job. Split what used to be one big handler into layers:

```python
# BAD (violates SRP): one class does routing + validation + ZCQL + formatting
class ChatHandler:
    def handle(self, request):
        # parses request, checks RBAC, builds ZCQL, calls GLM, formats response — all in one method
        ...

# GOOD: each class has exactly one reason to change
class ChatRequestValidator:
    """Only validates incoming payload shape."""
    def validate(self, payload: dict) -> None: ...

class NLQueryPlanner:
    """Only turns natural language into a structured query plan (GLM or regex)."""
    def plan(self, text: str, context: dict) -> QueryPlan: ...

class ZCQLQueryExecutor:
    """Only executes a QueryPlan against the Data Store."""
    def execute(self, plan: QueryPlan) -> list: ...

class ResponseFormatter:
    """Only turns raw rows into a user-facing answer + evidence trail."""
    def format(self, rows: list, plan: QueryPlan) -> dict: ...
```

### E.2 Open/Closed Principle (OCP)

Your Forecaster needs a Prophet-or-ARIMA fallback (flagged as a real deployment risk). Instead of an `if/else` that has to be edited every time you add a new algorithm, use a **Strategy interface** so new forecasting methods can be *added* without modifying existing code:

```python
from abc import ABC, abstractmethod

class ForecastStrategy(ABC):
    @abstractmethod
    def forecast(self, series: dict, periods: int) -> list: ...

class ProphetForecastStrategy(ForecastStrategy):
    def forecast(self, series, periods):
        from prophet import Prophet
        # ... Prophet implementation
        return result

class ARIMAForecastStrategy(ForecastStrategy):
    def forecast(self, series, periods):
        from statsmodels.tsa.arima.model import ARIMA
        # ... ARIMA implementation
        return result

class Forecaster:
    """Closed for modification, open for extension — add a new strategy class,
    never touch this one."""
    def __init__(self, strategy: ForecastStrategy):
        self.strategy = strategy

    def compute(self, series: dict, periods: int = 3) -> list:
        return self.strategy.forecast(series, periods)

# Wiring — try Prophet, fall back to ARIMA automatically
def build_forecaster() -> Forecaster:
    try:
        import prophet  # noqa
        return Forecaster(ProphetForecastStrategy())
    except ImportError:
        return Forecaster(ARIMAForecastStrategy())
```

### E.3 Liskov Substitution Principle (LSP)

Any `ForecastStrategy` implementation must be swappable without breaking the caller — meaning both `ProphetForecastStrategy` and `ARIMAForecastStrategy` must return the **same shape** of result (`[{ds, yhat, yhat_lower, yhat_upper}, ...]`), never a different structure or an exception type the caller doesn't expect. Apply the same discipline to `EntityResolutionStrategy` (fuzzy-match vs. future ML-based resolver) and `TranslationProvider` (Zia vs. any future provider) — same interface contract, interchangeable implementations.

### E.4 Interface Segregation Principle (ISP)

Don't force one fat interface on every consumer. Your RBAC module should expose narrow, role-specific interfaces rather than one giant `SecurityService` god-object:

```python
class PermissionChecker(ABC):
    @abstractmethod
    def can_access(self, user_role: str, action: str, scope: dict) -> bool: ...

class PIIMasker(ABC):
    @abstractmethod
    def mask(self, row: dict, user_role: str) -> dict: ...

class AuditLogger(ABC):
    @abstractmethod
    def log(self, actor: str, action: str, result: str) -> None: ...
```
A module that only needs to check permissions (like the TSE diagnostic handler) depends only on `PermissionChecker`, not on masking or logging concerns it doesn't use.

### E.5 Dependency Inversion Principle (DIP)

High-level modules (your business logic) should not depend on low-level modules (the Catalyst SDK directly) — both should depend on an abstraction. This is also what makes local testing possible without a live Catalyst connection:

```python
class CaseRepository(ABC):
    @abstractmethod
    def find_by_district(self, district: str) -> list: ...

class ZCQLCaseRepository(CaseRepository):
    """Low-level: talks to actual Catalyst ZCQL."""
    def __init__(self, zcql_client):
        self.zcql = zcql_client

    def find_by_district(self, district: str) -> list:
        return self.zcql.execute(f"SELECT * FROM CaseMaster WHERE District = '{district}'")

class InMemoryCaseRepository(CaseRepository):
    """Used only in unit tests — no live Catalyst connection needed."""
    def __init__(self, seed_data: list):
        self.data = seed_data

    def find_by_district(self, district: str) -> list:
        return [r for r in self.data if r['District'] == district]

# Business logic depends on the abstraction, not the concrete Catalyst client
class TrendAnalyzer:
    def __init__(self, case_repo: CaseRepository):
        self.case_repo = case_repo

    def compute_for_district(self, district: str):
        rows = self.case_repo.find_by_district(district)
        # ... pandas logic, unchanged whether rows came from ZCQL or a test fixture
```
This is precisely what lets you write the 300+ unit tests from the 100% plan **without hitting the live Data Store for every test run** — swap in `InMemoryCaseRepository` for tests, `ZCQLCaseRepository` for production.

---

## PART F — GRASP PRINCIPLES APPLIED

| GRASP Principle | Applied Where | How |
|---|---|---|
| **Information Expert** | `CaseRepository` owns all case-row access logic; `RiskScoreCalculator` owns all IPS math | Put behavior on the class that actually holds the data needed to do it — don't let `main.py` reach into raw ZCQL rows and compute scores itself. |
| **Creator** | `InvestigationFactory` creates `Investigation` objects, not `main.py` directly | The class that aggregates/contains an object should be the one that creates it. |
| **Controller** | `main.py`'s `handler()` function is a thin **Controller** — it receives the HTTP request, delegates to the right use-case class, and returns the response. It contains no business logic itself. | Keeps routing separate from logic, so the 72-action dispatch table stays a dispatch table, not a 3,500-line file. |
| **Low Coupling** | `TrendAnalyzer` depends on `CaseRepository` (interface), not on `ZCQLCaseRepository` (concrete) or the raw `zcatalyst_sdk` | Changing how ZCQL is called never forces a change in analytics logic. |
| **High Cohesion** | `common/forecast/`, `common/network/`, `common/financial/` each contain only classes related to that single concern | Matches your existing subdirectory-per-concern structure — keep extending it that way rather than adding cross-cutting logic into `main.py`. |
| **Polymorphism** | `ForecastStrategy`, `EntityResolutionStrategy` — behavior varies by type without `if/else` chains | See Part E.2. |
| **Pure Fabrication** | `CaseRepository`, `EvidenceWrapper`, `ContextManager` are not real-world "crime domain" concepts — they're invented purely to keep the design clean | These don't map to a real-world noun in policing, but exist to satisfy Low Coupling/High Cohesion. |
| **Indirection** | `CaseRepository` sits between business logic and the Catalyst SDK; `ForecastStrategy` sits between `Forecaster` and the actual ML library | Every volatile external dependency (Catalyst SDK calls, ML libraries) is accessed only through an indirection layer, never directly from business logic. |
| **Protected Variations** | The abstraction boundary around Catalyst SDK calls means a future Catalyst SDK version change, or a swap from Prophet to a different forecasting library, only requires changing the concrete implementation class, not every caller | This is the same mechanism as DIP (E.5) viewed from a design-pattern lens. |

---

## PART G — REVISED main.py CONTROLLER PATTERN

Putting it together — `main.py` becomes a thin Controller with dependency injection wiring at startup, not business logic:

```python
# functions/suraksha_ai/main.py
from zcatalyst_sdk import initialize
from common.repositories import ZCQLCaseRepository, ZCQLAccusedRepository
from common.analytics.trend_analyzer import TrendAnalyzer
from common.forecast.forecaster import build_forecaster
from common.security.rbac_middleware import PermissionChecker
from common.security.audit_logger import AuditLogger

def _build_container(app):
    """Composition root — the only place concrete classes are wired to interfaces."""
    zcql = app.zcql()
    return {
        'case_repo': ZCQLCaseRepository(zcql),
        'accused_repo': ZCQLAccusedRepository(zcql),
        'trend_analyzer': TrendAnalyzer(ZCQLCaseRepository(zcql)),
        'forecaster': build_forecaster(),
        'permission_checker': PermissionChecker(),
        'audit_logger': AuditLogger(app.datastore()),
    }

def handler(request):
    app = initialize()
    container = _build_container(app)
    action = request.get_json().get('action')

    # Controller: route only, no logic
    handlers = {
        'get_trends': lambda: container['trend_analyzer'].compute_for_district(
            request.get_json().get('district')
        ),
        'chat_query': lambda: ChatController(container).handle(request.get_json()),
        # ... remaining 70 actions, same pattern
    }

    if action not in handlers:
        return make_response(jsonify({'error': 'unknown action'}), 400)

    if not container['permission_checker'].can_access(request.user_role, action, {}):
        return make_response(jsonify({'error': 'forbidden'}), 403)

    try:
        result = handlers[action]()
        container['audit_logger'].log(request.user_id, action, 'success')
        return make_response(jsonify(result), 200)
    except Exception as e:
        container['audit_logger'].log(request.user_id, action, f'error: {e}')
        return make_response(jsonify({'error': str(e)}), 500)
```

This structure directly fixes two things at once: it's SOLID/GRASP-compliant, **and** it guarantees every path returns a proper response object and catches exceptions — which is exactly the pattern Catalyst's own docs point to for avoiding unhandled-exception timeout errors.

---

## PART H — FINAL DEPLOYMENT CHECKLIST

- [ ] Heavy ML libraries (`prophet`, `scikit-learn`, `networkx`, `rapidfuzz`) only in `analytics_cron/requirements.txt`, never in `suraksha_ai/requirements.txt`
- [ ] All Prophet/DBSCAN/entity-resolution/IPS-scoring compute moved to Cron functions, Advanced I/O only reads precomputed results
- [ ] Every function has its own `catalyst-config.json` and `requirements.txt` at its own folder root
- [ ] No shared in-memory state anywhere — everything persisted to Data Store or Cache
- [ ] `main.py` is a thin Controller — no business logic inline in the handler
- [ ] Every external dependency (Catalyst SDK, ML libraries, Zia/Stratus clients) accessed only through an interface/abstraction, never called directly from business logic classes
- [ ] Unit tests run against `InMemoryCaseRepository`-style fakes, not the live Data Store
- [ ] Tested locally via `catalyst serve` / `catalyst functions:shell` before every deploy
- [ ] Deployed and logged one function at a time (`catalyst deploy --only functions/X`) rather than deploying everything blind
- [ ] Cron schedule confirmed active via `catalyst functions:cron:list` after deploy
- [ ] Every handler branch returns a valid response object and wraps logic in try/except (per Catalyst's own timeout-avoidance guidance)

---

*This guide should be read alongside `Suraksha_AI_100_Percent_Implementation_Plan.md` — that document defines *what* to build; this one defines *how to structure and deploy it* so it doesn't break on Catalyst.*
