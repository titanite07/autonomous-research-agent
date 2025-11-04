# gRPC Authentication Testing Guide

## Prerequisites

Ensure all dependencies are installed:

```bash
pip install -r requirements.txt
```

## 1. Start the Services

### Option A: Using the startup script (Recommended)

```bash
python start_services.py
```

This will start both:
- gRPC Authentication Server (port 50051)
- FastAPI REST API (port 8000)

### Option B: Start services individually

**Terminal 1 - gRPC Server:**
```bash
python -m api.grpc_services.auth_service
```

**Terminal 2 - FastAPI Server:**
```bash
uvicorn api.main:app --reload --port 8000
```

## 2. Run Tests

### Test gRPC Server Directly

Test the gRPC authentication service:

```bash
pytest tests/test_grpc_auth_server.py -v -s
```

**Tests include:**
- ✓ User registration
- ✓ Duplicate email rejection
- ✓ Login with credentials
- ✓ Wrong password rejection
- ✓ Token validation
- ✓ Token refresh
- ✓ Get user info
- ✓ Logout

### Test FastAPI Routes

Test the REST API endpoints that use gRPC:

```bash
pytest tests/test_auth_routes.py -v -s
```

**Tests include:**
- ✓ POST /auth/register
- ✓ POST /auth/login
- ✓ POST /auth/refresh
- ✓ GET /auth/me
- ✓ POST /auth/verify
- ✓ POST /auth/logout
- ✓ Complete authentication flow

### Run All Tests

```bash
pytest tests/ -v -s
```

## 3. Manual Testing with API Docs

1. Open http://localhost:8000/docs
2. Try the following endpoints:

### Register a User

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "test@example.com",
  "username": "testuser",
  "password": "SecurePass123!",
  "full_name": "Test User"
}
```

Response:
```json
{
  "access_token": "session_token_here",
  "refresh_token": "refresh_token_here",
  "token_type": "bearer",
  "user": {
    "id": "user_id",
    "email": "test@example.com",
    "username": "testuser",
    "full_name": "Test User",
    "is_active": true,
    "is_verified": false
  }
}
```

### Login

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "testuser",
  "password": "SecurePass123!"
}
```

### Get Current User

```http
GET /api/v1/auth/me
Authorization: Bearer <access_token>
```

### Refresh Token

```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "<refresh_token>"
}
```

## 4. Architecture

```
┌─────────────────┐
│  Next.js Client │
└────────┬────────┘
         │ HTTP/REST
         ▼
┌─────────────────┐
│  FastAPI Server │ (Port 8000)
│   (api/main.py) │
└────────┬────────┘
         │ gRPC
         ▼
┌─────────────────────┐
│ gRPC Auth Service   │ (Port 50051)
│ (auth_service.py)   │
└──────────┬──────────┘
           │
           ▼
   ┌───────────────┐
   │  PostgreSQL   │
   └───────────────┘
```

## 5. What's Been Implemented

### gRPC Authentication Service

✅ **Protocol Buffers** (`grpc-protos/auth.proto`)
- Register, Login, ValidateToken, RefreshToken, GetCurrentUser, Logout

✅ **Server Implementation** (`api/grpc_services/auth_service.py`)
- Session-based authentication (stored in memory)
- Password hashing with bcrypt
- 24-hour session tokens
- 7-day refresh tokens
- User validation and error handling

✅ **Client Wrapper** (`api/grpc_client.py`)
- Python client for calling gRPC service
- Used by FastAPI routes
- Error handling and response formatting

### FastAPI Integration

✅ **Auth Routes** (`api/routes/auth.py`)
- REST endpoints that call gRPC service
- Pydantic validation
- JWT-compatible response format

✅ **Main App** (`api/main.py`)
- Routes registered at `/api/v1/auth/*`
- CORS enabled for frontend

### Testing

✅ **gRPC Tests** (`tests/test_grpc_auth_server.py`)
- Direct gRPC service testing
- 12 test cases covering all flows

✅ **API Tests** (`tests/test_auth_routes.py`)
- FastAPI endpoint testing
- Integration tests
- Complete auth flow test

## 6. Next Steps

After successful testing:

1. ✅ Verify all tests pass
2. ⏳ Implement Saved Searches feature
3. ⏳ Add Citation Export (BibTeX/RIS)
4. ⏳ Complete Phase 1 features
5. ⏳ Move to Phase 2 (Redis, Advanced Filters, PWA)

## 7. Troubleshooting

### gRPC Connection Error

If you see "failed to connect to all addresses":
- Ensure gRPC server is running on port 50051
- Check firewall settings
- Try `netstat -an | findstr 50051` to verify port is open

### Import Errors

If you see protobuf import errors:
```bash
# Recompile proto files
python -m grpc_tools.protoc -I./grpc-protos --python_out=./grpc_generated --grpc_python_out=./grpc_generated ./grpc-protos/auth.proto
```

### Database Errors

Ensure PostgreSQL is running and DATABASE_URL is set in `.env`:
```bash
DATABASE_URL=postgresql://localhost/research_agent
```

## 8. Environment Variables

Create `.env` file:

```bash
# Database
DATABASE_URL=postgresql://localhost/research_agent

# gRPC
GRPC_AUTH_HOST=localhost
GRPC_AUTH_PORT=50051

# API Keys (optional for testing)
GROQ_API_KEY=your_groq_api_key
```

---

**Status:** ✅ gRPC Authentication Implementation Complete
**Date:** [Current Date]
**Next:** Run tests and verify all features work correctly
