"""
Drug Data Models
Pydantic models for API request/response validation and data structures
for the Drug Interaction Detection System
"""

from pydantic import BaseModel, Field, validator, root_validator
from typing import List, Optional, Dict, Union, Any
from datetime import datetime
from enum import Enum
import re

# Enums for controlled vocabularies
class SeverityLevel(str, Enum):
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    SEVERE = "severe"

class RiskLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    SEVERE = "severe"

class EvidenceLevel(str, Enum):
    THEORETICAL = "theoretical"
    CASE_REPORT = "case_report"
    OBSERVATIONAL = "observational"
    CLINICAL_TRIAL = "clinical_trial"
    SYSTEMATIC_REVIEW = "systematic_review"

class DrugClass(str, Enum):
    ANTIBIOTIC = "antibiotic"
    ANALGESIC = "analgesic"
    ANTICOAGULANT = "anticoagulant"
    ANTIHYPERTENSIVE = "antihypertensive"
    ANTIDIABETIC = "antidiabetic"
    ANTIDEPRESSANT = "antidepressant"
    ANTICONVULSANT = "anticonvulsant"
    CARDIAC = "cardiac"
    RESPIRATORY = "respiratory"
    GASTROINTESTINAL = "gastrointestinal"
    HORMONAL = "hormonal"
    IMMUNOSUPPRESSANT = "immunosuppressant"
    ANTICANCER = "anticancer"
    OTHER = "other"

# Base Models
class DrugInfo(BaseModel):
    """Drug information model"""
    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=200, description="Drug name")
    generic_name: Optional[str] = Field(None, max_length=200, description="Generic drug name")
    brand_names: Optional[List[str]] = Field(default_factory=list, description="Brand names")
    drug_class: Optional[DrugClass] = Field(None, description="Therapeutic drug class")
    mechanism: Optional[str] = Field(None, max_length=1000, description="Mechanism of action")
    side_effects: Optional[str] = Field(None, max_length=2000, description="Common side effects")
    contraindications: Optional[str] = Field(None, max_length=1000, description="Contraindications")
    dosage_forms: Optional[List[str]] = Field(default_factory=list, description="Available dosage forms")
    strength: Optional[str] = Field(None, description="Drug strength/concentration")
    half_life: Optional[str] = Field(None, description="Drug half-life")
    metabolism: Optional[str] = Field(None, description="Metabolic pathway")
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default_factory=datetime.now)

    @validator('name', 'generic_name')
    def validate_drug_names(cls, v):
        if v and not re.match(r'^[a-zA-Z0-9\s\-\.]+$', v):
            raise ValueError('Drug names must contain only alphanumeric characters, spaces, hyphens, and periods')
        return v.strip() if v else v

    class Config:
        use_enum_values = True

class DrugInteraction(BaseModel):
    """Drug interaction model"""
    id: Optional[int] = None
    drug1_name: str = Field(..., min_length=1, description="First drug name")
    drug2_name: str = Field(..., min_length=1, description="Second drug name")
    severity: SeverityLevel = Field(..., description="Interaction severity level")
    description: str = Field(..., min_length=10, max_length=2000, description="Interaction description")
    mechanism: Optional[str] = Field(None, max_length=1000, description="Interaction mechanism")
    clinical_effects: Optional[str] = Field(None, max_length=1000, description="Clinical effects")
    management: Optional[str] = Field(None, max_length=1000, description="Management recommendations")
    evidence_level: Optional[EvidenceLevel] = Field(None, description="Evidence quality level")
    frequency: Optional[str] = Field(None, description="Interaction frequency")
    onset: Optional[str] = Field(None, description="Onset timing")
    documentation: Optional[str] = Field(None, description="Documentation quality")
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default_factory=datetime.now)

    @validator('drug1_name', 'drug2_name')
    def validate_drug_names(cls, v):
        if not re.match(r'^[a-zA-Z0-9\s\-\.]+$', v):
            raise ValueError('Drug names must contain only alphanumeric characters, spaces, hyphens, and periods')
        return v.strip()

    @root_validator
    def validate_different_drugs(cls, values):
        drug1 = values.get('drug1_name', '').lower()
        drug2 = values.get('drug2_name', '').lower()
        if drug1 == drug2:
            raise ValueError('Drug interaction must involve two different drugs')
        return values

    class Config:
        use_enum_values = True

class PatientInfo(BaseModel):
    """Patient information model"""
    patient_id: str = Field(..., min_length=1, max_length=50, description="Patient identifier")
    age: Optional[int] = Field(None, ge=0, le=150, description="Patient age")
    weight: Optional[float] = Field(None, ge=0, le=1000, description="Patient weight in kg")
    height: Optional[float] = Field(None, ge=0, le=300, description="Patient height in cm")
    gender: Optional[str] = Field(None, regex="^(male|female|other)$", description="Patient gender")
    allergies: Optional[List[str]] = Field(default_factory=list, description="Known allergies")
    medical_conditions: Optional[List[str]] = Field(default_factory=list, description="Medical conditions")
    current_medications: Optional[List[str]] = Field(default_factory=list, description="Current medications")

    @validator('patient_id')
    def validate_patient_id(cls, v):
        if not re.match(r'^[a-zA-Z0-9\-_]+$', v):
            raise ValueError('Patient ID must contain only alphanumeric characters, hyphens, and underscores')
        return v

class PrescriptionRequest(BaseModel):
    """Prescription analysis request model"""
    patient_info: PatientInfo = Field(..., description="Patient information")
    prescription_text: Optional[str] = Field(None, description="Raw prescription text")
    image_data: Optional[str] = Field(None, description="Base64 encoded prescription image")
    image_filename: Optional[str] = Field(None, description="Original image filename")
    analysis_options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Analysis configuration")

    @root_validator
    def validate_input_data(cls, values):
        text = values.get('prescription_text')
        image = values.get('image_data')
        if not text and not image:
            raise ValueError('Either prescription_text or image_data must be provided')
        return values

    @validator('image_data')
    def validate_image_data(cls, v):
        if v:
            # Basic base64 validation
            try:
                import base64
                base64.b64decode(v.split(',')[-1])  # Handle data URL format
            except Exception:
                raise ValueError('Invalid base64 image data')
        return v

class ExtractedDrug(BaseModel):
    """Extracted drug information"""
    name: str = Field(..., description="Extracted drug name")
    dosage: Optional[str] = Field(None, description="Dosage information")
    frequency: Optional[str] = Field(None, description="Dosage frequency")
    route: Optional[str] = Field(None, description="Route of administration")
    duration: Optional[str] = Field(None, description="Treatment duration")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence")
    standardized_name: Optional[str] = Field(None, description="Standardized drug name")
    drug_id: Optional[int] = Field(None, description="Database drug ID")

class InteractionAlert(BaseModel):
    """Drug interaction alert"""
    interaction: DrugInteraction = Field(..., description="Interaction details")
    affected_drugs: List[str] = Field(..., description="Drugs involved in interaction")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Risk assessment score")
    priority: int = Field(..., ge=1, le=5, description="Alert priority (1=highest, 5=lowest)")
    recommendations: List[str] = Field(default_factory=list, description="Clinical recommendations")

class PrescriptionAnalysis(BaseModel):
    """Prescription analysis results"""
    patient_id: str = Field(..., description="Patient identifier")
    analysis_id: str = Field(..., description="Unique analysis identifier")
    extracted_drugs: List[ExtractedDrug] = Field(default_factory=list, description="Extracted drugs")
    identified_interactions: List[InteractionAlert] = Field(default_factory=list, description="Drug interactions")
    risk_level: RiskLevel = Field(..., description="Overall risk assessment")
    recommendations: List[str] = Field(default_factory=list, description="Clinical recommendations")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Overall analysis confidence")
    warnings: List[str] = Field(default_factory=list, description="Clinical warnings")
    contraindications: List[str] = Field(default_factory=list, description="Identified contraindications")
    allergy_alerts: List[str] = Field(default_factory=list, description="Allergy-related alerts")
    dosage_concerns: List[str] = Field(default_factory=list, description="Dosage-related concerns")
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")
    processing_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Processing metadata")

    class Config:
        use_enum_values = True

class AnalysisResponse(BaseModel):
    """API response for prescription analysis"""
    success: bool = Field(..., description="Request success status")
    analysis: Optional[PrescriptionAnalysis] = Field(None, description="Analysis results")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    error_code: Optional[str] = Field(None, description="Error code for client handling")
    processing_time: float = Field(..., ge=0, description="Processing time in seconds")
    request_id: str = Field(..., description="Unique request identifier")
    api_version: str = Field(default="1.0", description="API version")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")

class AnalysisHistoryRequest(BaseModel):
    """Request for analysis history"""
    patient_id: Optional[str] = Field(None, description="Filter by patient ID")
    start_date: Optional[datetime] = Field(None, description="Start date filter")
    end_date: Optional[datetime] = Field(None, description="End date filter")
    limit: int = Field(default=50, ge=1, le=1000, description="Result limit")
    offset: int = Field(default=0, ge=0, description="Result offset")

class AnalysisHistoryResponse(BaseModel):
    """Response for analysis history"""
    success: bool = Field(..., description="Request success status")
    analyses: List[PrescriptionAnalysis] = Field(default_factory=list, description="Analysis history")
    total_count: int = Field(..., ge=0, description="Total number of analyses")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")

class DrugSearchRequest(BaseModel):
    """Drug search request"""
    query: str = Field(..., min_length=1, max_length=200, description="Search query")
    search_type: str = Field(default="fuzzy", regex="^(exact|fuzzy|contains)$", description="Search type")
    limit: int = Field(default=20, ge=1, le=100, description="Result limit")
    include_interactions: bool = Field(default=False, description="Include interaction data")

class DrugSearchResponse(BaseModel):
    """Drug search response"""
    success: bool = Field(..., description="Request success status")
    drugs: List[DrugInfo] = Field(default_factory=list, description="Found drugs")
    total_count: int = Field(..., ge=0, description="Total number of matches")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    processing_time: float = Field(..., ge=0, description="Processing time in seconds")

class SystemHealthResponse(BaseModel):
    """System health check response"""
    status: str = Field(..., regex="^(healthy|degraded|unhealthy)$", description="System status")
    database_connected: bool = Field(..., description="Database connection status")
    ml_models_loaded: bool = Field(..., description="ML models loading status")
    ocr_service_available: bool = Field(..., description="OCR service availability")
    uptime_seconds: float = Field(..., ge=0, description="System uptime in seconds")
    version: str = Field(..., description="System version")
    timestamp: datetime = Field(default_factory=datetime.now, description="Health check timestamp")

class UserCredentials(BaseModel):
    """User authentication credentials"""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    password: str = Field(..., min_length=6, max_length=128, description="Password")

    @validator('username')
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_\-\.]+$', v):
            raise ValueError('Username must contain only alphanumeric characters, underscores, hyphens, and periods')
        return v

class UserRegistration(UserCredentials):
    """User registration data"""
    email: str = Field(..., regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', description="Email address")
    full_name: str = Field(..., min_length=2, max_length=100, description="Full name")
    role: str = Field(default="user", regex="^(user|admin|pharmacist|doctor)$", description="User role")

class UserProfile(BaseModel):
    """User profile information"""
    id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    full_name: str = Field(..., description="Full name")
    role: str = Field(..., description="User role")
    created_at: datetime = Field(..., description="Account creation date")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    is_active: bool = Field(default=True, description="Account active status")

class TokenResponse(BaseModel):
    """Authentication token response"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: UserProfile = Field(..., description="User profile information")

# Configuration Models
class DatabaseConfig(BaseModel):
    """Database configuration"""
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    database: str = Field(..., description="Database name")
    username: str = Field(..., description="Database username")
    password: str = Field(..., description="Database password")
    pool_size: int = Field(default=10, description="Connection pool size")

class MLModelConfig(BaseModel):
    """Machine learning model configuration"""
    drug_extraction_model: str = Field(..., description="Drug extraction model path")
    interaction_model: str = Field(..., description="Interaction prediction model path")
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Confidence threshold")
    batch_size: int = Field(default=32, ge=1, description="Model batch size")

class SystemConfig(BaseModel):
    """System configuration"""
    database: DatabaseConfig = Field(..., description="Database configuration")
    ml_models: MLModelConfig = Field(..., description="ML model configuration")
    secret_key: str = Field(..., description="JWT secret key")
    token_expire_hours: int = Field(default=24, description="Token expiration time")
    max_file_size_mb: int = Field(default=10, description="Maximum upload file size")
    allowed_file_types: List[str] = Field(default=["jpg", "jpeg", "png", "pdf"], description="Allowed file types")
    debug: bool = Field(default=False, description="Debug mode")

    class Config:
        env_prefix = "DRUG_SYSTEM_"
