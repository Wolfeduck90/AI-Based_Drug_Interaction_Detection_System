"""
Prescription scan schemas
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ExtractedMedication(BaseModel):
    """Extracted medication schema"""
    name: str
    generic_name: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    route: Optional[str] = None
    prescriber: Optional[str] = None
    pharmacy: Optional[str] = None
    rx_number: Optional[str] = None
    ndc_number: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    matched_drug_id: Optional[int] = None

class ScanResult(BaseModel):
    """Scan result schema"""
    extracted_text: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    medications: List[ExtractedMedication]
    interactions: List[Dict[str, Any]] = []
    recommendations: List[str] = []
    risk_level: Optional[str] = None
    processing_time_ms: int

class ScanCreate(BaseModel):
    """Scan creation schema"""
    image_path: Optional[str] = None
    image_url: Optional[str] = None

class ScanResponse(BaseModel):
    """Scan response schema"""
    id: int
    user_id: int
    image_path: Optional[str] = None
    image_url: Optional[str] = None
    extracted_text: Optional[str] = None
    extracted_data: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None
    processing_status: ProcessingStatus
    processing_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    medications_detected: Optional[List[str]] = []
    interactions_found: int = 0
    risk_level: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class ScanHistoryRequest(BaseModel):
    """Scan history request schema"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[ProcessingStatus] = None
    limit: int = Field(default=50, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)

class ScanHistoryResponse(BaseModel):
    """Scan history response schema"""
    scans: List[ScanResponse]
    total_count: int
    has_more: bool

class OCRRequest(BaseModel):
    """OCR processing request schema"""
    enhance_image: bool = True
    extract_structured_data: bool = True
    check_interactions: bool = True

class OCRResponse(BaseModel):
    """OCR processing response schema"""
    success: bool
    scan_id: Optional[int] = None
    result: Optional[ScanResult] = None
    error: Optional[str] = None
    processing_time: float