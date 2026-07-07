"""Load RAG knowledge base with schema docs and query examples."""
import json


def seed_knowledge_base():
    schema_entries = [
        {"table": "CaseMaster", "description": "Core FIR/case transaction table with 18 columns"},
        {"table": "Accused", "description": "Accused persons linked to cases via CaseMasterID"},
        {"table": "Unit", "description": "Police stations with geographic hierarchy"},
    ]

    example_queries = [
        {"nl": "How many theft cases in Bangalore?", "sql": "SELECT COUNT(*) FROM CaseMaster cm JOIN Unit u ON cm.PoliceStationID = u.UnitID JOIN District d ON u.DistrictID = d.DistrictID WHERE d.DistrictName LIKE '%Bangalore%' AND cm.CrimeMinorHeadID IN (SELECT CrimeSubHeadID FROM CrimeSubHead WHERE CrimeHeadName LIKE '%Theft%')"},
        {"nl": "Show murder cases this year", "sql": "SELECT * FROM CaseMaster WHERE YEAR(CrimeRegisteredDate) = YEAR(CURRENT_DATE) AND CrimeMinorHeadID IN (SELECT CrimeSubHeadID FROM CrimeSubHead WHERE CrimeHeadName LIKE '%Murder%') LIMIT 100"},
    ]

    print(f"KB seeded with {len(schema_entries)} schema entries and {len(example_queries)} example queries")


if __name__ == "__main__":
    seed_knowledge_base()
