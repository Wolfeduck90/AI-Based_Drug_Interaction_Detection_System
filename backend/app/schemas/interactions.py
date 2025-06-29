"""
Drug interaction schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class SeverityLevel(str, Enum):
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CRITICAL = "critical"

class EvidenceLevel(str, Enum):
    THEORETICAL = "theoretical"
    CASE_REPORT = "case_report"
    OBSERVATIONAL = "observational"
    CLINICAL_TRIAL = "clinical_trial"
    SYSTEMATIC_REVIEW = "systematic_review"

class InteractionBase(BaseModel):
    """Base interaction schema"""
    severity: SeverityLevel
    interaction_type: Optional[str] = Field(None, max_length=50)
    mechanism: Optional[str] = None
    clinical_effect: str = Field(..., min_length=10)
    management: Optional[str] = None
    evidence_level: Optional[EvidenceLevel] = None
    frequency: Optional[str] = None
    onset: Optional[str] = None
    documentation: Optional[str] = None
    source: Optional[str] = Field(None, max_length=100)
    source_url: Optional[str] = Field(None, max_length=500)

class InteractionCreate(InteractionBase):
    """Interaction creation schema"""
    drug1_id: int
    drug2_id: int

class InteractionUpdate(BaseModel):
    """Interaction update schema"""
    severity: Optional[SeverityLevel] = None
    interaction_type: Optional[str] = Field(None, max_length=50)
    mechanism: Optional[str] = None
    clinical_effect: Optional[str] = Field(None, min_length=10)
    management: Optional[str] = None
    evidence_level: Optional[EvidenceLevel] = None
    frequency: Optional[str] = None
    onset: Optional[str] = None
    documentation: Optional[str] = None
    source: Optional[str] = Field(None, max_length=100)
    source_url: Optional[str] = Field(None, max_length=500)

class InteractionResponse(InteractionBase):
    """Interaction response schema"""
    id: int
    drug1_id: int
    drug2_id: int
    created_at: datetime
    updated_at: datetime
    drug1: Optional[Dict[str, Any]] = None
    drug2: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

class InteractionCheck(BaseModel):
    """Interaction check request schema"""
    medication_ids: Optional[List[int]] = None
    drug_names: Optional[List[str]] = None
    include_patient_medications: bool = True

class InteractionAlert(BaseModel):
    """Interaction alert schema"""
    drug1_name: str
    drug2_name: str
    severity: SeverityLevel
    description: str
    clinical_effects: Optional[str] = None
    management: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    risk_score: float = Field(..., ge=0.0, le=1.0)
    source: str

class InteractionCheckResponse(BaseModel):
    """Interaction check response schema"""
    total_interactions: int
    interactions_by_severity: Dict[str, List[InteractionAlert]]
    recommendations: List[str]
    emergency_flag: bool
    checked_medications: List[str]
    processing_time: float

class AlertBase(BaseModel):
    """Base alert schema"""
    alert_type: str = Field(..., max_length=50)
    severity: SeverityLevel
    title: str = Field(..., max_length=255)
    message: str
    recommendations: Optional[List[str]] = []
    expires_at: Optional[datetime] = None

class AlertCreate(AlertBase):
    """Alert creation schema"""
    interaction_id: Optional[int] = None
    medication_ids: Optional[List[int]] = []

class AlertResponse(AlertBase):
    """Alert response schema"""
    id: int
    user_id: int
    interaction_id: Optional[int] = None
    medication_ids: Optional[List[int]] = []
    is_acknowledged: bool
    acknowledged_at: Optional[datetime] = None
    is_dismissed: bool
    dismissed_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class AlertUpdate(BaseModel):
    """Alert update schema"""
    is_acknowledged: Optional[bool] = None
    is_dismissed: Optional[bool] = None