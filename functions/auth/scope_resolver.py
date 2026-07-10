from models.dto import UserContextDTO, AuthorizationScopeDTO
from functions.auth.rbac_middleware import RBACMiddleware


class ScopeResolver:
    def __init__(self):
        self._rbac = RBACMiddleware()

    def resolve_scope(self, user: UserContextDTO) -> AuthorizationScopeDTO:
        return self._rbac.get_authorization_scope(user)

    def get_row_scope_predicate(self, scope: AuthorizationScopeDTO, table_alias: str = "cm") -> str:
        if not scope.row_scope_type or not scope.row_scope_value:
            return "1=1"
        if scope.row_scope_type == "district":
            return f"{table_alias}.DistrictID = {scope.row_scope_value}"
        if scope.row_scope_type == "station":
            return f"{table_alias}.PoliceStationID = {scope.row_scope_value}"
        if scope.is_aggregate_scope:
            return "1=1"
        return "1=1"
