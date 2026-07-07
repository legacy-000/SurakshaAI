# Suraksha AI - Frontend Prompt for Lovable/Emergent

Build a React 18+ TypeScript SPA for the KSP Datathon 2026 crime analytics platform.

## Pages

1. **LoginPage** — KGID + password form, authenticates via POST /auth/login, redirects based on role
2. **ChatPage** — Conversational interface with:
   - Message bubbles (user query, AI response with evidence badges)
   - SQL drawer (toggle to show/hide generated SQL)
   - Kannada/English language toggle
   - Voice input button (mic icon) using Web Speech API
   - Voice output (TTS playback)
   - PDF export button
   - Suggested follow-ups as clickable chips
3. **NetworkPage** — Force-directed graph using vis-network:
   - Node color by risk tier
   - Edge hover shows shared case evidence tooltip
   - Community detection button (labels communities as "Candidate")
   - Search for accused name
4. **AnalyticsPage** — Two tabs:
   - Trends: Recharts LineChart with period selector, % change display
   - Hotspots: Leaflet map with Karnataka GeoJSON overlay, DBSCAN cluster circles
5. **SocioPage** — Bar charts of demographic distributions with n= and missing% disclosed, privacy suppression note
6. **OffenderPage** — Priority score display (large number, color-coded by tier), 6 feature contribution bars, case history table, disclaimer text
7. **ForecastPage** — Prophet forecast line chart with 80% confidence band, metrics table (MAE, RMSE, baseline comparison)
8. **AlertPage** — Alert cards with severity badges (critical/warning/info), evidence JSON view, acknowledge button
9. **WorkspacePage** — Case summary card, timeline component, similar cases table with similarity scores, lead cards with confidence badges, save investigation
10. **FinancialPage** — Shows "DATA NOT AVAILABLE IN PROVIDED KSP SCHEMA" with toggle for synthetic demo data
11. **AdminPage** — Audit log table with filters by user/action/date, user management interface

## Design
- Dark theme (dark navy/teal color scheme matching KSP branding)
- Responsive layout (sidebar nav + main content)
- Loading skeletons, error boundaries, empty states
- Kannada language toggle in header

## API Integration
Use fetch/axios with base URL from env. All requests include JWT Bearer token. Handle 401/403 redirects.
