"""
SQLAlchemy ORM models for the Autonomous Research Agent.
Defines database schema for users, papers, searches, and more.
"""

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, 
    DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from api.database import Base
import uuid

# UUID generator that works with both SQLite and PostgreSQL
def get_uuid():
    return str(uuid.uuid4())

# User Model
class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=get_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    avatar_url = Column(Text)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # Relationships
    research_jobs = relationship("ResearchJob", back_populates="user", cascade="all, delete-orphan")
    saved_searches = relationship("SavedSearch", back_populates="user", cascade="all, delete-orphan")
    saved_papers = relationship("SavedPaper", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.username} ({self.email})>"

# Research Job Model
class ResearchJob(Base):
    __tablename__ = "research_jobs"
    
    id = Column(String(36), primary_key=True, default=get_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    query = Column(Text, nullable=False)
    status = Column(String(50), default="pending", index=True)
    progress = Column(Integer, default=0)
    total_papers = Column(Integer, default=0)
    processing_time = Column(Float)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="research_jobs")
    papers = relationship("ResearchJobPaper", back_populates="job", cascade="all, delete-orphan")
    analysis_results = relationship("AnalysisResult", back_populates="job", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ResearchJob {self.id} - {self.status}>"

# Paper Model
class Paper(Base):
    __tablename__ = "papers"
    
    id = Column(String(255), primary_key=True)
    title = Column(Text, nullable=False)
    abstract = Column(Text)
    authors = Column(JSON)
    year = Column(Integer, index=True)
    citations = Column(Integer, default=0, index=True)
    url = Column(Text)
    source = Column(String(50), index=True)
    doi = Column(String(255))
    pdf_url = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    job_associations = relationship("ResearchJobPaper", back_populates="paper")
    saved_by_users = relationship("SavedPaper", back_populates="paper")
    summary = relationship("PaperSummary", back_populates="paper", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Paper {self.id}: {self.title[:50]}...>"

# Research Job Papers (many-to-many)
class ResearchJobPaper(Base):
    __tablename__ = "research_job_papers"
    
    id = Column(String(36), primary_key=True, default=get_uuid)
    job_id = Column(String(36), ForeignKey("research_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    paper_id = Column(String(255), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True)
    relevance_score = Column(Float, index=True)
    rank = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    job = relationship("ResearchJob", back_populates="papers")
    paper = relationship("Paper", back_populates="job_associations")
    
    def __repr__(self):
        return f"<ResearchJobPaper job={self.job_id} paper={self.paper_id}>"

# Saved Search Model
class SavedSearch(Base):
    __tablename__ = "saved_searches"
    
    id = Column(String(36), primary_key=True, default=get_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    query = Column(Text, nullable=False)
    filters = Column(JSON)
    is_favorite = Column(Boolean, default=False, index=True)
    search_count = Column(Integer, default=0)
    last_searched = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="saved_searches")
    
    def __repr__(self):
        return f"<SavedSearch {self.name} by user {self.user_id}>"

# Saved Paper Model
class SavedPaper(Base):
    __tablename__ = "saved_papers"
    
    id = Column(String(36), primary_key=True, default=get_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    paper_id = Column(String(255), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True)
    folder = Column(String(255), default="default", index=True)
    notes = Column(Text)
    tags = Column(JSON)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="saved_papers")
    paper = relationship("Paper", back_populates="saved_by_users")
    
    def __repr__(self):
        return f"<SavedPaper user={self.user_id} paper={self.paper_id}>"

# Paper Summary Model
class PaperSummary(Base):
    __tablename__ = "paper_summaries"
    
    id = Column(String(36), primary_key=True, default=get_uuid)
    paper_id = Column(String(255), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    summary = Column(Text, nullable=False)
    key_findings = Column(JSON)
    methodology = Column(Text)
    model_used = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    paper = relationship("Paper", back_populates="summary")
    
    def __repr__(self):
        return f"<PaperSummary for paper {self.paper_id}>"

# Analysis Result Model
class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    
    id = Column(String(36), primary_key=True, default=get_uuid)
    job_id = Column(String(36), ForeignKey("research_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    paper_ids = Column(JSON)
    synthesis = Column(Text)
    trends = Column(JSON)
    recommendations = Column(JSON)
    metadata = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    job = relationship("ResearchJob", back_populates="analysis_results")
    
    def __repr__(self):
        return f"<AnalysisResult for job {self.job_id}>"

# Chat History Model
class ChatHistory(Base):
    __tablename__ = "chat_history"
    
    id = Column(String(36), primary_key=True, default=get_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    session_id = Column(String(36), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    context = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<ChatHistory {self.role}: {self.message[:30]}...>"

# User Preferences Model
class UserPreference(Base):
    __tablename__ = "user_preferences"
    
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    theme = Column(String(20), default="dark")
    default_sources = Column(JSON, default=list)
    notifications_enabled = Column(Boolean, default=True)
    email_notifications = Column(Boolean, default=False)
    search_history_enabled = Column(Boolean, default=True)
    auto_save_searches = Column(Boolean, default=False)
    preferences = Column(JSON)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="preferences")
    
    def __repr__(self):
        return f"<UserPreference for user {self.user_id}>"

# API Key Model (Phase 3)
class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(String(36), primary_key=True, default=get_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    key_hash = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    scopes = Column(JSON)
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<APIKey {self.name} for user {self.user_id}>"
