# meeting Notes - Suraksha AI Architecture Sign-off

## Date
2026-06-30

## Participants
- Senior Software Architect
- Senior Full Stack Engineer
- Karnataka Police IT Lead

## Decisions
- Layered modular design approved.
- Presentation -> Controller -> Service -> AI Layer -> Repository -> Database flow is absolute. No skipping layers.
- SQLite is rejected for production; PostgreSQL + PostGIS will be used.
- Redis will store LLM conversational state and cache predictions.
