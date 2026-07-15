"""Self-check tests for Phase 6 — Technical Support Engineer Role."""

import sys, os
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BASE)
os.environ.setdefault("PYTHONPATH", BASE)

from models.dto import UserContextDTO, LoginRequestDTO
from auth.auth_handler import AuthHandler
from security.rbac_middleware import RBACMiddleware, CASE_DATA_TABLES
from support.tse_handler import TSEHandler


def test_tse_auth_login():
    auth = AuthHandler()
    res = auth.login(LoginRequestDTO(kgid="TSE001", password="pass123"))
    assert "token" in res
    assert res["user"]["role_name"] == "Technical Support Engineer"
    print("  PASS: tse_auth_login")


def test_tse_auth_verify():
    auth = AuthHandler()
    res = auth.login(LoginRequestDTO(kgid="TSE001", password="pass123"))
    uc = auth.verify_token(res["token"])
    assert uc is not None
    assert uc.role_name == "Technical Support Engineer"
    assert uc.kgid == "TSE001"
    print("  PASS: tse_auth_verify")


def test_tse_rbac_authorized_actions():
    rbac = RBACMiddleware()
    user = UserContextDTO(user_id="TSE001", kgid="TSE001", first_name="Anita", email="",
                          role_id=6, role_name="Technical Support Engineer")
    assert rbac.authorize_action(user, "tse_schema_tables")
    assert rbac.authorize_action(user, "tse_schema_columns")
    assert rbac.authorize_action(user, "tse_explain_query")
    assert rbac.authorize_action(user, "tse_constraint_check")
    assert rbac.authorize_action(user, "tse_system_metrics")
    assert rbac.authorize_action(user, "tse_active_sessions")
    assert rbac.authorize_action(user, "tse_index_stats")
    assert rbac.authorize_action(user, "tse_error_logs")
    assert rbac.authorize_action(user, "tse_cache_stats")
    assert rbac.authorize_action(user, "tse_auth_tokens")
    assert rbac.authorize_action(user, "tse_validate_sql")
    assert rbac.authorize_action(user, "list_audit_log")
    print("  PASS: tse_rbac_authorized_actions")


def test_tse_rbac_denied_data_actions():
    rbac = RBACMiddleware()
    user = UserContextDTO(user_id="TSE001", kgid="TSE001", first_name="Anita", email="",
                          role_id=6, role_name="Technical Support Engineer")
    assert not rbac.authorize_action(user, "chat_query"), "TSE cannot query case data"
    assert not rbac.authorize_action(user, "get_crime_stats"), "TSE cannot get stats"
    assert not rbac.authorize_action(user, "get_case_similarity"), "TSE cannot access similarity"
    assert not rbac.authorize_action(user, "get_offender_profile"), "TSE cannot access offender profiles"
    assert not rbac.authorize_action(user, "get_case_timeline"), "TSE cannot access timelines"
    assert not rbac.authorize_action(user, "get_case_leads"), "TSE cannot access leads"
    assert not rbac.authorize_action(user, "send_message"), "TSE cannot send comms"
    assert not rbac.authorize_action(user, "create_coordination"), "TSE cannot coordinate"
    assert not rbac.authorize_action(user, "import_table"), "TSE cannot import data"
    assert not rbac.authorize_action(user, "create_dynamic_group"), "TSE cannot manage groups"
    print("  PASS: tse_rbac_denied_data_actions")


def test_tse_table_access_allowed():
    rbac = RBACMiddleware()
    user = UserContextDTO(user_id="TSE001", kgid="TSE001", first_name="Anita", email="",
                          role_id=6, role_name="Technical Support Engineer")
    for tbl in CASE_DATA_TABLES:
        assert not rbac.table_access_allowed(user.role_name, tbl), f"TSE denied access to {tbl}"
    assert rbac.table_access_allowed(user.role_name, "information_schema.columns"), "TSE can access metadata tables"
    assert rbac.table_access_allowed(user.role_name, "pg_stat_activity"), "TSE can access pg stats"
    assert rbac.table_access_allowed(user.role_name, "AuditLog"), "TSE can access audit log"
    print("  PASS: tse_table_access_allowed")


def test_tse_handler_schema_tables():
    h = TSEHandler()
    res = h.schema_tables()
    assert "tables" in res
    assert len(res["tables"]) > 0
    print("  PASS: tse_handler_schema_tables")


def test_tse_handler_schema_columns():
    h = TSEHandler()
    res = h.schema_columns("CaseMaster")
    assert "columns" in res
    assert len(res["columns"]) > 0
    print("  PASS: tse_handler_schema_columns")


def test_tse_handler_validate_sql():
    h = TSEHandler()
    res = h.validate_sql("SELECT * FROM CaseMaster")
    assert res["valid"] is True
    assert len(res["issues"]) == 0
    print("  PASS: tse_handler_validate_sql_valid")


def test_tse_handler_validate_sql_ddl_rejected():
    h = TSEHandler()
    res = h.validate_sql("DROP TABLE CaseMaster")
    assert res["valid"] is False
    assert any("DDL/DML" in i for i in res["issues"])
    print("  PASS: tse_handler_validate_sql_ddl_rejected")


def test_tse_handler_error_logs():
    h = TSEHandler()
    res = h.error_logs(5)
    assert "errors" in res
    print("  PASS: tse_handler_error_logs")


def test_tse_handler_constraint_check():
    h = TSEHandler()
    res = h.constraint_check()
    assert "status" in res
    print("  PASS: tse_handler_constraint_check")


def test_tse_handler_system_metrics():
    h = TSEHandler()
    res = h.system_metrics()
    assert "status" in res or "metrics" in res
    print("  PASS: tse_handler_system_metrics")


def test_tse_handler_active_sessions():
    h = TSEHandler()
    res = h.active_sessions()
    assert "sessions" in res
    print("  PASS: tse_handler_active_sessions")


def test_tse_handler_cache_stats():
    h = TSEHandler()
    res = h.cache_stats()
    assert "hit_rate" in res
    print("  PASS: tse_handler_cache_stats")


def test_tse_handler_auth_tokens():
    h = TSEHandler()
    res = h.auth_tokens()
    assert "tokens" in res
    print("  PASS: tse_handler_auth_tokens")


def test_tse_scope_state():
    rbac = RBACMiddleware()
    user = UserContextDTO(user_id="TSE001", kgid="TSE001", first_name="Anita", email="",
                          role_id=6, role_name="Technical Support Engineer")
    clause = rbac.row_filter_clause(user)
    assert clause == "", "TSE has state scope (no filter clause)"
    print("  PASS: tse_scope_state")


def test_tse_max_rows():
    rbac = RBACMiddleware()
    assert rbac.enforce_row_limit("Technical Support Engineer", 500) == 100
    assert rbac.enforce_row_limit("Technical Support Engineer", 50) == 50
    print("  PASS: tse_max_rows")


def test_tse_pii_masked():
    rbac = RBACMiddleware()
    row = {"VictimName": "Sita", "CaseMasterID": 42, "BriedFacts": "Armed robbery"}
    masked = rbac.mask_pii(row, "Technical Support Engineer")
    assert masked["VictimName"] == "*** MASKED ***"
    assert masked["CaseMasterID"] == 42  # non-PII untouched
    assert masked["BriedFacts"] == "Armed robbery"  # non-PII, not masked
    print("  PASS: tse_pii_masked")
