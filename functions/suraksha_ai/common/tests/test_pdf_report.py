from pdf.pdf_exporter import upload_to_stratus, make_filename
from pdf.report_writer import generate_investigation_report_pdf
import sys
import os
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BASE)
os.environ.setdefault("PYTHONPATH", BASE)


def _fake_inv():
    return {
        "investigation_id": "inv-test-1234",
        "title": "Bengaluru Theft Ring 2026",
        "description": "Multi-district organized theft investigation.",
        "status": "open",
        "created_at": "2026-07-17T10:00:00",
    }


def _fake_cases():
    return [
        {"case_master_id": 1001, "crime_head": "Theft", "district": "Bengaluru Urban", "date": "2026-06-01"},
        {"case_master_id": 1002, "crime_head": "Robbery", "district": "Mysuru", "date": "2026-06-15"},
    ]


def _fake_graph():
    return {"node_count": 12, "edge_count": 7, "label": "Accused Network A", "center_node_name": "Ravi"}


def test_pdf_has_magic_bytes():
    b = generate_investigation_report_pdf(_fake_inv(), _fake_cases(), _fake_graph())
    assert isinstance(b, (bytes, bytearray))
    assert len(b) > 100
    assert b[:4] == b"%PDF"


def _extract_text(pdf_bytes: bytes) -> str:
    """Decode PDF content-stream text (fpdf2 compresses streams with FlateDecode)."""
    import re
    import zlib
    t = bytes(pdf_bytes).decode("latin-1", errors="ignore")
    out = [t]
    for s in re.findall(r"stream\r?\n(.*?)\r?\nendstream", t, flags=re.DOTALL):
        try:
            out.append(zlib.decompress(s.encode("latin-1")).decode("latin-1", errors="ignore"))
        except Exception:
            pass
    return "\n".join(out)


def test_pdf_renders_title():
    b = generate_investigation_report_pdf(_fake_inv(), _fake_cases(), _fake_graph())
    text = _extract_text(b)
    assert "Bengaluru Theft Ring 2026" in text


def test_export_returns_metadata_shape():
    b = generate_investigation_report_pdf(_fake_inv(), _fake_cases(), _fake_graph())
    res = upload_to_stratus(b, make_filename("inv-test-1234"))
    assert "file_id" in res and isinstance(res.get("file_id"), str)
    assert res.get("created_at") is not None
