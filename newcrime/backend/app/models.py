"""Fresh crime-intelligence schema (my own design, not derived from prior files).

Tables cover: users/RBAC, FIR cases, accused, victims, officers, investigations,
case<->person links, associations (for network analysis), financial accounts &
transactions (money-trail analysis), timeline events, alerts, crime patterns,
predictions, offender behaviour profiles, and chat conversations/messages.
"""
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text,
)
from sqlalchemy.orm import relationship

from .database import Base


def _now() -> datetime:
    return datetime.utcnow()


# ── Access / users ───────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    full_name = Column(String(100))
    email = Column(String(120))
    # NOTE: plaintext demo password (local only). Real deploy must hash.
    password = Column(String(255), nullable=False)
    # role in: investigator | analyst | supervisor | policymaker | admin
    role = Column(String(30), default="investigator", index=True)
    badge_number = Column(String(30))
    district = Column(String(60))
    subdivision = Column(String(100))
    station = Column(String(100))
    range_name = Column(String(60))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_now)


# ── People ───────────────────────────────────────────────────────────
class Officer(Base):
    __tablename__ = "officers"
    id = Column(Integer, primary_key=True)
    badge_number = Column(String(50), unique=True, index=True)
    name = Column(String(100), nullable=False)
    rank = Column(String(50))
    posting_station = Column(String(100))
    district = Column(String(60), index=True)
    contact_number = Column(String(20))

    investigations = relationship("Investigation", back_populates="officer")


class Accused(Base):
    __tablename__ = "accused"
    id = Column(Integer, primary_key=True)
    full_name = Column(String(100), nullable=False, index=True)
    aliases = Column(String(255))
    gender = Column(String(10))
    age = Column(Integer)
    address = Column(Text)
    district = Column(String(60), index=True)
    phone_number = Column(String(20))
    # socio-demographic attributes for sociological insight
    occupation = Column(String(60))
    education = Column(String(40))
    socio_economic = Column(String(20))     # Low | Lower-Mid | Middle | Upper-Mid | High
    urban_rural = Column(String(10))         # Urban | Rural
    migrant = Column(Boolean, default=False)
    previous_convictions = Column(Integer, default=0)
    status = Column(String(50), default="Suspect")   # Suspect | Arrested | Chargesheeted | Convicted | Absconding
    created_at = Column(DateTime, default=_now)

    case_links = relationship("CaseAccused", back_populates="accused")
    profile = relationship("BehaviorProfile", back_populates="accused", uselist=False)
    accounts = relationship("FinancialAccount", back_populates="accused")


class Victim(Base):
    __tablename__ = "victims"
    id = Column(Integer, primary_key=True)
    full_name = Column(String(100), nullable=False)
    gender = Column(String(10))
    age = Column(Integer)
    contact_number = Column(String(20))
    address = Column(Text)
    district = Column(String(60), index=True)
    occupation = Column(String(60))
    statement_summary = Column(Text)
    created_at = Column(DateTime, default=_now)

    case_links = relationship("CaseVictim", back_populates="victim")


# ── Cases / FIRs ─────────────────────────────────────────────────────
class Case(Base):
    __tablename__ = "cases"
    id = Column(Integer, primary_key=True)
    fir_number = Column(String(50), unique=True, index=True)
    title = Column(String(150), nullable=False)
    description = Column(Text)
    crime_type = Column(String(50), index=True)
    crime_head = Column(String(50))            # broad head e.g. Property, Body, Financial
    modus_operandi = Column(String(120))
    status = Column(String(30), default="Open", index=True)  # Open | Under Investigation | Chargesheeted | Closed | Cold
    severity = Column(String(20), default="Medium")           # Low | Medium | High | Critical
    district = Column(String(60), index=True)
    station = Column(String(100))
    location_name = Column(String(255))
    latitude = Column(Float)
    longitude = Column(Float)
    is_financial = Column(Boolean, default=False)
    loss_amount = Column(Float, default=0.0)   # monetary loss (INR)
    occurrence_date = Column(DateTime, index=True)
    reported_date = Column(DateTime)
    created_at = Column(DateTime, default=_now)

    accused_links = relationship("CaseAccused", back_populates="case")
    victim_links = relationship("CaseVictim", back_populates="case")
    investigation = relationship("Investigation", back_populates="case", uselist=False)
    events = relationship("TimelineEvent", back_populates="case")


class CaseAccused(Base):
    __tablename__ = "case_accused"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.id"), index=True)
    accused_id = Column(Integer, ForeignKey("accused.id"), index=True)
    role_in_crime = Column(String(50))    # Main | Accomplice | Financier | Handler

    case = relationship("Case", back_populates="accused_links")
    accused = relationship("Accused", back_populates="case_links")


class CaseVictim(Base):
    __tablename__ = "case_victim"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.id"), index=True)
    victim_id = Column(Integer, ForeignKey("victims.id"), index=True)

    case = relationship("Case", back_populates="victim_links")
    victim = relationship("Victim", back_populates="case_links")


class Association(Base):
    """Explicit accused<->accused link for criminal-network analysis."""
    __tablename__ = "associations"
    id = Column(Integer, primary_key=True)
    source_accused_id = Column(Integer, ForeignKey("accused.id"), index=True)
    target_accused_id = Column(Integer, ForeignKey("accused.id"), index=True)
    relationship_type = Column(String(40))   # Gang | Family | Financial | Associate | Co-accused
    gang_name = Column(String(80))
    strength = Column(Float, default=1.0)    # weight


# ── Investigations / timeline ────────────────────────────────────────
class Investigation(Base):
    __tablename__ = "investigations"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.id"), unique=True, index=True)
    officer_id = Column(Integer, ForeignKey("officers.id"), index=True)
    summary = Column(Text)
    leads_details = Column(Text)
    status = Column(String(50), default="Active")   # Active | Pending | Solved | Cold
    progress = Column(Integer, default=0)           # 0..100 (derived from stage)
    current_stage = Column(String(50))              # one of investigation.STAGES
    created_at = Column(DateTime, default=_now)

    case = relationship("Case", back_populates="investigation")
    officer = relationship("Officer", back_populates="investigations")


class TimelineEvent(Base):
    __tablename__ = "timeline_events"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.id"), index=True)
    event_title = Column(String(120), nullable=False)
    description = Column(Text)
    event_type = Column(String(50))   # FIR | Arrest | Evidence | Statement | Chargesheet | Court
    event_timestamp = Column(DateTime, index=True)

    case = relationship("Case", back_populates="events")


# ── Financial-crime module ───────────────────────────────────────────
class FinancialAccount(Base):
    __tablename__ = "financial_accounts"
    id = Column(Integer, primary_key=True)
    account_number = Column(String(30), index=True)
    holder_name = Column(String(100))
    bank = Column(String(60))
    account_type = Column(String(20))   # Savings | Current | Wallet | Crypto
    accused_id = Column(Integer, ForeignKey("accused.id"), index=True, nullable=True)
    is_suspicious = Column(Boolean, default=False)

    accused = relationship("Accused", back_populates="accounts")


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    from_account_id = Column(Integer, ForeignKey("financial_accounts.id"), index=True)
    to_account_id = Column(Integer, ForeignKey("financial_accounts.id"), index=True)
    amount = Column(Float)
    currency = Column(String(10), default="INR")
    channel = Column(String(20))   # UPI | NEFT | IMPS | Cash | Crypto
    case_id = Column(Integer, ForeignKey("cases.id"), index=True, nullable=True)
    flagged = Column(Boolean, default=False)
    txn_timestamp = Column(DateTime, index=True)


# ── Analytics / AI artefacts ─────────────────────────────────────────
class CrimePattern(Base):
    __tablename__ = "crime_patterns"
    id = Column(Integer, primary_key=True)
    pattern_name = Column(String(120), nullable=False)
    description = Column(Text)
    crime_type = Column(String(50), index=True)
    district = Column(String(60))
    temporal_signature = Column(String(120))    # e.g. "Weekend nights", "Festival season"
    modus_operandi_tags = Column(String(255))
    hotspot_radius_meters = Column(Float, default=500.0)
    case_count = Column(Integer, default=0)


class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True)
    target_area = Column(String(100), index=True)
    crime_type = Column(String(50), index=True)
    probability = Column(Float)
    risk_level = Column(String(20))    # Low | Medium | High | Critical
    forecast_window_start = Column(DateTime)
    forecast_window_end = Column(DateTime)
    contributing_factors = Column(Text)
    created_at = Column(DateTime, default=_now)


class BehaviorProfile(Base):
    __tablename__ = "behavior_profiles"
    id = Column(Integer, primary_key=True)
    accused_id = Column(Integer, ForeignKey("accused.id"), unique=True, index=True)
    risk_score = Column(Float, default=0.0)      # 0..100
    risk_band = Column(String(20))               # Low | Medium | High | Critical
    is_habitual = Column(Boolean, default=False)
    behavioral_traits = Column(Text)
    propensity_tags = Column(Text)               # comma-separated crime types
    modus_operandi = Column(String(120))
    updated_at = Column(DateTime, default=_now)

    accused = relationship("Accused", back_populates="profile")


class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True)
    title = Column(String(120), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(20), default="Medium")   # Low | Medium | High | Critical
    alert_type = Column(String(50))   # Repeat-offender | Gang-activity | Hotspot | Financial | Emerging-pattern
    district = Column(String(60))
    is_read = Column(Boolean, default=False)
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_now, index=True)


# ── Conversational AI ────────────────────────────────────────────────
class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True)
    title = Column(String(200))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True, index=True)
    language = Column(String(5), default="en")   # en | kn
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now)

    messages = relationship(
        "Message", back_populates="conversation",
        cascade="all, delete-orphan", order_by="Message.created_at",
    )


class CaseNote(Base):
    """Investigation notebook entry (Phase 1)."""
    __tablename__ = "case_notes"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.id"), index=True)
    author_name = Column(String(100))
    author_role = Column(String(30))
    content = Column(Text, nullable=False)
    pinned = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_now)


class EvidenceDocument(Base):
    """Uploaded evidence / document attached to a case (Phase 1)."""
    __tablename__ = "evidence_documents"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.id"), index=True)
    category = Column(String(50))       # Evidence | FIR Documents | ... (see router)
    filename = Column(String(255))      # stored name on disk
    original_name = Column(String(255))
    mime = Column(String(100))
    size = Column(Integer, default=0)
    uploaded_by = Column(String(100))
    ai_summary = Column(Text)           # AI-generated summary (mock)
    remarks = Column(Text)
    created_at = Column(DateTime, default=_now)


class Witness(Base):
    """Witness recorded during investigation (Phase 1)."""
    __tablename__ = "witnesses"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.id"), index=True)
    name = Column(String(100), nullable=False)
    contact = Column(String(30))
    statement = Column(Text)
    reliability = Column(String(20), default="Medium")   # Low | Medium | High
    document_path = Column(String(255))
    document_name = Column(String(255))
    created_at = Column(DateTime, default=_now)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50))
    user_name = Column(String(100))
    role = Column(String(30))
    action = Column(String(10))        # HTTP method
    path = Column(String(255))
    resource = Column(String(80))      # human-readable module
    status_code = Column(Integer)
    pii_accessed = Column(Boolean, default=False)
    action_type = Column(String(50))   # view, create, update, delete, export, login, upload, approve, reject
    detail = Column(Text)              # human-readable description
    ip_address = Column(String(45))
    user_agent = Column(String(255))
    session_id = Column(String(100))
    district = Column(String(60))
    prev_value = Column(Text)
    new_value = Column(Text)
    created_at = Column(DateTime, default=_now, index=True)


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), index=True)
    role = Column(String(20))    # user | assistant
    content = Column(Text)
    language = Column(String(5), default="en")
    sql_text = Column(Text)      # generated query (explainability)
    evidence_json = Column(Text) # JSON evidence/reasoning trail
    grounding_json = Column(Text)  # JSON Claim-Ledger grounding summary
    reasoning_json = Column(Text)  # JSON reasoning-path steps
    intent = Column(String(50))
    created_at = Column(DateTime, default=_now)

    conversation = relationship("Conversation", back_populates="messages")


# ── Stage approvals / access requests (investigation workflow) ────────
class StageApproval(Base):
    """Tracks who approved/rejected stage changes."""
    __tablename__ = "stage_approvals"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.id"), index=True)
    stage = Column(String(50), nullable=False)
    action = Column(String(20))  # approved | rejected | requested
    requested_by = Column(String(100))
    requested_role = Column(String(30))
    approved_by = Column(String(100))
    approved_role = Column(String(30))
    comments = Column(Text)
    created_at = Column(DateTime, default=_now)


class AccessRequest(Base):
    """Tracks role access requests."""
    __tablename__ = "access_requests"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.id"), index=True)
    requested_by = Column(String(100))
    requested_role = Column(String(30))
    reason = Column(Text)
    status = Column(String(20), default="pending")  # pending | approved | rejected
    reviewed_by = Column(String(100))
    created_at = Column(DateTime, default=_now)
