"""
FastAPI routes that use gRPC authentication.
Replaces JWT-based authentication with gRPC calls.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from api.grpc_client import get_auth_client

router = APIRouter()

# Request/Response Models
class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: Optional[str]
    is_active: bool
    is_verified: bool
    created_at: str

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest):
    """
    Register a new user via gRPC.
    """
    client = get_auth_client()
    result = client.register(
        email=request.email,
        username=request.username,
        password=request.password,
        full_name=request.full_name
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Registration failed")
        )
    
    return {
        "access_token": result["access_token"],
        "refresh_token": result["refresh_token"],
        "token_type": "bearer",
        "user": result["user"]
    }

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Login with username/email and password via gRPC.
    """
    client = get_auth_client()
    result = client.login(
        username=request.username,
        password=request.password
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result.get("error", "Invalid credentials")
        )
    
    return {
        "access_token": result["access_token"],
        "refresh_token": result["refresh_token"],
        "token_type": "bearer",
        "user": result["user"]
    }

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh access token via gRPC.
    """
    client = get_auth_client()
    result = client.refresh_token(request.refresh_token)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result.get("error", "Invalid refresh token")
        )
    
    # Get user info with new token
    user_result = client.get_user(result["access_token"])
    
    return {
        "access_token": result["access_token"],
        "refresh_token": result["refresh_token"],
        "token_type": "bearer",
        "user": user_result.get("user", {})
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user(token: str = Depends(lambda: None)):
    """
    Get current authenticated user's information via gRPC.
    Token should be passed in Authorization header.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    client = get_auth_client()
    result = client.get_user(token)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result.get("error", "Invalid token")
        )
    
    return result["user"]

@router.post("/verify")
async def verify_token(token: str):
    """
    Verify token validity via gRPC.
    """
    client = get_auth_client()
    result = client.verify_token(token)
    
    if not result.get("valid"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result.get("error", "Invalid token")
        )
    
    return {
        "valid": True,
        "user_id": result["user_id"],
        "username": result["username"]
    }

@router.post("/logout")
async def logout():
    """
    Logout user (client should delete tokens).
    """
    return {"message": "Successfully logged out"}
