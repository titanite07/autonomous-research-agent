"""
Research service - Business logic for search and analysis
Integrates with autogen_research_system.py
"""

import sys
import os
from typing import List, Dict, Any
import hashlib
from datetime import datetime

# Add parent directory to path to import autogen_research_system
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from autogen_research_system import AutoGenResearchSystem
from api.utils.relevance_calculator import get_relevance_calculator

class ResearchService:
    """Service class to handle research operations"""
    
    def __init__(self):
        """Initialize the research service"""
        # Don't create shared system instance - create per-request to avoid race conditions
        self.system = None
        self.relevance_calculator = get_relevance_calculator()
    
    def _normalize_paper(self, paper: Dict, source: str = "unknown", query: str = "") -> Dict:
        """
        Normalize paper data to match frontend expectations
        
        Args:
            paper: Raw paper data from scraper
            source: Source of the paper (arxiv, semantic_scholar, etc.)
            query: Search query for relevance calculation
            
        Returns:
            Normalized paper dictionary
        """
        # Generate a unique ID from title + authors
        paper_id = hashlib.md5(
            f"{paper.get('title', '')}_{','.join(paper.get('authors', []))}".encode()
        ).hexdigest()[:16]
        
        # Extract year from published_date
        year = 2024  # default
        if paper.get('published_date'):
            try:
                # Try parsing common date formats
                date_str = paper['published_date']
                for fmt in ['%d %B %Y', '%Y-%m-%d', '%Y']:
                    try:
                        dt = datetime.strptime(date_str, fmt)
                        year = dt.year
                        break
                    except:
                        continue
            except:
                pass
        
        # Determine source if not explicitly set
        if source == "unknown":
            if paper.get('arxiv_id'):
                source = "arxiv"
            elif paper.get('doi'):
                source = "semantic_scholar"
        
        # Calculate real-time relevance score
        relevance_score = 0.5  # Default fallback
        if query:
            try:
                relevance_score = self.relevance_calculator.calculate_relevance(
                    query=query,
                    title=paper.get("title", ""),
                    abstract=paper.get("abstract", ""),
                    keywords=paper.get("keywords", [])
                )
            except Exception as e:
                print(f"⚠️ Error calculating relevance: {e}")
                relevance_score = 0.5
        
        return {
            "id": paper_id,
            "title": paper.get("title", "Untitled"),
            "authors": paper.get("authors", []),
            "abstract": paper.get("abstract", ""),
            "year": year,
            "url": paper.get("url", ""),
            "citations": paper.get("citations", 0),
            "relevance_score": relevance_score,
            "source": source,
            "pdf_url": paper.get("pdf_url")
        }
    
    async def search_papers(
        self,
        query: str,
        max_results: int = 10,
        sources: List[str] = None,
        dedup_threshold: float = 0.15
    ) -> Dict[str, Any]:
        """
        Search for research papers across multiple sources with relevance scoring
        
        Args:
            query: Search query string
            max_results: Maximum number of papers to return
            sources: List of sources to search
            dedup_threshold: Threshold for semantic deduplication
            
        Returns:
            Dictionary with search results and metadata
        """
        print(f"\n🔍 Searching for papers on: {query}")
        print(f"   Sources: {', '.join(sources) if sources else 'arxiv, semantic_scholar'}")
        print(f"   Max results: {max_results}")
        
        # Create a new research system instance for this request (thread-safe)
        system = AutoGenResearchSystem()
        
        # Store max_results for filtering later
        self.max_results = max_results
        
        # Calculate expanded results per source to account for:
        # 1. Relevance filtering (some papers may be low relevance)
        # 2. Deduplication (some papers may be duplicates across sources)
        # 3. Invalid papers (some may be missing required fields)
        # Formula: (max_results * 3) to ensure enough papers after all filtering
        expanded_max_results = max(max_results * 3, 30)  # Minimum 30 papers per source
        
        print(f"🔍 Requesting {expanded_max_results} papers per source (filtering to {max_results} high-relevance)")
        
        # Let AutoGen system determine sources automatically if not specified
        # It will include Springer if API key is present
        if sources is None:
            sources = ["arxiv", "semantic_scholar"]
            # Check if Springer is available
            if hasattr(system, 'springer_scraper') and system.springer_scraper:
                sources.append("springer")
                print("✅ Springer source added (API key detected)")
        
        # Use AutoGen system to search with expanded results
        search_result = system.search_papers(
            query=query,
            max_results=expanded_max_results,  # Request more papers from each source
            sources=sources
        )
        
        # Extract papers from the result dictionary
        raw_papers = search_result.get("papers", []) if isinstance(search_result, dict) else []
        
        print(f"\n📄 Processing {len(raw_papers)} raw papers from scrapers")
        
        # Normalize papers to match frontend expectations
        normalized_papers = []
        for paper in raw_papers:
            # Convert ScrapedPaper to dict if needed
            if hasattr(paper, 'to_dict'):
                paper_dict = paper.to_dict()
            elif isinstance(paper, dict):
                paper_dict = paper
            else:
                continue
            
            # Determine source from paper metadata
            source = paper_dict.get('source', 'unknown')  # Use source field if available
            
            # Debug: Print source detection
            if source == 'springer':
                print(f"   ✅ Springer paper detected: {paper_dict.get('title', '')[:50]}...")
            
            if source == 'unknown':
                # Fallback to detection logic if source not set
                if paper_dict.get('arxiv_id'):
                    source = "arxiv"
                elif paper_dict.get('venue') and ('springer' in paper_dict.get('venue', '').lower() or 
                                                 'nature' in paper_dict.get('venue', '').lower() or
                                                 'bmc' in paper_dict.get('venue', '').lower()):
                    source = "springer"
                    print(f"   📖 Detected Springer via venue: {paper_dict.get('venue', '')}")
                elif paper_dict.get('doi') and 'springer' in paper_dict.get('doi', '').lower():
                    source = "springer"
                    print(f"   📖 Detected Springer via DOI: {paper_dict.get('doi', '')}")
                elif paper_dict.get('doi'):
                    source = "semantic_scholar"
            
            # Normalize with query for relevance calculation
            normalized = self._normalize_paper(paper_dict, source, query)
            normalized_papers.append(normalized)
        
        print(f"✅ Normalized {len(normalized_papers)} papers for frontend")
        
        # Filter papers by minimum relevance threshold
        # Lower threshold to ensure we get closer to max_results
        MIN_RELEVANCE_THRESHOLD = 0.30  # 30% minimum relevance (was 75%)
        filtered_papers = [
            paper for paper in normalized_papers 
            if paper['relevance_score'] >= MIN_RELEVANCE_THRESHOLD
        ]
        
        # Sort by relevance score FIRST (highest first)
        filtered_papers.sort(key=lambda p: p['relevance_score'], reverse=True)
        
        # If we still don't have enough papers, include all papers and sort by relevance
        if len(filtered_papers) < max_results and normalized_papers:
            print(f"⚠️ Only {len(filtered_papers)} papers above {MIN_RELEVANCE_THRESHOLD:.0%} threshold")
            print(f"📊 Including all {len(normalized_papers)} papers sorted by relevance")
            filtered_papers = sorted(normalized_papers, key=lambda p: p['relevance_score'], reverse=True)
        
        # Limit to max_results
        if len(filtered_papers) > max_results:
            filtered_papers = filtered_papers[:max_results]
            print(f"📊 Limiting results to requested {max_results} papers")
        else:
            print(f"📊 Returning {len(filtered_papers)} papers (requested {max_results})")
        
        # Log relevance scores
        if filtered_papers:
            avg_relevance = sum(p['relevance_score'] for p in filtered_papers) / len(filtered_papers)
            print(f"📊 Average relevance score: {avg_relevance:.2%}")
            top_paper = filtered_papers[0]  # Already sorted by relevance
            print(f"🏆 Most relevant: {top_paper['title'][:60]}... (score: {top_paper['relevance_score']:.2%})")
            
            # Log filtering stats
            removed_count = len(normalized_papers) - len(filtered_papers)
            if removed_count > 0:
                print(f"🔍 Filtered out {removed_count} low-relevance papers (<{MIN_RELEVANCE_THRESHOLD:.0%})")
        
        # Format results
        return {
            "query": query,
            "total_papers": len(filtered_papers),
            "papers": filtered_papers,
            "sources": sources,
            "dedup_threshold": dedup_threshold
        }
    
    async def analyze_papers(
        self,
        paper_ids: List[str],
        include_citations: bool = True,
        include_knowledge_graph: bool = True,
        job_id: str = None  # Optional job_id for WebSocket updates
    ) -> Dict[str, Any]:
        """
        Analyze selected papers with real-time progress updates
        
        Args:
            paper_ids: List of paper IDs to analyze
            include_citations: Build citation network
            include_knowledge_graph: Extract entities and build KG
            job_id: Optional job_id for WebSocket progress updates
            
        Returns:
            Dictionary with analysis results
        """
        
        from api.utils.event_broadcaster import emit_event_async
        
        print(f"🔬 Starting analysis of {len(paper_ids)} papers...")
        
        # Emit analysis started event
        if job_id:
            await emit_event_async(job_id, "analysis_started", {
                "message": f"Starting analysis of {len(paper_ids)} papers...",
                "total_papers": len(paper_ids),
                "step": "1/3"
            })
        
        try:
            # Import agents
            from agents.summarization_agent import SummarizationAgent
            from agents.synthesis_agent import SynthesisAgent
            from agents.citation_agent import CitationAgent
            
            # Get papers from database
            papers = self._get_papers_by_ids(paper_ids)
            
            if not papers:
                if job_id:
                    await emit_event_async(job_id, "analysis_error", {
                        "message": "Papers not found in database",
                        "error": "Papers not found"
                    })
                return {
                    "paper_ids": paper_ids,
                    "error": "Papers not found",
                    "citations": None,
                    "knowledge_graph": None
                }
            
            # Step 1: Summarize each paper
            print(f"📝 Step 1/3: Summarizing {len(papers)} papers...")
            
            if job_id:
                await emit_event_async(job_id, "summarizing", {
                    "message": f"Summarizing {len(papers)} papers...",
                    "step": "1/3",
                    "total": len(papers),
                    "progress": 0
                })
            
            summarization_agent = SummarizationAgent(
                provider="groq",
                temperature=0.3,
                use_fulltext=False
            )
            
            summaries = []
            for idx, paper in enumerate(papers):
                try:
                    summary = summarization_agent.summarize_paper(
                        paper=paper,
                        research_query=""
                    )
                    summaries.append(summary)
                    
                    # Emit progress update
                    if job_id:
                        progress = int(((idx + 1) / len(papers)) * 100)
                        await emit_event_async(job_id, "summarizing_progress", {
                            "message": f"Summarized paper {idx + 1}/{len(papers)}: {paper.get('title', 'Unknown')[:50]}...",
                            "step": "1/3",
                            "current": idx + 1,
                            "total": len(papers),
                            "progress": progress
                        })
                        
                except Exception as e:
                    print(f"⚠️ Error summarizing paper: {e}")
                    continue
            
            print(f"✅ Generated {len(summaries)} summaries")
            
            if job_id:
                await emit_event_async(job_id, "summarizing_complete", {
                    "message": f"Generated {len(summaries)} summaries",
                    "step": "1/3",
                    "total_summaries": len(summaries)
                })
            
            # Step 2: Synthesize findings across papers
            print(f"🧬 Step 2/3: Synthesizing findings...")
            
            if job_id:
                await emit_event_async(job_id, "synthesizing", {
                    "message": "Synthesizing findings across papers...",
                    "step": "2/3"
                })
            
            synthesis_agent = SynthesisAgent(
                provider="groq",
                temperature=0.5
            )
            
            synthesis = synthesis_agent.synthesize(
                summaries=summaries,
                research_query=""
            )
            
            print(f"✅ Synthesis complete")
            
            if job_id:
                await emit_event_async(job_id, "synthesis_complete", {
                    "message": "Synthesis complete",
                    "step": "2/3"
                })
            
            # Step 3: Build citation network (if requested)
            citations_data = None
            if include_citations:
                print(f"📚 Step 3/3: Building citation network...")
                
                if job_id:
                    await emit_event_async(job_id, "building_citations", {
                        "message": "Building citation network...",
                        "step": "3/3"
                    })
                
                citation_agent = CitationAgent()
                
                citation_graph = citation_agent.build_citation_network(papers)
                most_cited = citation_agent.get_most_cited(top_n=10)
                
                citations_data = {
                    "total_papers": len(papers),
                    "total_citations": citation_graph.number_of_edges(),
                    "most_cited_papers": most_cited,
                    "citation_network": {
                        "nodes": citation_graph.number_of_nodes(),
                        "edges": citation_graph.number_of_edges()
                    }
                }
                
                print(f"✅ Citation network built")
                
                if job_id:
                    await emit_event_async(job_id, "citations_complete", {
                        "message": f"Citation network built ({citation_graph.number_of_edges()} citations)",
                        "step": "3/3",
                        "total_citations": citation_graph.number_of_edges()
                    })
            
            # Build knowledge graph (if requested)
            kg_data = None
            if include_knowledge_graph:
                print(f"🕸️ Extracting knowledge graph...")
                
                if job_id:
                    await emit_event_async(job_id, "extracting_knowledge_graph", {
                        "message": "Extracting knowledge graph..."
                    })
                
                # Use synthesis results as knowledge graph foundation
                kg_data = {
                    "entities": synthesis.get("topic_keywords", [])[:20],
                    "themes": synthesis.get("synthesis_text", "")[:500],
                    "clusters": synthesis.get("paper_clusters", {}),
                    "temporal_patterns": synthesis.get("temporal_patterns", {})
                }
                print(f"✅ Knowledge graph extracted")
                
                if job_id:
                    await emit_event_async(job_id, "knowledge_graph_complete", {
                        "message": "Knowledge graph extracted",
                        "entities_count": len(kg_data.get("entities", []))
                    })
            
            # Save analysis results to database
            analysis_job_id = job_id  # Preserve the WebSocket job_id
            try:
                from api.database import SessionLocal
                from api.db_models import AnalysisResult, SearchHistory, Paper as PaperDB
                import uuid
                
                db = SessionLocal()
                try:
                    # Generate job_id for database record if not provided
                    if not analysis_job_id:
                        analysis_job_id = f"analysis-{str(uuid.uuid4())[:8]}"
                    
                    # Try to link to search_id if papers belong to same search
                    search_id = None
                    if papers and len(papers) > 0:
                        # Get the first paper's search_id
                        first_paper_id = int(paper_ids[0]) if isinstance(paper_ids[0], int) else (int(paper_ids[0]) if str(paper_ids[0]).isdigit() else None)
                        if first_paper_id:
                            paper_db = db.query(PaperDB).filter(PaperDB.id == first_paper_id).first()
                            if paper_db:
                                search_id = paper_db.search_id
                    
                    # Create analysis result record
                    analysis_result = AnalysisResult(
                        job_id=analysis_job_id,
                        search_id=search_id,
                        summaries=summaries,
                        synthesis=synthesis,
                        citations_data=citations_data,
                        knowledge_graph=kg_data,
                        total_papers=len(papers),
                        analysis_status="completed"
                    )
                    
                    db.add(analysis_result)
                    db.commit()
                    print(f"✅ Analysis results saved to database (job_id: {analysis_job_id})")
                    
                finally:
                    db.close()
                    
            except Exception as db_error:
                print(f"⚠️ Failed to save analysis to database: {db_error}")
                # Continue anyway - analysis still succeeded
            
            # Emit analysis complete event
            if job_id:
                await emit_event_async(job_id, "analysis_complete", {
                    "message": "Analysis complete!",
                    "total_papers": len(papers),
                    "summaries_count": len(summaries),
                    "analysis_job_id": analysis_job_id
                })
            
            return {
                "job_id": analysis_job_id,  # Return analysis job_id for later retrieval
                "paper_ids": paper_ids,
                "summaries": summaries,
                "synthesis": synthesis,
                "citations": citations_data,
                "knowledge_graph": kg_data,
                "total_papers_analyzed": len(papers)
            }
            
        except Exception as e:
            print(f"❌ Error in analysis: {e}")
            import traceback
            traceback.print_exc()
            
            # Emit error event
            if job_id:
                await emit_event_async(job_id, "analysis_error", {
                    "message": "Analysis failed",
                    "error": str(e)
                })
            
            # Save error to database
            error_job_id = None
            try:
                from api.database import SessionLocal
                from api.db_models import AnalysisResult
                import uuid
                
                db = SessionLocal()
                try:
                    error_job_id = f"analysis-{str(uuid.uuid4())[:8]}"
                    
                    analysis_result = AnalysisResult(
                        job_id=error_job_id,
                        search_id=None,
                        summaries=[],
                        synthesis={},
                        total_papers=len(paper_ids),
                        analysis_status="failed",
                        error_message=str(e)
                    )
                    
                    db.add(analysis_result)
                    db.commit()
                    print(f"⚠️ Analysis error saved to database (job_id: {error_job_id})")
                    
                finally:
                    db.close()
                    
            except Exception as db_error:
                print(f"⚠️ Failed to save error to database: {db_error}")
            
            return {
                "job_id": error_job_id,
                "paper_ids": paper_ids,
                "error": f"Analysis failed: {str(e)}",
                "citations": None,
                "knowledge_graph": None
            }
    
    def _get_papers_by_ids(self, paper_ids: List[str]) -> List[Dict]:
        """
        Retrieve papers by their IDs from database
        
        Args:
            paper_ids: List of paper database IDs (integers or strings)
            
        Returns:
            List of paper dictionaries
        """
        if not paper_ids:
            return []
        
        try:
            from api.database import SessionLocal
            from api.db_models import Paper as PaperDB
            
            db = SessionLocal()
            
            try:
                # Convert to integers (handle both string and int inputs)
                int_ids = []
                for pid in paper_ids:
                    if isinstance(pid, int):
                        int_ids.append(pid)
                    elif isinstance(pid, str) and pid.isdigit():
                        int_ids.append(int(pid))
                    else:
                        print(f"⚠️ Invalid paper ID: {pid}")
                
                if not int_ids:
                    print(f"⚠️ No valid paper IDs provided: {paper_ids}")
                    return []
                
                # Query papers by ID
                papers = db.query(PaperDB).filter(PaperDB.id.in_(int_ids)).all()
                
                # Convert to dictionaries
                paper_dicts = []
                for paper in papers:
                    paper_dict = paper.to_dict()
                    # Add compatibility fields for agents
                    paper_dict['published_date'] = str(paper.year) if paper.year else ""
                    paper_dicts.append(paper_dict)
                
                print(f"✅ Retrieved {len(paper_dicts)} papers from database")
                return paper_dicts
                
            finally:
                db.close()
                
        except Exception as e:
            print(f"⚠️ Error retrieving papers by IDs: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def generate_report(
        self,
        job_id: str,
        format: str = "markdown",
        websocket_job_id: str = None
    ) -> str:
        """
        Generate research report
        
        Args:
            job_id: Search job ID
            format: Report format (markdown, latex, etc.)
            websocket_job_id: Optional WebSocket job ID for real-time updates
            
        Returns:
            Generated report as string
        """
        
        from api.utils.event_broadcaster import emit_event_async
        
        print(f"📄 Generating {format} report for job {job_id}...")
        
        # Emit report generation started event
        if websocket_job_id:
            await emit_event_async(
                websocket_job_id,
                "report_generation_started",
                {
                    "message": "Starting report generation",
                    "search_job_id": job_id,
                    "format": format,
                    "step": "1/4"
                }
            )
        
        try:
            # Import agents
            from agents.writing_agent import WritingAgent
            from agents.citation_agent import CitationAgent
            
            # Get search results for this job
            # In production, fetch from database using job_id
            search_data = self._get_search_by_job_id(job_id)
            
            if not search_data:
                if websocket_job_id:
                    await emit_event_async(
                        websocket_job_id,
                        "report_error",
                        {"message": "Search results not found", "search_job_id": job_id}
                    )
                return f"# Report for Job {job_id}\n\n**Error:** Search results not found"
            
            papers = search_data.get("papers", [])
            query = search_data.get("query", "Research Query")
            
            if not papers:
                if websocket_job_id:
                    await emit_event_async(
                        websocket_job_id,
                        "report_error",
                        {"message": "No papers found for this search", "search_job_id": job_id}
                    )
                return f"# Report for Job {job_id}\n\n**Error:** No papers found for this search"
            
            # Emit analyzing event
            if websocket_job_id:
                await emit_event_async(
                    websocket_job_id,
                    "report_analyzing",
                    {
                        "message": f"Analyzing {len(papers)} papers",
                        "paper_count": len(papers),
                        "step": "2/4"
                    }
                )
            
            # Analyze papers first to get summaries and synthesis
            print(f"📊 Analyzing {len(papers)} papers...")
            paper_ids = [p.get("id") for p in papers]
            
            analysis = await self.analyze_papers(
                paper_ids=paper_ids,
                include_citations=True,
                include_knowledge_graph=False,
                job_id=websocket_job_id  # Pass WebSocket job_id for nested events
            )
            
            summaries = analysis.get("summaries", [])
            synthesis = analysis.get("synthesis", {})
            
            # Emit generating citations event
            if websocket_job_id:
                await emit_event_async(
                    websocket_job_id,
                    "report_generating_citations",
                    {
                        "message": "Generating citations",
                        "step": "3/4"
                    }
                )
            
            # Generate citations
            print(f"📚 Generating citations...")
            citation_agent = CitationAgent()
            citation_agent.build_citation_network(papers)
            citations = citation_agent.generate_bibliography(
                papers=papers,
                style="APA"
            )
            
            # Emit writing event
            if websocket_job_id:
                await emit_event_async(
                    websocket_job_id,
                    "report_writing",
                    {
                        "message": f"Writing {format} report",
                        "format": format,
                        "step": "4/4"
                    }
                )
            
            # Generate report using Writing Agent
            print(f"✍️ Writing literature review...")
            writing_agent = WritingAgent(
                provider="groq",
                temperature=0.7
            )
            
            if format == "executive_summary":
                report = writing_agent.write_executive_summary(
                    research_query=query,
                    summaries=summaries,
                    synthesis=synthesis,
                    max_words=500
                )
            else:
                report = writing_agent.write_literature_review(
                    research_query=query,
                    summaries=summaries,
                    synthesis=synthesis,
                    citations=citations,
                    format=format
                )
            
            print(f"✅ Report generated ({len(report)} characters)")
            
            # Emit report complete event
            if websocket_job_id:
                await emit_event_async(
                    websocket_job_id,
                    "report_complete",
                    {
                        "message": "Report generation complete",
                        "report_length": len(report),
                        "word_count": len(report.split()),
                        "format": format
                    }
                )
            
            # Save report to database
            try:
                from api.database import SessionLocal
                from api.db_models import Report as ReportDB, SearchHistory
                
                db = SessionLocal()
                try:
                    # Get search_id from job_id
                    search = db.query(SearchHistory).filter(SearchHistory.job_id == job_id).first()
                    search_id = search.id if search else None
                    
                    # Extract executive summary (first 500 chars or until first section)
                    executive_summary = report[:500] if len(report) > 500 else report
                    if "\n\n" in executive_summary:
                        executive_summary = executive_summary.split("\n\n")[0]
                    
                    # Extract key findings from synthesis
                    key_findings = []
                    if synthesis and "key_findings" in synthesis:
                        key_findings = synthesis["key_findings"]
                    elif synthesis and "main_themes" in synthesis:
                        key_findings = synthesis.get("main_themes", [])[:5]
                    
                    # Extract research gaps
                    research_gaps = []
                    if synthesis and "research_gaps" in synthesis:
                        research_gaps = synthesis["research_gaps"]
                    elif synthesis and "future_directions" in synthesis:
                        research_gaps = synthesis.get("future_directions", [])[:5]
                    
                    # Create report record
                    report_db = ReportDB(
                        search_id=search_id,
                        title=f"Literature Review: {query[:100]}",
                        report_type="literature_review" if format != "executive_summary" else "executive_summary",
                        format=format,
                        content=report,
                        executive_summary=executive_summary,
                        key_findings=key_findings,
                        research_gaps=research_gaps,
                        word_count=len(report.split()),
                        paper_count=len(papers),
                        citation_style="APA"
                    )
                    
                    db.add(report_db)
                    db.commit()
                    db.refresh(report_db)
                    
                    print(f"✅ Report saved to database (ID: {report_db.id})")
                    
                finally:
                    db.close()
                    
            except Exception as db_error:
                print(f"⚠️ Failed to save report to database: {db_error}")
                # Continue anyway - report generation succeeded
            
            return report
            
        except Exception as e:
            print(f"❌ Error generating report: {e}")
            import traceback
            traceback.print_exc()
            
            # Emit error event
            if websocket_job_id:
                await emit_event_async(
                    websocket_job_id,
                    "report_error",
                    {
                        "message": f"Error generating report: {str(e)}",
                        "search_job_id": job_id
                    }
                )
            
            return f"# Report Generation Error\n\nJob ID: {job_id}\nError: {str(e)}"
    
    def _get_search_by_job_id(self, job_id: str) -> Dict[str, Any]:
        """
        Retrieve search results by job ID from database
        
        Args:
            job_id: Search job ID (UUID string)
            
        Returns:
            Dictionary with search query and associated papers
        """
        if not job_id:
            return None
        
        try:
            from api.database import SessionLocal
            from api.db_models import SearchHistory, Paper as PaperDB
            
            db = SessionLocal()
            
            try:
                # Query search history by job_id
                search = db.query(SearchHistory).filter(SearchHistory.job_id == job_id).first()
                
                if not search:
                    print(f"⚠️ Search not found for job_id: {job_id}")
                    return None
                
                # Get associated papers
                papers = db.query(PaperDB).filter(PaperDB.search_id == search.id).all()
                
                # Convert papers to dictionaries
                paper_dicts = []
                for paper in papers:
                    paper_dict = paper.to_dict()
                    # Add compatibility fields for agents
                    paper_dict['published_date'] = str(paper.year) if paper.year else ""
                    paper_dicts.append(paper_dict)
                
                # Build search data dictionary
                search_data = {
                    "job_id": search.job_id,
                    "query": search.query,
                    "papers": paper_dicts,
                    "max_results": search.max_results,
                    "sources": search.sources,
                    "status": search.status,
                    "results_count": len(paper_dicts),
                    "created_at": search.created_at.isoformat() if search.created_at else None,
                    "completed_at": search.completed_at.isoformat() if search.completed_at else None
                }
                
                print(f"✅ Retrieved search {job_id} with {len(paper_dicts)} papers")
                return search_data
                
            finally:
                db.close()
                
        except Exception as e:
            print(f"⚠️ Error retrieving search by job_id: {e}")
            import traceback
            traceback.print_exc()
            return None
