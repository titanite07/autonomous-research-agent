"""
Synthesis Agent - Identifies patterns, trends, and gaps across multiple papers
"""
from typing import Dict, List, Tuple, Optional
from collections import Counter
import logging
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llm_config import LLMProvider

logger = logging.getLogger(__name__)


class ResearchSynthesis(BaseModel):
    """Structured synthesis of research findings"""
    common_themes: List[str] = Field(description="Common themes across papers")
    trends: List[str] = Field(description="Emerging trends identified")
    contradictions: List[str] = Field(description="Contradictory findings or debates")
    research_gaps: List[str] = Field(description="Identified research gaps")
    methodological_patterns: List[str] = Field(description="Common methodologies")
    key_authors: List[str] = Field(description="Frequently cited authors")
    temporal_insights: str = Field(description="How research evolved over time")


class SynthesisAgent:
    """Agent responsible for synthesizing insights across multiple papers"""
    
    def __init__(self, provider: str = "ollama", model: Optional[str] = None, temperature: float = 0.5):
        """
        Initialize SynthesisAgent
        
        Args:
            provider: LLM provider
            model: Model name
            temperature: Temperature for generation
        """
        self.llm = LLMProvider.create_llm(provider, model, temperature)
        self.vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
        
        logger.info(f"SynthesisAgent initialized with {provider}")
    
    def synthesize(self, summaries: List[Dict], research_query: str = "") -> Dict:
        """
        Synthesize insights across all paper summaries
        
        Args:
            summaries: List of paper summaries
            research_query: Original research query
            
        Returns:
            Dictionary containing synthesis results
        """
        logger.info(f"Synthesizing insights from {len(summaries)} papers")
        
        # Combine key findings
        all_findings = []
        for summary in summaries:
            all_findings.extend(summary.get("key_findings", []))
        
        # Combine methodologies
        methodologies = [s.get("methodology", "") for s in summaries]
        
        # Combine results
        results = [s.get("results", "") for s in summaries]
        
        # Create synthesis prompt
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are an expert research synthesizer who identifies patterns, trends, and gaps across multiple research papers.
Analyze the collective findings to provide high-level insights that go beyond individual papers."""),
            ("human", """Analyze the following research papers and provide a comprehensive synthesis.

Research Query: {research_query}

Total Papers Analyzed: {num_papers}

All Key Findings:
{findings}

Methodologies Used:
{methodologies}

Results Summary:
{results}

Please provide:
1. Common Themes (3-5 recurring topics or ideas)
2. Trends (emerging patterns or directions in the research)
3. Contradictions (conflicting findings or debates)
4. Research Gaps (areas that need more investigation)
5. Methodological Patterns (common approaches used)
6. Key Authors (if patterns of frequent citations exist)
7. Temporal Insights (how research evolved, if time data available)

Be specific and provide actionable insights.""")
        ])
        
        try:
            messages = prompt_template.format_messages(
                research_query=research_query or "General research",
                num_papers=len(summaries),
                findings="\n".join([f"- {f}" for f in all_findings[:50]]),  # Limit to 50 findings
                methodologies="\n".join([f"- {m}" for m in methodologies[:30]]),
                results="\n".join([f"- {r}" for r in results[:30]])
            )
            
            response = self.llm.invoke(messages)
            
            # Parse response (assuming structured format)
            synthesis_text = response.content
            
            # Also perform computational analysis
            clusters = self._cluster_papers(summaries)
            topic_keywords = self._extract_keywords(summaries)
            temporal_analysis = self._analyze_temporal_patterns(summaries)
            
            return {
                "synthesis_text": synthesis_text,
                "paper_clusters": clusters,
                "topic_keywords": topic_keywords,
                "temporal_patterns": temporal_analysis,
                "total_papers": len(summaries),
                "avg_relevance": np.mean([s.get("relevance_score", 5) for s in summaries])
            }
            
        except Exception as e:
            logger.error(f"Error during synthesis: {e}")
            
            return {
                "synthesis_text": "Error: Unable to generate synthesis",
                "paper_clusters": {},
                "topic_keywords": [],
                "temporal_patterns": {},
                "total_papers": len(summaries),
                "avg_relevance": 5.0
            }
    
    def _cluster_papers(self, summaries: List[Dict], n_clusters: int = 3) -> Dict:
        """
        Cluster papers based on content similarity
        
        Args:
            summaries: List of paper summaries
            n_clusters: Number of clusters
            
        Returns:
            Dictionary mapping cluster IDs to paper IDs
        """
        try:
            # Combine title and key findings for clustering
            texts = []
            for summary in summaries:
                text = f"{summary.get('title', '')} "
                text += " ".join(summary.get('key_findings', []))
                texts.append(text)
            
            if len(texts) < n_clusters:
                n_clusters = max(1, len(texts) // 2)
            
            # Vectorize and cluster
            vectors = self.vectorizer.fit_transform(texts)
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            labels = kmeans.fit_predict(vectors)
            
            # Group papers by cluster
            clusters = {}
            for i, label in enumerate(labels):
                cluster_id = f"cluster_{label}"
                if cluster_id not in clusters:
                    clusters[cluster_id] = []
                clusters[cluster_id].append({
                    "paper_id": summaries[i].get("paper_id", ""),
                    "title": summaries[i].get("title", ""),
                    "relevance": summaries[i].get("relevance_score", 0)
                })
            
            logger.info(f"Clustered papers into {n_clusters} groups")
            
            return clusters
            
        except Exception as e:
            logger.error(f"Error clustering papers: {e}")
            return {}
    
    def _extract_keywords(self, summaries: List[Dict], top_n: int = 20) -> List[Tuple[str, float]]:
        """
        Extract most important keywords across all papers
        
        Args:
            summaries: List of summaries
            top_n: Number of keywords to return
            
        Returns:
            List of (keyword, score) tuples
        """
        try:
            # Combine all text
            all_text = []
            for summary in summaries:
                text = f"{summary.get('title', '')} "
                text += " ".join(summary.get('key_findings', []))
                text += f" {summary.get('methodology', '')} "
                text += f" {summary.get('results', '')}"
                all_text.append(text)
            
            # Fit vectorizer
            vectors = self.vectorizer.fit_transform(all_text)
            
            # Get feature names and average scores
            feature_names = self.vectorizer.get_feature_names_out()
            avg_scores = np.array(vectors.mean(axis=0)).flatten()
            
            # Get top keywords
            top_indices = avg_scores.argsort()[-top_n:][::-1]
            keywords = [(feature_names[i], float(avg_scores[i])) for i in top_indices]
            
            logger.info(f"Extracted {len(keywords)} keywords")
            
            return keywords
            
        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            return []
    
    def _analyze_temporal_patterns(self, summaries: List[Dict]) -> Dict:
        """
        Analyze how research evolved over time
        
        Args:
            summaries: List of summaries
            
        Returns:
            Dictionary with temporal insights
        """
        # This would require publication dates from papers
        # For now, return placeholder
        return {
            "time_span": "Not available",
            "publication_trend": "Analysis requires date information",
            "evolving_topics": []
        }
    
    def identify_contradictions(self, summaries: List[Dict]) -> List[Dict]:
        """
        Identify potential contradictions between papers
        
        Args:
            summaries: List of summaries
            
        Returns:
            List of contradiction descriptions
        """
        logger.info("Analyzing papers for contradictions")
        
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", "You are an expert at identifying contradictions and debates in research."),
            ("human", """Compare these research findings and identify any contradictions or debates:

{findings}

List any contradictory findings, conflicting methodologies, or ongoing debates.""")
        ])
        
        try:
            # Collect findings from all papers
            findings_text = ""
            for i, summary in enumerate(summaries[:20]):  # Limit to 20 papers
                findings_text += f"\nPaper {i+1}: {summary.get('title', '')}\n"
                findings_text += f"Findings: {', '.join(summary.get('key_findings', []))}\n"
            
            messages = prompt_template.format_messages(findings=findings_text)
            response = self.llm.invoke(messages)
            
            return [{"contradiction": response.content}]
            
        except Exception as e:
            logger.error(f"Error identifying contradictions: {e}")
            return []
    
    def find_research_gaps(self, summaries: List[Dict], research_query: str = "") -> List[str]:
        """
        Identify gaps in the current research
        
        Args:
            summaries: List of summaries
            research_query: Original query
            
        Returns:
            List of research gaps
        """
        logger.info("Identifying research gaps")
        
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", "You are an expert at identifying research gaps and future directions."),
            ("human", """Based on these research papers, identify gaps and unexplored areas:

Research Query: {query}

Paper Summaries:
{summaries}

List 5-7 specific research gaps or unexplored areas.""")
        ])
        
        try:
            # Create summary text
            summary_text = ""
            for summary in summaries[:15]:  # Limit to 15 papers
                summary_text += f"\n- {summary.get('title', '')}: "
                summary_text += f"{summary.get('results', '')}\n"
            
            messages = prompt_template.format_messages(
                query=research_query,
                summaries=summary_text
            )
            
            response = self.llm.invoke(messages)
            
            # Parse response into list
            gaps = [line.strip() for line in response.content.split('\n') if line.strip()]
            
            return gaps
            
        except Exception as e:
            logger.error(f"Error finding research gaps: {e}")
            return []
    
    def generate_visual_summary(self, summaries: List[Dict]) -> Dict:
        """
        Generate data for visualizations
        
        Args:
            summaries: List of summaries
            
        Returns:
            Dictionary with visualization data
        """
        return {
            "relevance_distribution": [s.get("relevance_score", 0) for s in summaries],
            "cluster_sizes": self._get_cluster_sizes(summaries),
            "keyword_cloud": self._extract_keywords(summaries, top_n=50),
            "paper_count": len(summaries)
        }
    
    def _get_cluster_sizes(self, summaries: List[Dict]) -> Dict:
        """Get sizes of paper clusters"""
        clusters = self._cluster_papers(summaries)
        return {k: len(v) for k, v in clusters.items()}
