from investigation.lead_generator import LeadGenerator
from unittest.mock import MagicMock
import sys
import os
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BASE)
os.environ.setdefault("PYTHONPATH", BASE)


class TestLeadGenerator:
    def test_generate_leads_without_db(self):
        lg = LeadGenerator()
        leads = lg.generate_leads(101)
        assert len(leads) == 3
        types = {lead.lead_type for lead in leads}
        assert types == {"co_accused_link", "location_pattern", "witness_lead"}

    def test_confidence_scores_in_range(self):
        lg = LeadGenerator()
        leads = lg.generate_leads(55)
        for lead in leads:
            assert 0.0 <= lead.confidence_score <= 1.0
            assert lead.confidence_class in ("high", "medium", "low")

    def test_with_mock_db(self):
        mock_db = MagicMock()
        mock_db.is_connected = True
        mock_db.execute_non_query.return_value = {
            "columns": ["CrimeNo", "BriefFacts"],
            "rows": [["CN001", "Theft at market"]]
        }
        lg = LeadGenerator(db=mock_db)
        leads = lg.generate_leads(101)
        assert len(leads) == 3
        sql = mock_db.execute_non_query.call_args[0][0]
        assert "FROM CaseMaster" in sql
        assert "CaseMasterID=101" in sql
        assert "BriefFacts" in sql
        assert "BriedFacts" not in sql

    def test_with_mock_db_no_results(self):
        mock_db = MagicMock()
        mock_db.is_connected = True
        mock_db.execute_non_query.return_value = {"columns": [], "rows": []}
        lg = LeadGenerator(db=mock_db)
        leads = lg.generate_leads(101)
        assert len(leads) == 3

    def test_lead_ids_are_unique(self):
        lg = LeadGenerator()
        leads_a = lg.generate_leads(101)
        leads_b = lg.generate_leads(101)
        ids_a = [lead.lead_id for lead in leads_a]
        ids_b = [lead.lead_id for lead in leads_b]
        assert ids_a != ids_b

    def test_deterministic_confidence_fallback(self):
        lg = LeadGenerator()
        leads = lg.generate_leads(101)
        for lead in leads:
            if lead.lead_type == "co_accused_link":
                assert lead.confidence_score == 0.63
            elif lead.lead_type == "location_pattern":
                assert lead.confidence_score == 0.62
            elif lead.lead_type == "witness_lead":
                assert lead.confidence_score == 0.35
