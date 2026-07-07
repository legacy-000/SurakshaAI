class SmartBrowzClient:
    def generate_pdf(self, html_content: str, output_name: str = "report.pdf") -> str:
        return f"/exports/{output_name}"

    def generate_from_template(self, template_id: str, data: dict) -> str:
        return f"/exports/template_{template_id}.pdf"
