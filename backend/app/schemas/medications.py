"""
Medication-related schemas
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

class DrugBase(BaseModel):
    """Base drug schema"""
    name: str = Field(..., min_length=1, max_length=255)
    generic_name: Optional[str] = Field(None, max_length=255)
    brand_names: Optional[List[str]] = []
    ndc_numbers: Optional[List[str]] = []
    rxcui: Optional[str] = Field(None, max_length=50)
    drug_class: Optional[str] = Field(None, max_length=100)
    active_ingredients: Optional[List[str]] = []
    contraindications: Optional[str] = None
    side_effects: Optional[List[str]] = []
    dosage_forms: Optional[List[str]] = []
    strength_options: Optional[List[str]] = []

class DrugCreate(DrugBase):
    """Drug creation schema"""
    pass

class DrugUpdate(BaseModel):
    """Drug update schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    generic_name: Optional[str] = Field(None, max_length=255)
    brand_names: Optional[List[str]] = None
    ndc_numbers: Optional[List[str]] = None
    rxcui: Optional[str] = Field(None, max_length=50)
    drug_class: Optional[str] = Field(None, max_length=100)
    active_ingredients: Optional[List[str]] = None
    contraindications: Optional[str] = None
    side_effects: Optional[List[str]] = None
    dosage_forms: Optional[List[str]] = None
    strength_options: Optional[List[str]] = None

class DrugResponse(DrugBase):
    """Drug response schema"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class MedicationBase(BaseModel):
    """Base medication schema"""
    custom_name: Optional[str] = Field(None, max_length=255)
    dosage: Optional[str] = Field(None, max_length=100)
    frequency: Optional[str] = Field(None, max_length=100)
    route: Optional[str] = Field(None, max_length=50)
    prescriber: Optional[str] = Field(None, max_length=255)
    pharmacy: Optional[str] = Field(None, max_length=255)
    prescription_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    notes: Optional[str] = None

class MedicationCreate(MedicationBase):
    """Medication creation schema"""
    drug_id: Optional[int] = None
    
    @validator('drug_id', 'custom_name')
    def validate_drug_reference(cls, v, values):
        if not values.get('drug_id') and not values.get('custom_name'):
            raise ValueError('Either drug_id or custom_name must be provided')
        return v

class MedicationUpdate(MedicationBase):
    """Medication update schema"""
    drug_id: Optional[int] = None
    is_active: Optional[bool] = None

class MedicationResponse(MedicationBase):
    """Medication response schema"""
    id: int
    user_id: int
    drug_id: Optional[int] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    drug: Optional[DrugResponse] = None
    
    class Config:
        from_attributes = True

class MedicationSearch(BaseModel):
    """Medication search schema"""
    query: str = Field(..., min_length=1, max_length=255)
    search_type: str = Field(default="fuzzy", regex="^(exact|fuzzy|contains)$")
    limit: int = Field(default=20, ge=1, le=100)
    include_interactions: bool = False

class MedicationSearchResponse(BaseModel):
    """Medication search response schema"""
    drugs: List[DrugResponse]
    total_count: int
    query: str
    search_type: str