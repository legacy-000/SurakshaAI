"""
Generate CSV seed data files for all 34 Catalyst Data Store tables.
Target: meaningful AI analytics scale (~50 cases, ~500+ total rows).
Usage: python scripts/generate_seed_csvs.py
"""
import csv, os, random
from datetime import datetime, timedelta

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(DATA_DIR, exist_ok=True)

random.seed(42)

def write_csv(filename, headers, rows):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)
    print(f"  {filename}: {len(rows)} rows")

# ── Lookups ──────────────────────────────────────────────

write_csv("CasteMaster.csv",
    ["caste_master_id","caste_master_name"],
    [[i+1,n] for i,n in enumerate(["General","OBC","SC","ST","Vokkaliga","Lingayat","Kuruba","Idiga"])])

write_csv("ReligionMaster.csv",
    ["ReligionID","ReligionName"],
    [[i+1,n] for i,n in enumerate(["Hindu","Muslim","Christian","Sikh","Jain","Buddhist","Parsi","Other"])])

write_csv("OccupationMaster.csv",
    ["OccupationID","OccupationName"],
    [[i+1,n] for i,n in enumerate([
        "Government Employee","Private Employee","Farmer","Business","Student",
        "Unemployed","Daily Wage","Retired","Homemaker","Driver","Shopkeeper","Teacher",
        "Lawyer","Doctor","Engineer","IT Professional","Nurse","Security Guard"])])

write_csv("CaseCategory.csv",
    ["CaseCategoryID","LookupValue"],
    [["1","FIR"],["2","UDR"],["3","Zero FIR"],["4","PAR"]])

write_csv("GravityOffence.csv",
    ["GravityOffenceID","LookupValue"],
    [["1","Heinous"],["2","Non-Heinous"],["3","Petty"]])

write_csv("CaseStatusMaster.csv",
    ["CaseStatusID","CaseStatusName"],
    [[i+1,n] for i,n in enumerate([
        "Under Investigation","Charge Sheeted","Closed","Pending Trial",
        "Transferred","Awaiting Forensic"])])

write_csv("UnitType.csv",
    ["UnitTypeID","UnitTypeName","CityDistState","Hierarchy","Active"],
    [["1","Police Station","City","3","1"],["2","Circle Office","City","2","1"],
     ["3","District Office","District","1","1"]])

write_csv("Rank.csv",
    ["RankID","RankName","Hierarchy","Active"],
    [[i+1,n,"8-i","1"] for i,n in enumerate([
        "Director General","IG","SP","DSP","Inspector","Sub-Inspector","Head Constable","Constable"])])

write_csv("Designation.csv",
    ["DesignationID","DesignationName","Active","SortOrder"],
    [[i+1,n,"1",str(i+1)] for i,n in enumerate([
        "SHO","Investigating Officer","CI","SI","ASI","Addl SP"])])

# ── Geography ────────────────────────────────────────────

write_csv("State.csv",
    ["StateID","StateName","NationalityID","Active"],
    [[str(i+1),n,"1","1"] for i,n in enumerate([
        "Karnataka","Tamil Nadu","Kerala","Andhra Pradesh","Maharashtra"])])

write_csv("District.csv",
    ["DistrictID","DistrictName","StateID","Active"],
    [[str(i+1),n,"1","1"] for i,n in enumerate([
        "Bengaluru Urban","Bengaluru Rural","Mysuru","Hubballi","Mangaluru",
        "Belagavi","Shivamogga","Dharwad","Tumakuru","Kalaburagi"])])

write_csv("Court.csv",
    ["CourtID","CourtName","DistrictID","StateID","Active"],
    [["1","City Civil Court Bangalore","1","1","1"],
     ["2","Sessions Court Bangalore","1","1","1"],
     ["3","High Court of Karnataka","1","1","1"],
     ["4","Fast Track Court Mysuru","3","1","1"],
     ["5","District Court Hubballi","4","1","1"]])

stations = [
    (1001,"MG Road PS",1),(1002,"Indiranagar PS",1),(1003,"Koramangala PS",1),
    (1004,"Whitefield PS",1),(1005,"Jayanagar PS",1),(1006,"Malleshwaram PS",1),
    (1007,"Mysuru City PS",3),(1008,"Hubballi City PS",4)]
write_csv("Unit.csv",
    ["UnitID","UnitName","TypeID","ParentUnit","NationalityID","StateID","DistrictID","Active"],
    [[str(id),n,"1","","1","1",str(dist),"1"] for id,n,dist in stations])

# ── Employees (15) ──────────────────────────────────────
emps = [
    (101,"101","1001","5","1","KAR123456","Rajesh Kumar","1980-05-15","1","1","0","2005-06-01"),
    (102,"101","1001","6","2","KAR123457","Suresh Patel","1985-08-22","1","2","0","2010-09-15"),
    (103,"101","1001","6","4","KAR123458","Anita Sharma","1990-03-10","2","3","0","2015-01-20"),
    (104,"101","1002","5","1","KAR123459","Venkatesh Rao","1982-11-30","1","1","0","2007-04-10"),
    (105,"101","1002","6","2","KAR123460","Kavitha N","1988-07-14","2","2","0","2012-08-01"),
    (106,"101","1003","5","1","KAR123461","Mohan Das","1981-02-28","1","1","0","2006-03-15"),
    (107,"101","1003","6","2","KAR123462","Priya K","1992-09-05","2","3","0","2016-11-20"),
    (108,"101","1004","5","1","KAR123463","Srinivas Murthy","1979-12-01","1","1","0","2003-05-10"),
    (109,"101","1004","6","4","KAR123464","Naveen G","1991-04-18","1","2","0","2014-07-25"),
    (110,"101","1005","5","1","KAR123465","Lakshmi Devi","1983-06-22","2","1","0","2008-09-30"),
    (111,"101","1005","6","2","KAR123466","Ramesh Babu","1987-10-11","1","2","0","2011-12-05"),
    (112,"101","1006","6","4","KAR123467","Sunita Rao","1993-01-30","2","3","0","2017-04-15"),
    (113,"101","1007","5","1","KAR123468","Karthik S","1984-07-08","1","1","0","2009-06-20"),
    (114,"101","1008","5","1","KAR123469","Prakash Hegde","1985-09-12","1","1","0","2010-02-14"),
    (115,"101","1003","7","4","KAR123470","Manjunath R","1995-11-25","1","2","0","2018-08-01")]
write_csv("Employee.csv",
    ["EmployeeID","DistrictID","UnitID","RankID","DesignationID","KGID","FirstName",
     "EmployeeDOB","GenderID","BloodGroupID","PhysicallyChallenged","AppointmentDate"],
    [[str(e[0]),e[1],e[2],e[3],e[4],e[5],e[6],e[7],e[8],e[9],e[10],e[11]] for e in emps])

# ── Legal Reference ──────────────────────────────────────

write_csv("Act.csv",
    ["ActCode","ActDescription","ShortName","Active"],
    [["IPC","Indian Penal Code","IPC","1"],
     ["NDPS","Narcotic Drugs and Psychotropic Substances Act","NDPS","1"],
     ["CrPC","Code of Criminal Procedure","CrPC","1"],
     ["IT_Act","Information Technology Act","IT Act","1"],
     ["KA_Police","Karnataka Police Act","KA PC","1"]])

sections = [
    ("IPC","302","Murder","1"),("IPC","307","Attempt to murder","1"),
    ("IPC","324","Voluntary hurt by weapon","1"),("IPC","326","Grievous hurt by acid/weapon","1"),
    ("IPC","354","Assault on woman","1"),("IPC","376","Rape","1"),
    ("IPC","379","Theft","1"),("IPC","380","Theft in dwelling","1"),
    ("IPC","392","Robbery","1"),("IPC","394","Robbery with hurt","1"),
    ("IPC","397","Dacoity with firearm","1"),("IPC","420","Cheating","1"),
    ("IPC","457","Lurking house-trespass","1"),("IPC","498A","Cruelty by husband","1"),
    ("NDPS","20","Cultivation of cannabis","1"),("NDPS","21","Possession of psychotropic","1"),
    ("IT_Act","66","Computer-related offences","1"),("IT_Act","67","Publishing obscene material","1"),
    ("CrPC","144","Unlawful assembly order","1"),("KA_Police","107","Public nuisance","1")]
write_csv("Section.csv",
    ["ActCode","SectionCode","SectionDescription","Active"], sections)

# CrimeHead (6) + CrimeSubHead (12)
write_csv("CrimeHead.csv",
    ["CrimeHeadID","CrimeGroupName","Active"],
    [["1","Crimes Against Body","1"],["2","Crimes Against Property","1"],
     ["3","Crimes Against Women","1"],["4","Economic Offences","1"],
     ["5","Cyber Crimes","1"],["6","Narcotics","1"]])
write_csv("CrimeSubHead.csv",
    ["CrimeSubHeadID","CrimeHeadID","CrimeHeadName","SeqID"],
    [["1","1","Murder","1"],["2","1","Attempt to Murder","2"],["3","1","Assault","3"],
     ["4","2","Robbery","1"],["5","2","Burglary","2"],["6","2","Theft","3"],
     ["7","2","Vehicle Theft","4"],["8","3","Rape","1"],["9","3","Dowry Case","2"],
     ["10","4","Fraud","1"],["11","5","Cyber Fraud","1"],["12","6","Drug Possession","1"]])

# CrimeHeadActSection mapping
write_csv("CrimeHeadActSection.csv",
    ["CrimeHeadID","ActCode","SectionCode"],
    [["1","IPC","302"],["1","IPC","307"],["1","IPC","324"],["2","IPC","379"],
     ["2","IPC","380"],["2","IPC","392"],["2","IPC","457"],["3","IPC","354"],
     ["3","IPC","376"],["3","IPC","498A"],["4","IPC","420"],["5","IT_Act","66"],
     ["5","IT_Act","67"],["6","NDPS","20"],["6","NDPS","21"]])

# ── Core Data: 50 Cases ─────────────────────────────────

locations = [
    ("MG Road","12.9716","77.5946","1001","1"),
    ("Koramangala","12.9352","77.6245","1003","1"),
    ("Indiranagar","12.9783","77.6408","1002","1"),
    ("Whitefield","12.9698","77.7500","1004","1"),
    ("Jayanagar","12.9250","77.5938","1005","1"),
    ("Malleshwaram","12.9943","77.5710","1006","1"),
    ("Marathahalli","12.9591","77.6974","1004","1"),
    ("Electronic City","12.8399","77.6770","1003","1"),
    ("Yeshwanthpur","13.0269","77.5491","1006","1"),
    ("BTM Layout","12.9166","77.6101","1005","1"),
    ("Rajajinagar","12.9925","77.5527","1006","1"),
    ("Jalahalli","13.0451","77.5450","1003","1"),
    ("Banashankari","12.9154","77.5534","1005","1"),
    ("Yelahanka","13.1007","77.5963","1002","1"),
    ("Hebbal","13.0358","77.5970","1002","1"),
]
crime_types = [
    (1,1,"Theft of laptop from parked car","379","6","IPC"),
    (1,1,"Mobile phone snatched on street","379","6","IPC"),
    (2,2,"Assault outside bar","324","3","IPC"),
    (2,2,"Road rage assault","307","3","IPC"),
    (1,2,"Robbery at ATM","392","4","IPC"),
    (1,1,"Burglary in apartment","457","5","IPC"),
    (5,3,"Cyber fraud — OTP scam","420","10","IPC"),
    (5,3,"Phishing attack on bank customer","66","11","IT_Act"),
    (3,3,"Dowry harassment case","498A","9","IPC"),
    (3,3,"Sexual assault case","354","8","IPC"),
    (1,2,"Vehicle theft — bike stolen","379","7","IPC"),
    (2,1,"Attempted murder in gang fight","307","2","IPC"),
    (1,2,"Gold chain snatching","392","4","IPC"),
    (6,1,"Cannabis possession","20","12","NDPS"),
    (1,1,"Housebreaking at daytime","457","5","IPC"),
    (4,1,"Cheating in property deal","420","10","IPC"),
    (5,3,"Obscene content uploaded online","67","11","IT_Act"),
    (2,2,"Hurt by dangerous weapon","324","3","IPC"),
    (1,1,"Bag lifting in bus","379","6","IPC"),
    (3,3,"Rape of minor","376","8","IPC"),
]
comp_names = [
    "Ravi Kumar","Sita Sharma","Mohammed Ali","Priya Singh","Venkatesh Iyer",
    "Lakshmi N","Abdul Rahman","Geeta Reddy","Suresh Babu","Ananya K",
    "Mahesh Gowda","Divya M","Santosh Patil","Kavitha R","Rameshwar Naik",
    "Pooja Jain","Irfan Khan","Sunitha Devi","Gopal Rao","Meena A"]
accused_names = [
    "John Doe","Jane Smith","Rohit Verma","Vikram Raj","Santosh R",
    "Manoj Kumar","Sneha Reddy","Ravi Teja","Pradeep N","Suresh Poojari",
    "Anil Kumble","Rashid Khan","Naveen Gowda","Satish Shetty","Hari Prasad",
    "Deepak M","Arjun Singh","Rahul Dev","Prakash Rai","Kiran Y",
    "Monica S","Arun Kumar","Vijay Patil","Sharan B","Lokesh R"]
victim_names = [
    "Ravi Kumar","Priya Singh","Rajeshwari N","Mohan G","Anita Shetty",
    "Karthik S","Shiela Thomas","Deepa M","Narayan Rao","Uma Devi",
    "Prakash Hegde","Sushma R","Girish K","Meenakshi A","Harsha Vardhan",
    "Lata Mangeshkar","Rajiv Nair","Shweta P","Ramesh Chandra","Jaya K"]

num_cases = 50
case_master = []
complainants = []
act_sections = []
victims = []
accused = []
arrests = []
chargesheets = []
inv_occur = []
timelines = []
accused_id_counter = 1
arrest_id_counter = 1
cs_id_counter = 1
comp_id_counter = 1
vic_id_counter = 1

start_date = datetime(2026, 1, 1)

for cid in range(1, num_cases + 1):
    loc_name, lat, lon, ps_id, dist_id = random.choice(locations)
    gt, cr_sub, brief, sect, subhead_id, act = random.choice(crime_types)
    status = random.choice(["1","1","2","3","4","5"])
    court = random.choice(["1","2","3","1","2","4","5"])
    cat = random.choice(["1","1","1","2","3"])
    grav = "1" if gt <= 2 and subhead_id in ["1","2","8","20"] else random.choice(["2","2","3"])
    emps_for_ps = [e for e in emps if e[2] == ps_id]
    io = str(random.choice(emps_for_ps)[0]) if emps_for_ps else "101"
    reg_offset = random.randint(0, 175)  # ~6 months
    reg_date = start_date + timedelta(days=reg_offset, hours=random.randint(8,18), minutes=random.randint(0,59))
    inc_from = reg_date - timedelta(hours=random.randint(1,48), minutes=random.randint(0,59))
    inc_to = inc_from + timedelta(hours=random.randint(1,4))
    ps_received = inc_from + timedelta(hours=random.randint(1,12))
    crime_no_prefix = str(104430006 + random.choice([0,1,2,3]))
    crime_no = f"{crime_no_prefix}{reg_date.year}{cid:06d}"

    case_master.append([str(cid), crime_no, f"2026{cid:06d}",
        reg_date.strftime("%Y-%m-%d %H:%M:%S"), io, ps_id, cat, grav,
        str(gt), str(cr_sub), status, court,
        inc_from.strftime("%Y-%m-%d %H:%M:%S"), inc_to.strftime("%Y-%m-%d %H:%M:%S"),
        ps_received.strftime("%Y-%m-%d %H:%M:%S"), lat, lon,
        f"{brief} reported at {loc_name}. Case registered on {reg_date.strftime('%d-%b-%Y')}."])

    # Inv_OccuranceTime
    inv_occur.append([str(cid),
        inc_from.strftime("%Y-%m-%d %H:%M:%S"), inc_to.strftime("%Y-%m-%d %H:%M:%S"),
        lat, lon, f"Incident occurred at {loc_name}. {brief}."])

    # Complainants (1-2 per case)
    for j in range(random.choice([1,1,1,2])):
        cn = random.choice(comp_names)
        age = random.randint(22, 65)
        occ = str(random.randint(1, 18))
        rel = str(random.randint(1, 8))
        cas = str(random.randint(1, 8))
        gid = str(random.randint(1, 2))
        complainants.append([str(comp_id_counter), str(cid), cn, str(age), occ, rel, cas, gid])
        comp_id_counter += 1

    # Act-Section mapping
    as_list = [(str(cid), act, sect, "1", "1")]
    if random.random() < 0.4:
        extra = random.choice(sections)
        as_list.append((str(cid), extra[0], extra[1], "2", "2"))
    act_sections.extend(as_list)

    # Victims (0-1 per case, ~80% have victims)
    if random.random() < 0.8:
        vn = random.choice(victim_names)
        vage = random.randint(18, 70)
        vgid = str(random.randint(1, 2))
        vpol = random.choice(["0","0","0","1"])
        victims.append([str(vic_id_counter), str(cid), vn, str(vage), vgid, vpol])
        vic_id_counter += 1

    # Accused (1-3 per case)
    num_acc = random.choice([1,1,1,2,2,3])
    for j in range(num_acc):
        an = random.choice(accused_names)
        aage = random.randint(18, 55)
        agid = str(random.randint(1, 2))
        pid = f"A{accused_id_counter}"
        accused.append([str(accused_id_counter), str(cid), an, str(aage), agid, pid])
        # Arrest (60% of accused)
        if random.random() < 0.6:
            arr_date = reg_date + timedelta(days=random.randint(1, 30), hours=random.randint(6, 20))
            arr_type = random.choice(["1","1","2"])
            arr_state = random.choice(["1","1","2"])
            arr_dist = random.choice(["1","2","3"])
            arrests.append([str(arrest_id_counter), str(cid), arr_type,
                arr_date.strftime("%Y-%m-%d"), arr_state, arr_dist,
                ps_id, io, court, str(accused_id_counter), "1", "0"])
            arrest_id_counter += 1
        accused_id_counter += 1

    # Chargesheet (60% of cases)
    if random.random() < 0.6:
        cs_date = reg_date + timedelta(days=random.randint(30, 90), hours=random.randint(10, 16))
        cs_type = random.choice(["A","A","A","B","C"])
        chargesheets.append([str(cs_id_counter), str(cid),
            cs_date.strftime("%Y-%m-%d %H:%M:%S"), cs_type, io])
        cs_id_counter += 1

    # Timeline events (3-6 per case)
    events = [
        ("FIR Registered", f"FIR registered at {loc_name} PS", reg_date.strftime("%Y-%m-%d %H:%M:%S"), "Registration", loc_name, io),
        ("Investigation Started", "Case assigned to IO", (reg_date+timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"), "Investigation", loc_name, io),
    ]
    if random.random() < 0.6:
        ev_date = reg_date + timedelta(days=random.randint(1,7))
        events.append(("Scene Inspection", "Police team visited crime scene", ev_date.strftime("%Y-%m-%d %H:%M:%S"), "Field Visit", loc_name, io))
    if random.random() < 0.5:
        ev_date = reg_date + timedelta(days=random.randint(3,14))
        events.append(("Witness Statement", "Witness statement recorded", ev_date.strftime("%Y-%m-%d %H:%M:%S"), "Investigation", loc_name, io))
    if random.random() < 0.4:
        ev_date = reg_date + timedelta(days=random.randint(7,21))
        events.append(("Forensic Report", "Forensic analysis report received", ev_date.strftime("%Y-%m-%d %H:%M:%S"), "Forensic", loc_name, io))
    for ev in events:
        timelines.append([str(cid), ev[0], ev[1], ev[2], ev[3], ev[4], ev[5]])

write_csv("CaseMaster.csv",
    ["CaseMasterID","CrimeNo","CaseNo","CrimeRegisteredDate","PolicePersonID",
     "PoliceStationID","CaseCategoryID","GravityOffenceID","CrimeMajorHeadID",
     "CrimeMinorHeadID","CaseStatusID","CourtID","IncidentFromDate","IncidentToDate",
     "InfoReceivedPSDate","Latitude","Longitude","BriefFacts"], case_master)

write_csv("ComplainantDetails.csv",
    ["ComplainantID","CaseMasterID","ComplainantName","AgeYear","OccupationID",
     "ReligionID","CasteID","GenderID"], complainants)

write_csv("ActSectionAssociation.csv",
    ["CaseMasterID","ActID","SectionID","ActOrderID","SectionOrderID"], act_sections)

write_csv("Victim.csv",
    ["VictimMasterID","CaseMasterID","VictimName","AgeYear","GenderID","VictimPolice"], victims)

write_csv("Accused.csv",
    ["AccusedMasterID","CaseMasterID","AccusedName","AgeYear","GenderID","PersonID"], accused)

write_csv("ArrestSurrender.csv",
    ["ArrestSurrenderID","CaseMasterID","ArrestSurrenderTypeID","ArrestSurrenderDate",
     "ArrestSurrenderStateId","ArrestSurrenderDistrictId","PoliceStationID",
     "IOID","CourtID","AccusedMasterID","IsAccused","IsComplainantAccused"], arrests)

write_csv("ChargesheetDetails.csv",
    ["CSID","CaseMasterID","csdate","cstype","PolicePersonID"], chargesheets)

write_csv("Inv_OccuranceTime.csv",
    ["CaseMasterID","IncidentFromDate","IncidentToDate","latitude","longitude","location_description"],
    [[r[0],r[1],r[2],r[3],r[4],r[5]] for r in inv_occur])

write_csv("inv_arrestsurrenderaccused.csv",
    ["ArrestSurrenderID","AccusedMasterID"],
    [[str(i+1), r[9]] for i,r in enumerate(arrests)])

write_csv("TimelineEvent.csv",
    ["CaseMasterID","Title","Description","EventDate","EventType","Location","CreatedBy"], timelines)

# ── AI Supplementals ─────────────────────────────────────

behavior_subjects = [
    ("John Doe","Repeat Offender","Night theft in commercial areas","High","Night commercial theft","85.5","History of 10+ theft cases","2026-07-01"),
    ("Rohit Verma","Violent Offender","Assault during robbery attempts","High","Armed robbery pattern","78.0","Prior assault conviction","2026-07-02"),
    ("Manoj Kumar","Property Offender","Burglary in apartments posing as delivery","Medium","Delivery scam burglary","72.3","Modus operandi consistent","2026-07-05"),
    ("Vikram Raj","Cyber Criminal","Phishing calls targeting elderly","High","Elderly-targeted phishing","91.2","Linked to 15+ cyber fraud cases","2026-07-08"),
    ("Sneha Reddy","Repeat Offender","Chain snatching in market areas","Medium","Market chain snatching","65.0","Active in KR Market area","2026-07-10"),
    ("Pradeep N","Vehicle Offender","Motorcycle theft in parking lots","Medium","Parking lot theft ring","70.5","Part of organized vehicle theft ring","2026-07-12"),
    ("Satish Shetty","Drug Offender","Cannabis distribution near colleges","High","College-area drug distribution","82.0","Under surveillance","2026-07-15"),
    ("Deepak M","Property Offender","Housebreaking during daytime","Medium","Daytime housebreaking","68.5","Targets unoccupied homes","2026-07-18"),
]
write_csv("BehaviorProfile.csv",
    ["SubjectName","ProfileType","MO","RiskLevel","Pattern","Score","Notes","CreatedDate"],
    behavior_subjects)

crime_patterns = [
    ("Night Theft Cluster","Theft incidents concentrated in commercial areas 10PM-4AM","Theft","500","Weekdays 22:00-04:00","lock-picking,vehicle-breaking,commercial-area"),
    ("Weekend Assault Pattern","Assaults near transit hubs Fri-Sat evenings","Assault","300","Fri-Sat 20:00-02:00","public-transit,alcohol-related,group"),
    ("Residential Burglary Ring","Burglaries targeting unoccupied homes work hours","Burglary","800","Mon-Fri 09:00-17:00","forced-entry,rear-entrance,weekday"),
    ("Vehicle Theft Corridor","Stolen vehicles traced to highway corridors","Vehicle Theft","2000","All days 00:00-06:00","hotwiring,export-ring,highway"),
    ("Cyber Fraud Network","VoIP fraud calls targeting elderly 10AM-6PM","Fraud","100","All days 10:00-18:00","voip-spoofing,elderly-target,banking"),
    ("Market Chain Snatching","Gold chain snatching in crowded market areas","Robbery","200","Weekends 12:00-20:00","snatch-and-run,crowded-market,two-wheeler"),
    ("Pub Brawl Seasonals","Assaults outside pubs Fri-Sat nights","Assault","150","Fri-Sat 23:00-03:00","pub-area,weekend,alcohol-fueled"),
    ("ATM Robbery Cluster","Targeting solo ATM users late night","Robbery","100","All days 22:00-02:00","atm-target,solo-victim,weapon-show"),
    ("College Drug Distribution","Drug peddling near college campuses during semesters","Drug Offence","300","Mon-Sat 10:00-16:00","college-area,cannabis,p2p-sale"),
    ("DTPH Pattern","Dowry harassment cases post-wedding first 3 years","Domestic Crime","50","All days all hours","dowry-harassment,in-laws,marital"),
]
write_csv("CrimePattern.csv",
    ["pattern_name","description","crime_type","hotspot_radius_meters","temporal_signature","modus_operandi_tags"],
    crime_patterns)

alerts = [
    ("Theft Surge MG Road","Theft cases up 35% in MG Road area this month","High","Crime Trend","Active","IO101","2026-06-15 08:00:00",""),
    ("Burglary Warning Indiranagar","3 burglaries in Indiranagar this week","High","Crime Trend","Active","IO104","2026-06-18 09:30:00",""),
    ("Cyber Fraud Spike","Phishing complaints doubled in last 15 days","Medium","Cyber Crime","Active","IO102","2026-06-20 10:00:00",""),
    ("Hotspot: Koramangala","Predicted assault hotspot near bus stop","Medium","Prediction","Active","IO106","2026-06-22 06:00:00",""),
    ("Night Patrol Alert","Increased thefts in commercial zones at night","High","Patrol Recommendation","Active","IO108","2026-06-25 07:30:00",""),
    ("Repeat Offender Active","John Doe spotted in MG Road area","Critical","Offender Tracking","Active","IO101","2026-06-28 14:00:00",""),
    ("Vehicle Theft Ring","Organized vehicle theft ring operating in Whitefield","High","Intelligence","Active","IO108","2026-07-01 08:00:00",""),
    ("College Drug Alert","Drug peddling reported near 3 colleges","Medium","Narcotics","Active","IO106","2026-07-03 10:00:00",""),
    ("ATM Robbery Risk","Increased ATM robbery risk in Electronic City","Medium","Prediction","Active","IO107","2026-07-05 06:00:00",""),
    ("Weekend Patrol Needed","Assaults predicted near pubs this weekend","High","Patrol Recommendation","Active","IO106","2026-07-07 16:00:00",""),
]
write_csv("Alert.csv",
    ["Title","Message","Severity","Type","Status","AssignedTo","CreatedDate","ResolvedDate"], alerts)

predictions = [
    ("Burglary Risk Zone","Burglary","Indiranagar","12.9783","77.6408","0.85","2026-07-15","v1.0","Active"),
    ("Theft Hotspot","Theft","MG Road","12.9716","77.5946","0.78","2026-07-20","v1.0","Active"),
    ("Assault Risk Area","Assault","Koramangala Bus Stand","12.9352","77.6245","0.72","2026-07-18","v1.0","Active"),
    ("Cyber Fraud Zone","Fraud","Electronic City","12.8399","77.6770","0.81","2026-07-22","v1.0","Active"),
    ("Vehicle Theft Risk","Vehicle Theft","Whitefield","12.9698","77.7500","0.74","2026-07-25","v1.0","Active"),
    ("Robbery Hotspot","Robbery","BTM Layout","12.9166","77.6101","0.69","2026-07-19","v1.0","Active"),
    ("Drug Activity Zone","Drug Offence","Jayanagar College Area","12.9250","77.5938","0.77","2026-07-21","v1.0","Active"),
    ("Snatching Risk","Robbery","KR Market","12.9550","77.5750","0.65","2026-07-23","v1.0","Active"),
    ("Night Crime Zone","Theft","Malleshwaram","12.9943","77.5710","0.71","2026-07-24","v1.0","Active"),
    ("Weekend Assault Risk","Assault","MG Road Pubs","12.9716","77.5946","0.68","2026-07-26","v1.0","Active"),
    ("Dacoity Risk","Robbery","Marathahalli","12.9591","77.6974","0.60","2026-07-28","v1.0","Active"),
    ("Chain Snatching Alert","Robbery","Jayanagar 4th Block","12.9300","77.5800","0.73","2026-07-27","v1.0","Active"),
]
write_csv("Prediction.csv",
    ["Title","CrimeType","Location","Latitude","Longitude","Probability","PredictedDate","ModelVersion","Status"],
    predictions)

chat_contexts = [
    ("SESS001","USER001","Show theft cases in MG Road","Found 12 theft cases registered in MG Road area.", "2026-07-01 10:30:00"),
    ("SESS001","USER001","Which areas have highest crime?","MG Road (15 cases), Koramangala (12 cases), Indiranagar (10 cases).", "2026-07-01 10:31:00"),
    ("SESS001","USER001","Show monthly trend","Jan:3 Feb:5 Mar:7 Apr:9 May:12 Jun:14 — rising trend.", "2026-07-01 10:32:00"),
    ("SESS002","USER002","Whose accused name is John Doe?","John Doe is accused in Case #1 (Theft at MG Road). Repeat offender.", "2026-07-02 14:00:00"),
    ("SESS002","USER002","Map of all burglary cases","Found 6 burglary cases. Mapping to Indiranagar, Whitefield, Jayanagar.", "2026-07-02 14:01:00"),
    ("SESS002","USER002","Pattern analysis for last 3 months","Peak crime time: 10PM-2AM. Most affected: MG Road corridor.", "2026-07-02 14:03:00"),
    ("SESS003","USER003","List cases under IPC 420","8 cases found involving cheating/fraud under IPC 420.", "2026-07-03 09:00:00"),
    ("SESS003","USER003","Show network connections","3 accused linked across 5 cases in organized theft ring.", "2026-07-03 09:02:00"),
    ("SESS004","USER004","Generate investigation report for Case 1","Report generated: Case 202600001 — Theft at MG Road.", "2026-07-04 11:00:00"),
    ("SESS004","USER004","Similar cases to Case 2","3 similar assault cases found in Koramangala area.", "2026-07-04 11:01:00"),
    ("SESS004","USER004","Predict next crime hotspot","Model predicts Whitefield as next hotspot (probability 0.74).", "2026-07-04 11:02:00"),
    ("SESS005","USER005","How many accused per case?","Average 1.7 accused per case. Max: 3 (Case #15, #23).", "2026-07-05 15:30:00"),
    ("SESS005","USER005","Show unsolved cases","15 cases marked as Under Investigation.", "2026-07-05 15:31:00"),
    ("SESS006","USER006","Compare this month vs last month","This month: 14 cases. Last month: 12 cases. 16.7% increase.", "2026-07-06 10:00:00"),
    ("SESS006","USER006","Export crime statistics","CSV exported: crime_stats_jul_2026.csv (34 records).", "2026-07-06 10:01:00"),
]
write_csv("ChatContext.csv",
    ["SessionID","UserID","Message","Response","Timestamp"], chat_contexts)

total = sum([
    len(case_master), len(complainants), len(act_sections), len(victims), len(accused),
    len(arrests), len(chargesheets), len(inv_occur), len(arrests), len(timelines),
    8, 8, 18, 4, 3, 6, 3, 8, 6, 5, 20, 6, 12, 15, 5, 10, 15, 15, 10, 12, 15, 8, 10, 12
])
print(f"\nTotal rows across all CSVs: ~{total}")
