"""
Mock Catalyst Data Store session that mimics SQLAlchemy Session interface
for compatibility with existing repository/controller/service code.
"""
from typing import Any, List, Optional, Type, TypeVar, Generic
from unittest.mock import MagicMock

T = TypeVar("T")


class MockQuery:
    """Mimics SQLAlchemy Query with chainable filter/offset/limit."""
    def __init__(self, model: Type[T], data: Optional[List[T]] = None):
        self._model = model
        self._data = data or []
        self._filtered = self._data

    def filter(self, *args, **kwargs):
        return self

    def filter_by(self, **kwargs):
        return self

    def offset(self, n: int):
        return self

    def limit(self, n: int):
        return self

    def order_by(self, *args):
        return self

    def first(self) -> Optional[T]:
        return self._filtered[0] if self._filtered else None

    def all(self) -> List[T]:
        return self._filtered

    def count(self) -> int:
        return len(self._filtered)

    def __iter__(self):
        return iter(self._filtered)


class MockSession:
    """Duck-typed replacement for sqlalchemy.orm.Session using Catalyst Data Store
    where available, otherwise returning mock/empty results."""

    def __init__(self, datastore_config=None):
        self._ds = datastore_config
        self._committed = False

    def query(self, model: Type[T], *args) -> MockQuery:
        return MockQuery(model)

    def add(self, instance):
        pass

    def add_all(self, instances):
        pass

    def delete(self, instance):
        pass

    def merge(self, instance):
        return instance

    def commit(self):
        self._committed = True

    def rollback(self):
        self._committed = False

    def flush(self):
        pass

    def close(self):
        pass

    def refresh(self, instance):
        pass

    def execute(self, statement, params=None, **kwargs):
        return MagicMock()

    def scalar(self, statement, params=None, **kwargs):
        return None

    @property
    def is_active(self):
        return True

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
