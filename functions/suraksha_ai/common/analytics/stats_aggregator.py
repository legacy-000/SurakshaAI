from models.dto import DashboardStatsDTO


def _scalar_count(res: dict) -> int:
    if "error" in res or res.get("row_count", 0) <= 0:
        return 0
    try:
        return int(res["rows"][0][0])
    except (TypeError, ValueError, IndexError):
        return 0


def _rows_as_dicts(res: dict) -> list[dict]:
    cols = res.get("columns", []) or []
    out = []
    for row in res.get("rows", []) or []:
        if len(row) == len(cols):
            out.append(dict(zip(cols, row)))
    return out


class StatsAggregator:
    def get_dashboard_stats(self, user_scope: dict = None, db=None) -> DashboardStatsDTO:
        if db is not None and hasattr(db, 'is_connected') and db.is_connected:
            case_where = []
            if user_scope and user_scope.get("district_id"):
                units = db.execute_non_query(
                    f"SELECT UnitID FROM Unit WHERE DistrictID = {int(user_scope['district_id'])} LIMIT 300"
                )
                station_ids = [
                    int(r["UnitID"]) for r in _rows_as_dicts(units)
                    if r.get("UnitID") is not None
                ]
                if not station_ids:
                    return DashboardStatsDTO(district_count=0, station_count=0)
                case_where.append(
                    "PoliceStationID IN (" + ", ".join(str(i) for i in station_ids) + ")"
                )
            where_sql = " WHERE " + " AND ".join(case_where) if case_where else ""

            total_cases = _scalar_count(db.execute_non_query(
                f"SELECT COUNT(ROWID) FROM CaseMaster{where_sql}"
            ))

            heinous_where = case_where + ["CaeCategoryID = 1"]
            heinous_sql = " WHERE " + " AND ".join(heinous_where)
            heinous_cnt = _scalar_count(db.execute_non_query(
                f"SELECT COUNT(ROWID) FROM CaseMaster{heinous_sql}"
            ))
            heinous_pct = round(heinous_cnt / total_cases * 100, 1) if total_cases > 0 else 0.0

            status_res = db.execute_non_query(
                "SELECT CaseStatusID FROM CaseStatusMaster WHERE CaseStatusName = 'Under Investigation' LIMIT 10"
            )
            pending_ids = [
                int(r["CaseStatusID"]) for r in _rows_as_dicts(status_res)
                if r.get("CaseStatusID") is not None
            ]
            pending = 0
            if pending_ids:
                pending_where = case_where + [
                    "CaseStatusID IN (" + ", ".join(str(i) for i in pending_ids) + ")"
                ]
                pending_sql = " WHERE " + " AND ".join(pending_where)
                pending = _scalar_count(db.execute_non_query(
                    f"SELECT COUNT(ROWID) FROM CaseMaster{pending_sql}"
                ))

            district_count = _scalar_count(db.execute_non_query("SELECT COUNT(ROWID) FROM District"))
            station_count = _scalar_count(db.execute_non_query("SELECT COUNT(ROWID) FROM Unit"))

            return DashboardStatsDTO(
                total_cases=total_cases,
                heinous_pct=heinous_pct,
                pending_cases=pending,
                district_count=district_count,
                station_count=station_count,
            )

        raise RuntimeError("get_dashboard_stats: no DB connection")
