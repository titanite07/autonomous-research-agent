"""
Test suite for gRPC Authentication Server
Tests all auth service methods directly via gRPC
"""

import pytest
import grpc
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from grpc_generated import auth_pb2, auth_pb2_grpc


class TestGRPCAuthServer:
    """Test gRPC authentication server methods"""
    
    @pytest.fixture(scope="class")
    def grpc_channel(self):
        """Create gRPC channel for testing"""
        channel = grpc.insecure_channel('localhost:50051')
        yield channel
        channel.close()
    
    @pytest.fixture(scope="class")
    def auth_stub(self, grpc_channel):
        """Create auth service stub"""
        return auth_pb2_grpc.AuthServiceStub(grpc_channel)
    
    def test_register_new_user(self, auth_stub):
        """Test user registration"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        request = auth_pb2.RegisterRequest(
            email=f"test_{timestamp}@example.com",
            username=f"testuser_{timestamp}",
            password="TestPassword123!",
            full_name="Test User"
        )
        
        response = auth_stub.Register(request)
        
        assert response.success == True
        assert response.session_token != ""
        assert response.refresh_token != ""
        assert response.user.email == request.email
        assert response.user.username == request.username
        print(f"✓ Registration successful: {response.user.username}")
    
    def test_register_duplicate_email(self, auth_stub):
        """Test registration with duplicate email"""
        # First registration
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        email = f"duplicate_{timestamp}@example.com"
        
        request1 = auth_pb2.RegisterRequest(
            email=email,
            username=f"user1_{timestamp}",
            password="TestPassword123!",
            full_name="User One"
        )
        response1 = auth_stub.Register(request1)
        assert response1.success == True
        
        # Try to register with same email
        request2 = auth_pb2.RegisterRequest(
            email=email,
            username=f"user2_{timestamp}",
            password="TestPassword123!",
            full_name="User Two"
        )
        
        response2 = auth_stub.Register(request2)
        assert response2.success == False
        assert "already" in response2.message.lower() or "exists" in response2.message.lower()
        print("✓ Duplicate email rejection working")
    
    def test_login_success(self, auth_stub):
        """Test successful login"""
        # Register a user first
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        username = f"loginuser_{timestamp}"
        password = "TestPassword123!"
        
        register_req = auth_pb2.RegisterRequest(
            email=f"{username}@example.com",
            username=username,
            password=password,
            full_name="Login Test User"
        )
        auth_stub.Register(register_req)
        
        # Now try to login
        login_req = auth_pb2.LoginRequest(
            username=username,
            password=password
        )
        
        response = auth_stub.Login(login_req)
        
        assert response.success == True
        assert response.session_token != ""
        assert response.refresh_token != ""
        assert response.user.username == username
        print(f"✓ Login successful: {username}")
    
    def test_login_wrong_password(self, auth_stub):
        """Test login with wrong password"""
        # Register a user first
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        username = f"wrongpwd_{timestamp}"
        
        register_req = auth_pb2.RegisterRequest(
            email=f"{username}@example.com",
            username=username,
            password="CorrectPassword123!",
            full_name="Test User"
        )
        auth_stub.Register(register_req)
        
        # Try login with wrong password
        login_req = auth_pb2.LoginRequest(
            username=username,
            password="WrongPassword123!"
        )
        
        response = auth_stub.Login(login_req)
        assert response.success == False
        assert "password" in response.message.lower() or "invalid" in response.message.lower()
        print("✓ Wrong password rejection working")
    
    def test_validate_token_valid(self, auth_stub):
        """Test token validation with valid token"""
        # Register and get token
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        username = f"tokenuser_{timestamp}"
        
        register_req = auth_pb2.RegisterRequest(
            email=f"{username}@example.com",
            username=username,
            password="TestPassword123!",
            full_name="Token Test User"
        )
        register_response = auth_stub.Register(register_req)
        session_token = register_response.session_token
        
        # Validate the token
        validate_req = auth_pb2.ValidateTokenRequest(session_token=session_token)
        response = auth_stub.ValidateToken(validate_req)
        
        assert response.valid == True
        assert response.user_id != ""
        assert response.username == username
        print(f"✓ Token validation successful for: {username}")
    
    def test_validate_token_invalid(self, auth_stub):
        """Test token validation with invalid token"""
        validate_req = auth_pb2.ValidateTokenRequest(session_token="invalid_token_12345")
        
        response = auth_stub.ValidateToken(validate_req)
        assert response.valid == False
        print("✓ Invalid token rejection working")
    
    def test_refresh_token_success(self, auth_stub):
        """Test token refresh with valid refresh token"""
        # Register and get tokens
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        username = f"refreshuser_{timestamp}"
        
        register_req = auth_pb2.RegisterRequest(
            email=f"{username}@example.com",
            username=username,
            password="TestPassword123!",
            full_name="Refresh Test User"
        )
        register_response = auth_stub.Register(register_req)
        refresh_token = register_response.refresh_token
        
        # Refresh the token
        refresh_req = auth_pb2.RefreshTokenRequest(refresh_token=refresh_token)
        response = auth_stub.RefreshToken(refresh_req)
        
        assert response.success == True
        assert response.session_token != ""
        assert response.refresh_token != ""
        print(f"✓ Token refresh successful for: {username}")
    
    def test_refresh_token_invalid(self, auth_stub):
        """Test token refresh with invalid refresh token"""
        refresh_req = auth_pb2.RefreshTokenRequest(refresh_token="invalid_refresh_token")
        
        response = auth_stub.RefreshToken(refresh_req)
        assert response.success == False
        assert "invalid" in response.message.lower()
        print("✓ Invalid refresh token rejection working")
    
    def test_get_current_user(self, auth_stub):
        """Test getting current user info"""
        # Register and get token
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        username = f"getuser_{timestamp}"
        email = f"{username}@example.com"
        full_name = "Get User Test"
        
        register_req = auth_pb2.RegisterRequest(
            email=email,
            username=username,
            password="TestPassword123!",
            full_name=full_name
        )
        register_response = auth_stub.Register(register_req)
        session_token = register_response.session_token
        
        # Get user info
        get_user_req = auth_pb2.GetCurrentUserRequest(session_token=session_token)
        response = auth_stub.GetCurrentUser(get_user_req)
        
        assert response.success == True
        assert response.user.email == email
        assert response.user.username == username
        assert response.user.full_name == full_name
        print(f"✓ Get current user successful: {username}")
    
    def test_logout_success(self, auth_stub):
        """Test logout"""
        # Register and get token
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        username = f"logoutuser_{timestamp}"
        
        register_req = auth_pb2.RegisterRequest(
            email=f"{username}@example.com",
            username=username,
            password="TestPassword123!",
            full_name="Logout Test User"
        )
        register_response = auth_stub.Register(register_req)
        session_token = register_response.session_token
        
        # Logout
        logout_req = auth_pb2.LogoutRequest(session_token=session_token)
        response = auth_stub.Logout(logout_req)
        
        assert response.success == True
        
        # Try to use the token after logout (should be invalid)
        validate_req = auth_pb2.ValidateTokenRequest(session_token=session_token)
        validate_response = auth_stub.ValidateToken(validate_req)
        assert validate_response.valid == False
        
        print(f"✓ Logout successful: {username}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
