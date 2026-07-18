"""Self-check tests for Phase 5 — Investigation Suite."""

from comms.group_manager import GroupManager
from comms.permission_engine import PermissionEngine
from comms.message_engine import MessageEngine
from governance.governance import (
    ModelRegistry, PromptRegistry, AgentCapabilityRegistry,
    AgentExecutionTracker, MissionTracker, ClaimLedger,
)
from investigation.report_generator import ReportGenerator
from investigation.lead_generator import LeadGenerator
from investigation.timeline_generator import TimelineGenerator
from investigation.similarity_engine import SimilarityEngine
from investigation.investigation_manager import InvestigationManager
import sys
import os
import tempfile
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BASE)
os.environ.setdefault("PYTHONPATH", BASE)

# ponytail: clear persisted state from prior runs so each test starts clean
for _f in ('suraksha_governance.json', 'suraksha_investigations.json'):
    _p = os.path.join(tempfile.gettempdir(), _f)
    if os.path.exists(_p):
        os.remove(_p)


def test_investigation_create():
    mgr = InvestigationManager()
    inv = mgr.create("Test Investigation", "A test setup", "user1")
    assert inv.title == "Test Investigation"
    assert inv.description == "A test setup"
    assert inv.status == "open"
    assert inv.investigation_id is not None
    assert inv.case_count == 0
    print("  PASS: investigation_create")


def test_investigation_get():
    mgr = InvestigationManager()
    inv = mgr.create("Get test", "get check", "user1")
    output = mgr.get(inv.investigation_id)
    assert output is not None
    assert output["title"] == "Get test"
    assert output["cases"] == []
    print("  PASS: investigation_get")


def test_investigation_get_missing():
    mgr = InvestigationManager()
    assert mgr.get("nonexistent") is None
    print("  PASS: investigation_get_missing")


def test_investigation_list():
    mgr = InvestigationManager()
    mgr.create("A", "", "u1")
    mgr.create("B", "", "u2")
    assert len(mgr.list_all()) >= 2
    print("  PASS: investigation_list")


def test_investigation_add_case():
    mgr = InvestigationManager()
    inv = mgr.create("Case test", "", "u1")
    ok = mgr.add_case(inv.investigation_id, 101, "Primary case")
    assert ok
    output = mgr.get(inv.investigation_id)
    assert len(output["cases"]) == 1
    assert output["cases"][0]["case_master_id"] == 101
    print("  PASS: investigation_add_case")


def test_investigation_add_case_missing():
    mgr = InvestigationManager()
    assert mgr.add_case("bad", 1) is False
    print("  PASS: investigation_add_case_missing")


def test_investigation_add_graph():
    mgr = InvestigationManager()
    inv = mgr.create("Graph test", "", "u1")
    saved = mgr.add_graph(inv.investigation_id, {"nodes": [{"id": "n1"}], "edges": []}, "Test Graph")
    assert saved is not None
    assert saved.label == "Test Graph"
    assert saved.node_count == 1
    assert saved.edge_count == 0
    print("  PASS: investigation_add_graph")


def test_investigation_add_graph_missing():
    mgr = InvestigationManager()
    assert mgr.add_graph("bad", {}, "") is None
    print("  PASS: investigation_add_graph_missing")


def test_similarity_engine():
    sim = SimilarityEngine()
    results = sim.find_similar(101, top_k=3)
    assert len(results) == 3
    for r in results:
        assert r.case_master_id > 0
        assert 0.0 <= r.similarity_score <= 1.0
        assert r.crime_no is not None
        assert r.per_feature_scores is not None
        assert len(r.per_feature_scores) == 4
    print("  PASS: similarity_engine")


def test_timeline_generator():
    tl = TimelineGenerator()
    events = tl.generate(101)
    assert len(events) == 3
    types = [e.event_type for e in events]
    assert "crime_registration" in types
    assert "arrest" in types
    assert "chargesheet" in types
    for e in events:
        assert e.event_date is not None
        assert e.description
    print("  PASS: timeline_generator")


def test_timeline_chronological():
    tl = TimelineGenerator()
    events = tl.generate(101)
    dates = [e.event_date for e in events]
    assert dates == sorted(dates), "timeline events must be in chronological order"
    print("  PASS: timeline_chronological")


def test_lead_generator():
    lg = LeadGenerator()
    leads = lg.generate_leads(101)
    assert len(leads) == 3
    types = {lead.lead_type for lead in leads}
    assert "co_accused_link" in types
    assert "location_pattern" in types
    assert "witness_lead" in types
    for lead in leads:
        assert lead.lead_id is not None
        assert 0.0 <= lead.confidence_score <= 1.0
        assert lead.confidence_class in ("high", "medium", "low")
        assert len(lead.supporting_evidence) > 0
    print("  PASS: lead_generator")


def test_lead_confidence_range():
    lg = LeadGenerator()
    leads = lg.generate_leads(55)
    for lead in leads:
        assert 0.0 <= lead.confidence_score <= 1.0
    print("  PASS: lead_confidence_range")


def test_report_generator():
    rg = ReportGenerator()
    report = rg.generate("inv-123", {"title": "Test Inv", "cases": []})
    assert report.job_id is not None
    assert report.status == "completed"
    assert report.stratus_url is not None
    assert "inv-" in report.stratus_url
    print("  PASS: report_generator")


def test_investigation_roundtrip():
    mgr = InvestigationManager()
    inv = mgr.create("Roundtrip", "", "u1")
    mgr.add_case(inv.investigation_id, 201, "case one")
    mgr.add_case(inv.investigation_id, 202, "case two")
    mgr.add_graph(inv.investigation_id, {"nodes": [{"id": "n1"}, {"id": "n2"}], "edges": [
                  {"source": "n1", "target": "n2"}]}, "graph A")
    output = mgr.get(inv.investigation_id)
    assert len(output["cases"]) == 2
    assert len(output["graphs"]) == 1
    assert output["graphs"][0]["node_count"] == 2
    print("  PASS: investigation_roundtrip")


# ── Communication tests ──────────────────────────────────────────────

def test_message_send():
    eng = MessageEngine()
    msg = eng.send("STATUS_UPDATE", 1, "IO", 1, "South Station",
                   [2, 3], "Subject", "Body", cc_ids=[4],
                   priority="HIGH")
    assert msg.message_id is not None
    assert msg.type == "STATUS_UPDATE"
    assert msg.sender.employee_id == 1
    assert len(msg.recipients) == 2
    assert len(msg.cc) == 1
    assert msg.priority == "HIGH"
    assert msg.status == "SENT"
    assert eng.get(msg.message_id) is not None
    print("  PASS: message_send")


def test_message_inbox():
    eng = MessageEngine()
    eng.send("CASE_ASSIGNMENT", 1, "SHO", 1, "Station",
             [5], "Case assigned", "Details")
    eng.send("STATUS_UPDATE", 2, "IO", 1, "Station",
             [1], "Update", "Progress", priority="HIGH")
    inbox = eng.list_inbox(1)
    assert len(inbox) >= 1
    high = eng.list_inbox(1, priority_filter="HIGH")
    assert len(high) >= 1
    print("  PASS: message_inbox")


def test_message_thread():
    eng = MessageEngine()
    parent = eng.send("APPROVAL_REQUEST", 1, "IO", 1, "Station",
                      [2], "Review", "Please review")
    reply = eng.send("APPROVAL_REQUEST", 2, "SHO", 1, "Station",
                     [1], "Re: Review", "Approved",
                     parent_message_id=parent.message_id)
    thread = eng.get_thread(reply.message_id)
    assert len(thread) == 2
    print("  PASS: message_thread")


def test_message_ack():
    eng = MessageEngine()
    msg = eng.send("CRITICAL_ALERT", 1, "DSP", 1, "District",
                   [2], "Alert", "Emergency", priority="CRITICAL")
    assert eng.acknowledge(msg.message_id, 2)
    assert eng.get(msg.message_id).status == "ACKNOWLEDGED"
    assert eng.mark_read(msg.message_id, 2)
    print("  PASS: message_ack")


def test_permission_check():
    pe = PermissionEngine()
    r = pe.check("Constable", "CASE", "APPROVE")
    assert r.allowed is False
    r2 = pe.check("SHO", "CASE", "APPROVE", "own_station")
    assert r2.allowed is True
    r3 = pe.check("DSP", "CHARGESHEET", "APPROVE", "own_district")
    assert r3.allowed is True
    r4 = pe.check("Sub-Inspector", "CHARGESHEET", "APPROVE")
    assert r4.allowed is False
    print("  PASS: permission_check")


def test_permission_delegation():
    pe = PermissionEngine()
    d = pe.delegate(1, 2, "APPROVE_CHARGESHEET", "own_station",
                    reason="SHO on leave")
    assert d.status == "active"
    assert pe.has_delegation(2, "APPROVE_CHARGESHEET") is not None
    assert pe.has_delegation(3, "APPROVE_CHARGESHEET") is None
    assert pe.revoke_delegation(d.permission_id)
    assert pe.has_delegation(2, "APPROVE_CHARGESHEET") is None
    print("  PASS: permission_delegation")


def test_permission_emergency():
    pe = PermissionEngine()
    assert pe.is_emergency is False
    pe.set_emergency(True, 72)
    assert pe.is_emergency is True
    r = pe.check("Constable", "CHARGESHEET", "APPROVE")
    assert r.allowed is True
    assert "Emergency" in r.denial_reason
    pe.set_emergency(False)
    r2 = pe.check("Constable", "CHARGESHEET", "APPROVE")
    assert r2.allowed is False
    print("  PASS: permission_emergency")


def test_org_group():
    gm = GroupManager()
    g = gm.create_org_group("South Station", "STATION")
    assert g.group_name == "South Station"
    assert g.group_type == "STATION"
    assert gm.get_org_group(g.group_id) is not None
    assert len(gm.list_org_groups("STATION")) >= 1
    print("  PASS: org_group")


def test_dynamic_group():
    gm = GroupManager()
    g = gm.create_dynamic_group("Theft Task Force", "TASK_FORCE",
                                lead_id=1, case_ids=[101, 102],
                                duration_days=60)
    assert g.group_name == "Theft Task Force"
    assert len(g.linked_case_ids) == 2
    assert g.dissolve_at is not None
    assert gm.get_dynamic_group(g.group_id) is not None
    assert len(gm.list_dynamic_groups()) >= 1
    assert gm.dissolve_group(g.group_id)
    assert gm.get_dynamic_group(g.group_id).status == "dissolved"
    print("  PASS: dynamic_group")


def test_group_members():
    gm = GroupManager()
    g = gm.create_dynamic_group("Task Force", "TASK_FORCE")
    m = gm.add_group_member(g.group_id, 1, "LEAD", can_approve=True)
    assert m is not None
    assert m.role == "LEAD"
    assert m.can_approve is True
    gm.add_group_member(g.group_id, 2, "MEMBER", can_modify=True)
    assert len(gm.list_members(g.group_id)) == 2
    assert gm.get_member(g.group_id, 1) is not None
    assert gm.remove_group_member(g.group_id, 2)
    assert len(gm.list_members(g.group_id)) == 1
    groups = gm.list_groups_for_employee(1)
    assert len(groups) >= 1
    print("  PASS: group_members")


def test_coordination():
    gm = GroupManager()
    req = gm.create_coordination(1, 2, "SUSPECT_LOCATION",
                                 "Suspect sighted", "Details at...",
                                 case_id=101)
    assert req.request_type == "SUSPECT_LOCATION"
    assert req.linked_case_id == 101
    assert gm.update_coordination(req.request_id, "approved", assigned_to=3)
    assert gm.get_coordination(req.request_id).status == "approved"
    assert gm.get_coordination(req.request_id).assigned_to_employee_id == 3
    assert len(gm.list_coordination(from_id=1)) >= 1
    print("  PASS: coordination")


# ── AI Governance tests ───────────────────────────────────────────────

def test_model_registry():
    r = ModelRegistry()
    e = r.register("GLM", "crm-di-glm47b_30b_it", "Zoho", ["tool_calling", "sql"])
    assert e.model_id is not None
    assert e.model_name == "GLM"
    assert "tool_calling" in e.capabilities
    assert r.get(e.model_id).model_version == "crm-di-glm47b_30b_it"
    assert len(r.list_all()) == 1
    print("  PASS: model_registry")


def test_prompt_registry():
    r = PromptRegistry()
    e = r.register("system_prompt", "1.0", "You are a crime analyst.", "m1")
    assert e.prompt_id is not None
    assert e.prompt_name == "system_prompt"
    assert e.model_id == "m1"
    assert r.get(e.prompt_id).prompt_text == "You are a crime analyst."
    assert len(r.list_all()) == 1
    print("  PASS: prompt_registry")


def test_agent_capability_registry():
    r = AgentCapabilityRegistry()
    dto = r.register("db_agent", ["query", "lookup"], "Query the database.", ["chat_query"])
    assert dto.agent_name == "db_agent"
    assert "query" in dto.intents
    assert "chat_query" in dto.required_permissions
    assert r.get("db_agent").description == "Query the database."
    print("  PASS: agent_capability_registry")


def test_execution_tracker():
    t = AgentExecutionTracker()
    e = t.start("mission-1", "db_agent", "query", "show theft cases")
    assert e.status == "running"
    assert e.mission_id == "mission-1"
    ok = t.complete(e.execution_id, "Found 100 cases", ["ev1", "ev2"])
    assert ok
    completed = t.get(e.execution_id)
    assert completed.status == "completed"
    assert completed.output_summary == "Found 100 cases"
    assert len(t.list_by_mission("mission-1")) == 1
    print("  PASS: execution_tracker")


def test_execution_fail():
    t = AgentExecutionTracker()
    e = t.start("mission-2", "db_agent", "query", "bad query")
    ok = t.fail(e.execution_id, "error: timeout")
    assert ok
    assert t.get(e.execution_id).status == "failed"

    # missing execution
    assert t.complete("nonexistent") is False
    assert t.fail("nonexistent") is False
    print("  PASS: execution_fail")


def test_mission_tracker():
    exec_tracker = AgentExecutionTracker()
    mt = MissionTracker(exec_tracker)
    mission = mt.create("find theft cases", "user1", {"primary": "database_query"})
    assert mission.status == "created"
    assert mission.user_id == "user1"
    assert mt.get_mission(mission.mission_id).query == "find theft cases"

    ok = mt.update_mission_status(mission.mission_id, "completed", "Mission done")
    assert ok
    assert mt.get_mission(mission.mission_id).status == "completed"
    assert mt.get_mission(mission.mission_id).completed_at is not None
    assert len(mt.list_missions()) == 1
    print("  PASS: mission_tracker")


def test_mission_tasks():
    exec_tracker = AgentExecutionTracker()
    mt = MissionTracker(exec_tracker)
    mission = mt.create("analyze hotspot", "user1")
    task = mt.add_task(mission.mission_id, "geo_agent", "geospatial", "find hotspot")
    assert task is not None
    assert task.status == "pending"

    started = mt.start_task(task.task_id)
    assert started.status == "running"
    assert started.started_at is not None

    ok = mt.complete_task(task.task_id, {"cluster": "A"}, [])
    assert ok
    assert mt.get_task(task.task_id).status == "completed"

    # missing mission — add_task returns None
    assert mt.add_task("nonexistent", "a", "b") is None
    print("  PASS: mission_tasks")


def test_claim_ledger():
    cl = ClaimLedger()
    e = cl.add_entry("Case solved", "DATABASE_FACT", "CaseMaster", confidence=1.0)
    assert e.claim_id is not None
    assert e.classification == "DATABASE_FACT"
    assert e.validation_status == "Under Review"
    assert e.confidence_label == "high"
    assert len(cl.list_all()) == 1

    # low confidence
    e2 = cl.add_entry("Maybe involved", "MODEL_HYPOTHESIS", "AI", confidence=0.3)
    assert e2.confidence_label == "low"
    print("  PASS: claim_ledger")


def test_claim_update_status():
    cl = ClaimLedger()
    e = cl.add_entry("Test claim", "DATABASE_FACT", "test")
    ok = cl.update_status(e.claim_id, "Accepted")
    assert ok
    assert cl.get(e.claim_id).validation_status == "Accepted"

    # missing claim
    assert cl.update_status("nonexistent", "Accepted") is False
    print("  PASS: claim_update_status")


if __name__ == "__main__":
    print("Phase 5 — Investigation Suite + AI Governance tests:")
    test_investigation_create()
    test_investigation_get()
    test_investigation_get_missing()
    test_investigation_list()
    test_investigation_add_case()
    test_investigation_add_case_missing()
    test_investigation_add_graph()
    test_investigation_add_graph_missing()
    test_similarity_engine()
    test_timeline_generator()
    test_timeline_chronological()
    test_lead_generator()
    test_lead_confidence_range()
    test_report_generator()
    test_investigation_roundtrip()
    test_model_registry()
    test_prompt_registry()
    test_agent_capability_registry()
    test_execution_tracker()
    test_execution_fail()
    test_mission_tracker()
    test_mission_tasks()
    test_claim_ledger()
    test_claim_update_status()
    test_message_send()
    test_message_inbox()
    test_message_thread()
    test_message_ack()
    test_permission_check()
    test_permission_delegation()
    test_permission_emergency()
    test_org_group()
    test_dynamic_group()
    test_group_members()
    test_coordination()
    print("\nAll Phase 5 tests PASSED.")
