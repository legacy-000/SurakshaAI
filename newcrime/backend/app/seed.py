"""Generate a fresh synthetic crime database (Karnataka-flavoured).

Deterministic (seeded) so results are reproducible. Run via `python -m app.seed`
or automatically on first startup if the DB is empty.
"""
import random
from datetime import datetime, timedelta

from faker import Faker

from .database import Base, SessionLocal, engine
from . import models as m

fake = Faker("en_IN")
Faker.seed(42)
random.seed(42)

DISTRICTS = [
    "Bengaluru City", "Bengaluru Rural", "Mysuru", "Mangaluru", "Hubballi-Dharwad",
    "Belagavi", "Kalaburagi", "Ballari", "Vijayapura", "Davanagere", "Shivamogga",
    "Tumakuru", "Udupi", "Hassan", "Mandya",
]
STATIONS = ["Central PS", "North PS", "South PS", "East PS", "West PS", "Market PS", "Cyber Crime PS"]

CRIME_TYPES = {
    "Theft": "Property", "Burglary": "Property", "Robbery": "Property",
    "Vehicle Theft": "Property", "Chain Snatching": "Property",
    "Assault": "Body", "Murder": "Body", "Kidnapping": "Body",
    "Domestic Violence": "Body", "Cyber Fraud": "Financial", "Bank Fraud": "Financial",
    "UPI Scam": "Financial", "Extortion": "Financial", "Drug Trafficking": "Narcotics",
    "Human Trafficking": "Body", "Rioting": "Public Order",
}
MODUS = {
    "Theft": ["Pickpocketing", "Shoplifting", "Lock-breaking"],
    "Burglary": ["Night break-in", "Lock-breaking", "Duplicate key"],
    "Robbery": ["Armed hold-up", "Highway robbery", "Home invasion"],
    "Vehicle Theft": ["Hotwiring", "Duplicate key", "Tow-away"],
    "Chain Snatching": ["Two-wheeler snatch", "Crowd distraction"],
    "Assault": ["Group attack", "Weapon assault"],
    "Murder": ["Premeditated", "Sudden provocation", "Contract killing"],
    "Kidnapping": ["Ransom", "Elopement"],
    "Domestic Violence": ["Dowry harassment", "Physical abuse"],
    "Cyber Fraud": ["Phishing", "OTP fraud", "Fake job offer"],
    "Bank Fraud": ["Loan fraud", "Cheque forgery", "Insider fraud"],
    "UPI Scam": ["QR-code scam", "Fake payment link", "SIM swap"],
    "Extortion": ["Threat calls", "Protection money"],
    "Drug Trafficking": ["Courier network", "Peddling ring"],
    "Human Trafficking": ["Labour racket", "Fake employment"],
    "Rioting": ["Communal clash", "Mob violence"],
}
GANGS = ["Chikpet Gang", "Ring Road Crew", "KR Market Syndicate", "Silk Route Network",
         "Night Owls", "Cyber Hydra", "Highway Hawks"]
OCCUPATIONS = ["Unemployed", "Daily Wage", "Driver", "Shopkeeper", "Farmer", "Student",
               "IT Worker", "Mechanic", "Salesman", "Businessman", "Labourer"]
EDU = ["Illiterate", "Primary", "Secondary", "PUC", "Graduate", "Post-Graduate"]
SES = ["Low", "Lower-Mid", "Middle", "Upper-Mid", "High"]
RANKS = ["Constable", "Head Constable", "ASI", "SI", "Inspector", "DySP"]
STATUS_ACCUSED = ["Suspect", "Arrested", "Chargesheeted", "Convicted", "Absconding"]
STATUS_CASE = ["Open", "Under Investigation", "Chargesheeted", "Closed", "Cold"]
SEVERITY = ["Low", "Medium", "High", "Critical"]
BANKS = ["SBI", "Canara Bank", "HDFC", "ICICI", "Axis", "PhonePe Wallet", "Paytm"]

# rough lat/lon centroids for a scatter/hotspot map (offline, no tiles)
DISTRICT_GEO = {
    "Bengaluru City": (12.97, 77.59), "Bengaluru Rural": (13.23, 77.57),
    "Mysuru": (12.30, 76.64), "Mangaluru": (12.91, 74.86), "Hubballi-Dharwad": (15.36, 75.12),
    "Belagavi": (15.85, 74.50), "Kalaburagi": (17.33, 76.83), "Ballari": (15.14, 76.92),
    "Vijayapura": (16.83, 75.71), "Davanagere": (14.47, 75.92), "Shivamogga": (13.93, 75.57),
    "Tumakuru": (13.34, 77.10), "Udupi": (13.34, 74.75), "Hassan": (13.00, 76.10),
    "Mandya": (12.52, 76.90),
}


def _dt(days_ago_max=540):
    d = datetime.utcnow() - timedelta(days=random.randint(0, days_ago_max),
                                      hours=random.randint(0, 23),
                                      minutes=random.randint(0, 59))
    return d


def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def seed(n_cases=260, n_accused=180, n_victims=200):
    reset_db()
    db = SessionLocal()

    # ── Users (RBAC demo accounts — full Karnataka State Police hierarchy) ──
    demo_users = [
        # (username, full_name, role, badge, district, subdivision, station, range_name)
        ("dgp", "DGP K. Rajendra Kumar, IPS", "dgp", "KA-DGP-0001", "State HQ", None, "State HQ", None),
        ("addl_dgp", "Addl. DGP S. Murugan, IPS", "addl_dgp", "KA-ADGP-0003", "State HQ", None, "State HQ", None),
        ("ig", "IGP R. Hitendra, IPS", "ig", "KA-IGP-0012", "Bengaluru City", None, "Range HQ", "Bengaluru"),
        ("dig", "DIG V. Sharanappa, IPS", "dig", "KA-DIG-0018", "Mysuru", None, "Range HQ", "Mysuru"),
        ("sp", "SP D. Roopa, IPS", "sp", "KA-SP-0034", "Bengaluru City", None, "District HQ", "Bengaluru"),
        ("sp_mysuru", "SP H. Lakshmipathi", "sp", "KA-SP-0041", "Mysuru", None, "District HQ", "Mysuru"),
        ("dsp", "Dy.SP N. Prakash", "dsp", "KA-DSP-0071", "Bengaluru City", "Bengaluru East", "Subdivision HQ", "Bengaluru"),
        ("acp", "ACP M. Chandra", "acp", "KA-ACP-0089", "Bengaluru City", "Bengaluru West", "Subdivision HQ", "Bengaluru"),
        ("ci", "CI R. Gowda", "ci", "KA-CI-0125", "Bengaluru City", "Bengaluru South", "Bengaluru South PS", "Bengaluru"),
        ("sho", "Insp. M. Shetty", "sho", "KA-SHO-0442", "Bengaluru City", "Bengaluru East", "Central PS", "Bengaluru"),
        ("pi", "PI A. Kumar", "pi", "KA-PI-0567", "Bengaluru City", "Bengaluru East", "East PS", "Bengaluru"),
        ("si", "SI Anitha Rao", "sub_inspector", "KA-SI-1187", "Bengaluru City", "Bengaluru East", "Central PS", "Bengaluru"),
        ("asi", "ASI K. Venkatesh", "asi", "KA-ASI-2001", "Bengaluru City", "Bengaluru East", "Central PS", "Bengaluru"),
        ("hc", "HC Raju Nayak", "head_constable", "KA-HC-2891", "Bengaluru City", "Bengaluru East", "Central PS", "Bengaluru"),
        ("constable", "PC Ravi Gowda", "constable", "KA-PC-3391", "Bengaluru City", "Bengaluru East", "Central PS", "Bengaluru"),
        ("analyst", "Analyst A. Sharma", "analyst", "KA-ANL-2205", "Bengaluru City", None, "District HQ", "Bengaluru"),
        # Keep the old commander as DGP alias for backward compat
        ("commander", "Cmdr. S. Iyer", "dgp", "KA-CMD-0009", "State HQ", None, "State HQ", None),
    ]
    for uname, name, role, badge, dist, subdiv, stn, rng in demo_users:
        db.add(m.User(username=uname, full_name=name, email=f"{uname}@ksp.gov.in",
                      password="password", role=role, badge_number=badge, district=dist,
                      subdivision=subdiv, station=stn, range_name=rng))

    # ── Officers ──
    officers = []
    for i in range(40):
        dist = random.choice(DISTRICTS)
        o = m.Officer(badge_number=f"KA{1000+i}", name=fake.name(),
                      rank=random.choice(RANKS), posting_station=random.choice(STATIONS),
                      district=dist, contact_number=fake.msisdn()[:10])
        officers.append(o); db.add(o)

    # ── Accused ──
    accused = []
    for i in range(n_accused):
        dist = random.choice(DISTRICTS)
        prior = random.choices([0, 1, 2, 3, 5, 8], weights=[40, 25, 15, 10, 6, 4])[0]
        a = m.Accused(
            full_name=fake.name(), aliases=random.choice(["", fake.first_name(), fake.first_name()]),
            gender=random.choices(["Male", "Female"], weights=[85, 15])[0],
            age=random.randint(18, 62), address=fake.address().replace("\n", ", "),
            district=dist, phone_number=fake.msisdn()[:10],
            occupation=random.choice(OCCUPATIONS), education=random.choice(EDU),
            socio_economic=random.choices(SES, weights=[35, 25, 22, 12, 6])[0],
            urban_rural=random.choices(["Urban", "Rural"], weights=[62, 38])[0],
            migrant=random.random() < 0.28, previous_convictions=prior,
            status=random.choice(STATUS_ACCUSED),
        )
        accused.append(a); db.add(a)

    # ── Victims ──
    victims = []
    for i in range(n_victims):
        v = m.Victim(full_name=fake.name(),
                     gender=random.choice(["Male", "Female"]),
                     age=random.randint(5, 80), contact_number=fake.msisdn()[:10],
                     address=fake.address().replace("\n", ", "), district=random.choice(DISTRICTS),
                     occupation=random.choice(OCCUPATIONS),
                     statement_summary=fake.sentence(nb_words=12))
        victims.append(v); db.add(v)
    db.flush()  # assign ids

    # ── Cases + links + investigations + timeline + financial ──
    accounts = []
    for a in random.sample(accused, k=int(len(accused) * 0.5)):
        acc = m.FinancialAccount(account_number=fake.bban()[:16], holder_name=a.full_name,
                                 bank=random.choice(BANKS), account_type=random.choice(["Savings", "Current", "Wallet"]),
                                 accused_id=a.id, is_suspicious=random.random() < 0.3)
        accounts.append(acc); db.add(acc)
    # a few mule/shell accounts not tied to a known accused
    for _ in range(20):
        acc = m.FinancialAccount(account_number=fake.bban()[:16], holder_name=fake.name(),
                                 bank=random.choice(BANKS), account_type=random.choice(["Savings", "Wallet", "Crypto"]),
                                 accused_id=None, is_suspicious=random.random() < 0.6)
        accounts.append(acc); db.add(acc)
    db.flush()

    for i in range(n_cases):
        ct = random.choice(list(CRIME_TYPES.keys()))
        dist = random.choice(DISTRICTS)
        lat, lon = DISTRICT_GEO[dist]
        occ = _dt()
        is_fin = CRIME_TYPES[ct] == "Financial"
        loss = round(random.uniform(20000, 5000000), 0) if is_fin else (
            round(random.uniform(2000, 400000), 0) if CRIME_TYPES[ct] == "Property" else 0.0)
        case = m.Case(
            fir_number=f"FIR/{occ.year}/{dist[:3].upper()}/{1000+i}",
            title=f"{ct} at {fake.street_name()}",
            description=fake.paragraph(nb_sentences=3),
            crime_type=ct, crime_head=CRIME_TYPES[ct],
            modus_operandi=random.choice(MODUS[ct]),
            status=random.choices(STATUS_CASE, weights=[25, 30, 18, 20, 7])[0],
            severity=random.choices(SEVERITY, weights=[20, 40, 28, 12])[0],
            district=dist, station=random.choice(STATIONS),
            location_name=f"{fake.street_name()}, {dist}",
            latitude=lat + random.uniform(-0.25, 0.25), longitude=lon + random.uniform(-0.25, 0.25),
            is_financial=is_fin, loss_amount=loss,
            occurrence_date=occ, reported_date=occ + timedelta(days=random.randint(0, 4)),
        )
        db.add(case); db.flush()

        # link accused (some cases share accused -> networks)
        k = random.choices([1, 2, 3, 4], weights=[45, 30, 15, 10])[0]
        chosen = random.sample(accused, k=min(k, len(accused)))
        for j, a in enumerate(chosen):
            db.add(m.CaseAccused(case_id=case.id, accused_id=a.id,
                                 role_in_crime="Main" if j == 0 else random.choice(["Accomplice", "Financier", "Handler"])))
        # link victims
        for v in random.sample(victims, k=random.randint(0, 2)):
            db.add(m.CaseVictim(case_id=case.id, victim_id=v.id))

        # investigation
        off = random.choice(officers)
        inv_status = {"Open": "Active", "Under Investigation": "Active", "Chargesheeted": "Solved",
                      "Closed": "Solved", "Cold": "Cold"}[case.status]
        # map case status -> a sensible investigation stage
        stage = {"Open": "Initial Review", "Under Investigation": "Evidence Collection",
                 "Chargesheeted": "Charges Filed", "Closed": "Case Closed",
                 "Cold": "Intelligence Gathering"}[case.status]
        stages_list = ["Case Assigned", "Initial Review", "Evidence Collection", "Victim Analysis",
                       "Suspect Identification", "Witness Statements", "Intelligence Gathering",
                       "Criminal Analysis", "AI Investigation Completed", "Report Preparation",
                       "Charges Filed", "Case Closed"]
        prog = round((stages_list.index(stage) + 1) / len(stages_list) * 100)
        db.add(m.Investigation(case_id=case.id, officer_id=off.id,
                               summary=fake.paragraph(nb_sentences=2),
                               leads_details=fake.sentence(nb_words=14),
                               status=inv_status, progress=prog, current_stage=stage))

        # timeline
        base = case.reported_date
        evs = [("FIR Registered", "FIR", 0), ("Spot Inspection", "Evidence", 1),
               ("Witness Statement", "Statement", 3)]
        if case.status in ("Chargesheeted", "Closed"):
            evs += [("Arrest Made", "Arrest", 12), ("Chargesheet Filed", "Chargesheet", 40)]
        for title, etype, off_days in evs:
            db.add(m.TimelineEvent(case_id=case.id, event_title=title, event_type=etype,
                                   description=fake.sentence(nb_words=10),
                                   event_timestamp=base + timedelta(days=off_days)))

        # financial transactions for financial cases (money trail)
        if is_fin and len(accounts) > 4:
            trail_len = random.randint(2, 5)
            chain = random.sample(accounts, k=trail_len)
            amt = loss
            for s in range(trail_len - 1):
                db.add(m.Transaction(from_account_id=chain[s].id, to_account_id=chain[s + 1].id,
                                     amount=round(amt * random.uniform(0.6, 0.95), 0),
                                     channel=random.choice(["UPI", "NEFT", "IMPS", "Crypto"]),
                                     case_id=case.id, flagged=random.random() < 0.7,
                                     txn_timestamp=occ + timedelta(hours=random.randint(1, 72))))

    # ── Associations (network) from co-accused + explicit gangs ──
    # co-accused edges
    seen = set()
    rows = db.query(m.CaseAccused).all()
    by_case = {}
    for r in rows:
        by_case.setdefault(r.case_id, []).append(r.accused_id)
    for case_id, ids in by_case.items():
        for x in range(len(ids)):
            for y in range(x + 1, len(ids)):
                a, b = sorted((ids[x], ids[y]))
                if (a, b) in seen:
                    continue
                seen.add((a, b))
                db.add(m.Association(source_accused_id=a, target_accused_id=b,
                                     relationship_type="Co-accused", strength=1.0))
    # gang clusters
    for gang in GANGS:
        members = random.sample(accused, k=random.randint(4, 8))
        for x in range(len(members)):
            for y in range(x + 1, len(members)):
                if random.random() < 0.6:
                    a, b = sorted((members[x].id, members[y].id))
                    if (a, b) in seen:
                        continue
                    seen.add((a, b))
                    db.add(m.Association(source_accused_id=a, target_accused_id=b,
                                         relationship_type=random.choice(["Gang", "Associate", "Financial"]),
                                         gang_name=gang, strength=round(random.uniform(1.5, 4.0), 1)))

    # ── Behaviour profiles / risk scoring ──
    for a in accused:
        n_cases_a = len([r for r in rows if r.accused_id == a.id])
        raw = (a.previous_convictions * 12) + (n_cases_a * 8) + (10 if a.status == "Absconding" else 0)
        raw += random.randint(0, 15)
        score = min(100, raw)
        band = ("Critical" if score >= 75 else "High" if score >= 50
                else "Medium" if score >= 25 else "Low")
        types = list({db.get(m.Case, r.case_id).crime_type for r in rows if r.accused_id == a.id})
        db.add(m.BehaviorProfile(
            accused_id=a.id, risk_score=score, risk_band=band,
            is_habitual=(a.previous_convictions >= 3 or n_cases_a >= 3),
            behavioral_traits=", ".join(random.sample(
                ["impulsive", "organised", "violent", "tech-savvy", "repeat pattern",
                 "operates in group", "targets elderly", "night-active"], k=3)),
            propensity_tags=", ".join(types[:3]) if types else random.choice(list(CRIME_TYPES)),
            modus_operandi=random.choice(sum(MODUS.values(), [])),
        ))

    # ── Crime patterns ──
    pattern_defs = [
        ("Weekend Chain-Snatching Spree", "Chain Snatching", "Bengaluru City", "Weekend nights", "Two-wheeler snatch, Crowd distraction"),
        ("Festival-Season Burglary Wave", "Burglary", "Mysuru", "Festival season", "Night break-in, Lock-breaking"),
        ("UPI QR-Code Fraud Ring", "UPI Scam", "Bengaluru City", "Payday week", "QR-code scam, Fake payment link"),
        ("Highway Night Robbery", "Robbery", "Tumakuru", "Late night", "Highway robbery, Armed hold-up"),
        ("Fake Job Cyber Fraud", "Cyber Fraud", "Hubballi-Dharwad", "Month-end", "Fake job offer, Phishing"),
        ("Vehicle Theft Cluster", "Vehicle Theft", "Belagavi", "Weekday mornings", "Hotwiring, Tow-away"),
    ]
    for name, ct, dist, temporal, tags in pattern_defs:
        cnt = db.query(m.Case).filter(m.Case.crime_type == ct, m.Case.district == dist).count()
        db.add(m.CrimePattern(pattern_name=name, crime_type=ct, district=dist,
                              temporal_signature=temporal, modus_operandi_tags=tags,
                              description=f"Recurring {ct} pattern in {dist} ({temporal.lower()}).",
                              case_count=max(cnt, random.randint(3, 12))))

    # ── Predictions / early warning ──
    for _ in range(12):
        dist = random.choice(DISTRICTS)
        ct = random.choice(list(CRIME_TYPES.keys()))
        prob = round(random.uniform(0.45, 0.95), 2)
        start = datetime.utcnow() + timedelta(days=random.randint(1, 7))
        db.add(m.Prediction(
            target_area=dist, crime_type=ct, probability=prob,
            risk_level=("Critical" if prob >= 0.85 else "High" if prob >= 0.7 else "Medium"),
            forecast_window_start=start, forecast_window_end=start + timedelta(days=14),
            contributing_factors="; ".join(random.sample(
                ["recent spike in similar FIRs", "known offender released", "festival gathering",
                 "prior hotspot", "seasonal trend", "gang activity detected"], k=3)),
        ))

    # ── Alerts ──
    alert_defs = [
        ("Repeat offender spotted", "Repeat-offender", "High"),
        ("Gang activity surge in Chikpet", "Gang-activity", "Critical"),
        ("Emerging UPI fraud cluster", "Emerging-pattern", "High"),
        ("New hotspot: KR Market", "Hotspot", "Medium"),
        ("Suspicious money trail flagged", "Financial", "High"),
        ("Chain-snatching spike this weekend", "Emerging-pattern", "Medium"),
    ]
    for title, atype, sev in alert_defs:
        db.add(m.Alert(title=title, message=fake.sentence(nb_words=16), severity=sev,
                       alert_type=atype, district=random.choice(DISTRICTS),
                       created_at=_dt(20)))

    db.commit()
    counts = {t.__tablename__: db.query(t).count() for t in
              [m.User, m.Case, m.Accused, m.Victim, m.Officer, m.Association,
               m.Transaction, m.Alert, m.Prediction, m.CrimePattern, m.BehaviorProfile]}
    db.close()
    return counts


if __name__ == "__main__":
    print("Seeding fresh crime-intelligence database...")
    c = seed()
    for k, v in c.items():
        print(f"  {k:20s} {v}")
    print("Done.")
