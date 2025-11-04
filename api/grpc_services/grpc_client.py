"""
gRPC Client for FastAPI Integration
Allows REST endpoints to call gRPC authentication service
"""

import grpc
from typing import Optional

try:
    from grpc_generated import auth_pb2, auth_pb2_grpc
except ImportError:
    print("⚠️  Generated protobuf code not found. Run protoc to generate Python code from auth.proto")
    auth_pb2 = None
    auth_pb2_grpc = None


class AuthGRPCClient:
    """Client wrapper for gRPC authentication service"""
    
    def __init__(self, host='localhost', port=50051):
        self.host = host
        self.port = port
        self.channel = None
        self.stub = None
        self._connect()
    
    def _connect(self):
        """Establish connection to gRPC server"""
        if auth_pb2_grpc is None:
            raise ImportError("gRPC protobuf code not generated. Run protoc first.")
        
        self.channel = grpc.insecure_channel(f'{self.host}:{self.port}')
        self.stub = auth_pb2_grpc.AuthServiceStub(self.channel)
    
    def close(self):
        """Close gRPC connection"""
        if self.channel:
            self.channel.close()
    
    def register(self, email: str, username: str, password: str, full_name: str = ""):
        """Register a new user"""
        request = auth_pb2.RegisterRequest(
            email=email,
            username=username,
            password=password,
            full_name=full_name
        )
        try:
            response = self.stub.Register(request)
            return {
                'success': response.success,
                'message': response.message,
                'session_token': response.session_token if response.success else None,
                'refresh_token': response.refresh_token if response.success else None,
                'user': {
                    'id': response.user.id,
                    'email': response.user.email,
                    'username': response.user.username,
                    'full_name': response.user.full_name,
                } if response.success else None
            }
        except grpc.RpcError as e:
            return {
                'success': False,
                'message': f'gRPC error: {e.details()}'
            }
    
    def login(self, username: str, password: str):
        """Login with credentials"""
        request = auth_pb2.LoginRequest(
            username=username,
            password=password
        )
        try:
            response = self.stub.Login(request)
            return {
                'success': response.success,
                'message': response.message,
                'session_token': response.session_token if response.success else None,
                'refresh_token': response.refresh_token if response.success else None,
                'user': {
                    'id': response.user.id,
                    'email': response.user.email,
                    'username': response.user.username,
                    'full_name': response.user.full_name,
                } if response.success else None
            }
        except grpc.RpcError as e:
            return {
                'success': False,
                'message': f'gRPC error: {e.details()}'
            }
    
    def validate_token(self, session_token: str):
        """Validate session token"""
        request = auth_pb2.ValidateTokenRequest(
            session_token=session_token
        )
        try:
            response = self.stub.ValidateToken(request)
            return {
                'valid': response.valid,
                'user_id': response.user_id if response.valid else None,
                'username': response.username if response.valid else None,
            }
        except grpc.RpcError as e:
            return {
                'valid': False,
                'error': str(e.details())
            }
    
    def refresh_token(self, refresh_token: str):
        """Refresh session token"""
        request = auth_pb2.RefreshTokenRequest(
            refresh_token=refresh_token
        )
        try:
            response = self.stub.RefreshToken(request)
            return {
                'success': response.success,
                'message': response.message,
                'session_token': response.session_token if response.success else None,
                'refresh_token': response.refresh_token if response.success else None,
            }
        except grpc.RpcError as e:
            return {
                'success': False,
                'message': f'gRPC error: {e.details()}'
            }
    
    def get_current_user(self, session_token: str):
        """Get current user information"""
        request = auth_pb2.GetCurrentUserRequest(
            session_token=session_token
        )
        try:
            response = self.stub.GetCurrentUser(request)
            return {
                'success': response.success,
                'message': response.message,
                'user': {
                    'id': response.user.id,
                    'email': response.user.email,
                    'username': response.user.username,
                    'full_name': response.user.full_name,
                    'avatar_url': response.user.avatar_url,
                    'is_active': response.user.is_active,
                    'is_verified': response.user.is_verified,
                } if response.success else None
            }
        except grpc.RpcError as e:
            return {
                'success': False,
                'message': f'gRPC error: {e.details()}'
            }
    
    def logout(self, session_token: str):
        """Logout user"""
        request = auth_pb2.LogoutRequest(
            session_token=session_token
        )
        try:
            response = self.stub.Logout(request)
            return {
                'success': response.success,
                'message': response.message
            }
        except grpc.RpcError as e:
            return {
                'success': False,
                'message': f'gRPC error: {e.details()}'
            }


# Singleton instance for reuse
_grpc_client = None

def get_grpc_auth_client() -> AuthGRPCClient:
    """Get or create gRPC auth client instance"""
    global _grpc_client
    if _grpc_client is None:
        _grpc_client = AuthGRPCClient()
    return _grpc_client
