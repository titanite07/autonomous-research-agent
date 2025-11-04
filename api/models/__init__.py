"""
Pydantic models for API request/response validation
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# Search Request/Response Models

class SearchRequest(BaseModel):
    """Request model for paper search"""
    query: str = Field(..., description="Research query string", min_length=1)
    max_results: Optional[int] = Field(default=10, description="Maximum number of papers")
    sources: Optional[List[str]] = Field(default=None, description="Search sources")
    dedup_threshold: Optional[float] = Field(default=0.15, description="Deduplication threshold")
    full_text: Optional[bool] = Field(default=False, description="Enable full-text analysis")
    
    class Config:
        # Allow extra fields to be ignored
        extra = "ignore"

class PaperModel(BaseModel):
    """Model for a research paper"""
    id: str
    title: str
    authors: List[str]
    abstract: str
    year: Optional[int] = None
    url: Optional[str] = None
    pdf_url: Optional[str] = None
    citation_count: int = 0
    relevance_score: float = 0.0
    source: str  # "arxiv", "semantic_scholar", etc.
    venue: Optional[str] = None
    doi: Optional[str] = None

class SearchResponse(BaseModel):
    """Response model for paper search"""
    job_id: str
    status: str  # "processing", "completed", "failed"
    query: str
    total_papers: int
    papers: List[PaperModel]
    processing_time: float
    timestamp: datetime

# Analysis Request/Response Models

class AnalysisRequest(BaseModel):
    """Request model for paper analysis"""
    paper_ids: List[int] = Field(..., min_length=1, description="List of database paper IDs to analyze")
    analysis_type: str = Field(default="comprehensive", description="Type of analysis")
    include_citations: bool = Field(default=True, description="Include citation network")
    include_knowledge_graph: bool = Field(default=True, description="Build knowledge graph")
    job_id: Optional[str] = Field(default=None, description="WebSocket job ID for real-time updates")

class AnalysisResponse(BaseModel):
    """Response model for analysis results"""
    job_id: str
    status: str
    analysis_type: str
    summary: str
    key_findings: List[str]
    research_gaps: List[str]
    citation_network: Optional[Dict[str, Any]] = None
    knowledge_graph: Optional[Dict[str, Any]] = None
    timestamp: datetime

# Agent Status Models

class AgentStatus(BaseModel):
    """Model for agent status"""
    agent_name: str
    status: str  # "idle", "working", "completed", "error"
    current_task: Optional[str] = None
    progress: float = 0.0  # 0.0 to 1.0
    tokens_used: int = 0
    messages: List[str] = []

class ResearchStatus(BaseModel):
    """Model for overall research status"""
    job_id: str
    status: str
    progress: float
    agents: List[AgentStatus]
    current_phase: str
    timestamp: datetime

# Export Models

class ExportRequest(BaseModel):
    """Request model for report export"""
    job_id: str
    format: str = Field(..., description="Export format: pdf, docx, latex, markdown")
    include_citations: bool = True
    include_graphs: bool = True

class ExportResponse(BaseModel):
    """Response model for export"""
    job_id: str
    format: str
    download_url: str
    file_size: int
    timestamp: datetime

# Error Models

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime
