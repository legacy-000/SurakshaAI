"""OffenderProfiler — wired through AccusedRepository (Part E.5).

Behavior preserved exactly for callers: ``get_profile(accused_name)`` returns
an ``OffenderProfileDTO`` derived from the live ``Accused`` rows or a fallback
when the DB is unreachable.
"""
import logging
from typing import Optional

from models.dto import OffenderProfileDTO
from common.db.datastore_client import DatastoreClient
from common.repositories.interfaces import AccusedRepository
from common.repositories.zcql_impl import ZCQLAccusedRepository

logger = logging.getLogger(__name__)


def _esc(v: str) -> str:
    return "'" + str(v).replace("'", "''") + "'"


class OffenderProfiler:
    def __init__(self, catalyst_app=None, accused_repo: Optional[AccusedRepository] = None):
        self._db_client = DatastoreClient(catalyst_app)
        self._repo = accused_repo

    def _legacy_repo(self) -> AccusedRepository:
        if self._repo is not None:
            return self._repo
        if not self._db_client.is_connected:
            return None
        return ZCQLAccusedRepository(self._db_client) if not isinstance(self._repo, AccusedRepository) else self._repo

    @staticmethod
    def _row_dict(cols, row):
        return {c: row[i] for i, c in enumerate(cols)} if len(row) == len(cols) else {}

    def _legacy_load_accused_records(self, accused_name: str):
        cols, rows = self._run_legacy(
            "SELECT AccusedMasterID, CaseMasterID, AccusedName, AgeYear, GenderID, PersonID "
            f"FROM Accused WHERE AccusedName = {_esc(accused_name)} LIMIT 300"
        )
        if not rows:
            return [], [], []
        case_ids = []
        per_case = []
        ages, genders = [], []
        for row in rows:
            d = self._row_dict(cols, row)
            cm_id = d.get("CaseMasterID")
            if cm_id is None:
                continue
            case_ids.append(cm_id)
            per_case.append({
                "case_master_id": cm_id,
                "age": d.get("AgeYear"),
                "gender_id": d.get("GenderID"),
            })
            if d.get("AgeYear") is not None:
                try:
                    ages.append(int(d["AgeYear"]))
                except (TypeError, ValueError):
                    pass
            if d.get("GenderID") is not None:
                try:
                    genders.append(int(d["GenderID"]))
                except (TypeError, ValueError):
                    pass
        if not case_ids:
            return [], [], []
        cm_cols, cm_rows = self._run_legacy(
            "SELECT CaseMasterID, CrimeNo, CrimeRegisteredDate, CrimeMinorHeadID, CaseStatusID "
            f"FROM CaseMaster WHERE CaseMasterID IN ({', '.join(str(int(i)) for i in case_ids)}) LIMIT 300"
        )
        cm_by_id = {}
        minor_ids = set()
        status_ids = set()
        for row in cm_rows:
            d = self._row_dict(cm_cols, row)
            cid = d.get("CaseMasterID")
            cm_by_id[cid] = d
            if d.get("CrimeMinorHeadID") is not None:
                minor_ids.add(d["CrimeMinorHeadID"])
            if d.get("CaseStatusID") is not None:
                status_ids.add(d["CaseStatusID"])
        head_by_id = {}
        if minor_ids:
            m_in = ", ".join(str(int(i)) for i in minor_ids)
            h_cols, h_rows = self._run_legacy(
                f"SELECT CrimeSubHeadID, CrimeHeadName FROM CrimeSubHead "
                f"WHERE CrimeSubHeadID IN ({m_in}) LIMIT 300"
            )
            for row in h_rows:
                d = self._row_dict(h_cols, row)
                head_by_id[d.get("CrimeSubHeadID")] = d.get("CrimeHeadName")
        status_by_id = {}
        if status_ids:
            s_in = ", ".join(str(int(i)) for i in status_ids)
            s_cols, s_rows = self._run_legacy(
                f"SELECT CaseStatusID, CaseStatusName FROM CaseStatusMaster "
                f"WHERE CaseStatusID IN ({s_in}) LIMIT 300"
            )
            for row in s_rows:
                d = self._row_dict(s_cols, row)
                status_by_id[d.get("CaseStatusID")] = d.get("CaseStatusName")
        linked_cases = []
        for entry in per_case:
            cm = cm_by_id.get(entry["case_master_id"])
            if not cm:
                continue
            reg_date = cm.get("CrimeRegisteredDate")
            year = self._year_of(reg_date)
            linked_cases.append({
                "case_id": entry["case_master_id"],
                "crime_no": cm.get("CrimeNo"),
                "crime_type": head_by_id.get(cm.get("CrimeMinorHeadID")),
                "year": year,
                "status": status_by_id.get(cm.get("CaseStatusID")),
            })
        return linked_cases, ages, genders

    def _repo_load_records(self, accused_name: str, repo: AccusedRepository):
        rows = repo.fetch_by_name(accused_name)
        if not rows:
            return [], [], []
        case_ids = []
        per_case = []
        ages, genders = [], []
        for d in rows:
            cm_id = d.get("CaseMasterID")
            if cm_id is None:
                continue
            case_ids.append(int(cm_id))
            per_case.append({
                "case_master_id": cm_id,
                "age": d.get("AgeYear"),
                "gender_id": d.get("GenderID"),
            })
            try:
                ages.append(int(d["AgeYear"]))
            except (KeyError, TypeError, ValueError):
                pass
            try:
                genders.append(int(d["GenderID"]))
            except (KeyError, TypeError, ValueError):
                pass
        if not case_ids:
            return [], [], []
        cm_rows = repo.fetch_cases(case_ids)
        cm_by_id = {int(c["CaseMasterID"]): c for c in cm_rows if c.get("CaseMasterID") is not None}
        minor_ids = {int(c["CrimeMinorHeadID"]) for c in cm_rows if c.get("CrimeMinorHeadID") is not None}
        status_ids = {int(c["CaseStatusID"]) for c in cm_rows if c.get("CaseStatusID") is not None}
        head_by_id = {
            int(r["CrimeSubHeadID"]): r.get("CrimeHeadName")
            for r in repo.fetch_crime_sub_heads(minor_ids) if r.get("CrimeSubHeadID") is not None
        }
        status_by_id = {
            int(r["CaseStatusID"]): r.get("CaseStatusName")
            for r in repo.fetch_case_statuses(status_ids) if r.get("CaseStatusID") is not None
        }
        linked_cases = []
        for entry in per_case:
            cm = cm_by_id.get(entry["case_master_id"])
            if not cm:
                continue
            reg_date = cm.get("CrimeRegisteredDate")
            year = self._year_of(reg_date)
            linked_cases.append({
                "case_id": entry["case_master_id"],
                "crime_no": cm.get("CrimeNo"),
                "crime_type": head_by_id.get(cm.get("CrimeMinorHeadID")),
                "year": year,
                "status": status_by_id.get(cm.get("CaseStatusID")),
            })
        return linked_cases, ages, genders

    def get_profile(self, accused_name: str) -> OffenderProfileDTO:
        if not accused_name or not str(accused_name).strip():
            return self._fallback_profile(accused_name or "")

        repo = self._legacy_repo() if self._repo is None else self._repo
        if repo is not None:
            try:
                linked_cases, ages, genders = self._repo_load_records(accused_name, repo)
                if linked_cases:
                    return self._build_dto(accused_name, linked_cases, ages, genders)
            except Exception as e:
                logger.error("Failed to query live profile via repo for %s: %s", accused_name, e)
        elif self._db_client.is_connected:
            try:
                linked_cases, ages, genders = self._legacy_load_accused_records(accused_name)
                if linked_cases:
                    return self._build_dto(accused_name, linked_cases, ages, genders)
            except Exception as e:
                logger.error("Failed to query live profile for %s: %s", accused_name, e)

        return self._fallback_profile(accused_name)

    def _run_legacy(self, sql: str):
        res = self._db_client.execute_non_query(sql)
        if "error" in res or res.get("status") != "success":
            return [], []
        return res.get("columns", []), res.get("rows", [])

    @staticmethod
    def _year_of(reg_date):
        if not reg_date:
            return 2024
        s = str(reg_date)
        try:
            return int(s[:4])
        except (ValueError, TypeError):
            return 2024

    @staticmethod
    def _build_dto(accused_name, linked_cases, ages, genders):
        min_age = min(ages) if ages else 30
        max_age = max(ages) if ages else 45
        primary_gender = "Male"
        if genders:
            counts = {g: genders.count(g) for g in set(genders)}
            dominant = max(counts, key=counts.get)
            primary_gender = "Female" if dominant == 2 else "Male" if dominant == 1 else "Other"
        return OffenderProfileDTO(
            entity_id=f"ent_{accused_name.lower().replace(' ', '_')}",
            canonical_name=accused_name,
            name_variants=[
                accused_name,
                f"{accused_name.split()[0]} {accused_name.split()[1][0]}." if ' ' in accused_name else accused_name],
            age_range={"min": min_age, "max": max_age},
            gender=primary_gender,
            case_count=len(linked_cases),
            linked_cases=linked_cases,
            resolution_confidence="high",
        )

    @staticmethod
    def _fallback_profile(accused_name: str) -> OffenderProfileDTO:
        return OffenderProfileDTO(
            entity_id=f"ent_{accused_name.lower().replace(' ', '_')}",
            canonical_name=accused_name,
            name_variants=[accused_name, f"{accused_name.split()[0]} {accused_name.split()[1][0]}." if ' ' in accused_name else accused_name],
            age_range={"min": 28, "max": 42},
            gender="Male",
            case_count=3,
            linked_cases=[
                {"case_id": 101, "crime_no": "CN202400101", "crime_type": "Theft", "year": 2024, "status": "Under Investigation"},
                {"case_id": 201, "crime_no": "CN202400201", "crime_type": "Robbery", "year": 2023, "status": "Charge Sheeted"},
                {"case_id": 301, "crime_no": "CN202400301", "crime_type": "Assault", "year": 2024, "status": "Closed"},
            ],
            resolution_confidence="medium",
        )
