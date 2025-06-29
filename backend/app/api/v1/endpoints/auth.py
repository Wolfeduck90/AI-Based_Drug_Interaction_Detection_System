"""
Authentication endpoints
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.database import get_db
from app.core.security import (
    authenticate_user, create_access_token, create_refresh_token,
    get_password_hash, verify_token, get_current_user
)
from app.core.exceptions import AuthenticationException, ConflictError
from app.models.database_models import User
from app.schemas.auth import (
    UserCreate, UserLogin, AuthResponse, UserResponse, 
    Token, PasswordChange, PasswordReset
)

logger = structlog.get_logger(__name__)
router = APIRouter()
security = HTTPBearer()

@router.post("/register", response_model=AuthResponse)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user"""
    
    # Check if user already exists
    from sqlalchemy import select
    
    existing_user = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    
    if existing_user.scalar_one_or_none():
        raise ConflictError("Email already registered")
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    
    new_user = User(
        email=user_data.email,
        name=user_data.name,
        password_hash=hashed_password,
        phone=user_data.phone,
        date_of_birth=user_data.date_of_birth,
        emergency_contact=user_data.emergency_contact,
        allergies=user_data.allergies,
        medical_conditions=user_data.medical_conditions,
        role=user_data.role,
        is_active=True,
        is_verified=False  # Email verification would be implemented here
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Create tokens
    access_token = create_access_token(data={"sub": new_user.id})
    refresh_token = create_refresh_token(data={"sub": new_user.id})
    
    logger.info("User registered", user_id=new_user.id, email=new_user.email)
    
    return AuthResponse(
        user=UserResponse.from_orm(new_user),
        token=Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=30 * 60  # 30 minutes
        )
    )

@router.post("/login", response_model=AuthResponse)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return tokens"""
    
    user = await authenticate_user(db, credentials.email, credentials.password)
    
    if not user:
        raise AuthenticationException("Invalid email or password")
    
    if not user.is_active:
        raise AuthenticationException("Account is deactivated")
    
    # Create tokens
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})
    
    logger.info("User logged in", user_id=user.id, email=user.email)
    
    return AuthResponse(
        user=UserResponse.from_orm(user),
        token=Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=30 * 60  # 30 minutes
        )
    )

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token"""
    
    try:
        payload = verify_token(refresh_token)
        
        if payload.get("type") != "refresh":
            raise AuthenticationException("Invalid token type")
        
        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationException("Invalid token payload")
        
        # Verify user still exists and is active
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            raise AuthenticationException("User not found or inactive")
        
        # Create new access token
        new_access_token = create_access_token(data={"sub": user.id})
        
        return Token(
            access_token=new_access_token,
            refresh_token=refresh_token,  # Keep the same refresh token
            expires_in=30 * 60
        )
        
    except Exception as e:
        logger.error("Token refresh failed", error=str(e))
        raise AuthenticationException("Invalid refresh token")

@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change user password"""
    
    from app.core.security import verify_password
    
    # Verify current password
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise AuthenticationException("Current password is incorrect")
    
    # Update password
    current_user.password_hash = get_password_hash(password_data.new_password)
    await db.commit()
    
    logger.info("Password changed", user_id=current_user.id)
    
    return {"message": "Password changed successfully"}

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user)
):
    """Logout user (client should discard tokens)"""
    
    logger.info("User logged out", user_id=current_user.id)
    
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    
    return UserResponse.from_orm(current_user)

@router.post("/forgot-password")
async def forgot_password(
    request: PasswordReset,
    db: AsyncSession = Depends(get_db)
):
    """Request password reset (placeholder implementation)"""
    
    # In a real implementation, this would:
    # 1. Check if user exists
    # 2. Generate a secure reset token
    # 3. Send email with reset link
    # 4. Store token with expiration
    
    logger.info("Password reset requested", email=request.email)
    
    # Always return success to prevent email enumeration
    return {"message": "If the email exists, a reset link has been sent"}