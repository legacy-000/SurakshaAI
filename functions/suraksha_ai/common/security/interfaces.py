"""Narrow security interfaces (Part E.4 — ISP).

The previous ``RBACMiddleware`` was a god-object with ``authorize_action``,
``row_filter_clause``, ``mask_pii``, ``enforce_row_limit``, and
``table_access_allowed`` all on a single class. After ISP:

* ``PermissionChecker`` — only what permission gating needs.
* ``RowScopeProvider`` — only what needs to emit a WHERE clause / row limit.
* ``PIIMasker`` — only what needs to redact PII from response payloads.
* ``AuditEventLogger`` — only what needs to record audit events.

A consumer that only needs, say, PII masking depends on ``PIIMasker`` — not
on all four concerns. ``RBACMiddleware`` remains as a thin composition
facade for the existing ``main.py`` call sites; new code is encouraged to
depend on the narrow interfaces directly.
"""
from abc import ABC, abstractmethod
from typing import Optional

from models.dto import UserContextDTO


class PermissionChecker(ABC):
    """Narrow: can a given user perform a given action?"""

    @abstractmethod
    def can_access(self, user_role: str, action: str, scope: Optional[dict] = None) -> bool: ...


class RowScopeProvider(ABC):
    """Narrow: emit a WHERE clause + row-limit for a user's row-scope."""

    @abstractmethod
    def row_filter_clause(self, user: UserContextDTO) -> str: ...

    @abstractmethod
    def max_rows(self, user_role: str) -> int: ...

    @abstractmethod
    def is_table_allowed(self, user_role: str, table_name: str) -> bool: ...


class PIIMasker(ABC):
    """Narrow: redact PII columns from a response row before sending."""

    @abstractmethod
    def mask(self, row_data: dict, user_role: str) -> dict: ...


class AuditEventLogger(ABC):
    """Narrow: persist an audit event."""

    @abstractmethod
    def log(self, user: Optional[UserContextDTO], action: str, params: dict, result: str) -> None: ...

    @abstractmethod
    def recent(self, limit: int = 100, event_type: Optional[str] = None,
               category: Optional[str] = None, actor: Optional[str] = None) -> list: ...
