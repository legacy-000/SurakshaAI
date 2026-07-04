# SurakshaAI — Catalyst Data Store Schema
## Source: Police FIR System ER Diagram — Karnataka Police Department

**Total: 28 core tables** (26 explicitly defined + 2 inferred from Relationship Matrix)

---

## PHASE 1: Lookup/Master Tables (create first — no FK dependencies)

### 1. CasteMaster
| Column | Type | Key | Max Len |
|--------|------|-----|---------|
| caste_master_id | Integer | PK | — |
| caste_master_name | Var Char | — | 100 |

### 2. ReligionMaster
| Column | Type | Key | Max Len |
|--------|------|-----|---------|
| ReligionID | Integer | PK | — |
| ReligionName | Var Char | — | 100 |

### 3. OccupationMaster
| Column | Type | Key | Max Len |
|--------|------|-----|---------|
| OccupationID | Integer | PK | — |
| OccupationName | Var Char | — | 200 |

### 4. CaseCategory
| Column | Type | Key | Max Len |
|--------|------|-----|---------|
| CaseCategoryID | Integer | PK | — |
| LookupValue | Var Char | — | 100 |

### 5. GravityOffence
| Column | Type | Key | Max Len |
|--------|------|-----|---------|
| GravityOffenceID | Integer | PK | — |
| LookupValue | Var Char | — | 200 |

### 6. CaseStatusMaster
| Column | Type | Key | Max Len |
|--------|------|-----|---------|
| CaseStatusID | Integer | PK | — |
| CaseStatusName | Var Char | — | 200 |

### 7. UnitType
| Column | Type | Key | Max Len |
|--------|------|-----|---------|
| UnitTypeID | Integer | PK | — |
| UnitTypeName | Var Char | — | 200 |
| CityDistState | Var Char | — | 50 |
| Hierarchy | Integer | — | — |
| Active | Boolean | — | — |

### 8. Rank
| Column | Type | Key | Max Len |
|--------|------|-----|---------|
| RankID | Integer | PK | — |
| RankName | Var Char | — | 100 |
| Hierarchy | Integer | — | — |
| Active | Boolean | — | — |

### 9. Designation
| Column | Type | Key | Max Len |
|--------|------|-----|---------|
| DesignationID | Integer | PK | — |
| DesignationName | Var Char | — | 200 |
| Active | Boolean | — | — |
| SortOrder | Integer | — | — |

---

## PHASE 2: Geography & Organization

### 10. State
| Column | Type | Key | Max Len |
|--------|------|-----|---------|
| StateID | Integer | PK | — |
| StateName | Var Char | — | 200 |
| NationalityID | Integer | — | — |
| Active | Boolean | — | — |

### 11. District
| Column | Type | Key | Max Len |
|--------|------|-----|---------|
| DistrictID | Integer | PK | — |
| DistrictName | Var Char | — | 200 |
| StateID | Integer | FK | — |
| Active | Boolean | — | — |

### 12. Court
| Column | Type | Key | Max Len |
|--------|------|-----|---------|
| CourtID | Integer | PK | — |
| CourtName | Var Char | — | 200 |
| DistrictID | Integer | FK | — |
| StateID | Integer | FK | — |
| Active | Boolean | — | — |

### 13. Unit (Police Station)
| Column | Type | Key | Max Len |
|--------|------|-----|---------|
| UnitID | Integer | PK | — |
| UnitName | Var Char | — | 200 |
| TypeID | Integer | FK | — |
| ParentUnit | Integer | — | — |
| NationalityID | Integer | — | — |
| StateID | Integer | FK | — |
| DistrictID | Integer | FK | — |
| Active | Boolean | — | — |

### 14. Employee
| Column | Type | Key | Max Len |
|--------|------|-----|---------|
| EmployeeID | Integer | PK | — |
| DistrictID | Integer | FK | — |
| UnitID | Integer | FK | — |
| RankID | Integer | FK | — |
| DesignationID | Integer | FK | — |
| KGID | Var Char | — | 50 |
| FirstName | Var Char | — | 100 |
| EmployeeDOB | Date Time | — | — |
| GenderID | Integer | — | — |
| BloodGroupID | Integer | — | — |
| PhysicallyChallenged | Boolean | — | — |
| AppointmentDate | Date Time | — | — |

---

## PHASE 3: Legal Reference Tables

### 15. Act
| Column | Type | Key | Max Len |
|--------|------|-----|---------|
| ActCode | Var Char | PK | 50 |
| ActDescription | Var Char | — | 500 |
| ShortName | Var Char | — | 100 |
| Active | Boolean | — | — |

### 16. Section
| Column | Type | Key | Max Len |
|--------|------|-----|---------|
| ActCode | Var Char | FK | 50 |
| SectionCode | Var Char | PK | 50 |
| SectionDescription | Var Char | — | 500 |
| Active | Boolean | — | — |

### 17. CrimeHead
| Column | Type | Key | Max Len |
|--------|------|-----|---------|
| CrimeHeadID | Integer | PK | — |
| CrimeGroupName | Var Char | — | 200 |
| Active | Boolean | — | — |

### 18. CrimeSubHead
| Column | Type | Key | Max Len |
|--------|------|-----|---------|
| CrimeSubHeadID | Integer | PK | — |
| CrimeHeadID | Integer | FK | — |
| CrimeHeadName | Var Char | — | 200 |
| SeqID | Integer | — | — |

### 19. CrimeHeadActSection (Junction)
| Column | Type | Key | Max Len |
|--------|------|-----|---------|
| CrimeHeadID | Integer | FK | — |
| ActCode | Var Char | FK | 50 |
| SectionCode | Var Char | — | 50 |

---

## PHASE 4: Core Transactional Tables

### 20. CaseMaster (Central Table)
| Column | Type | Key | Max Len |
|--------|------|-----|---------|
| CaseMasterID | Integer | PK | — |
| CrimeNo | Var Char | — | — |
| CaseNo | Var Char | — | — |
| CrimeRegisteredDate | Date Time | — | — |
| PolicePersonID | Integer | FK | — |
| PoliceStationID | Integer | FK | — |
| CaseCategoryID | Integer | FK | — |
| GravityOffenceID | Integer | FK | — |
| CrimeMajorHeadID | Integer | FK | — |
| CrimeMinorHeadID | Integer | FK | — |
| CaseStatusID | Integer | FK | — |
| CourtID | Integer | FK | — |
| IncidentFromDate | Date Time | — | — |
| IncidentToDate | Date Time | — | — |
| InfoReceivedPSDate | Date Time | — | — |
| Latitude | Decimal | — | — |
| Longitude | Decimal | — | — |
| BriefFacts | Text | — | — |

### 21. ComplainantDetails
| Column | Type | Key | Max Len |
|--------|------|-----|---------|
| ComplainantID | Integer | PK | — |
| CaseMasterID | Integer | FK | — |
| ComplainantName | Var Char | — | 200 |
| AgeYear | Integer | — | — |
| OccupationID | Integer | FK | — |
| ReligionID | Integer | FK | — |
| CasteID | Integer | FK | — |
| GenderID | Integer | — | — |

### 22. Victim
| Column | Type | Key | Max Len |
|--------|------|-----|---------|
| VictimMasterID | Integer | PK | — |
| CaseMasterID | Integer | FK | — |
| VictimName | Var Char | — | 200 |
| AgeYear | Integer | — | — |
| GenderID | Integer | — | — |
| VictimPolice | Var Char | — | 10 |

### 23. Accused
| Column | Type | Key | Max Len |
|--------|------|-----|---------|
| AccusedMasterID | Integer | PK | — |
| CaseMasterID | Integer | FK | — |
| AccusedName | Var Char | — | 200 |
| AgeYear | Integer | — | — |
| GenderID | Integer | — | — |
| PersonID | Var Char | — | 20 |

### 24. ActSectionAssociation
| Column | Type | Key | Max Len |
|--------|------|-----|---------|
| CaseMasterID | Integer | FK | — |
| ActID | Var Char | FK | 50 |
| SectionID | Var Char | FK | 50 |
| ActOrderID | Integer | — | — |
| SectionOrderID | Integer | — | — |

### 25. ArrestSurrender
| Column | Type | Key | Max Len |
|--------|------|-----|---------|
| ArrestSurrenderID | Integer | PK | — |
| CaseMasterID | Integer | FK | — |
| ArrestSurrenderTypeID | Integer | — | — |
| ArrestSurrenderDate | Date Time | — | — |
| ArrestSurrenderStateId | Integer | FK | — |
| ArrestSurrenderDistrictId | Integer | FK | — |
| PoliceStationID | Integer | FK | — |
| IOID | Integer | FK | — |
| CourtID | Integer | FK | — |
| AccusedMasterID | Integer | FK | — |
| IsAccused | Boolean | — | — |
| IsComplainantAccused | Boolean | — | — |

### 26. ChargesheetDetails
| Column | Type | Key | Max Len |
|--------|------|-----|---------|
| CSID | Integer | PK | — |
| CaseMasterID | Integer | FK | — |
| csdate | Date Time | — | — |
| cstype | Var Char | — | 10 |
| PolicePersonID | Integer | FK | — |

---

## INFERRED TABLES (from Relationship Matrix — no column list in PDF)

### 27. Inv_OccuranceTime
*Relationship: 1:1 with CaseMaster. Stores incident occurrence details.*
| Column | Type | Key | Max Len |
|--------|------|-----|---------|
| CaseMasterID | Integer | PK/FK | — |
| IncidentFromDate | Date Time | — | — |
| IncidentToDate | Date Time | — | — |
| latitude | Decimal | — | — |
| longitude | Decimal | — | — |
| location_description | Var Char | — | 500 |

### 28. inv_arrestsurrenderaccused
*Junction table for many-to-many between ArrestSurrender ↔ Accused.*
| Column | Type | Key | Max Len |
|--------|------|-----|---------|
| ArrestSurrenderID | Integer | FK | — |
| AccusedMasterID | Integer | FK | — |

---

## SUPPLEMENTAL TABLES (SurakshaAI-specific, not in ER Diagram)

These are optional AI/analytics tables for the SurakshaAI platform features:

### 29. CrimePattern
*AI crime pattern analysis — stores identified crime patterns for hotspots, temporal analysis, and MO clustering.*
| Column | Type | Key | Max Len |
|--------|------|-----|---------|
| ROWID | — | PK | — |
| pattern_name | Var Char | — | 100 |
| description | Text | — | — |
| crime_type | Var Char | — | 50 |
| hotspot_radius_meters | Decimal | — | — |
| temporal_signature | Var Char | — | 100 |
| modus_operandi_tags | Var Char | — | 255 |
| Created_Time | Date Time | — | — |
| Modified_Time | Date Time | — | — |

### 30. Alert
*System-generated alerts for crime trends, anomalies, and notifications.*
### 31. Prediction
*AI crime predictions for forecasting and risk assessment.*
### 32. ChatContext
*AI chat conversation storage for the NL2SQL assistant.*
### 33. BehaviorProfile
*AI behavioral profiling for suspect/victim analysis.*
### 34. TimelineEvent
*Case timeline events for visualization.*

---

## IMPORT ORDER (Catalyst CLI)

```bash
# Phase 1 — Lookups
catalyst ds:import ./data/CasteMaster.csv --table CasteMaster
catalyst ds:import ./data/ReligionMaster.csv --table ReligionMaster
catalyst ds:import ./data/OccupationMaster.csv --table OccupationMaster
catalyst ds:import ./data/CaseCategory.csv --table CaseCategory
catalyst ds:import ./data/GravityOffence.csv --table GravityOffence
catalyst ds:import ./data/CaseStatusMaster.csv --table CaseStatusMaster
catalyst ds:import ./data/UnitType.csv --table UnitType
catalyst ds:import ./data/Rank.csv --table Rank
catalyst ds:import ./data/Designation.csv --table Designation

# Phase 2 — Geography & Organization
catalyst ds:import ./data/State.csv --table State
catalyst ds:import ./data/District.csv --table District
catalyst ds:import ./data/Court.csv --table Court
catalyst ds:import ./data/Unit.csv --table Unit
catalyst ds:import ./data/Employee.csv --table Employee

# Phase 3 — Legal References
catalyst ds:import ./data/Act.csv --table Act
catalyst ds:import ./data/Section.csv --table Section
catalyst ds:import ./data/CrimeHead.csv --table CrimeHead
catalyst ds:import ./data/CrimeSubHead.csv --table CrimeSubHead
catalyst ds:import ./data/CrimeHeadActSection.csv --table CrimeHeadActSection

# Phase 4 — Core Transactional
catalyst ds:import ./data/CaseMaster.csv --table CaseMaster
catalyst ds:import ./data/ComplainantDetails.csv --table ComplainantDetails
catalyst ds:import ./data/Victim.csv --table Victim
catalyst ds:import ./data/Accused.csv --table Accused
catalyst ds:import ./data/ActSectionAssociation.csv --table ActSectionAssociation
catalyst ds:import ./data/ArrestSurrender.csv --table ArrestSurrender
catalyst ds:import ./data/ChargesheetDetails.csv --table ChargesheetDetails
catalyst ds:import ./data/Inv_OccuranceTime.csv --table Inv_OccuranceTime
catalyst ds:import ./data/inv_arrestsurrenderaccused.csv --table inv_arrestsurrenderaccused

# Phase 5 — Supplemental AI Tables
catalyst ds:import ./data/CrimePattern.csv --table CrimePattern
catalyst ds:import ./data/Alert.csv --table Alert
catalyst ds:import ./data/Prediction.csv --table Prediction
catalyst ds:import ./data/ChatContext.csv --table ChatContext
catalyst ds:import ./data/BehaviorProfile.csv --table BehaviorProfile
catalyst ds:import ./data/TimelineEvent.csv --table TimelineEvent
```
