from common.ai.quickml_client import QuickMLClient
from common.ai.rag_retriever import SchemaRAGRetriever
from common.sql.sql_validator import SQLValidator

SCHEMA_DEFS = """
Tables:
- CaseMaster: CrimeNo, CaseNo, CrimeRegisteredDate, PolicePersonID, PoliceStationID, CaeCategoryID, GravityOffenceID, CrimeMajorHeadID, CrimeMinorHeadID, CaseStatusID, CourtID, IncidentFromDate, IncidentToDate, InfoReceivedPSDate, latitide, longitude, BriedFacts
- Accused: CaseMasterID, AccusedName, AgeYear, GenderID, PersonID
- District: DistrictID, DistrictName, StateID, Active
- CrimeHead: CrimeHeadID, CrimeGroupName, Active
- CrimeSubHead: CrimeSubHeadID, CrimeHeadID, CrimeHeadName, SeqID
- Unit: UnitID, UnitName, TypeID, ParentUnit, NationalityID, StateID, DistrictID, Active
- Employee: EmployeeID, DistrictID, UnitID, RankID, DesignationID, KGID, FirstName, EmployeeDOB, GenderID, AppointmentDate
- ComplainantDetails: CaseMasterID, ComplainantName, AgeYear, OccupationID, ReligionID, CasteID, GenderID
- Victim: CaseMasterID, VictimName, AgeYear, GenderID, VictimPolice
- Act: ActCode, ActDescription, ShortName, Active
- Section: ActCode, SectionCode, SectionDescription, Active
- CaseStatusMaster: CaseStatusID, CaseStatusName
- Court: CourtID, CourtName, DistrictID, StateID, Active
- State: StateID, StateName, NationalityID, Active
- Designation: DesignationID, DesignationName, Active, SortOrder
- Rank: RankID, RankName, Hierarchy, Active
- CaseCategory: CaseCategoryID, LookupValue
- GravityOffence: GravityOffenceID, LookupValue
- UnitType: UnitTypeID, UnitTypeName, CityDistState, Hierarchy, Active
- ArrestSurrender: CaseMasterID, ArrestSurrenderTypeID, ArrestSurrenderDate, ArrestSurrenderStateId, ArrestSurrenderDistrictId, PoliceStationID, IOID, CourtID, AccusedMasterID, IsAccused, IsComplainantAccused
- ChargesheetDetails: CSID, CaseMasterID, csdate, cstype, PolicePersonID
"""


class NL2SQLEngine:
    def __init__(self, catalyst_app=None):
        self.quickml = QuickMLClient(catalyst_app)
        self.rag = SchemaRAGRetriever(catalyst_app)
        self.validator = SQLValidator()

    def generate_sql(self, query: str, context: list = None) -> dict:
        schema_context = self.rag.retrieve_schema(top_k=8)
        examples = self.rag.retrieve_examples(query, top_k=3)
        if schema_context.get("error"):
            return {"error": "RAG_FAILED", "message": schema_context["message"]}

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(query, schema_context, examples)
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]

        result = self.quickml.chat(messages, temperature=0.1, max_tokens=4096)
        if result.get("error"):
            return result

        text = result.get("text", "")
        sql_text = self._extract_sql(text)
        if not sql_text.strip():
            return {
                "error": "SQLGEN_EMPTY",
                "message": f"Model returned empty SQL. Raw: {text[:200]}",
                "raw_response": text}

        validation = self.validator.validate(sql_text)
        if not validation.get("is_valid", False):
            return {"error": "SQLGEN_001", "sql_text": sql_text, "validation": validation, "raw_response": text}

        return {"sql_text": sql_text, "validation": validation, "model": result.get("model"), "raw_response": text}

    def _build_system_prompt(self) -> str:
        return f"""You are a SQL generator for Zoho Catalyst ZCQL. Rules:
1. ONLY SELECT queries.
2. Use ZCQL syntax: column names are case-sensitive (exactly as listed).
3. Use table aliases: CaseMaster cm, Accused a, District d, Unit u, CrimeSubHead csh, CrimeHead ch.
4. For JOINs use: FROM CaseMaster cm, Unit u WHERE cm.PoliceStationID = u.UnitID.
5. No nested subqueries, no UNION, no CTEs.
6. ZCQL does NOT support: ORDER BY alias, HAVING, subqueries in WHERE.
7. The column CaseMasterID does NOT exist in CaseMaster table (use ROWID instead).
8. All tables use ROWID as auto-generated primary key.{SCHEMA_DEFS}"""

    def _build_user_prompt(self, query, schema_context, examples):
        parts = [f"Question: {query}"]
        tbls = schema_context.get("table_descriptions", [])
        if tbls:
            parts.append("\nRelevant tables:")
            for t in tbls:
                parts.append(f"  - {t.get('name')}: {t.get('description')}")
        cols = schema_context.get("column_descriptions", [])
        if cols:
            parts.append("\nKey columns:")
            for c in cols[:10]:
                parts.append(f"  - {c.get('table')}.{c.get('column')} ({c.get('type')})")
        if examples:
            parts.append("\nSimilar examples:")
            for ex in examples[:2]:
                parts.append(f"  Q: {ex.get('natural_language')}")
                parts.append(f"  SQL: {ex.get('sql')}")
        return "\n".join(parts)

    def _extract_sql(self, text: str) -> str:
        clean = text.replace("```sql", "").replace("```SQL", "").replace("```", "").strip()
        lines = [ln for ln in clean.split("\n") if ln.strip().upper().startswith("SELECT")
                 or ln.strip().upper().startswith("WITH")]
        if lines:
            return lines[0].strip()
        for ln in clean.split("\n"):
            if "SELECT" in ln.upper():
                return ln.strip()
        return clean.split("\n")[0].strip()
