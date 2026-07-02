"""
Catalyst Data Store configuration for SurakshaAI.
Replaces PostgreSQL + SQLAlchemy with Zoho Catalyst Data Store.
"""
import os
from typing import Any, Dict, List, Optional

try:
    from catalyst import Catalyst
    from catalyst.datastore import DataStore
    CATALYST_AVAILABLE = True
except ImportError:
    CATALYST_AVAILABLE = False


class CatalystDataStoreConfig:
    """Configuration and accessor for Catalyst Data Store."""

    def __init__(self):
        self.app = None
        self.datastore = None
        self._initialize()

    def _initialize(self):
        if CATALYST_AVAILABLE:
            try:
                self.app = Catalyst.initialize()
                self.datastore = DataStore(self.app)
            except Exception as e:
                print(f"Error initializing Catalyst Data Store: {e}")
        else:
            print("Catalyst SDK not available. Using mock Data Store.")

    def get_table(self, table_name: str):
        if self.datastore:
            try:
                return self.datastore.table(table_name)
            except Exception as e:
                print(f"Error accessing table {table_name}: {e}")
        return None

    def insert_row(self, table_name: str, row_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        table = self.get_table(table_name)
        if table:
            try:
                return table.insert_row(row_data)
            except Exception as e:
                print(f"Error inserting row into {table_name}: {e}")
        return row_data

    def get_row(self, table_name: str, row_id: str) -> Optional[Dict[str, Any]]:
        table = self.get_table(table_name)
        if table:
            try:
                return table.get_row(row_id)
            except Exception as e:
                print(f"Error getting row from {table_name}: {e}")
        return None

    def update_row(self, table_name: str, row_id: str, row_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        table = self.get_table(table_name)
        if table:
            try:
                return table.update_row(row_id, row_data)
            except Exception as e:
                print(f"Error updating row in {table_name}: {e}")
        return row_data

    def delete_row(self, table_name: str, row_id: str) -> bool:
        table = self.get_table(table_name)
        if table:
            try:
                table.delete_row(row_id)
                return True
            except Exception as e:
                print(f"Error deleting row from {table_name}: {e}")
        return True

    def get_rows(self, table_name: str, criteria: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        table = self.get_table(table_name)
        if table:
            try:
                if criteria:
                    return table.get_rows(criteria)
                return table.get_rows()
            except Exception as e:
                print(f"Error getting rows from {table_name}: {e}")
        return []


datastore_config = CatalystDataStoreConfig()
