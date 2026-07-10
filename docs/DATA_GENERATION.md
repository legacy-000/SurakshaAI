# DATA GENERATION PLAN — Suraksha AI

## Overview

Deterministic, configurable, schema-compliant synthetic data generator for the KSP FIR database (26 KSP tables + 31 prototype tables). Reuses and extends the existing `scripts/generate_seed_csvs.py` infrastructure.

## Generation Order (Dependency-Respecting)

| Order | Entity | Table | Records per Profile (S/M/L) | FK Dependencies | Type |
|-------|--------|-------|---------------------------|-----------------|------|
| 1 | UnitType | T023 | 3 / 3 / 3 | none | Master |
| 1 | Rank | T024 | 8 / 8 / 8 | none | Master |
| 1 | Designation | T025 | 6 / 6 / 6 | none | Master |
| 1 | CasteMaster | T013 | 8 / 8 / 8 | none | Master |
| 1 | ReligionMaster | T014 | 8 / 8 / 8 | none | Master |
| 1 | OccupationMaster | T015 | 18 / 18 / 18 | none | Master |
| 1 | CaseCategory | T016 | 4 / 4 / 4 | none | Master |
| 1 | GravityOffence | T017 | 3 / 3 / 3 | none | Master |
| 1 | CaseStatusMaster | T018 | 6 / 6 / 6 | none | Master |
| 1 | Act | T007 | 5 / 5 / 5 | none | Legal |
| 1 | State | T021 | 5 / 5 / 5 | none | Geo |
| 1 | CrimeHead | T010 | 6 / 6 / 6 | none | Classification |
| 2 | District | T020 | 5 / 10 / 15 | State | Geo |
| 2 | Section | T008 | 20 / 20 / 20 | Act | Legal |
| 2 | CrimeSubHead | T011 | 12 / 12 / 12 | CrimeHead | Classification |
| 2 | CrimeHeadActSection | T012 | 15 / 15 / 15 | CrimeHead, Act | Junction |
| 2 | Unit | T022 | 10 / 30 / 60 | UnitType, State, District | Geo |
| 2 | Court | T019 | 3 / 5 / 10 | District, State | Geo |
| 3 | Employee | T026 | 15 / 30 / 60 | District, Unit, Rank, Designation | Personnel |
| 4 | CaseMaster | T001 | 100 / 500 / 2000 | Employee, Unit, CaseCategory, GravityOffence, CrimeHead, CrimeSubHead, CaseStatus, Court | Core Transaction |
| 5 | ComplainantDetails | T002 | 250 / 1250 / 5000 | CaseMaster, Occupation, Religion, Caste | Person |
| 5 | Victim | T003 | 70 / 350 / 1400 | CaseMaster | Person |
| 5 | Accused | T004 | 160 / 800 / 3200 | CaseMaster | Person |
| 5 | ActSectionAssociation | T009 | 140 / 700 / 2800 | CaseMaster, Act, Section | Junction |
| 5 | Inv_OccuranceTime | inferred | 100 / 500 / 2000 | CaseMaster | Detail |
| 6 | ArrestSurrender | T005 | 100 / 500 / 2000 | CaseMaster, State, District, Unit, Employee, Court, Accused | Event |
| 6 | ChargesheetDetails | T006 | 50 / 250 / 1000 | CaseMaster, Employee | Event |
| 7 | TimelineEvent | PT011-A | 400 / 2000 / 8000 | CaseMaster | Event |
| 7 | BehaviorProfile | supp | 8 / 20 / 40 | none | AI |
| 7 | CrimePattern | supp | 10 / 10 / 10 | none | AI |
| 7 | Alert | supp | 10 / 20 / 40 | none | AI |
| 7 | Prediction | supp | 12 / 25 / 50 | none | AI |
| 7 | ChatContext | supp | 15 / 30 / 60 | none | AI |

## Embedded Patterns

### P1 Seasonal Variation
- **Theft**: elevated Oct–Jan (festival season), lower Feb–Apr. Factor: 1.0–2.5x
- **Assault**: elevated Fri–Sat nights. Weekend factor: 1.8x
- **Burglary**: elevated Mon–Fri 09:00–17:00 (work hours). Factor: 1.5x
- **Cyber fraud**: steady year-round, slight peak in tax season (Mar–Apr)

### P2 Hour-of-Day Patterns
- **Theft/vehicle theft**: peak 22:00–04:00 (night)
- **Assault/robbery**: peak 20:00–02:00 (evening/night)
- **Burglary**: peak 09:00–17:00 (daytime, unoccupied homes)
- **Cyber fraud**: peak 10:00–18:00 (business hours)

### P3 Crime Hotspots (geographic clusters)
- **Cluster A** Bangalore Urban: MG Road, Koramangala, Indiranagar — concentrated within 5km radius
- **Cluster B** Mysuru: Mysuru City PS area — moderate density
- **Cluster C** Hubli: Hubli City PS area — moderate density

### P4 Repeat Offenders (5 named individuals)
| Name | Cases | Districts | MO Pattern |
|------|-------|-----------|------------|
| Ravi Kumar | 8 | Bengaluru Urban + Rural | Night theft in commercial areas |
| Suresh P | 5 | Bengaluru Urban + Mysuru | Vehicle theft / chain snatching |
| Rajesh K | 4 | Bengaluru Urban | Burglary in apartments |
| Manoj R | 3 | Mysuru + Hubli | Assault in pub areas |
| Venkatesh G | 3 | Bengaluru Urban + Rural | Cyber fraud / phishing |

### P5 Co-accused Networks
- Ravi Kumar ↔ Suresh P (2 shared cases)
- Suresh P ↔ Manoj R (1 shared case)
- Rajesh K ↔ Venkatesh G (1 shared case)

### P6 Crime-Category Correlations
- Theft + Vehicle theft: 40% co-occurrence in same area
- Assault + Robbery: 25% co-occurrence
- Drug possession + Theft: 15% co-occurrence

### P7 Trend Patterns
- **Bengaluru Urban**: rising trend (+2.5% month-over-month)
- **Mysuru**: stable (±0.5%)
- **Hubli**: declining (-1.2% month-over-month)

### P8 Missing & Quality Issues (per DQ register)
| DQ ID | Issue | Rate | Affected Table |
|-------|-------|------|----------------|
| DQ-01 | Missing GPS | 20% of cases | CaseMaster.latitude/longitude = NULL |
| DQ-02 | Duplicate accused names | 5 name variants | Accused → 3 AccusedMasterID with identical name |
| DQ-03 | Inconsistent name spellings | 3 pairs | Accused: "Ravikumar" vs "Ravi Kumar" vs "Ravi K" |
| DQ-04 | Kannada/English variants | 2 names | "Mohammed Ali" ↔ "Muhammad Ali" |
| DQ-05 | Missing age | 10% of persons | AgeYear = NULL |
| DQ-06 | Invalid coordinates | 3% of GPS | lat/lng outside Karnataka bounding box |
| DQ-07 | Inconsistent gender | 2% | GenderID = 3 (Other/Unknown) |
| DQ-11 | Incomplete chargesheets | 10% of pending | cstype = NULL |

## Configuration

```python
seed = 42           # deterministic reproducibility
profile = "MEDIUM"  # SMALL | MEDIUM | LARGE
output_dir = "data/" # CSV output directory
cases = 500         # overridden by profile
```

## Dataset Size Profiles

| Metric | SMALL | MEDIUM | LARGE |
|--------|-------|--------|-------|
| Cases | 100 | 500 | 2,000 |
| Districts | 5 | 10 | 15 |
| Stations | 10 | 30 | 60 |
| Employees | 15 | 30 | 60 |
| Total rows | ~1,200 | ~5,500 | ~22,000 |
| Generation time | ~2s | ~10s | ~40s |
| Use case | Unit tests | Demo | Performance |

## Validation Checks

After generation, validate:
1. Record counts match expected ranges
2. No NULL in PK columns
3. Every FK value references an existing PK
4. No duplicate PKs within a table
5. Every enum value is within valid range
6. Arrest dates are after crime dates
7. Chargesheet dates are after arrest dates
8. GPS coords within Karnataka bounding box (when not DQ-06)
9. Repeat offender names appear in expected count
10. Hotspot clusters have >=5 cases within radius

## Output Files

One CSV per table in the configured `output_dir`:
`{TableName}.csv` with headers matching the column names in schema_ksp.sql / schema_prototype.sql.

## Usage

```bash
# SMALL profile, default output
python database/data_generator.py --profile SMALL

# MEDIUM with custom seed and output
python database/data_generator.py --profile MEDIUM --seed 123 --output data/

# LARGE for performance testing
python database/data_generator.py --profile LARGE --seed 42

# Generate CSVs only (no DB insert)
python database/data_generator.py --profile MEDIUM --csv-only

# Validate without generating
python database/data_generator.py --validate-only --input data/

# Seed Catalyst Data Store from CSVs
python database/data_generator.py --seed-datastore --input data/
```
