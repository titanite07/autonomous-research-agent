"""
Database models for the research agent.
Defines tables for searches, papers, reports, and citations.
"""

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from api.database import Base
from datetime import datetime
from typing import List, Dict, Any


class SearchHistory(Base):
    """
    Stores user search queries and metadata.
    """
    __tablename__ = "search_history"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(50), unique=True, index=True, nullable=False)
    query = Column(Text, nullable=False)
    max_results = Column(Integer, default=20)
    sources = Column(JSON)  # List of sources: ["arxiv", "semantic_scholar"]
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    results_count = Column(Integer, default=0)
    avg_relevance = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    papers = relationship("Paper", back_populates="search", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "job_id": self.job_id,
            "query": self.query,
            "max_results": self.max_results,
            "sources": self.sources,
            "status": self.status,
            "results_count": self.results_count,
            "avg_relevance": self.avg_relevance,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class Paper(Base):
    """
    Stores individual paper details from searches.
    """
    __tablename__ = "papers"
    
    id = Column(Integer, primary_key=True, index=True)
    search_id = Column(Integer, ForeignKey("search_history.id"), nullable=False)
    
    # Paper metadata
    title = Column(Text, nullable=False)
    authors = Column(JSON)  # List of author names
    abstract = Column(Text, nullable=True)
    year = Column(Integer, nullable=True)
    url = Column(Text, nullable=True)
    pdf_url = Column(Text, nullable=True)
    doi = Column(String(255), nullable=True)
    arxiv_id = Column(String(50), nullable=True)
    
    # Search-specific fields
    source = Column(String(50), nullable=False)  # arxiv, semantic_scholar, springer
    relevance_score = Column(Float, default=0.0)  # 0-100
    citation_count = Column(Integer, default=0)
    
    # Additional metadata
    keywords = Column(JSON, nullable=True)  # List of keywords
    venue = Column(String(255), nullable=True)  # Conference/Journal name
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    search = relationship("SearchHistory", back_populates="papers")
    citations_as_source = relationship(
        "CitationLink",
        foreign_keys="CitationLink.source_paper_id",
        back_populates="source_paper",
        cascade="all, delete-orphan"
    )
    citations_as_target = relationship(
        "CitationLink",
        foreign_keys="CitationLink.target_paper_id",
        back_populates="target_paper",
        cascade="all, delete-orphan"
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "title": self.title,
            "authors": self.authors,
            "abstract": self.abstract,
            "year": self.year,
            "url": self.url,
            "pdf_url": self.pdf_url,
            "doi": self.doi,
            "arxiv_id": self.arxiv_id,
            "source": self.source,
            "relevance_score": self.relevance_score,
            "citation_count": self.citation_count,
            "keywords": self.keywords,
            "venue": self.venue,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Report(Base):
    """
    Stores generated literature review reports.
    """
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    search_id = Column(Integer, ForeignKey("search_history.id"), nullable=True)
    
    # Report metadata
    title = Column(String(500), nullable=False)
    report_type = Column(String(50), default="literature_review")  # literature_review, summary, comparative
    format = Column(String(20), default="markdown")  # markdown, pdf, latex, html
    
    # Report content
    content = Column(Text, nullable=False)
    executive_summary = Column(Text, nullable=True)
    key_findings = Column(JSON, nullable=True)  # List of key findings
    research_gaps = Column(JSON, nullable=True)  # List of identified gaps
    
    # Metadata
    word_count = Column(Integer, default=0)
    paper_count = Column(Integer, default=0)
    citation_style = Column(String(20), default="APA")  # APA, MLA, Chicago, IEEE, Harvard
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "search_id": self.search_id,
            "title": self.title,
            "report_type": self.report_type,
            "format": self.format,
            "content": self.content,
            "executive_summary": self.executive_summary,
            "key_findings": self.key_findings,
            "research_gaps": self.research_gaps,
            "word_count": self.word_count,
            "paper_count": self.paper_count,
            "citation_style": self.citation_style,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class CitationLink(Base):
    """
    Stores citation relationships between papers.
    Used for building citation networks.
    """
    __tablename__ = "citation_links"
    
    id = Column(Integer, primary_key=True, index=True)
    source_paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False)
    target_paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False)
    
    # Citation metadata
    citation_type = Column(String(50), default="references")  # references, cited_by
    context = Column(Text, nullable=True)  # Text around the citation
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    source_paper = relationship(
        "Paper",
        foreign_keys=[source_paper_id],
        back_populates="citations_as_source"
    )
    target_paper = relationship(
        "Paper",
        foreign_keys=[target_paper_id],
        back_populates="citations_as_target"
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "source_paper_id": self.source_paper_id,
            "target_paper_id": self.target_paper_id,
            "citation_type": self.citation_type,
            "context": self.context,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AnalysisResult(Base):
    """
    Stores analysis results from agent processing.
    Includes summaries, synthesis, and metadata.
    """
    __tablename__ = "analysis_results"
    
    id = Column(Integer, primary_key=True, index=True)
    search_id = Column(Integer, ForeignKey("search_history.id"), nullable=True)
    job_id = Column(String(50), unique=True, index=True, nullable=False)
    
    # Analysis data
    summaries = Column(JSON, nullable=True)  # List of paper summaries
    synthesis = Column(JSON, nullable=True)  # Synthesis results
    citations_data = Column(JSON, nullable=True)  # Citation network data
    knowledge_graph = Column(JSON, nullable=True)  # Knowledge graph data
    
    # Metadata
    total_papers = Column(Integer, default=0)
    analysis_status = Column(String(20), default="completed")  # completed, failed, partial
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "search_id": self.search_id,
            "job_id": self.job_id,
            "summaries": self.summaries,
            "synthesis": self.synthesis,
            "citations_data": self.citations_data,
            "knowledge_graph": self.knowledge_graph,
            "total_papers": self.total_papers,
            "analysis_status": self.analysis_status,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
