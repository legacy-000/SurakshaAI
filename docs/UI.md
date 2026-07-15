# SURAKSHA Police FIR System — UI/UX Specification

**Document Version:** 1.0  
**Last Updated:** 2026-07-15  
**Language Support:** English / Kannada (ಕನ್ನಡ)  
**Target Platform:** Web (Responsive Desktop/Tablet)

---

## 1. System Overview & User Roles

### 1.1 User Personas & Authorization Levels

| Role | Title | Access Level | Primary Functions |
|---|---|---|---|
| **Constable** | Police Officer / Patrol | Base | File FIRs, record basic complainant/victim/accused info, view own station cases |
| **Sub-Inspector** | Investigating Officer (IO) | Mid | Full case investigation, evidence entry, arrest records, chargesheet drafts |
| **Inspector** | Station House Officer (SHO) | Mid-High | Station case oversight, approval workflows, report generation |
| **DSP** | District Superintendent | High | District-wide intelligence, trend analysis, network analysis, briefings |
| **Commander** | Intelligence Commander | Highest | Multi-agent orchestration, forecasting, alerts, strategic briefings |
| **Analyst** | Intelligence Analyst | Mid | Case similarity, offender analysis, pattern detection (read-only for most data) |

### 1.2 Global Navigation & Language Controls

All dashboards feature:
- **Top-left logo:** SURAKSHA AI logo + system name
- **Top-center breadcrumb:** Current module > Sub-section
- **Top-right controls:**
  - 🌐 **Language toggle** (English ↔ ಕನ್ನಡ Kannada) — instantly re-renders all UI
  - 👤 **User profile** (name, rank, station, last login)
  - 🔔 **Alert bell** (unread alerts count, quick-view popover)
  - ⚙️ **Settings** (preferences, notifications, keyboard layout)
  - 🚪 **Logout**

---

## 2. Dashboard Suites by Role & Agent Pairing

### Dashboard Architecture Pattern

Each dashboard follows this structure:
```
┌─ Header (Title + Quick Filters + AI Assistant)
├─ Main Content Area (Grid of Cards/Tables/Maps/Charts)
├─ Right Sidebar (Intelligence Drawer or Context)
├─ Kannada Typing Bar (if enabled in settings)
└─ Footer (Audit log link, export options)
```

---

## 3. Phase 1 Dashboards: FIR Lifecycle Management

### 3.1 **Case Registration Dashboard** (Constable / Sub-Inspector)

**Purpose:** File new FIRs and manage immediate case setup.  
**Primary Agent:** Database Intelligence Agent  
**AI Assistant Name:** "**CaseBot**" (ಕೇಸ್‌ಬಾಟ್)

#### Key Screens:

**3.1.1 FIR Registration Form**
- **Sections:**
  1. **Incident Details**
     - Incident from date/time (ಘಟನೆಯ ಆರಂಭ ದಿನಾಂಕ/ಸಮಯ)
     - Incident to date/time
     - Incident location (free-text + GPS coordinates map picker)
     - Brief facts (large textarea with word count, 500–5000 words)
  
  2. **Complainant Information**
     - Full name (ಸಂಪೂರ್ಣ ಹೆಸರು)
     - Age, Gender (m/f/t)
     - Occupation (dropdown from OccupationMaster)
     - Religion (dropdown from ReligionMaster)
     - Caste (dropdown from CasteMaster)
     - Contact number, email
  
  3. **Victim(s)**
     - Repeatable block for multiple victims
     - Name, Age, Gender
     - VictimPolice flag (if victim is police officer)
  
  4. **Accused(s)**
     - Repeatable block for multiple accused
     - Name, Age, Gender, Sorting ID (A1, A2, A3…)
  
  5. **Legal Classification**
     - Crime Category (FIR / UDR / PAR / Zero FIR) — dropdown
     - Gravity Offence (Heinous / Non-Heinous) — dropdown
     - Crime Major Head (crimes against body, property, etc.) — dropdown
     - Crime Minor Head (Murder, Robbery, etc.) — nested dropdown
     - Acts & Sections (multi-select: Act + Section pairs from Act/Section tables)
  
  6. **Approval**
     - Registered by (auto-filled from logged-in user)
     - Police station (auto-filled from user's unit, modifiable by SHO)
     - Date of registration (auto-filled with today's date)
     - **Submit & Generate FIR** button
       - On success: displays Crime No (e.g., "104430006202600001") + Case No
       - Triggers CaseBot: "Would you like to add arrests, victims, or legal sections now?"

- **CaseBot AI Panel** (Right sidebar, collapsible)
  - Conversational prompts:
    - "What is the primary crime?" → suggests crime head/sections
    - "Any weapons involved?" → auto-tags relevant IPC sections
    - "Multiple accused?" → guides multi-accused entry
  - "Confidence checker": flags missing mandatory fields in natural language
  - **Buttons:**
    - "Auto-fill similar case" (retrieves past FIRs with similar facts)
    - "Review sections" (shows IPC sections with brief definitions)
    - "Help" (links to FAQ)

- **Kannada Typing Support:**
  - Toggle "Enable Kannada typing" in settings
  - Floating keyboard bar at bottom with Kannada layout (Phonetic / Typewriter)
  - Highlights active input field
  - Copy/paste support for Kannada text from external sources

---

**3.1.2 Case Status Dashboard (Overview for logged-in case)**

Displays after FIR creation:
- **Card 1:** Case Summary (Crime No, Category, registered date, SHO, IO)
- **Card 2:** Complainant snapshot (name, contact, occupation)
- **Card 3:** Victim count + quick list (expandable)
- **Card 4:** Accused count + quick list (expandable)
- **Card 5:** Legal sections (Act + Sections with definitions on hover)
- **Card 6:** Location map (incident location + arrest locations, if any)
- **Action buttons:** Edit case, Add victim, Add accused, Record arrest, View chargesheet, Generate report

---

### 3.2 **Investigation Workspace** (Sub-Inspector / Inspector)

**Purpose:** Track investigation progress, record arrests, link evidence, plan next steps.  
**Primary Agent:** Investigation Intelligence Agent + Database Intelligence Agent  
**AI Assistant Name:** "**InvestigationAI**" (ತನಿಖೆ-ಎಐ)

#### Key Screens:

**3.2.1 Investigation Timeline & Task Board**

- **Left panel (Timeline):**
  - Vertical timeline of case milestones:
    - ✓ FIR filed (date)
    - ○ Accused arrested (date) — click to expand arrest details
    - ○ Evidence collected (date)
    - ○ Chargesheet prepared (date)
    - ○ Court case opened (date)
  - Add milestone button → modal to log new investigation event

- **Center panel (Investigation Notes):**
  - Rich text editor for investigator notes (with timestamps)
  - Pin important findings to top
  - Attach images/docs/audio
  - **InvestigationAI panel** (collapsible right):
    - "What gaps remain in this investigation?"
    - "Suggest next investigative steps based on similar cases"
    - "Any contradictions in witness statements?" (flagged via Claim Ledger)
    - "Recommend evidence to collect"
    - Buttons: "Generate investigation report draft" (→ Phase 15 feature), "Link to other cases"

- **Right panel (Context sidebar):**
  - Quick stats: Investigation age, arrest status, chargesheet status
  - Related cases (from Case Similarity Agent)
  - Assigned IO, SHO approval status

- **Bottom panel (Task board):**
  - Kanban columns: To Do | In Progress | Blocked | Complete
  - Drag-drop task cards with priority, due date, assignee
  - InvestigationAI suggests next tasks

---

**3.2.2 Arrest & Surrender Management**

- **Arrest form (modal/slide-in):**
  - Select accused from case (auto-filled from Accused table)
  - Arrest/Surrender type (dropdown: Arrest / Voluntary Surrender)
  - Date/time of arrest
  - Location (State/District/PoliceStation dropdowns + GPS coords)
  - Investigating Officer (auto-filled, modifiable)
  - Court produced before (dropdown from Court table)
  - Is Accused / Is Complainant Accused flags
  - Photo of accused (upload)
  - **Submit** → creates ArrestSurrender record, triggers InvestigationAI:
    - "Chargesheet deadline?" (calculates from arrest date)
    - "Any prior arrests of this person?" (checks Accused table via offender pool)

- **Arrest List View:**
  - Table: Accused Name | Arrest Date | Location | IO | Status (Bailed/In Custody/Chargesheeted) | Actions
  - Filter by: Status, date range, IO
  - Bulk action: Mark ready for chargesheet

---

### 3.3 **Case Search & Retrieval** (All Roles)

**Purpose:** Fast case lookup by Crime No, complainant, accused, location, or free-text.  
**Primary Agent:** Database Intelligence Agent  
**AI Assistant Name:** "**SearchBot**" (ಹುಡುಕು-ಬಾಟ್)

#### Key Screens:

**3.3.1 Case Search Interface**

- **Search bar (sticky header):**
  - Placeholder: "Search by Crime No, complainant name, accused, location…"
  - Search mode toggle: Quick | Advanced | Natural Language
  
  **Quick Mode:**
  - Single input → searches Crime No, Case No, Complainant Name, Accused Name
  - Results in-line: Matching cases in a collapsible list with preview cards
  
  **Advanced Mode:**
  - Filters: Date range, Crime category, Crime head, Gravity, Police station, Case status, Court
  - Geo-filter: Radius around incident location
  - Multi-select for acts/sections
  - Results count + sorting (by date, relevance, case ID)
  
  **Natural Language Mode:**
  - Free-text query input: "Robbery cases in Bengaluru last month" or "ಬೆಂಗಳೂರಿನಲ್ಲಿ ಕಳ್ಳತನದ ಪ್ರಕರಣಗಳು"
  - SearchBot analyzes query → auto-populates filters in Advanced mode
  - Shows confidence score for interpreted filters
  - "Did you mean…?" suggestions

- **Search Results View:**
  - Each result is a card:
    - Case summary (Crime No, Complainant, Accused count, Category, Status)
    - Snippet of brief facts (first 150 chars)
    - Date & location tags
    - "View details" button → opens Case Detail panel

- **SearchBot AI Panel:**
  - "No results? Try…" suggestions
  - "Similar cases to this result?" (Case Similarity Agent)
  - "People network linked to accused?" (Network Agent)
  - "Any alerts on this case?" (Alert Agent)

---

### 3.4 **Chargesheet Management** (Sub-Inspector / Inspector)

**Purpose:** Draft, review, and file chargesheet with linked evidence and legal sections.  
**Primary Agent:** Database Intelligence Agent + Report Intelligence Agent  
**AI Assistant Name:** "**ChargesheetAI**" (ಪ್ರಸ್ತಾವನೆ-ಎಐ)

#### Key Screens:

**3.4.1 Chargesheet Preparation Form**

- **Header:** Case info (Crime No, Complainant, Accused list)
- **Chargesheet sections:**
  1. **Case summary** (auto-filled from BriefFacts + investigation notes)
  2. **Findings** (rich text + structured evidence list)
     - Evidence table: Evidence description | Type (Physical/Documentary/Testimonial) | Collected date | Handler | Status (Attached/Missing)
  3. **Accused & Charges**
     - Repeatable: For each accused, select applicable act-sections from ActSectionAssociation
     - Auto-calculated impact based on charge severity
  4. **Legal opinion** (text field)
  5. **Recommendation** (radio: Chargesheet / False Case / Undetected)
  6. **Approver** (auto-filled SHO or designated officer)
  7. **Chargesheet date** (defaults to today)

- **Chargesheet type (dropdown):**
  - A: Chargesheet
  - B: False Case
  - C: Undetected

- **ChargesheetAI Panel:**
  - "Review evidence completeness" → flags missing evidence types (physical, witness, documentary)
  - "Check legal sections for consistency" → cross-checks charges against crime facts
  - "Similar chargesheet language?" → retrieves past chargesheet templates
  - "Generate chargesheet narrative" (Phase 15 feature)
  - Button: "Preview PDF" → shows full chargesheet formatted for court

- **Approval Workflow:**
  - Submit → pending SHO review
  - SHO view: "Approve" | "Request revisions" | "Reject"
  - On approval: ChargesheetDetails record created with cstype, csdate, PolicePersonID

---

## 4. Phase 2 Dashboards: Intelligence & Analysis

### 4.1 **Command Center Dashboard** (DSP / Commander)

**Purpose:** Real-time overview of district crime patterns, active investigations, and priority alerts.  
**Primary Agent:** Database Intelligence Agent + Trend Intelligence Agent + Alert Intelligence Agent + Geospatial Intelligence Agent  
**AI Assistant Name:** "**CommanderAI**" (ಸೈನ್ಯಾಧಿಕಾರಿ-ಎಐ)

#### Key Screens:

**4.1.1 Intelligence Hub (Landing View)**

- **Top row (KPI Cards) — data-backed only:**
  1. **Active cases** (count by status: Under Investigation | Chargesheeted | Closed)
  2. **This month's FIRs** (total count, vs. last month % change)
  3. **Arrests** (this month, this week trend)
  4. **Chargesheet rate** (chargesheet rate %, last 90 days trend line)
  5. **Crime hotspots** (top 3 locations by incident count, this month)
  
  → Each card shows: primary number, secondary metric, last update timestamp, confidence/data quality icon

- **Map panel (center-left):**
  - **Karnataka map** with district boundaries
  - **Heat map overlay:** incident density by district + sub-district
  - **Incident markers:** clustered by location, color-coded by crime category
  - **Arrest markers:** blue pins for active arrest locations
  - **Click interactions:**
    - Click district → zooms to district, shows station-level view
    - Click incident pin → expands case summary card in right panel
  - **Legend:** Color scale (crime category), marker types
  
  → **GeoBot AI assistant** (integrated): "Show me robbery hotspots in Bengaluru" | "Arrests by location" | "Incident density trend"

- **Intelligence Stream (right panel):**
  - Vertical timeline of recent events (last 7 days):
    - ✓ "FIR 104430006202600001 filed — Robbery, Bengaluru South" (with time)
    - ✓ "Accused A1 arrested in FIR 104430006202600001" (with time)
    - ⚠️ "Alert: Repeat offender in custody for 3rd time this month" (severity badge)
    - ✓ "Chargesheet filed for FIR 104430006202600002"
  - Click any item → expands details in main panel
  - Filter by: Event type, severity, time range
  - **CommanderAI suggests:** "Anything unusual here?" | "Related cases?" | "Forecast this trend?"

- **Right sidebar (Intelligence Drawer):**
  - **Quick filters:** Time period (This week | Last month | Last 90 days | Custom), Crime category, Police station, Case status
  - **Pinned intelligence** (saved by officer):
    - Saved queries, linked cases, offender dossiers
  - **Recent alerts** (collapsible):
    - Alert title, severity, affected scope, timestamp
    - "Acknowledge" / "Review" / "Dismiss" buttons

---

**4.1.2 Offender Pool & Dossier View**

- **Offender list view:**
  - Table: Offender name | Age | Gender | # FIRs | Last arrest date | Priority rank | Actions
  - Filters: Priority, crime category, location, repeat offender (2+ arrests)
  - Sort: By # FIRs (descending), by last arrest date, by priority rank
  - Bulk action: Flag for network analysis, generate dossier

- **Offender Dossier (modal/panel):**
  - **Header:** Photo + name + age + gender + priority score (1–10 with confidence %)
  - **Case history:** Timeline of all FIRs linked to this offender
  - **Arrest history:** ArrestSurrender records with dates, locations, bail status
  - **Co-accused network:** List of people arrested with offender (frequency count)
  - **Geographic pattern:** Incident locations on map (heat map of offender's activity area)
  - **Behavioral summary:** Crime categories, severity trend, seasonal patterns
  - **Intelligence notes:** Analyst observations (read-only to IO, editable by DSP/Commander)
  - **Related offenders:** Similar profile offenders
  - **Action buttons:** Open linked cases | View network graph | Generate offender brief (Phase 15)

- **OffenderAI Assistant:**
  - "Who are this offender's known associates?"
  - "Pattern in crime locations?" → GeoBot analysis
  - "Forecast likelihood of re-arrest" → Forecast Agent
  - "Similar offender profiles in database"

---

### 4.2 **Network Intelligence Dashboard** (DSP / Commander / Analyst)

**Purpose:** Analyze criminal networks and relationship patterns.  
**Primary Agent:** Network Intelligence Agent + Offender Intelligence Agent  
**AI Assistant Name:** "**NetworkAI**" (ನೆಟ್‌ವರ್ಕ್-ಎಐ)

#### Key Screens:

**4.2.1 Network Graph Visualization**

- **Interactive graph (center):**
  - Nodes: Offenders (circle nodes, sized by centrality), Cases (square nodes, color-coded by crime category)
  - Edges: Co-accused links (line thickness = frequency), Related cases (dashed lines)
  - **Click interactions:**
    - Click node → highlights connected subgraph, shows node details in right panel
    - Drag node → manual layout adjustment (temporary, not saved)
    - Double-click → opens Offender Dossier
  - **Legend:** Node types, edge types, node size/color meaning
  
- **Graph controls (top-left):**
  - Layout: Force-directed | Hierarchical | Radial | Circular
  - Node size by: Centrality | # Cases | # Arrests
  - Node color by: Crime category | Priority | Recent activity
  - Edge thickness by: Co-arrest frequency | Recency
  - Filter: Time range, crime category, geographic area (state/district)
  - **Zoom / Pan / Reset view buttons**
  - Export: PNG | SVG | JSON

- **Network metrics panel (left sidebar):**
  - **Key measures:**
    - Network density (0–1 scale, explained on hover)
    - Largest cluster size (# nodes)
    - Central figures (top 5 by betweenness centrality, ranked)
    - Bridges (offenders connecting distinct clusters)
  - NetworkAI interpretation: "This network is highly connected" | "3 distinct clusters identified" | "High-risk hub at: [name]"

- **Right panel (Node details):**
  - When node selected:
    - If offender: dossier summary (photo, cases, recent arrests)
    - If case: case summary (Crime No, complainant, accused, FIR date)
  - Related nodes list (connected by edges)
  - Evidence for relationship (co-arrested in FIRs: [Crime No list])

- **NetworkAI Assistant:**
  - "Show me connections to [offender name]"
  - "Who is the highest-priority person in this network?"
  - "Emerging connections in last 30 days?"
  - "Recommend high-risk offender pairs for surveillance"

---

### 4.3 **Case Similarity & Pattern Detection Dashboard** (DSP / Analyst)

**Purpose:** Identify similar cases and detect recurring patterns.  
**Primary Agent:** Case Similarity Agent + Trend Intelligence Agent  
**AI Assistant Name:** "**PatternBot**" (ಪ್ಯಾಟರ್ನ್-ಬಾಟ್)

#### Key Screens:

**4.3.1 Similar Cases Interface**

- **Input section (top):**
  - "Analyze case" input → dropdown of recent cases or search
  - Selected case preview card (Crime No, complainant, accused, brief facts snippet)
  - "Find similar cases" button → triggers Case Similarity Agent

- **Results view (main):**
  - **Pivot card (center-top):** Selected case (larger view)
  - **Similar case cards (below, in grid or list):**
    - Each card shows:
      - Case summary (Crime No, complainant, accused count, crime category)
      - Similarity score (0–100%) with breakdown:
        - Fact similarity (brief facts text match %)
        - Crime category match
        - Accused profile similarity (age, gender patterns)
        - Location proximity
        - Temporal proximity (months apart)
      - **Key differences** flagged (e.g., "Different crime head but same IPC section")
      - "View details" link
  
  - **Similarity threshold slider** (top-right): 0–100%, dynamically filters results

- **Pattern detection panel (left):**
  - **Temporal patterns:**
    - "Cases by month" (bar chart, last 12 months)
    - "Trend: Increasing | Stable | Decreasing" (with statistical confidence)
  - **Geographic clustering:**
    - "Hotspot areas" (linked to GeoBot recommendations)
  - **Offender recurrence:**
    - "Repeat offenders" (# unique offenders in similar case cluster)
  - **Crime method patterns:**
    - Most common crime sub-heads
    - Weapon usage patterns

- **PatternBot AI Assistant:**
  - "Is this a series?" (analyzes if cases are linked by method, offender, location)
  - "Recommend related investigation leads"
  - "Forecast next likely incident" → Forecast Agent
  - "Alert DSP of emerging pattern"

---

### 4.4 **Geospatial Intelligence Dashboard** (DSP / Commander)

**Purpose:** Visualize crime distribution, plan resource deployment.  
**Primary Agent:** Geospatial Intelligence Agent  
**AI Assistant Name:** "**GeoBot**" (ಭೌಗೋಳಿಕ-ಬಾಟ್)

#### Key Screens:

**4.4.1 Crime Heat Map & Hotspot Analysis**

- **Map (center, full-screen):**
  - Base layer: Karnataka map + district/taluk boundaries
  - Heat map overlay: Incident density (from latitude/longitude in CaseMaster)
  - Color scale: Green (low) → Yellow → Orange → Red (high density)
  - **Granularity controls:** State | District | Sub-district (taluk) zoom levels
  - **Clustering:** Auto-clusters incidents at high zoom, expands at low zoom

- **Filters (left panel):**
  - Time period: Last week | Month | Quarter | Year | Custom
  - Crime category: Multi-select (Robbery, Assault, Theft, etc.)
  - Gravity: Heinous | Non-Heinous
  - Case status: All | Under Investigation | Chargesheeted | Closed
  
  - **GeoBot interprets:**
    - "Crime density increased 15% in Bengaluru South this month"
    - "Robbery hotspot near [location], 8 incidents in 30 days"
    - "Recommendation: Increase patrolling in [radius]"

- **Hotspot list (right panel):**
  - Ranked by incident count (this period):
    1. Bengaluru South: 24 incidents (Robbery 40%, Theft 35%, Other 25%)
    2. Bengaluru East: 18 incidents …
  - Click any hotspot → zooms map, shows incident details, suggests prevention strategies

- **Predictive hotspot layer:**
  - Forecast Agent generates "Expected hotspots next 7 days" overlay (different color, lower opacity)
  - GeoBot confidence: "60% confidence in next week's forecast"

- **Resource allocation suggestions (GeoBot):**
  - "Recommend 3 additional patrol units in Bengaluru South"
  - "Checkpoint recommendations based on incident patterns"

---

## 5. Phase 3 Dashboards: Advanced Intelligence & Forecasting

### 5.1 **Forecast & Trend Analysis Dashboard** (DSP / Commander)

**Purpose:** Display crime trends and forecasts without LLM fabrication; all metrics backed by versioned Forecast Results.  
**Primary Agent:** Forecast Intelligence Agent + Trend Intelligence Agent  
**AI Assistant Name:** "**TrendBot**" (ಟ್ರೆಂಡ್-ಬಾಟ್)

#### Key Screens:

**5.1.1 Crime Forecast Interface**

- **Forecast selection (top):**
  - "View forecast for:" dropdown → Crime category (Robbery | Assault | Theft | All), District, Time horizon (7 days | 30 days | 90 days)
  - Forecast run date + version (e.g., "Forecast run 2026-07-10, v2.1, baseline: naïve forecast")
  - Last refresh time + next refresh scheduled time

- **Main forecast panel:**
  - **Time-series chart:**
    - X-axis: Time (dates)
    - Y-axis: Case count (incidents)
    - Historical data (solid line, last 12 months)
    - Baseline forecast (dashed line, naïve model)
    - Predicted forecast (solid line with confidence interval shaded)
    - **Hover interactions:** Shows exact values + model + version for that point
  
  - **Performance metrics (below chart):**
    - Forecast accuracy on holdout test set (RMSE, MAE, MAPE %)
    - "Baseline comparison: Our model is [X]% better/worse than naïve baseline"
    - Model version + retraining date
    - Drift warning (if applicable): "Model accuracy declined 5% this month — retraining recommended"

- **Forecast interpretation (TrendBot, right panel):**
  - Natural language summary:
    - "Robbery cases expected to [increase | decrease | stay stable] next 7 days"
    - "30-day forecast: ~[X] incidents, vs. [baseline] from naive model"
    - "Confidence: High | Medium | Low" (tied to forecast error bounds)
  - Caveats: "Forecast assumes continuation of current pattern; external events could alter trend"

- **Forecast quality indicators:**
  - Data completeness: "98% of districts reporting" (linked to data-quality warnings)
  - Latest data lag: "Latest data is 2 days old" (due to reporting delays)
  - Model retraining cadence: "Last retrained 2026-07-10; next retraining 2026-07-24"

- **Comparative forecasts (optional, for DSP/Commander):**
  - Compare forecasts across: Districts, Crime categories, Time periods
  - Visualization: Side-by-side mini charts or overlay

- **TrendBot Assistant:**
  - "Is this trend statistically significant?" (links to statistical test results)
  - "What external factors might influence this forecast?" (external data integration, future work)
  - "Generate brief on forecast implications for resource allocation"

---

### 5.2 **Alert & Anomaly Dashboard** (DSP / Commander / Analyst)

**Purpose:** Deliver officer-controlled, explainable early warnings with full provenance.  
**Primary Agent:** Alert Intelligence Agent  
**AI Assistant Name:** "**AlertBot**" (ಎಚ್ಚರಿಕೆ-ಬಾಟ್)

#### Key Screens:

**5.2.1 Alert Management Interface**

- **Alert list view (main):**
  - Table: Alert title | Severity | Type | Affected scope | Triggered date | Status | Action
  
  - **Severity badges:** 🔴 Critical | 🟠 High | 🟡 Medium | 🟢 Low
  - **Alert types:**
    - Repeat offender (same person in multiple arrests)
    - Hotspot emergence (unusual cluster of incidents)
    - Forecast anomaly (actual cases exceed forecast bounds)
    - Network expansion (new co-accused links to known cluster)
    - Cross-district pattern (similar cases in multiple districts)
    - Data quality (missing data, unusual values)
  
  - **Status badges:** New | Acknowledged | Under Review | Resolved | False Positive
  - **Action buttons:** View details | Acknowledge | Update status | Dismiss | Generate brief

- **Filters & sorting (left):**
  - Filter by: Severity, type, status, date range, district, affected offender
  - Sort by: Date (newest first), severity, type
  - **Quick filters:** Show only | New alerts | Critical alerts | This week's alerts

- **Alert detail panel (expanded from list):**
  - **Header:** Alert title + severity badge + type + triggered date
  - **Trigger rule:** "Alert rule: Offender with 3+ arrests in 30 days"
  - **Observed value:** "[Offender name] arrested 3 times in last 25 days"
  - **Baseline:** "Historical baseline: 0.8 arrests/month for this offender class"
  - **Affected scope:** "[3 FIRs listed], [3 districts], [2 police stations]"
  - **Evidence:** Links to FIR records, arrest records (full provenance)
  - **Model/algorithm info:** "Alert rule version: 2.1, last updated 2026-06-15"
  - **Confidence:** "High confidence" (rule-based, deterministic)
  
  - **Officer actions:**
    - "Acknowledge" → status = Acknowledged, timestamp recorded
    - "Dismiss" → status = Dismissed, requires optional reason
    - "Escalate to DSP" → creates notification
    - "Link related alert" → suggests similar patterns
    - "Generate briefing" → Phase 15 feature
  
  - **AlertBot interpretation:**
    - "Why this alert?" Explains trigger in plain language
    - "Recommended action:" Suggests next investigation step
    - "Related alerts:" Lists connected patterns or suspects

---

## 6. Phase 4 Dashboards: AI-Assisted Investigation & Reporting

### 6.1 **Investigation Assistant & Lead Generation** (IO / Inspector)

**Purpose:** AI-assisted investigation planning with evidence-backed hypotheses.  
**Primary Agent:** Investigation Intelligence Agent + Lead Intelligence Agent + Report Intelligence Agent  
**AI Assistant Name:** "**InvestigationGPT**" (ತನಿಖೆ-ಜೆಪಿಟಿ)

#### Key Screens:

**6.1.1 Investigation Workspace**

- **Left panel (Investigation outline):**
  - Hierarchical outline:
    - Case facts (editable rich-text summary)
    - Evidence collected (checkbox list with photos/docs)
    - Witnesses interviewed (names + notes)
    - Leads under investigation
    - Contradictions/gaps flagged by Claim Ledger
  
- **Center panel (Rich canvas):**
  - Multi-view toggle: Timeline | Network | Evidence | Notes
  
  **Timeline view:**
  - Vertical timeline of investigation events (arrest, evidence collection, witness interview)
  - Drag-to-reorder, drag-to-link events
  - Click event → expands details + related evidence in sidebar
  
  **Network view:**
  - Simplified people network (subset of Network Intelligence agent)
  - Nodes: People (complainant, victims, accused, witnesses)
  - Edges: Relationships (co-accused, family, known associate)
  - Helps IO see connections

- **Right panel (InvestigationGPT assistant):**
  - **Investigation stage selector (top):** Early | Active | Advanced | Ready for chargesheet
  
  - **AI recommendations:**
    - "Next investigative step?" → InvestigationAI suggests based on case facts + similar cases
    - "Gaps in evidence?" → Flags missing evidence types, witness testimony
    - "Contradictions?" → Claim Ledger highlights conflicting statements
    - "Leads to prioritize?" → Prioritizes by evidence strength + case similarity
  
  - **Hypothesis generation (collapsible):**
    - InvestigationAI generates 2–3 alternate hypotheses
    - Each with: narrative | supporting evidence | contradicting evidence | confidence level
    - Example:
      - Hypothesis 1: "Accused A1 is primary offender" (70% confidence, 8 supporting facts, 1 contradiction)
      - Hypothesis 2: "Accused A1 is accomplice, A2 is primary" (25% confidence, 4 supporting facts, 3 contradictions)
      - Hypothesis 3: "Unknown third party involved" (15% confidence, 2 supporting facts, 2 contradictions)
    - Buttons: "Accept" | "Reject" | "Investigate further"
    - Evidence for each supported by links to case records (fully traceable)
  
  - **Lead suggestions:**
    - LeadBot suggests: "Interview witness W3 about timeline discrepancy" | "Cross-check A2's alibi with CCTV"
    - Each lead shows: objective | recommended approach | expected outcome | priority
    - Status: Not started | In progress | Complete
    - "Mark as done" → logs completion, triggers next lead suggestions

- **Kannada typing support:**
  - Witness statement input field → enable Kannada typing for notes in local language

---

### 6.2 **Report & Briefing Generation** (Inspector / DSP / Commander)

**Purpose:** Generate professional, evidence-backed reports and briefings for court/administration.  
**Primary Agent:** Report Intelligence Agent  
**AI Assistant Name:** "**ReportBot**" (ವರದಿ-ಬಾಟ್)

#### Key Screens:

**6.2.1 Briefing Builder**

- **Report type selector (top):**
  - Investigation report (for chargesheet)
  - Offender dossier
  - Alert brief
  - Network brief
  - Intelligence summary (ad-hoc brief)

- **Selected report view:**
  - **Example: Investigation Report**
    - Auto-populated sections (from case data):
      - Case summary (Crime No, complainant, accused, FIR date, IO, status)
      - Incident narrative (from BriefFacts + investigation notes)
      - Evidence inventory (table: item, type, collected date, handler, storage location, status)
      - Witness summary (names, statement dates, key findings)
      - Accused details (for each: name, age, charges, arrest details, custody/bail status)
      - Legal sections (acts/sections invoked with brief definitions)
      - Investigation timeline
      - Investigator's conclusion
      - Prosecutor's recommendation (by SHO/DSP)
    
    - **Editing:** Sections are editable rich-text; officer can add/remove sections, reorder
    - **Evidence provenance:** Hover any evidence item → shows metadata (collected by, date, chain of custody)
    - **Appendix (auto-generated):** Model/algorithm versions used, data sources, limitations, confidence indicators
  
  - **Preview/Export options (right):**
    - Preview as PDF
    - Download PDF (authorized only)
    - Print
    - Email to court / prosecutor / DSP
    - Archive to case file
  
  - **ReportBot assistant:**
    - "Anything missing from this report?" → Flags incomplete sections
    - "Suggest narrative based on similar cases" → GenerativeAI (Phase 15) retrieves templates
    - "Check for contradictions with prior statements" → Claim Ledger review
    - "Is evidence properly documented?" → Checks chain of custody

---

## 7. Global Features & AI Assistant Infrastructure

### 7.1 **Unified AI Assistant Design Pattern**

Every dashboard includes a **context-aware AI panel** following this pattern:

```
┌─ Assistant Header ─────────────────────┐
│ 🤖 AssistantName (e.g., CaseBot)      │ [Collapse/Expand ⌃]
│ ಎನ್ನನ ಸಹಾಯಕ (Kannada name)            │ [Settings ⚙️]
└─────────────────────────────────────────┘
├─ Suggested Prompts (clickable cards):
│  • "What gaps remain?"
│  • "Recommend next steps"
│  • "Similar cases exist?"
├─ OR Natural language input:
│  ┌───────────────────────────────────┐
│  │ Ask me anything about this...      │
│  │ [Microphone icon] [Submit button] │
│  └───────────────────────────────────┘
├─ Conversation history (scrollable):
│  Officer: "What gaps remain?"
│  CaseBot: "Evidence summary is incomplete…"
│  [Show evidence checklist]
├─ Action buttons (context-specific):
│  [Auto-fill form] [Link similar] [Generate report draft]
└─ Footer:
   Powered by [Agent name] | Learn more | Report issue
```

### 7.2 **Multi-Language Support (English ↔ Kannada)**

- **Implementation:**
  - All UI labels, placeholders, help text stored in JSON translation files
  - Toggle language in top-right settings → entire page re-renders instantly
  - User preference saved to localStorage + backend profile
  - Kannada fonts: Noto Sans Kannada (Google Fonts) + fallback

- **Content translation rules:**
  - Database field values (e.g., Crime category names, occupation names) translated from lookup tables
  - User-generated content (e.g., case facts, investigation notes) remain in original language (stored as-is)
  - AI assistant responses generated in current language
  - Reports generate in language of current session (option to override)

- **Example UI translations:**

| English | Kannada (ಕನ್ನಡ) |
|---|---|
| Case Registration | ಪ್ರಕರಣ ನೋಂದಣಿ |
| Complainant Name | ದೂರುದಾರರ ಹೆಸರು |
| Accused | ಆರೋಪಿ |
| Investigation Workspace | ತನಿಖೆ ಕಾರ್ಯಕ್ಷೇತ್ರ |
| Arrest & Surrender | ಬಂಧನ ಮತ್ತು ಸರಣಾಮಿ |
| Offender Dossier | ಅಪರಾಧಿ ಡೊಸಿಯರ್ |
| Generate Report | ವರದಿ ರಚಿಸಿ |

---

### 7.3 **Kannada Typing Support (Kannada Keyboard)**

**Feature:** Floating Kannada input panel (opt-in in settings).

**Implementation:**
- **Typing modes:**
  1. **Phonetic (Google Transliteration API compatible):**
     - User types Latin characters: "namaskara" → suggests ನಮಸ್ಕಾರ
     - Picks from dropdown suggestions or auto-commits
  
  2. **Typewriter (Kannada keyboard layout):**
     - Visual keyboard shows Kannada consonants, vowels, modifiers
     - Click key or use arrow keys to select
     - Supports QWERTY → Kannada mapping (configurable)

- **UI:**
  - Toggle: "Enable Kannada typing" checkbox in ⚙️ Settings
  - When enabled: Floating bar appears at bottom of screen
  - Shows: Active input field indicator, typing mode toggle, keyboard toggle, clear button
  - Supports copy/paste from external Kannada text sources
  - Auto-hides on blur, re-appears on focus of textarea/input

- **Integration:**
  - Works in all text fields: Case facts, investigation notes, witness statements, etc.
  - Preserves Kannada text in database (UTF-8 encoded)
  - Search & filtering works with Kannada queries (phonetic or native)

---

### 7.4 **Evidence Validator & Claim Ledger UI**

**Purpose:** Make uncertainty and provenance transparent to officers.

**Implementation:**
- **Claim Ledger view (accessible from any case):**
  - Shows every factual statement about a case, classified as:
    - 🟦 DATABASE_FACT (from database tables, authoritative)
    - 🟨 COMPUTED_FINDING (derived from data by deterministic algorithm)
    - 🟧 MODEL_PREDICTION (inferred by ML model, includes confidence %)
    - 🟪 MODEL_HYPOTHESIS (speculative, unproven)
  
  - For each claim:
    - Statement text
    - Classification badge (color-coded)
    - Producer (agent, model version)
    - Evidence references (links to source records)
    - Confidence level (if applicable) + semantic meaning
    - Validation status: Accepted | Under Review | Disputed | Rejected
  
  - Officer can: Accept claim | Request evidence | Flag as contradiction | Add note

- **Contradiction detector:**
  - When new evidence contradicts prior claim, system flags both with visual alert
  - Example: "Witness A says incident occurred at 10 PM, but FIR registered at 9:15 PM"
  - InvestigationAI prompts: "Resolve contradiction?"
  - Officer resolves by: Accepting new evidence, marking prior as outdated, adding investigative note

---

## 8. Settings & User Preferences

### 8.1 **Settings Panel** (⚙️ in top-right)

- **Display:**
  - Language: English / ಕನ್ನಡ
  - Theme: Light | Dark
  - Font size: Small | Normal | Large
  
- **Input:**
  - ☑ Enable Kannada typing
  - Kannada typing mode: Phonetic | Typewriter
  - Keyboard layout (if typewriter): Standard | Alt
  
- **Notifications:**
  - ☑ Alert notifications (sound, desktop)
  - ☑ Case update notifications
  - Alert frequency: Real-time | Daily digest | Weekly
  
- **Permissions & data scope:**
  - View-only cases: [Station X cases only]
  - Edit permissions: [Own station + investigations assigned to me]
  - Generate reports: [Yes]
  - Export data: [Yes]
  
- **AI Assistant settings:**
  - ☑ Show suggested prompts
  - ☑ Auto-suggest next steps
  - Suggestion confidence threshold: [Slider 0–100%]
  - Explainability level: Simple | Detailed | Technical
  
- **Audit & compliance:**
  - Last login: [timestamp]
  - IP address: [x.x.x.x]
  - View audit log (links to audit trail for data access)

---

## 9. Accessibility & Mobile Responsiveness

### 9.1 **Responsive Design Breakpoints**

| Breakpoint | Devices | Adjustments |
|---|---|---|
| **Tablet (≤768px width)** | iPad, Android tablets | Side panel → slide-in drawer, cards → stacked layout, hide non-critical columns in tables |
| **Mobile (≤480px width)** | Smartphones | Full-screen modal for forms, map → embedded, tables → card-based list, AI panel → collapsible top bar |

### 9.2 **Accessibility (WCAG 2.1 AA)**

- All buttons, links, form labels have descriptive text (screen-reader friendly)
- Color is not the only indicator (badges include text labels)
- Keyboard navigation: Tab through all interactive elements
- Focus indicators: Visible outline on focused elements
- Form validation: Clear error messages, linked to fields
- Kannada text: Proper Unicode support + font fallbacks

---

## 10. Data Flow & Integration with SURAKSHA AI Architecture

### 10.1 **Agent-to-UI Response Mapping**

Each agent returns a structured result:
```json
{
  "agent_id": "database_intelligence",
  "capability": "query_cases_by_location",
  "status": "success",
  "findings": [
    {
      "type": "DATABASE_FACT",
      "statement": "8 robbery incidents within 5 km radius in last 30 days",
      "evidence_refs": ["CaseMaster:104430...001", "CaseMaster:104430...002"],
      "confidence": null
    }
  ],
  "artifacts": [
    {
      "type": "map_overlay",
      "data": { "coordinates": [...], "density": [...] }
    }
  ],
  "suggested_next_tasks": [
    { "task": "Analyze offender network", "priority": "high" }
  ],
  "execution_provenance": {
    "timestamp": "2026-07-15T14:30:00Z",
    "model_version": "claude-sonnet-4-6",
    "query_latency_ms": 245
  }
}
```

**UI renders:**
- Findings → Claim Ledger
- Artifacts → Maps, charts, tables
- Suggested tasks → InvestigationAI prompt suggestions
- Provenance → Footnote in report

---

### 10.2 **Mission Orchestration UI (Commander Only)**

**Purpose:** Visualize multi-agent orchestration for complex investigations.

**Screen: Mission Control**
- **Mission timeline (top):**
  - Shows mission start time, planned end time, current elapsed time
  - Progress bar with mission phase indicator
- **Task DAG visualization (center):**
  - Nodes: Each agent task (Database query, Investigation analysis, Offender scoring, etc.)
  - Edges: Task dependencies (which tasks must complete before others)
  - Node color: Green (complete) | Yellow (in-progress) | Gray (pending) | Red (failed)
  - Click node → expands result in sidebar
- **Concurrent execution tracker:**
  - "Running 3 of 5 concurrent tasks"
  - Estimated time to completion
- **Result aggregation:**
  - As tasks complete, results appear in Claim Ledger
  - Commander reviews before final briefing
  - Replan button (if evidence gaps remain, up to 3 replans)

---

## 11. Rollout Phases & Feature Deployment Timeline

| Phase | Dashboards | Target Users | Go-Live Target |
|---|---|---|---|
| **Phase 1 (Current)** | Case Registration, Investigation Workspace, Search, Chargesheet Mgmt | Constable, Sub-Insp, Inspector | July 2026 |
| **Phase 2** | Command Center, Offender Pool, Network Intelligence, Case Similarity, Geospatial | DSP, Analyst | August 2026 |
| **Phase 3** | Forecast & Trend, Alert Dashboard | DSP, Commander | September 2026 |
| **Phase 4** | Investigation Assistant, Report Builder, Mission Control | All (role-based) | October 2026 |

---

## 12. Data Governance & Audit Trail

### 12.1 **Audit Logging**

Every action logged:
- **User action:** Officer name, rank, unit, timestamp, action (created FIR, viewed case, generated report)
- **Case access:** Officer ID, case ID, access type (read/write), timestamp, IP address
- **Report generation:** Report type, generated by, recipients, timestamp, digital signature
- **AI assistance:** Query to assistant, assistant response, model version, timestamp

Audit trail accessible to: Officer (own actions only), SHO (station-wide), DSP (district-wide), System admin (all)

---

## 13. Glossary of Terms (English / ಕನ್ನಡ)

| Term | Kannada | Definition |
|---|---|---|
| FIR | ಎಫ್‌ಐಆರ್ | First Information Report — initial police report of crime |
| UDR | ಯುಡಿಆರ್ | Un-reported Detention Record |
| PAR | ಪಿಎಆರ್ | Persons Against Records |
| Crime No | ಅಪರಾಧ ಸಂಖ್ಯೆ | Unique case identifier, formatted: 1 digit category + 4 digit district + 4 digit station + 4 digit year + 5 digit serial |
| Chargesheet | ಪ್ರಸ್ತಾವನೆ | Formal document filed by police to prosecute accused in court |
| IO | ಐಒ | Investigating Officer |
| SHO | ಎಸ್‌ಎಚ್‌ಓ | Station House Officer (senior police rank, heads station) |
| DSP | ಡಿಎಸ್‌ಪಿ | Deputy Superintendent of Police (district-level authority) |
| Offender Dossier | ಅಪರಾಧಿ ಪೋರ್ಟ್ಫೋಲಿಯೋ | Compiled profile of repeat offender with history, patterns, network |
| Claim Ledger | ಹಕ್ಕು ಪಂಜಿ | Transparent record of every factual statement, evidence, and provenance in case |
| Network Intelligence | ನೆಟ್‌ವರ್ಕ್ ಬುದ್ಧಿಮತ್ತೆ | Analysis of criminal connections, co-accused links, related cases |
| Forecast | ಮುನ್ನೆಚ್ಚರಣೆ | Data-driven prediction of future crime trends based on historical patterns |

---

## 14. Success Metrics & KPIs

| Metric | Target | Measurement |
|---|---|---|
| **Case registration time** | < 15 min | Time from incident report to FIR filed |
| **Investigation duration** | < 90 days (median) | FIR → chargesheet date |
| **Chargesheet rate** | > 85% | Chargesheeted cases / total closed cases |
| **Officer efficiency** | +30% (vs. manual) | Cases handled per IO per month |
| **AI assistance adoption** | > 60% of eligible officers | Officers using AI assistant ≥ 5x per week |
| **Report accuracy** | > 95% | Reports passed prosecutor review without major revisions |
| **Data integrity** | > 98% | Audit checks pass, no fabricated facts rendered as facts |

---

## 15. Frequently Asked Questions (FAQ)

### 15.1 **User FAQs**

**Q: How do I file an FIR in Kannada?**  
A: Toggle language to ಕನ್ನಡ in top-right. All field labels + AI assistant responses will be in Kannada. You can type Kannada in text fields using the built-in keyboard or by enabling Kannada phonetic input in settings. Case facts remain searchable in Kannada.

**Q: What does the AI assistant actually do?**  
A: The AI assistant (e.g., CaseBot) suggests next steps, flags missing information, retrieves similar cases, and helps you plan investigations—but it never makes decisions for you. Every suggestion is based on facts from the database or trusted evidence. You review and approve all actions.

**Q: Can the system automatically merge offender records?**  
A: No. The system may suggest that two offender records might be the same person, showing confidence levels and supporting/contradicting evidence. You review and decide whether to merge. No automatic merges occur.

**Q: How do I trust the forecasts?**  
A: All forecasts show: (1) historical data used, (2) baseline comparison (naive model), (3) accuracy metrics, (4) model version, (5) last retraining date. You can see if it outperforms the baseline and how confident it is.

**Q: I found a contradiction in case data. What do I do?**  
A: Open the Claim Ledger view. Flag the contradiction. The system will show both statements, their evidence, and prompt you to resolve (update, reject, or add note). Audit trail records everything.

---

## 16. Security & Compliance Considerations

- **Authentication:** Catalyst Authentication (minted by system, never client-supplied)
- **Authorization:** Row-level scope, column-level restrictions (e.g., Constable cannot see chargesheet), PII masking for minors
- **Data encryption:** All data in transit (HTTPS) and at rest (Catalyst managed keys)
- **Audit trail:** Every access, modification, report generation logged with user, timestamp, IP
- **Session timeout:** 30 minutes inactivity, auto-logout
- **Comply with:** GDPR (if applicable), Indian Police Manuals, confidentiality laws, RTI exemptions

---

## 17. Future Enhancements (Post-Phase 4)

- 🚀 Mobile app (iOS/Android) for on-field case filing
- 🚀 Voice input for case facts (Kannada speech-to-text)
- 🚀 Automated court document generation
- 🚀 Integration with CCTV footage annotation
- 🚀 Blockchain for evidence chain-of-custody
- 🚀 Predictive suspect ranking (Phase 14+ feature)
- 🚀 Real-time collaboration (multiple IOs editing same case)
- 🚀 Advanced statistical analysis tools for large case datasets

---

**End of UI/UX Specification Document**

---

**Document Approval Sign-off:**
- Product Owner: [Name]
- Tech Lead: [Name]
- Compliance Officer: [Name]
- Approved Date: [Date]

**Version History:**
- v1.0: 2026-07-15 — Initial comprehensive UI specification with all dashboards, multilingual support, Kannada typing, AI assistants, and integration with SURAKSHA AI architecture.
