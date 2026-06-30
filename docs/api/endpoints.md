# Suraksha AI API Specification

## Auth Router
- `POST /api/auth/login` -> Authenticates officer

## AI Chat Router
- `POST /api/chat/query` -> Process chat query

## Network Analysis Router
- `GET /api/network/case/{case_id}` -> Link analysis graph data

## Analytics Router
- `GET /api/analytics/predictions` -> Hotspot prediction

## Geospatial Maps Router
- `GET /api/map/layers` -> Leaflet map coordinate layers

## Precinct Reports Router
- `POST /api/report/generate` -> Build intelligence report

## Dashboard Router
- `GET /api/dashboard/summary` -> Aggregate metrics
