# Suraksha AI — Status & Limitations

## Current Status

### Core Infrastructure
- **Runtime**: Python 3.11, Catalyst AdvancedIO (Flask-based)
- **Database**: 26 Catalyst DataStore tables, all populated with seed/sample data
- **Frontend**: React dashboard (deployed via Catalyst Web Client)
- **API Gateway**: Routes `/api/` → function, enables browser access

### What Works (Tested)

| Feature | Status | Details |
|---------|--------|---------|
| Greeting/Identity | ✅ | "hi", "who are you" → proper responses |
| Total case count | ✅ | `SELECT COUNT(ROWID) AS total_cases FROM CaseMaster` → 389 |
| Crime-type queries | ✅ | "Show theft/murder/robbery/assault cases" → two-step lookup: CrimeSubHead → CaseMaster |
| Statistics by type | ✅ | GROUP BY CrimeMinorHeadID → 8 groups |
| All-cases fallback | ✅ | Any unrecognized query returns all cases (safe default) |
| Login | ✅ | Returns full user object with role_name for sidebar nav |
| Navigation | ✅ | HashRouter → all dashboard pages accessible |
| Chat (frontend) | ✅ | text/plain content type avoids CORS preflight |

### What Is Not Working

| Feature | Status | Reason |
|---------|--------|--------|
| NL2SQL model | ❌ **Disabled** | Catalyst GLM generates invalid ZCQL (`CaseMasterID`, JOINs, LIKE, COUNT(*) ) — never produced a single valid query |
| Ad-hoc JOINs | ❌ **ZCQL limitation** | No implicit JOINs; only Catalyst-defined relationships work (none configured for these tables) |

### Recently Added (2026-07-15)

| Feature | How It Works |
|---------|-------------|
| **Location filtering** | `LOCATION_RE` extracts "in/at/for <place>" → `PLACE_DISTRICT_MAP` maps to district name → two-step ZCQL: `SELECT DistrictID FROM District WHERE DistrictName = 'X'` → `SELECT UnitID FROM Unit WHERE DistrictID = Y` → `WHERE PoliceStationID IN (ids)` |
| **Status filtering** | `STATUS_MAP` maps keywords ("active"→"Under Investigation", "closed"→"Closed") → `SELECT CaseStatusID FROM CaseStatusMaster` → `WHERE CaseStatusID = Z` |
| **Temporal filtering** | Regex for "this year", "last year", "2024 cases", "since 2024" → `WHERE CrimeRegisteredDate >= 'YYYY-01-01'` |
| **Combined queries** | Crime type + location + status + temporal all AND-ed together (e.g., "theft cases in Bangalore in 2024") |
| **Karnataka state-level** | `"karnataka"` mapped to `__all__` sentinel → no filter (all data is Karnataka) |
| **GLM tool-calling (ADR-017)** | GLM receives `query_datastore` tool definition with typed params → returns structured tool call → `ToolExecutor` validates params against allow-list → builds valid ZCQL → executes → feeds result back to GLM for composition. `chat_handler.py` tries GLM first, falls back to regex pattern matcher if GLM is unavailable. |
| **Tool executor** | `tool_executor.py` validates table (enum), columns, where conditions (op in `=,!=,>,<,>=,<=,IN`), group_by, order_by, limit. Builds valid ZCQL respecting constraints (no JOIN/LIKE/subquery). Resolves column aliases (`latitude`→`latitide`, `BriefFacts`→`BriedFacts`, `CaseCategoryID`→`CaeCategoryID`). |
| **QuickML REST client** | `quickml_client.py` uses `Zoho-oauthtoken` auth (not `Bearer`), passes `tools`, `tool_choice`, `chat_template_kwargs` directly to the GLM API. Returns both `text` and `tool_calls` from responses. |
| **SchemaRegistry** | `schema_registry.py` — full hardcoded schema map for all 26 tables (column names, types, descriptions). Drift-warns against actual Data Store on init. `generate_tool_def()` builds the `query_datastore` tool dynamically from the schema. `generate_system_prompt()` builds the system prompt with every table/column. `validate_tool_params()` checks column names against per-table schema — returns clear errors for invalid columns. Resolves aliases (`latitude`→`latitide`, `BriefFacts`→`BriedFacts`). |

---

## ZCQL Limitations (Catalyst DataStore)

ZCQL is a restricted SQL dialect. Key constraints:

| Capability | Standard SQL | ZCQL |
|------------|-------------|------|
| JOIN | `JOIN ... ON` | **Not supported** (unless Catalyst relationship defined in console) |
| Subquery | `WHERE x IN (SELECT...)` | **Not supported** |
| LIKE | `WHERE name LIKE '%X%'` | **Not supported** |
| COUNT(*) | `COUNT(*)` | **Not supported** — use `COUNT(ROWID)` |
| Column aliases | `SELECT COUNT(*) AS cnt` | Alias ignored; raw expression name returned |
| Functions | `LOWER()`, `UPPER()`, `YEAR()` | **Not supported** |
| ORDER BY alias | `ORDER BY cnt` | **Not supported** |
| HAVING | `HAVING COUNT(*) > 5` | **Not supported** |
| UNION / CTEs | `UNION`, `WITH` | **Not supported** |

### Workaround Pattern
The current approach avoids all ZCQL limitations by:

1. **Two-step lookup**: Query CrimeSubHead for ID → query CaseMaster with `CrimeMinorHeadID = X`
2. **No JOINs**: Single-table queries only (CaseMaster / CrimeSubHead / Unit)
3. **No LIKE**: Use exact `=` for known values
4. **COUNT(ROWID)**: Instead of `COUNT(*)`
5. **Pattern matching**: Hardcoded regex-to-SQL mapping for common queries

---

## All 26 Tables — Schema & Usage

### Transactional Tables (core data)

| # | Table | Rows | Key Columns | How to Use |
|---|-------|------|-------------|------------|
| 1 | **CaseMaster** | 389 | CrimeNo, CrimeMinorHeadID, PoliceStationID, latitide, longitude, CaseStatusID | Central table. All queries filter/group by its FK columns |
| 2 | **Accused** | 144 | CaseMasterID, AccusedName, AgeYear, GenderID | "who was accused in case X", "repeat offenders" |
| 3 | **ComplainantDetails** | 30 | CaseMasterID, ComplainantName, OccupationID, ReligionID, CasteID | "victim/complainant demographics" |
| 4 | **Victim** | 40 | CaseMasterID, VictimName, AgeYear, GenderID | "victim profiles" |
| 5 | **ArrestSurrender** | 14 | CaseMasterID, ArrestSurrenderDate, PoliceStationID, IOID, CourtID | "arrest records", "surrender details" |
| 6 | **ChargesheetDetails** | 25 | CaseMasterID, csdate, cstype, PolicePersonID | "chargesheet status", "filing timeline" |
| 7 | **ActSectionAssociation** | 20 | CaseMasterID, ActID, SectionID | "which sections applied to a case" |
| 8 | **CrimeHeadActSection** | 9 | CrimeHeadID, ActCode, SectionCode | "which sections for which crime type" |

### Lookup / Master Tables

| # | Table | Rows | Key Columns | How to Use |
|---|-------|------|-------------|------------|
| 9 | **CrimeHead** | 3 | CrimeHeadID, CrimeGroupName | Major crime groups (Property, Violent, etc.) |
| 10 | **CrimeSubHead** | 8 | CrimeSubHeadID, CrimeHeadID, CrimeHeadName | Sub-types: Theft, Murder, Robbery, etc. |
| 11 | **District** | 30 | DistrictID, DistrictName, StateID | Geographic filter |
| 12 | **Unit** | 72 | UnitID, UnitName, DistrictID | Police stations — geographic anchor |
| 13 | **Employee** | ? | EmployeeID, UnitID, RankID, DesignationID | Investigating officers |
| 14 | **CaseStatusMaster** | seed | CaseStatusID, CaseStatusName | "Under Investigation", "Closed", etc. |
| 15 | **CaseCategory** | seed | CaseCategoryID, LookupValue | "Criminal", "Civil" |
| 16 | **GravityOffence** | seed | GravityOffenceID, LookupValue | "Heinous", "Lesser" |
| 17 | **Court** | seed | CourtID, CourtName, DistrictID | Court assignments |
| 18 | **State** | seed | StateID, StateName | State reference |
| 19 | **UnitType** | seed | UnitTypeID, UnitTypeName | "Police Station", "Range HQ", etc. |
| 20 | **Designation** | 5 | DesignationID, DesignationName | "Police Inspector", "Constable" |
| 21 | **Rank** | 5 | RankID, RankName, Hierarchy | Rank hierarchy |
| 22 | **Act** | 5 | ActCode, ActDescription, ShortName | "IPC", "CrPC", "Special Laws" |
| 23 | **Section** | 30 | ActCode, SectionCode, SectionDescription | "302", "376", "420" etc. |
| 24 | **OccupationMaster** | 6 | OccupationID, OccupationName | Complainant occupation |
| 25 | **CasteMaster** | 5 | caste_master_id, caste_master_name | Caste lookup (lowercase naming!) |
| 26 | **ReligionMaster** | 5 | ReligionID, ReligionName | Religion lookup |

---

## Effective Usage of All 26 Tables

Since ZCQL prohibits JOINs, the only way to query across tables is:

### Strategy 1: Two-Step Lookup (currently used)
Query table A → extract FK values → query table B with WHERE on those values.

```
Step 1: SELECT CrimeSubHeadID FROM CrimeSubHead WHERE CrimeHeadName = 'Theft'
Step 2: SELECT ... FROM CaseMaster WHERE CrimeMinorHeadID IN (1)
```

**Applicable to**:
- CaseMaster ↔ CrimeSubHead (crime-type filter) ✅ **implemented**
- CaseMaster ↔ Unit (station filter) — needs exact UnitID
- CaseMaster ↔ District — needs Unit → District relationship (requires Unit query first)
- Employee ↔ Unit/Designation/Rank — two-step lookup
- ComplainantDetails ↔ OccupationMaster/CasteMaster/ReligionMaster — demographic queries

### Strategy 2: Standalone Table Queries
Query a single non-CaseMaster table directly for summary/aggregate.

**Examples**:
- `SELECT COUNT(ROWID) FROM Accused` — total accused count
- `SELECT ArrestSurrenderTypeID, COUNT(ROWID) FROM ArrestSurrender GROUP BY ArrestSurrenderTypeID` — arrest types
- `SELECT cstype, COUNT(ROWID) FROM ChargesheetDetails GROUP BY cstype` — chargesheet types
- `SELECT OccupationName FROM OccupationMaster` — list occupations
- `SELECT ReligionName FROM ReligionMaster` — list religions

### Strategy 3: Client-Side Join
Query multiple tables separately from the frontend and join in JavaScript.

**Flow**:
1. Fetch CrimeSubHead list → display crime types
2. User clicks a type → fetch CaseMaster with that CrimeMinorHeadID
3. Fetch Unit list → display station names
4. Client-side merges data for display

**Prerequisite**: Frontend code changes in `api.ts` and `ChatPage.tsx`

### Strategy 4: Pre-Joined Catalyst Tables (Future)
Define table relationships in the Catalyst Console →
ZCQL supports `Table.column` dot-notation JOINs when relationships are configured.
**Requires**: Catalyst Console access (not available via CLI)

### Strategy 5: Application-Layer Aggregation (Recommended for completeness)
Build a lightweight aggregation layer in the Python function that:

1. Accepts a query intent (not raw SQL)
2. Executes multiple single-table ZCQL queries
3. Joins/aggregates results in Python
4. Returns structured data

**Example implementation** (not yet built):
```
/dashboard endpoint:
  SELECT COUNT(ROWID) FROM CaseMaster → total cases
  SELECT COUNT(ROWID) FROM Accused → total accused
  SELECT CrimeMinorHeadID, COUNT(ROWID) FROM CaseMaster GROUP BY CrimeMinorHeadID → per-type stats
  → Python merges CrimeSubHead names into the response
```

---

## Recommended Next Steps

1. ✅ ~~Location queries~~ — **Done** (two-step Unit/District lookup)
2. ✅ ~~Case status filter~~ — **Done** (two-step CaseStatusMaster lookup)
3. ✅ ~~Temporal queries~~ — **Done** (direct date comparison on CrimeRegisteredDate)
4. **Standalone table queries**: Query non-CaseMaster tables directly — Accused count, Chargesheet details, complainant demographics, etc.
5. **Application-layer aggregation (Strategy 5)**: Build Python endpoint that aggregates across tables (total cases + accused + chargesheet status + per-type stats) for the dashboard overview
6. **Frontend client-side joins (Strategy 3)**: Fetch Unit/District lists in frontend and merge with CaseMaster data for richer display
7. **Accused profiles**: Query Accused → group by name for repeat offender detection
