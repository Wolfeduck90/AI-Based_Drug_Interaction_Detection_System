"""
FastAPI Backend Server for Drug Interaction Detection System
This serves as the main API backend that coordinates all system components
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import sqlite3
import hashlib
import jwt
import os
from datetime import datetime, timedelta
import logging
from pathlib import Path
import tempfile
import asyncio
from contextlib import asynccontextmanager

# Import our custom modules
from database import DatabaseManager, User, Drug, Interaction
from ocr_processor import OCRProcessor
from interaction_engine import DrugInteractionEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security configuration
SECRET_KEY = "your-secret-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Initialize components
db_manager = DatabaseManager()
ocr_processor = OCRProcessor()
interaction_engine = DrugInteractionEngine()
security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting Drug Interaction Detection API...")
    db_manager.init_db()
    logger.info("Database initialized")
    yield
    # Shutdown
    logger.info("Shutting down Drug Interaction Detection API...")

# Initialize FastAPI app
app = FastAPI(
    title="Drug Interaction Detection API",
    description="AI-powered drug interaction detection system",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class UserRegistration(BaseModel):
    username: str
    email: str
    password: str
    date_of_birth: str
    medical_conditions: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class DrugInput(BaseModel):
    drug_name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None

class InteractionCheck(BaseModel):
    drugs: List[str]
    user_id: Optional[int] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class ScanResult(BaseModel):
    extracted_drugs: List[Dict]
    interactions: List[Dict]
    alerts: List[Dict]
    risk_level: str

# Authentication functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        return username
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

def get_current_user(username: str = Depends(verify_token)) -> User:
    """Get current authenticated user"""
    user = db_manager.get_user_by_username(username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

# API Routes

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Drug Interaction Detection API",
        "version": "1.0.0",
        "status": "active",
        "endpoints": [
            "/register",
            "/login", 
            "/scan-medication",
            "/check-interactions",
            "/user/profile",
            "/user/medications",
            "/user/scan-history"
        ]
    }

@app.post("/register", response_model=Dict)
async def register_user(user_data: UserRegistration):
    """Register a new user"""
    try:
        # Check if user already exists
        existing_user = db_manager.get_user_by_username(user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Username already registered"
            )
        
        existing_email = db_manager.get_user_by_email(user_data.email)
        if existing_email:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
        
        # Hash password and create user
        hashed_password = hash_password(user_data.password)
        
        user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=hashed_password,
            date_of_birth=user_data.date_of_birth,
            medical_conditions=user_data.medical_conditions
        )
        
        user_id = db_manager.create_user(user)
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user_data.username}, expires_delta=access_token_expires
        )
        
        return {
            "message": "User registered successfully",
            "user_id": user_id,
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@app.post("/login", response_model=Token)
async def login_user(user_credentials: UserLogin):
    """Authenticate user and return access token"""
    try:
        # Get user from database
        user = db_manager.get_user_by_username(user_credentials.username)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid username or password"
            )
        
        # Verify password
        hashed_input = hash_password(user_credentials.password)
        if hashed_input != user.password_hash:
            raise HTTPException(
                status_code=401,
                detail="Invalid username or password"
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@app.post("/scan-medication", response_model=ScanResult)
async def scan_medication(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Process uploaded medication image and detect interactions"""
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="File must be an image"
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Process image with OCR
            ocr_result = ocr_processor.process_image(temp_file_path)
            
            if not ocr_result['success']:
                raise HTTPException(
                    status_code=400,
                    detail=f"OCR processing failed: {ocr_result.get('error', 'Unknown error')}"
                )
            
            # Get user's current medications
            user_medications = db_manager.get_user_medications(current_user.id)
            current_drugs = [med['drug_name'] for med in user_medications]
            
            # Process with interaction engine
            result = interaction_engine.process_medication_scan(
                ocr_result['extracted_text'],
                user_drugs=current_drugs
            )
            
            # Save scan result
            interaction_engine.save_scan_result(current_user.id, result)
            
            return ScanResult(
                extracted_drugs=result['extracted_drugs'],
                interactions=result['interactions'],
                alerts=result['alerts'],
                risk_level=result['risk_level']
            )
            
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Scan processing error: {e}")
        raise HTTPException(status_code=500, detail="Scan processing failed")

@app.post("/check-interactions")
async def check_interactions(
    interaction_check: InteractionCheck,
    current_user: User = Depends(get_current_user)
):
    """Check for interactions between specified drugs"""
    try:
        # Get user's current medications if not provided
        all_drugs = interaction_check.drugs.copy()
        
        if not interaction_check.user_id or interaction_check.user_id == current_user.id:
            user_medications = db_manager.get_user_medications(current_user.id)
            user_drugs = [med['drug_name'] for med in user_medications]
            all_drugs.extend(user_drugs)
        
        # Remove duplicates
        all_drugs = list(set(all_drugs))
        
        # Check interactions
        interactions = interaction_engine.interaction_detector.check_interactions(all_drugs)
        alerts = interaction_engine.interaction_detector.generate_alerts(interactions)
        
        return {
            "drugs_checked": all_drugs,
            "interactions_found": len(interactions),
            "interactions": interactions,
            "alerts": alerts,
            "risk_level": interaction_engine.calculate_overall_risk(alerts)
        }
        
    except Exception as e:
        logger.error(f"Interaction check error: {e}")
        raise HTTPException(status_code=500, detail="Interaction check failed")

@app.get("/user/profile")
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile information"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "date_of_birth": current_user.date_of_birth,
        "medical_conditions": current_user.medical_conditions,
        "created_at": current_user.created_at
    }

@app.get("/user/medications")
async def get_user_medications(current_user: User = Depends(get_current_user)):
    """Get user's current medications"""
    try:
        medications = db_manager.get_user_medications(current_user.id)
        return {"medications": medications}
    except Exception as e:
        logger.error(f"Error fetching user medications: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch medications")

@app.post("/user/medications")
async def add_user_medication(
    drug_input: DrugInput,
    current_user: User = Depends(get_current_user)
):
    """Add medication to user's list"""
    try:
        success = db_manager.add_user_medication(
            current_user.id,
            drug_input.drug_name,
            drug_input.dosage,
            drug_input.frequency
        )
        
        if success:
            return {"message": "Medication added successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to add medication")
            
    except Exception as e:
        logger.error(f"Error adding medication: {e}")
        raise HTTPException(status_code=500, detail="Failed to add medication")

@app.delete("/user/medications/{medication_id}")
async def remove_user_medication(
    medication_id: int,
    current_user: User = Depends(get_current_user)
):
    """Remove medication from user's list"""
    try:
        success = db_manager.remove_user_medication(current_user.id, medication_id)
        
        if success:
            return {"message": "Medication removed successfully"}
        else:
            raise HTTPException(status_code=404, detail="Medication not found")
            
    except Exception as e:
        logger.error(f"Error removing medication: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove medication")

@app.get("/user/scan-history")
async def get_scan_history(current_user: User = Depends(get_current_user)):
    """Get user's scan history"""
    try:
        history = db_manager.get_user_scan_history(current_user.id)
        return {"scan_history": history}
    except Exception as e:
        logger.error(f"Error fetching scan history: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch scan history")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "database": "operational",
            "ocr_processor": "operational", 
            "interaction_engine": "operational"
        }
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {"error": "Endpoint not found", "status_code": 404}

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return {"error": "Internal server error", "status_code": 500}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
