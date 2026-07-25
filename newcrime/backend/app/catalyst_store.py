"""Catalyst Datastore abstraction layer using REST API + OAuth."""
from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
import urllib.error
from collections import Counter
from datetime import date, datetime
from typing import Any


class CatalystStore:
    def __init__(self, project_id: str, client_id: str, client_secret: str,
                 refresh_token: str, dc: str = "in"):
        self._project_id = project_id
        self._client_id = client_id
        self._client_secret = client_secret
        self._refresh_token = refresh_token
        self._dc = dc
        self._base = f"https://api.catalyst.zoho.{dc}/baas/v1/project/{project_id}"
        self._token: str = ""
        self._token_expiry: float = 0
        # last Datastore failure, surfaced by /api/health
        self.last_error: str | None = None

    def _get_token(self) -> str:
        if self._token and time.time() < self._token_expiry:
            return self._token
        data = urllib.parse.urlencode({
            "refresh_token": self._refresh_token,
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "grant_type": "refresh_token",
        }).encode()
        req = urllib.request.Request(
            f"https://accounts.zoho.{self._dc}/oauth/v2/token",
            data=data, method="POST")
        try:
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")[:300]
            raise RuntimeError(
                f"Zoho OAuth refresh failed (HTTP {e.code}): {body}") from None
        if "access_token" not in result:
            # Zoho answers 200 with an {"error": ...} body on bad credentials;
            # surface which field is at fault without logging the secrets.
            raise RuntimeError(
                f"Zoho OAuth refresh returned no access_token: {result}. "
                f"Config seen: dc={self._dc!r} "
                f"project_id={'set' if self._project_id else 'MISSING'} "
                f"client_id={'set' if self._client_id else 'MISSING'} "
                f"client_secret={'set' if self._client_secret else 'MISSING'} "
                f"refresh_token={'set' if self._refresh_token else 'MISSING'}")
        self._token = result["access_token"]
        self._token_expiry = time.time() + result.get("expires_in", 3600) - 300
        return self._token

    def _req(self, url: str, method: str = "GET", body=None) -> dict:
        token = self._get_token()
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
            err = e.read().decode("utf-8", errors="replace")[:500]
            return {"error": True, "status": e.code, "message": err}

    def query(self, zcql: str) -> list[dict]:
        """Run ZCQL. Returns [] for a genuinely empty result.

        A failed query also returns [], which reads downstream as "no data" —
        so record why, rather than letting a broken token or a bad table name
        render as an empty screen.
        """
        result = self._req(f"{self._base}/query", "POST", {"query": zcql})
        if result.get("error"):
            self.last_error = (f"query failed ({result.get('status')}): "
                               f"{str(result.get('message'))[:200]} :: {zcql[:120]}")
            return []
        self.last_error = None
        if not result.get("data"):
            return []
        return [self._flatten(row) for row in result["data"]]

    # Datastore wants "YYYY-MM-DD HH:MM:SS" and rejects ISO-8601 with the "T"
    # separator, microseconds or an offset.
    _ISO = re.compile(
        r"^(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2}:\d{2})(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?$")

    @classmethod
    def _coerce(cls, row: dict) -> dict:
        """Normalise datetimes for the Datastore.

        Done here rather than at each call site so no caller can forget and
        have the whole insert rejected for one field.
        """
        out = {}
        for key, value in row.items():
            if isinstance(value, (datetime, date)):
                out[key] = value.strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(value, str):
                match = cls._ISO.match(value)
                out[key] = f"{match.group(1)} {match.group(2)}" if match else value
            else:
                out[key] = value
        return out

    def insert(self, table: str, row: dict) -> dict:
        """Insert one row and return it, including its new ROWID.

        The row API takes a *list* of rows and answers INVALID_INPUT to a bare
        object, so callers reading ROWID off the result got nothing.
        """
        result = self._req(f"{self._base}/table/{table}/row", "POST", [self._coerce(row)])
        if result.get("error"):
            raise RuntimeError(
                f"insert into {table} failed ({result.get('status')}): "
                f"{result.get('message')}")
        data = result.get("data")
        if isinstance(data, list):
            return self._flatten(data[0]) if data else {}
        return data if isinstance(data, dict) else {}

    def update(self, table: str, rowid: int, data: dict) -> dict:
        payload = dict(data, ROWID=str(rowid))
        result = self._req(f"{self._base}/table/{table}/row", "PUT", [self._coerce(payload)])
        if result.get("error"):
            raise RuntimeError(
                f"update {table}/{rowid} failed ({result.get('status')}): "
                f"{result.get('message')}")
        rows = result.get("data")
        if isinstance(rows, list):
            return self._flatten(rows[0]) if rows else {}
        return rows if isinstance(rows, dict) else {}

    def delete(self, table: str, rowid: int) -> None:
        self._req(f"{self._base}/table/{table}/row/{rowid}", "DELETE")

    def get(self, table: str, rowid: int) -> dict | None:
        result = self._req(f"{self._base}/table/{table}/row/{rowid}")
        data = result.get("data")
        if not data:
            return None
        return data if isinstance(data, dict) else None

    def count(self, table: str, where: str = "") -> int:
        clause = f" WHERE {where}" if where else ""
        rows = self.query(f"SELECT COUNT(ROWID) AS cnt FROM {table}{clause}")
        if rows:
            return int(rows[0].get("cnt", rows[0].get(f"{table}.cnt", 0)))
        return 0

    def bulk_insert(self, table: str, rows: list[dict]) -> list[dict]:
        results = []
        for chunk in _chunks(rows, 200):
            result = self._req(f"{self._base}/table/{table}/row", "POST", chunk)
            data = result.get("data", [])
            if isinstance(data, list):
                results.extend(data)
        return results

    def aggregate(self, table: str, group_col: str, where: str = "") -> dict[str, int]:
        clause = f" WHERE {where}" if where else ""
        rows = self.query(f"SELECT {group_col} FROM {table}{clause}")
        return dict(Counter(
            row.get(group_col) or row.get(f"{table}.{group_col}") or "Unknown"
            for row in rows
        ))

    def join(self, left_table: str, right_table: str,
             left_key: str, right_key: str,
             where: str = "", right_where: str = "") -> list[dict]:
        left_clause = f" WHERE {where}" if where else ""
        right_clause = f" WHERE {right_where}" if right_where else ""

        left_rows = self.query(f"SELECT * FROM {left_table}{left_clause}")
        right_rows = self.query(f"SELECT * FROM {right_table}{right_clause}")

        right_index: dict[Any, list[dict]] = {}
        for r in right_rows:
            key = r.get(right_key) or r.get(f"{right_table}.{right_key}")
            right_index.setdefault(key, []).append(r)

        result = []
        for lr in left_rows:
            lk = lr.get(left_key) or lr.get(f"{left_table}.{left_key}")
            for rr in right_index.get(lk, []):
                merged = {}
                for k, v in lr.items():
                    merged[f"{left_table}.{k}" if "." not in k else k] = v
                for k, v in rr.items():
                    merged[f"{right_table}.{k}" if "." not in k else k] = v
                result.append(merged)
        return result

    def fetch_all(self, table: str, where: str = "") -> list[dict]:
        clause = f" WHERE {where}" if where else ""
        return self.query(f"SELECT * FROM {table}{clause}")

    @staticmethod
    def _flatten(row: dict) -> dict:
        if len(row) == 1:
            key = next(iter(row))
            val = row[key]
            if isinstance(val, dict):
                return val
        return row


def _chunks(lst: list, size: int):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]


_store_instance: CatalystStore | None = None


def init_catalyst_store():
    global _store_instance
    from .config import settings
    if not settings.catalyst_project_id:
        _store_instance = None
        return
    _store_instance = CatalystStore(
        project_id=settings.catalyst_project_id,
        client_id=settings.catalyst_client_id,
        client_secret=settings.catalyst_client_secret,
        refresh_token=settings.catalyst_refresh_token,
        dc=settings.catalyst_dc,
    )


def get_store() -> CatalystStore:
    if _store_instance is None:
        raise RuntimeError("CatalystStore not initialized")
    return _store_instance
