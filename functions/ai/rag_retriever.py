from models.dto import RetrievedSchemaContextDTO


class SchemaRAGRetriever:
    def retrieve_schema(self, intent_type: str = "DATA_QUERY", top_k: int = 5) -> RetrievedSchemaContextDTO:
        return RetrievedSchemaContextDTO(
            table_descriptions=[
                {"name": "CaseMaster", "description": "Core FIR/case transaction table"},
                {"name": "Accused", "description": "Accused persons linked to cases"},
                {"name": "Victim", "description": "Victim information per case"},
                {"name": "ComplainantDetails", "description": "Complainant demographics"},
                {"name": "Unit", "description": "Police stations and units"}
            ],
            column_descriptions=[
                {"table": "CaseMaster", "column": "CrimeNo", "type": "VARCHAR"},
                {"table": "CaseMaster", "column": "CrimeRegisteredDate", "type": "DATE"},
                {"table": "CaseMaster", "column": "latitude", "type": "DECIMAL"},
                {"table": "CaseMaster", "column": "longitude", "type": "DECIMAL"},
                {"table": "Accused", "column": "AccusedName", "type": "VARCHAR"}
            ]
        )


class TerminologyRAGRetriever:
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
            {"english": "Complainant", "kannada": "ದೂರುದಾರ", "category": "legal"}
        ]
        return terms
