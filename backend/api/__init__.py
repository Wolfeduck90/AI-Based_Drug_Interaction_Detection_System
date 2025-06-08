"""
API Package
FastAPI routes and authentication for the Drug Interaction Detection System
"""

from .auth import (
    AuthManager,
    get_current_user,
    create_access_token,
    verify_token,
    hash_password,
    verify_password,
    oauth2_scheme
)

from .endpoints import (
    router as api_router,
    auth_router,
    drugs_router,
    analysis_router,
    system_router
)

__all__ = [
    # Authentication
    "AuthManager",
    "get_current_user",
    "create_access_token",
    "verify_token", 
    "hash_password",
    "verify_password",
    "oauth2_scheme",
    
    # Routers
    "api_router",
    "auth_router",
    "drugs_router",
    "analysis_router",
    "system_router"
]

# API version
API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"
