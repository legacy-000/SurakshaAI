import csv, json, sys, time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

BASE = Path(__file__).resolve().parent / "catalyst_import_data"
URL = "http://localhost:3000/api/suraksha_ai"

# Catalyst table columns have typos; map CSV -> Catalyst
COLUMN_MAP = {
    "CaseMaster": {
        "CaseMasterID": None,  # auto ROWID
        "latitude": "latitide",
        "BriefFacts": "BriedFacts",
        "CaseCategoryID": "CaeCategoryID",
    },
    "Accused": {
        "AccusedMasterID": None,  # auto ROWID
    },
}

# Tables where Active is boolean (convert 1/0 to true/false)
BOOL_TABLES = {"District", "CrimeHead", "Unit", "State", "UnitType", "Court"}

def post(action, table_name, rows):
    body = json.dumps({"action": action, "params": {"table_name": table_name, "rows": rows}}).encode()
    req = Request(URL, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(req, timeout=60) as resp:
            return json.loads(resp.read())
    except HTTPError as e:
        return json.loads(e.read())

def read_csv(name):
    rows = []
    with open(BASE / name, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cleaned = {}
            for k, v in row.items():
                k = k.strip()
                if v is None:
                    cleaned[k] = None
                else:
                    v = v.strip()
                    if v.isdigit():
                        cleaned[k] = int(v)
                    elif v.replace(".", "", 1).replace("-", "", 1).isdigit() and v.count(".") <= 1:
                        cleaned[k] = float(v) if "." in v else int(v)
                    elif v.lower() in ("true", "false"):
                        cleaned[k] = v.lower() == "true"
                    else:
                        cleaned[k] = v
            rows.append(cleaned)
    return rows

def map_columns(table, rows):
    """Rename/drop columns per CATALOG_MAP, convert booleans."""
    mapping = COLUMN_MAP.get(table, {})
    is_bool = table in BOOL_TABLES
    out = []
    for row in rows:
        remapped = {}
        for csv_col, val in row.items():
            target = mapping.get(csv_col, csv_col)
            if target is None:
                continue  # skip (auto-generated)
            if is_bool and target == "Active":
                remapped[target] = bool(val)
            else:
                remapped[target] = val
        out.append(remapped)
    return out

SEED = [
    ("State", [
        {"StateID": 1, "StateName": "Karnataka", "NationalityID": 1, "Active": True},
    ]),
    ("UnitType", [
        {"UnitTypeID": 1, "UnitTypeName": "Police Station", "Hierarchy": 1, "Active": True},
    ]),
    ("CaseCategory", [
        {"CaseCategoryID": 1, "LookupValue": "Criminal"},
    ]),
    ("GravityOffence", [
        {"GravityOffenceID": 1, "LookupValue": "Heinous"},
    ]),
    ("CaseStatusMaster", [
        {"CaseStatusID": 1, "CaseStatusName": "Under Investigation"},
        {"CaseStatusID": 2, "CaseStatusName": "Charge Sheet Filed"},
        {"CaseStatusID": 3, "CaseStatusName": "Court Proceedings"},
    ]),
    ("Court", [
        {"CourtID": 1, "CourtName": "Bangalore Urban District Court", "DistrictID": 1, "StateID": 1, "Active": True},
    ]),
    ("Employee", [
        {"EmployeeID": 14, "DistrictID": 1, "UnitID": 1, "RankID": 1, "DesignationID": 1,
         "KGID": "KG-014", "FirstName": "Officer", "EmployeeDOB": "1985-01-01", "GenderID": 1,
         "AppointmentDate": "2010-01-01"},
        {"EmployeeID": 65, "DistrictID": 1, "UnitID": 1, "RankID": 1, "DesignationID": 1,
         "KGID": "KG-065", "FirstName": "SI", "EmployeeDOB": "1980-01-01", "GenderID": 1,
         "AppointmentDate": "2005-01-01"},
    ]),
]

CSV_FILES = [
    ("District", "District.csv"),
    ("CrimeHead", "CrimeHead.csv"),
    ("CrimeSubHead", "CrimeSubHead.csv"),
    ("Unit", "Unit.csv"),
    ("CaseMaster", "CaseMaster.csv"),
    ("Accused", "Accused.csv"),
]

if __name__ == "__main__":
    for table, rows in SEED:
        print(f"Inserting {len(rows)} rows into {table}...", end=" ")
        sys.stdout.flush()
        res = post("import_table", table, rows)
        status = res.get("status", res.get("error", ""))
        if "DUPLICATE" in status or "duplicate" in str(res).lower():
            print("skipped (already exists)")
        else:
            print(status)
        time.sleep(0.3)

    for table, filename in CSV_FILES:
        raw = read_csv(filename)
        rows = map_columns(table, raw)
        print(f"Inserting {len(rows)} rows into {table} from {filename}...", end=" ")
        sys.stdout.flush()
        for i in range(0, len(rows), 50):
            batch = rows[i:i+50]
            res = post("import_table", table, batch)
            if res.get("status") != "success":
                msg = str(res)
                if "Duplicate" in msg:
                    print(f"skipped batch {i//50} (duplicates)", end=" ")
                    continue
                print(f"FAILED at batch {i//50}: {res}")
                break
            time.sleep(0.2)
        else:
            print(f"done ({len(rows)} rows)")
