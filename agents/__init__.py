"""Agents package for autonomous research agent"""

# Lazy imports to avoid circular dependencies
def __getattr__(name):
    if name == "SearchAgent":
        from .search_agent import SearchAgent
        return SearchAgent
    elif name == "Paper":
        from .search_agent import Paper
        return Paper
    elif name == "SummarizationAgent":
        from .summarization_agent import SummarizationAgent
        return SummarizationAgent
    elif name == "PaperSummary":
        from .summarization_agent import PaperSummary
        return PaperSummary
    elif name == "SynthesisAgent":
        from .synthesis_agent import SynthesisAgent
        return SynthesisAgent
    elif name == "ResearchSynthesis":
        from .synthesis_agent import ResearchSynthesis
        return ResearchSynthesis
    elif name == "CitationAgent":
        from .citation_agent import CitationAgent
        return CitationAgent
    elif name == "WritingAgent":
        from .writing_agent import WritingAgent
        return WritingAgent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "SearchAgent",
    "Paper",
    "SummarizationAgent",
    "PaperSummary",
    "SynthesisAgent",
    "ResearchSynthesis",
    "CitationAgent",
    "WritingAgent",
]
