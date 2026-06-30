# Suraksha AI - Architecture Overview

This document outlines the layered architecture design.

## Layer flow
All requests propagate sequentially:

```
[ Presentation Layer (Frontend Client) ]
                 ↓
[ Controller Layer (FastAPI Route Controllers) ]
                 ↓
[ Service Layer (Business / Orchestration Logic) ]
                 ↓
[ AI Layer (LangChain Agents, forecasting, graphs) ]
                 ↓
[ Repository Layer (SQLAlchemy Database Access) ]
                 ↓
[ Database Layer (PostgreSQL with PostGIS) ]
```

*Note: No layer may skip another layer.*
