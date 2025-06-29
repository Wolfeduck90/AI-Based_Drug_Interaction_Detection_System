"""
Custom exception classes
"""

from fastapi import HTTPException
from typing import Optional

class CustomHTTPException(HTTPException):
    """Custom HTTP exception with error codes"""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        headers: Optional[dict] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code

class ValidationException(CustomHTTPException):
    """Validation error exception"""
    
    def __init__(self, detail: str, field: Optional[str] = None):
        super().__init__(
            status_code=422,
            detail=detail,
            error_code="VALIDATION_ERROR"
        )
        self.field = field

class ProcessingException(CustomHTTPException):
    """Processing error exception"""
    
    def __init__(self, detail: str, process_type: Optional[str] = None):
        super().__init__(
            status_code=500,
            detail=detail,
            error_code="PROCESSING_ERROR"
        )
        self.process_type = process_type

class AuthenticationException(CustomHTTPException):
    """Authentication error exception"""
    
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=401,
            detail=detail,
            error_code="AUTHENTICATION_ERROR",
            headers={"WWW-Authenticate": "Bearer"}
        )

class AuthorizationException(CustomHTTPException):
    """Authorization error exception"""
    
    def __init__(self, detail: str = "Access denied"):
        super().__init__(
            status_code=403,
            detail=detail,
            error_code="AUTHORIZATION_ERROR"
        )

class NotFoundError(CustomHTTPException):
    """Resource not found exception"""
    
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(
            status_code=404,
            detail=detail,
            error_code="NOT_FOUND"
        )

class ConflictError(CustomHTTPException):
    """Resource conflict exception"""
    
    def __init__(self, detail: str = "Resource conflict"):
        super().__init__(
            status_code=409,
            detail=detail,
            error_code="CONFLICT"
        )