"""
Summarization Agent - Extracts key findings from research papers
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
import json
import re
from pydantic import ValidationError
import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llm_config import LLMProvider
from core.pdf_manager import PDFManager
from agents.fulltext_analyzer import FullTextAnalyzer

logger = logging.getLogger(__name__)


class PaperSummary(BaseModel):
    """Structured summary of a research paper"""
    key_findings: List[str] = Field(description="List of 3-5 key findings from the paper")
    methodology: str = Field(description="Brief description of the research methodology")
    results: str = Field(description="Summary of main results and conclusions")
    limitations: List[str] = Field(description="List of limitations mentioned in the paper")
    future_work: str = Field(description="Suggested future research directions")
    relevance_score: float = Field(description="Relevance score from 0-10 for the research query")


class SummarizationAgent:
    """Agent responsible for extracting key findings from research papers"""
    
    def __init__(self, provider: str = "ollama", model: Optional[str] = None, temperature: float = 0.3, use_fulltext: bool = False):
        """
        Initialize SummarizationAgent
        
        Args:
            provider: LLM provider (openai, ollama)
            model: Model name (provider-specific, None for default)
            temperature: Temperature for LLM generation
            use_fulltext: Whether to download and analyze full PDF text
        """
        self.llm = LLMProvider.create_llm(provider, model, temperature)
        self.parser = PydanticOutputParser(pydantic_object=PaperSummary)
        self.use_fulltext = use_fulltext
        
        # Initialize PDF manager and fulltext analyzer if enabled
        if use_fulltext:
            self.pdf_manager = PDFManager()
            self.fulltext_analyzer = FullTextAnalyzer()
            logger.info(f"SummarizationAgent initialized with {provider} (full-text analysis enabled)")
        else:
            self.pdf_manager = None
            self.fulltext_analyzer = None
            logger.info(f"SummarizationAgent initialized with {provider}")
    
    def summarize_paper(self, paper, research_query: str = "") -> Dict:
        """
        Summarize a single research paper
        
        Args:
            paper: Paper object or dictionary containing paper information
            research_query: Original research query for relevance assessment
            
        Returns:
            Dictionary containing structured summary
        """
        # Convert Paper object to dictionary if needed
        if hasattr(paper, 'to_dict'):
            paper_dict = paper.to_dict()
        elif isinstance(paper, dict):
            paper_dict = paper
        else:
            paper_dict = {
                'title': str(getattr(paper, 'title', 'Unknown')),
                'authors': getattr(paper, 'authors', []),
                'abstract': getattr(paper, 'abstract', ''),
                'paper_id': getattr(paper, 'paper_id', ''),
                'url': getattr(paper, 'url', '')
            }
        
        logger.info(f"Summarizing paper: {paper_dict.get('title', 'Unknown')[:50]}...")
        
        # Try to get full-text analysis if enabled
        fulltext_info = None
        if self.use_fulltext and self.pdf_manager and self.fulltext_analyzer:
            try:
                # Prepare paper dict for PDF manager (needs pdf_url and paper_id keys)
                pdf_paper = {
                    'pdf_url': paper_dict.get('url', ''),
                    'paper_id': paper_dict.get('paper_id', '')
                }
                
                if pdf_paper['pdf_url'] and pdf_paper['paper_id']:
                    logger.info(f"Downloading and analyzing full text for paper: {pdf_paper['paper_id']}")
                    
                    # Run async function in event loop
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    
                    full_text = loop.run_until_complete(
                        self.pdf_manager.get_full_text(pdf_paper)
                    )
                    
                    if full_text:
                        logger.info(f"Full text extracted ({len(full_text)} chars), analyzing...")
                        fulltext_info = self.fulltext_analyzer.analyze_full_paper(full_text)
                        logger.info(f"Full-text analysis complete: {len(fulltext_info.get('sections', {}))} sections found")
                    else:
                        logger.warning(f"Failed to extract full text for paper {pdf_paper['paper_id']}")
            except Exception as e:
                logger.warning(f"Error during full-text analysis: {e}")
                fulltext_info = None
        
        # Choose prompt template based on whether we have full-text info
        if fulltext_info:
            prompt_template = self._create_fulltext_prompt()
        else:
            prompt_template = self._create_abstract_prompt()
        
        try:
            # Prepare paper text
            authors_str = ", ".join(paper_dict.get("authors", [])[:5])  # Limit to first 5 authors
            if len(paper_dict.get("authors", [])) > 5:
                authors_str += " et al."
            
            # Create the prompt with appropriate context
            if fulltext_info:
                # Include full-text analysis in prompt
                methodology_text = fulltext_info.get('sections', {}).get('methodology', '')[:1000]
                results_text = fulltext_info.get('sections', {}).get('results', '')[:1000]
                key_methodology = '\n'.join(f"- {s}" for s in fulltext_info.get('key_methodology', []))
                key_results = '\n'.join(f"- {s}" for s in fulltext_info.get('key_results', []))
                
                messages = prompt_template.format_messages(
                    research_query=research_query or "General academic research",
                    title=paper_dict.get("title", ""),
                    authors=authors_str,
                    abstract=paper_dict.get("abstract", ""),
                    methodology=methodology_text,
                    results=results_text,
                    key_methodology=key_methodology,
                    key_results=key_results,
                    figures=fulltext_info.get('figures_count', 0),
                    tables=fulltext_info.get('tables_count', 0),
                    equations=fulltext_info.get('equations_count', 0),
                    format_instructions=self.parser.get_format_instructions()
                )
            else:
                # Use abstract-only prompt
                messages = prompt_template.format_messages(
                    research_query=research_query or "General academic research",
                    title=paper_dict.get("title", ""),
                    authors=authors_str,
                    abstract=paper_dict.get("abstract", ""),
                    format_instructions=self.parser.get_format_instructions()
                )
            
            # Get LLM response
            response = self.llm.invoke(messages)

            # Parse the structured output (try strict parser first, then fallbacks)
            try:
                summary = self.parser.parse(response.content)
                # PydanticOutputParser returns a pydantic model or dict-like
                try:
                    summary_dict = summary.dict()
                except Exception:
                    # handle pydantic v2 objects
                    summary_dict = getattr(summary, 'model_dump', lambda: summary)()
            except Exception as parse_err:
                logger.debug(f"Primary parse failed: {parse_err}. Attempting fallback JSON extraction.")
                summary_dict = None
                # Try to extract a JSON object from the model output
                try:
                    text = response.content if isinstance(response.content, str) else str(response.content)
                    m = re.search(r"(\{[\s\S]*\})", text)
                    if m:
                        obj = json.loads(m.group(1))
                        # Validate/normalize with PaperSummary
                        try:
                            # pydantic v2
                            summary_obj = PaperSummary.model_validate(obj)
                            summary_dict = summary_obj.model_dump()
                        except AttributeError:
                            # pydantic v1
                            summary_obj = PaperSummary.parse_obj(obj)
                            summary_dict = summary_obj.dict()
                    else:
                        logger.debug("No JSON blob found in model output during fallback parsing.")
                except Exception as fallback_err:
                    logger.error(f"Fallback parsing also failed: {fallback_err}")

                if summary_dict is None:
                    # final fallback: return a minimal summary with error note
                    logger.error("Unable to parse structured summary, returning minimal fallback summary.")
                    summary_dict = {
                        "key_findings": ["Error: could not parse model output into structured summary"],
                        "methodology": "Not available",
                        "results": "Not available",
                        "limitations": [],
                        "future_work": "Not available",
                        "relevance_score": 5.0
                    }
            summary_dict["paper_id"] = paper_dict.get("paper_id", "")
            summary_dict["title"] = paper_dict.get("title", "")
            summary_dict["url"] = paper_dict.get("url", "")
            
            logger.info(f"Successfully summarized paper with relevance score: {summary.relevance_score}")
            
            return summary_dict
            
        except Exception as e:
            logger.error(f"Error summarizing paper: {e}")
            
            # Return a basic summary on failure
            return {
                "paper_id": paper_dict.get("paper_id", ""),
                "title": paper_dict.get("title", ""),
                "url": paper_dict.get("url", ""),
                "key_findings": ["Error: Unable to extract key findings"],
                "methodology": "Not available",
                "results": "Not available",
                "limitations": [],
                "future_work": "Not available",
                "relevance_score": 5.0
            }
    
    def summarize_batch(self, papers: List, research_query: str = "") -> List[Dict]:
        """
        Summarize multiple papers
        
        Args:
            papers: List of Paper objects or dictionaries
            research_query: Original research query
            
        Returns:
            List of summary dictionaries
        """
        logger.info(f"Summarizing batch of {len(papers)} papers")
        
        summaries = []
        for i, paper in enumerate(papers, 1):
            logger.info(f"Processing paper {i}/{len(papers)}")
            summary = self.summarize_paper(paper, research_query)
            summaries.append(summary)
        
        logger.info(f"Completed summarization of {len(summaries)} papers")
        
        return summaries
    
    def extract_technical_details(self, paper: Dict) -> Dict:
        """
        Extract technical details like datasets, models, metrics
        
        Args:
            paper: Paper dictionary
            
        Returns:
            Dictionary with technical details
        """
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", "You are an expert at extracting technical details from research papers."),
            ("human", """Extract technical details from this paper:

Title: {title}
Abstract: {abstract}

Please identify:
1. Datasets used (if any)
2. Models or algorithms proposed/used
3. Evaluation metrics
4. Key hyperparameters or configurations
5. Baseline comparisons

Format your response as a JSON object.""")
        ])
        
        try:
            messages = prompt_template.format_messages(
                title=paper.get("title", ""),
                abstract=paper.get("abstract", "")
            )
            
            response = self.llm.invoke(messages)
            
            # Parse JSON response
            import json
            technical_details = json.loads(response.content)
            
            return technical_details
            
        except Exception as e:
            logger.error(f"Error extracting technical details: {e}")
            return {}
    
    def quick_summary(self, paper: Dict, max_words: int = 100) -> str:
        """
        Generate a quick summary in plain text
        
        Args:
            paper: Paper dictionary
            max_words: Maximum number of words
            
        Returns:
            Plain text summary
        """
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", "You are an expert at creating concise research summaries."),
            ("human", """Create a brief summary (max {max_words} words) of this paper:

Title: {title}
Abstract: {abstract}

Focus on the main contribution and key finding.""")
        ])
        
        try:
            messages = prompt_template.format_messages(
                title=paper.get("title", ""),
                abstract=paper.get("abstract", ""),
                max_words=max_words
            )
            
            response = self.llm.invoke(messages)
            
            return response.content.strip()
            
        except Exception as e:
            logger.error(f"Error creating quick summary: {e}")
            return paper.get("abstract", "")[:max_words * 6]  # Approximate word count
    
    def rank_by_relevance(self, summaries: List[Dict]) -> List[Dict]:
        """
        Rank papers by relevance score
        
        Args:
            summaries: List of summary dictionaries
            
        Returns:
            Sorted list of summaries
        """
        return sorted(summaries, key=lambda x: x.get("relevance_score", 0), reverse=True)
    
    def _create_abstract_prompt(self) -> ChatPromptTemplate:
        """Create prompt template for abstract-only analysis"""
        return ChatPromptTemplate.from_messages([
            ("system", """You are an expert research assistant specialized in analyzing academic papers.
Your task is to extract key information from research papers and provide structured summaries.
Be concise, accurate, and focus on the most important aspects."""),
            ("human", """Analyze the following research paper and extract key information.

Research Query Context: {research_query}

Paper Title: {title}

Authors: {authors}

Abstract: {abstract}

Please provide a structured summary with the following components:
1. Key Findings (3-5 main discoveries or contributions)
2. Methodology (research approach and methods used)
3. Results (main findings and conclusions)
4. Limitations (acknowledged limitations or constraints)
5. Future Work (suggested research directions)
6. Relevance Score (0-10, how relevant is this paper to the research query)

{format_instructions}""")
        ])
    
    def _create_fulltext_prompt(self) -> ChatPromptTemplate:
        """Create prompt template for full-text analysis"""
        return ChatPromptTemplate.from_messages([
            ("system", """You are an expert research assistant specialized in analyzing academic papers.
Your task is to extract key information from research papers using the full text and provide structured summaries.
Be concise, accurate, and focus on the most important aspects."""),
            ("human", """Analyze the following research paper using both abstract and full-text extracts.

Research Query Context: {research_query}

Paper Title: {title}

Authors: {authors}

Abstract: {abstract}

=== FULL-TEXT ANALYSIS ===

Methodology Section (excerpt):
{methodology}

Key Methodology Highlights:
{key_methodology}

Results Section (excerpt):
{results}

Key Results Highlights:
{key_results}

Paper contains: {figures} figures, {tables} tables, {equations} equations

=== END FULL-TEXT ANALYSIS ===

Please provide a structured summary with the following components:
1. Key Findings (3-5 main discoveries or contributions, use full-text insights)
2. Methodology (detailed research approach from methodology section)
3. Results (comprehensive findings from results section)
4. Limitations (acknowledged limitations or constraints)
5. Future Work (suggested research directions)
6. Relevance Score (0-10, how relevant is this paper to the research query)

{format_instructions}""")
        ])