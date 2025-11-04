"""
Relevance Calculator - Calculate semantic similarity between query and paper
Uses TF-IDF and cosine similarity for fast relevance scoring
"""

from typing import Dict, List
import re
import math
from collections import Counter


class RelevanceCalculator:
    """Calculate relevance score between query and paper abstract"""
    
    def __init__(self):
        # Common stop words to ignore
        self.stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'this', 'we', 'our', 'their', 'which'
        }
    
    def preprocess_text(self, text: str) -> List[str]:
        """
        Preprocess text for similarity calculation
        
        Args:
            text: Input text
            
        Returns:
            List of processed tokens
        """
        if not text:
            return []
        
        # Convert to lowercase and remove special characters
        text = text.lower()
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        
        # Tokenize and remove stop words
        tokens = [
            word for word in text.split()
            if word and len(word) > 2 and word not in self.stop_words
        ]
        
        return tokens
    
    def calculate_cosine_similarity(self, tokens1: List[str], tokens2: List[str]) -> float:
        """
        Calculate cosine similarity between two token lists
        
        Args:
            tokens1: First token list
            tokens2: Second token list
            
        Returns:
            Cosine similarity score (0-1)
        """
        if not tokens1 or not tokens2:
            return 0.0
        
        # Create frequency vectors
        freq1 = Counter(tokens1)
        freq2 = Counter(tokens2)
        
        # Get all unique tokens
        all_tokens = set(tokens1) | set(tokens2)
        
        # Calculate dot product and magnitudes
        dot_product = sum(freq1.get(token, 0) * freq2.get(token, 0) for token in all_tokens)
        magnitude1 = math.sqrt(sum(count ** 2 for count in freq1.values()))
        magnitude2 = math.sqrt(sum(count ** 2 for count in freq2.values()))
        
        # Avoid division by zero
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        # Calculate cosine similarity
        similarity = dot_product / (magnitude1 * magnitude2)
        
        return similarity
    
    def calculate_keyword_overlap(self, query_tokens: List[str], text_tokens: List[str]) -> float:
        """
        Calculate keyword overlap ratio
        
        Args:
            query_tokens: Query tokens
            text_tokens: Text tokens
            
        Returns:
            Overlap ratio (0-1)
        """
        if not query_tokens:
            return 0.0
        
        query_set = set(query_tokens)
        text_set = set(text_tokens)
        
        # Calculate Jaccard similarity
        intersection = query_set & text_set
        union = query_set | text_set
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def calculate_relevance(
        self, 
        query: str, 
        title: str, 
        abstract: str = None,
        keywords: List[str] = None
    ) -> float:
        """
        Calculate relevance score between query and paper
        
        Args:
            query: Search query
            title: Paper title
            abstract: Paper abstract (optional)
            keywords: Paper keywords (optional)
            
        Returns:
            Relevance score (0-1)
        """
        # Preprocess inputs
        query_tokens = self.preprocess_text(query)
        title_tokens = self.preprocess_text(title)
        
        if not query_tokens:
            return 0.5  # Default score if query is empty
        
        # Calculate title similarity (weighted more heavily)
        title_similarity = self.calculate_cosine_similarity(query_tokens, title_tokens)
        title_overlap = self.calculate_keyword_overlap(query_tokens, title_tokens)
        title_score = (title_similarity * 0.7 + title_overlap * 0.3)
        
        # Calculate abstract similarity if available
        abstract_score = 0.0
        if abstract:
            abstract_tokens = self.preprocess_text(abstract)
            abstract_similarity = self.calculate_cosine_similarity(query_tokens, abstract_tokens)
            abstract_overlap = self.calculate_keyword_overlap(query_tokens, abstract_tokens)
            abstract_score = (abstract_similarity * 0.7 + abstract_overlap * 0.3)
        
        # Calculate keywords similarity if available
        keywords_score = 0.0
        if keywords:
            keywords_text = ' '.join(keywords)
            keywords_tokens = self.preprocess_text(keywords_text)
            keywords_similarity = self.calculate_cosine_similarity(query_tokens, keywords_tokens)
            keywords_overlap = self.calculate_keyword_overlap(query_tokens, keywords_tokens)
            keywords_score = (keywords_similarity * 0.7 + keywords_overlap * 0.3)
        
        # Weighted combination
        # Title is most important (50%), abstract (35%), keywords (15%)
        if abstract and keywords:
            final_score = (title_score * 0.5 + abstract_score * 0.35 + keywords_score * 0.15)
        elif abstract:
            final_score = (title_score * 0.6 + abstract_score * 0.4)
        elif keywords:
            final_score = (title_score * 0.7 + keywords_score * 0.3)
        else:
            final_score = title_score
        
        # Apply boost for exact phrase matches in title (case-insensitive)
        query_lower = query.lower()
        title_lower = title.lower()
        if query_lower in title_lower:
            final_score = min(1.0, final_score + 0.2)  # +20% boost for exact match
        
        # Apply boost for high keyword overlap
        if title_overlap > 0.5:  # More than 50% of query words in title
            final_score = min(1.0, final_score + 0.1)  # +10% boost
        
        # Ensure score is between 0 and 1
        final_score = max(0.0, min(1.0, final_score))
        
        # Scale scores to use more of the range (0.1 - 1.0 instead of 0.0 - 1.0)
        # This makes differences more visible
        final_score = 0.1 + (final_score * 0.9)
        
        return final_score
    
    def calculate_batch_relevance(
        self, 
        query: str, 
        papers: List[Dict]
    ) -> List[Dict]:
        """
        Calculate relevance scores for multiple papers
        
        Args:
            query: Search query
            papers: List of paper dictionaries
            
        Returns:
            Papers with relevance_score field added
        """
        for paper in papers:
            relevance = self.calculate_relevance(
                query=query,
                title=paper.get('title', ''),
                abstract=paper.get('abstract', ''),
                keywords=paper.get('keywords', [])
            )
            paper['relevance_score'] = relevance
        
        return papers


# Singleton instance
_calculator = None

def get_relevance_calculator() -> RelevanceCalculator:
    """Get or create relevance calculator instance"""
    global _calculator
    if _calculator is None:
        _calculator = RelevanceCalculator()
    return _calculator
