# Suraksha AI - API Contract

## Authentication
| Method | Route | Description |
|--------|-------|-------------|
| POST | /auth/login | Login with KGID + password |
| POST | /auth/refresh | Refresh JWT token |
| GET | /auth/me | Get current user profile |

## Chat
| Method | Route | Description |
|--------|-------|-------------|
| POST | /chat/query | Send text query |
| POST | /chat/voice | Send voice query (base64 audio) |
| POST | /chat/followup | Follow-up with context |
| GET | /conversations | List conversations |
| GET | /conversations/{id}/messages | Get messages |
| DELETE | /conversations/{id} | Delete conversation |

## Analytics
| Method | Route | Description |
|--------|-------|-------------|
| GET | /analytics/trends | Crime trend data |
| GET | /analytics/hotspots | DBSCAN hotspot clusters |
| GET | /analytics/sociological | Demographic analysis |
| GET | /analytics/stats/dashboard | Dashboard KPIs |

## Network
| Method | Route | Description |
|--------|-------|-------------|
| POST | /network/search | Build criminal network graph |
| GET | /network/{run_id} | Get saved graph |
| POST | /network/communities | Detect Louvain communities |

## Offender
| Method | Route | Description |
|--------|-------|-------------|
| GET | /offender/{name} | Get offender profile |
| GET | /offender/{entity_id}/score | Get priority score |

## Cases
| Method | Route | Description |
|--------|-------|-------------|
| GET | /cases/{id}/summary | Case summary |
| GET | /cases/{id}/timeline | Investigation timeline |
| GET | /cases/{id}/similar | Similar cases |

## Forecast & Alerts
| Method | Route | Description |
|--------|-------|-------------|
| GET | /forecasts | Prophet forecast |
| GET | /alerts | Early warning alerts |
| PUT | /alerts/{id}/acknowledge | Acknowledge alert |

## Export
| Method | Route | Description |
|--------|-------|-------------|
| GET | /export/conversation/{id}/pdf | Export conversation PDF |
| GET | /export/investigation/{id}/pdf | Export investigation PDF |

## Health
| Method | Route | Description |
|--------|-------|-------------|
| GET | /health | Health check |
| GET | /ready | Readiness check |
