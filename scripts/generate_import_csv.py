import os
import csv
import random
from datetime import datetime, timedelta

def main():
    print("Generating deterministic CSV files for Zoho Catalyst Datastore import...")
    
    # Create export directory
    export_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "catalyst_import_data")
    os.makedirs(export_dir, exist_ok=True)
    
    # Set seed for deterministic generation
    random.seed(42)
    
    # 1. District Data
    districts = [
        {"DistrictID": 1, "DistrictName": "Bangalore Urban", "StateID": 1, "Active": 1},
        {"DistrictID": 2, "DistrictName": "Bangalore Rural", "StateID": 1, "Active": 1},
        {"DistrictID": 3, "DistrictName": "Mysuru", "StateID": 1, "Active": 1},
        {"DistrictID": 4, "DistrictName": "Hubli", "StateID": 1, "Active": 1},
        {"DistrictID": 5, "DistrictName": "Mangalore", "StateID": 1, "Active": 1},
        {"DistrictID": 6, "DistrictName": "Belgaum", "StateID": 1, "Active": 1},
        {"DistrictID": 7, "DistrictName": "Dharwad", "StateID": 1, "Active": 1},
        {"DistrictID": 8, "DistrictName": "Shivamogga", "StateID": 1, "Active": 1},
        {"DistrictID": 9, "DistrictName": "Tumkur", "StateID": 1, "Active": 1},
        {"DistrictID": 10, "DistrictName": "Kalaburagi", "StateID": 1, "Active": 1}
    ]
    
    district_path = os.path.join(export_dir, "District.csv")
    with open(district_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["DistrictID", "DistrictName", "StateID", "Active"])
        writer.writeheader()
        writer.writerows(districts)
    print(f"Generated {district_path} ({len(districts)} rows)")

    # 2. Unit Data (Police Stations)
    units = []
    unit_id_counter = 1
    for d in districts:
        num_stations = {
            1: 12, 2: 8, 3: 10, 4: 7, 5: 6, 6: 8, 7: 5, 8: 5, 9: 6, 10: 5
        }[d["DistrictID"]]
        for s in range(1, num_stations + 1):
            units.append({
                "UnitID": unit_id_counter,
                "UnitName": f"{d['DistrictName']} PS {s}",
                "TypeID": 1,
                "ParentUnit": 0,
                "NationalityID": 1,
                "StateID": 1,
                "DistrictID": d["DistrictID"],
                "Active": 1
            })
            unit_id_counter += 1
            
    unit_path = os.path.join(export_dir, "Unit.csv")
    with open(unit_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["UnitID", "UnitName", "TypeID", "ParentUnit", "NationalityID", "StateID", "DistrictID", "Active"])
        writer.writeheader()
        writer.writerows(units)
    print(f"Generated {unit_path} ({len(units)} rows)")

    # 3. CrimeHead Data
    crime_heads = [
        {"CrimeHeadID": 1, "CrimeGroupName": "Property Crimes", "Active": 1},
        {"CrimeHeadID": 2, "CrimeGroupName": "Crimes Against Body", "Active": 1},
        {"CrimeHeadID": 3, "CrimeGroupName": "White Collar Crimes", "Active": 1}
    ]
    crime_head_path = os.path.join(export_dir, "CrimeHead.csv")
    with open(crime_head_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["CrimeHeadID", "CrimeGroupName", "Active"])
        writer.writeheader()
        writer.writerows(crime_heads)
    print(f"Generated {crime_head_path} ({len(crime_heads)} rows)")

    # 4. CrimeSubHead Data
    crime_subheads = [
        {"CrimeSubHeadID": 1, "CrimeHeadID": 1, "CrimeHeadName": "Theft", "SeqID": 1},
        {"CrimeSubHeadID": 2, "CrimeHeadID": 1, "CrimeHeadName": "Robbery", "SeqID": 2},
        {"CrimeSubHeadID": 3, "CrimeHeadID": 2, "CrimeHeadName": "Murder", "SeqID": 3},
        {"CrimeSubHeadID": 4, "CrimeHeadID": 2, "CrimeHeadName": "Assault", "SeqID": 4},
        {"CrimeSubHeadID": 5, "CrimeHeadID": 2, "CrimeHeadName": "Kidnapping", "SeqID": 5},
        {"CrimeSubHeadID": 6, "CrimeHeadID": 1, "CrimeHeadName": "Burglary", "SeqID": 6},
        {"CrimeSubHeadID": 7, "CrimeHeadID": 3, "CrimeHeadName": "Cheating", "SeqID": 7},
        {"CrimeSubHeadID": 8, "CrimeHeadID": 1, "CrimeHeadName": "Snatching", "SeqID": 8}
    ]
    crime_subhead_path = os.path.join(export_dir, "CrimeSubHead.csv")
    with open(crime_subhead_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["CrimeSubHeadID", "CrimeHeadID", "CrimeHeadName", "SeqID"])
        writer.writeheader()
        writer.writerows(crime_subheads)
    print(f"Generated {crime_subhead_path} ({len(crime_subheads)} rows)")

    # 5. CaseMaster & Accused Data
    cases = []
    accused_records = []
    
    crime_types_mapping = {
        "Theft": 1, "Robbery": 2, "Murder": 3, "Assault": 4,
        "Kidnapping": 5, "Burglary": 6, "Cheating": 7, "Snatching": 8
    }
    
    statuses = ["Under Investigation", "Charge Sheeted", "Closed", "Pending"]
    status_ids = { "Under Investigation": 1, "Charge Sheeted": 2, "Closed": 3, "Pending": 4 }
    
    repeat_accused_profiles = [
        {"name": "Ravi Kumar", "cases": 8, "districts": [1, 2]},
        {"name": "Suresh P", "cases": 5, "districts": [1, 3]},
        {"name": "Rajesh K", "cases": 4, "districts": [1]},
        {"name": "Manoj R", "cases": 3, "districts": [3, 4]},
        {"name": "Venkatesh G", "cases": 3, "districts": [1, 2]}
    ]
    
    # Generate cases
    case_id_counter = 1
    accused_id_counter = 1
    
    # Group units by district for easy lookup
    units_by_district = {}
    for u in units:
        units_by_district.setdefault(u["DistrictID"], []).append(u)
        
    for d in districts:
        dist_units = units_by_district.get(d["DistrictID"], [])
        for u in dist_units:
            station_cases = random.randint(3, 8)
            for _ in range(station_cases):
                case_id = case_id_counter
                date = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 545))
                crime_name = random.choice(list(crime_types_mapping.keys()))
                crime_minor_head_id = crime_types_mapping[crime_name]
                status_name = random.choice(statuses)
                status_id = status_ids[status_name]
                
                # Get lat bounds
                lat_bounds = {
                    "Bangalore Urban": (12.85, 13.1),
                    "Bangalore Rural": (12.7, 13.0),
                    "Mysuru": (12.2, 12.4),
                    "Hubli": (15.3, 15.5),
                    "Mangalore": (12.8, 13.0),
                }.get(d["DistrictName"], (12.0, 16.0))
                
                lat = round(random.uniform(lat_bounds[0], lat_bounds[1]), 6)
                lng = round(random.uniform(74.0, 78.5), 6)
                
                cases.append({
                    "CaseMasterID": case_id,
                    "CrimeNo": f"10{d['DistrictID']:02d}{u['UnitID']:02d}2024{case_id:05d}",
                    "CaseNo": f"CASE-{case_id}",
                    "CrimeRegisteredDate": date.strftime("%Y-%m-%d"),
                    "PolicePersonID": random.randint(1, 100),
                    "PoliceStationID": u["UnitID"],
                    "CaseCategoryID": 1,
                    "GravityOffenceID": 1,
                    "CrimeMajorHeadID": 1,
                    "CrimeMinorHeadID": crime_minor_head_id,
                    "CaseStatusID": status_id,
                    "CourtID": 1,
                    "IncidentFromDate": (date - timedelta(hours=random.randint(1, 24))).strftime("%Y-%m-%d %H:%M:%S"),
                    "IncidentToDate": date.strftime("%Y-%m-%d %H:%M:%S"),
                    "InfoReceivedPSDate": date.strftime("%Y-%m-%d %H:%M:%S"),
                    "latitude": lat,
                    "longitude": lng,
                    "BriefFacts": f"{crime_name} reported at {d['DistrictName']} on {date.strftime('%Y-%m-%d')}"
                })
                case_id_counter += 1

    # Map repeat accused to generated cases
    for acc in repeat_accused_profiles:
        eligible_cases = [c for c in cases if any(u["DistrictID"] in acc["districts"] for u in units if u["UnitID"] == c["PoliceStationID"])]
        if not eligible_cases:
            eligible_cases = cases
            
        chosen_cases = random.sample(eligible_cases, min(acc["cases"], len(eligible_cases)))
        for c in chosen_cases:
            accused_records.append({
                "AccusedMasterID": accused_id_counter,
                "CaseMasterID": c["CaseMasterID"],
                "AccusedName": acc["name"],
                "AgeYear": random.randint(25, 45),
                "GenderID": 1,
                "PersonID": f"P-{random.randint(10000, 99999)}"
            })
            accused_id_counter += 1

    # Add some random non-repeat accused
    for c in cases:
        if random.random() < 0.3:
            # 30% chance of having another accused
            accused_records.append({
                "AccusedMasterID": accused_id_counter,
                "CaseMasterID": c["CaseMasterID"],
                "AccusedName": f"Accused_{accused_id_counter}",
                "AgeYear": random.randint(18, 60),
                "GenderID": random.choice([1, 2]),
                "PersonID": f"P-{random.randint(10000, 99999)}"
            })
            accused_id_counter += 1

    # Save CaseMaster.csv
    case_path = os.path.join(export_dir, "CaseMaster.csv")
    with open(case_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            "CaseMasterID", "CrimeNo", "CaseNo", "CrimeRegisteredDate", "PolicePersonID", 
            "PoliceStationID", "CaseCategoryID", "GravityOffenceID", "CrimeMajorHeadID", 
            "CrimeMinorHeadID", "CaseStatusID", "CourtID", "IncidentFromDate", "IncidentToDate", 
            "InfoReceivedPSDate", "latitude", "longitude", "BriefFacts"
        ])
        writer.writeheader()
        writer.writerows(cases)
    print(f"Generated {case_path} ({len(cases)} rows)")

    # Save Accused.csv
    accused_path = os.path.join(export_dir, "Accused.csv")
    with open(accused_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["AccusedMasterID", "CaseMasterID", "AccusedName", "AgeYear", "GenderID", "PersonID"])
        writer.writeheader()
        writer.writerows(accused_records)
    print(f"Generated {accused_path} ({len(accused_records)} rows)")

    print("CSV generation completed successfully! Files are saved in 'catalyst_import_data/' directory.")

if __name__ == "__main__":
    main()
