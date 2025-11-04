"""
Research Coordinator - Orchestrates multi-agent research workflow using LangGraph
"""
from typing import Dict, List, TypedDict, Annotated, Optional
import logging
from langgraph.graph import StateGraph, END
import operator

from agents.search_agent import SearchAgent
from agents.summarization_agent import SummarizationAgent
from agents.synthesis_agent import SynthesisAgent
from agents.citation_agent import CitationAgent
from agents.writing_agent import WritingAgent

logger = logging.getLogger(__name__)


class ResearchState(TypedDict):
    """State object for research workflow"""
    research_query: str
    max_papers: int
    papers: Annotated[List[Dict], operator.add]
    summaries: Annotated[List[Dict], operator.add]
    synthesis: Dict
    citations: List[str]
    final_report: str
    error: str
    current_step: str


class ResearchCoordinator:
    """Coordinates multi-agent research workflow"""
    
    def __init__(
        self,
        provider: str = "ollama",
        model: Optional[str] = None,
        temperature: float = 0.5,
        citation_style: str = "APA",
        use_vector_store: bool = False,
        use_fulltext: bool = False,
        sources: List[str] = None,
        dedup_threshold: float = 0.15
    ):
        """
        Initialize Research Coordinator
        
        Args:
            provider: LLM provider (ollama, openai)
            model: Model name (None for default)
            temperature: Temperature for generation
            citation_style: Citation style (APA, MLA, Chicago, etc.)
            use_vector_store: Enable vector store for semantic search
            use_fulltext: Enable full-text PDF analysis
            sources: Paper sources to search (default: ["arxiv", "semantic_scholar"])
            dedup_threshold: Semantic similarity threshold for deduplication (0.05-0.30, default: 0.15)
        """
        # Initialize agents with the same LLM configuration
        if sources is None:
            sources = ["arxiv", "semantic_scholar"]
        self.search_agent = SearchAgent(
            use_vector_store=use_vector_store, 
            sources=sources, 
            dedup_threshold=dedup_threshold
        )
        self.summarization_agent = SummarizationAgent(provider, model, temperature, use_fulltext=use_fulltext)
        self.synthesis_agent = SynthesisAgent(provider, model, temperature)
        self.citation_agent = CitationAgent()
        self.writing_agent = WritingAgent(provider, model, temperature + 0.2)
        
        self.citation_style = citation_style
        self.use_vector_store = use_vector_store
        self.use_fulltext = use_fulltext
        
        # Build workflow graph
        self.workflow = self._build_workflow()
        
        logger.info(f"ResearchCoordinator initialized with {provider} (vector_store={use_vector_store}, fulltext={use_fulltext})")
    
    def _build_workflow(self) -> StateGraph:
        """
        Build the LangGraph workflow
        
        Returns:
            StateGraph workflow
        """
        workflow = StateGraph(ResearchState)
        
        # Add nodes
        workflow.add_node("search", self._search_papers)
        workflow.add_node("summarize", self._summarize_papers)
        workflow.add_node("synthesize", self._synthesize_findings)
        workflow.add_node("cite", self._generate_citations)
        workflow.add_node("write", self._write_report)
        
        # Define edges (workflow sequence)
        workflow.set_entry_point("search")
        workflow.add_edge("search", "summarize")
        workflow.add_edge("summarize", "synthesize")
        workflow.add_edge("synthesize", "cite")
        workflow.add_edge("cite", "write")
        workflow.add_edge("write", END)
        
        logger.info("Workflow graph built with 5 nodes")
        
        return workflow.compile()
    
    def _search_papers(self, state: ResearchState) -> ResearchState:
        """
        Search for relevant papers
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with papers
        """
        logger.info(f"Step 1/5: Searching for papers on '{state['research_query']}'")
        
        try:
            # Update SearchAgent's max_results based on current state
            self.search_agent.max_results = state.get("max_papers", 20)
            
            papers = self.search_agent.search(
                query=state["research_query"]
            )
            
            logger.info(f"Found {len(papers)} papers")
            
            # Note: Papers are already added to vector store during deduplication
            # if vector store is enabled, so no need to add them again here
            
            state["papers"] = papers
            state["current_step"] = "search_complete"
            
        except Exception as e:
            logger.error(f"Error in search step: {e}")
            state["error"] = f"Search failed: {str(e)}"
            state["papers"] = []
        
        return state
    
    def _summarize_papers(self, state: ResearchState) -> ResearchState:
        """
        Summarize each paper
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with summaries
        """
        logger.info(f"Step 2/5: Summarizing {len(state['papers'])} papers")
        
        try:
            papers = state.get("papers", [])
            
            if not papers:
                logger.warning("No papers to summarize")
                state["summaries"] = []
                return state
            
            summaries = self.summarization_agent.summarize_batch(
                papers=papers,
                research_query=state["research_query"]
            )
            
            logger.info(f"Generated {len(summaries)} summaries")
            
            state["summaries"] = summaries
            state["current_step"] = "summarization_complete"
            
        except Exception as e:
            logger.error(f"Error in summarization step: {e}")
            state["error"] = f"Summarization failed: {str(e)}"
            state["summaries"] = []
        
        return state
    
    def _synthesize_findings(self, state: ResearchState) -> ResearchState:
        """
        Synthesize findings across papers
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with synthesis
        """
        logger.info(f"Step 3/5: Synthesizing findings from {len(state['summaries'])} papers")
        
        try:
            summaries = state.get("summaries", [])
            
            if not summaries:
                logger.warning("No summaries to synthesize")
                state["synthesis"] = {}
                return state
            
            synthesis = self.synthesis_agent.synthesize(
                summaries=summaries,
                research_query=state["research_query"]
            )
            
            logger.info("Synthesis complete")
            
            state["synthesis"] = synthesis
            state["current_step"] = "synthesis_complete"
            
        except Exception as e:
            logger.error(f"Error in synthesis step: {e}")
            state["error"] = f"Synthesis failed: {str(e)}"
            state["synthesis"] = {}
        
        return state
    
    def _generate_citations(self, state: ResearchState) -> ResearchState:
        """
        Generate citations for all papers
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with citations
        """
        logger.info(f"Step 4/5: Generating {self.citation_style} citations")
        
        try:
            papers = state.get("papers", [])
            
            if not papers:
                logger.warning("No papers to cite")
                state["citations"] = []
                return state
            
            # Build citation network
            self.citation_agent.build_citation_network(papers)
            
            # Generate bibliography
            citations = self.citation_agent.generate_bibliography(
                papers=papers,
                style=self.citation_style
            )
            
            logger.info(f"Generated {len(citations)} citations")
            
            state["citations"] = citations
            state["current_step"] = "citations_complete"
            
        except Exception as e:
            logger.error(f"Error in citation step: {e}")
            state["error"] = f"Citation generation failed: {str(e)}"
            state["citations"] = []
        
        return state
    
    def _write_report(self, state: ResearchState) -> ResearchState:
        """
        Write final research report
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with final report
        """
        logger.info("Step 5/5: Writing final report")
        
        try:
            summaries = state.get("summaries", [])
            synthesis = state.get("synthesis", {})
            citations = state.get("citations", [])
            
            if not summaries:
                logger.warning("No summaries available for report")
                state["final_report"] = "Error: No data available for report generation"
                return state
            
            report = self.writing_agent.write_literature_review(
                research_query=state["research_query"],
                summaries=summaries,
                synthesis=synthesis,
                citations=citations,
                format="markdown"
            )
            
            logger.info(f"Final report generated ({len(report)} characters)")
            
            state["final_report"] = report
            state["current_step"] = "complete"
            
        except Exception as e:
            logger.error(f"Error in writing step: {e}")
            state["error"] = f"Report writing failed: {str(e)}"
            state["final_report"] = ""
        
        return state
    
    def run(
        self,
        research_query: str,
        max_papers: int = 20,
        verbose: bool = True
    ) -> Dict:
        """
        Run the complete research workflow
        
        Args:
            research_query: Research question
            max_papers: Maximum number of papers to analyze
            verbose: Whether to print progress
            
        Returns:
            Dictionary with results
        """
        logger.info(f"Starting research workflow for: {research_query}")
        
        # Initialize state
        initial_state: ResearchState = {
            "research_query": research_query,
            "max_papers": max_papers,
            "papers": [],
            "summaries": [],
            "synthesis": {},
            "citations": [],
            "final_report": "",
            "error": "",
            "current_step": "initializing"
        }
        
        try:
            # Execute workflow
            if verbose:
                print(f"\n{'='*60}")
                print(f"Starting Autonomous Research Agent")
                print(f"Query: {research_query}")
                print(f"Max Papers: {max_papers}")
                print(f"{'='*60}\n")
            
            final_state = self.workflow.invoke(initial_state)
            
            if verbose:
                print(f"\n{'='*60}")
                print(f"Research Complete!")
                print(f"Papers Found: {len(final_state.get('papers', []))}")
                print(f"Summaries Generated: {len(final_state.get('summaries', []))}")
                print(f"Citations Created: {len(final_state.get('citations', []))}")
                print(f"Final Step: {final_state.get('current_step', 'unknown')}")
                print(f"{'='*60}\n")
            
            return {
                "success": True,
                "papers": final_state.get("papers", []),
                "summaries": final_state.get("summaries", []),
                "synthesis": final_state.get("synthesis", {}),
                "citations": final_state.get("citations", []),
                "report": final_state.get("final_report", ""),
                "error": final_state.get("error", "")
            }
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            
            if verbose:
                print(f"\nError: {str(e)}\n")
            
            return {
                "success": False,
                "papers": [],
                "summaries": [],
                "synthesis": {},
                "citations": [],
                "report": "",
                "error": str(e)
            }
    
    def run_custom(
        self,
        research_query: str,
        max_papers: int = 20,
        steps: List[str] = None,
        verbose: bool = True
    ) -> Dict:
        """
        Run custom workflow with specific steps
        
        Args:
            research_query: Research question
            max_papers: Maximum papers
            steps: List of steps to execute (e.g., ["search", "summarize"])
            verbose: Print progress
            
        Returns:
            Results dictionary
        """
        if steps is None:
            steps = ["search", "summarize", "synthesize", "cite", "write"]
        
        logger.info(f"Running custom workflow with steps: {steps}")
        
        # Build custom workflow
        custom_workflow = StateGraph(ResearchState)
        
        # Map step names to functions
        step_functions = {
            "search": self._search_papers,
            "summarize": self._summarize_papers,
            "synthesize": self._synthesize_findings,
            "cite": self._generate_citations,
            "write": self._write_report
        }
        
        # Add nodes for specified steps
        for step in steps:
            if step in step_functions:
                custom_workflow.add_node(step, step_functions[step])
        
        # Create linear edges
        custom_workflow.set_entry_point(steps[0])
        for i in range(len(steps) - 1):
            custom_workflow.add_edge(steps[i], steps[i + 1])
        custom_workflow.add_edge(steps[-1], END)
        
        # Compile and run
        compiled_workflow = custom_workflow.compile()
        
        initial_state: ResearchState = {
            "research_query": research_query,
            "max_papers": max_papers,
            "papers": [],
            "summaries": [],
            "synthesis": {},
            "citations": [],
            "final_report": "",
            "error": "",
            "current_step": "initializing"
        }
        
        final_state = compiled_workflow.invoke(initial_state)
        
        return {
            "success": True,
            "papers": final_state.get("papers", []),
            "summaries": final_state.get("summaries", []),
            "synthesis": final_state.get("synthesis", {}),
            "citations": final_state.get("citations", []),
            "report": final_state.get("final_report", ""),
            "error": final_state.get("error", "")
        }
    
    def get_workflow_graph(self) -> str:
        """
        Get visual representation of workflow
        
        Returns:
            Mermaid diagram string
        """
        return """
graph TD
    A[Start] --> B[Search Agent]
    B --> C[Summarization Agent]
    C --> D[Synthesis Agent]
    D --> E[Citation Agent]
    E --> F[Writing Agent]
    F --> G[End]
    
    B -.-> |Papers| C
    C -.-> |Summaries| D
    D -.-> |Synthesis| E
    E -.-> |Citations| F
    F -.-> |Report| G
"""
