"""
Synthetic data generator for Suraksha AI — KSP FIR database (57 tables).

Deterministic, configurable, schema-compliant. Embeds crime patterns,
repeat offenders, hotspots, seasonal/hourly/trend signals, and intentional
data-quality issues. Outputs CSV files.

Usage:
    python database/data_generator.py --profile MEDIUM
    python database/data_generator.py --profile SMALL --seed 123
    python database/data_generator.py --profile LARGE --output data/large/
    python database/data_generator.py --validate-only --input data/
"""

import argparse
import csv
import os
import random
import sys
from collections import defaultdict
from datetime import datetime, timedelta, date
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def clamp(n, lo, hi):
    return max(lo, min(hi, n))


class Profile:
    SMALL = "SMALL"
    MEDIUM = "MEDIUM"
    LARGE = "LARGE"


PROFILES = {
    Profile.SMALL: {
        "cases": 100, "districts": 5, "stations": 10, "employees": 15,
        "courts": 3, "repeat_offenders": 3, "hotspot_density": 0.3,
        "spike_magnitude": 2.0, "missing_gps_rate": 0.1, "trend_volatility": 0.03,
    },
    Profile.MEDIUM: {
        "cases": 500, "districts": 10, "stations": 30, "employees": 30,
        "courts": 5, "repeat_offenders": 5, "hotspot_density": 0.4,
        "spike_magnitude": 2.5, "missing_gps_rate": 0.2, "trend_volatility": 0.025,
    },
    Profile.LARGE: {
        "cases": 2000, "districts": 15, "stations": 60, "employees": 60,
        "courts": 8, "repeat_offenders": 8, "hotspot_density": 0.5,
        "spike_magnitude": 3.0, "missing_gps_rate": 0.2, "trend_volatility": 0.02,
    },
}


class DataGenerator:
    """Deterministic synthetic data generator for 57 KSP + prototype tables."""

    def __init__(self, profile=Profile.MEDIUM, seed=42, output_dir=None):
        self.profile_name = profile
        self.cfg = PROFILES[profile]
        self.seed = seed
        self.rng = random.Random(seed)
        self.output_dir = Path(output_dir) if output_dir else DATA_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.tables = {}
        self._next_id = defaultdict(int)

    def _next(self, table_key):
        self._next_id[table_key] += 1
        return self._next_id[table_key]

    def _pick(self, seq):
        return self.rng.choice(seq)

    def _pick_weighted(self, items, weights):
        population = list(items)
        return self.rng.choices(population, weights=weights, k=1)[0]

    def _randint(self, lo, hi):
        return self.rng.randint(lo, hi)

    def _uniform(self, lo, hi):
        return self.rng.uniform(lo, hi)

    def _date(self, start, end):
        delta = end - start
        return start + timedelta(days=self._randint(0, delta.days))

    def _maybe(self, rate):
        return self.rng.random() < rate

    def _dow_shift(self, base_date, target_dow):
        """Shift base_date to the nearest day matching target_dow (Sun=0, Sat=6)."""
        days_ahead = target_dow - base_date.weekday()
        if days_ahead < 0:
            days_ahead += 7
        if days_ahead == 0:
            days_ahead = 7  # prefer a non-exact shift to spread dates
        return base_date + timedelta(days=days_ahead)

    # ── Write Helpers ─────────────────────────────────────

    def write_csv(self, table_name, headers, rows):
        path = self.output_dir / f"{table_name}.csv"
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(headers)
            for r in rows:
                w.writerow(r)
        self.tables[table_name] = rows
        return rows

    # ── Master / Lookup Tables (Order 1 — no FKs) ─────────

    def generate_lookups(self):
        p = self.cfg

        self.write_csv("UnitType",
            ["UnitTypeID", "UnitTypeName", "CityDistState", "Hierarchy", "Active"],
            [["1", "Police Station", "City", "3", "1"],
             ["2", "Circle Office", "City", "2", "1"],
             ["3", "District Office", "District", "1", "1"]])

        self.write_csv("Rank",
            ["RankID", "RankName", "Hierarchy", "Active"],
            [[str(i + 1), n, str(8 - i), "1"]
             for i, n in enumerate(["Director General", "IG", "SP", "DSP",
                                    "Inspector", "Sub-Inspector", "Head Constable", "Constable"])])

        self.write_csv("Designation",
            ["DesignationID", "DesignationName", "SortOrder", "Active"],
            [[str(i + 1), n, str(i + 1), "1"]
             for i, n in enumerate(["SHO", "Investigating Officer", "CI", "SI", "ASI", "Addl SP"])])

        self.write_csv("CasteMaster",
            ["caste_master_id", "caste_master_name"],
            [[i + 1, n] for i, n in enumerate(
                ["General", "OBC", "SC", "ST", "Vokkaliga", "Lingayat", "Kuruba", "Idiga"])])

        self.write_csv("ReligionMaster",
            ["ReligionID", "ReligionName"],
            [[i + 1, n] for i, n in enumerate(
                ["Hindu", "Muslim", "Christian", "Sikh", "Jain", "Buddhist", "Parsi", "Other"])])

        self.write_csv("OccupationMaster",
            ["OccupationID", "OccupationName"],
            [[i + 1, n] for i, n in enumerate([
                "Government Employee", "Private Employee", "Farmer", "Business", "Student",
                "Unemployed", "Daily Wage", "Retired", "Homemaker", "Driver", "Shopkeeper",
                "Teacher", "Lawyer", "Doctor", "Engineer", "IT Professional", "Nurse",
                "Security Guard"])])

        self.write_csv("CaseCategory",
            ["CaseCategoryID", "LookupValue"],
            [["1", "FIR"], ["2", "UDR"], ["3", "Zero FIR"], ["4", "PAR"]])

        self.write_csv("GravityOffence",
            ["GravityOffenceID", "LookupValue"],
            [["1", "Heinous"], ["2", "Non-Heinous"], ["3", "Petty"]])

        self.write_csv("CaseStatusMaster",
            ["CaseStatusID", "CaseStatusName"],
            [[i + 1, n] for i, n in enumerate([
                "Under Investigation", "Charge Sheeted", "Closed", "Pending Trial",
                "Transferred", "Awaiting Forensic"])])

        self.write_csv("Act",
            ["ActCode", "ActDescription", "ShortName", "Active"],
            [["IPC", "Indian Penal Code", "IPC", "1"],
             ["NDPS", "Narcotic Drugs and Psychotropic Substances Act", "NDPS", "1"],
             ["CrPC", "Code of Criminal Procedure", "CrPC", "1"],
             ["IT_Act", "Information Technology Act", "IT Act", "1"],
             ["KA_Police", "Karnataka Police Act", "KA PC", "1"]])

        self.write_csv("CrimeHead",
            ["CrimeHeadID", "CrimeGroupName", "Active"],
            [["1", "Crimes Against Body", "1"],
             ["2", "Crimes Against Property", "1"],
             ["3", "Crimes Against Women", "1"],
             ["4", "Economic Offences", "1"],
             ["5", "Cyber Crimes", "1"],
             ["6", "Narcotics", "1"]])

        self.write_csv("State",
            ["StateID", "StateName", "NationalityID", "Active"],
            [[str(i + 1), n, "1", "1"]
             for i, n in enumerate(["Karnataka", "Tamil Nadu", "Kerala", "Andhra Pradesh", "Maharashtra"])])

    # ── Second Tier (FK→lookups) ──────────────────────────

    def generate_geo_and_legal(self):
        p = self.cfg
        district_names = [
            "Bengaluru Urban", "Bengaluru Rural", "Mysuru", "Hubballi", "Mangaluru",
            "Belagavi", "Shivamogga", "Dharwad", "Tumakuru", "Kalaburagi",
            "Udupi", "Hassan", "Davangere", "Ballari", "Raichur",
        ][:p["districts"]]

        self.district_ids = {n: i + 1 for i, n in enumerate(district_names)}
        self.write_csv("District",
            ["DistrictID", "DistrictName", "StateID", "Active"],
            [[str(i + 1), n, "1", "1"] for i, n in enumerate(district_names)])

        sections = [
            ("IPC", "302", "Murder"),
            ("IPC", "307", "Attempt to murder"),
            ("IPC", "324", "Voluntary hurt by weapon"),
            ("IPC", "326", "Grievous hurt by acid/weapon"),
            ("IPC", "354", "Assault on woman"),
            ("IPC", "376", "Rape"),
            ("IPC", "379", "Theft"),
            ("IPC", "380", "Theft in dwelling"),
            ("IPC", "392", "Robbery"),
            ("IPC", "394", "Robbery with hurt"),
            ("IPC", "397", "Dacoity with firearm"),
            ("IPC", "420", "Cheating"),
            ("IPC", "457", "Lurking house-trespass"),
            ("IPC", "498A", "Cruelty by husband"),
            ("NDPS", "20", "Cultivation of cannabis"),
            ("NDPS", "21", "Possession of psychotropic"),
            ("IT_Act", "66", "Computer-related offences"),
            ("IT_Act", "67", "Publishing obscene material"),
            ("CrPC", "144", "Unlawful assembly order"),
            ("KA_Police", "107", "Public nuisance"),
        ]
        self.write_csv("Section",
            ["ActCode", "SectionCode", "SectionDescription", "Active"],
            [[a, s, d, "1"] for a, s, d in sections])

        self.sections_by_act = defaultdict(list)
        for a, s, d in sections:
            self.sections_by_act[a].append((a, s, d))

        self.write_csv("CrimeSubHead",
            ["CrimeSubHeadID", "CrimeHeadID", "CrimeHeadName", "SeqID"],
            [["1", "1", "Murder", "1"], ["2", "1", "Attempt to Murder", "2"],
             ["3", "1", "Assault", "3"], ["4", "2", "Robbery", "1"],
             ["5", "2", "Burglary", "2"], ["6", "2", "Theft", "3"],
             ["7", "2", "Vehicle Theft", "4"], ["8", "3", "Rape", "1"],
             ["9", "3", "Dowry Case", "2"], ["10", "4", "Fraud", "1"],
             ["11", "5", "Cyber Fraud", "1"], ["12", "6", "Drug Possession", "1"]])

        self.crime_sub_heads = [
            (1, 1, "Murder"), (2, 1, "Attempt to Murder"), (3, 1, "Assault"),
            (4, 2, "Robbery"), (5, 2, "Burglary"), (6, 2, "Theft"),
            (7, 2, "Vehicle Theft"), (8, 3, "Rape"), (9, 3, "Dowry Case"),
            (10, 4, "Fraud"), (11, 5, "Cyber Fraud"), (12, 6, "Drug Possession"),
        ]

        self.write_csv("CrimeHeadActSection",
            ["CrimeHeadID", "ActCode", "SectionCode"],
            [["1", "IPC", "302"], ["1", "IPC", "307"], ["1", "IPC", "324"],
             ["2", "IPC", "379"], ["2", "IPC", "380"], ["2", "IPC", "392"],
             ["2", "IPC", "457"], ["3", "IPC", "354"], ["3", "IPC", "376"],
             ["3", "IPC", "498A"], ["4", "IPC", "420"], ["5", "IT_Act", "66"],
             ["5", "IT_Act", "67"], ["6", "NDPS", "20"], ["6", "NDPS", "21"]])

        # Station names per district
        station_patterns = {
            "Bengaluru Urban": ["MG Road", "Indiranagar", "Koramangala", "Whitefield",
                                "Jayanagar", "Malleshwaram", "Marathahalli", "Electronic City",
                                "Yeshwanthpur", "BTM Layout", "Rajajinagar", "Yelahanka"],
            "Bengaluru Rural": ["Nelamangala", "Devanahalli", "Doddaballapura", "Hoskote"],
            "Mysuru": ["Mysuru City", "K R Mohalla", "Kuvempunagar", "Vijayanagar", "Nazarbad"],
            "Hubballi": ["Hubballi City", "Old Hubballi", "Gokul Road"],
            "Mangaluru": ["Mangaluru City", "Kankanady", "Surathkal", "Bunder"],
            "Belagavi": ["Belagavi City", "Tilakwadi", "Macleod"],
            "Shivamogga": ["Shivamogga City", "Vidyanagar"],
            "Dharwad": ["Dharwad City", "Saptapur"],
            "Tumakuru": ["Tumakuru City", "Kyathasandra"],
            "Kalaburagi": ["Kalaburagi City", "Shahbad"],
            "Udupi": ["Udupi City", "Manipal"],
            "Hassan": ["Hassan City", "Holenarsipur"],
            "Davangere": ["Davangere City"],
            "Ballari": ["Ballari City", "Cantonment"],
            "Raichur": ["Raichur City"],
        }

        stations = []
        sid = 1000
        for d_name in district_names:
            names = station_patterns.get(d_name, [f"{d_name} PS"])
            for sname in names:
                sid += 1
                stations.append((sid, f"{sname} PS", 1, sid, 1, 1,
                                 self.district_ids[d_name], 1))
        self.stations = stations[:p["stations"]]
        self.station_ids = [s[0] for s in self.stations]

        self.write_csv("Unit",
            ["UnitID", "UnitName", "TypeID", "ParentUnit", "NationalityID",
             "StateID", "DistrictID", "Active"],
            [[str(s[0]), s[1], str(s[2]), str(s[3]), str(s[4]),
              str(s[5]), str(s[6]), str(s[7])] for s in self.stations])

        # Courts
        court_names = ["City Civil Court", "Sessions Court", "Fast Track Court",
                       "District Court", "Judicial Magistrate Court",
                       "High Court Circuit Bench", "Family Court", "CBI Special Court"]
        courts = []
        for i in range(min(p["courts"], len(court_names))):
            did = i % len(district_names) + 1
            courts.append((i + 1, f"{court_names[i]} Bengaluru" if did == 1
                           else f"{court_names[i]} {district_names[did - 1]}",
                           did, 1, 1))
        self.write_csv("Court",
            ["CourtID", "CourtName", "DistrictID", "StateID", "Active"],
            [[str(c[0]), c[1], str(c[2]), str(c[3]), str(c[4])] for c in courts])

    # ── Employees (Order 3) ───────────────────────────────

    def generate_employees(self):
        p = self.cfg
        first_names = [
            "Rajesh", "Suresh", "Anita", "Venkatesh", "Kavitha", "Mohan",
            "Priya", "Srinivas", "Naveen", "Lakshmi", "Ramesh", "Sunita",
            "Karthik", "Prakash", "Manjunath", "Usha", "Ganesh", "Deepa",
            "Shankar", "Radha", "Harish", "Meena", "Satish", "Anil",
            "Arun", "Divya", "Mahesh", "Rekha", "Vijay", "Shwetha",
        ][:p["employees"]]

        self.employees = []
        for i, fn in enumerate(first_names):
            eid = 101 + i
            unit = self._pick(self.station_ids)
            dist = self._dist_of_station(unit)
            rank = str(self._randint(4, 8))
            desig = str(self._randint(1, 4))
            kgid = f"KAR{eid:06d}"
            dob = f"{self._randint(1970, 1995)}-{self._randint(1, 12):02d}-{self._randint(1, 28):02d}"
            gender = "2" if fn in ("Anita", "Kavitha", "Priya", "Lakshmi", "Sunita",
                                   "Deepa", "Radha", "Meena", "Divya", "Rekha",
                                   "Shwetha", "Usha") else "1"
            bg = str(self._randint(1, 8))
            appt = f"{self._randint(2000, 2018)}-{self._randint(1, 12):02d}-{self._randint(1, 28):02d}"
            self.employees.append((eid, dist, unit, rank, desig, kgid, fn,
                                   dob, gender, bg, "0", appt))

        self.write_csv("Employee",
            ["EmployeeID", "DistrictID", "UnitID", "RankID", "DesignationID",
             "KGID", "FirstName", "EmployeeDOB", "GenderID", "BloodGroupID",
             "PhysicallyChallenged", "AppointmentDate"],
            [[str(e[0]), str(e[1]), str(e[2]), e[3], e[4], e[5], e[6],
              e[7], e[8], e[9], e[10], e[11]] for e in self.employees])

    def _dist_of_station(self, station_id):
        for s in self.stations:
            if s[0] == station_id:
                return s[6]
        return 1

    def _stations_of_district(self, dist_id):
        return [s[0] for s in self.stations if s[6] == dist_id]

    def _district_name(self, dist_id):
        for n, did in self.district_ids.items():
            if did == dist_id:
                return n
        return "Unknown"

    # ── Cases + Transactions (Order 4-6) ──────────────────

    def generate_cases(self):
        p = self.cfg
        # Temperature by district (trend pattern)
        trend_map = {
            "Bengaluru Urban": (+0.025, 1.0),
            "Mysuru": (0.0, 0.8),
            "Hubballi": (-0.012, 0.6),
        }
        default_trend = (+0.005, 0.5)

        # Seasonal multipliers per crime type (month -> factor)
        def seasonal_factor(crime_sub_head_id, month):
            if crime_sub_head_id in (6, 7):  # Theft, Vehicle Theft
                return 1.0 + 0.8 * (1 if month in (10, 11, 12, 1) else 0)
            if crime_sub_head_id in (3, 4):  # Assault, Robbery
                return 1.0 + 0.6 * (1 if month in (12, 1, 5, 6) else 0)
            if crime_sub_head_id in (5,):  # Burglary
                return 1.0 + 0.4 * (1 if month in (3, 4, 9, 10) else 0)
            if crime_sub_head_id == 11:  # Cyber Fraud
                return 1.0 + 0.3 * (1 if month in (3, 4) else 0)
            return 1.0

        # Repeat offenders config
        repeat_names = [
            ("Ravi Kumar", 8, [1, 2], (6,), "Night theft in commercial areas"),
            ("Suresh P", 5, [1, 3], (6, 7), "Vehicle theft and chain snatching"),
            ("Rajesh K", 4, [1], (5,), "Apartment burglary posing as delivery"),
            ("Manoj R", 3, [3, 4], (3,), "Assault in pub areas"),
            ("Venkatesh G", 3, [1, 2], (10, 11), "Phishing and cyber fraud"),
        ][:p["repeat_offenders"]]
        # Add additional generic repeat offenders for larger profiles
        extra_names = [
            ("Arun Kumar", 3, [5], (7,), "Bike theft in parking lots"),
            ("Pradeep N", 2, [6, 7], (3,), "Chain snatching in market"),
            ("Satish Shetty", 2, [8], (12,), "Drug peddling near colleges"),
        ]
        for en in extra_names:
            if p["repeat_offenders"] > len(repeat_names):
                repeat_names.append(en)
        self.repeat_offenders_config = repeat_names

        # Build repeat offender case assignment
        repeat_cases = {}
        for name, num_cases, dist_ids, crime_types, mo in repeat_names:
            repeat_cases[name] = {
                "count": num_cases,
                "districts": dist_ids,
                "crime_types": crime_types,
                "mo": mo,
                "assigned_to_cases": [],
            }

        case_master = []
        complainants = []
        act_sections = []
        victims = []
        accused = []
        arrests = []
        chargesheets = []
        inv_occur = []

        # Location coords per district
        district_centroids = {
            "Bengaluru Urban": (12.95, 77.60),
            "Bengaluru Rural": (13.00, 77.50),
            "Mysuru": (12.30, 76.65),
            "Hubballi": (15.35, 75.15),
            "Mangaluru": (12.90, 74.85),
            "Belagavi": (15.85, 74.50),
            "Shivamogga": (13.90, 75.55),
            "Dharwad": (15.45, 75.00),
            "Tumakuru": (13.35, 77.10),
            "Kalaburagi": (17.35, 76.85),
            "Udupi": (13.35, 74.75),
            "Hassan": (13.00, 76.10),
            "Davangere": (14.45, 75.90),
            "Ballari": (15.15, 76.90),
            "Raichur": (16.20, 77.35),
        }

        complainant_names = [
            "Ravi Kumar", "Sita Sharma", "Mohammed Ali", "Priya Singh",
            "Venkatesh Iyer", "Lakshmi N", "Abdul Rahman", "Geeta Reddy",
            "Suresh Babu", "Ananya K", "Mahesh Gowda", "Divya M",
            "Santosh Patil", "Kavitha R", "Rameshwar Naik", "Pooja Jain",
            "Irfan Khan", "Sunitha Devi", "Gopal Rao", "Meena A",
            "Shashank G", "Rekha N", "Nagaraj", "Asha Rani", "Kumar S",
        ]

        accused_name_pool = [
            "John Doe", "Jane Smith", "Rohit Verma", "Vikram Raj", "Santosh R",
            "Manoj Kumar", "Sneha Reddy", "Ravi Teja", "Pradeep N", "Suresh Poojari",
            "Anil Kumble", "Rashid Khan", "Naveen Gowda", "Satish Shetty", "Hari Prasad",
            "Deepak M", "Arjun Singh", "Rahul Dev", "Prakash Rai", "Kiran Y",
            "Monica S", "Arun Kumar", "Vijay Patil", "Sharan B", "Lokesh R",
        ]

        victim_names = [
            "Rajeshwari N", "Mohan G", "Anita Shetty", "Karthik S", "Shiela Thomas",
            "Deepa M", "Narayan Rao", "Uma Devi", "Prakash Hegde", "Sushma R",
            "Girish K", "Meenakshi A", "Harsha Vardhan", "Rajiv Nair", "Shweta P",
            "Ramesh Chandra", "Jaya K", "Vikram Bhat", "Shobha R", "Harish K",
        ]

        start_date = date(2025, 1, 1)
        end_date = date(2026, 7, 31)

        # DQ-03: inconsistent name spellings
        name_spelling_variants = {
            "Ravi Kumar": ["Ravikumar", "Ravi K", "Ravi Kumar"],
            "Suresh P": ["Suresh Poojari", "Suresh P"],
        }
        # DQ-04: Kannada/English variants
        kn_en_variants = {
            "Mohammed Ali": "Muhammad Ali",
        }

        ac_id = 1
        comp_id = 1
        vic_id = 1
        arrest_id = 1
        cs_id = 1

        for cid in range(1, p["cases"] + 1):
            # Pick district based on trend + hotspot bias
            dist_names = [n for n, _ in sorted(self.district_ids.items(), key=lambda x: x[1])]
            weights = []
            for dn in dist_names:
                if dn == "Bengaluru Urban":
                    w = 2.5  # hotspot
                elif dn in ("Mysuru", "Hubballi", "Mangaluru"):
                    w = 1.5
                else:
                    w = 1.0
                weights.append(w)
            dist_name = self._pick_weighted(dist_names, weights)
            dist_id = self.district_ids[dist_name]

            # Station
            station_ids = self._stations_of_district(dist_id)
            station_id = self._pick(station_ids) if station_ids else 1001

            # Crime type (with pattern bias)
            crime_weights = [2.0, 1.0, 1.5, 1.2, 1.5, 2.5, 1.5, 0.8, 0.6, 1.2, 1.5, 0.6]
            crime_type_idx = self._pick_weighted(
                list(range(12)), crime_weights)
            (crime_major_id, crime_sub_id, crime_name) = self.crime_sub_heads[crime_type_idx]

            # Date with seasonal + trend bias
            trend, base_weight = trend_map.get(dist_name, default_trend)
            day_offset = self._randint(0, (end_date - start_date).days)
            # Apply trend: scale day_offset so later dates have more cases
            trend_scale = 1.0 + trend * day_offset
            if self._maybe(0.3):
                day_offset = int(day_offset * (1.0 + trend_scale * 0.1))

            reg_date = start_date + timedelta(days=int(day_offset))
            # Apply seasonal factor
            sf = seasonal_factor(crime_sub_id, reg_date.month)
            if self._maybe(sf * 0.3 - 0.2):
                pass  # keep the date

            # Day-of-week pattern
            if crime_sub_id in (3, 4):  # Assault, Robbery -> weekend
                reg_date = self._dow_shift(reg_date, 5)  # Fri/Sat
            elif crime_sub_id in (5,):  # Burglary -> weekday
                reg_date = self._dow_shift(reg_date, 2)  # Tue-Thu

            # Hour bias
            if crime_sub_id in (6, 7):  # Theft
                hour = self._pick([22, 23, 0, 1, 2, 3])
            elif crime_sub_id in (3, 4, 8):  # Assault/Robbery/Rape
                hour = self._pick([20, 21, 22, 23, 0, 1])
            elif crime_sub_id in (5,):  # Burglary
                hour = self._pick([9, 10, 11, 14, 15, 16])
            elif crime_sub_id == 11:  # Cyber Fraud
                hour = self._pick([10, 11, 12, 14, 15, 16])
            else:
                hour = self._randint(6, 22)
            minute = self._randint(0, 59)
            reg_dt = datetime(reg_date.year, reg_date.month, reg_date.day, hour, minute)

            # Incident timing
            inc_from = reg_dt - timedelta(hours=self._randint(1, 48))
            inc_to = inc_from + timedelta(hours=self._randint(1, 6))
            ps_received = inc_from + timedelta(hours=self._randint(1, 12))

            # GPS
            centroid = district_centroids.get(dist_name, (13.0, 77.0))
            gps_lat = round(centroid[0] + self._uniform(-0.15, 0.15), 6)
            gps_lng = round(centroid[1] + self._uniform(-0.15, 0.15), 6)
            # DQ-01: missing GPS
            if self._maybe(p["missing_gps_rate"]):
                gps_lat, gps_lng = None, None
            # DQ-06: invalid coordinates
            if self._maybe(0.03):
                gps_lat = round(self._uniform(6.0, 10.0), 6)  # outside Karnataka

            # Status (realistic distribution)
            status_weights = [35, 30, 15, 10, 5, 5]
            status_id = str(self._pick_weighted(list(range(1, 7)), status_weights))

            # Gravity
            if crime_sub_id in (1, 8):
                gravity = "1"
            elif crime_sub_id in (2, 3, 4, 6, 7, 12):
                gravity = self._pick(["1", "2", "2"])
            else:
                gravity = self._pick(["2", "2", "3"])

            # Court
            court_id = str(self._randint(1, p["courts"]))

            # Category
            cat_id = self._pick(["1", "1", "1", "2", "3"])

            # IO
            emp_ids = [e[0] for e in self.employees if e[2] == station_id]
            io_id = str(self._pick(emp_ids)) if emp_ids else "101"

            # CrimeNo — encoded: prefix + year + serial
            prefix = f"10{dist_id:02d}{station_id % 100:02d}"
            crime_no = f"{prefix}{reg_dt.year}{cid:06d}"
            case_no = f"{reg_dt.year}{cid:05d}"

            brief = f"{crime_name} reported at {self._district_name(dist_id)}. "
            if gps_lat:
                brief += f"Coordinates: {gps_lat}, {gps_lng}. "
            brief += f"Case registered on {reg_dt.strftime('%d-%b-%Y')}."

            case_master.append([
                str(cid), crime_no, case_no,
                reg_dt.strftime("%Y-%m-%d %H:%M:%S"), io_id, str(station_id),
                cat_id, gravity, str(crime_major_id), str(crime_sub_id),
                status_id, court_id,
                inc_from.strftime("%Y-%m-%d %H:%M:%S"),
                inc_to.strftime("%Y-%m-%d %H:%M:%S"),
                ps_received.strftime("%Y-%m-%d %H:%M:%S"),
                str(gps_lat) if gps_lat else "",
                str(gps_lng) if gps_lng else "",
                brief,
            ])

            # Inv_OccuranceTime
            inv_occur.append([
                str(cid), inc_from.strftime("%Y-%m-%d %H:%M:%S"),
                inc_to.strftime("%Y-%m-%d %H:%M:%S"),
                str(gps_lat) if gps_lat else "",
                str(gps_lng) if gps_lng else "",
                f"Incident occurred at {self._district_name(dist_id)}."])

            # Complainants (1-2 per case)
            for _ in range(self._pick([1, 1, 1, 2])):
                cn = self._pick(complainant_names)
                age = self._randint(22, 65) if not self._maybe(0.1) else ""
                occ = str(self._randint(1, 18))
                rel = str(self._randint(1, 8))
                cas = str(self._randint(1, 8))
                gid = str(self._randint(1, 2))
                # DQ-07: inconsistent gender
                if self._maybe(0.02):
                    gid = "3"
                complainants.append([str(comp_id), str(cid), cn, str(age), occ, rel, cas, gid])
                comp_id += 1

            # Act-Section mapping
            act_sections.append([str(cid), "IPC", str(crime_sub_id),
                                 str(self._randint(1, 3)), "1"])
            if self._maybe(0.4):
                sections_flat = sum((v for v in self.sections_by_act.values()), [])
                extra = self._pick(sections_flat)
                act_sections.append([str(cid), extra[0], extra[1], str(self._randint(1, 3)), "2"])

            # Check if case has a repeat offender
            assigned_repeat = None
            for rname, rinfo in repeat_cases.items():
                if rinfo["count"] > len(rinfo["assigned_to_cases"]):
                    if dist_id in rinfo["districts"] and crime_sub_id in rinfo["crime_types"]:
                        assigned_repeat = rname
                        rinfo["assigned_to_cases"].append(cid)
                        break

            # Victims (0-1 per case)
            if self._maybe(0.75):
                vn = self._pick(victim_names)
                vage = str(self._randint(18, 70)) if not self._maybe(0.1) else ""
                vgid = str(self._randint(1, 2))
                vpol = self._pick(["0", "0", "0", "1"])
                victims.append([str(vic_id), str(cid), vn, vage, vgid, vpol])
                vic_id += 1

            # Accused (1-3 per case)
            num_acc = self._pick([1, 1, 1, 2, 2, 3])
            for _ in range(num_acc):
                if assigned_repeat and not any(
                    a[0] == ac_id for a in accused if a[1] == str(cid) and a[2] == assigned_repeat):
                    an = assigned_repeat
                else:
                    an = self._pick(accused_name_pool)
                aage = str(self._randint(18, 55)) if not self._maybe(0.1) else ""
                agid = str(self._randint(1, 2))
                if self._maybe(0.02):
                    agid = "3"
                pid = f"A{ac_id}"
                accused.append([str(ac_id), str(cid), an, aage, agid, pid])

                # DQ-03: inconsistent spelling for repeat offenders
                if an in name_spelling_variants and self._maybe(0.3):
                    variant = self._pick(name_spelling_variants[an])
                    accused[-1][2] = variant

                # DQ-04: Kannada/English variant
                if an in kn_en_variants and self._maybe(0.2):
                    accused[-1][2] = kn_en_variants[an]

                # Arrest (60% of accused)
                if self._maybe(0.6):
                    arr_date = reg_dt + timedelta(days=self._randint(1, 30))
                    arr_type = self._pick(["1", "1", "2"])
                    arr_state = self._pick(["1", "1", "2"])
                    arr_dist = self._pick(["1", "2", "3"])
                    arrests.append([
                        str(arrest_id), str(cid), arr_type,
                        arr_date.strftime("%Y-%m-%d"), arr_state, arr_dist,
                        str(station_id), io_id, court_id, str(ac_id), "1", "0"])
                    arrest_id += 1
                ac_id += 1

            # Chargesheet (60% of cases, but only for certain statuses)
            if self._maybe(0.6) and status_id in ("2", "3", "4"):
                cs_date = reg_dt + timedelta(days=self._randint(30, 90))
                # DQ-11: incomplete
                cs_type = self._pick(["A", "A", "A", "B", "C", ""])
                chargesheets.append([str(cs_id), str(cid),
                                     cs_date.strftime("%Y-%m-%d %H:%M:%S"),
                                     cs_type, io_id])
                cs_id += 1

        self.write_csv("CaseMaster",
            ["CaseMasterID", "CrimeNo", "CaseNo", "CrimeRegisteredDate",
             "PolicePersonID", "PoliceStationID", "CaseCategoryID",
             "GravityOffenceID", "CrimeMajorHeadID", "CrimeMinorHeadID",
             "CaseStatusID", "CourtID", "IncidentFromDate", "IncidentToDate",
             "InfoReceivedPSDate", "latitude", "longitude", "BriefFacts"],
            case_master)

        self.write_csv("ComplainantDetails",
            ["ComplainantID", "CaseMasterID", "ComplainantName", "AgeYear",
             "OccupationID", "ReligionID", "CasteID", "GenderID"],
            complainants)

        self.write_csv("ActSectionAssociation",
            ["CaseMasterID", "ActID", "SectionID", "ActOrderID", "SectionOrderID"],
            act_sections)

        self.write_csv("Victim",
            ["VictimMasterID", "CaseMasterID", "VictimName", "AgeYear",
             "GenderID", "VictimPolice"],
            victims)

        self.write_csv("Accused",
            ["AccusedMasterID", "CaseMasterID", "AccusedName", "AgeYear",
             "GenderID", "PersonID"],
            accused)

        self.write_csv("ArrestSurrender",
            ["ArrestSurrenderID", "CaseMasterID", "ArrestSurrenderTypeID",
             "ArrestSurrenderDate", "ArrestSurrenderStateId",
             "ArrestSurrenderDistrictId", "PoliceStationID", "IOID", "CourtID",
             "AccusedMasterID", "IsAccused", "IsComplainantAccused"],
            arrests)

        self.write_csv("ChargesheetDetails",
            ["CSID", "CaseMasterID", "csdate", "cstype", "PolicePersonID"],
            chargesheets)

        self.write_csv("Inv_OccuranceTime",
            ["CaseMasterID", "IncidentFromDate", "IncidentToDate", "latitude",
             "longitude", "location_description"],
            inv_occur)

        # ──inv_arrestsurrenderaccused junction ─────────────
        self.write_csv("inv_arrestsurrenderaccused",
            ["ArrestSurrenderID", "AccusedMasterID"],
            [[str(i + 1), r[9]] for i, r in enumerate(arrests)])

        # Repeat offender map for cross-reference
        self.accused_records = accused
        self.case_records = case_master
        self._repeat_case_assignment = repeat_cases

    # ── Timeline Events (Order 7) ─────────────────────────

    def generate_timelines(self):
        p = self.cfg
        timelines = []
        event_templates = {
            "FIR Registered": ("Registration", 0),
            "Investigation Started": ("Investigation", 2),
            "Scene Inspection": ("Field Visit", 1),
            "Witness Statement Recorded": ("Investigation", 7),
            "Forensic Report Received": ("Forensic", 10),
            "Arrest Made": ("Arrest", 5),
            "Chargesheet Filed": ("Legal", 45),
            "Court Hearing": ("Legal", 60),
            "Accused Released on Bail": ("Legal", 15),
            "Case Transferred": ("Administrative", 30),
        }

        for case in self.case_records:
            cid = case[0]
            reg_date_str = case[3]
            try:
                base = datetime.strptime(reg_date_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                base = datetime(2025, 1, 1)
            station_name = "Unknown"
            for s in self.stations:
                if str(s[0]) == case[5]:
                    station_name = s[1]
                    break

            num_events = self._randint(3, 6)
            used_events = set()
            for _ in range(num_events):
                ev_key = self._pick(list(event_templates.keys()))
                if ev_key in used_events and self._maybe(0.5):
                    continue
                used_events.add(ev_key)
                ev_type, delay_days = event_templates[ev_key]
                ev_date = base + timedelta(days=self._randint(delay_days, delay_days + 14),
                                          hours=self._randint(6, 18))
                timelines.append([
                    cid, ev_key, f"{ev_key} at {station_name}",
                    ev_date.strftime("%Y-%m-%d %H:%M:%S"), ev_type, station_name,
                    self._pick(["101", "102", "103"])])

        self.write_csv("TimelineEvent",
            ["CaseMasterID", "Title", "Description", "EventDate", "EventType",
             "Location", "CreatedBy"],
            timelines)

    # ── AI Supplementals ───────────────────────────────────

    def generate_ai_supplementals(self):
        p = self.cfg

        self.write_csv("BehaviorProfile",
            ["SubjectName", "ProfileType", "MO", "RiskLevel", "Pattern", "Score",
             "Notes", "CreatedDate"],
            [[n, t, m, rl, pat, s, notes, d] for n, t, m, rl, pat, s, notes, d in [
                ("Ravi Kumar", "Repeat Offender", "Night theft in commercial areas",
                 "High", "Night commercial theft", "85.5",
                 "History of 10+ theft cases", "2025-07-01"),
                ("Suresh P", "Property Offender", "Vehicle theft and chain snatching",
                 "High", "Vehicle theft ring", "78.0",
                 "Linked to vehicle theft network", "2025-07-02"),
                ("Rajesh K", "Property Offender", "Burglary posing as delivery person",
                 "Medium", "Delivery scam burglary", "72.3",
                 "Modus operandi consistent", "2025-07-05"),
                ("Rohit Verma", "Violent Offender", "Assault during robbery attempts",
                 "High", "Armed robbery pattern", "76.0",
                 "Prior assault conviction", "2025-07-03"),
                ("Manoj Kumar", "Property Offender", "Apartment burglary",
                 "Medium", "Daytime burglary", "68.5",
                 "Targets unoccupied homes", "2025-07-18"),
                ("Sneha Reddy", "Repeat Offender", "Chain snatching in market areas",
                 "Medium", "Market chain snatching", "65.0",
                 "Active in KR Market area", "2025-07-10"),
                ("Arun Kumar", "Vehicle Offender", "Motorcycle theft in parking lots",
                 "Medium", "Parking lot theft", "70.5",
                 "Part of organized theft ring", "2025-07-12"),
                ("Satish Shetty", "Drug Offender", "Cannabis distribution near colleges",
                 "High", "College-area drug distribution", "82.0",
                 "Under surveillance", "2025-07-15"),
            ][:min(len(self.repeat_offenders_config) * 2 + 3, 20)]])

        self.write_csv("CrimePattern",
            ["pattern_name", "description", "crime_type", "hotspot_radius_meters",
             "temporal_signature", "modus_operandi_tags"],
            [
                ("Night Theft Cluster",
                 "Theft incidents concentrated in commercial areas 10PM-4AM",
                 "Theft", "500", "Weekdays 22:00-04:00",
                 "lock-picking,vehicle-breaking,commercial-area"),
                ("Weekend Assault Pattern",
                 "Assaults near transit hubs Fri-Sat evenings",
                 "Assault", "300", "Fri-Sat 20:00-02:00",
                 "public-transit,alcohol-related,group"),
                ("Residential Burglary Ring",
                 "Burglaries targeting unoccupied homes work hours",
                 "Burglary", "800", "Mon-Fri 09:00-17:00",
                 "forced-entry,rear-entrance,weekday"),
                ("Vehicle Theft Corridor",
                 "Stolen vehicles traced to highway corridors",
                 "Vehicle Theft", "2000", "All days 00:00-06:00",
                 "hotwiring,export-ring,highway"),
                ("Cyber Fraud Network",
                 "VoIP fraud calls targeting elderly 10AM-6PM",
                 "Fraud", "100", "All days 10:00-18:00",
                 "voip-spoofing,elderly-target,banking"),
                ("Market Chain Snatching",
                 "Gold chain snatching in crowded market areas",
                 "Robbery", "200", "Weekends 12:00-20:00",
                 "snatch-and-run,crowded-market,two-wheeler"),
                ("Pub Brawl Seasonals",
                 "Assaults outside pubs Fri-Sat nights",
                 "Assault", "150", "Fri-Sat 23:00-03:00",
                 "pub-area,weekend,alcohol-fueled"),
                ("ATM Robbery Cluster",
                 "Targeting solo ATM users late night",
                 "Robbery", "100", "All days 22:00-02:00",
                 "atm-target,solo-victim,weapon-show"),
                ("College Drug Distribution",
                 "Drug peddling near college campuses during semesters",
                 "Drug Offence", "300", "Mon-Sat 10:00-16:00",
                 "college-area,cannabis,p2p-sale"),
                ("Dowry Harassment Pattern",
                 "Dowry harassment cases post-wedding first 3 years",
                 "Domestic Crime", "50", "All days all hours",
                 "dowry-harassment,in-laws,marital"),
            ])

        self.write_csv("Alert",
            ["Title", "Message", "Severity", "Type", "Status", "AssignedTo",
             "CreatedDate", "ResolvedDate"],
            [
                ("Theft Surge MG Road", "Theft cases up 35% in MG Road area this month",
                 "High", "Crime Trend", "Active", "IO101", "2026-06-15 08:00:00", ""),
                ("Burglary Warning Indiranagar",
                 "3 burglaries in Indiranagar this week",
                 "High", "Crime Trend", "Active", "IO104", "2026-06-18 09:30:00", ""),
                ("Cyber Fraud Spike", "Phishing complaints doubled in last 15 days",
                 "Medium", "Cyber Crime", "Active", "IO102", "2026-06-20 10:00:00", ""),
                ("Hotspot: Koramangala", "Predicted assault hotspot near bus stop",
                 "Medium", "Prediction", "Active", "IO106", "2026-06-22 06:00:00", ""),
                ("Night Patrol Alert",
                 "Increased thefts in commercial zones at night",
                 "High", "Patrol Recommendation", "Active", "IO108",
                 "2026-06-25 07:30:00", ""),
                ("Repeat Offender Active",
                 "Ravi Kumar spotted in MG Road area",
                 "Critical", "Offender Tracking", "Active", "IO101",
                 "2026-06-28 14:00:00", ""),
                ("Vehicle Theft Ring",
                 "Organized vehicle theft ring operating in Whitefield",
                 "High", "Intelligence", "Active", "IO108", "2026-07-01 08:00:00", ""),
                ("College Drug Alert",
                 "Drug peddling reported near 3 colleges",
                 "Medium", "Narcotics", "Active", "IO106", "2026-07-03 10:00:00", ""),
                ("ATM Robbery Risk",
                 "Increased ATM robbery risk in Electronic City",
                 "Medium", "Prediction", "Active", "IO107", "2026-07-05 06:00:00", ""),
                ("Weekend Patrol Needed",
                 "Assaults predicted near pubs this weekend",
                 "High", "Patrol Recommendation", "Active", "IO106",
                 "2026-07-07 16:00:00", ""),
            ][:min(10 + p["cases"] // 50, 40)])

        self.write_csv("Prediction",
            ["Title", "CrimeType", "Location", "Latitude", "Longitude",
             "Probability", "PredictedDate", "ModelVersion", "Status"],
            [
                ("Burglary Risk Zone", "Burglary", "Indiranagar",
                 "12.9783", "77.6408", "0.85", "2026-07-15", "v1.0", "Active"),
                ("Theft Hotspot", "Theft", "MG Road",
                 "12.9716", "77.5946", "0.78", "2026-07-20", "v1.0", "Active"),
                ("Assault Risk Area", "Assault", "Koramangala Bus Stand",
                 "12.9352", "77.6245", "0.72", "2026-07-18", "v1.0", "Active"),
                ("Cyber Fraud Zone", "Fraud", "Electronic City",
                 "12.8399", "77.6770", "0.81", "2026-07-22", "v1.0", "Active"),
                ("Vehicle Theft Risk", "Vehicle Theft", "Whitefield",
                 "12.9698", "77.7500", "0.74", "2026-07-25", "v1.0", "Active"),
                ("Robbery Hotspot", "Robbery", "BTM Layout",
                 "12.9166", "77.6101", "0.69", "2026-07-19", "v1.0", "Active"),
                ("Drug Activity Zone", "Drug Offence", "Jayanagar College Area",
                 "12.9250", "77.5938", "0.77", "2026-07-21", "v1.0", "Active"),
                ("Snatching Risk", "Robbery", "KR Market",
                 "12.9550", "77.5750", "0.65", "2026-07-23", "v1.0", "Active"),
                ("Night Crime Zone", "Theft", "Malleshwaram",
                 "12.9943", "77.5710", "0.71", "2026-07-24", "v1.0", "Active"),
                ("Weekend Assault Risk", "Assault", "MG Road Pubs",
                 "12.9716", "77.5946", "0.68", "2026-07-26", "v1.0", "Active"),
                ("Chain Snatching Alert", "Robbery", "Jayanagar 4th Block",
                 "12.9300", "77.5800", "0.73", "2026-07-27", "v1.0", "Active"),
                ("Dacoity Risk", "Robbery", "Marathahalli",
                 "12.9591", "77.6974", "0.60", "2026-07-28", "v1.0", "Active"),
            ][:min(12 + p["cases"] // 100, 50)])

        self.write_csv("ChatContext",
            ["SessionID", "UserID", "Message", "Response", "Timestamp"],
            [
                ("SESS001", "USER001", "Show theft cases in MG Road",
                 "Found 12 theft cases registered in MG Road area.", "2026-07-01 10:30:00"),
                ("SESS001", "USER001", "Which areas have highest crime?",
                 "MG Road (15 cases), Koramangala (12 cases), Indiranagar (10 cases).",
                 "2026-07-01 10:31:00"),
                ("SESS001", "USER001", "Show monthly trend",
                 "Jan:3 Feb:5 Mar:7 Apr:9 May:12 Jun:14 — rising trend.",
                 "2026-07-01 10:32:00"),
                ("SESS002", "USER002", "Whose accused name is John Doe?",
                 "John Doe is accused in Case #1. Repeat offender.",
                 "2026-07-02 14:00:00"),
                ("SESS002", "USER002", "Map of all burglary cases",
                 "Found 6 burglary cases in Indiranagar, Whitefield, Jayanagar.",
                 "2026-07-02 14:01:00"),
                ("SESS004", "USER004", "Similar cases to Case 2",
                 "3 similar assault cases found in Koramangala area.",
                 "2026-07-04 11:01:00"),
            ])

    # ── Prototype Tables ───────────────────────────────────

    def generate_prototype(self):
        p = self.cfg

        self.write_csv("AppUserProfile",
            ["user_id", "kgid", "first_name", "email", "role_id", "unit_id",
             "district_id", "language_preference", "is_active", "created_at", "updated_at"],
            [["U001", "KAR101001", "Rajesh Kumar", "rajesh.k@ksp.gov.in",
              "1", str(self.station_ids[0]), "1", "en", "1",
              "2025-01-01 00:00:00", "2025-01-01 00:00:00"]])

        self.write_csv("RolePermission",
            ["role_id", "role_name", "permitted_apis", "permitted_screens",
             "permitted_tables", "can_view_sql", "can_view_audit",
             "can_export_pdf", "can_view_pii", "can_manage_users"],
            [
                ["1", "Investigator", '["/chat/*","/analytics/*","/offender/*","/network/*"]',
                 '["chat","analytics","offender","network","workspace"]',
                 '["CaseMaster","Accused","Victim","ComplainantDetails"]',
                 "1", "0", "1", "0", "0"],
                ["2", "Analyst", '["/chat/*","/analytics/*","/forecast/*"]',
                 '["chat","analytics","forecast","sociological"]',
                 '["CaseMaster","Accused","Victim"]',
                 "1", "0", "1", "0", "0"],
                ["3", "Supervisor", '["/*"]',
                 '["*"]',
                 '["*"]',
                 "1", "1", "1", "0", "0"],
                ["4", "Policymaker", '["/analytics/*","/forecast/*"]',
                 '["analytics","forecast","sociological"]',
                 '["CaseMaster"]',
                 "1", "0", "1", "0", "0"],
                ["5", "System Administrator", '["/*"]',
                 '["*"]', '["*"]',
                 "1", "1", "1", "1", "1"],
            ])

        self.write_csv("UserDataScope",
            ["scope_id", "user_id", "scope_type", "scope_value", "is_aggregate_scope"],
            [["1", "U001", "district", "1", "0"]])

        # SchemaMetadata — auto-generated from tables
        schema_meta = []
        for tname, rows in self.tables.items():
            if not rows:
                continue
            first_row = rows[0]
            if isinstance(first_row, list):
                headers = first_row  # Already have headers from write_csv
                break
        self.write_csv("SchemaMetadata",
            ["table_name", "column_name", "data_type", "is_primary_key",
             "is_foreign_key", "references_table", "references_column",
             "description", "pii_classification", "is_queryable"],
            [
                ["CaseMaster", "CaseMasterID", "INT", "1", "0", "", "",
                 "Primary key", "none", "1"],
                ["CaseMaster", "CrimeNo", "VARCHAR", "0", "0", "", "",
                 "Encoded FIR number", "none", "1"],
                ["CaseMaster", "CrimeRegisteredDate", "DATE", "0", "0", "", "",
                 "FIR registration date", "none", "1"],
                ["CaseMaster", "BriefFacts", "TEXT", "0", "0", "", "",
                 "Case narrative", "none", "1"],
                ["Accused", "AccusedName", "VARCHAR", "0", "0", "", "",
                 "Name of accused person", "direct", "1"],
                ["Accused", "AgeYear", "INT", "0", "0", "", "",
                 "Age of accused", "quasi", "1"],
                ["Victim", "VictimName", "VARCHAR", "0", "0", "", "",
                 "Name of victim", "direct", "1"],
                ["ComplainantDetails", "ComplainantName", "VARCHAR", "0", "0", "", "",
                 "Name of complainant", "direct", "1"],
            ])

        self.write_csv("BusinessGlossary",
            ["term_id", "term_english", "term_kannada", "definition_english",
             "definition_kannada", "related_tables", "category"],
            [
                ["1", "FIR", "FIR", "First Information Report",
                 "ಪ್ರಥಮ ಮಾಹಿತಿ ವರದಿ",
                 '["CaseMaster"]', "legal"],
                ["2", "Theft", "ಕಳ್ಳತನ", "Unlawful taking of property",
                 "ಆಸ್ತಿಯನ್ನು ಅಕ್ರಮವಾಗಿ ತೆಗೆದುಕೊಳ್ಳುವುದು",
                 '["CaseMaster","CrimeSubHead"]', "crime_type"],
                ["3", "Accused", "ಆರೋಪಿ", "Person charged with a crime",
                 "ಅಪರಾಧದ ಆರೋಪ ಹೊತ್ತ ವ್ಯಕ್ತಿ",
                 '["Accused"]', "legal"],
                ["4", "Charge Sheet", "ಚಾರ್ಜ್ಶೀಟ್",
                 "Formal police report filed in court",
                 "ನ್ಯಾಯಾಲಯದಲ್ಲಿ ಸಲ್ಲಿಸಲಾದ ನಿಯಮಬದ್ಧ ಪೊಲೀಸ್ ವರದಿ",
                 '["ChargesheetDetails"]', "legal"],
                ["5", "Investigation", "ತನಿಖೆ",
                 "Police inquiry into a crime",
                 "ಅಪರಾಧದ ಬಗ್ಗೆ ಪೊಲೀಸ್ ತನಿಖೆ",
                 '["CaseMaster","Investigation"]', "procedure"],
            ])

        self.write_csv("NLSQLExample",
            ["example_id", "natural_language_query", "generated_sql",
             "intent_type", "tables_used", "complexity_score"],
            [
                ["1", "How many theft cases in Bangalore last month?",
                 "SELECT COUNT(*) FROM CaseMaster cm JOIN CrimeSubHead csh ON cm.CrimeMinorHeadID=csh.CrimeSubHeadID WHERE csh.CrimeHeadName='Theft' AND cm.CrimeRegisteredDate >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH)",
                 "aggregation", '["CaseMaster","CrimeSubHead"]', "2"],
                ["2", "Show all accused named Ravi Kumar",
                 "SELECT * FROM Accused WHERE AccusedName LIKE '%Ravi Kumar%'",
                 "filter", '["Accused"]', "1"],
                ["3", "Which district has the most crime?",
                 "SELECT d.DistrictName, COUNT(cm.CaseMasterID) as case_count FROM CaseMaster cm JOIN Unit u ON cm.PoliceStationID=u.UnitID JOIN District d ON u.DistrictID=d.DistrictID GROUP BY d.DistrictName ORDER BY case_count DESC LIMIT 1",
                 "aggregation", '["CaseMaster","Unit","District"]', "3"],
                ["4", "Show crime trend by month this year",
                 "SELECT DATE_FORMAT(CrimeRegisteredDate, '%Y-%m') as month, COUNT(*) as count FROM CaseMaster WHERE YEAR(CrimeRegisteredDate)=YEAR(CURDATE()) GROUP BY month ORDER BY month",
                 "trend", '["CaseMaster"]', "2"],
            ])

        self.write_csv("ModelRegistry",
            ["model_id", "model_name", "model_version", "deployed_at",
             "is_active", "parameters_json"],
            [
                ["1", "quickml_llm", "v1.0", "2025-06-01 00:00:00", "1",
                 '{"model":"llama-3.1-70b","temperature":0.1,"max_tokens":4096}'],
                ["2", "prophet_forecast", "prophet_v1.0", "2025-06-01 00:00:00", "1",
                 '{"yearly_seasonality":true,"weekly_seasonality":true,"interval_width":0.8}'],
                ["3", "priority_score", "1.0.0", "2025-06-01 00:00:00", "1",
                 '{"version":"1.0.0","features":["case_frequency","crime_type_diversity","geographic_spread","recent_activity_frequency","co_accused_network_size","arrest_surrender_ratio"]}'],
            ])

        self.write_csv("PromptTemplateRegistry",
            ["template_id", "template_name", "template_version", "template_text", "is_active"],
            [
                ["1", "nl2sql_system", "v2.1",
                 "You are a SQL expert for the Karnataka Police FIR database...", "1"],
                ["2", "summarization", "v1.0",
                 "Summarize the following crime case details...", "1"],
                ["3", "answer_generation", "v1.0",
                 "Generate a natural language answer from query results...", "1"],
            ])

        self.write_csv("FeatureFlag",
            ["flag_id", "flag_name", "flag_value", "description"],
            [
                ["1", "voice_enabled", "1", "Enable voice input/output"],
                ["2", "kannada_enabled", "1", "Enable Kannada language support"],
                ["3", "forecast_enabled", "1", "Enable forecasting module"],
            ])

        self.write_csv("FinancialAccount",
            ["account_id", "account_number", "account_holder_name", "bank_name",
             "account_type", "is_synthetic"],
            [[str(i + 1), f"SBIN{1000+i}", n, "State Bank of India",
              "savings", "1"]
             for i, n in enumerate(["Ravi Kumar", "Suresh P", "Rajesh K",
                                    "Manoj R", "Venkatesh G", "John Doe",
                                    "Rohit Verma", "Satish Shetty"])])

        self.write_csv("FinancialTransaction",
            ["transaction_id", "account_id", "transaction_date", "amount",
             "transaction_type", "beneficiary_account", "is_synthetic"],
            [[str(i + 1), str(self._randint(1, 8)),
              f"2025-{self._randint(1,12):02d}-{self._randint(1,28):02d}",
              str(round(self._uniform(1000, 500000), 2)),
              self._pick(["credit", "debit"]), f"ACC{1000+i}", "1"]
             for i in range(20)])

        self.write_csv("CaseTransactionAssociation",
            ["association_id", "case_master_id", "transaction_id", "is_synthetic"],
            [[str(i + 1), str(self._randint(1, p["cases"])),
              str(self._randint(1, 20)), "1"]
             for i in range(min(30, p["cases"]))])

    # ── Run All ────────────────────────────────────────────

    def generate_all(self):
        print(f"Generating data: profile={self.profile_name}, seed={self.seed}")
        self.generate_lookups()
        self.generate_geo_and_legal()
        self.generate_employees()
        self.generate_cases()
        self.generate_timelines()
        self.generate_ai_supplementals()
        self.generate_prototype()
        total_rows = sum(len(v) for v in self.tables.values())
        print(f"Generated {len(self.tables)} tables, ~{total_rows} total rows")
        return self.tables


# ── Validator ──────────────────────────────────────────────

class DataValidator:
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.errors = []
        self.warnings = []

    def log(self, msg, is_error=False):
        (self.errors if is_error else self.warnings).append(msg)
        print(f"  {'FAIL' if is_error else 'WARN'}: {msg}")

    def validate_all(self):
        pk_map = {
            "CaseMaster": "CaseMasterID",
            "Accused": "AccusedMasterID",
            "Victim": "VictimMasterID",
            "ComplainantDetails": "ComplainantID",
            "ArrestSurrender": "ArrestSurrenderID",
            "ChargesheetDetails": "CSID",
            "District": "DistrictID",
            "State": "StateID",
            "Unit": "UnitID",
            "Employee": "EmployeeID",
            "Court": "CourtID",
        }
        fk_map = {
            "CaseMaster": {"PolicePersonID": ("Employee", "EmployeeID"),
                           "PoliceStationID": ("Unit", "UnitID"),
                           "CourtID": ("Court", "CourtID")},
            "Accused": {"CaseMasterID": ("CaseMaster", "CaseMasterID")},
            "Victim": {"CaseMasterID": ("CaseMaster", "CaseMasterID")},
            "ComplainantDetails": {"CaseMasterID": ("CaseMaster", "CaseMasterID")},
            "ArrestSurrender": {"CaseMasterID": ("CaseMaster", "CaseMasterID"),
                                "AccusedMasterID": ("Accused", "AccusedMasterID")},
        }

        tables = {}
        for fpath in self.data_dir.glob("*.csv"):
            with open(fpath, newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                headers = next(reader)
                rows = [r for r in reader]
                tables[fpath.stem] = {"headers": headers, "rows": rows}

        for tname, info in tables.items():
            rows = info["rows"]
            self.log(f"{tname}: {len(rows)} rows")
            if tname in pk_map:
                pk_col = pk_map[tname]
                try:
                    pk_idx = info["headers"].index(pk_col)
                except ValueError:
                    continue
                seen = set()
                for i, r in enumerate(rows):
                    val = r[pk_idx] if pk_idx < len(r) else ""
                    if not val:
                        self.log(f"  {tname} row {i}: NULL PK", True)
                    elif val in seen:
                        self.log(f"  {tname} row {i}: duplicate PK {val}", True)
                    seen.add(val)

            if tname in fk_map:
                for fk_col, (ref_table, ref_pk) in fk_map[tname].items():
                    if ref_table not in tables:
                        continue
                    try:
                        fk_idx = info["headers"].index(fk_col)
                    except ValueError:
                        continue
                    ref_pks = {r[tables[ref_table]["headers"].index(ref_pk)]
                               for r in tables[ref_table]["rows"]
                               if ref_pk in tables[ref_table]["headers"]}
                    for i, r in enumerate(rows):
                        val = r[fk_idx] if fk_idx < len(r) else ""
                        if val and val not in ref_pks:
                            self.log(f"  {tname} row {i}: FK {fk_col}={val} not in {ref_table}.{ref_pk}", True)

        repeat_offenders = ["Ravi Kumar", "Suresh P", "Rajesh K", "Manoj R", "Venkatesh G"]
        if "Accused" in tables:
            accused_rows = tables["Accused"]["rows"]
            name_idx = tables["Accused"]["headers"].index("AccusedName") if "AccusedName" in tables["Accused"]["headers"] else -1
            if name_idx >= 0:
                for rname in repeat_offenders:
                    count = sum(1 for r in accused_rows if rname in r[name_idx])
                    if count > 0:
                        self.log(f"  Repeat offender '{rname}' appears in {count} records")
                    else:
                        self.log(f"  Repeat offender '{rname}' not found", False)

        missing_gps_count = 0
        if "CaseMaster" in tables:
            cm = tables["CaseMaster"]
            try:
                lat_idx = cm["headers"].index("latitude")
                for r in cm["rows"]:
                    if not r[lat_idx]:
                        missing_gps_count += 1
                if missing_gps_count:
                    self.log(f"  Cases with missing GPS: {missing_gps_count}/{len(cm['rows'])} "
                             f"({100*missing_gps_count/len(cm['rows']):.0f}%)")
            except ValueError:
                pass

        print(f"\nValidation complete: {len(self.errors)} errors, {len(self.warnings)} warnings")
        return len(self.errors) == 0


# ── CLI ────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Suraksha AI synthetic data generator for 57 KSP + prototype tables")
    parser.add_argument("--profile", choices=["SMALL", "MEDIUM", "LARGE"], default="MEDIUM")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", default=None,
                        help="Output directory (default: data/ under project root)")
    parser.add_argument("--validate-only", action="store_true",
                        help="Skip generation, validate existing CSVs")
    parser.add_argument("--input", default=None,
                        help="Input CSV directory (for --validate-only)")
    parser.add_argument("--csv-only", action="store_true",
                        help="Generate CSVs only (no DB insert)")
    parser.add_argument("--seed-datastore", action="store_true",
                        help="Seed Catalyst Data Store from generated CSVs")
    args = parser.parse_args()

    if args.validate_only:
        data_dir = args.input or DATA_DIR
        validator = DataValidator(data_dir)
        ok = validator.validate_all()
        sys.exit(0 if ok else 1)

    gen = DataGenerator(profile=args.profile, seed=args.seed, output_dir=args.output)
    gen.generate_all()

    validator = DataValidator(gen.output_dir)
    ok = validator.validate_all()

    print(f"\nOutput: {gen.output_dir}")
    print(f"Profile: {args.profile} | Seed: {args.seed} | Validation: {'PASS' if ok else 'FAIL'}")
    print(f"To seed Catalyst Data Store: python database/data_generator.py --seed-datastore --input {gen.output_dir}")


if __name__ == "__main__":
    main()
