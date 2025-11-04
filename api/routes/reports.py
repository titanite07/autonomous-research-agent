"""
Reports API routes
Handles report generation and management with database persistence
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import Response
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from datetime import datetime
import uuid

from api.database import get_db
from api.db_models import SearchHistory, Paper as PaperDB, Report as ReportDB
from api.services.report_generator import ReportGenerator

router = APIRouter()
report_generator = ReportGenerator()

def get_research_service():
    """Lazy-load ResearchService to avoid module-level initialization issues"""
    from api.services.research_service import ResearchService
    return ResearchService()

@router.get("/reports")
async def get_reports(
    limit: int = 50,
    report_type: str = None,
    db: Session = Depends(get_db)
):
    """
    Get list of generated reports from database
    
    - **limit**: Maximum number of reports to return
    - **report_type**: Filter by type (literature_review, summary, comparative)
    """
    
    try:
        # Query reports from database
        query = db.query(ReportDB)
        
        if report_type:
            query = query.filter(ReportDB.report_type == report_type)
        
        reports = query.order_by(ReportDB.created_at.desc()).limit(limit).all()
        
        return {
            "reports": [report.to_dict() for report in reports],
            "total": len(reports),
            "filtered": report_type is not None
        }
        
    except Exception as e:
        print(f"❌ Error fetching reports: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report/{report_id}")
async def get_report(report_id: int, db: Session = Depends(get_db)):
    """Get a specific report by ID with full content"""
    
    try:
        report = db.query(ReportDB).filter(ReportDB.id == report_id).first()
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return report.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error fetching report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/report")
async def generate_report_with_websocket(request: Dict):
    """
    Generate a report using ResearchService (supports WebSocket events)
    
    - **job_id**: The search job ID (also used for WebSocket connection)
    - **format**: Output format (markdown, latex, etc.)
    """
    
    try:
        job_id = request.get("job_id")
        format_type = request.get("format", "markdown")
        
        if not job_id:
            raise HTTPException(status_code=400, detail="job_id is required")
        
        # Get ResearchService instance
        research_service = get_research_service()
        
        # Generate report using ResearchService (emits WebSocket events)
        report_content = await research_service.generate_report(
            job_id=job_id,
            format=format_type
        )
        
        return {
            "job_id": job_id,
            "status": "completed",
            "format": format_type,
            "content": report_content
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error generating report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/reports/generate/{job_id}")
async def generate_report(
    job_id: str,
    citation_style: str = "APA",
    format: str = "markdown",
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Generate a literature review report from a completed search
    
    - **job_id**: The search job ID to generate report from
    - **citation_style**: Citation format (APA, MLA, Chicago, IEEE, Harvard)
    - **format**: Output format (markdown, html, text)
    """
    
    try:
        # Get search history
        search_history = db.query(SearchHistory).filter(SearchHistory.job_id == job_id).first()
        
        if not search_history:
            raise HTTPException(status_code=404, detail="Search not found")
        
        if search_history.status != "completed":
            raise HTTPException(status_code=400, detail="Search not completed yet")
        
        # Get papers
        papers = db.query(PaperDB).filter(PaperDB.search_id == search_history.id).all()
        
        if not papers:
            raise HTTPException(status_code=400, detail="No papers found for this search")
        
        # Convert papers to dict format
        papers_data = [paper.to_dict() for paper in papers]
        
        # Generate report
        report_data = report_generator.generate_literature_review(
            query=search_history.query,
            papers=papers_data,
            citation_style=citation_style,
            format=format
        )
        
        # Save to database
        report = ReportDB(
            search_id=search_history.id,
            title=report_data["title"],
            report_type="literature_review",
            format=format,
            content=report_data["content"],
            executive_summary=report_data["executive_summary"],
            key_findings=report_data["key_findings"],
            research_gaps=report_data["research_gaps"],
            word_count=report_data["word_count"],
            paper_count=report_data["paper_count"],
            citation_style=citation_style
        )
        
        db.add(report)
        db.commit()
        db.refresh(report)
        
        return {
            "message": "Report generated successfully",
            "report_id": report.id,
            "report": report.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error generating report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/report/export/{report_id}")
async def export_report(
    report_id: int,
    export_format: str = "markdown",
    db: Session = Depends(get_db)
):
    """
    Export a report in different formats (markdown, html, text, pdf)
    
    - **report_id**: The report ID to export
    - **export_format**: Export format (markdown, html, text, pdf)
    """
    
    try:
        report = db.query(ReportDB).filter(ReportDB.id == report_id).first()
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        content = report.content
        
        # Determine content type and filename
        if export_format == "html":
            content_type = "text/html"
            filename = f"report_{report_id}.html"
            # Convert markdown to HTML if needed
            if report.format == "markdown":
                # Simple conversion (for full implementation, use markdown library)
                content = f"<html><body><pre>{content}</pre></body></html>"
        
        elif export_format == "text":
            content_type = "text/plain"
            filename = f"report_{report_id}.txt"
            
        elif export_format == "pdf":
            # PDF export would require additional library (reportlab or weasyprint)
            raise HTTPException(status_code=501, detail="PDF export coming soon")
        
        else:  # markdown
            content_type = "text/markdown"
            filename = f"report_{report_id}.md"
        
        return Response(
            content=content,
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error exporting report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/report/{report_id}")
async def delete_report(report_id: int, db: Session = Depends(get_db)):
    """Delete a report from database"""
    
    try:
        report = db.query(ReportDB).filter(ReportDB.id == report_id).first()
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        db.delete(report)
        db.commit()
        
        return {
            "message": "Report deleted successfully",
            "report_id": report_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
