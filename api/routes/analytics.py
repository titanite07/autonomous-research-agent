"""
Analytics API routes
Provides analytics and statistics about research activity
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, List
from datetime import datetime, timedelta
from collections import Counter

from api.database import get_db
from api.db_models import SearchHistory, Paper

router = APIRouter()

@router.get("/analytics")
async def get_analytics(db: Session = Depends(get_db)):
    """
    Get comprehensive analytics about research activity
    
    Returns:
    - Total searches
    - Papers analyzed
    - Average relevance scores
    - Source distribution
    - Search trends
    - Top topics
    """
    
    try:
        # Get all search history from database
        all_searches = db.query(SearchHistory).all()
        completed_searches = db.query(SearchHistory).filter(
            SearchHistory.status == 'completed'
        ).all()
        
        total_searches = len(all_searches)
        completed_count = len(completed_searches)
        
        # Papers analyzed
        total_papers = db.query(func.count(Paper.id)).scalar() or 0
        
        # Source distribution
        source_counter = Counter()
        for search in completed_searches:
            if search.papers:
                for paper in search.papers:
                    source_counter[paper.source] += 1
        
        papers_per_source = [
            {
                "source": source,
                "papers": count,
                "color": {
                    "arxiv": "#3b82f6",
                    "semantic_scholar": "#10b981",
                    "springer": "#f59e0b",
                    "pubmed": "#ef4444"
                }.get(source, "#6366f1")
            }
            for source, count in source_counter.most_common()
        ]
        
        # Weekly search activity (last 7 days)
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        daily_searches = {i: 0 for i in range(7)}
        
        recent_searches = db.query(SearchHistory).filter(
            SearchHistory.created_at >= week_ago
        ).all()
        
        for search in recent_searches:
            days_ago = (now - search.created_at).days
            if 0 <= days_ago < 7:
                daily_searches[6 - days_ago] += 1
        
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        search_history_data = [
            {"date": days[i], "searches": daily_searches[i]}
            for i in range(7)
        ]
        
        # Top search queries - extract keywords
        query_counter = Counter()
        for search in all_searches:
            query = search.query.strip()
            if query:
                # Extract keywords (simple approach)
                keywords = [word for word in query.lower().split() if len(word) > 3]
                query_counter.update(keywords[:3])  # Take first 3 significant words
        
        top_searches_data = [
            {"topic": topic.capitalize(), "searches": count}
            for topic, count in query_counter.most_common(5)
        ]
        
        # Calculate average relevance score from papers
        relevance_by_search = {}
        for search in completed_searches:
            if search.papers:
                avg_score = sum(p.relevance_score for p in search.papers) / len(search.papers)
                query_preview = search.query.split()[0] if search.query else "Query"
                relevance_by_search[search.id] = {
                    "query": query_preview,
                    "avgScore": round(avg_score, 2)
                }
        
        relevance_score_data = list(relevance_by_search.values())[:5] if relevance_by_search else [
            {"query": "No data", "avgScore": 0.0}
        ]
        
        # Calculate average relevance percentage
        avg_relevance = sum(item["avgScore"] for item in relevance_score_data) / len(relevance_score_data) if relevance_score_data else 0
        
        # Active days (last 30 days)
        thirty_days_ago = now - timedelta(days=30)
        active_searches = db.query(SearchHistory).filter(
            SearchHistory.created_at >= thirty_days_ago
        ).all()
        
        active_days_set = set()
        for search in active_searches:
            active_days_set.add(search.created_at.date())
        
        active_days = len(active_days_set)
        
        # Calculate month-over-month growth
        searches_last_month = len(active_searches)
        searches_prev_month = total_searches - searches_last_month
        searches_growth = ((searches_last_month - searches_prev_month) / searches_prev_month * 100) if searches_prev_month > 0 else 0
        
        return {
            "stats": {
                "total_searches": total_searches,
                "completed_searches": completed_count,
                "total_papers": total_papers,
                "avg_relevance": round(avg_relevance * 100, 1),
                "active_days": active_days,
                "searches_growth": round(searches_growth, 1),
                "papers_growth": 8.3,  # Mock for now
                "relevance_growth": 2.1  # Mock for now
            },
            "charts": {
                "search_history_data": search_history_data,
                "papers_per_source_data": papers_per_source,
                "relevance_score_data": relevance_score_data,
                "top_searches_data": top_searches_data
            }
        }
        
    except Exception as e:
        print(f"❌ Error generating analytics: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/summary")
async def get_analytics_summary(db: Session = Depends(get_db)):
    """Get quick analytics summary"""
    
    try:
        total_searches = db.query(func.count(SearchHistory.id)).scalar() or 0
        completed_searches = db.query(func.count(SearchHistory.id)).filter(
            SearchHistory.status == 'completed'
        ).scalar() or 0
        total_papers = db.query(func.count(Paper.id)).scalar() or 0
        
        return {
            "total_searches": total_searches,
            "completed_searches": completed_searches,
            "total_papers": total_papers,
            "success_rate": round(completed_searches / total_searches * 100, 1) if total_searches > 0 else 0
        }
        
    except Exception as e:
        print(f"❌ Error generating analytics summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
