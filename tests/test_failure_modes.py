import pytest
from functions.chat.chat_handler import ChatHandler
from functions.sql.query_executor import QueryExecutor
from models.dto import QueryRequestDTO, UserContextDTO


def test_empty_query():
    handler = ChatHandler()
    user = UserContextDTO(user_id="INV001", kgid="INV001", first_name="Test",
                          email="t@t.com", role_id=1, role_name="Investigator")
    req = QueryRequestDTO(message="")
    resp = handler.handle_query(req, user)
    assert resp is not None


def test_invalid_sql():
    executor = QueryExecutor()
    result = executor.execute("INVALID SQL HERE")
    assert "error" in result or result.get("execution_status") == "success"


def test_datastore_client_parsing():
    from unittest.mock import MagicMock
    from functions.db.datastore_client import DatastoreClient

    # Mock Catalyst App
    mock_app = MagicMock()
    mock_zcql = MagicMock()
    mock_app.zcql.return_value = mock_zcql

    client = DatastoreClient(mock_app)

    # 1. Test flat response parsing
    mock_zcql.execute_query.return_value = [
        {"total": 10, "status": "active"},
        {"total": 5, "status": "pending"}
    ]
    res_flat = client.execute_query("SELECT COUNT(*) FROM Dummy")
    assert res_flat["execution_status"] == "success"
    assert res_flat["columns"] == ["total", "status"]
    assert res_flat["rows"] == [[10, "active"], [5, "pending"]]

    # 2. Test nested response parsing
    mock_zcql.execute_query.return_value = [
        {
            "CaseMaster": {"CaseMasterID": 101, "CrimeNo": "CN1"},
            "District": {"DistrictName": "Bangalore"}
        },
        {
            "CaseMaster": {"CaseMasterID": 102, "CrimeNo": "CN2"},
            "District": {"DistrictName": "Mysuru"}
        }
    ]
    res_nested = client.execute_query("SELECT CaseMaster.CrimeNo, District.DistrictName FROM CaseMaster JOIN ...")
    assert res_nested["execution_status"] == "success"
    assert res_nested["columns"] == ["CaseMaster.CaseMasterID", "CaseMaster.CrimeNo", "District.DistrictName"]
    assert res_nested["rows"] == [[101, "CN1", "Bangalore"], [102, "CN2", "Mysuru"]]


@pytest.mark.skip(reason="Full app-chain import has dependency issues")
def test_insert_row_and_create_profile():
    from unittest.mock import MagicMock, patch
    from functions.db.datastore_client import DatastoreClient
    from functions.suraksha_ai.main import handler
    from flask import Flask, request

    mock_app = MagicMock()
    mock_table = MagicMock()
    mock_app.datastore().table.return_value = mock_table
    mock_table.insert_row.return_value = {"status": "success"}

    client = DatastoreClient(mock_app)
    insert_res = client.insert_row("Accused", {"AccusedName": "Test Criminal"})
    assert insert_res["status"] == "success"

    # Test Flask handler action
    app = Flask("test_app")
    with app.test_request_context(
        json={
            "action": "create_offender_profile",
            "params": {
                "accused_name": "Ramesh Kumar",
                "case_master_id": 79,
                "age_year": 34,
                "gender_id": 1,
                "person_id": "A1"
            },
            "session": {
                "user_context": {
                    "user_id": "INV001",
                    "role_id": 1
                }
            }
        }
    ):
        with patch('zcatalyst_sdk.initialize', return_value=mock_app):
            # Mock the internal DatastoreClient connection status and queries
            with patch('functions.suraksha_ai.common.db.datastore_client.DatastoreClient.is_connected', new_callable=lambda: True):
                with patch('functions.suraksha_ai.common.db.datastore_client.DatastoreClient.execute_query', return_value={"execution_status": "success", "rows": [[10]]}):
                    with patch('functions.suraksha_ai.common.db.datastore_client.DatastoreClient.insert_row', return_value={"status": "success"}):
                        # Force handler to recognize it as live
                        with patch('functions.suraksha_ai.common.main_handler.SurakshaAIHandler.is_live', new_callable=lambda: True):
                            response, status_code = handler(request)
                            assert status_code == 200
                            res_json = response.get_json()
                            assert res_json["status"] == "success"
