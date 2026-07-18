"""``RBACMiddleware`` — composition facade over the narrow interfaces (Part E.4).

After the ISP refactor, the narrow concerns live in:
  * :class:`DefaultPermissionChecker`  -> can this role do this action?
  * :class:`DefaultRowScopeProvider`   -> WHERE clause / row-limit / table allowlist
  * :class:`DefaultPIIMasker`          -> redact PII for non-authorized roles
  * ``AuditLogger`` (in ``audit_logger.py``) — persistence of audit events

A caller that only needs one concern now depends only on the corresponding
interface. ``RBACMiddleware`` remains for the existing ``main.py`` action
handlers — every public method delegates to the appropriate narrow impl.
"""
import logging

from common.db.datastore_client import DatastoreClient
from common.security.narrow import (
    DefaultPermissionChecker,
    DefaultPIIMasker,
    DefaultRowScopeProvider,
    load_role_overrides_from_db,
)
from common.security.audit_logger import AuditLogger

logger = logging.getLogger(__name__)


class RBACMiddleware:
    def __init__(self, db=None):
        self._db = db if db is not None else DatastoreClient()
        # Try to load overrides exactly once at construction (handles fresh-data
        # permission flips without restarts).
        try:
            load_role_overrides_from_db(self._db)
        except Exception:
            pass
        self._checker = DefaultPermissionChecker()
        self._scope = DefaultRowScopeProvider()
        self._masker = DefaultPIIMasker()
        # Reuse the existing AuditLogger (kept unchanged).
        self.audit = AuditLogger(self._db)

    def get_permissions(self, role_name: str) -> dict:
        """Backward-compat accessor for tests / external introspection."""
        from common.security.narrow import _perms_for
        return _perms_for(role_name)

    def authorize_action(self, user, action: str) -> bool:
        """Delegates to ``DefaultPermissionChecker``."""
        return self._checker.can_access(user.role_name, action)

    def row_filter_clause(self, user) -> str:
        """Delegates to ``DefaultRowScopeProvider``."""
        return self._scope.row_filter_clause(user)

    def enforce_row_limit(self, role_name: str, query_limit: int = None) -> int:
        cap = self._scope.max_rows(role_name)
        if query_limit is None or query_limit > cap:
            return cap
        return query_limit

    def table_access_allowed(self, role_name: str, table_name: str) -> bool:
        """Delegates to ``DefaultRowScopeProvider.is_table_allowed``."""
        return self._scope.is_table_allowed(role_name, table_name)

    def mask_pii(self, row_data: dict, role_name: str) -> dict:
        """Delegates to ``DefaultPIIMasker``."""
        return self._masker.mask(row_data, role_name)
