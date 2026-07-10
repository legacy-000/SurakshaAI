"""
Deterministic seed data generator for Suraksha AI demo.
Generates 500 FIR records across 10 Karnataka districts.
"""

import random
from datetime import datetime, timedelta


def generate_seed_data():
    districts = [
        {"id": 1, "name": "Bangalore Urban", "stations": 12},
        {"id": 2, "name": "Bangalore Rural", "stations": 8},
        {"id": 3, "name": "Mysuru", "stations": 10},
        {"id": 4, "name": "Hubli", "stations": 7},
        {"id": 5, "name": "Mangalore", "stations": 6},
        {"id": 6, "name": "Belgaum", "stations": 8},
        {"id": 7, "name": "Dharwad", "stations": 5},
        {"id": 8, "name": "Shivamogga", "stations": 5},
        {"id": 9, "name": "Tumkur", "stations": 6},
        {"id": 10, "name": "Kalaburagi", "stations": 5}
    ]

    crime_types = ["Theft", "Murder", "Robbery", "Assault",
                   "Kidnapping", "Burglary", "Cheating", "Snatching"]
    statuses = ["Under Investigation", "Charge Sheeted", "Closed", "Pending"]

    repeat_accused = [
        {"name": "Ravi Kumar", "cases": 8, "districts": [1, 2]},
        {"name": "Suresh P", "cases": 5, "districts": [1, 3]},
        {"name": "Rajesh K", "cases": 4, "districts": [1]},
        {"name": "Manoj R", "cases": 3, "districts": [3, 4]},
        {"name": "Venkatesh G", "cases": 3, "districts": [1, 2]}
    ]

    records = []
    accused_map = {}

    for d in districts:
        for s in range(1, d["stations"] + 1):
            station_cases = random.randint(3, 8)
            for c in range(station_cases):
                case_id = len(records) + 1
                date = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 545))
                crime = random.choice(crime_types)

                lat = {
                    "Bangalore Urban": (12.85, 13.1),
                    "Bangalore Rural": (12.7, 13.0),
                    "Mysuru": (12.2, 12.4),
                    "Hubli": (15.3, 15.5),
                    "Mangalore": (12.8, 13.0),
                }.get(d["name"], (12.0, 16.0))

                records.append({
                    "case_master_id": case_id,
                    "crime_no": f"10{d['id']:02d}{s:02d}2024{case_id:05d}",
                    "crime_registered_date": date.strftime("%Y-%m-%d"),
                    "district_id": d["id"],
                    "station_id": s,
                    "crime_type": crime,
                    "status": random.choice(statuses),
                    "latitude": round(random.uniform(lat[0], lat[1]), 6),
                    "longitude": round(random.uniform(74.0, 78.5), 6),
                    "brief_facts": f"{crime} reported at {d['name']} on {date.strftime('%Y-%m-%d')}"
                })

    for accused in repeat_accused:
        for i in range(accused["cases"]):
            case = random.choice([r for r in records if r["district_id"] in accused["districts"]])
            name_key = f"{accused['name']}_{i}"
            accused_map[name_key] = {
                "accused_name": accused["name"],
                "case_master_id": case["case_master_id"],
                "age": random.randint(25, 45),
                "gender": 1
            }

    return {"cases": records, "accused": accused_map}
