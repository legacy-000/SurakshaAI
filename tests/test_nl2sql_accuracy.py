from unittest.mock import patch
from functions.ai.nl2sql_engine import NL2SQLEngine

TEST_QUERIES = [
    "How many cases in Bangalore?",
    "Show theft cases this year",
    "List all murder cases",
    "Who are the accused in case 101?",
    "Show cases with pending status",
    "Count cases by district",
    "What is the most common crime type?",
    "Cases registered in 2024",
    "Which station has most cases?",
    "Show cases with GPS coordinates nearby"
]


def test_nl2sql_generates_valid_sql():
    with patch("functions.ai.quickml_client.QuickMLClient.chat") as mock_chat:
        mock_chat.return_value = {
            "text": "SELECT COUNT(*) FROM CaseMaster WHERE DistrictID = 1",
            "model": "mock-model",
            "full_response": {}
        }
        engine = NL2SQLEngine()
        valid_count = 0
        for q in TEST_QUERIES:
            result = engine.generate_sql(q)
            if result.get("sql_text") and "SELECT" in result["sql_text"].upper():
                valid_count += 1
        assert valid_count >= 7
