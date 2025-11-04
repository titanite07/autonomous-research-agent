"""
Test suite for FastAPI Auth Routes using gRPC
Tests REST endpoints that integrate with gRPC auth service
"""

import pytest
import sys
import os
from datetime import datetime
from fastapi.testclient import TestClient

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import FastAPI app
from api.main import app

client = TestClient(app)


class TestAuthRoutes:
    """Test FastAPI authentication routes"""
    
    def test_register_endpoint(self):
        """Test POST /auth/register"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        response = client.post("/auth/register", json={
            "email": f"apittest_{timestamp}@example.com",
            "username": f"apiuser_{timestamp}",
            "password": "TestPassword123!",
            "full_name": "API Test User"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        print(f"✓ Register endpoint working: {data['user']['username']}")
    
    def test_register_invalid_email(self):
        """Test registration with invalid email"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        response = client.post("/auth/register", json={
            "email": "invalid-email",
            "username": f"baduser_{timestamp}",
            "password": "TestPassword123!",
            "full_name": "Bad User"
        })
        
        assert response.status_code == 422  # Validation error
        print("✓ Invalid email validation working")
    
    def test_register_short_password(self):
        """Test registration with short password"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        response = client.post("/auth/register", json={
            "email": f"shortpwd_{timestamp}@example.com",
            "username": f"shortpwd_{timestamp}",
            "password": "short",
            "full_name": "Short Password User"
        })
        
        assert response.status_code == 422  # Validation error
        print("✓ Short password validation working")
    
    def test_login_endpoint(self):
        """Test POST /auth/login"""
        # Register a user first
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        username = f"logintest_{timestamp}"
        password = "TestPassword123!"
        
        client.post("/auth/register", json={
            "email": f"{username}@example.com",
            "username": username,
            "password": password,
            "full_name": "Login Test User"
        })
        
        # Now login
        response = client.post("/auth/login", json={
            "username": username,
            "password": password
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["username"] == username
        print(f"✓ Login endpoint working: {username}")
    
    def test_login_wrong_credentials(self):
        """Test login with wrong credentials"""
        response = client.post("/auth/login", json={
            "username": "nonexistent_user",
            "password": "WrongPassword123!"
        })
        
        assert response.status_code == 401
        print("✓ Wrong credentials rejection working")
    
    def test_refresh_token_endpoint(self):
        """Test POST /auth/refresh"""
        # Register and get tokens
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        username = f"refreshtest_{timestamp}"
        
        register_response = client.post("/auth/register", json={
            "email": f"{username}@example.com",
            "username": username,
            "password": "TestPassword123!",
            "full_name": "Refresh Test User"
        })
        
        refresh_token = register_response.json()["refresh_token"]
        
        # Refresh the token
        response = client.post("/auth/refresh", json={
            "refresh_token": refresh_token
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        print(f"✓ Token refresh endpoint working")
    
    def test_get_current_user_endpoint(self):
        """Test GET /auth/me"""
        # Register and get token
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        username = f"metest_{timestamp}"
        email = f"{username}@example.com"
        
        register_response = client.post("/auth/register", json={
            "email": email,
            "username": username,
            "password": "TestPassword123!",
            "full_name": "Me Test User"
        })
        
        access_token = register_response.json()["access_token"]
        
        # Get current user
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == email
        assert data["username"] == username
        print(f"✓ Get current user endpoint working: {username}")
    
    def test_get_current_user_no_token(self):
        """Test GET /auth/me without token"""
        response = client.get("/auth/me")
        
        assert response.status_code == 401
        print("✓ No token rejection working")
    
    def test_verify_token_endpoint(self):
        """Test POST /auth/verify"""
        # Register and get token
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        username = f"verifytest_{timestamp}"
        
        register_response = client.post("/auth/register", json={
            "email": f"{username}@example.com",
            "username": username,
            "password": "TestPassword123!",
            "full_name": "Verify Test User"
        })
        
        access_token = register_response.json()["access_token"]
        
        # Verify the token
        response = client.post(
            "/auth/verify",
            params={"token": access_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == True
        assert data["username"] == username
        print(f"✓ Token verification endpoint working")
    
    def test_logout_endpoint(self):
        """Test POST /auth/logout"""
        # Register and get token
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        username = f"logouttest_{timestamp}"
        
        register_response = client.post("/auth/register", json={
            "email": f"{username}@example.com",
            "username": username,
            "password": "TestPassword123!",
            "full_name": "Logout Test User"
        })
        
        access_token = register_response.json()["access_token"]
        
        # Logout
        response = client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"✓ Logout endpoint working")


class TestAuthIntegration:
    """Integration tests for complete auth flow"""
    
    def test_complete_auth_flow(self):
        """Test complete authentication flow: register -> login -> verify -> refresh -> logout"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        username = f"flowtest_{timestamp}"
        email = f"{username}@example.com"
        password = "TestPassword123!"
        
        # Step 1: Register
        print("\n--- Step 1: Register ---")
        register_response = client.post("/auth/register", json={
            "email": email,
            "username": username,
            "password": password,
            "full_name": "Flow Test User"
        })
        assert register_response.status_code == 201
        register_data = register_response.json()
        access_token = register_data["access_token"]
        refresh_token = register_data["refresh_token"]
        print(f"✓ Registered: {username}")
        
        # Step 2: Verify token
        print("\n--- Step 2: Verify Token ---")
        verify_response = client.post(
            "/auth/verify",
            params={"token": access_token}
        )
        assert verify_response.status_code == 200
        print("✓ Token verified")
        
        # Step 3: Get user info
        print("\n--- Step 3: Get User Info ---")
        me_response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert me_response.status_code == 200
        user_data = me_response.json()
        assert user_data["username"] == username
        print(f"✓ Got user info: {user_data['email']}")
        
        # Step 4: Refresh token
        print("\n--- Step 4: Refresh Token ---")
        refresh_response = client.post("/auth/refresh", json={
            "refresh_token": refresh_token
        })
        assert refresh_response.status_code == 200
        new_access_token = refresh_response.json()["access_token"]
        print("✓ Token refreshed")
        
        # Step 5: Verify new token
        print("\n--- Step 5: Verify New Token ---")
        verify2_response = client.post(
            "/auth/verify",
            params={"token": new_access_token}
        )
        assert verify2_response.status_code == 200
        print("✓ New token verified")
        
        # Step 6: Logout
        print("\n--- Step 6: Logout ---")
        logout_response = client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {new_access_token}"}
        )
        assert logout_response.status_code == 200
        print("✓ Logged out")
        
        print("\n=== Complete auth flow test passed! ===")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
