"""
gRPC Authentication Service Implementation
Uses sessions stored in database instead of JWT tokens
"""

import grpc
from concurrent import futures
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from sqlalchemy.orm import Session as DBSession
from api.database import SessionLocal
from api.models.db_models import User, UserPreference
from api.auth.jwt_handler import get_password_hash, verify_password

# Import generated protobuf code
try:
    from grpc_generated import auth_pb2, auth_pb2_grpc
except ImportError as e:
    print(f"⚠️  Generated protobuf code not found: {e}")
    print("Run: python -m grpc_tools.protoc -I./grpc-protos --python_out=./grpc_generated --grpc_python_out=./grpc_generated ./grpc-protos/auth.proto")
    sys.exit(1)

# Session storage (in production, use Redis or database)
# Format: {session_token: {user_id, expires_at, refresh_token}}
SESSIONS = {}
REFRESH_TOKENS = {}

SESSION_EXPIRE_HOURS = 24
REFRESH_EXPIRE_DAYS = 7


def generate_token() -> str:
    """Generate a secure random session token"""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Hash token for storage"""
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(user_id: str) -> tuple[str, str, datetime]:
    """
    Create a new session for user
    Returns: (session_token, refresh_token, expires_at)
    """
    session_token = generate_token()
    refresh_token = generate_token()
    expires_at = datetime.utcnow() + timedelta(hours=SESSION_EXPIRE_HOURS)
    
    # Store session
    SESSIONS[session_token] = {
        'user_id': user_id,
        'expires_at': expires_at,
        'refresh_token': refresh_token
    }
    
    # Store refresh token
    refresh_expires = datetime.utcnow() + timedelta(days=REFRESH_EXPIRE_DAYS)
    REFRESH_TOKENS[refresh_token] = {
        'user_id': user_id,
        'expires_at': refresh_expires,
        'session_token': session_token
    }
    
    return session_token, refresh_token, expires_at


def validate_session(session_token: str) -> Optional[dict]:
    """Validate session token and return session data"""
    session = SESSIONS.get(session_token)
    if not session:
        return None
    
    # Check expiration
    if datetime.utcnow() > session['expires_at']:
        # Session expired, remove it
        del SESSIONS[session_token]
        return None
    
    return session


def invalidate_session(session_token: str):
    """Invalidate a session"""
    session = SESSIONS.get(session_token)
    if session:
        # Remove refresh token
        refresh_token = session.get('refresh_token')
        if refresh_token and refresh_token in REFRESH_TOKENS:
            del REFRESH_TOKENS[refresh_token]
        # Remove session
        del SESSIONS[session_token]


class AuthServiceServicer(auth_pb2_grpc.AuthServiceServicer):
    """gRPC Authentication Service Implementation"""
    
    def get_db(self) -> DBSession:
        """Get database session"""
        return SessionLocal()
    
    def Register(self, request, context):
        """Register a new user"""
        db = self.get_db()
        try:
            # Validate input
            if not request.email or not request.username or not request.password:
                return auth_pb2.AuthResponse(
                    success=False,
                    message="Email, username, and password are required"
                )
            
            if len(request.password) < 8:
                return auth_pb2.AuthResponse(
                    success=False,
                    message="Password must be at least 8 characters"
                )
            
            # Check if email exists
            existing_email = db.query(User).filter(User.email == request.email).first()
            if existing_email:
                return auth_pb2.AuthResponse(
                    success=False,
                    message="Email already registered"
                )
            
            # Check if username exists
            existing_username = db.query(User).filter(User.username == request.username).first()
            if existing_username:
                return auth_pb2.AuthResponse(
                    success=False,
                    message="Username already taken"
                )
            
            # Create new user
            password_hash = get_password_hash(request.password)
            new_user = User(
                email=request.email,
                username=request.username,
                password_hash=password_hash,
                full_name=request.full_name if request.full_name else None,
                is_active=True,
                is_verified=False
            )
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            # Create default preferences
            preferences = UserPreference(
                user_id=new_user.id,
                theme="dark",
                default_sources=["arxiv", "semantic_scholar", "springer"]
            )
            db.add(preferences)
            db.commit()
            
            # Create session
            session_token, refresh_token, expires_at = create_session(new_user.id)
            
            return auth_pb2.AuthResponse(
                success=True,
                message="User registered successfully",
                session_token=session_token,
                refresh_token=refresh_token,
                expires_at=int(expires_at.timestamp()),
                user=auth_pb2.User(
                    id=new_user.id,
                    email=new_user.email,
                    username=new_user.username,
                    full_name=new_user.full_name or "",
                    avatar_url=new_user.avatar_url or "",
                    is_active=new_user.is_active,
                    is_verified=new_user.is_verified,
                    created_at=int(new_user.created_at.timestamp()) if new_user.created_at else 0,
                    last_login=int(new_user.last_login.timestamp()) if new_user.last_login else 0
                )
            )
        
        except Exception as e:
            return auth_pb2.AuthResponse(
                success=False,
                message=f"Registration failed: {str(e)}"
            )
        finally:
            db.close()
    
    def Login(self, request, context):
        """Login with credentials"""
        db = self.get_db()
        try:
            # Find user by username or email
            user = db.query(User).filter(
                (User.username == request.username) | (User.email == request.username)
            ).first()
            
            if not user:
                return auth_pb2.AuthResponse(
                    success=False,
                    message="Invalid username or password"
                )
            
            # Verify password
            if not verify_password(request.password, user.password_hash):
                return auth_pb2.AuthResponse(
                    success=False,
                    message="Invalid username or password"
                )
            
            # Check if user is active
            if not user.is_active:
                return auth_pb2.AuthResponse(
                    success=False,
                    message="User account is deactivated"
                )
            
            # Update last login
            user.last_login = datetime.utcnow()
            db.commit()
            
            # Create session
            session_token, refresh_token, expires_at = create_session(user.id)
            
            return auth_pb2.AuthResponse(
                success=True,
                message="Login successful",
                session_token=session_token,
                refresh_token=refresh_token,
                expires_at=int(expires_at.timestamp()),
                user=auth_pb2.User(
                    id=user.id,
                    email=user.email,
                    username=user.username,
                    full_name=user.full_name or "",
                    avatar_url=user.avatar_url or "",
                    is_active=user.is_active,
                    is_verified=user.is_verified,
                    created_at=int(user.created_at.timestamp()) if user.created_at else 0,
                    last_login=int(user.last_login.timestamp()) if user.last_login else 0
                )
            )
        
        except Exception as e:
            return auth_pb2.AuthResponse(
                success=False,
                message=f"Login failed: {str(e)}"
            )
        finally:
            db.close()
    
    def ValidateToken(self, request, context):
        """Validate session token"""
        session = validate_session(request.session_token)
        
        if not session:
            return auth_pb2.ValidateTokenResponse(
                valid=False,
                user_id="",
                username="",
                expires_at=0
            )
        
        db = self.get_db()
        try:
            user = db.query(User).filter(User.id == session['user_id']).first()
            
            if not user or not user.is_active:
                return auth_pb2.ValidateTokenResponse(
                    valid=False,
                    user_id="",
                    username="",
                    expires_at=0
                )
            
            return auth_pb2.ValidateTokenResponse(
                valid=True,
                user_id=user.id,
                username=user.username,
                expires_at=int(session['expires_at'].timestamp())
            )
        finally:
            db.close()
    
    def RefreshToken(self, request, context):
        """Refresh session using refresh token"""
        refresh_data = REFRESH_TOKENS.get(request.refresh_token)
        
        if not refresh_data:
            return auth_pb2.AuthResponse(
                success=False,
                message="Invalid refresh token"
            )
        
        # Check expiration
        if datetime.utcnow() > refresh_data['expires_at']:
            del REFRESH_TOKENS[request.refresh_token]
            return auth_pb2.AuthResponse(
                success=False,
                message="Refresh token expired"
            )
        
        db = self.get_db()
        try:
            user = db.query(User).filter(User.id == refresh_data['user_id']).first()
            
            if not user or not user.is_active:
                return auth_pb2.AuthResponse(
                    success=False,
                    message="User not found or inactive"
                )
            
            # Invalidate old session
            old_session_token = refresh_data.get('session_token')
            if old_session_token and old_session_token in SESSIONS:
                del SESSIONS[old_session_token]
            
            # Create new session
            session_token, new_refresh_token, expires_at = create_session(user.id)
            
            # Remove old refresh token
            del REFRESH_TOKENS[request.refresh_token]
            
            return auth_pb2.AuthResponse(
                success=True,
                message="Token refreshed successfully",
                session_token=session_token,
                refresh_token=new_refresh_token,
                expires_at=int(expires_at.timestamp()),
                user=auth_pb2.User(
                    id=user.id,
                    email=user.email,
                    username=user.username,
                    full_name=user.full_name or "",
                    avatar_url=user.avatar_url or "",
                    is_active=user.is_active,
                    is_verified=user.is_verified,
                    created_at=int(user.created_at.timestamp()) if user.created_at else 0,
                    last_login=int(user.last_login.timestamp()) if user.last_login else 0
                )
            )
        finally:
            db.close()
    
    def GetCurrentUser(self, request, context):
        """Get current user information"""
        session = validate_session(request.session_token)
        
        if not session:
            return auth_pb2.UserResponse(
                success=False,
                message="Invalid or expired session"
            )
        
        db = self.get_db()
        try:
            user = db.query(User).filter(User.id == session['user_id']).first()
            
            if not user:
                return auth_pb2.UserResponse(
                    success=False,
                    message="User not found"
                )
            
            return auth_pb2.UserResponse(
                success=True,
                message="User retrieved successfully",
                user=auth_pb2.User(
                    id=user.id,
                    email=user.email,
                    username=user.username,
                    full_name=user.full_name or "",
                    avatar_url=user.avatar_url or "",
                    is_active=user.is_active,
                    is_verified=user.is_verified,
                    created_at=int(user.created_at.timestamp()) if user.created_at else 0,
                    last_login=int(user.last_login.timestamp()) if user.last_login else 0
                )
            )
        finally:
            db.close()
    
    def UpdateUser(self, request, context):
        """Update user profile"""
        session = validate_session(request.session_token)
        
        if not session:
            return auth_pb2.UserResponse(
                success=False,
                message="Invalid or expired session"
            )
        
        db = self.get_db()
        try:
            user = db.query(User).filter(User.id == session['user_id']).first()
            
            if not user:
                return auth_pb2.UserResponse(
                    success=False,
                    message="User not found"
                )
            
            # Update fields
            if request.full_name:
                user.full_name = request.full_name
            if request.avatar_url:
                user.avatar_url = request.avatar_url
            
            db.commit()
            db.refresh(user)
            
            return auth_pb2.UserResponse(
                success=True,
                message="User updated successfully",
                user=auth_pb2.User(
                    id=user.id,
                    email=user.email,
                    username=user.username,
                    full_name=user.full_name or "",
                    avatar_url=user.avatar_url or "",
                    is_active=user.is_active,
                    is_verified=user.is_verified,
                    created_at=int(user.created_at.timestamp()) if user.created_at else 0,
                    last_login=int(user.last_login.timestamp()) if user.last_login else 0
                )
            )
        finally:
            db.close()
    
    def Logout(self, request, context):
        """Logout user (invalidate session)"""
        invalidate_session(request.session_token)
        
        return auth_pb2.LogoutResponse(
            success=True,
            message="Logged out successfully"
        )
    
    def ChangePassword(self, request, context):
        """Change user password"""
        session = validate_session(request.session_token)
        
        if not session:
            return auth_pb2.StatusResponse(
                success=False,
                message="Invalid or expired session"
            )
        
        db = self.get_db()
        try:
            user = db.query(User).filter(User.id == session['user_id']).first()
            
            if not user:
                return auth_pb2.StatusResponse(
                    success=False,
                    message="User not found"
                )
            
            # Verify old password
            if not verify_password(request.old_password, user.password_hash):
                return auth_pb2.StatusResponse(
                    success=False,
                    message="Incorrect old password"
                )
            
            # Validate new password
            if len(request.new_password) < 8:
                return auth_pb2.StatusResponse(
                    success=False,
                    message="New password must be at least 8 characters"
                )
            
            # Update password
            user.password_hash = get_password_hash(request.new_password)
            db.commit()
            
            # Invalidate all sessions for this user
            for token, sess in list(SESSIONS.items()):
                if sess['user_id'] == user.id:
                    invalidate_session(token)
            
            return auth_pb2.StatusResponse(
                success=True,
                message="Password changed successfully. Please login again."
            )
        finally:
            db.close()


def serve(port=50051):
    """Start the gRPC server"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    auth_pb2_grpc.add_AuthServiceServicer_to_server(
        AuthServiceServicer(), server
    )
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    print(f'🚀 gRPC Authentication Server started on port {port}')
    server.wait_for_termination()


if __name__ == '__main__':
    serve()
