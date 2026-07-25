"""One-time SQLite -> Catalyst Datastore migration via REST API.

Usage:
    cd newcrime/backend
    set CATALYST_TOKEN=1000.xxxx.yyyy
    python -m app.migrate_to_catalyst --dry-run
    python -m app.migrate_to_catalyst --clear
    python -m app.migrate_to_catalyst --only cases,investigations --clear
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
import urllib.request
import urllib.error

MIGRATION_ORDER = [
    ("users", []),
    ("officers", []),
    ("accused", []),
    ("victims", []),
    ("cases", []),
    ("financial_accounts", [("accused_id", "accused")]),
    ("investigations", [("case_id", "cases"), ("officer_id", "officers")]),
    ("case_accused", [("case_id", "cases"), ("accused_id", "accused")]),
    ("case_victim", [("case_id", "cases"), ("victim_id", "victims")]),
    ("associations", [("source_accused_id", "accused"), ("target_accused_id", "accused")]),
    ("behavior_profiles", [("accused_id", "accused")]),
    ("timeline_events", [("case_id", "cases")]),
    ("transactions", [("source_account_id", "financial_accounts"),
                      ("target_account_id", "financial_accounts"),
                      ("case_id", "cases")]),
    ("alerts", []),
    ("crime_patterns", []),
    ("predictions", []),
    ("conversations", [("user_id", "users"), ("case_id", "cases")]),
    ("messages", [("conversation_id", "conversations")]),
    ("case_notes", [("case_id", "cases")]),
    ("witnesses", [("case_id", "cases")]),
    ("evidence_documents", [("case_id", "cases")]),
    ("stage_approvals", [("case_id", "cases")]),
    ("access_requests", [("case_id", "cases")]),
    ("audit_logs", []),
]

CATALYST_COLUMNS = {
    "users": {"username", "full_name", "email", "password", "role",
              "badge_number", "district", "subdivision", "station",
              "range_name", "is_active"},
    "officers": {"badge_number", "name", "rank", "posting_station",
                 "district", "contact_number"},
    "accused": {"full_name", "aliases", "gender", "age", "address",
                "district", "phone_number", "occupation", "education",
                "socio_economic", "urban_rural", "migrant",
                "previous_convictions", "status"},
    "victims": {"full_name", "gender", "age", "contact_number", "address",
                "district", "occupation", "statement_summary"},
    "cases": {"fir_number", "title", "description", "crime_type", "crime_head",
              "modus_operandi", "status", "severity", "district", "station",
              "location_name", "latitude", "longitude", "is_financial",
              "loss_amount", "occurrence_date", "reported_date"},
    "case_accused": {"case_id", "accused_id", "role_in_crime"},
    "case_victim": {"case_id", "victim_id"},
    "associations": {"source_accused_id", "target_accused_id",
                     "relationship_type", "gang_name", "strength"},
    "investigations": {"case_id", "officer_id", "summary", "leads_details",
                       "status", "progress", "current_stage"},
    "timeline_events": {"case_id", "event_title", "description", "event_type",
                        "event_timestamp"},
    "financial_accounts": {"account_number", "holder_name", "bank",
                           "account_type", "accused_id", "is_suspicious"},
    "transactions": {"source_account_id", "target_account_id", "amount",
                     "currency", "channel", "case_id", "flagged",
                     "transaction_timestamp"},
    "crime_patterns": {"pattern_name", "description", "crime_type", "district",
                       "temporal_signature", "modus_operandi_tags",
                       "hotspot_radius_meters", "case_count"},
    "predictions": {"target_area", "crime_type", "probability", "risk_level",
                    "forecast_window_start", "forecast_window_end",
                    "contributing_factors"},
    "behavior_profiles": {"accused_id", "risk_score", "risk_band", "is_habitual",
                          "behavioral_traits", "propensity_tags", "modus_operandi"},
    "alerts": {"title", "message", "severity", "alert_type", "district",
               "is_read", "resolved"},
    "conversations": {"title", "user_id", "case_id", "language"},
    "messages": {"conversation_id", "role", "content", "language", "sql_text",
                 "evidence_json", "grounding_json", "reasoning_json", "intent"},
    "case_notes": {"case_id", "author_name", "author_role", "content", "pinned"},
    "evidence_documents": {"case_id", "category", "filename", "original_name",
                           "mime", "size", "uploaded_by", "ai_summary", "remarks"},
    "witnesses": {"case_id", "name", "contact", "statement", "reliability",
                  "document_path", "document_name"},
    "stage_approvals": {"case_id", "stage", "action", "requested_by",
                        "requested_role", "approved_by", "approved_role",
                        "comments"},
    "access_requests": {"case_id", "requested_by", "requested_role", "reason",
                        "status", "reviewed_by"},
    "audit_logs": {"user_id", "user_name", "role", "path", "resource",
                   "status_code", "pii_accessed", "action_type", "detail",
                   "ip_address", "user_agent", "session_id", "district",
                   "prev_value", "new_value", "log_timestamp"},
}

BOOL_COLUMNS = {
    "is_financial", "is_suspicious", "is_habitual", "resolved",
    "migrant", "is_active", "flagged", "pii_accessed", "is_read", "pinned",
}

INT_COLUMNS = {
    "hotspot_radius_meters", "case_count", "previous_convictions", "status_code",
}

DATETIME_COLUMNS = {
    "occurrence_date", "reported_date", "event_timestamp", "txn_timestamp",
    "transaction_timestamp", "forecast_window_start", "forecast_window_end",
    "log_timestamp",
}

COLUMN_RENAMES = {
    "transactions": {"from_account_id": "source_account_id",
                     "to_account_id": "target_account_id",
                     "txn_timestamp": "transaction_timestamp"},
    "audit_logs": {"created_at": "log_timestamp"},
}

MANDATORY_DEFAULTS = {
    "messages": {"intent": "general"},
    "audit_logs": {"action_type": "view"},
}

SKIP_COLUMNS = {"updated_at"}

_DT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}")

id_maps: dict[str, dict[int, int]] = {}


def _load_catalystrc() -> dict:
    rc_path = os.path.join(os.path.dirname(__file__), "..", ".catalystrc")
    if not os.path.exists(rc_path):
        sys.exit("ERROR: .catalystrc not found.")
    with open(rc_path) as f:
        rc = json.load(f)
    proj = rc["projects"][0]
    return {"project_id": proj["id"]}


def _api(config: dict) -> str:
    dc = os.environ.get("ZOHO_DC", "in")
    return f"https://api.catalyst.zoho.{dc}/baas/v1/project/{config['project_id']}"


def _req(url: str, token: str, method: str = "GET", body=None) -> dict:
    headers = {"Authorization": f"Zoho-oauthtoken {token}"}
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")[:300]
        return {"error": True, "status": e.code, "message": err_body}


def _normalize_dt(val):
    if val is None:
        return None
    s = str(val)
    if not _DT_RE.match(s):
        return s
    s = s.replace("T", " ", 1)
    if "." in s:
        s = s[:s.index(".")]
    if "+" in s:
        s = s[:s.index("+")]
    return s


def _clear_table(base_url: str, token: str, table: str) -> int:
    count = 0
    while True:
        result = _req(f"{base_url}/table/{table}/row", token)
        if result.get("error") or not result.get("data"):
            break
        ids = [str(r["ROWID"]) for r in result["data"] if r.get("ROWID")]
        if not ids:
            break
        _req(f"{base_url}/table/{table}/row?ids={','.join(ids)}", token, "DELETE")
        count += len(ids)
    return count


def _read_sqlite_table(conn: sqlite3.Connection, table: str, valid_cols: set[str],
                       renames: dict[str, str | None]):
    conn.row_factory = sqlite3.Row
    cursor = conn.execute(f"SELECT * FROM {table}")
    columns = [d[0] for d in cursor.description]

    rows = []
    old_ids = []
    for row in cursor.fetchall():
        d = {}
        for col in columns:
            if col == "id":
                old_ids.append(row[col])
                continue

            out_col = col
            if col in renames:
                out_col = renames[col]
                if out_col is None:
                    continue
            elif col in SKIP_COLUMNS:
                continue

            if out_col not in valid_cols:
                continue

            val = row[col]
            if out_col in BOOL_COLUMNS and val is not None:
                val = bool(int(val))
            elif out_col in INT_COLUMNS and val is not None:
                val = int(float(val))
            elif out_col in DATETIME_COLUMNS and val is not None:
                val = _normalize_dt(val)
            d[out_col] = val
        rows.append(d)
    if not old_ids:
        old_ids = list(range(1, len(rows) + 1))
    return rows, old_ids


def _apply_defaults(rows: list[dict], table: str):
    defaults = MANDATORY_DEFAULTS.get(table)
    if not defaults:
        return
    for row in rows:
        for k, v in defaults.items():
            if row.get(k) is None or row.get(k) == "":
                row[k] = v


def _remap_fks(rows: list[dict], fk_defs: list[tuple[str, str]]):
    for row in rows:
        for fk_col, ref_table in fk_defs:
            old_id = row.get(fk_col)
            if old_id is not None and ref_table in id_maps:
                row[fk_col] = id_maps[ref_table].get(int(old_id))


def _insert_chunk(base_url: str, token: str, table: str,
                  chunk: list[dict]) -> list[int | None]:
    result = _req(f"{base_url}/table/{table}/row", token, "POST", chunk)
    if result.get("error"):
        print(f"    ERR {result.get('status')}: {result.get('message', '')[:120]}")
        return [None] * len(chunk)
    data = result.get("data", result)
    if isinstance(data, list):
        return [int(r.get("ROWID", 0)) if isinstance(r, dict) else None
                for r in data]
    return [None] * len(chunk)


def migrate(db_path: str = "crimeintel.db", dry_run: bool = False,
            only: set[str] | None = None, clear: bool = False):
    config = _load_catalystrc()
    base_url = _api(config)
    token = os.environ.get("CATALYST_TOKEN", "")

    if not dry_run and not token:
        sys.exit("ERROR: Set CATALYST_TOKEN env var.")

    conn = sqlite3.connect(db_path)
    label = "DRY RUN" if dry_run else "LIVE"
    print(f"[{label}] {db_path} -> Catalyst (project {config['project_id']})")
    if only:
        print(f"  Tables: {', '.join(only)}")
    print("=" * 60)

    total = 0
    ok_total = 0

    for table_name, fk_defs in MIGRATION_ORDER:
        if only and table_name not in only:
            id_maps.setdefault(table_name, {})
            continue

        valid_cols = CATALYST_COLUMNS.get(table_name, set())
        renames = COLUMN_RENAMES.get(table_name, {})

        try:
            rows, old_ids = _read_sqlite_table(conn, table_name, valid_cols, renames)
        except Exception as e:
            print(f"  SKIP {table_name}: {e}")
            id_maps[table_name] = {}
            continue

        if not rows:
            print(f"  {table_name}: 0 rows")
            id_maps[table_name] = {}
            continue

        _remap_fks(rows, fk_defs)
        _apply_defaults(rows, table_name)

        if dry_run:
            print(f"  {table_name}: {len(rows)} rows ready  cols={sorted(rows[0].keys())}")
            id_maps[table_name] = {oid: oid for oid in old_ids}
            total += len(rows)
            ok_total += len(rows)
            continue

        if clear:
            cleared = _clear_table(base_url, token, table_name)
            if cleared:
                print(f"  {table_name}: cleared {cleared} existing rows")

        new_map: dict[int, int] = {}
        chunk_size = 200
        for i in range(0, len(rows), chunk_size):
            chunk = rows[i:i + chunk_size]
            new_rowids = _insert_chunk(base_url, token, table_name, chunk)
            for j, rid in enumerate(new_rowids):
                idx = i + j
                if idx < len(old_ids) and rid:
                    new_map[old_ids[idx]] = rid

        id_maps[table_name] = new_map
        ok = sum(1 for v in new_map.values() if v)
        total += len(rows)
        ok_total += ok
        tag = "OK" if ok == len(rows) else f"FAIL {len(rows) - ok}"
        print(f"  {table_name}: {ok}/{len(rows)} [{tag}]")

    conn.close()
    print("=" * 60)
    print(f"Result: {ok_total}/{total} rows inserted across {len(MIGRATION_ORDER)} tables")


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--help" in args:
        print(__doc__)
        sys.exit(0)

    dry = "--dry-run" in args
    clear = "--clear" in args
    only_tables = None
    for a in args:
        if a.startswith("--only="):
            only_tables = set(a.split("=", 1)[1].split(","))
        elif a == "--only":
            idx = args.index(a)
            if idx + 1 < len(args):
                only_tables = set(args[idx + 1].split(","))

    db = next((a for a in args if not a.startswith("--")), "crimeintel.db")
    migrate(db, dry_run=dry, only=only_tables, clear=clear)
