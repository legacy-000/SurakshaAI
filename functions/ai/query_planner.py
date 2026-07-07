from models.dto import IntentResultDTO, ExtractedEntityDTO, RetrievedSchemaContextDTO, QueryPlanDTO


class QueryPlanner:
    def plan(self, intent: IntentResultDTO, entities: list[ExtractedEntityDTO],
             schema_context: RetrievedSchemaContextDTO) -> QueryPlanDTO:
        tables = ["CaseMaster"]
        joins = []
        filters = []
        aggregations = []
        limit = 100

        for e in entities:
            if e.entity_type == "year":
                filters.append({
                    "table": "CaseMaster", "column": "CrimeRegisteredDate",
                    "operator": "YEAR", "value": e.entity_value
                })
            elif e.entity_type == "location":
                filters.append({
                    "table": "District", "column": "DistrictName",
                    "operator": "LIKE", "value": e.entity_value
                })
                if "District" not in tables:
                    tables.append("District")
                    joins.append({
                        "from": "CaseMaster", "to": "Unit",
                        "from_key": "PoliceStationID", "to_key": "UnitID"
                    })
                    joins.append({
                        "from": "Unit", "to": "District",
                        "from_key": "DistrictID", "to_key": "DistrictID"
                    })
            elif e.entity_type == "crime_type":
                filters.append({
                    "table": "CrimeSubHead", "column": "CrimeHeadName",
                    "operator": "LIKE", "value": e.entity_value
                })
                if "CrimeSubHead" not in tables:
                    tables.append("CrimeSubHead")
                    joins.append({
                        "from": "CaseMaster", "to": "CrimeSubHead",
                        "from_key": "CrimeMinorHeadID", "to_key": "CrimeSubHeadID"
                    })

        if intent.intent_type in ("TREND_QUERY",):
            aggregations.append({
                "type": "COUNT", "column": "CaseMasterID", "alias": "case_count"
            })
            aggregations.append({
                "type": "GROUP_BY", "column": "CrimeRegisteredDate"
            })

        return QueryPlanDTO(
            tables=tables, joins=joins, filters=filters,
            aggregations=aggregations, limit=limit
        )
