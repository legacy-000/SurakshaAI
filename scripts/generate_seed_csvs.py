"""
Generate CSV seed data files for all Catalyst Data Store tables.
Usage: python scripts/generate_seed_csvs.py
Each CSV can be imported via: catalyst ds:import ./data/<table>.csv --table <TableName>
"""
import csv
import os
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(DATA_DIR, exist_ok=True)


def write_csv(filename, headers, rows):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    print(f"  ✅ {filename} ({len(rows)} rows)")


# ============================================================
# 1. CaseMaster
# ============================================================
write_csv("CaseMaster.csv",
    ["CaseMasterID", "CrimeNo", "CaseNo", "CrimeRegisteredDate", "PolicePersonID",
     "PoliceStationID", "CaseCategoryID", "GravityOffenceID", "CrimeMajorHeadID",
     "CrimeMinorHeadID", "CaseStatusID", "CourtID", "IncidentFromDate", "IncidentToDate",
     "InfoReceivedPSDate", "Latitude", "Longitude", "BriefFacts"],
    [
        ["1", "104430006202600001", "202600001", "2026-01-15 10:30:00", "101",
         "1001", "1", "1", "1", "1", "1", "1", "2026-01-14 20:00:00", "2026-01-14 22:00:00",
         "2026-01-15 08:00:00", "12.9716", "77.5946", "Theft reported at MG Road area. Victim reported missing laptop."],
        ["2", "104430006202600002", "202600002", "2026-02-20 14:00:00", "102",
         "1001", "1", "2", "2", "3", "1", "2", "2026-02-19 23:00:00", "2026-02-20 01:00:00",
         "2026-02-20 12:00:00", "12.9352", "77.6245", "Assault case reported near Koramangala bus stop."],
        ["3", "304430006202600001", "202600003", "2026-03-05 09:00:00", "103",
         "1002", "2", "1", "1", "2", "2", "1", "2026-03-04 18:00:00", "2026-03-04 20:00:00",
         "2026-03-05 07:00:00", "12.9815", "77.6042", "UDR registered for unnatural death reported in Indiranagar."],
    ])


# ============================================================
# 2. ComplainantDetails
# ============================================================
write_csv("ComplainantDetails.csv",
    ["ComplainantID", "CaseMasterID", "ComplainantName", "AgeYear", "OccupationID", "ReligionID", "CasteID", "GenderID"],
    [
        ["1", "1", "Ravi Kumar", "32", "1", "1", "1", "1"],
        ["2", "1", "Sita Sharma", "28", "2", "2", "2", "2"],
        ["3", "2", "Mohammed Ali", "45", "3", "3", "3", "1"],
    ])


# ============================================================
# 3. ActSectionAssociation
# ============================================================
write_csv("ActSectionAssociation.csv",
    ["CaseMasterID", "ActID", "SectionID", "ActOrderID", "SectionOrderID"],
    [
        ["1", "IPC", "379", "1", "1"],
        ["1", "IPC", "380", "2", "2"],
        ["2", "IPC", "324", "1", "1"],
        ["2", "IPC", "307", "2", "2"],
    ])


# ============================================================
# 4. Victim
# ============================================================
write_csv("Victim.csv",
    ["VictimMasterID", "CaseMasterID", "VictimName", "AgeYear", "GenderID", "VictimPolice"],
    [
        ["1", "1", "Ravi Kumar", "32", "1", "0"],
        ["2", "2", "Priya Singh", "29", "2", "0"],
        ["3", "3", "Deceased Person", "55", "1", "0"],
    ])


# ============================================================
# 5. Accused
# ============================================================
write_csv("Accused.csv",
    ["AccusedMasterID", "CaseMasterID", "AccusedName", "AgeYear", "GenderID", "PersonID"],
    [
        ["1", "1", "John Doe", "35", "1", "A1"],
        ["2", "1", "Jane Smith", "30", "2", "A2"],
        ["3", "2", "Rohit Verma", "28", "1", "A1"],
    ])


# ============================================================
# 6. ArrestSurrender
# ============================================================
write_csv("ArrestSurrender.csv",
    ["ArrestSurrenderID", "CaseMasterID", "ArrestSurrenderTypeID", "ArrestSurrenderDate",
     "ArrestSurrenderStateId", "ArrestSurrenderDistrictId", "PoliceStationID",
     "IOID", "CourtID", "AccusedMasterID", "IsAccused", "IsComplainantAccused"],
    [
        ["1", "1", "1", "2026-01-20", "1", "1", "1001", "101", "1", "1", "1", "0"],
        ["2", "2", "1", "2026-02-25", "1", "1", "1001", "102", "2", "3", "1", "0"],
    ])


# ============================================================
# 7. ChargesheetDetails
# ============================================================
write_csv("ChargesheetDetails.csv",
    ["CSID", "CaseMasterID", "csdate", "cstype", "PolicePersonID"],
    [
        ["1", "1", "2026-03-15", "A", "101"],
        ["2", "2", "2026-04-10", "A", "102"],
    ])


# ============================================================
# 8. Act
# ============================================================
write_csv("Act.csv",
    ["ActCode", "ActDescription", "ShortName", "Active"],
    [
        ["IPC", "Indian Penal Code", "IPC", "1"],
        ["NDPS", "Narcotic Drugs and Psychotropic Substances Act", "NDPS", "1"],
        ["CrPC", "Code of Criminal Procedure", "CrPC", "1"],
        ["KA_Police", "Karnataka Police Act", "KA Police Act", "1"],
    ])


# ============================================================
# 9. Section
# ============================================================
write_csv("Section.csv",
    ["ActCode", "SectionCode", "SectionDescription", "Active"],
    [
        ["IPC", "302", "Punishment for murder", "1"],
        ["IPC", "307", "Attempt to murder", "1"],
        ["IPC", "324", "Voluntarily causing hurt by dangerous weapons", "1"],
        ["IPC", "379", "Punishment for theft", "1"],
        ["IPC", "380", "Theft in dwelling house", "1"],
        ["IPC", "420", "Cheating and dishonestly inducing delivery of property", "1"],
        ["NDPS", "20", "Punishment for cultivation of cannabis plant", "1"],
        ["NDPS", "21", "Punishment for manufacture, possession of psychotropic substances", "1"],
    ])


# ============================================================
# 10. CrimeHeadActSection
# ============================================================
write_csv("CrimeHeadActSection.csv",
    ["CrimeHeadID", "ActCode", "SectionCode"],
    [
        ["1", "IPC", "302"],
        ["1", "IPC", "307"],
        ["2", "IPC", "324"],
        ["3", "IPC", "379"],
        ["3", "IPC", "380"],
    ])


# ============================================================
# 11. CrimeHead
# ============================================================
write_csv("CrimeHead.csv",
    ["CrimeHeadID", "CrimeGroupName", "Active"],
    [
        ["1", "Crimes Against Body", "1"],
        ["2", "Crimes Against Property", "1"],
        ["3", "Crimes Against Women", "1"],
        ["4", "Economic Offences", "1"],
        ["5", "Cyber Crimes", "1"],
    ])


# ============================================================
# 12. CrimeSubHead
# ============================================================
write_csv("CrimeSubHead.csv",
    ["CrimeSubHeadID", "CrimeHeadID", "CrimeHeadName", "SeqID"],
    [
        ["1", "1", "Murder", "1"],
        ["2", "1", "Attempt to Murder", "2"],
        ["3", "1", "Assault", "3"],
        ["4", "2", "Robbery", "1"],
        ["5", "2", "Burglary", "2"],
        ["6", "2", "Theft", "3"],
        ["7", "3", "Rape", "1"],
        ["8", "3", "Dowry Death", "2"],
    ])


# ============================================================
# 13. CaseCategory
# ============================================================
write_csv("CaseCategory.csv",
    ["CaseCategoryID", "LookupValue"],
    [
        ["1", "FIR"],
        ["2", "UDR"],
        ["3", "Zero FIR"],
        ["4", "PAR"],
    ])


# ============================================================
# 14. GravityOffence
# ============================================================
write_csv("GravityOffence.csv",
    ["GravityOffenceID", "LookupValue"],
    [
        ["1", "Heinous"],
        ["2", "Non-Heinous"],
        ["3", "Petty"],
    ])


# ============================================================
# 15. CaseStatusMaster
# ============================================================
write_csv("CaseStatusMaster.csv",
    ["CaseStatusID", "CaseStatusName"],
    [
        ["1", "Under Investigation"],
        ["2", "Charge Sheeted"],
        ["3", "Closed"],
        ["4", "Pending Trial"],
        ["5", "Transferred"],
    ])


# ============================================================
# 16. CasteMaster
# ============================================================
write_csv("CasteMaster.csv",
    ["caste_master_id", "caste_master_name"],
    [
        ["1", "General"],
        ["2", "OBC"],
        ["3", "SC"],
        ["4", "ST"],
    ])


# ============================================================
# 17. ReligionMaster
# ============================================================
write_csv("ReligionMaster.csv",
    ["ReligionID", "ReligionName"],
    [
        ["1", "Hindu"],
        ["2", "Muslim"],
        ["3", "Christian"],
        ["4", "Sikh"],
        ["5", "Jain"],
    ])


# ============================================================
# 18. OccupationMaster
# ============================================================
write_csv("OccupationMaster.csv",
    ["OccupationID", "OccupationName"],
    [
        ["1", "Government Employee"],
        ["2", "Private Employee"],
        ["3", "Farmer"],
        ["4", "Business"],
        ["5", "Student"],
        ["6", "Unemployed"],
    ])


# ============================================================
# 19. Court
# ============================================================
write_csv("Court.csv",
    ["CourtID", "CourtName", "DistrictID", "StateID", "Active"],
    [
        ["1", "City Civil Court Bangalore", "1", "1", "1"],
        ["2", "Sessions Court Bangalore", "1", "1", "1"],
        ["3", "High Court of Karnataka", "1", "1", "1"],
    ])


# ============================================================
# 20. District
# ============================================================
write_csv("District.csv",
    ["DistrictID", "DistrictName", "StateID", "Active"],
    [
        ["1", "Bengaluru Urban", "1", "1"],
        ["2", "Bengaluru Rural", "1", "1"],
        ["3", "Mysuru", "1", "1"],
        ["4", "Hubballi", "1", "1"],
        ["5", "Mangaluru", "1", "1"],
    ])


# ============================================================
# 21. State
# ============================================================
write_csv("State.csv",
    ["StateID", "StateName", "NationalityID", "Active"],
    [
        ["1", "Karnataka", "1", "1"],
        ["2", "Tamil Nadu", "1", "1"],
        ["3", "Kerala", "1", "1"],
        ["4", "Andhra Pradesh", "1", "1"],
    ])


# ============================================================
# 22. Unit (Police Station)
# ============================================================
write_csv("Unit.csv",
    ["UnitID", "UnitName", "TypeID", "ParentUnit", "NationalityID", "StateID", "DistrictID", "Active"],
    [
        ["1001", "MG Road Police Station", "1", "", "1", "1", "1", "1"],
        ["1002", "Indiranagar Police Station", "1", "", "1", "1", "1", "1"],
        ["1003", "Koramangala Police Station", "1", "", "1", "1", "1", "1"],
        ["1004", "Whitefield Police Station", "1", "", "1", "1", "1", "1"],
    ])


# ============================================================
# 23. UnitType
# ============================================================
write_csv("UnitType.csv",
    ["UnitTypeID", "UnitTypeName", "CityDistState", "Hierarchy", "Active"],
    [
        ["1", "Police Station", "City", "3", "1"],
        ["2", "Circle Office", "City", "2", "1"],
        ["3", "District Office", "District", "1", "1"],
    ])


# ============================================================
# 24. Rank
# ============================================================
write_csv("Rank.csv",
    ["RankID", "RankName", "Hierarchy", "Active"],
    [
        ["1", "Director General of Police", "1", "1"],
        ["2", "Inspector General", "2", "1"],
        ["3", "Superintendent of Police", "3", "1"],
        ["4", "Deputy Superintendent", "4", "1"],
        ["5", "Inspector", "5", "1"],
        ["6", "Sub-Inspector", "6", "1"],
        ["7", "Head Constable", "7", "1"],
        ["8", "Constable", "8", "1"],
    ])


# ============================================================
# 25. Designation
# ============================================================
write_csv("Designation.csv",
    ["DesignationID", "DesignationName", "Active", "SortOrder"],
    [
        ["1", "Station House Officer (SHO)", "1", "1"],
        ["2", "Investigating Officer", "1", "2"],
        ["3", "Circle Inspector", "1", "3"],
        ["4", "Sub-Inspector", "1", "4"],
        ["5", "Assistant Sub-Inspector", "1", "5"],
    ])


# ============================================================
# 26. Employee
# ============================================================
write_csv("Employee.csv",
    ["EmployeeID", "DistrictID", "UnitID", "RankID", "DesignationID",
     "KGID", "FirstName", "EmployeeDOB", "GenderID", "BloodGroupID",
     "PhysicallyChallenged", "AppointmentDate"],
    [
        ["101", "1", "1001", "5", "1", "KAR123456", "Rajesh Kumar", "1980-05-15", "1", "1", "0", "2005-06-01"],
        ["102", "1", "1001", "6", "2", "KAR123457", "Suresh Patel", "1985-08-22", "1", "2", "0", "2010-09-15"],
        ["103", "1", "1001", "6", "4", "KAR123458", "Anita Sharma", "1990-03-10", "2", "3", "0", "2015-01-20"],
        ["104", "1", "1002", "5", "1", "KAR123459", "Venkatesh Rao", "1982-11-30", "1", "1", "0", "2007-04-10"],
    ])


# ============================================================
# 27. Inv_OccuranceTime
# ============================================================
write_csv("Inv_OccuranceTime.csv",
    ["CaseMasterID", "IncidentFromDate", "IncidentToDate", "latitude", "longitude", "BriefFacts"],
    [
        ["1", "2026-01-14 20:00:00", "2026-01-14 22:00:00", "12.9716", "77.5946", "Theft incident at MG Road commercial area."],
        ["2", "2026-02-19 23:00:00", "2026-02-20 01:00:00", "12.9352", "77.6245", "Assault near Koramangala bus stop."],
        ["3", "2026-03-04 18:00:00", "2026-03-04 20:00:00", "12.9815", "77.6042", "Unnatural death reported in Indiranagar."],
    ])


# ============================================================
# 28. ChatContext
# ============================================================
write_csv("ChatContext.csv",
    ["SessionID", "UserID", "Message", "Response", "Timestamp"],
    [
        ["SESS001", "USER001", "Show me all theft cases in Bangalore", "Found 15 theft cases registered in Bangalore.", "2026-07-01 10:30:00"],
        ["SESS001", "USER001", "Which areas have highest crime?", "MG Road and Koramangala have highest reported incidents.", "2026-07-01 10:31:00"],
    ])


# ============================================================
# 29. Alert
# ============================================================
write_csv("Alert.csv",
    ["Title", "Message", "Severity", "Type", "Status", "AssignedTo", "CreatedDate", "ResolvedDate"],
    [
        ["High Crime Alert", "Theft incidents increased 20% in MG Road area", "High", "Crime Trend", "Active", "IO101", "2026-07-01 00:00:00", ""],
        ["Hotspot Alert", "Predicted burglary hotspot in Indiranagar", "Medium", "Prediction", "Active", "IO102", "2026-07-01 06:00:00", ""],
    ])


# ============================================================
# 30. Prediction
# ============================================================
write_csv("Prediction.csv",
    ["Title", "CrimeType", "Location", "Latitude", "Longitude", "Probability", "PredictedDate", "ModelVersion", "Status"],
    [
        ["Burglary Risk Zone", "Burglary", "Indiranagar", "12.9783", "77.6408", "0.85", "2026-07-15", "v1.0", "Active"],
        ["Theft Hotspot", "Theft", "MG Road", "12.9716", "77.5946", "0.78", "2026-07-20", "v1.0", "Active"],
    ])


# ============================================================
# 31. BehaviorProfile
# ============================================================
write_csv("BehaviorProfile.csv",
    ["SubjectName", "ProfileType", "MO", "RiskLevel", "Pattern", "Score", "Notes", "CreatedDate"],
    [
        ["John Doe", "Repeat Offender", "Theft during night hours in commercial areas", "High", "Night-time commercial theft", "85.5", "Known criminal with history of theft", "2026-07-01"],
    ])


# ============================================================
# 32. TimelineEvent
# ============================================================
write_csv("TimelineEvent.csv",
    ["CaseMasterID", "Title", "Description", "EventDate", "EventType", "Location", "CreatedBy"],
    [
        ["1", "FIR Registered", "FIR registered at MG Road Police Station", "2026-01-15 10:30:00", "Registration", "MG Road Police Station", "101"],
        ["1", "Investigation Started", "Case assigned to Investigating Officer", "2026-01-15 14:00:00", "Investigation", "MG Road Police Station", "101"],
        ["1", "Arrest Made", "Accused John Doe arrested", "2026-01-20 09:00:00", "Arrest", "Jayanagar", "101"],
        ["2", "FIR Registered", "Assault case registered at Koramangala", "2026-02-20 14:00:00", "Registration", "Koramangala Police Station", "102"],
    ])


print(f"\n✅ All 32 CSV files generated in: {DATA_DIR}")
print("\nTo import into Catalyst Data Store:")
print("  catalyst ds:import ./data/CasteMaster.csv --table CasteMaster")
print("  catalyst ds:import ./data/ReligionMaster.csv --table ReligionMaster")
print("  # ... repeat for each table")
