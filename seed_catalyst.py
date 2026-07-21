"""POST seed data into Catalyst Data Store via import_table action."""
import json
import random
import datetime
import urllib.request
import urllib.error

API = "https://surakshaai-60076341598.development.catalystserverless.in/api/"
rng = random.Random(42)


def post(table_name, rows):
    payload = json.dumps({"action": "import_table", "params": {"table_name": table_name, "rows": rows}}).encode()
    req = urllib.request.Request(API + "?action=import_table", data=payload,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"error": e.code, "body": e.read().decode()}
    except Exception as e:
        return {"error": str(e)}


def insert(table, rows, batch=50):
    for i in range(0, len(rows), batch):
        b = rows[i:i+batch]
        r = post(table, b)
        n = r.get('inserted', 'ERR')
        e = r.get('error', '') or r.get('message', '')
        s = "OK" if r.get('inserted') else "FAIL"
        print(f"  {table}[{i}:{i+len(b)}] {s} {n if n!='ERR' else ''} {e[:120] if e else ''}")


# ── Seed data ───────────────────────────────────────────────────────────
# Using correct PK column names per STATIC_SCHEMA (no ROWID/CREATORID etc.)
insert("State", [
    {"StateID": 1, "StateName": "Karnataka", "NationalityID": 1, "Active": True},
])

insert("UnitType", [
    {"UnitTypeID": 1, "UnitTypeName": "Police Station", "CityDistState": "", "Hierarchy": 1, "Active": True},
])

insert("District", [
    {"DistrictID": 1, "DistrictName": "Bengaluru Urban", "StateID": 1, "Active": True},
    {"DistrictID": 2, "DistrictName": "Bengaluru Rural", "StateID": 1, "Active": True},
    {"DistrictID": 3, "DistrictName": "Mysuru", "StateID": 1, "Active": True},
    {"DistrictID": 4, "DistrictName": "Hubballi-Dharwad", "StateID": 1, "Active": True},
    {"DistrictID": 5, "DistrictName": "Mangaluru", "StateID": 1, "Active": True},
    {"DistrictID": 6, "DistrictName": "Belagavi", "StateID": 1, "Active": True},
])

insert("CaseCategory", [
    {"CaseCategoryID": 1, "LookupValue": "Criminal"},
])

insert("GravityOffence", [
    {"GravityOffenceID": 1, "LookupValue": "Heinous"},
    {"GravityOffenceID": 2, "LookupValue": "Non-Heinous"},
])

insert("CaseStatusMaster", [
    {"CaseStatusID": 1, "CaseStatusName": "Under Investigation"},
    {"CaseStatusID": 2, "CaseStatusName": "Charge Sheet Filed"},
    {"CaseStatusID": 3, "CaseStatusName": "Court Proceedings"},
])

insert("Court", [
    {"CourtID": 1, "CourtName": "Bengaluru Urban District Court", "DistrictID": 1, "StateID": 1, "Active": True},
    {"CourtID": 2, "CourtName": "Bengaluru Rural District Court", "DistrictID": 2, "StateID": 1, "Active": True},
    {"CourtID": 3, "CourtName": "Mysuru District Court", "DistrictID": 3, "StateID": 1, "Active": True},
    {"CourtID": 4, "CourtName": "Hubballi District Court", "DistrictID": 4, "StateID": 1, "Active": True},
    {"CourtID": 5, "CourtName": "Mangaluru District Court", "DistrictID": 5, "StateID": 1, "Active": True},
    {"CourtID": 6, "CourtName": "Belagavi District Court", "DistrictID": 6, "StateID": 1, "Active": True},
])

insert("CrimeHead", [
    {"CrimeHeadID": 1, "CrimeGroupName": "Crimes Against Person", "Active": True},
    {"CrimeHeadID": 2, "CrimeGroupName": "Crimes Against Property", "Active": True},
    {"CrimeHeadID": 3, "CrimeGroupName": "Crimes Against Women", "Active": True},
])

insert("CrimeSubHead", [
    {"CrimeSubHeadID": 1, "CrimeHeadID": 1, "CrimeHeadName": "Murder", "SeqID": 1},
    {"CrimeSubHeadID": 2, "CrimeHeadID": 1, "CrimeHeadName": "Attempt to Murder", "SeqID": 2},
    {"CrimeSubHeadID": 3, "CrimeHeadID": 1, "CrimeHeadName": "Hurt/Grievous Hurt", "SeqID": 3},
    {"CrimeSubHeadID": 4, "CrimeHeadID": 2, "CrimeHeadName": "Theft", "SeqID": 1},
    {"CrimeSubHeadID": 5, "CrimeHeadID": 2, "CrimeHeadName": "Burglary", "SeqID": 2},
    {"CrimeSubHeadID": 6, "CrimeHeadID": 2, "CrimeHeadName": "Robbery", "SeqID": 3},
    {"CrimeSubHeadID": 7, "CrimeHeadID": 3, "CrimeHeadName": "Rape", "SeqID": 1},
    {"CrimeSubHeadID": 8, "CrimeHeadID": 3, "CrimeHeadName": "Assault on Women", "SeqID": 2},
])

insert("Unit", [
    {"UnitID": 1, "UnitName": "Cubbon Park PS", "TypeID": 1, "DistrictID": 1, "StateID": 1, "Active": True},
    {"UnitID": 2, "UnitName": "Koramangala PS", "TypeID": 1, "DistrictID": 1, "StateID": 1, "Active": True},
    {"UnitID": 3, "UnitName": "Yelahanka PS", "TypeID": 1, "DistrictID": 2, "StateID": 1, "Active": True},
    {"UnitID": 4, "UnitName": "Devanahalli PS", "TypeID": 1, "DistrictID": 2, "StateID": 1, "Active": True},
    {"UnitID": 5, "UnitName": "Mysuru North PS", "TypeID": 1, "DistrictID": 3, "StateID": 1, "Active": True},
    {"UnitID": 6, "UnitName": "Mysuru South PS", "TypeID": 1, "DistrictID": 3, "StateID": 1, "Active": True},
    {"UnitID": 7, "UnitName": "Hubballi City PS", "TypeID": 1, "DistrictID": 4, "StateID": 1, "Active": True},
    {"UnitID": 8, "UnitName": "Dharwad Town PS", "TypeID": 1, "DistrictID": 4, "StateID": 1, "Active": True},
    {"UnitID": 9, "UnitName": "Mangaluru City PS", "TypeID": 1, "DistrictID": 5, "StateID": 1, "Active": True},
    {"UnitID": 10, "UnitName": "Surathkal PS", "TypeID": 1, "DistrictID": 5, "StateID": 1, "Active": True},
    {"UnitID": 11, "UnitName": "Belagavi City PS", "TypeID": 1, "DistrictID": 6, "StateID": 1, "Active": True},
    {"UnitID": 12, "UnitName": "Khanapur PS", "TypeID": 1, "DistrictID": 6, "StateID": 1, "Active": True},
])

insert("Employee", [
    {"EmployeeID": 1, "DistrictID": 1, "UnitID": 1, "RankID": 2, "DesignationID": 2,
     "KGID": "KG-001", "FirstName": "Arun Kumar", "GenderID": 1},
    {"EmployeeID": 2, "DistrictID": 1, "UnitID": 2, "RankID": 2, "DesignationID": 2,
     "KGID": "KG-002", "FirstName": "Meena Sharma", "GenderID": 2},
    {"EmployeeID": 3, "DistrictID": 2, "UnitID": 3, "RankID": 1, "DesignationID": 1,
     "KGID": "KG-003", "FirstName": "Suresh Patil", "GenderID": 1},
    {"EmployeeID": 4, "DistrictID": 3, "UnitID": 5, "RankID": 2, "DesignationID": 2,
     "KGID": "KG-004", "FirstName": "Lakshmi Devi", "GenderID": 2},
    {"EmployeeID": 5, "DistrictID": 4, "UnitID": 7, "RankID": 1, "DesignationID": 1,
     "KGID": "KG-005", "FirstName": "Rajesh Joshi", "GenderID": 1},
    {"EmployeeID": 6, "DistrictID": 5, "UnitID": 9, "RankID": 2, "DesignationID": 2,
     "KGID": "KG-006", "FirstName": "Priya Shetty", "GenderID": 2},
])

# ── CaseMaster (150 cases, 2024-01 to 2026-06) ──────────────────────────
print("\n--- CaseMaster ---")
start = datetime.date(2024, 1, 1)
end = datetime.date(2026, 6, 30)
total = (end - start).days

cases = []
for i in range(1, 151):
    dist = rng.randint(1, 6)
    station = rng.choice({1:[1,2],2:[3,4],3:[5,6],4:[7,8],5:[9,10],6:[11,12]}[dist])
    io = rng.choice({1:[1,2],2:[3],3:[4],4:[5],5:[6],6:[1]}[dist])
    csh = rng.randint(1, 8)
    ch = {1:1,2:1,3:1,4:2,5:2,6:2,7:3,8:3}[csh]
    rd = start + datetime.timedelta(days=rng.randint(0, total))
    lat = round({1:12.97,2:13.05,3:12.30,4:15.35,5:12.91,6:15.85}[dist] + rng.uniform(-0.08, 0.08), 6)
    lng = round({1:77.59,2:77.58,3:76.65,4:75.14,5:74.86,6:74.50}[dist] + rng.uniform(-0.08, 0.08), 6)
    cases.append({
        "CrimeRegisteredDate": rd.isoformat(), "CrimeNo": f"FIR/2024/{dist:03d}/{i:04d}",
        "CaseNo": f"CASE/2024/{dist:03d}/{i:04d}", "PolicePersonID": io,
        "PoliceStationID": station, "CaeCategoryID": 1,
        "GravityOffenceID": 1 if csh in (1,7) else 2,
        "CrimeMajorHeadID": ch, "CrimeMinorHeadID": csh,
        "CaseStatusID": rng.choice([1,1,1,2,2,3]), "CourtID": dist,
        "IncidentFromDate": (rd - datetime.timedelta(days=rng.randint(0,7))).isoformat(),
        "IncidentToDate": rd.isoformat(), "InfoReceivedPSDate": rd.isoformat(),
        "latitide": lat, "longitude": lng,
        "BriedFacts": f"Case {i} in district {dist}"})

insert("CaseMaster", cases)
print("\n--- Accused ---")

accused, aid = [], 0
male = ["Ravi Kumar","Suresh Patel","Mohan Singh","Venkatesh Rao","Ganesh Iyer",
        "Mahesh Reddy","Siddharth Jain","Prakash Nair","Dinesh Shetty","Arun Naik",
        "Karthik Bhat","Naveen Hegde","Vinay Acharya","Rahul Verma","Deepak Yadav"]
for cid in range(1, 151):
    for _ in range(rng.choices([1,2,3], weights=[60,30,10])[0]):
        nm = rng.choice(male)
        accused.append({"CaseMasterID": cid, "AccusedName": nm, "AgeYear": rng.randint(22,55),
                        "GenderID": 1, "PersonID": f"PER-{abs(hash(nm)) % 10000:04d}"})
insert("Accused", accused, 30)

comp = []
female = ["Sunita Devi","Lakshmi Bai","Kavita Joshi","Anita Shetty","Pooja Reddy",
          "Neha Sharma","Radha Krishnan","Meena Kumari","Shanti Devi","Rekha Singh",
          "Sneha Patil","Asha Nair","Maya Bhat"]
for cid in range(1, 151):
    if rng.random() < 0.65:
        nm = rng.choice(female + male)
        comp.append({"CaseMasterID": cid, "ComplainantName": nm, "AgeYear": rng.randint(25,60),
                     "OccupationID": rng.randint(1,6), "ReligionID": rng.randint(1,5),
                     "CasteID": rng.randint(1,5), "GenderID": 2 if nm in female else 1})
insert("ComplainantDetails", comp, 30)

vic = []
for cid in range(1, 151):
    if rng.random() < 0.45:
        nm = rng.choice(female + male)
        vic.append({"CaseMasterID": cid, "VictimName": nm, "AgeYear": rng.randint(18,60),
                    "GenderID": 2 if nm in female else 1,
                    "VictimPolice": rng.choice(["No","No","No","Yes"])})
insert("Victim", vic, 30)

print("\nDone. Trigger analytics webhook to verify.")
