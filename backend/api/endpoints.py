"""
FastAPI endpoints for the Drug Interaction Detection System

This file contains all the API endpoints for image upload, OCR processing,
drug interaction detection, and user management.
"""

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
import asyncio
import logging
from datetime import datetime
import uuid
import os

from ..models.database import SessionLocal, get_db
from ..models.drug_models import User, DrugInteraction, ScanHistory
from .auth import verify_token, get_current_user, UserResponse
from ..ocr_processor import OCRProcessor
from ..config import UPLOAD_CONFIG, OCR_CONFIG, DRUG_DB_CONFIG

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()
security = HTTPBearer()

# Initialize OCR processor
ocr_processor = OCRProcessor()

class DrugInteractionResponse:
    """Response model for drug interaction detection"""
    def __init__(self, interactions: List[dict], severity: str, recommendations: List[str]):
        self.interactions = interactions
        self.severity = severity
        self.recommendations = recommendations
        self.timestamp = datetime.now().isoformat()

@router.post("/upload-image/")
async def upload_medication_image(
    file: UploadFile = File(...),
    user_id: Optional[int] = Form(None),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Upload and process a medication label image using OCR
    
    This endpoint accepts an image file, processes it using OCR to extract
    drug names, and returns the extracted information along with potential
    drug interactions.
    
    Args:
        file: The uploaded image file
        user_id: Optional user ID for tracking
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        JSON response with extracted drug information and interactions
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith(tuple(UPLOAD_CONFIG['allowed_extensions'])):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: {UPLOAD_CONFIG['allowed_extensions']}"
            )
        
        # Check file size
        file_content = await file.read()
        if len(file_content) > UPLOAD_CONFIG['max_file_size']:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size: {UPLOAD_CONFIG['max_file_size']} bytes"
            )
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        safe_filename = f"{file_id}{file_extension}"
        file_path = UPLOAD_CONFIG['upload_dir'] / safe_filename
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        
        logger.info(f"File uploaded: {safe_filename} by user {current_user.id}")
        
        # Process image with OCR
        extracted_text = await ocr_processor.extract_text_from_image(str(file_path))
        
        # Extract drug names from OCR text
        drug_names = await ocr_processor.extract_drug_names(extracted_text)
        
        # Check for drug interactions
        interactions = await check_drug_interactions(drug_names, db)
        
        # Save scan history
        scan_record = ScanHistory(
            user_id=current_user.id,
            image_path=str(file_path),
            extracted_text=extracted_text,
            drug_names=",".join(drug_names),
            interaction_count=len(interactions)
        )
        db.add(scan_record)
        db.commit()
        
        # Clean up uploaded file (optional, keep for audit trail)
        # os.remove(file_path)
        
        return {
            "status": "success",
            "scan_id": scan_record.id,
            "extracted_text": extracted_text,
            "drug_names": drug_names,
            "interactions": interactions,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing image upload: {str(e)}")
        # Clean up file on error
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@router.post("/check-interactions/")
async def check_drug_interactions_endpoint(
    drug_names: List[str],
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Check for drug interactions given a list of drug names
    
    This endpoint takes a list of drug names and checks for potential
    interactions using the drug interaction database.
    
    Args:
        drug_names: List of drug names to check
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        JSON response with interaction details and severity levels
    """
    try:
        if not drug_names or len(drug_names) < 2:
            return {
                "status": "success",
                "message": "Need at least 2 drugs to check interactions",
                "interactions": [],
                "severity": "NONE"
            }
        
        # Check interactions
        interactions = await check_drug_interactions(drug_names, db)
        
        # Determine overall severity
        severity_level = determine_interaction_severity(interactions)
        
        # Generate recommendations
        recommendations = generate_recommendations(interactions, severity_level)
        
        return {
            "status": "success",
            "drug_names": drug_names,
            "interactions": interactions,
            "severity": severity_level,
            "recommendations": recommendations,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error checking drug interactions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error checking interactions: {str(e)}")

@router.get("/scan-history/")
async def get_scan_history(
    limit: int = 10,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get scan history for the current user
    
    Args:
        limit: Number of records to return
        offset: Number of records to skip
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        List of scan history records
    """
    try:
        scans = db.query(ScanHistory).filter(
            ScanHistory.user_id == current_user.id
        ).order_by(ScanHistory.created_at.desc()).offset(offset).limit(limit).all()
        
        return {
            "status": "success",
            "scans": [
                {
                    "id": scan.id,
                    "drug_names": scan.drug_names.split(",") if scan.drug_names else [],
                    "interaction_count": scan.interaction_count,
                    "created_at": scan.created_at.isoformat(),
                    "extracted_text": scan.extracted_text[:100] + "..." if len(scan.extracted_text) > 100 else scan.extracted_text
                }
                for scan in scans
            ]
        }
        
    except Exception as e:
        logger.error(f"Error fetching scan history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching history: {str(e)}")

@router.get("/drug-info/{drug_name}")
async def get_drug_information(
    drug_name: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get detailed information about a specific drug
    
    Args:
        drug_name: Name of the drug to look up
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Detailed drug information including interactions
    """
    try:
        # Query drug information from database
        drug_info = db.query(DrugInteraction).filter(
            DrugInteraction.drug_name.ilike(f"%{drug_name}%")
        ).first()
        
        if not drug_info:
            # Try to fetch from external API (placeholder for actual implementation)
            drug_info = await fetch_drug_info_from_api(drug_name)
        
        return {
            "status": "success",
            "drug_name": drug_name,
            "information": drug_info,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching drug information: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching drug info: {str(e)}")

@router.post("/add-interaction/")
async def add_drug_interaction(
    drug1: str = Form(...),
    drug2: str = Form(...),
    severity: str = Form(...),
    description: str = Form(...),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Add a new drug interaction to the database (admin only)
    
    Args:
        drug1: First drug name
        drug2: Second drug name
        severity: Interaction severity level
        description: Description of the interaction
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Confirmation of interaction addition
    """
    try:
        # Check if user has admin privileges (implement based on your user model)
        if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin privileges required")
        
        # Check if interaction already exists
        existing = db.query(DrugInteraction).filter(
            ((DrugInteraction.drug_name == drug1) & (DrugInteraction.interacting_drug == drug2)) |
            ((DrugInteraction.drug_name == drug2) & (DrugInteraction.interacting_drug == drug1))
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Interaction already exists")
        
        # Add new interaction
        new_interaction = DrugInteraction(
            drug_name=drug1,
            interacting_drug=drug2,
            severity=severity,
            description=description
        )
        
        db.add(new_interaction)
        db.commit()
        
        logger.info(f"New interaction added: {drug1} - {drug2} by admin {current_user.id}")
        
        return {
            "status": "success",
            "message": "Drug interaction added successfully",
            "interaction_id": new_interaction.id
        }
        
    except Exception as e:
        logger.error(f"Error adding drug interaction: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adding interaction: {str(e)}")

# Helper functions

async def check_drug_interactions(drug_names: List[str], db) -> List[dict]:
    """
    Check for interactions between multiple drugs
    
    Args:
        drug_names: List of drug names to check
        db: Database session
    
    Returns:
        List of interaction details
    """
    interactions = []
    
    for i, drug1 in enumerate(drug_names):
        for drug2 in drug_names[i+1:]:
            # Query database for interactions
            interaction = db.query(DrugInteraction).filter(
                ((DrugInteraction.drug_name.ilike(f"%{drug1}%")) & 
                 (DrugInteraction.interacting_drug.ilike(f"%{drug2}%"))) |
                ((DrugInteraction.drug_name.ilike(f"%{drug2}%")) & 
                 (DrugInteraction.interacting_drug.ilike(f"%{drug1}%")))
            ).first()
            
            if interaction:
                interactions.append({
                    "drug1": drug1,
                    "drug2": drug2,
                    "severity": interaction.severity,
                    "description": interaction.description,
                    "severity_level": DRUG_DB_CONFIG['interaction_severity_levels'].get(interaction.severity, 1)
                })
    
    return interactions

def determine_interaction_severity(interactions: List[dict]) -> str:
    """Determine overall severity level from all interactions"""
    if not interactions:
        return "NONE"
    
    severity_levels = [interaction.get('severity', 'MINOR') for interaction in interactions]
    
    if 'CRITICAL' in severity_levels:
        return 'CRITICAL'
    elif 'MAJOR' in severity_levels:
        return 'MAJOR'
    elif 'MODERATE' in severity_levels:
        return 'MODERATE'
    else:
        return 'MINOR'

def generate_recommendations(interactions: List[dict], severity: str) -> List[str]:
    """Generate recommendations based on interaction severity"""
    recommendations = []
    
    if severity == 'CRITICAL':
        recommendations.extend([
            "URGENT: Consult healthcare provider immediately",
            "Do not take these medications together without medical supervision",
            "Contact emergency services if experiencing adverse reactions"
        ])
    elif severity == 'MAJOR':
        recommendations.extend([
            "Consult healthcare provider before taking these medications together",
            "Monitor for side effects closely",
            "Consider alternative medications"
        ])
    elif severity == 'MODERATE':
        recommendations.extend([
            "Inform your healthcare provider about this combination",
            "Monitor for any unusual symptoms",
            "Take medications as prescribed with proper spacing"
        ])
    elif severity == 'MINOR':
        recommendations.extend([
            "Generally safe combination",
            "Inform healthcare provider during next visit",
            "Follow standard dosing instructions"
        ])
    
    return recommendations

async def fetch_drug_info_from_api(drug_name: str) -> dict:
    """
    Fetch drug information from external APIs (placeholder)
    This would integrate with FDA, RxNorm, or other drug databases
    """
    # Placeholder for actual API integration
    return {
        "name": drug_name,
        "generic_name": f"Generic {drug_name}",
        "description": f"Information about {drug_name}",
        "common_uses": ["Pain relief", "Inflammation reduction"],
        "side_effects": ["Nausea", "Dizziness"],
        "warnings": ["Do not exceed recommended dose"]
    }
