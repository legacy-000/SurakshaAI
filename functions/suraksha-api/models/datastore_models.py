"""
Catalyst Data Store models for SurakshaAI.
Core schema matches the official Karnataka Police FIR System ER Diagram (26 defined + 2 inferred tables).
Plus supplemental AI/analytics tables for the SurakshaAI platform.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime

from configuration.database import datastore_config


class CatalystDataStoreModel:
    """Base class for Catalyst Data Store backed models."""

    def __init__(self, table_name: str):
        self.table_name = table_name
        self._config = datastore_config

    def create(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        row = self._config.insert_row(self.table_name, data)
        if row is None:
            data["ROWID"] = f"mock_{datetime.now().timestamp()}"
            data["Created_Time"] = datetime.now().isoformat()
            return data
        return row

    def get(self, row_id: str) -> Optional[Dict[str, Any]]:
        return self._config.get_row(self.table_name, row_id)

    def update(self, row_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        row = self._config.update_row(self.table_name, row_id, data)
        if row is None:
            data["ROWID"] = row_id
            data["Modified_Time"] = datetime.now().isoformat()
            return data
        return row

    def delete(self, row_id: str) -> bool:
        return self._config.delete_row(self.table_name, row_id)

    def get_all(self, criteria: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        return self._config.get_rows(self.table_name, criteria)


# ============================================================
# CORE TABLES (Police FIR ER Diagram — 28 tables)
# ============================================================

# --- Core Transactional Tables (7) ---

class CaseMaster(CatalystDataStoreModel):
    """Master FIR/Case table. Central entity — links to all other tables."""
    def __init__(self):
        super().__init__("CaseMaster")


class ComplainantDetails(CatalystDataStoreModel):
    """Complainant information linked to a case."""
    def __init__(self):
        super().__init__("ComplainantDetails")


class ActSectionAssociation(CatalystDataStoreModel):
    """Links legal acts and sections invoked in a case."""
    def __init__(self):
        super().__init__("ActSectionAssociation")


class Victim(CatalystDataStoreModel):
    """Victim(s) linked to a case."""
    def __init__(self):
        super().__init__("Victim")


class Accused(CatalystDataStoreModel):
    """Accused person(s) linked to a case."""
    def __init__(self):
        super().__init__("Accused")


class ArrestSurrender(CatalystDataStoreModel):
    """Arrest or surrender events linked to a case and accused."""
    def __init__(self):
        super().__init__("ArrestSurrender")


class ChargesheetDetails(CatalystDataStoreModel):
    """Chargesheet submission details for a case."""
    def __init__(self):
        super().__init__("ChargesheetDetails")


# --- Inferred Tables (2 — referenced in Relationship Matrix but not defined) ---

class InvOccuranceTime(CatalystDataStoreModel):
    """
    Occurrence time and location of the incident.
    Inferred table — 1:1 relationship with CaseMaster (per Relationship Matrix).
    Likely columns: CaseMasterID (PK/FK), IncidentFromDate, IncidentToDate,
    InfoReceivedPSDate, latitude, longitude, location_description.
    """
    def __init__(self):
        super().__init__("Inv_OccuranceTime")


class InvArrestSurrenderAccused(CatalystDataStoreModel):
    """
    Junction table linking ArrestSurrender to Accused (many-to-many).
    Inferred table — referenced in Relationship Matrix as 'inv_arrestsurrenderaccused'.
    One arrest event can link multiple accused persons.
    Likely columns: ID (PK), ArrestSurrenderID (FK), AccusedMasterID (FK).
    """
    def __init__(self):
        super().__init__("inv_arrestsurrenderaccused")


# --- Legal/Classification Tables (6) ---

class Act(CatalystDataStoreModel):
    """Legal acts (IPC, NDPS, CrPC, etc.)."""
    def __init__(self):
        super().__init__("Act")


class Section(CatalystDataStoreModel):
    """Sections within a legal act (302, 307, 379, etc.)."""
    def __init__(self):
        super().__init__("Section")


class CrimeHeadActSection(CatalystDataStoreModel):
    """Junction table: CrimeHead ↔ Act + Section mapping."""
    def __init__(self):
        super().__init__("CrimeHeadActSection")


class CrimeHead(CatalystDataStoreModel):
    """Major crime head classification (Crimes Against Body, Property, etc.)."""
    def __init__(self):
        super().__init__("CrimeHead")


class CrimeSubHead(CatalystDataStoreModel):
    """Minor crime sub-head classification (Murder, Robbery, Theft, etc.)."""
    def __init__(self):
        super().__init__("CrimeSubHead")


class CaseCategory(CatalystDataStoreModel):
    """Case category lookup (FIR, UDR, Zero FIR, PAR)."""
    def __init__(self):
        super().__init__("CaseCategory")


# --- Lookup/Master Tables (7) ---

class CasteMaster(CatalystDataStoreModel):
    """Caste lookup table."""
    def __init__(self):
        super().__init__("CasteMaster")


class ReligionMaster(CatalystDataStoreModel):
    """Religion lookup table."""
    def __init__(self):
        super().__init__("ReligionMaster")


class OccupationMaster(CatalystDataStoreModel):
    """Occupation lookup table."""
    def __init__(self):
        super().__init__("OccupationMaster")


class CaseStatusMaster(CatalystDataStoreModel):
    """Case status lookup (Under Investigation, Charge Sheeted, Closed, etc.)."""
    def __init__(self):
        super().__init__("CaseStatusMaster")


class GravityOffence(CatalystDataStoreModel):
    """Gravity level of offence (Heinous, Non-Heinous, Petty)."""
    def __init__(self):
        super().__init__("GravityOffence")


class Rank(CatalystDataStoreModel):
    """Police rank hierarchy (Constable, Inspector, DSP, etc.)."""
    def __init__(self):
        super().__init__("Rank")


class Designation(CatalystDataStoreModel):
    """Police designation (SHO, Investigating Officer, etc.)."""
    def __init__(self):
        super().__init__("Designation")


# --- Geo/Organizational Tables (6) ---

class Court(CatalystDataStoreModel):
    """Court information."""
    def __init__(self):
        super().__init__("Court")


class District(CatalystDataStoreModel):
    """District information."""
    def __init__(self):
        super().__init__("District")


class State(CatalystDataStoreModel):
    """State information."""
    def __init__(self):
        super().__init__("State")


class Unit(CatalystDataStoreModel):
    """Police station / unit."""
    def __init__(self):
        super().__init__("Unit")


class UnitType(CatalystDataStoreModel):
    """Type of police unit (Police Station, Circle Office, District Office)."""
    def __init__(self):
        super().__init__("UnitType")


class Employee(CatalystDataStoreModel):
    """Police employee records."""
    def __init__(self):
        super().__init__("Employee")


# ============================================================
# SUPPLEMENTAL TABLES (SurakshaAI AI/Analytics — not in ER Diagram)
# ============================================================

class CrimePattern(CatalystDataStoreModel):
    """AI-generated crime pattern analysis (SurakshaAI supplemental)."""
    def __init__(self):
        super().__init__("CrimePattern")


class Alert(CatalystDataStoreModel):
    """System-generated alerts (SurakshaAI supplemental)."""
    def __init__(self):
        super().__init__("Alert")


class Prediction(CatalystDataStoreModel):
    """AI crime predictions (SurakshaAI supplemental)."""
    def __init__(self):
        super().__init__("Prediction")


class ChatContext(CatalystDataStoreModel):
    """AI chat conversation storage (SurakshaAI supplemental)."""
    def __init__(self):
        super().__init__("ChatContext")


class BehaviorProfile(CatalystDataStoreModel):
    """AI behavioral profiling (SurakshaAI supplemental)."""
    def __init__(self):
        super().__init__("BehaviorProfile")


class TimelineEvent(CatalystDataStoreModel):
    """Case timeline events for visualization (SurakshaAI supplemental)."""
    def __init__(self):
        super().__init__("TimelineEvent")
