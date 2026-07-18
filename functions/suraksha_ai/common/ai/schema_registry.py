import logging

logger = logging.getLogger(__name__)

# Fallback schema: hardcoded comprehensive map. Merged with live Data Store when deployed.
# The descriptions here are the authoritative source — Data Store provides the actual column list.
STATIC_SCHEMA = {
    "CaseMaster": {
        "ROWID": {"type": "INT", "desc": "Auto-generated row ID (use instead of CaseMasterID)"},
        "CrimeNo": {"type": "VARCHAR", "desc": "FIR number"},
        "CaseNo": {"type": "VARCHAR", "desc": "Internal case number"},
        "CrimeRegisteredDate": {"type": "DATE", "desc": "Date FIR registered"},
        "PolicePersonID": {"type": "INT", "desc": "FK to Employee (investigating officer)"},
        "PoliceStationID": {"type": "INT", "desc": "FK to Unit (police station)"},
        "CaeCategoryID": {"type": "INT", "desc": "FK to CaseCategory (note: not CaseCategoryID)"},
        "GravityOffenceID": {"type": "INT", "desc": "FK to GravityOffence"},
        "CrimeMajorHeadID": {"type": "INT", "desc": "FK to CrimeHead"},
        "CrimeMinorHeadID": {"type": "INT", "desc": "FK to CrimeSubHead (crime type)"},
        "CaseStatusID": {"type": "INT", "desc": "FK to CaseStatusMaster"},
        "CourtID": {"type": "INT", "desc": "FK to Court"},
        "IncidentFromDate": {"type": "DATETIME", "desc": "Crime start time"},
        "IncidentToDate": {"type": "DATETIME", "desc": "Crime end time"},
        "InfoReceivedPSDate": {"type": "DATETIME", "desc": "Info received at police station"},
        "latitide": {"type": "DECIMAL", "desc": "Latitude (note: this is the actual column name, not latitude)"},
        "longitude": {"type": "DECIMAL", "desc": "Longitude"},
        "BriedFacts": {"type": "TEXT", "desc": "Brief facts of the case (note: not BriefFacts)"},
    },
    "Accused": {
        "ROWID": {"type": "INT", "desc": "Auto-generated row ID"},
        "CaseMasterID": {"type": "INT", "desc": "FK to CaseMaster"},
        "AccusedName": {"type": "VARCHAR", "desc": "Accused name"},
        "AgeYear": {"type": "INT", "desc": "Age at time of crime"},
        "GenderID": {"type": "INT", "desc": "Gender (1=Male, 2=Female)"},
        "PersonID": {"type": "VARCHAR", "desc": "Unique person identifier for cross-case matching"},
    },
    "ComplainantDetails": {
        "ROWID": {"type": "INT", "desc": "Auto-generated row ID"},
        "CaseMasterID": {"type": "INT", "desc": "FK to CaseMaster"},
        "ComplainantName": {"type": "VARCHAR", "desc": "Complainant name"},
        "AgeYear": {"type": "INT", "desc": "Age"},
        "OccupationID": {"type": "INT", "desc": "FK to OccupationMaster"},
        "ReligionID": {"type": "INT", "desc": "FK to ReligionMaster"},
        "CasteID": {"type": "INT", "desc": "FK to CasteMaster"},
        "GenderID": {"type": "INT", "desc": "Gender (1=Male, 2=Female)"},
    },
    "Victim": {
        "ROWID": {"type": "INT", "desc": "Auto-generated row ID"},
        "CaseMasterID": {"type": "INT", "desc": "FK to CaseMaster"},
        "VictimName": {"type": "VARCHAR", "desc": "Victim name"},
        "AgeYear": {"type": "INT", "desc": "Age"},
        "GenderID": {"type": "INT", "desc": "Gender (1=Male, 2=Female)"},
        "VictimPolice": {"type": "VARCHAR", "desc": "Is victim also police (Yes/No)"},
    },
    "District": {
        "DistrictID": {"type": "INT", "desc": "PK"},
        "DistrictName": {"type": "VARCHAR", "desc": "District name"},
        "StateID": {"type": "INT", "desc": "FK to State"},
        "Active": {"type": "BOOL", "desc": "Active flag"},
    },
    "CrimeHead": {
        "CrimeHeadID": {"type": "INT", "desc": "PK"},
        "CrimeGroupName": {"type": "VARCHAR", "desc": "Crime group name (Property, Violent, etc.)"},
        "Active": {"type": "BOOL", "desc": "Active flag"},
    },
    "CrimeSubHead": {
        "CrimeSubHeadID": {"type": "INT", "desc": "PK"},
        "CrimeHeadID": {"type": "INT", "desc": "FK to CrimeHead"},
        "CrimeHeadName": {"type": "VARCHAR", "desc": "Crime type name (Theft, Murder, Robbery, etc.)"},
        "SeqID": {"type": "INT", "desc": "Display sequence"},
    },
    "Unit": {
        "UnitID": {"type": "INT", "desc": "PK"},
        "UnitName": {"type": "VARCHAR", "desc": "Police station name"},
        "TypeID": {"type": "INT", "desc": "FK to UnitType"},
        "ParentUnit": {"type": "INT", "desc": "Parent unit ID"},
        "NationalityID": {"type": "INT", "desc": "Nationality"},
        "StateID": {"type": "INT", "desc": "FK to State"},
        "DistrictID": {"type": "INT", "desc": "FK to District"},
        "Active": {"type": "BOOL", "desc": "Active flag"},
    },
    "Employee": {
        "EmployeeID": {"type": "INT", "desc": "PK"},
        "DistrictID": {"type": "INT", "desc": "FK to District"},
        "UnitID": {"type": "INT", "desc": "FK to Unit"},
        "RankID": {"type": "INT", "desc": "FK to Rank"},
        "DesignationID": {"type": "INT", "desc": "FK to Designation"},
        "KGID": {"type": "VARCHAR", "desc": "Unique personnel ID"},
        "FirstName": {"type": "VARCHAR", "desc": "First name"},
        "EmployeeDOB": {"type": "DATE", "desc": "Date of birth"},
        "GenderID": {"type": "INT", "desc": "Gender (1=Male, 2=Female)"},
        "AppointmentDate": {"type": "DATE", "desc": "Appointment date"},
    },
    "CaseStatusMaster": {
        "CaseStatusID": {"type": "INT", "desc": "PK"},
        "CaseStatusName": {"type": "VARCHAR", "desc": "Status name (Under Investigation, Charge Sheet Filed, Court Proceedings, Closed)"},
    },
    "Court": {
        "CourtID": {"type": "INT", "desc": "PK"},
        "CourtName": {"type": "VARCHAR", "desc": "Court name"},
        "DistrictID": {"type": "INT", "desc": "FK to District"},
        "StateID": {"type": "INT", "desc": "FK to State"},
        "Active": {"type": "BOOL", "desc": "Active flag"},
    },
    "State": {
        "StateID": {"type": "INT", "desc": "PK"},
        "StateName": {"type": "VARCHAR", "desc": "State name"},
        "NationalityID": {"type": "INT", "desc": "Nationality"},
        "Active": {"type": "BOOL", "desc": "Active flag"},
    },
    "Designation": {
        "DesignationID": {"type": "INT", "desc": "PK"},
        "DesignationName": {"type": "VARCHAR", "desc": "Designation name (Police Inspector, Constable, etc.)"},
        "Active": {"type": "BOOL", "desc": "Active flag"},
        "SortOrder": {"type": "INT", "desc": "Display order"},
    },
    "Rank": {
        "RankID": {"type": "INT", "desc": "PK"},
        "RankName": {"type": "VARCHAR", "desc": "Rank name"},
        "Hierarchy": {"type": "INT", "desc": "Rank level (lower = higher rank)"},
        "Active": {"type": "BOOL", "desc": "Active flag"},
    },
    "CaseCategory": {
        "CaseCategoryID": {"type": "INT", "desc": "PK"},
        "LookupValue": {"type": "VARCHAR", "desc": "Category (Criminal, etc.)"},
    },
    "GravityOffence": {
        "GravityOffenceID": {"type": "INT", "desc": "PK"},
        "LookupValue": {"type": "VARCHAR", "desc": "Gravity (Heinous, Lesser, etc.)"},
    },
    "UnitType": {
        "UnitTypeID": {"type": "INT", "desc": "PK"},
        "UnitTypeName": {"type": "VARCHAR", "desc": "Unit type (Police Station, Range HQ, etc.)"},
        "CityDistState": {"type": "VARCHAR", "desc": "City/district/state"},
        "Hierarchy": {"type": "INT", "desc": "Hierarchy level"},
        "Active": {"type": "BOOL", "desc": "Active flag"},
    },
    "Act": {
        "ActCode": {"type": "INT", "desc": "PK"},
        "ActDescription": {"type": "VARCHAR", "desc": "Full act description"},
        "ShortName": {"type": "VARCHAR", "desc": "Short name (IPC, CrPC, etc.)"},
        "Active": {"type": "BOOL", "desc": "Active flag"},
    },
    "Section": {
        "ActCode": {"type": "INT", "desc": "FK to Act (composite PK)"},
        "SectionCode": {"type": "VARCHAR", "desc": "Section number (302, 376, 420, etc.)"},
        "SectionDescription": {"type": "VARCHAR", "desc": "Section description"},
        "Active": {"type": "BOOL", "desc": "Active flag"},
    },
    "ActSectionAssociation": {
        "AssociationID": {"type": "INT", "desc": "PK"},
        "CaseMasterID": {"type": "INT", "desc": "FK to CaseMaster"},
        "ActID": {"type": "INT", "desc": "FK to Act"},
        "SectionID": {"type": "INT", "desc": "FK to Section"},
        "ActOrderID": {"type": "INT", "desc": "Order within act"},
        "SectionOrderID": {"type": "INT", "desc": "Order within section"},
    },
    "CrimeHeadActSection": {
        "CrimeHeadID": {"type": "INT", "desc": "FK to CrimeHead"},
        "ActCode": {"type": "INT", "desc": "FK to Act"},
        "SectionCode": {"type": "VARCHAR", "desc": "FK to Section"},
    },
    "ArrestSurrender": {
        "ROWID": {"type": "INT", "desc": "Auto-generated row ID"},
        "CaseMasterID": {"type": "INT", "desc": "FK to CaseMaster"},
        "ArrestSurrenderTypeID": {"type": "INT", "desc": "Arrest type"},
        "ArrestSurrenderDate": {"type": "DATE", "desc": "Arrest date"},
        "ArrestSurrenderStateId": {"type": "INT", "desc": "FK to State"},
        "ArrestSurrenderDistrictId": {"type": "INT", "desc": "FK to District"},
        "PoliceStationID": {"type": "INT", "desc": "FK to Unit"},
        "IOID": {"type": "INT", "desc": "Investigating officer (FK to Employee)"},
        "CourtID": {"type": "INT", "desc": "FK to Court"},
        "AccusedMasterID": {"type": "INT", "desc": "FK to Accused"},
        "IsAccused": {"type": "BOOL", "desc": "Is accused"},
        "IsComplainantAccused": {"type": "BOOL", "desc": "Is complainant also accused"},
    },
    "ChargesheetDetails": {
        "CSID": {"type": "INT", "desc": "PK"},
        "CaseMasterID": {"type": "INT", "desc": "FK to CaseMaster"},
        "csdate": {"type": "DATE", "desc": "Chargesheet date"},
        "cstype": {"type": "VARCHAR", "desc": "Chargesheet type (Final, etc.)"},
        "PolicePersonID": {"type": "INT", "desc": "FK to Employee"},
    },
    "OccupationMaster": {
        "OccupationID": {"type": "INT", "desc": "PK"},
        "OccupationName": {"type": "VARCHAR", "desc": "Occupation name (Farmer, Private Employee, etc.)"},
    },
    "CasteMaster": {
        "caste_master_id": {"type": "INT", "desc": "PK (lowercase column name)"},
        "caste_master_name": {"type": "VARCHAR", "desc": "Caste name (General, OBC, SC, etc.)"},
    },
    "ReligionMaster": {
        "ReligionID": {"type": "INT", "desc": "PK"},
        "ReligionName": {"type": "VARCHAR", "desc": "Religion name (Hindu, Muslim, Christian, etc.)"},
    },
}

COLUMN_ALIASES = {
    "latitude": "latitide", "lat": "latitide", "lng": "longitude",
    "brief_facts": "BriedFacts", "brief_fact": "BriedFacts", "brieffacts": "BriedFacts",
    "CaseCategoryID": "CaeCategoryID", "case_category_id": "CaeCategoryID",
}

ALLOWED_OPS = {"=", "!=", ">", "<", ">=", "<=", "IN"}
MAX_LIMIT = 1000


class SchemaRegistry:
    def __init__(self, catalyst_app=None):
        self._schema = dict(STATIC_SCHEMA)
        self._column_aliases = dict(COLUMN_ALIASES)
        if catalyst_app:
            self._load_from_datastore(catalyst_app)

    def _load_from_datastore(self, catalyst_app):
        """Dynamically load schema from Data Store, merging with static descriptions."""
        try:
            for table_name in list(self._schema.keys()):
                try:
                    tbl = catalyst_app.datastore().table(table_name)
                    actual_cols = {}
                    for c in tbl.get_all_columns():
                        d = c.to_dict() if hasattr(c, 'to_dict') else c
                        name = d.get("column_name", "")
                        col_type = d.get("column_type", "VARCHAR")
                        actual_cols[name] = {
                            "type": col_type,
                            "desc": self._schema.get(
                                table_name,
                                {}).get(
                                name,
                                {}).get(
                                "desc",
                                f"Column from {table_name}")}
                    if actual_cols:
                        self._schema[table_name] = actual_cols
                except Exception:
                    logger.debug("Table %s not accessible, keeping static schema", table_name)

            # Discover any new tables not in the static schema
            try:
                catalyst_app.zcql().execute_query("SELECT * FROM District LIMIT 1")
                # ZCQL doesn't provide list_tables; spot-check by known tables
                logger.info("Schema loaded dynamically from Data Store for %d tables", len(self._schema))
            except Exception:
                pass
        except Exception as e:
            logger.warning("Dynamic schema load failed, using static fallback: %s", e)

    @property
    def tables(self) -> list[str]:
        return sorted(self._schema.keys())

    def get_columns(self, table: str) -> dict:
        return self._schema.get(table, {})

    def get_column_names(self, table: str) -> list[str]:
        return list(self._schema.get(table, {}).keys())

    def resolve_column(self, col: str) -> str:
        return self._column_aliases.get(col, col)

    def table_description(self, table: str) -> str:
        cols = self._schema.get(table, {})
        items = [f"{n} ({c['type']}) — {c['desc']}" for n, c in cols.items()]
        return f"{table}: " + ", ".join(items)

    def generate_tool_def(self) -> dict:
        table_enum = self.tables
        tool = {
            "type": "function",
            "function": {
                "name": "query_datastore",
                "description": "Query crime data from the Catalyst Data Store. Returns structured records. Use this for any question about crime data — cases, accused, victims, locations, arrests, chargesheets, or legal sections.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "table": {
                            "type": "string",
                            "enum": table_enum,
                            "description": "The table to query. " + "; ".join(
                                f"{t}: {list(self.get_column_names(t))[:5]}..." for t in table_enum[:5]
                            ),
                        },
                        "columns": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Column names to return. Available per table:\n" + "\n".join(
                                f"  {t}: {', '.join(self.get_column_names(t))}" for t in table_enum
                            ),
                        },
                        "where": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "column": {"type": "string", "description": "Column name (must exist in the table)"},
                                    "operator": {"type": "string", "enum": list(ALLOWED_OPS), "description": "Comparison operator. No LIKE, no subqueries."},
                                    "value": {"description": "Filter value. Use exact match."},
                                },
                                "required": ["column", "operator", "value"],
                            },
                            "description": "Filter conditions (AND-ed). Use IN with a list of IDs for multi-value filters. No LIKE or subqueries.",
                        },
                        "group_by": {
                            "type": "string",
                            "description": "Column to GROUP BY. Use with COUNT(ROWID) in columns for aggregation.",
                        },
                        "order_by": {
                            "type": "object",
                            "properties": {
                                "column": {"type": "string"},
                                "direction": {"type": "string", "enum": ["ASC", "DESC"]},
                            },
                            "description": "Sort order. Cannot alias expressions.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": f"Max rows (1–{MAX_LIMIT}). Default 50.",
                            "maximum": MAX_LIMIT,
                            "default": 50,
                        },
                    },
                    "required": ["table", "columns"],
                },
            },
        }
        return tool

    def generate_system_prompt(self) -> str:
        lines = [
            "You are Suraksha AI, a crime intelligence assistant for Karnataka Police.",
            "",
            "You help officers query the crime database using the query_datastore tool.",
            "The database uses ZCQL (a restricted SQL dialect):",
            "- No JOINs — do multi-step queries: look up IDs first, then query the target table with IN",
            "- No LIKE — use exact = matching",
            "- No subqueries — use IN with literal IDs",
            "- COUNT(ROWID) instead of COUNT(*)",
            "- Column names are case-sensitive (use the exact names listed below)",
            "",
            "Available tables and columns:",
        ]
        for t in self.tables:
            cols = self.get_columns(t)
            parts = [f"{n} ({c['type']})" for n, c in cols.items()]
            lines.append(f"  {t}: {', '.join(parts)}")

        lines.extend([
            "",
            "For multi-step queries (e.g., 'theft cases in Bangalore'):",
            "  1. Call query_datastore on CrimeSubHead with columns=CrimeSubHeadID WHERE CrimeHeadName = 'Theft'",
            "  2. Call query_datastore on District with columns=DistrictID WHERE DistrictName = 'Bangalore Urban'",
            "  3. Call query_datastore on Unit with columns=UnitID WHERE DistrictID = <id>",
            "  4. Call query_datastore on CaseMaster with columns=... WHERE CrimeMinorHeadID IN (<ids>) AND PoliceStationID IN (<ids>)",
            "",
            "Keep answers concise and professional. Only use the query_datastore tool when data is needed.",
        ])
        return "\n".join(lines)

    def validate_columns(self, table: str, columns: list[str]) -> list[str]:
        set(self._schema.get(table, {}).keys()) | set(self._column_aliases.keys())
        bad = []
        for c in columns:
            resolved = self._column_aliases.get(c, c)
            if resolved not in self._schema.get(table, {}):
                bad.append(c)
        return bad

    def validate_tool_params(self, params: dict) -> dict:
        errors = []
        table = params.get("table")
        if not table:
            errors.append("table is required")
        elif table not in self._schema:
            errors.append(f"Unknown table '{table}'. Available: {self.tables}")

        columns = params.get("columns", [])
        if not columns or not isinstance(columns, list):
            errors.append("columns must be a non-empty array")

        if table and table in self._schema and isinstance(columns, list) and columns:
            bad_cols = self.validate_columns(table, columns)
            if bad_cols:
                valid = self.get_column_names(table)
                errors.append(f"Invalid columns for {table}: {bad_cols}. Valid: {valid}")

        where = params.get("where", [])
        if where is not None and not isinstance(where, list):
            errors.append("where must be an array")
        elif where and table and table in self._schema:
            for i, cond in enumerate(where):
                if not isinstance(cond, dict):
                    errors.append(f"where[{i}] must be an object")
                    continue
                col = cond.get("column", "")
                if col and col not in self._schema[table] and self._column_aliases.get(col) not in self._schema[table]:
                    errors.append(f"where[{i}] column '{col}' not in {table}")
                if cond.get("operator") not in ALLOWED_OPS:
                    errors.append(f"where[{i}] operator '{cond.get('operator')}' not allowed")

        group_by = params.get("group_by")
        if group_by and table and table in self._schema and group_by not in self._schema[table] and self._column_aliases.get(
                group_by) not in self._schema[table]:
            errors.append(f"group_by column '{group_by}' not in {table}")

        order_by = params.get("order_by")
        if order_by and isinstance(order_by, dict):
            col = order_by.get("column", "")
            if col and table and table in self._schema and col not in self._schema[table] and self._column_aliases.get(
                    col) not in self._schema[table]:
                errors.append(f"order_by column '{col}' not in {table}")

        limit = params.get("limit", 50)
        if not isinstance(limit, int) or limit < 1 or limit > MAX_LIMIT:
            errors.append(f"limit must be int 1–{MAX_LIMIT}")

        if errors:
            return {"valid": False, "errors": errors}
        return {"valid": True}

    def build_zcql(self, params: dict) -> str:
        table = params["table"]
        columns = params["columns"]
        where = params.get("where", [])
        group_by = params.get("group_by")
        order_by = params.get("order_by")
        limit = min(params.get("limit", 50), MAX_LIMIT)

        cols_str = ", ".join(self.resolve_column(c) for c in columns)
        sql = f"SELECT {cols_str} FROM {table}"

        if where:
            conditions = []
            for cond in where:
                col = self.resolve_column(cond["column"])
                op = cond.get("operator", "=")
                val = cond["value"]
                if op == "IN":
                    if isinstance(val, list):
                        items = [_fmt(v) for v in val]
                        conditions.append(f"{col} IN ({', '.join(items)})")
                    else:
                        conditions.append(f"{col} = {_fmt(val)}")
                else:
                    conditions.append(f"{col} {op} {_fmt(val)}")
            sql += " WHERE " + " AND ".join(conditions)

        if group_by:
            sql += f" GROUP BY {self.resolve_column(group_by)}"
        if order_by and isinstance(order_by, dict):
            sql += f" ORDER BY {self.resolve_column(order_by.get('column', ''))} {order_by.get('direction', 'ASC')}"
        sql += f" LIMIT {limit}"
        return sql


KNOWN_QUALITY_ISSUES = {
    "CaseMaster": {
        "latitide": {"type": "nullable", "note": "GPS coordinates may be missing for some cases"},
        "longitude": {"type": "nullable", "note": "GPS coordinates may be missing for some cases"},
        "BriedFacts": {"type": "nullable", "note": "Brief facts text may be empty for some cases"},
    },
    "ComplainantDetails": {
        "ROWID": {"type": "sparse", "note": "Only ~30 complainant records exist — not all cases have complainant data"},
        "OccupationID": {"type": "nullable", "note": "Occupation may not be recorded for all complainants"},
        "ReligionID": {"type": "nullable", "note": "Religion may not be recorded for all complainants"},
    },
    "Victim": {
        "ROWID": {"type": "sparse", "note": "Only ~40 victim records exist — not all cases have victim data"},
    },
    "ArrestSurrender": {
        "ROWID": {"type": "sparse", "note": "Only ~14 arrest records — not all cases lead to arrest"},
    },
    "ChargesheetDetails": {
        "CSID": {"type": "sparse", "note": "Only ~25 chargesheet records — not all cases have chargesheets filed"},
    },
    "Accused": {
        "PersonID": {"type": "nullable", "note": "PersonID may be missing — cross-case matching is limited"},
        "AgeYear": {"type": "nullable", "note": "Age may not be recorded for all accused"},
    },
}


def data_quality_warnings(table: str, columns: list[str]) -> list[str]:
    warnings = []
    table_issues = KNOWN_QUALITY_ISSUES.get(table, {})
    for col in columns:
        issue = table_issues.get(col)
        if issue:
            warnings.append(f"{table}.{col}: {issue['note']}")
    return warnings


def _fmt(val) -> str:
    if val is None:
        return "NULL"
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, (int, float)):
        return str(val)
    return f"'{str(val).replace(chr(39), chr(39)+chr(39))}'"
