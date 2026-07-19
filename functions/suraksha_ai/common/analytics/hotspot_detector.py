"""HotspotDetector — DBSCAN-style clustering with compute/serve split.

Same shape of class + new methods for bulk precompute and serve-side reads.
"""
import math
import uuid
from typing import Iterable, Optional

from models.dto import HotspotRequestDTO, HotspotResultDTO, HotspotClusterDTO
from common.db.datastore_client import DatastoreClient
from common.repositories.interfaces import CaseRepository, PrecomputedStore
from common.repositories.zcql_impl import ZCQLCaseRepository, CatalystRowPrecomputedStore


def _csv_ints(values) -> str:
    return ", ".join(str(int(v)) for v in values)


def _haversine_km(lat1, lon1, lat2, lon2):
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return 6371 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _dbscan(points, eps_km, min_cases):
    n = len(points)
    labels = [-1] * n

    for i in range(n):
        if labels[i] != -1:
            continue
        neighbors = []
        for j in range(n):
            if i != j and _haversine_km(points[i][0], points[i][1],
                                        points[j][0], points[j][1]) <= eps_km:
                neighbors.append(j)
        if len(neighbors) < min_cases - 1:
            labels[i] = -2
            continue

        cluster_id = i
        labels[i] = cluster_id
        seed = neighbors[:]
        while seed:
            j = seed.pop()
            if labels[j] == -2:
                labels[j] = cluster_id
            if labels[j] != -1:
                continue
            labels[j] = cluster_id
            j_neighbors = []
            for k in range(n):
                if j != k and _haversine_km(points[j][0], points[j][1],
                                            points[k][0], points[k][1]) <= eps_km:
                    j_neighbors.append(k)
            if len(j_neighbors) >= min_cases - 1:
                for nj in j_neighbors:
                    if labels[nj] in (-1, -2):
                        seed.append(nj)

    clusters = {}
    for i, label in enumerate(labels):
        if label >= 0:
            clusters.setdefault(label, []).append(i)

    result = []
    for cid, indices in clusters.items():
        member_lats = [points[idx][0] for idx in indices]
        member_lngs = [points[idx][1] for idx in indices]
        centroid_lat = sum(member_lats) / len(member_lats)
        centroid_lng = sum(member_lngs) / len(member_lngs)
        radius = max(_haversine_km(centroid_lat, centroid_lng,
                                   member_lats[k], member_lngs[k])
                     for k in range(len(indices))) if len(indices) > 1 else 0.0
        crime_type = points[indices[0]][3] if len(points[0]) > 3 else None
        result.append({
            "centroid_lat": round(centroid_lat, 4),
            "centroid_lng": round(centroid_lng, 4),
            "case_count": len(indices),
            "radius_km": round(radius, 2),
            "crime_type": crime_type,
            "case_ids": [points[idx][2] for idx in indices],
        })
    return result


class HotspotDetector:
    def __init__(self, case_repo: Optional[CaseRepository] = None,
                 store: Optional[PrecomputedStore] = None):
        self._repo = case_repo
        self._store = store

    def _fmt_params(self, eps_km, min_cases):
        return {"eps": eps_km, "min_samples": min_cases, "metric": "haversine"}

    def _district_station_ids(self, db, district_id: int) -> list[int]:
        repo = self._repo
        if repo is not None:
            return repo.station_ids_for_district(district_id)
        if not getattr(db, "is_connected", False):
            return []
        res = db.execute_non_query(
            f"SELECT UnitID FROM Unit WHERE DistrictID = {int(district_id)} LIMIT 300"
        )
        if "error" in res:
            return []
        return [int(r["UnitID"]) for r in self._rows_as_dicts(res) if r.get("UnitID") is not None]

    @staticmethod
    def _rows_as_dicts(res: dict) -> list[dict]:
        cols = res.get("columns", []) or []
        out = []
        for row in res.get("rows", []) or []:
            if len(row) == len(cols):
                out.append(dict(zip(cols, row)))
        return out

    def _legacy_repo_from_db(self, db) -> CaseRepository:
        return ZCQLCaseRepository(db) if isinstance(db, DatastoreClient) else None

    def detect(self, req: HotspotRequestDTO, db=None, repo=None) -> HotspotResultDTO:
        query_id = str(uuid.uuid4())
        cases_without_gps = 0
        points: list[tuple] = []
        repo = repo or self._repo or self._legacy_repo_from_db(db)

        station_ids = self._district_station_ids(db, req.district_id)

        if repo is not None:
            rows = repo.fetch_geo_points(
                station_ids,
                getattr(req, "crime_sub_head_ids", None),
                getattr(req, "date_from", None),
                getattr(req, "date_to", None),
            )
            if not rows and station_ids:
                rows = repo.fetch_geo_points(
                    [],
                    getattr(req, "crime_sub_head_ids", None),
                    getattr(req, "date_from", None),
                    getattr(req, "date_to", None),
                )
            for r in rows:
                try:
                    lat = float(r["latitude"])
                    lng = float(r["longitude"])
                    rid = int(r.get("CaseMasterID") or 0)
                    cat = str(r.get("CaseCategoryID", "Unknown"))
                    points.append((lat, lng, rid, cat))
                except (KeyError, TypeError, ValueError):
                    cases_without_gps += 1
        elif db is not None and getattr(db, "is_connected", False):
            if not station_ids:
                return HotspotResultDTO(
                    query_id=query_id, clusters=[],
                    cases_without_gps=cases_without_gps, total_cases_analyzed=0,
                    algorithm="DBSCAN",
                    algorithm_params=self._fmt_params(req.eps_km, req.min_cases),
                )
            # Phase 1: CrimeSubHeadID → CrimeHeadName
            sid_name: dict[str, str] = {}
            sr = db.execute_non_query(
                "SELECT CrimeSubHeadID, CrimeHeadName FROM CrimeSubHead")
            if "error" not in sr:
                sc = sr.get("columns", [])
                for row in sr.get("rows", []):
                    d = dict(zip(sc, row))
                    k = str(d.get("CrimeSubHeadID", ""))
                    v = str(d.get("CrimeHeadName", ""))
                    if k and v:
                        sid_name[k] = v

            # Phase 2: Fetch geo points with CrimeMinorHeadID
            where_parts = [f"PoliceStationID IN ({_csv_ints(station_ids)})"]
            if getattr(req, "crime_sub_head_ids", None):
                where_parts.append(f"CrimeMinorHeadID IN ({_csv_ints(req.crime_sub_head_ids)})")
            if getattr(req, "date_from", None):
                where_parts.append(f"CrimeRegisteredDate >= '{req.date_from}'")
            if getattr(req, "date_to", None):
                where_parts.append(f"CrimeRegisteredDate <= '{req.date_to}'")
            sql = (
                "SELECT latitide, longitude, ROWID, CrimeMinorHeadID FROM CaseMaster "
                "WHERE " + " AND ".join(where_parts)
            )
            res = db.execute_non_query(sql)
            if "error" not in res and (res.get("row_count", 0) > 0 or res.get("rows")):
                cols = res["columns"]
                lat_idx = cols.index("latitide") if "latitide" in cols else 0
                lng_idx = cols.index("longitude") if "longitude" in cols else 1
                rid_idx = cols.index("ROWID") if "ROWID" in cols else 2
                sid_idx = cols.index("CrimeMinorHeadID") if "CrimeMinorHeadID" in cols else 3
                for row in res["rows"]:
                    lat_val = row[lat_idx] if lat_idx < len(row) else None
                    lng_val = row[lng_idx] if lng_idx < len(row) else None
                    try:
                        lat = float(lat_val)
                        lng = float(lng_val)
                        rid = int(row[rid_idx]) if rid_idx < len(row) and row[rid_idx] is not None else 0
                        sid = str(row[sid_idx]) if sid_idx < len(row) and row[sid_idx] is not None else ""
                        cat = sid_name.get(sid, "Unknown")
                        points.append((lat, lng, rid, cat))
                    except (TypeError, ValueError, IndexError):
                        cases_without_gps += 1

        total = len(points) + cases_without_gps

        if points:
            clusters_raw = _dbscan(points, req.eps_km, req.min_cases)
            clusters = []
            for i, cr in enumerate(clusters_raw):
                clusters.append(HotspotClusterDTO(
                    cluster_id=i + 1,
                    centroid_lat=cr["centroid_lat"],
                    centroid_lng=cr["centroid_lng"],
                    case_count=cr["case_count"],
                    radius_km=cr["radius_km"],
                    crime_type=cr["crime_type"],
                    case_ids=cr["case_ids"],
                ))
        else:
            clusters = []

        return HotspotResultDTO(
            query_id=query_id,
            clusters=clusters,
            cases_without_gps=cases_without_gps,
            total_cases_analyzed=total,
            algorithm="DBSCAN",
            algorithm_params=self._fmt_params(req.eps_km, req.min_cases),
        )

    def compute_all_and_store(self, catalyst_app) -> dict:
        """Cron path. Walks every district, writes one snapshot."""
        db = DatastoreClient(catalyst_app)
        repo = ZCQLCaseRepository(db)
        store = self._store or CatalystRowPrecomputedStore(db)

        district_ids = self._all_district_ids(db)
        if not district_ids:
            return {"status": "skipped", "reason": "no districts"}
        per_district: list[dict] = []
        for did in district_ids[:50]:
            req = HotspotRequestDTO(district_id=did)
            res = self.detect(req, repo=repo, db=db)
            per_district.append({
                "district_id": did,
                "clusters": [{"cluster_id": c.cluster_id,
                              "centroid_lat": c.centroid_lat,
                              "centroid_lng": c.centroid_lng,
                              "case_count": c.case_count,
                              "radius_km": c.radius_km,
                              "crime_type": c.crime_type} for c in res.clusters],
                "total": res.total_cases_analyzed,
            })
        payload = {"computed_at": _now_iso(), "districts": per_district}
        store.save_hotspots(payload)
        return {"status": "ok", "districts": len(per_district)}

    def load_all_precomputed(self) -> Optional[dict]:
        return self._store.load_hotspots() if self._store else None

    @staticmethod
    def _all_district_ids(db: DatastoreClient) -> list[int]:
        if not db.is_connected:
            return []
        res = db.execute_non_query("SELECT DistrictID FROM District LIMIT 300")
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


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
