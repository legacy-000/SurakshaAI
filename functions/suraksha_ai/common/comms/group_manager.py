import json, uuid
from datetime import datetime, timedelta
from typing import Optional
from models.dto import OrgGroupDTO, DynamicGroupDTO, DynamicGroupMemberDTO, CoordinationRequestDTO


class GroupManager:
    def __init__(self, db=None):
        self._db = db
        self._org_groups = {}
        self._dynamic_groups = {}
        self._memberships = {}
        self._coordination = {}
        self._dg_table = "DynamicGroups"
        self._gm_table = "GroupMembers"
        self._cr_table = "CoordinationRequests"

    def _is_live(self):
        return self._db and self._db.is_connected

    def _load_dynamic_groups(self):
        if not self._is_live():
            return
        for table in [self._dg_table, self._gm_table, self._cr_table]:
            res = self._db.execute_non_query(f"SELECT * FROM {table}")
            if res.get("rows"):
                for row in res["rows"]:
                    d = dict(zip(res["columns"], row))
                    if table == self._dg_table:
                        d["linked_case_ids"] = json.loads(d.get("linked_case_ids_json", "[]"))
                        d["linked_offender_ids"] = json.loads(d.get("linked_offender_ids_json", "[]"))
                        d.pop("linked_case_ids_json", None); d.pop("linked_offender_ids_json", None)
                        g = DynamicGroupDTO(**d)
                        self._dynamic_groups[g.group_id] = g
                    elif table == self._gm_table:
                        self._memberships[f"{d['group_id']}:{d['employee_id']}"] = DynamicGroupMemberDTO(**d)
                    elif table == self._cr_table:
                        d["linked_case_ids"] = json.loads(d.get("linked_case_ids_json", "[]"))
                        d.pop("linked_case_ids_json", None)
                        req = CoordinationRequestDTO(**d)
                        self._coordination[req.request_id] = req

    # ── OrgGroup ──────────────────────────────────────────────────────
    def create_org_group(self, name: str, group_type: str = "STATION", parent_id: str = None) -> OrgGroupDTO:
        g = OrgGroupDTO(group_id=str(uuid.uuid4()), group_name=name, group_type=group_type, parent_group_id=parent_id, created_at=datetime.now().isoformat())
        self._org_groups[g.group_id] = g
        return g

    def get_org_group(self, group_id: str) -> Optional[OrgGroupDTO]:
        return self._org_groups.get(group_id)

    def list_org_groups(self, group_type: str = None) -> list[OrgGroupDTO]:
        if group_type:
            return [g for g in self._org_groups.values() if g.group_type == group_type]
        return list(self._org_groups.values())

    # ── Dynamic Group ─────────────────────────────────────────────────
    def create_dynamic_group(self, name: str, group_type: str = "TASK_FORCE", lead_id: int = 0,
                              case_ids: list[int] = None, offender_ids: list[int] = None,
                              duration_days: int = 90, description: str = None) -> DynamicGroupDTO:
        g = DynamicGroupDTO(
            group_id=str(uuid.uuid4()), group_name=name, group_type=group_type,
            description=description, lead_employee_id=lead_id,
            linked_case_ids=case_ids or [], linked_offender_ids=offender_ids or [],
            dissolve_at=(datetime.now() + timedelta(days=duration_days)).isoformat(),
            created_at=datetime.now().isoformat(),
        )
        if self._is_live():
            self._db.insert_bulk_rows(self._dg_table, [{
                "group_id": g.group_id, "group_name": g.group_name, "group_type": g.group_type,
                "description": g.description or "",
                "lead_employee_id": g.lead_employee_id, "status": g.status,
                "linked_case_ids_json": json.dumps(g.linked_case_ids),
                "linked_offender_ids_json": json.dumps(g.linked_offender_ids),
                "dissolve_at": g.dissolve_at or "", "created_at": g.created_at,
            }])
        self._dynamic_groups[g.group_id] = g
        return g

    def get_dynamic_group(self, group_id: str) -> Optional[DynamicGroupDTO]:
        return self._dynamic_groups.get(group_id)

    def list_dynamic_groups(self, active_only: bool = True) -> list[DynamicGroupDTO]:
        self._load_dynamic_groups()
        results = list(self._dynamic_groups.values())
        if active_only:
            now = datetime.now().isoformat()
            results = [g for g in results if g.status == "active" and (not g.dissolve_at or g.dissolve_at > now)]
        return results

    def dissolve_group(self, group_id: str) -> bool:
        g = self._dynamic_groups.get(group_id)
        if not g:
            return False
        g.status = "dissolved"
        if self._is_live():
            self._db.execute_non_query(f"UPDATE {self._dg_table} SET status='dissolved' WHERE group_id='{group_id.replace(chr(39),chr(39)+chr(39))}'")
        return True

    def add_group_member(self, group_id: str, employee_id: int, role: str = "MEMBER",
                          can_modify: bool = False, can_approve: bool = False, data_scope: str = "group") -> Optional[DynamicGroupMemberDTO]:
        if group_id not in self._dynamic_groups:
            return None
        m = DynamicGroupMemberDTO(membership_id=str(uuid.uuid4()), group_id=group_id, employee_id=employee_id, role=role, can_modify=can_modify, can_approve=can_approve, data_scope=data_scope)
        if self._is_live():
            self._db.insert_bulk_rows(self._gm_table, [{k: (str(v).lower() if isinstance(v, bool) else v) for k, v in m.model_dump().items()}])
        self._memberships[f"{group_id}:{employee_id}"] = m
        return m

    def remove_group_member(self, group_id: str, employee_id: int) -> bool:
        key = f"{group_id}:{employee_id}"
        if key not in self._memberships:
            return False
        del self._memberships[key]
        if self._is_live():
            self._db.execute_non_query(f"DELETE FROM {self._gm_table} WHERE group_id='{group_id.replace(chr(39),chr(39)+chr(39))}' AND employee_id={employee_id}")
        return True

    def get_member(self, group_id: str, employee_id: int) -> Optional[DynamicGroupMemberDTO]:
        return self._memberships.get(f"{group_id}:{employee_id}")

    def list_members(self, group_id: str) -> list[DynamicGroupMemberDTO]:
        self._load_dynamic_groups()
        return [m for k, m in self._memberships.items() if k.startswith(f"{group_id}:")]

    def list_groups_for_employee(self, employee_id: int) -> list[DynamicGroupDTO]:
        self._load_dynamic_groups()
        gids = [k.split(":")[0] for k in self._memberships if k.endswith(f":{employee_id}")]
        return [self._dynamic_groups[gid] for gid in gids if gid in self._dynamic_groups]

    # ── Coordination ──────────────────────────────────────────────────
    def create_coordination(self, from_id: int, to_unit_id: int, req_type: str = "SUSPECT_LOCATION",
                             subject: str = "", body: str = "", case_id: int = None) -> CoordinationRequestDTO:
        req = CoordinationRequestDTO(
            request_id=str(uuid.uuid4()), from_employee_id=from_id, to_unit_id=to_unit_id,
            request_type=req_type, subject=subject, body=body, linked_case_id=case_id,
            created_at=datetime.now().isoformat(),
        )
        if self._is_live():
            self._db.insert_bulk_rows(self._cr_table, [{
                "request_id": req.request_id, "from_employee_id": req.from_employee_id,
                "to_unit_id": req.to_unit_id, "request_type": req.request_type,
                "subject": req.subject, "body": req.body, "linked_case_id": req.linked_case_id,
                "status": req.status, "created_at": req.created_at,
            }])
        self._coordination[req.request_id] = req
        return req

    def get_coordination(self, request_id: str) -> Optional[CoordinationRequestDTO]:
        return self._coordination.get(request_id)

    def update_coordination(self, request_id: str, status: str, assigned_to: int = None) -> bool:
        req = self._coordination.get(request_id)
        if not req:
            return False
        req.status = status
        if assigned_to:
            req.assigned_to_employee_id = assigned_to
        if self._is_live():
            self._db.execute_non_query(f"UPDATE {self._cr_table} SET status='{status.replace(chr(39),chr(39)+chr(39))}' WHERE request_id='{request_id.replace(chr(39),chr(39)+chr(39))}'")
        return True

    def list_coordination(self, from_id: int = None, to_unit: int = None, status: str = None) -> list[CoordinationRequestDTO]:
        self._load_dynamic_groups()
        results = list(self._coordination.values())
        if from_id:
            results = [r for r in results if r.from_employee_id == from_id]
        if to_unit:
            results = [r for r in results if r.to_unit_id == to_unit]
        if status:
            results = [r for r in results if r.status == status]
        return results
