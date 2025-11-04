# 🚀 Quick Start Guide - Phase 1 Features

## Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+ (or use SQLite for local development)
- Git

---

## 📦 Installation

### 1. Clone & Install Dependencies

```bash
# Backend dependencies
pip install -r requirements.txt

# Frontend dependencies
cd frontend
npm install
cd ..
```

### 2. Set Up Environment Variables

Create `.env` file in the project root:

```env
# Database (choose one)
# Option 1: PostgreSQL (Production)
DATABASE_URL=postgresql://username:password@localhost:5432/research_agent

# Option 2: SQLite (Development - Default)
# DATABASE_URL=sqlite:///./research_agent.db

# Security
SECRET_KEY=your-super-secret-key-min-32-characters-change-this

# API Keys
GROQ_API_KEY=your_groq_api_key_here
SPRINGER_API_KEY=your_springer_api_key_here

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Initialize Database

```bash
# Run database initialization script
python scripts/init_db.py
```

This will create all necessary tables:
- ✅ users
- ✅ research_jobs
- ✅ papers
- ✅ research_job_papers
- ✅ saved_searches
- ✅ saved_papers
- ✅ paper_summaries
- ✅ analysis_results
- ✅ chat_history
- ✅ user_preferences
- ✅ api_keys

---

## 🏃 Running the Application

### Start Backend (Terminal 1)

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at:
- **API:** http://localhost:8000
- **Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Start Frontend (Terminal 2)

```bash
cd frontend
npm run dev
```

Frontend will be available at:
- **App:** http://localhost:3000

---

## 🔐 Testing Authentication

### 1. Register a New User

**Endpoint:** `POST /api/v1/auth/register`

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "securepassword123",
    "full_name": "Test User"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "test@example.com",
    "username": "testuser",
    "full_name": "Test User",
    "is_verified": false
  }
}
```

### 2. Login

**Endpoint:** `POST /api/v1/auth/login`

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "securepassword123"
  }'
```

### 3. Access Protected Endpoint

**Endpoint:** `GET /api/v1/auth/me`

```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4. Refresh Token

**Endpoint:** `POST /api/v1/auth/refresh`

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

---

## 🧪 Testing the Full Workflow

### 1. Search for Papers (No Auth Required)

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning transformers",
    "max_results": 5
  }'
```

### 2. Get Your Profile (Auth Required)

```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 3. Save a Search (Coming in Phase 1.3)

```bash
curl -X POST http://localhost:8000/api/v1/saved-searches \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ML Research",
    "query": "machine learning transformers",
    "is_favorite": true
  }'
```

---

## 🐳 Docker Setup (Optional)

### Using Docker Compose

```bash
# Build and start all services
docker-compose up -d

# Initialize database
docker-compose exec backend python scripts/init_db.py

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Docker Compose Configuration

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: research_agent
      POSTGRES_PASSWORD: password
      POSTGRES_DB: research_agent
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend:
    build: .
    command: uvicorn api.main:app --host 0.0.0.0 --port 8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://research_agent:password@postgres:5432/research_agent
      SECRET_KEY: your-secret-key-here
      GROQ_API_KEY: ${GROQ_API_KEY}
    depends_on:
      - postgres

  frontend:
    build: ./frontend
    command: npm run dev
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000

volumes:
  postgres_data:
```

---

## 📱 Frontend Integration

### Creating Auth Context

Create `frontend/src/contexts/AuthContext.tsx`:

```typescript
'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';

interface User {
  id: string;
  email: string;
  username: string;
  full_name?: string;
  is_verified: boolean;
}

interface AuthContextType {
  user: User | null;
  accessToken: string | null;
  login: (username: string, password: string) => Promise<void>;
  register: (email: string, username: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);

  useEffect(() => {
    // Load token from localStorage on mount
    const token = localStorage.getItem('access_token');
    if (token) {
      setAccessToken(token);
      fetchUser(token);
    }
  }, []);

  const fetchUser = async (token: string) => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/auth/me', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      }
    } catch (error) {
      console.error('Failed to fetch user:', error);
    }
  };

  const login = async (username: string, password: string) => {
    const response = await fetch('http://localhost:8000/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });

    if (!response.ok) throw new Error('Login failed');

    const data = await response.json();
    setAccessToken(data.access_token);
    setUser(data.user);
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
  };

  const register = async (email: string, username: string, password: string) => {
    const response = await fetch('http://localhost:8000/api/v1/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, username, password })
    });

    if (!response.ok) throw new Error('Registration failed');

    const data = await response.json();
    setAccessToken(data.access_token);
    setUser(data.user);
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
  };

  const logout = () => {
    setUser(null);
    setAccessToken(null);
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  };

  return (
    <AuthContext.Provider value={{
      user,
      accessToken,
      login,
      register,
      logout,
      isAuthenticated: !!user
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};
```

---

## 🧩 What's Working Now

### ✅ Completed Features:
1. **User Authentication**
   - Registration with email/username/password
   - Login with JWT tokens
   - Token refresh mechanism
   - Protected routes
   - User profile management

2. **Database Layer**
   - PostgreSQL/SQLite support
   - SQLAlchemy ORM models
   - Migration-ready structure
   - Proper relationships and indexes

3. **Security**
   - Password hashing with bcrypt
   - JWT token generation and validation
   - HTTP Bearer authentication
   - Token expiration handling

### ⏳ Coming Next (Phase 1 Remaining):
1. **Saved Searches** (4-6 hours)
   - Bookmark searches for quick access
   - Favorite searches
   - Re-run saved searches

2. **Citation Export** (3-4 hours)
   - BibTeX format export
   - RIS format export
   - Bulk export functionality

---

## 🐛 Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
pg_isready

# Test connection
psql -U username -d research_agent
```

### Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Port Already in Use

```bash
# Kill process on port 8000
kill -9 $(lsof -t -i:8000)

# Kill process on port 3000
kill -9 $(lsof -t -i:3000)
```

---

## 📚 Next Steps

1. **Try the authentication flow** using the API docs at http://localhost:8000/docs
2. **Implement frontend auth components** using the provided AuthContext
3. **Test protected routes** by adding authentication to existing endpoints
4. **Continue with Phase 1** - implement saved searches and citation export

---

## 🆘 Need Help?

- **API Documentation:** http://localhost:8000/docs
- **Check Logs:** Terminal output for errors
- **Database Issues:** Run `python scripts/init_db.py` again
- **Frontend Issues:** Delete `.next` folder and `node_modules`, reinstall

---

**🎉 You're all set! The authentication system is ready to use.**

For the complete implementation roadmap, see `IMPLEMENTATION_ROADMAP.md`.
