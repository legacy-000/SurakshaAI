"""ZCQL-backed implementations (Part E.5, F Indirection)."""
import logging
from typing import Iterable, Optional

from common.db.datastore_client import DatastoreClient
from common.repositories.interfaces import (
    AccusedRepository,
    CaseRepository,
    PrecomputedStore,
)

logger = logging.getLogger(__name__)


def _csv_ints(values) -> str:
    return ", ".join(str(int(v)) for v in values)


def _esc(v) -> str:
    return "'" + str(v).replace("'", "''") + "'"


class ZCQLCaseRepository(CaseRepository):
    def __init__(self, db: DatastoreClient):
        self._db = db

    def fetch_dates_in_window(
        self,
        station_ids: Iterable[int],
        crime_sub_head_ids: Optional[Iterable[int]],
        date_from: Optional[str],
        date_to: Optional[str],
        limit: int = 5000,
    ) -> list[dict]:
        station_ids = list(station_ids or [])
        if not station_ids:
            return []
        where = [f"PoliceStationID IN ({_csv_ints(station_ids)})"]
        if crime_sub_head_ids:
            sub = list(crime_sub_head_ids)
            if sub:
                where.append(f"CrimeMinorHeadID IN ({_csv_ints(sub)})")
        if date_from:
            where.append(f"CrimeRegisteredDate >= {_esc(date_from)}")
        if date_to:
            where.append(f"CrimeRegisteredDate <= {_esc(date_to)}")
        sql = (
            "SELECT CrimeRegisteredDate, ROWID FROM CaseMaster WHERE "
            + " AND ".join(where)
            + f" LIMIT {int(limit)}"
        )
        res = self._db.execute_non_query(sql)
        if "error" in res:
            return []
        return self._as_dicts(res)

    def fetch_geo_points(
        self,
        station_ids: Iterable[int],
        crime_sub_head_ids: Optional[Iterable[int]],
        date_from: Optional[str],
        date_to: Optional[str],
        limit: int = 10000,
    ) -> list[dict]:
        station_ids = list(station_ids or [])
        if not station_ids:
            return []
        where = [f"PoliceStationID IN ({_csv_ints(station_ids)})"]
        if crime_sub_head_ids:
            sub = list(crime_sub_head_ids)
            if sub:
                where.append(f"CrimeMinorHeadID IN ({_csv_ints(sub)})")
        if date_from:
            where.append(f"CrimeRegisteredDate >= {_esc(date_from)}")
        if date_to:
            where.append(f"CrimeRegisteredDate <= {_esc(date_to)}")
        sql = (
            "SELECT latitude, longitude, CaseMasterID, CaseCategoryID FROM CaseMaster WHERE "
            + " AND ".join(where)
            + f" LIMIT {int(limit)}"
        )
        res = self._db.execute_non_query(sql)
        if "error" in res:
            return []
        return self._as_dicts(res)

    def station_ids_for_districts(self, district_ids: Iterable[int]) -> list[int]:
        district_ids = list(district_ids or [])
        if not district_ids:
            return []
        res = self._db.execute_non_query(
            f"SELECT UnitID FROM Unit WHERE DistrictID IN ({_csv_ints(district_ids)}) LIMIT 1000"
        )
        if "error" in res:
            return []
        out: list[int] = []
        for r in self._as_dicts(res):
            try:
                out.append(int(r["UnitID"]))
            except (KeyError, TypeError, ValueError):
                pass
        return out

    def station_ids_for_district(self, district_id: int) -> list[int]:
        return self.station_ids_for_districts([district_id])

    @staticmethod
    def _as_dicts(res: dict) -> list[dict]:
        cols = res.get("columns", []) or []
        rows = res.get("rows", []) or []
        out: list[dict] = []
        for row in rows:
            if len(row) == len(cols):
                out.append(dict(zip(cols, row)))
            elif row and isinstance(row, dict):
                out.append(row)
        return out


class ZCQLAccusedRepository(AccusedRepository):
    def __init__(self, db: DatastoreClient):
        self._db = db

    def fetch_all(self, limit: int = 10000) -> list[dict]:
        res = self._db.execute_non_query(
            f"SELECT AccusedMasterID, CaseMasterID, AccusedName, AgeYear, "
            f"GenderID, PersonID FROM Accused LIMIT {int(limit)}"
        )
        if "error" in res:
            return []
        return ZCQLCaseRepository._as_dicts(res)

    def fetch_by_name(self, accused_name: str, limit: int = 1000) -> list[dict]:
        if not accused_name or not str(accused_name).strip():
            return []
        res = self._db.execute_non_query(
            "SELECT AccusedMasterID, CaseMasterID, AccusedName, AgeYear, GenderID, PersonID "
            f"FROM Accused WHERE AccusedName = {_esc(accused_name)} LIMIT {int(limit)}"
        )
        if "error" in res:
            return []
        return ZCQLCaseRepository._as_dicts(res)

    def fetch_cases(self, case_master_ids: Iterable[int], limit: int = 1000) -> list[dict]:
        ids = list(case_master_ids or [])
        if not ids:
            return []
        res = self._db.execute_non_query(
            "SELECT CaseMasterID, CrimeNo, CrimeRegisteredDate, CrimeMinorHeadID, "
            f"CaseStatusID FROM CaseMaster WHERE CaseMasterID IN ({_csv_ints(ids)}) LIMIT {int(limit)}"
        )
        if "error" in res:
            return []
        return ZCQLCaseRepository._as_dicts(res)

    def fetch_crime_sub_heads(self, sub_head_ids: Iterable[int], limit: int = 1000) -> list[dict]:
        ids = list(sub_head_ids or [])
        if not ids:
            return []
        res = self._db.execute_non_query(
            f"SELECT CrimeSubHeadID, CrimeHeadName FROM CrimeSubHead "
            f"WHERE CrimeSubHeadID IN ({_csv_ints(ids)}) LIMIT {int(limit)}"
        )
        if "error" in res:
            return []
        return ZCQLCaseRepository._as_dicts(res)

    def fetch_case_statuses(self, status_ids: Iterable[int], limit: int = 1000) -> list[dict]:
        ids = list(status_ids or [])
        if not ids:
            return []
        res = self._db.execute_non_query(
            f"SELECT CaseStatusID, CaseStatusName FROM CaseStatusMaster "
            f"WHERE CaseStatusID IN ({_csv_ints(ids)}) LIMIT {int(limit)}"
        )
        if "error" in res:
            return []
        return ZCQLCaseRepository._as_dicts(res)


class CatalystRowPrecomputedStore(PrecomputedStore):
    """Stores precomputed snapshots as rows in dedicated tables.

    Each ``save_*`` writes a single-row upsert keyed by a stable id. The
    serve-side ``load_*`` does a fast ``SELECT ... LIMIT 1``.
    """

    _TABLES = {
        "trends": ("TrendSnapshot", "all"),
        "hotspots": ("HotspotSnapshot", "all"),
        "forecast": ("ForecastResult", "by_key"),
        "entity_resolution": ("ResolvedEntity", "all"),
        "ips_scores": ("IPSScore", "all"),
    }

    def __init__(self, db: DatastoreClient):
        self._db = db

    def save_trends(self, payload: dict) -> bool:
        return self._save_one("TrendSnapshot", "singleton", payload)

    def load_trends(self) -> Optional[dict]:
        return self._load_one("TrendSnapshot", "singleton")

    def save_hotspots(self, payload: dict) -> bool:
        return self._save_one("HotspotSnapshot", "singleton", payload)

    def load_hotspots(self) -> Optional[dict]:
        return self._load_one("HotspotSnapshot", "singleton")

    def save_forecast(self, district_id: int, crime_sub_head_id: int, payload: dict) -> bool:
        key = f"{int(district_id)}_{int(crime_sub_head_id)}"
        return self._save_one("ForecastResult", key, payload)

    def load_forecast(self, district_id: int, crime_sub_head_id: int) -> Optional[dict]:
        key = f"{int(district_id)}_{int(crime_sub_head_id)}"
        return self._load_one("ForecastResult", key)

    def save_entity_resolution(self, payload: dict) -> bool:
        return self._save_one("ResolvedEntity", "singleton", payload)

    def load_entity_resolution(self) -> Optional[dict]:
        return self._load_one("ResolvedEntity", "singleton")

    def save_ips_scores(self, payload: dict) -> bool:
        return self._save_one("IPSScore", "singleton", payload)

    def load_ips_scores(self) -> Optional[dict]:
        return self._load_one("IPSScore", "singleton")

    def _save_one(self, table: str, key: str, payload: dict) -> bool:
        if not self._db.is_connected:
            return False
        row = {"SnapshotKey": key, "Payload": self._pack(payload), "UpdatedAt": _now_iso()}
        res = self._db.insert_bulk_rows(table, [row])
        return "error" not in res

    def _load_one(self, table: str, key: str) -> Optional[dict]:
        if not self._db.is_connected:
            return None
        res = self._db.execute_non_query(
            f"SELECT Payload FROM {table} WHERE SnapshotKey = {_esc(key)} "
            f"ORDER BY UpdatedAt DESC LIMIT 1"
        )
        if "error" in res or not res.get("rows"):
            return None
        rows = res.get("rows") or []
        if not rows:
            return None
        first = rows[0]
        cols = res.get("columns", []) or []
        if cols and "Payload" in cols:
            return self._unpack(first[cols.index("Payload")])
        return None

    @staticmethod
    def _pack(payload: dict) -> str:
        import json
        try:
            return json.dumps(payload)
        except (TypeError, ValueError):
            return "{}"

    @staticmethod
    def _unpack(raw) -> dict:
        import json
        if isinstance(raw, dict):
            return raw
        if not raw:
            return {}
        try:
            return json.loads(str(raw))
        except (TypeError, ValueError):
            return {}


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
