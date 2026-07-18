from db.datastore_client import DatastoreClient
from unittest.mock import MagicMock
import sys
import os
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BASE)
os.environ.setdefault("PYTHONPATH", BASE)


class TestDatastoreClient:
    def test_not_connected_returns_error(self):
        client = DatastoreClient(catalyst_app=None)
        assert not client.is_connected
        result = client.execute_non_query("SELECT 1")
        assert result["error"] == "DB_NOT_CONNECTED"

    def test_zcql_nested_response_parsing(self):
        mock_app = MagicMock()
        mock_zcql = MagicMock()
        mock_app.zcql.return_value = mock_zcql
        mock_zcql.execute_query.return_value = [
            {"CaseMaster": {"CaseMasterID": 101, "CrimeNo": "CN1"}},
            {"CaseMaster": {"CaseMasterID": 102, "CrimeNo": "CN2"}},
        ]
        client = DatastoreClient(mock_app)
        res = client.execute_non_query("SELECT * FROM CaseMaster")
        assert res["status"] == "success"
        assert res["columns"] == ["CaseMasterID", "CrimeNo"]
        assert res["rows"] == [[101, "CN1"], [102, "CN2"]]

    def test_zcql_empty_response(self):
        mock_app = MagicMock()
        mock_zcql = MagicMock()
        mock_app.zcql.return_value = mock_zcql
        mock_zcql.execute_query.return_value = None
        client = DatastoreClient(mock_app)
        res = client.execute_non_query("SELECT * FROM Empty")
        assert res["status"] == "success"
        assert res["row_count"] == 0

    def test_execute_error_returns_error_dict(self):
        mock_app = MagicMock()
        mock_zcql = MagicMock()
        mock_app.zcql.return_value = mock_zcql
        mock_zcql.execute_query.side_effect = Exception("Connection timeout")
        client = DatastoreClient(mock_app)
        res = client.execute_non_query("SELECT 1")
        assert res["error"] == "DB_EXEC_FAILED"

    def test_zcql_single_row_response(self):
        mock_app = MagicMock()
        mock_zcql = MagicMock()
        mock_app.zcql.return_value = mock_zcql
        mock_zcql.execute_query.return_value = [
            {"CaseMaster": {"CrimeNo": "CN001"}}
        ]
        client = DatastoreClient(mock_app)
        res = client.execute_non_query("SELECT * FROM CaseMaster")
        assert res["status"] == "success"
        assert res["row_count"] == 1

    def test_insert_bulk_not_connected(self):
        client = DatastoreClient(catalyst_app=None)
        res = client.insert_bulk_rows("TestTable", [{"col": "val"}])
        assert res["error"] == "DB_NOT_CONNECTED"
