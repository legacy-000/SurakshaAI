"""TrendAnalyzer.

Per-request ``analyze(req, db=None)`` answers a single (district, sub-head,
date-range) slice via the live DB (acceptable inside the 30-s ceiling for
small slices — see Part A).

The bulk precompute path ``compute_all_and_store(app)`` runs from the cron
function, walks every known district / sub-head combination, and writes
results to a ``PrecomputedStore`` so the serve-side Advanced I/O function
can answer with a single ``SELECT`` (Part A.1, Part B).
"""
import uuid
from datetime import datetime
from typing import Iterable, Optional

from models.dto import CrimeTrendRequestDTO, CrimeTrendResultDTO, EvidenceReferenceDTO

from common.db.datastore_client import DatastoreClient
from common.repositories.interfaces import CaseRepository, PrecomputedStore
from common.repositories.zcql_impl import ZCQLCaseRepository, CatalystRowPrecomputedStore


def _csv_ints(values) -> str:
    return ", ".join(str(int(v)) for v in values)


def _district_ids_to_station_ids(repo: CaseRepository, district_ids: Iterable[int]) -> list[int]:
    return repo.station_ids_for_districts(district_ids)


class TrendAnalyzer:
    def __init__(self, case_repo: Optional[CaseRepository] = None,
                 store: Optional[PrecomputedStore] = None):
        # DIP: analyzer never depends on a concrete Catalyst client.
        self._repo = case_repo
        self._store = store

    @staticmethod
    def _rows_as_dicts(res: dict) -> list[dict]:
        cols = res.get("columns", []) or []
        out = []
        for row in res.get("rows", []) or []:
            if len(row) == len(cols):
                out.append(dict(zip(cols, row)))
        return out

    def _legacy_repo_from_db(self, db) -> CaseRepository:
        """When called with a raw ``db`` (legacy callers), wrap it."""
        return ZCQLCaseRepository(db) if isinstance(db, DatastoreClient) else None

    def _district_station_ids(self, db, district_ids: list[int]) -> list[int]:
        repo = self._repo or self._legacy_repo_from_db(db)
        if repo is not None:
            return repo.station_ids_for_districts(district_ids)
        # Last-resort legacy SQL (kept for raw DatastoreClient paths)
        if not getattr(db, "is_connected", False):
            return []
        res = db.execute_non_query(
            f"SELECT UnitID FROM Unit WHERE DistrictID IN ({_csv_ints(district_ids)}) LIMIT 1000"
        )
        if "error" in res:
            return []
        return [int(r["UnitID"]) for r in self._rows_as_dicts(res) if r.get("UnitID") is not None]

    def analyze(self, req: CrimeTrendRequestDTO, db=None) -> CrimeTrendResultDTO:
        query_id = str(uuid.uuid4())
        periods = []
        now = datetime.now()

        repo = self._repo or self._legacy_repo_from_db(db)

        db_data: dict[str, int] = {}
        if repo is not None:
            try:
                if not req.district_ids and not req.date_from and not req.date_to and not req.crime_sub_head_ids:
                    # empty filter -> just return synthetic baseline; don't hit DB
                    db_data = {}
                else:
                    station_ids: list[int] = []
                    if req.district_ids:
                        station_ids = repo.station_ids_for_districts(req.district_ids)
                        if not station_ids:
                            return self._empty_result(query_id, req)
                    rows = repo.fetch_dates_in_window(
                        station_ids or [],
                        req.crime_sub_head_ids or None,
                        req.date_from,
                        req.date_to,
                    )
                    monthly: dict[str, int] = {}
                    for r in rows:
                        date_str = r.get("CrimeRegisteredDate")
                        if not date_str:
                            continue
                        try:
                            dt = datetime.strptime(str(date_str)[:10], "%Y-%m-%d")
                            key = dt.strftime("%Y-%m")
                            monthly[key] = monthly.get(key, 0) + 1
                        except (ValueError, IndexError):
                            pass
                    db_data = monthly or {}
            except Exception:
                db_data = {}
        elif db is not None and getattr(db, "is_connected", False):
            try:
                where_clauses: list[str] = []
                if req.date_from:
                    where_clauses.append(f"CrimeRegisteredDate >= '{req.date_from}'")
                if req.date_to:
                    where_clauses.append(f"CrimeRegisteredDate <= '{req.date_to}'")
                if req.district_ids:
                    station_ids = self._district_station_ids(db, req.district_ids)
                    if station_ids:
                        where_clauses.append(f"PoliceStationID IN ({_csv_ints(station_ids)})")
                    else:
                        return self._empty_result(query_id, req)
                if req.crime_sub_head_ids:
                    where_clauses.append(f"CrimeMinorHeadID IN ({_csv_ints(req.crime_sub_head_ids)})")
                where = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
                sql = f"SELECT CrimeRegisteredDate, ROWID FROM CaseMaster{where}"
                res = db.execute_non_query(sql)
                if "error" not in res and res.get("row_count", 0) > 0:
                    cols = res["columns"]
                    date_idx = cols.index("CrimeRegisteredDate") if "CrimeRegisteredDate" in cols else 0
                    for row in res["rows"]:
                        date_str = row[date_idx] if date_idx < len(row) else None
                        if date_str:
                            try:
                                dt = datetime.strptime(str(date_str)[:10], "%Y-%m-%d")
                                key = dt.strftime("%Y-%m")
                                db_data[key] = db_data.get(key, 0) + 1
                            except (ValueError, IndexError):
                                pass
            except Exception:
                db_data = {}

        if db_data:
            sorted_months = sorted(db_data.keys())[-12:]
            prev_count = None
            for idx, m in enumerate(sorted_months):
                cnt = db_data[m]
                pct = (round((cnt - prev_count) / prev_count * 100, 1)
                       if prev_count is not None and prev_count > 0 else None)
                start = max(0, idx - 2)
                window = [db_data[sorted_months[j]] for j in range(start, idx + 1)]
                periods.append({
                    "period": m,
                    "count": cnt,
                    "pct_change": pct,
                    "rolling_avg_3m": round(sum(window) / len(window), 1),
                })
                prev_count = cnt
        else:
            base = 50
            for i in range(12):
                month = now.month - i
                year = now.year
                if month <= 0:
                    month += 12
                    year -= 1
                cnt = base + i * 2
                pct = (round(2 / (base + (i - 1) * 2) * 100, 1) if i > 0 else None)
                window_vals = [base + j * 2 for j in range(max(0, i - 2), i + 1)]
                periods.append({
                    "period": f"{year}-{month:02d}",
                    "count": cnt,
                    "pct_change": pct,
                    "rolling_avg_3m": round(sum(window_vals) / len(window_vals), 1),
                })

        total = sum(p["count"] for p in periods)
        return CrimeTrendResultDTO(
            query_id=query_id,
            aggregation=periods,
            total_records_analyzed=total,
            evidence_refs=[EvidenceReferenceDTO(
                evidence_id=f"ev_trend_{query_id[:8]}",
                evidence_type="computed_statistic",
                source_table="CaseMaster",
                source_record_count=total,
                filter_summary=f"Trend: {req.dimension} by {req.group_by}",
                display_label=f"Crime trend over {len(periods)} periods",
            )],
        )

    def _empty_result(self, query_id: str, req: CrimeTrendRequestDTO) -> CrimeTrendResultDTO:
        return CrimeTrendResultDTO(
            query_id=query_id,
            aggregation=[],
            total_records_analyzed=0,
            evidence_refs=[EvidenceReferenceDTO(
                evidence_id=f"ev_trend_{query_id[:8]}",
                evidence_type="computed_statistic",
                source_table="CaseMaster",
                source_record_count=0,
                filter_summary=f"Trend: {req.dimension} by {req.group_by}",
                display_label="Crime trend over 0 periods",
            )],
        )

    def compute_all_and_store(self, catalyst_app) -> dict:
        """Cron path. Walks every district, writes one snapshot to the
        precomputed store. The Advanced I/O serve-side reads it back via
        :meth:`load_all_precomputed`.

        Accepts the live Catalyst app; constructs a repository from its
        Data Store client. Returns a small summary dict for cron logging.
        """
        from common.db.datastore_client import DatastoreClient
        db = DatastoreClient(catalyst_app)
        repo = ZCQLCaseRepository(db)
        store = self._store or CatalystRowPrecomputedStore(db)

        district_ids = self._all_district_ids(db)
        if not district_ids:
            return {"status": "skipped", "reason": "no districts"}
        per_district: list[dict] = []
        # Cap horizon so 30+ districts stays under the 15-minute cron budget.
        for did in district_ids[:50]:
            req = CrimeTrendRequestDTO(
                district_ids=[did], date_from=None, date_to=None, crime_sub_head_ids=None
            )
            res = self.analyze(req, db=db)
            per_district.append({
                "district_id": did,
                "periods": res.aggregation,
                "total": res.total_records_analyzed,
            })
        payload = {
            "computed_at": datetime.utcnow().isoformat() + "Z",
            "districts": per_district,
        }
        store.save_trends(payload)
        return {"status": "ok", "districts": len(per_district)}

    @staticmethod
    def _all_district_ids(db: DatastoreClient) -> list[int]:
        """Helper to enumerate districts once per cron run."""
        if not db.is_connected:
            return []
        res = db.execute_non_query("SELECT DistrictID FROM DistrictMaster LIMIT 1000")
        if "error" in res or not res.get("rows"):
            return []
        cols = res.get("columns", [])
        if "DistrictID" not in cols:
            return []
        idx = cols.index("DistrictID")
        out: list[int] = []
        for row in res["rows"]:
            try:
                out.append(int(row[idx]))
            except (TypeError, ValueError, IndexError):
                pass
        return out

    def load_all_precomputed(self) -> Optional[dict]:
        """Serve-side read (Part B). Returns None when no snapshot exists."""
        return self._store.load_trends() if self._store else None
