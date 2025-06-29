"""
API v1 router
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, medications, interactions, scans, users

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(medications.router, prefix="/medications", tags=["medications"])
api_router.include_router(interactions.router, prefix="/interactions", tags=["interactions"])
api_router.include_router(scans.router, prefix="/scans", tags=["scans"])