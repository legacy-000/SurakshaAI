import csv, json, sys, time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

URL = "http://localhost:3000/api/suraksha_ai"

def post(action, table_name, rows):
    body = json.dumps({"action": action, "params": {"table_name": table_name, "rows": rows}}).encode()
    req = Request(URL, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(req, timeout=60) as resp:
            return json.loads(resp.read())
    except HTTPError as e:
        return json.loads(e.read())

def insert(table, rows):
    for i in range(0, len(rows), 50):
        batch = rows[i:i+50]
        res = post("import_table", table, batch)
        if res.get("status") != "success":
            msg = str(res)
            if "Duplicate" in msg:
                print(f"  batch {i//50}: duplicate (skipped)")
                continue
            print(f"  batch {i//50}: FAILED {res}")
        time.sleep(0.2)

# ── Lookup tables ──
SEED_TABLES = [
    ("Act", [
        {"ActCode": 1, "ActDescription": "Indian Penal Code (IPC) 1860", "ShortName": "IPC", "Active": True},
        {"ActCode": 2, "ActDescription": "Code of Criminal Procedure 1973", "ShortName": "CrPC", "Active": True},
        {"ActCode": 3, "ActDescription": "Indian Evidence Act 1872", "ShortName": "IEA", "Active": True},
        {"ActCode": 4, "ActDescription": "Indian Arms Act 1959", "ShortName": "Arms", "Active": True},
        {"ActCode": 5, "ActDescription": "Narcotic Drugs and Psychotropic Substances Act 1985", "ShortName": "NDPS", "Active": True},
    ]),
    ("Section", [
        {"ActCode": 1, "SectionCode": "302", "SectionDescription": "Punishment for murder", "Active": True},
        {"ActCode": 1, "SectionCode": "307", "SectionDescription": "Attempt to murder", "Active": True},
        {"ActCode": 1, "SectionCode": "323", "SectionDescription": "Punishment for voluntarily causing hurt", "Active": True},
        {"ActCode": 1, "SectionCode": "324", "SectionDescription": "Voluntarily causing hurt by dangerous weapons", "Active": True},
        {"ActCode": 1, "SectionCode": "354", "SectionDescription": "Assault or criminal force to woman with intent to outrage her modesty", "Active": True},
        {"ActCode": 1, "SectionCode": "376", "SectionDescription": "Punishment for rape", "Active": True},
        {"ActCode": 1, "SectionCode": "379", "SectionDescription": "Punishment for theft", "Active": True},
        {"ActCode": 1, "SectionCode": "380", "SectionDescription": "Theft in dwelling house", "Active": True},
        {"ActCode": 1, "SectionCode": "392", "SectionDescription": "Punishment for robbery", "Active": True},
        {"ActCode": 1, "SectionCode": "394", "SectionDescription": "Voluntarily causing hurt in committing robbery", "Active": True},
        {"ActCode": 1, "SectionCode": "395", "SectionDescription": "Punishment for dacoity", "Active": True},
        {"ActCode": 1, "SectionCode": "397", "SectionDescription": "Robbery or dacoity with attempt to cause death or grievous hurt", "Active": True},
        {"ActCode": 1, "SectionCode": "420", "SectionDescription": "Cheating and dishonestly inducing delivery of property", "Active": True},
        {"ActCode": 1, "SectionCode": "454", "SectionDescription": "Lurking house-trespass or house-breaking", "Active": True},
        {"ActCode": 1, "SectionCode": "457", "SectionDescription": "Lurking house-trespass or house-breaking by night", "Active": True},
    ]),
    ("CasteMaster", [
        {"caste_master_id": 1, "caste_master_name": "General"},
        {"caste_master_id": 2, "caste_master_name": "OBC"},
        {"caste_master_id": 3, "caste_master_name": "SC"},
        {"caste_master_id": 4, "caste_master_name": "ST"},
        {"caste_master_id": 5, "caste_master_name": "Other"},
    ]),
    ("ReligionMaster", [
        {"ReligionID": 1, "ReligionName": "Hindu"},
        {"ReligionID": 2, "ReligionName": "Muslim"},
        {"ReligionID": 3, "ReligionName": "Christian"},
        {"ReligionID": 4, "ReligionName": "Sikh"},
        {"ReligionID": 5, "ReligionName": "Jain"},
    ]),
    ("OccupationMaster", [
        {"OccupationID": 1, "OccupationName": "Private Employee"},
        {"OccupationID": 2, "OccupationName": "Government Employee"},
        {"OccupationID": 3, "OccupationName": "Business"},
        {"OccupationID": 4, "OccupationName": "Farmer"},
        {"OccupationID": 5, "OccupationName": "Student"},
        {"OccupationID": 6, "OccupationName": "Unemployed"},
    ]),
    ("Designation", [
        {"DesignationID": 1, "DesignationName": "Police Inspector", "Active": True, "SortOrder": 1},
        {"DesignationID": 2, "DesignationName": "Sub-Inspector", "Active": True, "SortOrder": 2},
        {"DesignationID": 3, "DesignationName": "Head Constable", "Active": True, "SortOrder": 3},
        {"DesignationID": 4, "DesignationName": "Constable", "Active": True, "SortOrder": 4},
        {"DesignationID": 5, "DesignationName": "Deputy Superintendent", "Active": True, "SortOrder": 5},
    ]),
    ("Rank", [
        {"RankID": 1, "RankName": "Inspector", "Hierarchy": 1, "Active": True},
        {"RankID": 2, "RankName": "Sub-Inspector", "Hierarchy": 2, "Active": True},
        {"RankID": 3, "RankName": "Head Constable", "Hierarchy": 3, "Active": True},
        {"RankID": 4, "RankName": "Constable", "Hierarchy": 4, "Active": True},
        {"RankID": 5, "RankName": "DySP", "Hierarchy": 5, "Active": True},
    ]),
]

# ── Relation tables (reference existing IDs) ──
CrimeHeadActSection_DATA = [
    {"CrimeHeadID": 1, "ActCode": 1, "SectionCode": "379"},  # Property → IPC 379 theft
    {"CrimeHeadID": 1, "ActCode": 1, "SectionCode": "380"},
    {"CrimeHeadID": 1, "ActCode": 1, "SectionCode": "392"},
    {"CrimeHeadID": 2, "ActCode": 1, "SectionCode": "302"},  # Violent → IPC 302 murder
    {"CrimeHeadID": 2, "ActCode": 1, "SectionCode": "307"},
    {"CrimeHeadID": 2, "ActCode": 1, "SectionCode": "323"},
    {"CrimeHeadID": 2, "ActCode": 1, "SectionCode": "324"},
    {"CrimeHeadID": 3, "ActCode": 1, "SectionCode": "420"},  # Economic → IPC 420 cheating
    {"CrimeHeadID": 3, "ActCode": 1, "SectionCode": "376"},
]

# GenderID: 1=Male, 2=Female

# We have 389 CaseMaster rows with ROWID 1..389 (plus 1 orphan test row if still there).
# Accused has 144 rows with ROWID 1..144 referencing CaseMasterID values from CSV.
# For simplicity, link the detail tables to the first N CaseMaster rows.

COMPLAINANT_DATA = []
VICTIM_DATA = []
ARREST_DATA = []
CHARGESHEET_DATA = []

# Generate realistic sample data for first 100 CaseMaster rows
import random
random.seed(42)

male_names = ["Ramesh", "Suresh", "Mahesh", "Dinesh", "Rajesh", "Anil", "Sunil", "Vijay", "Arjun", "Kiran",
              "Prakash", "Manjunath", "Venkatesh", "Nagaraj", "Girish", "Santhosh", "Praveen", "Mohan", "Ravi", "Kumar"]
female_names = ["Lakshmi", "Saraswathi", "Parvathi", "Anita", "Sunitha", "Geetha", "Rekha", "Asha", "Deepa", "Nandini",
                "Shwetha", "Pavithra", "Kavitha", "Sneha", "Divya", "Bhavya", "Pooja", "Neha", "Priya", "Shanthi"]

for case_id in range(1, 101):
    # 2 complainants per 10 cases
    if case_id % 10 in (1, 5):
        name = random.choice(male_names)
        COMPLAINANT_DATA.append({
            "CaseMasterID": case_id,
            "ComplainantName": name,
            "AgeYear": random.randint(22, 65),
            "OccupationID": random.randint(1, 6),
            "ReligionID": random.randint(1, 5),
            "CasteID": random.randint(1, 5),
            "GenderID": 1,
        })
    elif case_id % 10 == 8:
        name = random.choice(female_names)
        COMPLAINANT_DATA.append({
            "CaseMasterID": case_id,
            "ComplainantName": name,
            "AgeYear": random.randint(20, 55),
            "OccupationID": random.randint(1, 6),
            "ReligionID": random.randint(1, 5),
            "CasteID": random.randint(1, 5),
            "GenderID": 2,
        })

    # Victim for ~40% of cases
    if case_id % 10 in (2, 3, 6, 9):
        is_female = random.random() < 0.4
        name = random.choice(female_names if is_female else male_names)
        VICTIM_DATA.append({
            "CaseMasterID": case_id,
            "VictimName": name,
            "AgeYear": random.randint(18, 70),
            "GenderID": 2 if is_female else 1,
            "VictimPolice": "No",
        })

    # Arrest/Surrender for ~30% of cases
    if case_id % 7 == 0:
        ARREST_DATA.append({
            "CaseMasterID": case_id,
            "ArrestSurrenderTypeID": 1,
            "ArrestSurrenderDate": f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
            "ArrestSurrenderStateId": 1,
            "ArrestSurrenderDistrictId": 1,
            "PoliceStationID": random.randint(1, 10),
            "IOID": random.choice([14, 65]),
            "CourtID": 1,
            "AccusedMasterID": case_id if case_id <= 144 else 1,
            "IsAccused": True,
            "IsComplainantAccused": False,
        })


    # Chargesheet for ~25% of cases
    if case_id % 4 == 0:
        CHARGESHEET_DATA.append({
            "CSID": case_id,
            "CaseMasterID": case_id,
            "csdate": f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
            "cstype": "Final",
            "PolicePersonID": random.choice([14, 65]),
        })

# ActSectionAssociation links CaseMaster to Act+Section
ACT_SECTION_ASSOC_DATA = []
for case_id in range(1, 101):
    if case_id % 5 == 0:
        ACT_SECTION_ASSOC_DATA.append({
            "AssociationID": case_id,
            "CaseMasterID": case_id,
            "ActID": 1,
            "SectionID": random.randint(1, 15),
            "ActOrderID": 1,
            "SectionOrderID": 1,
        })

if __name__ == "__main__":
    print("=== Lookup tables ===")
    for table, rows in SEED_TABLES:
        print(f"{table}: {len(rows)} rows...", end=" ")
        sys.stdout.flush()
        insert(table, rows)
        print("done")

    print("\n=== CrimeHead -> Act+Section ===")
    print(f"CrimeHeadActSection: {len(CrimeHeadActSection_DATA)} rows...", end=" ")
    insert("CrimeHeadActSection", CrimeHeadActSection_DATA)
    print("done")

    print("\n=== CaseMaster -> Act+Section ===")
    print(f"ActSectionAssociation: {len(ACT_SECTION_ASSOC_DATA)} rows...", end=" ")
    insert("ActSectionAssociation", ACT_SECTION_ASSOC_DATA)
    print("done")

    print("\n=== ComplainantDetails ===")
    print(f"{len(COMPLAINANT_DATA)} rows...", end=" ")
    insert("ComplainantDetails", COMPLAINANT_DATA)
    print("done")

    print("\n=== Victim ===")
    print(f"{len(VICTIM_DATA)} rows...", end=" ")
    insert("Victim", VICTIM_DATA)
    print("done")

    print("\n=== ArrestSurrender ===")
    print(f"{len(ARREST_DATA)} rows...", end=" ")
    insert("ArrestSurrender", ARREST_DATA)
    print("done")

    print("\n=== ChargesheetDetails ===")
    print(f"{len(CHARGESHEET_DATA)} rows...", end=" ")
    insert("ChargesheetDetails", CHARGESHEET_DATA)
    print("done")

    print("\nAll done!")
