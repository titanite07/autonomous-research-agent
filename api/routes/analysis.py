"""
Analysis API routes
Handles paper analysis, citations, knowledge graphs
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Dict
import uuid

from api.models import AnalysisRequest, AnalysisResponse
from api.services.research_service import ResearchService
from api.database import get_db
from api.db_models import Paper, AnalysisResult, SearchHistory, Report

router = APIRouter()

@router.post("/analyze", response_model=Dict)
async def analyze_papers(
    request: AnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Perform deep analysis on selected papers from database
    
    - **paper_ids**: List of database paper IDs to analyze
    - **analysis_type**: Type of analysis (comprehensive, quick, citation_only)
    - **include_citations**: Build citation network
    - **include_knowledge_graph**: Extract entities and build KG
    - **job_id**: Optional WebSocket job ID for real-time updates
    
    Returns detailed analysis including summaries, findings, gaps, etc.
    """
    
    try:
        print(f"📊 Received analysis request for {len(request.paper_ids)} papers")
        
        # Validate paper IDs exist in database
        papers = db.query(Paper).filter(Paper.id.in_(request.paper_ids)).all()
        
        if not papers:
            raise HTTPException(
                status_code=404,
                detail=f"No papers found with IDs: {request.paper_ids}"
            )
        
        if len(papers) != len(request.paper_ids):
            found_ids = [p.id for p in papers]
            missing_ids = set(request.paper_ids) - set(found_ids)
            print(f"⚠️ Warning: Papers not found: {missing_ids}")
        
        print(f"✅ Found {len(papers)} papers in database")
        
        # Get or create search_id (use the first paper's search_id)
        search_id = papers[0].search_id
        
        # Generate job_id for tracking if not provided
        analysis_job_id = request.job_id or f"analysis-{uuid.uuid4()}"
        
        # Initialize research service
        service = ResearchService()
        
        # Perform analysis with WebSocket support
        result = await service.analyze_papers(
            paper_ids=request.paper_ids,
            include_citations=request.include_citations,
            include_knowledge_graph=request.include_knowledge_graph,
            job_id=analysis_job_id
        )
        
        # Add metadata to response
        result["job_id"] = analysis_job_id
        result["search_id"] = search_id
        result["total_papers"] = len(papers)
        result["status"] = "completed"
        
        print(f"✅ Analysis completed for job {analysis_job_id}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in analysis endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/{job_id}/{format}")
async def export_report(
    job_id: str,
    format: str,
    db: Session = Depends(get_db)
):
    """
    Export research report in various formats
    
    - **job_id**: The search job ID
    - **format**: Export format (pdf, docx, latex, markdown, html)
    
    Returns the report content or download information
    """
    
    valid_formats = ["pdf", "docx", "latex", "markdown", "html"]
    if format not in valid_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid format. Must be one of: {', '.join(valid_formats)}"
        )
    
    try:
        # Look for report by search job_id
        search = db.query(SearchHistory).filter(SearchHistory.job_id == job_id).first()
        
        if not search:
            raise HTTPException(
                status_code=404,
                detail=f"Search with job_id '{job_id}' not found"
            )
        
        # Get the most recent report for this search
        report = db.query(Report).filter(
            Report.search_id == search.id
        ).order_by(Report.created_at.desc()).first()
        
        if not report:
            raise HTTPException(
                status_code=404,
                detail=f"No report found for job_id '{job_id}'. Generate a report first using /api/v1/report"
            )
        
        print(f"📄 Exporting report {report.id} in {format} format")
        
        # Return content based on format
        if format == "markdown":
            return {
                "job_id": job_id,
                "report_id": report.id,
                "format": "markdown",
                "content": report.content,
                "title": report.title,
                "metadata": {
                    "word_count": report.word_count,
                    "paper_count": report.paper_count,
                    "citation_style": report.citation_style,
                    "created_at": report.created_at.isoformat() if report.created_at else None
                }
            }
        
        elif format == "html":
            # Convert markdown to HTML (basic conversion)
            import markdown
            html_content = markdown.markdown(
                report.content,
                extensions=['extra', 'codehilite', 'toc']
            )
            
            # Wrap in HTML template
            html_full = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{report.title}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
            line-height: 1.6;
            color: #333;
        }}
        h1, h2, h3 {{ color: #2c3e50; }}
        code {{ 
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
        }}
        pre {{
            background: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        blockquote {{
            border-left: 4px solid #ddd;
            padding-left: 20px;
            color: #666;
        }}
    </style>
</head>
<body>
{html_content}
<hr>
<footer>
    <p><small>Generated: {report.created_at.strftime('%Y-%m-%d %H:%M:%S') if report.created_at else 'N/A'} | 
    Word Count: {report.word_count} | Papers: {report.paper_count}</small></p>
</footer>
</body>
</html>
"""
            
            return {
                "job_id": job_id,
                "report_id": report.id,
                "format": "html",
                "content": html_full,
                "title": report.title,
                "metadata": {
                    "word_count": report.word_count,
                    "paper_count": report.paper_count,
                    "created_at": report.created_at.isoformat() if report.created_at else None
                }
            }
        
        elif format == "latex":
            # Convert markdown to LaTeX (basic conversion)
            latex_content = convert_markdown_to_latex(report.content, report.title)
            
            return {
                "job_id": job_id,
                "report_id": report.id,
                "format": "latex",
                "content": latex_content,
                "title": report.title,
                "metadata": {
                    "word_count": report.word_count,
                    "paper_count": report.paper_count,
                    "created_at": report.created_at.isoformat() if report.created_at else None
                }
            }
        
        elif format == "pdf":
            # PDF generation would require additional libraries
            # For now, return instructions
            return {
                "job_id": job_id,
                "report_id": report.id,
                "format": "pdf",
                "status": "not_implemented",
                "message": "PDF export requires additional setup. Use markdown or HTML export and convert manually.",
                "alternatives": {
                    "html": f"/api/v1/export/{job_id}/html",
                    "markdown": f"/api/v1/export/{job_id}/markdown",
                    "latex": f"/api/v1/export/{job_id}/latex"
                }
            }
        
        elif format == "docx":
            # DOCX generation would require python-docx
            return {
                "job_id": job_id,
                "report_id": report.id,
                "format": "docx",
                "status": "not_implemented",
                "message": "DOCX export requires additional setup. Use markdown or HTML export and convert manually.",
                "alternatives": {
                    "html": f"/api/v1/export/{job_id}/html",
                    "markdown": f"/api/v1/export/{job_id}/markdown",
                    "latex": f"/api/v1/export/{job_id}/latex"
                }
            }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in export endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def convert_markdown_to_latex(markdown_content: str, title: str) -> str:
    """
    Convert markdown report to LaTeX format
    
    Args:
        markdown_content: The markdown content
        title: Report title
        
    Returns:
        LaTeX formatted document
    """
    
    # Basic markdown to LaTeX conversion
    latex_content = markdown_content
    
    # Convert headers
    latex_content = latex_content.replace("### ", "\\subsubsection{").replace("\n", "}\n", 1)
    latex_content = latex_content.replace("## ", "\\subsection{").replace("\n", "}\n", 1)
    latex_content = latex_content.replace("# ", "\\section{").replace("\n", "}\n", 1)
    
    # Convert bold and italic
    import re
    latex_content = re.sub(r'\*\*(.+?)\*\*', r'\\textbf{\1}', latex_content)
    latex_content = re.sub(r'\*(.+?)\*', r'\\textit{\1}', latex_content)
    
    # Convert code blocks
    latex_content = re.sub(r'```(.+?)```', r'\\begin{verbatim}\1\\end{verbatim}', latex_content, flags=re.DOTALL)
    latex_content = re.sub(r'`(.+?)`', r'\\texttt{\1}', latex_content)
    
    # Escape special LaTeX characters
    special_chars = {'&': '\\&', '%': '\\%', '$': '\\$', '#': '\\#', '_': '\\_', '{': '\\{', '}': '\\}'}
    for char, escaped in special_chars.items():
        latex_content = latex_content.replace(char, escaped)
    
    # Create full LaTeX document
    latex_doc = f"""\\documentclass[12pt,a4paper]{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage{{hyperref}}
\\usepackage{{graphicx}}
\\usepackage{{amsmath}}
\\usepackage{{cite}}

\\title{{{title}}}
\\author{{Autonomous Research Agent}}
\\date{{\\today}}

\\begin{{document}}

\\maketitle
\\tableofcontents
\\newpage

{latex_content}

\\end{{document}}
"""
    
    return latex_doc


@router.get("/network/{job_id}")
async def get_citation_network(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Get citation network data for visualization
    
    - **job_id**: The search job ID
    
    Returns papers and citation links for network visualization
    """
    
    try:
        # Get search history
        search_history = db.query(SearchHistory).filter(SearchHistory.job_id == job_id).first()
        
        if not search_history:
            raise HTTPException(status_code=404, detail="Search not found")
        
        # Get papers
        papers = db.query(Paper).filter(Paper.search_id == search_history.id).all()
        
        if not papers:
            raise HTTPException(status_code=404, detail="No papers found for this search")
        
        # Build network data
        network_papers = []
        for paper in papers:
            network_papers.append({
                "id": str(paper.id),
                "title": paper.title,
                "authors": paper.authors.split(", ") if paper.authors else [],
                "citations": paper.citations or 0,
                "year": paper.year or 2024,
                "url": paper.url or "",
                "abstract": paper.abstract or "",
                "relevance_score": paper.relevance_score or 0.5,
                "source": paper.source or "unknown"
            })
        
        # Generate citation links based on paper relationships
        # This is a simplified version - in production, you'd want to query actual citation data
        links = []
        for i, paper1 in enumerate(papers):
            for j, paper2 in enumerate(papers):
                if i < j:  # Avoid duplicates
                    # Create a link if papers share similar topics or one cites the other
                    # For now, create links between highly cited papers
                    if paper1.citations and paper2.citations:
                        if paper1.citations > 10000 or paper2.citations > 10000:
                            weight = min(paper1.relevance_score or 0.5, paper2.relevance_score or 0.5)
                            links.append({
                                "source": str(paper1.id),
                                "target": str(paper2.id),
                                "weight": weight
                            })
        
        return {
            "job_id": job_id,
            "papers": network_papers,
            "links": links,
            "stats": {
                "total_papers": len(papers),
                "total_connections": len(links),
                "total_citations": sum(p.citations or 0 for p in papers),
                "avg_citations": sum(p.citations or 0 for p in papers) / len(papers) if papers else 0
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error fetching citation network: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
