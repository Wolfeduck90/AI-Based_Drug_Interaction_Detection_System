"""
SQLAlchemy database models
"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, Float, 
    ForeignKey, JSON, Enum as SQLEnum, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.core.database import Base

class UserRole(str, enum.Enum):
    USER = "user"
    DOCTOR = "doctor"
    PHARMACIST = "pharmacist"
    ADMIN = "admin"

class SeverityLevel(str, enum.Enum):
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CRITICAL = "critical"

class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    emergency_contact = Column(String(500), nullable=True)
    allergies = Column(JSON, nullable=True)  # List of allergies
    medical_conditions = Column(JSON, nullable=True)  # List of conditions
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    medications = relationship("Medication", back_populates="user", cascade="all, delete-orphan")
    scans = relationship("PrescriptionScan", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("InteractionAlert", back_populates="user", cascade="all, delete-orphan")

class Drug(Base):
    """Drug reference model"""
    __tablename__ = "drugs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    generic_name = Column(String(255), nullable=True, index=True)
    brand_names = Column(JSON, nullable=True)  # List of brand names
    ndc_numbers = Column(JSON, nullable=True)  # List of NDC numbers
    rxcui = Column(String(50), nullable=True, index=True)  # RxNorm identifier
    drug_class = Column(String(100), nullable=True, index=True)
    active_ingredients = Column(JSON, nullable=True)
    contraindications = Column(Text, nullable=True)
    side_effects = Column(JSON, nullable=True)
    dosage_forms = Column(JSON, nullable=True)  # tablet, capsule, etc.
    strength_options = Column(JSON, nullable=True)  # Available strengths
    fda_approval_date = Column(DateTime, nullable=True)
    manufacturer = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    medications = relationship("Medication", back_populates="drug")
    
    # Indexes
    __table_args__ = (
        Index('ix_drugs_search', 'name', 'generic_name'),
    )

class DrugInteraction(Base):
    """Drug interaction reference model"""
    __tablename__ = "drug_interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    drug1_id = Column(Integer, ForeignKey("drugs.id"), nullable=False)
    drug2_id = Column(Integer, ForeignKey("drugs.id"), nullable=False)
    severity = Column(SQLEnum(SeverityLevel), nullable=False, index=True)
    interaction_type = Column(String(50), nullable=True)  # pharmacokinetic, pharmacodynamic
    mechanism = Column(Text, nullable=True)
    clinical_effect = Column(Text, nullable=False)
    management = Column(Text, nullable=True)
    evidence_level = Column(String(20), nullable=True)  # established, probable, theoretical
    frequency = Column(String(20), nullable=True)
    onset = Column(String(20), nullable=True)  # rapid, delayed
    documentation = Column(String(20), nullable=True)  # excellent, good, fair, poor
    source = Column(String(100), nullable=True)
    source_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    drug1 = relationship("Drug", foreign_keys=[drug1_id])
    drug2 = relationship("Drug", foreign_keys=[drug2_id])
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('drug1_id', 'drug2_id', name='uq_drug_interaction_pair'),
        Index('ix_drug_interactions_severity', 'severity'),
    )

class Medication(Base):
    """User medication model"""
    __tablename__ = "medications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    drug_id = Column(Integer, ForeignKey("drugs.id"), nullable=True)
    custom_name = Column(String(255), nullable=True)  # For non-standard entries
    dosage = Column(String(100), nullable=True)
    frequency = Column(String(100), nullable=True)
    route = Column(String(50), nullable=True)  # oral, topical, injection
    prescriber = Column(String(255), nullable=True)
    pharmacy = Column(String(255), nullable=True)
    prescription_date = Column(DateTime, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="medications")
    drug = relationship("Drug", back_populates="medications")
    
    # Indexes
    __table_args__ = (
        Index('ix_medications_user_active', 'user_id', 'is_active'),
    )

class PrescriptionScan(Base):
    """Prescription scan history model"""
    __tablename__ = "prescription_scans"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    image_path = Column(String(500), nullable=True)
    image_url = Column(String(500), nullable=True)
    extracted_text = Column(Text, nullable=True)
    extracted_data = Column(JSON, nullable=True)  # Structured medication data
    confidence_score = Column(Float, nullable=True)
    processing_status = Column(SQLEnum(ProcessingStatus), default=ProcessingStatus.PENDING)
    processing_time_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    medications_detected = Column(JSON, nullable=True)  # List of detected medications
    interactions_found = Column(Integer, default=0)
    risk_level = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="scans")
    
    # Indexes
    __table_args__ = (
        Index('ix_scans_user_date', 'user_id', 'created_at'),
    )

class InteractionAlert(Base):
    """Drug interaction alert model"""
    __tablename__ = "interaction_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    interaction_id = Column(Integer, ForeignKey("drug_interactions.id"), nullable=True)
    medication_ids = Column(JSON, nullable=True)  # List of medication IDs involved
    severity = Column(SQLEnum(SeverityLevel), nullable=False, index=True)
    alert_type = Column(String(50), nullable=False)  # interaction, allergy, contraindication
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    recommendations = Column(JSON, nullable=True)  # List of recommendations
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime, nullable=True)
    is_dismissed = Column(Boolean, default=False)
    dismissed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="alerts")
    interaction = relationship("DrugInteraction")
    
    # Indexes
    __table_args__ = (
        Index('ix_alerts_user_active', 'user_id', 'is_acknowledged', 'is_dismissed'),
    )

class AuditLog(Base):
    """Audit log for tracking important actions"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(50), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('ix_audit_logs_user_action', 'user_id', 'action'),
        Index('ix_audit_logs_date', 'created_at'),
    )