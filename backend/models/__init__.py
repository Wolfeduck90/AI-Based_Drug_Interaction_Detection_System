"""
Models Package
Database models and Pydantic schemas for the Drug Interaction Detection System
"""

from .database import (
    Database,
    get_database,
    init_database,
    close_database,
    DrugModel,
    InteractionModel,
    UserModel,
    AnalysisModel
)

from .drug_models import (
    # Core Models
    DrugInfo,
    DrugInteraction,
    PatientInfo,
    
    # Request/Response Models
    PrescriptionRequest,
    PrescriptionAnalysis,
    AnalysisResponse,
    
    # Search Models
    DrugSearchRequest,
    DrugSearchResponse,
    
    # History Models
    AnalysisHistoryRequest,
    AnalysisHistoryResponse,
    
    # Authentication Models
    UserCredentials,
    UserRegistration,
    UserProfile,
    TokenResponse,
    
    # System Models
    SystemHealthResponse,
    SystemConfig,
    
    # Analysis Models
    ExtractedDrug,
    InteractionAlert,
    
    # Enums
    SeverityLevel,
    RiskLevel,
    EvidenceLevel,
    DrugClass
)

__all__ = [
    # Database components
    "Database",
    "get_database",
    "init_database",
    "close_database",
    "DrugModel",
    "InteractionModel",
    "UserModel",
    "AnalysisModel",
    
    # Pydantic models
    "DrugInfo",
    "DrugInteraction",
    "PatientInfo",
    "PrescriptionRequest",
    "PrescriptionAnalysis",
    "AnalysisResponse",
    "DrugSearchRequest",
    "DrugSearchResponse",
    "AnalysisHistoryRequest",
    "AnalysisHistoryResponse",
    "UserCredentials",
    "UserRegistration",
    "UserProfile",
    "TokenResponse",
    "SystemHealthResponse",
    "SystemConfig",
    "ExtractedDrug",
    "InteractionAlert",
    
    # Enums
    "SeverityLevel",
    "RiskLevel",
    "EvidenceLevel",
    "DrugClass"
]

# Version information
__version__ = "1.0.0"
__author__ = "Drug Interaction Detection System"
