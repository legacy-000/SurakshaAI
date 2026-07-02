"""
Catalyst Data Store models for SurakshaAI.
Replaces SQLAlchemy ORM models with Zoho Catalyst Data Store SDK.
Each model wraps a Data Store table and provides CRUD operations.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime

from backend.configuration.database import datastore_config


class CatalystDataStoreModel:
    """Base class for Catalyst Data Store backed models."""

    def __init__(self, table_name: str):
        self.table_name = table_name
        self._config = datastore_config

    def create(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        row = self._config.insert_row(self.table_name, data)
        if row is None:
            data["ROWID"] = f"mock_{datetime.now().timestamp()}"
            data["Created_Time"] = datetime.now().isoformat()
            return data
        return row

    def get(self, row_id: str) -> Optional[Dict[str, Any]]:
        return self._config.get_row(self.table_name, row_id)

    def update(self, row_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        row = self._config.update_row(self.table_name, row_id, data)
        if row is None:
            data["ROWID"] = row_id
            data["Modified_Time"] = datetime.now().isoformat()
            return data
        return row

    def delete(self, row_id: str) -> bool:
        return self._config.delete_row(self.table_name, row_id)

    def get_all(self, criteria: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        return self._config.get_rows(self.table_name, criteria)


class User(CatalystDataStoreModel):
    def __init__(self):
        super().__init__("User")


class Case(CatalystDataStoreModel):
    def __init__(self):
        super().__init__("Case")


class Accused(CatalystDataStoreModel):
    def __init__(self):
        super().__init__("Accused")


class Victim(CatalystDataStoreModel):
    def __init__(self):
        super().__init__("Victim")


class Officer(CatalystDataStoreModel):
    def __init__(self):
        super().__init__("Officer")


class CrimePattern(CatalystDataStoreModel):
    def __init__(self):
        super().__init__("CrimePattern")


class Alert(CatalystDataStoreModel):
    def __init__(self):
        super().__init__("Alert")


class Prediction(CatalystDataStoreModel):
    def __init__(self):
        super().__init__("Prediction")


class ChatContext(CatalystDataStoreModel):
    def __init__(self):
        super().__init__("ChatContext")


class Investigation(CatalystDataStoreModel):
    def __init__(self):
        super().__init__("Investigation")


class BehaviorProfile(CatalystDataStoreModel):
    def __init__(self):
        super().__init__("BehaviorProfile")


class TimelineEvent(CatalystDataStoreModel):
    def __init__(self):
        super().__init__("TimelineEvent")
