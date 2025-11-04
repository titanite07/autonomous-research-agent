"""
History API routes
Handles search history and tracking
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict
from datetime import datetime, timedelta
import uuid

from api.database import get_db
from api.db_models import SearchHistory, Paper

router = APIRouter()

@router.get("/history")
async def get_search_history(
    limit: int = 50,
    status: str = None,
    db: Session = Depends(get_db)
):
    """
    Get search history
    
    - **limit**: Maximum number of records to return
    - **status**: Filter by status (completed, processing, failed)
    """
    
    try:
        # Query database for search history
        query = db.query(SearchHistory)
        
        # Filter by status if provided
        if status:
            query = query.filter(SearchHistory.status == status)
        
        # Order by created_at (newest first) and apply limit
        searches = query.order_by(SearchHistory.created_at.desc()).limit(limit).all()
        
        # Convert to response format
        history_list = []
        for search in searches:
            # Get paper count for this search
            paper_count = len(search.papers) if search.papers else 0
            
            # Get sources from papers
            sources = list(set(paper.source for paper in search.papers)) if search.papers else []
            
            history_item = {
                "id": search.id,
                "job_id": search.job_id,
                "query": search.query,
                "max_results": search.max_results,
                "sources": sources,
                "created_at": search.created_at.isoformat() if search.created_at else datetime.utcnow().isoformat(),
                "completed_at": search.completed_at.isoformat() if search.completed_at else None,
                "status": search.status,
                "paper_count": paper_count
            }
            history_list.append(history_item)
        
        return {
            "history": history_list,
            "total": len(history_list),
            "filtered": status is not None
        }
        
    except Exception as e:
        print(f"❌ Error fetching history: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{job_id}")
async def get_history_item(job_id: str, db: Session = Depends(get_db)):
    """Get a specific history item by job_id"""
    
    try:
        # Query database for the search history
        search = db.query(SearchHistory).filter(SearchHistory.job_id == job_id).first()
        
        if not search:
            raise HTTPException(status_code=404, detail="History item not found")
        
        # Get paper count and sources
        paper_count = len(search.papers) if search.papers else 0
        sources = list(set(paper.source for paper in search.papers)) if search.papers else []
        
        return {
            "id": search.id,
            "job_id": search.job_id,
            "query": search.query,
            "max_results": search.max_results,
            "sources": sources,
            "created_at": search.created_at.isoformat() if search.created_at else datetime.utcnow().isoformat(),
            "completed_at": search.completed_at.isoformat() if search.completed_at else None,
            "status": search.status,
            "paper_count": paper_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error fetching history item: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history/{job_id}")
async def delete_history_item(job_id: str, db: Session = Depends(get_db)):
    """Delete a history item"""
    
    try:
        # Query database for the search history
        search = db.query(SearchHistory).filter(SearchHistory.job_id == job_id).first()
        
        if not search:
            raise HTTPException(status_code=404, detail="History item not found")
        
        # Delete the search history (cascade will delete associated papers)
        db.delete(search)
        db.commit()
        
        return {
            "message": "History item deleted successfully",
            "job_id": job_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting history item: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))
