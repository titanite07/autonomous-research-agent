"""
Authentication middleware (optional)
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.security import APIKeyHeader
import os

# API key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def add_auth_middleware(app: FastAPI):
    """
    Add authentication middleware to FastAPI app
    
    Currently disabled for development. Enable for production.
    """
    
    @app.middleware("http")
    async def auth_middleware(request: Request, call_next):
        # Skip auth for docs and health check
        if request.url.path in ["/", "/docs", "/redoc", "/openapi.json", "/api/v1/health"]:
            return await call_next(request)
        
        # Get API key from header
        api_key = request.headers.get("X-API-Key")
        
        # Check API key (replace with real validation)
        valid_api_key = os.getenv("API_KEY", "your-secret-api-key")
        
        if api_key != valid_api_key:
            raise HTTPException(
                status_code=401,
                detail="Invalid or missing API key"
            )
        
        # Continue to route
        response = await call_next(request)
        return response
