"""
Search API routes
Handles paper search requests with database persistence
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Dict
import uuid
from datetime import datetime

from api.models import SearchRequest, SearchResponse, PaperModel
from api.services.research_service import ResearchService
from api.database import get_db
from api.db_models import SearchHistory, Paper as PaperDB

router = APIRouter()

@router.post("/search", response_model=Dict)
async def search_papers(
    request: SearchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Submit a research query for processing
    
    - **query**: Research query string
    - **max_results**: Maximum number of papers (1-50)
    - **sources**: List of sources ["arxiv", "semantic_scholar"]
    - **dedup_threshold**: Semantic deduplication threshold (0.05-0.30)
    - **full_text**: Enable full-text PDF analysis
    
    Returns a job_id to check status and retrieve results
    """
    
    try:
        # Log the incoming request
        print(f"📥 Received search request: {request.query}")
        print(f"   Max results: {request.max_results}")
        print(f"   Sources: {request.sources}")
        
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Create database entry
        search_history = SearchHistory(
            job_id=job_id,
            query=request.query,
            max_results=request.max_results or 10,
            sources=request.sources,
            status="processing"
        )
        db.add(search_history)
        db.commit()
        db.refresh(search_history)
        
        # Start background task
        background_tasks.add_task(
            process_search,
            job_id=job_id,
            request=request
        )
        
        return {
            "job_id": job_id,
            "status": "processing",
            "message": "Search started. Use /api/v1/status/{job_id} to check progress.",
            "estimated_time": f"{(request.max_results or 10) * 3}s"  # Rough estimate
        }
        
    except Exception as e:
        print(f"❌ Error in search endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_search(job_id: str, request: SearchRequest):
    """Background task to process search with WebSocket updates"""
    from api.database import SessionLocal
    from api.routes.websocket import send_progress_update
    
    db = SessionLocal()
    
    try:
        # Get search history entry
        search_history = db.query(SearchHistory).filter(SearchHistory.job_id == job_id).first()
        if not search_history:
            return
        
        # Send search started event (non-blocking)
        try:
            await send_progress_update(job_id, "search_started", {
                "query": request.query,
                "message": f"Starting search for: {request.query}"
            })
        except Exception:
            pass  # WebSocket not connected, continue anyway
        
        # Initialize research service
        service = ResearchService()
        
        # Send searching event (non-blocking)
        try:
            await send_progress_update(job_id, "searching", {
                "message": f"Searching across {len(request.sources)} sources...",
                "sources": request.sources
            })
        except Exception:
            pass
        
        # Perform search
        results = await service.search_papers(
            query=request.query,
            max_results=request.max_results,
            sources=request.sources,
            dedup_threshold=request.dedup_threshold
        )
        
        # Send papers found event (non-blocking)
        if results and "papers" in results:
            try:
                await send_progress_update(job_id, "papers_found", {
                    "count": len(results["papers"]),
                    "message": f"Found {len(results['papers'])} papers"
                })
            except Exception:
                pass
        
        # Store papers in database
        if results and "papers" in results:
            papers_data = results["papers"]
            total_relevance = 0.0
            
            # Send processing event (non-blocking)
            try:
                await send_progress_update(job_id, "processing", {
                    "message": "Processing and scoring papers...",
                    "total": len(papers_data)
                })
            except Exception:
                pass
            
            for idx, paper_data in enumerate(papers_data):
                paper = PaperDB(
                    search_id=search_history.id,
                    title=paper_data.get("title", ""),
                    authors=paper_data.get("authors", []),
                    abstract=paper_data.get("abstract", ""),
                    year=paper_data.get("year"),
                    url=paper_data.get("url"),
                    pdf_url=paper_data.get("pdf_url"),
                    doi=paper_data.get("doi"),
                    arxiv_id=paper_data.get("arxiv_id"),
                    source=paper_data.get("source", "unknown"),
                    relevance_score=paper_data.get("relevance_score", 0.0),
                    citation_count=paper_data.get("citation_count", 0),
                    keywords=paper_data.get("keywords", []),
                    venue=paper_data.get("venue")
                )
                db.add(paper)
                total_relevance += paper_data.get("relevance_score", 0.0)
                
                # Send progress update every 5 papers (non-blocking)
                if (idx + 1) % 5 == 0:
                    try:
                        await send_progress_update(job_id, "progress", {
                            "processed": idx + 1,
                            "total": len(papers_data),
                            "message": f"Processed {idx + 1}/{len(papers_data)} papers"
                        })
                    except Exception:
                        pass
            
            # Update search history
            search_history.status = "completed"
            search_history.results_count = len(papers_data)
            search_history.avg_relevance = total_relevance / len(papers_data) if papers_data else 0.0
            search_history.completed_at = datetime.now()
            
            # Send completion event (non-blocking)
            try:
                await send_progress_update(job_id, "completed", {
                    "message": "Search completed successfully!",
                    "total_papers": len(papers_data),
                    "avg_relevance": search_history.avg_relevance
                })
            except Exception:
                pass
        else:
            search_history.status = "completed"
            search_history.results_count = 0
            search_history.completed_at = datetime.now()
            
            try:
                await send_progress_update(job_id, "completed", {
                    "message": "Search completed with no results",
                    "total_papers": 0
                })
            except Exception:
                pass
        
        db.commit()
        
    except Exception as e:
        # Update status to failed
        try:
            search_history = db.query(SearchHistory).filter(SearchHistory.job_id == job_id).first()
            if search_history:
                search_history.status = "failed"
                search_history.error_message = str(e)
                search_history.completed_at = datetime.now()
                db.commit()
                
                # Send error event (non-blocking)
                try:
                    await send_progress_update(job_id, "error", {
                        "message": f"Search failed: {str(e)}"
                    })
                except Exception:
                    pass
        except:
            pass
    finally:
        db.close()

@router.get("/status/{job_id}")
async def get_search_status(job_id: str, db: Session = Depends(get_db)):
    """
    Get the status of a search job
    
    - **job_id**: The job ID returned from /search
    
    Returns current status, progress, and results if completed
    """
    
    search_history = db.query(SearchHistory).filter(SearchHistory.job_id == job_id).first()
    
    if not search_history:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Calculate progress based on status
    progress = 0.0
    if search_history.status == "processing":
        progress = 0.5
    elif search_history.status == "completed":
        progress = 1.0
    
    return {
        "job_id": job_id,
        "status": search_history.status,
        "progress": progress,
        "query": search_history.query,
        "created_at": search_history.created_at.isoformat() if search_history.created_at else None,
        "error": search_history.error_message,
        "results_available": search_history.status == "completed"
    }

@router.get("/results/{job_id}", response_model=Dict)
async def get_search_results(job_id: str, db: Session = Depends(get_db)):
    """
    Get the results of a completed search job
    
    - **job_id**: The job ID returned from /search
    
    Returns the full search results including papers, metadata, etc.
    """
    
    search_history = db.query(SearchHistory).filter(SearchHistory.job_id == job_id).first()
    
    if not search_history:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if search_history.status == "processing":
        raise HTTPException(
            status_code=202,
            detail="Search is still processing. Check /status/{job_id} for progress."
        )
    
    if search_history.status == "failed":
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {search_history.error_message or 'Unknown error'}"
        )
    
    # Get papers from database
    papers = db.query(PaperDB).filter(PaperDB.search_id == search_history.id).all()
    
    return {
        "job_id": job_id,
        "status": search_history.status,
        "query": search_history.query,
        "results": {
            "papers": [paper.to_dict() for paper in papers],
            "total_count": len(papers),
            "avg_relevance": search_history.avg_relevance,
            "sources": search_history.sources
        },
        "created_at": search_history.created_at.isoformat() if search_history.created_at else None,
        "completed_at": search_history.completed_at.isoformat() if search_history.completed_at else None
    }

@router.delete("/results/{job_id}")
async def delete_search_results(job_id: str, db: Session = Depends(get_db)):
    """
    Delete search results from database
    
    - **job_id**: The job ID to delete
    """
    
    search_history = db.query(SearchHistory).filter(SearchHistory.job_id == job_id).first()
    
    if not search_history:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Delete will cascade to papers
    db.delete(search_history)
    db.commit()
    
    return {
        "message": "Search results deleted successfully",
        "job_id": job_id
    }
