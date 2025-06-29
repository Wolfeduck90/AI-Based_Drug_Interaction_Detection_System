"""
Prescription scan endpoints
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import structlog
import time
import os
from pathlib import Path

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import get_settings
from app.core.exceptions import ProcessingException, ValidationException
from app.models.database_models import User, PrescriptionScan, ProcessingStatus
from app.schemas.scans import (
    ScanResponse, ScanHistoryRequest, ScanHistoryResponse, 
    OCRRequest, OCRResponse
)
from app.services.ocr_service import ocr_service
from app.services.interaction_service import interaction_service

logger = structlog.get_logger(__name__)
router = APIRouter()
settings = get_settings()

@router.post("/upload", response_model=OCRResponse)
async def upload_and_scan_prescription(
    file: UploadFile = File(...),
    enhance_image: bool = Form(True),
    check_interactions: bool = Form(True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload prescription image and process with OCR
    """
    start_time = time.time()
    
    try:
        # Validate file
        if not file.content_type or not file.content_type.startswith('image/'):
            raise ValidationException("File must be an image")
        
        if file.content_type not in settings.ALLOWED_FILE_TYPES:
            raise ValidationException(f"Unsupported file type: {file.content_type}")
        
        # Read file data
        file_data = await file.read()
        
        if len(file_data) > settings.MAX_FILE_SIZE:
            raise ValidationException(f"File too large. Maximum size: {settings.MAX_FILE_SIZE} bytes")
        
        # Create scan record
        scan = PrescriptionScan(
            user_id=current_user.id,
            processing_status=ProcessingStatus.PROCESSING
        )
        
        db.add(scan)
        await db.commit()
        await db.refresh(scan)
        
        try:
            # Save uploaded file
            upload_dir = Path(settings.UPLOAD_DIR)
            upload_dir.mkdir(exist_ok=True)
            
            file_path = upload_dir / f"scan_{scan.id}_{file.filename}"
            
            with open(file_path, "wb") as f:
                f.write(file_data)
            
            scan.image_path = str(file_path)
            
            # Process with OCR
            scan_result = await ocr_service.process_image(file_data, enhance_image)
            
            # Update scan record
            scan.extracted_text = scan_result.extracted_text
            scan.confidence_score = scan_result.confidence_score
            scan.processing_time_ms = scan_result.processing_time_ms
            scan.extracted_data = {
                "medications": [med.dict() for med in scan_result.medications]
            }
            scan.medications_detected = [med.name for med in scan_result.medications]
            scan.processing_status = ProcessingStatus.COMPLETED
            
            # Check interactions if requested
            interactions = []
            if check_interactions and scan_result.medications:
                drug_names = [med.name for med in scan_result.medications]
                interactions = await interaction_service.check_interactions(
                    db=db,
                    drug_names=drug_names,
                    user_id=current_user.id
                )
                
                scan.interactions_found = len(interactions)
                
                # Determine risk level
                if any(i.severity.value == 'critical' for i in interactions):
                    scan.risk_level = 'critical'
                elif any(i.severity.value == 'major' for i in interactions):
                    scan.risk_level = 'major'
                elif any(i.severity.value == 'moderate' for i in interactions):
                    scan.risk_level = 'moderate'
                else:
                    scan.risk_level = 'low'
            
            await db.commit()
            
            # Generate recommendations
            recommendations = []
            if interactions:
                recommendations = await interaction_service.generate_recommendations(interactions)
            
            # Update scan result with interactions
            scan_result.interactions = [alert.dict() for alert in interactions]
            scan_result.recommendations = recommendations
            scan_result.risk_level = scan.risk_level
            
            processing_time = time.time() - start_time
            
            logger.info(
                "Prescription scan completed",
                scan_id=scan.id,
                user_id=current_user.id,
                medications_found=len(scan_result.medications),
                interactions_found=len(interactions),
                processing_time=processing_time
            )
            
            return OCRResponse(
                success=True,
                scan_id=scan.id,
                result=scan_result,
                processing_time=processing_time
            )
            
        except Exception as e:
            # Update scan record with error
            scan.processing_status = ProcessingStatus.FAILED
            scan.error_message = str(e)
            await db.commit()
            
            logger.error(
                "Prescription scan failed",
                scan_id=scan.id,
                user_id=current_user.id,
                error=str(e)
            )
            
            raise ProcessingException(f"Scan processing failed: {str(e)}")
            
    except Exception as e:
        processing_time = time.time() - start_time
        
        return OCRResponse(
            success=False,
            error=str(e),
            processing_time=processing_time
        )

@router.get("/history", response_model=ScanHistoryResponse)
async def get_scan_history(
    limit: int = 50,
    offset: int = 0,
    status: Optional[ProcessingStatus] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's scan history
    """
    from sqlalchemy import select, desc, func
    
    # Build query
    query = select(PrescriptionScan).where(PrescriptionScan.user_id == current_user.id)
    
    if status:
        query = query.where(PrescriptionScan.processing_status == status)
    
    # Get total count
    count_query = select(func.count(PrescriptionScan.id)).where(
        PrescriptionScan.user_id == current_user.id
    )
    if status:
        count_query = count_query.where(PrescriptionScan.processing_status == status)
    
    total_result = await db.execute(count_query)
    total_count = total_result.scalar()
    
    # Get scans with pagination
    query = query.order_by(desc(PrescriptionScan.created_at)).offset(offset).limit(limit)
    result = await db.execute(query)
    scans = result.scalars().all()
    
    return ScanHistoryResponse(
        scans=[ScanResponse.from_orm(scan) for scan in scans],
        total_count=total_count,
        has_more=offset + len(scans) < total_count
    )

@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan_details(
    scan_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed scan information
    """
    from sqlalchemy import select
    
    result = await db.execute(
        select(PrescriptionScan).where(
            PrescriptionScan.id == scan_id,
            PrescriptionScan.user_id == current_user.id
        )
    )
    
    scan = result.scalar_one_or_none()
    
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    return ScanResponse.from_orm(scan)

@router.delete("/{scan_id}")
async def delete_scan(
    scan_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a scan record and associated files
    """
    from sqlalchemy import select
    
    result = await db.execute(
        select(PrescriptionScan).where(
            PrescriptionScan.id == scan_id,
            PrescriptionScan.user_id == current_user.id
        )
    )
    
    scan = result.scalar_one_or_none()
    
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Delete associated file
    if scan.image_path and os.path.exists(scan.image_path):
        try:
            os.remove(scan.image_path)
        except Exception as e:
            logger.warning("Failed to delete scan file", file_path=scan.image_path, error=str(e))
    
    # Delete database record
    await db.delete(scan)
    await db.commit()
    
    logger.info("Scan deleted", scan_id=scan_id, user_id=current_user.id)
    
    return {"message": "Scan deleted successfully"}

@router.get("/stats/summary")
async def get_scan_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get scan statistics for the user
    """
    from sqlalchemy import select, func
    
    # Total scans
    total_result = await db.execute(
        select(func.count(PrescriptionScan.id)).where(
            PrescriptionScan.user_id == current_user.id
        )
    )
    total_scans = total_result.scalar()
    
    # Successful scans
    success_result = await db.execute(
        select(func.count(PrescriptionScan.id)).where(
            PrescriptionScan.user_id == current_user.id,
            PrescriptionScan.processing_status == ProcessingStatus.COMPLETED
        )
    )
    successful_scans = success_result.scalar()
    
    # Total interactions found
    interactions_result = await db.execute(
        select(func.sum(PrescriptionScan.interactions_found)).where(
            PrescriptionScan.user_id == current_user.id,
            PrescriptionScan.processing_status == ProcessingStatus.COMPLETED
        )
    )
    total_interactions = interactions_result.scalar() or 0
    
    # High risk scans
    high_risk_result = await db.execute(
        select(func.count(PrescriptionScan.id)).where(
            PrescriptionScan.user_id == current_user.id,
            PrescriptionScan.risk_level.in_(['critical', 'major'])
        )
    )
    high_risk_scans = high_risk_result.scalar()
    
    # Average confidence
    confidence_result = await db.execute(
        select(func.avg(PrescriptionScan.confidence_score)).where(
            PrescriptionScan.user_id == current_user.id,
            PrescriptionScan.processing_status == ProcessingStatus.COMPLETED,
            PrescriptionScan.confidence_score.isnot(None)
        )
    )
    avg_confidence = confidence_result.scalar() or 0
    
    return {
        "total_scans": total_scans,
        "successful_scans": successful_scans,
        "total_interactions": int(total_interactions),
        "high_risk_scans": high_risk_scans,
        "average_confidence": round(float(avg_confidence), 2) if avg_confidence else 0,
        "success_rate": round((successful_scans / total_scans * 100), 1) if total_scans > 0 else 0
    }