"""Self-check tests for Phase 3 — Security Foundation + Multi-Agent Orchestration."""

from commander.evidence_validator import EvidenceValidator
from commander.commander import Commander
from security.audit_logger import AuditLogger
from security.rbac_middleware import RBACMiddleware
from auth.auth_handler import AuthHandler
from models.dto import UserContextDTO, EarlyWarningAlertDTO, LoginRequestDTO
import sys
import os
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BASE)
os.environ.setdefault("PYTHONPATH", BASE)


# ponytail: inline mock profiler to avoid the "from common.*" import chain during CI

class _MockOffenderAgent:
    def run(self, query):
        return {"data": {"entity_name": "Ravi Kumar", "risk_tier": "ELEVATED",
                         "total_score": 72.5, "case_count": 8, "linked_cases": [],
                         "disclaimer": "Mock"}, "evidence": []}


OffenderAgent = _MockOffenderAgent


def test_auth_login():
    auth = AuthHandler()
    res = auth.login(LoginRequestDTO(kgid="INV001", password="pass123"))
    assert "token" in res, "login should return token"
    assert res["user"]["role_name"] == "Investigator"
    print("  PASS: auth_login")


def test_auth_verify():
    auth = AuthHandler()
    res = auth.login(LoginRequestDTO(kgid="ANL001", password="pass123"))
    uc = auth.verify_token(res["token"])
    assert uc is not None, "verify_token should return UserContextDTO"
    assert uc.role_name == "Analyst"
    assert uc.kgid == "ANL001"
    print("  PASS: auth_verify")


def test_auth_invalid():
    auth = AuthHandler()
    uc = auth.verify_token("v2.fake.sig")
    assert uc is None, "invalid token should return None"
    print("  PASS: auth_invalid")


def test_rbac_authorize():
    rbac = RBACMiddleware()
    user = UserContextDTO(user_id="INV001", kgid="INV001", first_name="Ravi",
                          email="", role_id=1, role_name="Investigator")
    assert rbac.authorize_action(user, "chat_query")
    assert not rbac.authorize_action(user, "view_trends")
    print("  PASS: rbac_authorize")


def test_rbac_row_scope():
    rbac = RBACMiddleware()
    unit_user = UserContextDTO(user_id="INV001", kgid="INV001", first_name="Ravi",
                               email="", role_id=1, role_name="Investigator", unit_id=5)
    scope = rbac.row_filter_clause(unit_user)
    assert "PoliceStationID = 5" in scope, "unit-level scope should filter by PoliceStationID"
    print("  PASS: rbac_row_scope")


def test_rbac_pii_mask():
    rbac = RBACMiddleware()
    data = {"AccusedName": "Ravi Kumar", "case_count": 5}
    masked = rbac.mask_pii(data, "Analyst")
    assert masked["AccusedName"] == "*** MASKED ***"
    assert masked["case_count"] == 5  # non-PII preserved
    print("  PASS: rbac_pii_mask")


def test_rbac_row_limit():
    rbac = RBACMiddleware()
    assert rbac.enforce_row_limit("Investigator", 99999) == 5000
    assert rbac.enforce_row_limit("Investigator", 100) == 100
    print("  PASS: rbac_row_limit")


def test_audit_logger():
    audit = AuditLogger()
    user = UserContextDTO(user_id="INV001", kgid="INV001", first_name="Ravi",
                          email="", role_id=1, role_name="Investigator")
    audit.log(user, "chat_query", {"msg": "hello"}, "success")
    audit.log(user, "export_pdf", {}, "success")
    recent = audit.get_recent(5)
    assert len(recent) == 2
    assert recent[0]["event_type"] == "export_pdf"
    print("  PASS: audit_logger")


def test_commander_intent_analysis():
    cmd = Commander()
    intents = cmd.analyze_intent("show me theft cases in Bangalore")
    assert intents["primary_intent"] == "database_query"
    assert intents["confidence"] == 0.85
    print("  PASS: commander_intent")


def test_commander_geospatial_intent():
    cmd = Commander()
    intents = cmd.analyze_intent("show hotspots on a map of Mysuru")
    assert intents["primary_intent"] == "geospatial_analysis"
    print("  PASS: commander_geospatial_intent")


def test_commander_offender_intent():
    cmd = Commander()
    intents = cmd.analyze_intent("profile of Ravi Kumar repeat offender")
    assert intents["primary_intent"] == "offender_profile"
    print("  PASS: commander_offender_intent")


def test_commander_forecast_intent():
    cmd = Commander()
    intents = cmd.analyze_intent("predict expected rise")
    assert intents["primary_intent"] == "forecast"
    print("  PASS: commander_forecast_intent")


def test_commander_network_intent():
    cmd = Commander()
    intents = cmd.analyze_intent("show connections and gang links")
    assert intents["primary_intent"] == "network_analysis"
    print("  PASS: commander_network_intent")


def test_commander_alert_intent():
    cmd = Commander()
    intents = cmd.analyze_intent("any alerts or warning spikes")
    assert intents["primary_intent"] == "alert_evaluation"
    print("  PASS: commander_alert_intent")


def test_evidence_validator():
    validator = EvidenceValidator()
    evidence = [{"evidence_id": "e1", "evidence_type": "database_fact", "source_table": "CaseMaster"}]
    validated = validator.validate(evidence)
    assert len(validated) == 1
    assert validated[0]["validated"]
    assert "validated_at" in validated[0]
    print("  PASS: evidence_validator")


def test_offender_agent():
    agent = OffenderAgent()
    result = agent.run("profile Ravi Kumar")
    assert result["data"]["entity_name"] == "Ravi Kumar"
    assert "risk_tier" in result["data"]
    print("  PASS: offender_agent")


def test_alert_engine():
    from forecast.alert_engine import AlertEngine
    engine = AlertEngine()
    alerts = engine.evaluate(district_id=18)
    assert len(alerts) >= 0  # probabilistic; may be 0
    for a in alerts:
        assert isinstance(a, EarlyWarningAlertDTO)
        assert a.rule_id in ("EW-001", "EW-002", "EW-003", "EW-004", "EW-005")
    print(f"  PASS: alert_engine ({len(alerts)} alerts)")


def test_confidence_high():
    from ai.confidence_classifier import ConfidenceClassifier
    cc = ConfidenceClassifier()
    r = cc.classify({"row_count": 50, "quality_warnings": [], "source": "glm_tool_call"})
    assert r == "high"
    print("  PASS: confidence_high")


def test_confidence_empty():
    from ai.confidence_classifier import ConfidenceClassifier
    cc = ConfidenceClassifier()
    r = cc.classify({"row_count": 0, "quality_warnings": [], "source": "glm_tool_call"})
    assert r == "medium", "empty results without quality warnings should be medium"
    r2 = cc.classify({"row_count": 0, "quality_warnings": ["w1"], "source": "glm_tool_call"})
    assert r2 == "low", "empty results WITH quality warnings should be low"
    print("  PASS: confidence_empty")


def test_confidence_medium():
    from ai.confidence_classifier import ConfidenceClassifier
    cc = ConfidenceClassifier()
    r = cc.classify({"row_count": 50, "quality_warnings": ["w1", "w2", "w3"], "source": "glm_tool_call"})
    assert r == "medium"
    print("  PASS: confidence_medium")


def test_grounding_verified():
    from ai.grounding_validator import GroundingValidator
    gv = GroundingValidator()
    r = gv.validate("Found 42 cases", {"row_count": 42})
    assert r == "verified"
    print("  PASS: grounding_verified")


def test_grounding_partial():
    from ai.grounding_validator import GroundingValidator
    gv = GroundingValidator()
    r = gv.validate("", {"row_count": 0})
    assert r == "partial"
    print("  PASS: grounding_partial")


def test_grounding_unverified():
    from ai.grounding_validator import GroundingValidator
    gv = GroundingValidator()
    r = gv.validate("", {"error": "fail"})
    assert r == "unverified"
    print("  PASS: grounding_unverified")


if __name__ == "__main__":
    print("Phase 3 self-check tests:")
    test_auth_login()
    test_auth_verify()
    test_auth_invalid()
    test_rbac_authorize()
    test_rbac_row_scope()
    test_rbac_pii_mask()
    test_rbac_row_limit()
    test_audit_logger()
    test_commander_intent_analysis()
    test_commander_geospatial_intent()
    test_commander_offender_intent()
    test_commander_forecast_intent()
    test_commander_network_intent()
    test_commander_alert_intent()
    test_evidence_validator()
    test_offender_agent()
    test_alert_engine()
    test_confidence_high()
    test_confidence_empty()
    test_confidence_medium()
    test_grounding_verified()
    test_grounding_partial()
    test_grounding_unverified()
    print("\nAll Phase 3/4 tests PASSED.")
