class SQLValidator:
    ALLOWED_TABLES = {
        "CaseMaster", "ComplainantDetails", "Victim", "Accused",
        "ArrestSurrender", "ChargesheetDetails", "Act", "Section",
        "ActSectionAssociation", "CrimeHead", "CrimeSubHead",
        "CrimeHeadActSection", "CasteMaster", "ReligionMaster",
        "OccupationMaster", "CaseCategory", "GravityOffence",
        "CaseStatusMaster", "Court", "District", "State", "Unit",
        "UnitType", "Rank", "Designation", "Employee"
    }

    def validate(self, sql_text: str) -> dict:
        if not sql_text or not sql_text.strip():
            return {"is_valid": False, "errors": ["Empty SQL query"]}

        sql_upper = sql_text.strip().upper()
        if not sql_upper.startswith("SELECT"):
            return {"is_valid": False, "errors": ["Only SELECT queries allowed"]}

        if "INTO" in sql_upper or "DELETE" in sql_upper or "UPDATE" in sql_upper or "INSERT" in sql_upper:
            return {"is_valid": False, "errors": ["Data modification not allowed"]}

        return {"is_valid": True, "validated_sql": sql_text, "warnings": []}

