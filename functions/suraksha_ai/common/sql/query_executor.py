from common.db.datastore_client import DatastoreClient


class QueryExecutor:
    def __init__(self, catalyst_app=None):
        self.client = DatastoreClient(catalyst_app)

    def execute(self, sql_text: str, max_rows: int = 1000, timeout: int = 30) -> dict:
        return self.client.execute_query(sql_text, max_rows, timeout)

    @property
    def is_connected(self):
        return self.client.is_connected
