"""In-memory fakes (Part E.5 — tests, local dev, offline cron dry-runs).

These are interchangeable with the ZCQL-backed implementations at the
CaseRepository / AccusedRepository / PrecomputedStore interface level
(Liskov compliance — same method contracts, same return shapes).
"""
from datetime import datetime, timezone
from typing import Iterable, Optional


class InMemoryCaseRepository:
    def __init__(self, cases: Iterable[dict] | None = None, units: Iterable[dict] | None = None):
        self._cases = list(cases or [])
        self._units = list(units or [])

    def fetch_dates_in_window(
        self,
        station_ids: Iterable[int],
        crime_sub_head_ids: Optional[Iterable[int]],
        date_from: Optional[str],
        date_to: Optional[str],
        limit: int = 5000,
    ) -> list[dict]:
        stations = set(int(s) for s in (station_ids or []))
        sub = set(int(s) for s in (crime_sub_head_ids or []) if s is not None)
        out: list[dict] = []
        for c in self._cases:
            if int(c.get("PoliceStationID", -1)) not in stations:
                continue
            if sub and int(c.get("CrimeMinorHeadID", -1)) not in sub:
                continue
            d = str(c.get("CrimeRegisteredDate", ""))[:10]
            if date_from and d < date_from:
                continue
            if date_to and d > date_to:
                continue
            out.append({"CrimeRegisteredDate": c.get("CrimeRegisteredDate"), "ROWID": c.get("ROWID") or c.get("ROWID")})
            if len(out) >= limit:
                break
        return out

    def fetch_geo_points(
        self,
        station_ids: Iterable[int],
        crime_sub_head_ids: Optional[Iterable[int]],
        date_from: Optional[str],
        date_to: Optional[str],
        limit: int = 10000,
    ) -> list[dict]:
        stations = set(int(s) for s in (station_ids or []))
        sub = set(int(s) for s in (crime_sub_head_ids or []) if s is not None)
        out: list[dict] = []
        for c in self._cases:
            if int(c.get("PoliceStationID", -1)) not in stations:
                continue
            if sub and int(c.get("CrimeMinorHeadID", -1)) not in sub:
                continue
            d = str(c.get("CrimeRegisteredDate", ""))[:10]
            if date_from and d < date_from:
                continue
            if date_to and d > date_to:
                continue
            try:
                out.append({
                    "latitude": float(c["latitude"]),
                    "longitude": float(c["longitude"]),
                    "CaseMasterID": int(c.get("CaseMasterID") or c.get("ROWID") or 0),
                    "CaseCategoryID": str(c.get("CaseCategoryID", "Unknown")),
                })
            except (KeyError, TypeError, ValueError):
                continue
            if len(out) >= limit:
                break
        return out

    def station_ids_for_districts(self, district_ids: Iterable[int]) -> list[int]:
        wanted = set(int(d) for d in (district_ids or []))
        return [int(u["UnitID"]) for u in self._units if int(u.get("DistrictID", -1)) in wanted]

    def station_ids_for_district(self, district_id: int) -> list[int]:
        return self.station_ids_for_districts([district_id])


class InMemoryAccusedRepository:
    def __init__(
        self,
        accused: Iterable[dict] | None = None,
        cases: Iterable[dict] | None = None,
        sub_heads: Iterable[dict] | None = None,
        statuses: Iterable[dict] | None = None,
    ):
        self._accused = list(accused or [])
        self._cases = list(cases or [])
        self._sub_heads = {sh["CrimeSubHeadID"]: sh.get("CrimeHeadName") for sh in (sub_heads or [])}
        self._statuses = {s["CaseStatusID"]: s.get("CaseStatusName") for s in (statuses or [])}

    def fetch_all(self, limit: int = 10000) -> list[dict]:
        return list(self._accused[:limit])

    def fetch_by_name(self, accused_name: str, limit: int = 1000) -> list[dict]:
        if not accused_name:
            return []
        return [a for a in self._accused if str(a.get("AccusedName")) == accused_name][:limit]

    def fetch_cases(self, case_master_ids: Iterable[int], limit: int = 1000) -> list[dict]:
        wanted = set(int(i) for i in (case_master_ids or []))
        return [c for c in self._cases if int(c.get("CaseMasterID", -1)) in wanted][:limit]

    def fetch_crime_sub_heads(self, sub_head_ids: Iterable[int], limit: int = 1000) -> list[dict]:
        wanted = set(int(i) for i in (sub_head_ids or []))
        return [{"CrimeSubHeadID": sid, "CrimeHeadName": self._sub_heads.get(sid)}
                for sid in wanted if sid in self._sub_heads][:limit]

    def fetch_case_statuses(self, status_ids: Iterable[int], limit: int = 1000) -> list[dict]:
        wanted = set(int(i) for i in (status_ids or []))
        return [{"CaseStatusID": sid, "CaseStatusName": self._statuses.get(sid)}
                for sid in wanted if sid in self._statuses][:limit]


class InMemoryPrecomputedStore:
    def __init__(self):
        self._trends: Optional[dict] = None
        self._hotspots: Optional[dict] = None
        self._forecast: dict[tuple[int, int], dict] = {}
        self._entity: Optional[dict] = None
        self._ips: Optional[dict] = None

    def save_trends(self, payload: dict) -> bool:
        self._trends = payload
        return True

    def load_trends(self) -> Optional[dict]:
        return self._trends

    def save_hotspots(self, payload: dict) -> bool:
        self._hotspots = payload
        return True

    def load_hotspots(self) -> Optional[dict]:
        return self._hotspots

    def save_forecast(self, district_id: int, crime_sub_head_id: int, payload: dict) -> bool:
        self._forecast[(int(district_id), int(crime_sub_head_id))] = payload
        return True

    def load_forecast(self, district_id: int, crime_sub_head_id: int) -> Optional[dict]:
        return self._forecast.get((int(district_id), int(crime_sub_head_id)))

    def save_entity_resolution(self, payload: dict) -> bool:
        self._entity = payload
        return True

    def load_entity_resolution(self) -> Optional[dict]:
        return self._entity

    def save_ips_scores(self, payload: dict) -> bool:
        self._ips = payload
        return True

    def load_ips_scores(self) -> Optional[dict]:
        return self._ips
