"""
Catalyst Data Store configuration for SurakshaAI.
Replaces SQLAlchemy/PostgreSQL with Zoho Catalyst Data Store NoSQL.
"""
import os
from typing import Dict, Any, Optional

try:
    from catalyst import Catalyst
    from catalyst.datastore import DataStore
    catalyst_available = True
except ImportError:
    catalyst_available = False


class CatalystDataStoreConfig:
    """Configuration for Catalyst Data Store."""
    
    def __init__(self):
        self.app = None
        self.datastore = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Catalyst app and datastore."""
        if catalyst_available:
            try:
                self.app = Catalyst.initialize()
                self.datastore = DataStore(self.app)
            except Exception as e:
                print(f"Error initializing Catalyst Data Store: {e}")
        else:
            print("Warning: Catalyst SDK not available. Using mock configuration.")
    
    def get_datastore(self) -> Optional[Any]:
        """Get the datastore instance."""
        return self.datastore
    
    def get_table(self, table_name: str) -> Optional[Any]:
        """Get a specific table from datastore."""
        if self.datastore:
            return self.datastore.table(table_name)
        return None
    
    def create_table(self, table_name: str, schema: Dict[str, Any]) -> bool:
        """Create a table with specified schema."""
        if self.datastore:
            try:
                self.datastore.create_table(table_name, schema)
                return True
            except Exception as e:
                print(f"Error creating table {table_name}: {e}")
        return False


# Singleton instance
datastore_config = CatalystDataStoreConfig()
