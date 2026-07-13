import logging

logger = logging.getLogger(__name__)

SCHEMA_KB_NAME = "ksp-dev-rag-kb-schema"
EXAMPLES_KB_NAME = "ksp-dev-rag-kb-examples"


class SchemaRAGRetriever:
    def __init__(self, catalyst_app=None):
        self._catalyst_app = catalyst_app
        from functions.db.datastore_client import DatastoreClient
        self._db = DatastoreClient(catalyst_app)

    @property
    def is_available(self):
        return self._catalyst_app is not None

    def retrieve_schema(self, intent_type: str = "DATA_QUERY", top_k: int = 5) -> dict:
        if not self.is_available:
            return self._static_context()

        try:
            kb = self._catalyst_app.quick_ml().kb(SCHEMA_KB_NAME)
            results = kb.search_text(f"Tables relevant for {intent_type} query", top_k=top_k)

            tables = []
            columns = []
            for item in (results or []):
                content = item.get("content", "")
                metadata = item.get("metadata", {})
                if metadata.get("type") == "table":
                    tables.append({"name": metadata.get("name"), "description": content})
                elif metadata.get("type") == "column":
                    columns.append(metadata)

            return {
                "table_descriptions": tables,
                "column_descriptions": columns if columns else self._fallback_columns(),
            }

        except Exception as e:
            logger.error("RAG KB schema search failed: %s", e)
            return self._static_context()

    def retrieve_examples(self, query: str, top_k: int = 3) -> list[dict]:
        fallback = [
            {
                "natural_language": "Show theft cases in Bangalore",
                "sql": "SELECT cm.CaseMasterID, cm.CrimeNo, cm.CrimeRegisteredDate FROM CaseMaster cm JOIN Unit u ON cm.PoliceStationID = u.UnitID JOIN District d ON u.DistrictID = d.DistrictID JOIN CrimeSubHead csh ON cm.CrimeMinorHeadID = csh.CrimeSubHeadID WHERE d.DistrictName = 'Bangalore' AND csh.CrimeHeadName = 'Theft' LIMIT 100"
            },
            {
                "natural_language": "How many murder cases in Mysore this year?",
                "sql": "SELECT COUNT(*) FROM CaseMaster cm JOIN Unit u ON cm.PoliceStationID = u.UnitID JOIN District d ON u.DistrictID = d.DistrictID JOIN CrimeSubHead csh ON cm.CrimeMinorHeadID = csh.CrimeSubHeadID WHERE d.DistrictName = 'Mysore' AND csh.CrimeHeadName = 'Murder' AND cm.CrimeRegisteredDate >= '2026-01-01'"
            },
            {
                "natural_language": "List all accused in crime number 123/2025",
                "sql": "SELECT a.AccusedName, cm.CrimeNo FROM Accused a JOIN CaseMaster cm ON a.CaseMasterID = cm.CaseMasterID WHERE cm.CrimeNo = '123/2025'"
            }
        ]
        if not self.is_available:
            return fallback

        try:
            kb = self._catalyst_app.quick_ml().kb(EXAMPLES_KB_NAME)
            results = kb.search_text(query, top_k=top_k)
            retrieved = [{"natural_language": r.get("content", ""), "sql": (r.get("metadata") or {}).get("sql", "")} for r in (results or [])]
            return retrieved if retrieved else fallback
        except Exception as e:
            logger.warning("RAG KB example search failed: %s", e)
            return fallback

    def _fallback_columns(self) -> list[dict]:
        return [
            {"table": "CaseMaster", "column": "CaseMasterID", "type": "INT"},
            {"table": "CaseMaster", "column": "CrimeRegisteredDate", "type": "DATE"},
            {"table": "CaseMaster", "column": "latitude", "type": "DECIMAL"},
            {"table": "Accused", "column": "AccusedName", "type": "VARCHAR"},
        ]

    def _static_context(self) -> dict:
        return {
            "table_descriptions": [
                {"name": "CaseMaster", "description": "Core FIR/case transaction table with crime details, dates, location"},
                {"name": "Accused", "description": "Accused persons linked to cases via CaseMasterID"},
                {"name": "ComplainantDetails", "description": "Complainant demographics per case"},
                {"name": "Victim", "description": "Victim information per case"},
                {"name": "Unit", "description": "Police stations and units mapped to districts"},
                {"name": "District", "description": "District master with names and state mapping"},
                {"name": "CrimeSubHead", "description": "Crime type/sub-category names linked to CrimeHead"},
            ],
            "column_descriptions": self._fallback_columns(),
        }


class TerminologyRAGRetriever:
    def __init__(self, catalyst_app=None):
        self._catalyst_app = catalyst_app

    def retrieve_terms(self, language_code: str = "en") -> list[dict]:
        terms = [
            {"english": "Theft", "kannada": "ಕಳ್ಳತನ", "category": "crime_type"},
            {"english": "Murder", "kannada": "ಹತ್ಯೆ", "category": "crime_type"},
            {"english": "Robbery", "kannada": "ದರೋಡೆ", "category": "crime_type"},
            {"english": "Assault", "kannada": "ಹಲ್ಲೆ", "category": "crime_type"},
            {"english": "Kidnapping", "kannada": "ಅಪಹರಣ", "category": "crime_type"},
            {"english": "FIR", "kannada": "ಎಫ್ಐಆರ್", "category": "legal"},
            {"english": "Chargesheet", "kannada": "ಚಾರ್ಜ್ಶೀಟ್", "category": "legal"},
            {"english": "Accused", "kannada": "ಆರೋಪಿ", "category": "legal"},
            {"english": "Complainant", "kannada": "ದೂರುದಾರ", "category": "legal"},
        ]
        return terms
