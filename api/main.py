"""
FastAPI Backend for AutoGen Research Agent
Serves the Next.js frontend and provides API endpoints for research operations
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os

from api.routes import search, analysis, websocket, history, analytics, reports, chat, auth
from api.middleware.auth import add_auth_middleware
from api.database import init_db, check_db_connection

# Create FastAPI app
app = FastAPI(
    title="AutoGen Research API",
    description="API for autonomous research agent with multi-agent AI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now (restrict in production)
    allow_credentials=False,  # Must be False when allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
# add_auth_middleware(app)  # Uncomment when auth is implemented

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(search.router, prefix="/api/v1", tags=["search"])
app.include_router(analysis.router, prefix="/api/v1", tags=["analysis"])
app.include_router(history.router, prefix="/api/v1", tags=["history"])
app.include_router(analytics.router, prefix="/api/v1", tags=["analytics"])
app.include_router(reports.router, prefix="/api/v1", tags=["reports"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - API status"""
    return {
        "name": "AutoGen Research API",
        "version": "1.0.0",
        "status": "healthy",
        "docs": "/docs",
        "frontend": "http://localhost:3000"
    }

# Health check endpoint
@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint for monitoring"""
    # Check Groq API connection
    groq_status = "connected" if os.getenv("GROQ_API_KEY") else "not_configured"
    
    # Check database connection
    db_status = "connected" if check_db_connection() else "disconnected"
    
    # Overall health
    overall_status = "healthy" if db_status == "connected" else "degraded"
    
    return {
        "status": overall_status,
        "service": "autogen-research-api",
        "groq_api": groq_status,
        "database": db_status,
        "autogen": "ready"
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "type": type(exc).__name__
        }
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    print("🚀 AutoGen Research API starting...")
    print("📝 API Docs available at: http://localhost:8000/docs")
    print("🌐 Frontend should connect to: http://localhost:8000")
    
    # Initialize database
    try:
        init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
    
    # Check connections
    if check_db_connection():
        print("✅ Database connection: OK")
    else:
        print("⚠️  Database connection: FAILED")
    
    if os.getenv("GROQ_API_KEY"):
        print("✅ Groq API key: Configured")
    else:
        print("⚠️  Groq API key: Not found")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    print("👋 AutoGen Research API shutting down...")
    
    # Close database connections
    from api.database import engine
    try:
        engine.dispose()
        print("✅ Database connections closed")
    except Exception as e:
        print(f"⚠️  Error closing database: {e}")

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload for development
        log_level="info",
        timeout_keep_alive=300,  # 5 minutes keep-alive timeout
        timeout_notify=300,  # 5 minutes notification timeout
        limit_concurrency=100,  # Max concurrent connections
        limit_max_requests=1000  # Max requests before worker restart
    )
