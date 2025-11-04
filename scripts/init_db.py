"""
Database initialization script.
Run this to set up the database schema.
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.database import Base, engine, test_connection
from api.models.db_models import (
    User, ResearchJob, Paper, ResearchJobPaper,
    SavedSearch, SavedPaper, PaperSummary,
    AnalysisResult, ChatHistory, UserPreference, APIKey
)

def init_database():
    """Initialize the database by creating all tables"""
    print("🔧 Initializing database...")
    
    # Test connection first
    if not test_connection():
        print("❌ Failed to connect to database")
        print("📝 Make sure DATABASE_URL environment variable is set correctly")
        return False
    
    print("✅ Database connection successful")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully")
        
        # Print created tables
        print("\n📊 Created tables:")
        for table in Base.metadata.sorted_tables:
            print(f"  - {table.name}")
        
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

if __name__ == "__main__":
    success = init_database()
    if success:
        print("\n🎉 Database initialization complete!")
        print("\n💡 Next steps:")
        print("  1. Start the backend: uvicorn api.main:app --reload")
        print("  2. Visit http://localhost:8000/docs for API documentation")
        print("  3. Start the frontend: cd frontend && npm run dev")
    else:
        print("\n❌ Database initialization failed")
        sys.exit(1)
