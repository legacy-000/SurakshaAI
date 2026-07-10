"""Generate the Lovable frontend prompt for building the Suraksha AI UI."""
import json

PROMPT = """You are building a React/TypeScript frontend for Suraksha AI — a police crime analytics platform for KSP Datathon 2026.

Pages needed:
1. Login — KGID + password form, role-based redirect
2. Dashboard — KPI cards (Total Cases, Heinous %, Pending, Districts), trend sparkline
3. Chat — conversational interface with message bubbles, SQL drawer, Kannada support, voice mic button, PDF export
4. Network — force-directed graph (vis-network) with node hover/click, edge evidence tooltips, community detection button
5. Analytics — trend line chart (Recharts), hotspot Leaflet map (Karnataka GeoJSON), bar charts
6. Sociological — demographic distributions with privacy suppression disclosure
7. Offender Profile — priority score display (color-coded), 6 feature bars, case history table
8. Forecast — Prophet forecast line with confidence band, MAE/RMSE metrics
9. Alerts — alert cards with severity badges, evidence links, acknowledge button
10. Investigation Workspace — case summary, timeline, similar cases, leads, save/export
11. Financial — "DATA NOT AVAILABLE" state with synthetic demo toggle
12. Admin — audit log viewer, user management

Use: Recharts for charts, Leaflet for maps, vis-network for graphs. Dark theme. Kannada language toggle.
"""

if __name__ == "__main__":
    print(PROMPT)
