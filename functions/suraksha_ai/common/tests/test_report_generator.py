from investigation.report_generator import ReportGenerator
import sys
import os
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BASE)
os.environ.setdefault("PYTHONPATH", BASE)


class TestReportGenerator:
    def test_generate_returns_job_id(self):
        rg = ReportGenerator()
        report = rg.generate("inv-123", {"title": "Test Inv", "cases": []})
        assert report.job_id is not None
        assert report.status == "completed"

    def test_stratus_url_includes_investigation_id(self):
        rg = ReportGenerator()
        report = rg.generate("inv-abc12345", {"title": "Test", "cases": []})
        assert "inv-" in report.stratus_url
        assert report.stratus_url.endswith(".pdf")
