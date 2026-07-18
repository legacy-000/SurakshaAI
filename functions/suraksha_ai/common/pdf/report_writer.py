"""PDF generation for SurakshaAI investigation reports.

Uses fpdf2 (pure-python, ~300KB). No heavy deps.
"""
from fpdf import FPDF


def generate_investigation_report_pdf(
    investigation: dict,
    cases: list = None,
    graph: dict = None,
) -> bytes:
    """Build a 1-3 page PDF report from investigation data. Returns PDF bytes."""
    inv = investigation or {}
    cases = cases or []
    graph = graph or {}

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 16)
    title = f"Investigation: {inv.get('title') or 'Untitled'}"
    pdf.cell(0, 10, title, ln=True)
    pdf.ln(2)

    # Metadata
    pdf.set_font("Helvetica", "", 10)
    meta = [
        ("Investigation ID", inv.get("investigation_id", "")),
        ("Status", inv.get("status", "")),
        ("Created At", inv.get("created_at", "")),
        ("Description", inv.get("description", "")),
    ]
    for k, v in meta:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(40, 6, f"{k}:")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, str(v), ln=True)

    pdf.ln(4)

    # Cases
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Linked Cases", ln=True)
    if not cases:
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, "No cases linked.", ln=True)
    else:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(30, 7, "CaseMasterID", border=1)
        pdf.cell(50, 7, "Crime Head", border=1)
        pdf.cell(40, 7, "District", border=1)
        pdf.cell(40, 7, "Date", border=1, ln=True)
        pdf.set_font("Helvetica", "", 10)
        for c in cases:
            pdf.cell(30, 6, str(c.get("case_master_id", c.get("CaseMasterID", ""))), border=1)
            pdf.cell(50, 6, str(c.get("crime_head", c.get("crime_type", ""))), border=1)
            pdf.cell(40, 6, str(c.get("district", "")), border=1)
            pdf.cell(40, 6, str(c.get("date", c.get("created_at", ""))), border=1, ln=True)

    pdf.ln(4)

    # Graph summary
    unit = graph[-1] if isinstance(graph, list) and graph else (graph if graph else {})
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Graph Summary", ln=True)
    pdf.set_font("Helvetica", "", 10)
    nc = unit.get("node_count", len(unit.get("nodes", [])) if unit else 0)
    pdf.cell(0, 6, f"Nodes: {nc}", ln=True)
    ec = unit.get("edge_count", len(unit.get("edges", [])) if unit else 0)
    pdf.cell(0, 6, f"Edges: {ec}", ln=True)
    if unit.get("label"):
        pdf.cell(0, 6, f"Label: {unit.get('label')}", ln=True)
    if unit.get("center_node_name"):
        pdf.cell(0, 6, f"Center: {unit.get('center_node_name')}", ln=True)

    return pdf.output()
