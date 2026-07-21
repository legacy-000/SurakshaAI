from common.db.datastore_client import DatastoreClient


class QueryExecutor:
    def __init__(self, catalyst_app=None):
        self.client = DatastoreClient(catalyst_app)

    def execute(self, sql_text: str, max_rows=1000, timeout=30) -> dict:
        return self.client.execute_non_query(sql_text)

    def execute_non_query(self, sql_text: str) -> dict:
        return self.client.execute_non_query(sql_text)

    @property
    def is_connected(self):
        return self.client.is_connected
