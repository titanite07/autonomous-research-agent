"""
gRPC client wrapper for authentication.
Use this in FastAPI endpoints to call gRPC auth service.
"""

import grpc
from typing import Optional, Dict, Any
import os
import sys

# Add the generated proto directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from grpc_generated import auth_pb2, auth_pb2_grpc

# gRPC server configuration
GRPC_HOST = os.getenv("GRPC_AUTH_HOST", "localhost")
GRPC_PORT = os.getenv("GRPC_AUTH_PORT", "50051")
GRPC_ADDRESS = f"{GRPC_HOST}:{GRPC_PORT}"

class AuthServiceClient:
    """Client for gRPC Authentication Service"""
    
    def __init__(self, address: str = GRPC_ADDRESS):
        self.address = address
        self.channel = None
        self.stub = None
    
    def connect(self):
        """Establish gRPC connection"""
        self.channel = grpc.insecure_channel(self.address)
        self.stub = auth_pb2_grpc.AuthServiceStub(self.channel)
    
    def close(self):
        """Close gRPC connection"""
        if self.channel:
            self.channel.close()
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def register(self, email: str, username: str, password: str, 
                 full_name: Optional[str] = None) -> Dict[str, Any]:
        """Register a new user via gRPC"""
        request = auth_pb2.RegisterRequest(
            email=email,
            username=username,
            password=password,
            full_name=full_name or ""
        )
        
        try:
            response = self.stub.Register(request)
            
            if response.success:
                return {
                    "success": True,
                    "access_token": response.session_token,
                    "refresh_token": response.refresh_token,
                    "user": {
                        "id": response.user.id,
                        "email": response.user.email,
                        "username": response.user.username,
                        "full_name": response.user.full_name,
                        "is_verified": response.user.is_verified,
                        "created_at": response.user.created_at
                    }
                }
            else:
                return {
                    "success": False,
                    "error": response.message
                }
        except grpc.RpcError as e:
            return {
                "success": False,
                "error": f"gRPC Error: {e.details()}"
            }
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """Login user via gRPC"""
        request = auth_pb2.LoginRequest(
            username=username,
            password=password
        )
        
        try:
            response = self.stub.Login(request)
            
            if response.success:
                return {
                    "success": True,
                    "access_token": response.session_token,
                    "refresh_token": response.refresh_token,
                    "user": {
                        "id": response.user.id,
                        "email": response.user.email,
                        "username": response.user.username,
                        "full_name": response.user.full_name,
                        "is_verified": response.user.is_verified,
                        "created_at": response.user.created_at
                    }
                }
            else:
                return {
                    "success": False,
                    "error": response.message
                }
        except grpc.RpcError as e:
            return {
                "success": False,
                "error": f"gRPC Error: {e.details()}"
            }
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify token via gRPC"""
        request = auth_pb2.ValidateTokenRequest(session_token=token)
        
        try:
            response = self.stub.ValidateToken(request)
            
            if response.valid:
                return {
                    "valid": True,
                    "user_id": response.user_id,
                    "username": response.username
                }
            else:
                return {
                    "valid": False,
                    "error": response.error_message
                }
        except grpc.RpcError as e:
            return {
                "valid": False,
                "error": f"gRPC Error: {e.details()}"
            }
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token via gRPC"""
        request = auth_pb2.RefreshTokenRequest(refresh_token=refresh_token)
        
        try:
            response = self.stub.RefreshToken(request)
            
            if response.success:
                return {
                    "success": True,
                    "access_token": response.session_token,
                    "refresh_token": response.refresh_token
                }
            else:
                return {
                    "success": False,
                    "error": response.message
                }
        except grpc.RpcError as e:
            return {
                "success": False,
                "error": f"gRPC Error: {e.details()}"
            }
    
    def get_user(self, token: str) -> Dict[str, Any]:
        """Get user info via gRPC"""
        request = auth_pb2.GetCurrentUserRequest(session_token=token)
        
        try:
            response = self.stub.GetCurrentUser(request)
            
            if response.success:
                return {
                    "success": True,
                    "user": {
                        "id": response.user.id,
                        "email": response.user.email,
                        "username": response.user.username,
                        "full_name": response.user.full_name,
                        "is_verified": response.user.is_verified,
                        "is_active": response.user.is_active,
                        "created_at": response.user.created_at
                    }
                }
            else:
                return {
                    "success": False,
                    "error": response.message
                }
        except grpc.RpcError as e:
            return {
                "success": False,
                "error": f"gRPC Error: {e.details()}"
            }

# Singleton instance
_client_instance = None

def get_auth_client() -> AuthServiceClient:
    """Get or create auth client singleton"""
    global _client_instance
    if _client_instance is None:
        _client_instance = AuthServiceClient()
        _client_instance.connect()
    return _client_instance
