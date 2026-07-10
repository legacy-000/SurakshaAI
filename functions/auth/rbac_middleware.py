from models.dto import UserContextDTO, AuthorizationScopeDTO
from config.constants import (
    ROLE_INVESTIGATOR, ROLE_ANALYST, ROLE_SUPERVISOR,
    ROLE_POLICYMAKER, ROLE_SYSTEM_ADMIN
)


class RBACMiddleware:
    def __init__(self):
        self._role_permissions = {
            1: {  # Investigator
                "permitted_apis": ["CHAT", "CASE", "NET", "PROF", "INV", "EXP"],
                "permitted_screens": ["chat", "network", "workspace", "hotspots"],
                "permitted_tables": ["CaseMaster", "Accused", "Victim", "ComplainantDetails",
                                    "ArrestSurrender", "ChargesheetDetails", "ActSectionAssociation"],
                "can_view_sql": True, "can_export_pdf": True, "can_view_pii": True
            },
            2: {  # Analyst
                "permitted_apis": ["CHAT", "ANL", "NET", "PROF", "FIN", "FC"],
                "permitted_screens": ["chat", "analytics", "network", "sociological", "forecast", "financial"],
                "permitted_tables": ["CaseMaster", "Accused", "Victim", "ComplainantDetails",
                                    "CrimeHead", "CrimeSubHead", "ArrestSurrender"],
                "can_view_sql": True, "can_export_pdf": True, "can_view_pii": False
            },
            3: {  # Supervisor
                "permitted_apis": ["CHAT", "CASE", "NET", "AL", "INV", "EXP"],
                "permitted_screens": ["chat", "network", "workspace", "alerts", "dashboard"],
                "permitted_tables": ["CaseMaster", "Accused", "Unit", "Employee"],
                "can_view_sql": True, "can_export_pdf": True, "can_view_pii": True
            },
            4: {  # Policymaker
                "permitted_apis": ["CHAT", "ANL", "FC", "FIN"],
                "permitted_screens": ["chat", "analytics", "forecast", "sociological", "dashboard"],
                "permitted_tables": ["CaseMaster", "CrimeHead", "CrimeSubHead"],
                "can_view_sql": False, "can_export_pdf": True, "can_view_pii": False
            },
            5: {  # System Administrator
                "permitted_apis": ["ALL"],
                "permitted_screens": ["ALL"],
                "permitted_tables": ["ALL"],
                "can_view_sql": True, "can_export_pdf": True, "can_view_pii": True,
                "can_manage_users": True
            }
        }

    def resolve_user(self, kgid: str) -> UserContextDTO:
        mock_users = {
            "INV001": {"kgid": "INV001", "name": "Ravi Kumar", "role": 1, "unit": 1, "district": 1},
            "ANL001": {"kgid": "ANL001", "name": "Priya Sharma", "role": 2, "unit": 2, "district": 18},
            "SUP001": {"kgid": "SUP001", "name": "Amit Singh", "role": 3, "unit": 1, "district": 1},
            "POL001": {"kgid": "POL001", "name": "Suresh Reddy", "role": 4},
            "ADM001": {"kgid": "ADM001", "name": "Admin User", "role": 5}
        }
        u = mock_users.get(kgid)
        if not u:
            return None
        return UserContextDTO(
            user_id=kgid, kgid=kgid, first_name=u["name"],
            email=f"{kgid.lower()}@ksp.gov.in", role_id=u["role"],
            role_name=self._get_role_name(u["role"]),
            unit_id=u.get("unit"), district_id=u.get("district")
        )

    def get_authorization_scope(self, user: UserContextDTO) -> AuthorizationScopeDTO:
        perms = self._role_permissions.get(user.role_id, self._role_permissions[1])
        scope = AuthorizationScopeDTO(
            user_id=user.user_id, role_id=user.role_id,
            permitted_apis=perms["permitted_apis"],
            permitted_screens=perms["permitted_screens"],
            permitted_tables=perms["permitted_tables"],
            can_view_sql=perms["can_view_sql"],
            can_export_pdf=perms["can_export_pdf"],
            can_view_pii=perms["can_view_pii"]
        )
        if user.district_id:
            scope.row_scope_type = "district"
            scope.row_scope_value = user.district_id
        return scope

    def check_api_access(self, scope: AuthorizationScopeDTO, api_id: str) -> bool:
        if "ALL" in scope.permitted_apis:
            return True
        prefix = api_id.split("-")[0] if "-" in api_id else api_id.split("_")[0]
        for p in scope.permitted_apis:
            if api_id.startswith(p) or prefix == p:
                return True
        return False

    def _get_role_name(self, role_id: int) -> str:
        mapping = {1: ROLE_INVESTIGATOR, 2: ROLE_ANALYST, 3: ROLE_SUPERVISOR,
                   4: ROLE_POLICYMAKER, 5: ROLE_SYSTEM_ADMIN}
        return mapping.get(role_id, ROLE_INVESTIGATOR)
