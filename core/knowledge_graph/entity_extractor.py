"""
Entity Extractor Module
Extracts entities (authors, concepts, methods, datasets) from research papers
"""
import re
import logging
from typing import List, Dict, Set, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class EntityExtractor:
    """Extract entities from research paper text"""
    
    def __init__(self):
        """Initialize entity extractor"""
        self.logger = logger
        
        # Common ML/AI concepts and methods (can be expanded)
        self.ml_methods = {
            'neural network', 'deep learning', 'machine learning', 'random forest',
            'svm', 'support vector machine', 'decision tree', 'naive bayes',
            'k-means', 'clustering', 'classification', 'regression',
            'convolutional neural network', 'cnn', 'rnn', 'lstm', 'gru',
            'transformer', 'bert', 'gpt', 'attention mechanism',
            'reinforcement learning', 'q-learning', 'policy gradient',
            'gradient descent', 'backpropagation', 'optimization'
        }
        
        # Common datasets (can be expanded)
        self.known_datasets = {
            'imagenet', 'mnist', 'cifar', 'coco', 'pascal voc',
            'glue', 'squad', 'wikipedia', 'common crawl',
            'wikitext', 'bookcorpus', 'openwebtext'
        }
        
        # Technical concepts
        self.tech_concepts = {
            'accuracy', 'precision', 'recall', 'f1 score', 'auc',
            'training', 'testing', 'validation', 'overfitting', 'underfitting',
            'hyperparameter', 'feature extraction', 'embedding',
            'loss function', 'activation function', 'dropout', 'batch normalization'
        }
    
    def extract_authors(self, paper_data: Dict) -> List[Dict[str, Any]]:
        """
        Extract author entities from paper data
        
        Args:
            paper_data: Paper data from Phase 2.1 extraction
            
        Returns:
            List of author entities with properties
        """
        authors = []
        
        # Extract from metadata if available
        if 'metadata' in paper_data and 'authors' in paper_data['metadata']:
            for author_name in paper_data['metadata']['authors']:
                author = {
                    'name': author_name.strip(),
                    'author_id': self._generate_author_id(author_name)
                }
                authors.append(author)
        
        # Try to extract from title page or first section
        if not authors and 'sections' in paper_data:
            authors = self._extract_authors_from_text(paper_data)
        
        self.logger.info(f"Extracted {len(authors)} authors")
        return authors
    
    def extract_concepts(self, paper_data: Dict, top_n: int = 20) -> List[Dict[str, Any]]:
        """
        Extract key concepts from paper
        
        Args:
            paper_data: Paper data from Phase 2.1 extraction
            top_n: Number of top concepts to extract
            
        Returns:
            List of concept entities with properties
        """
        concepts = {}
        
        # Combine text from title, abstract, and sections
        text_parts = []
        
        if 'title' in paper_data:
            text_parts.append(paper_data['title'])
        
        if 'abstract' in paper_data:
            text_parts.append(paper_data['abstract'])
        
        if 'full_text' in paper_data:
            text_parts.append(paper_data['full_text'])
        
        if 'sections' in paper_data:
            sections = paper_data['sections']
            # Handle both list and dict formats
            if isinstance(sections, list):
                for section in sections:
                    if isinstance(section, dict):
                        text = section.get('content') or section.get('text', '')
                        text_parts.append(text)
                    elif isinstance(section, str):
                        text_parts.append(section)
            elif isinstance(sections, dict):
                for section_content in sections.values():
                    if isinstance(section_content, str):
                        text_parts.append(section_content)
        
        full_text = ' '.join(str(part) for part in text_parts).lower()
        
        # Extract known technical concepts
        for concept in self.tech_concepts:
            count = len(re.findall(r'\b' + re.escape(concept) + r'\b', full_text, re.IGNORECASE))
            if count > 0:
                concept_id = self._generate_concept_id(concept)
                concepts[concept_id] = {
                    'name': concept,
                    'concept_id': concept_id,
                    'frequency': count,
                    'category': 'technical_concept'
                }
        
        # Extract key phrases using simple heuristics
        # (In production, would use more sophisticated NLP/LLM extraction)
        key_phrases = self._extract_key_phrases(full_text)
        for phrase, count in key_phrases.items():
            if phrase not in self.tech_concepts and len(phrase.split()) <= 3:
                concept_id = self._generate_concept_id(phrase)
                if concept_id not in concepts:
                    concepts[concept_id] = {
                        'name': phrase,
                        'concept_id': concept_id,
                        'frequency': count,
                        'category': 'domain_concept'
                    }
        
        # Sort by frequency and return top N
        sorted_concepts = sorted(
            concepts.values(),
            key=lambda x: x['frequency'],
            reverse=True
        )[:top_n]
        
        self.logger.info(f"Extracted {len(sorted_concepts)} concepts")
        return sorted_concepts
    
    def extract_methods(self, paper_data: Dict) -> List[Dict[str, Any]]:
        """
        Extract methods/algorithms from paper
        
        Args:
            paper_data: Paper data from Phase 2.1 extraction
            
        Returns:
            List of method entities with properties
        """
        methods = {}
        
        # Combine text from all sections
        text_parts = []
        
        if 'full_text' in paper_data:
            text_parts.append(paper_data['full_text'])
        
        if 'sections' in paper_data:
            sections = paper_data['sections']
            if isinstance(sections, list):
                for section in sections:
                    if isinstance(section, dict):
                        text = section.get('content') or section.get('text', '')
                        text_parts.append(text)
            elif isinstance(sections, dict):
                for section_content in sections.values():
                    if isinstance(section_content, str):
                        text_parts.append(section_content)
        
        full_text = ' '.join(str(part) for part in text_parts).lower()
        
        # Extract known ML methods
        for method in self.ml_methods:
            count = len(re.findall(r'\b' + re.escape(method) + r'\b', full_text, re.IGNORECASE))
            if count > 0:
                method_id = self._generate_method_id(method)
                methods[method_id] = {
                    'name': method,
                    'method_id': method_id,
                    'frequency': count,
                    'category': 'machine_learning'
                }
        
        # Extract algorithm names (simple pattern matching)
        algorithm_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:algorithm|method|approach))\b'
        algorithm_matches = re.finditer(algorithm_pattern, ' '.join(text_parts))
        
        for match in algorithm_matches:
            method_name = match.group(1).lower()
            method_id = self._generate_method_id(method_name)
            if method_id not in methods:
                methods[method_id] = {
                    'name': method_name,
                    'method_id': method_id,
                    'category': 'algorithm'
                }
        
        self.logger.info(f"Extracted {len(methods)} methods")
        return list(methods.values())
    
    def extract_datasets(self, paper_data: Dict) -> List[Dict[str, Any]]:
        """
        Extract datasets mentioned in paper
        
        Args:
            paper_data: Paper data from Phase 2.1 extraction
            
        Returns:
            List of dataset entities with properties
        """
        datasets = {}
        
        # Combine text from all sections
        text_parts = []
        
        if 'full_text' in paper_data:
            text_parts.append(paper_data['full_text'])
        
        if 'sections' in paper_data:
            sections = paper_data['sections']
            if isinstance(sections, list):
                for section in sections:
                    if isinstance(section, dict):
                        text = section.get('content') or section.get('text', '')
                        text_parts.append(text)
            elif isinstance(sections, dict):
                for section_content in sections.values():
                    if isinstance(section_content, str):
                        text_parts.append(section_content)
        
        full_text = ' '.join(str(part) for part in text_parts).lower()
        
        # Extract known datasets
        for dataset in self.known_datasets:
            if dataset in full_text:
                dataset_id = self._generate_dataset_id(dataset)
                datasets[dataset_id] = {
                    'name': dataset,
                    'dataset_id': dataset_id
                }
        
        # Extract dataset patterns (e.g., "X dataset", "X corpus")
        dataset_pattern = r'\b([A-Z][a-zA-Z0-9\-]+(?:\s+[A-Z][a-zA-Z0-9\-]+)*)\s+(?:dataset|corpus|benchmark)\b'
        dataset_matches = re.finditer(dataset_pattern, ' '.join(text_parts))
        
        for match in dataset_matches:
            dataset_name = match.group(1).strip()
            dataset_id = self._generate_dataset_id(dataset_name.lower())
            if dataset_id not in datasets:
                datasets[dataset_id] = {
                    'name': dataset_name,
                    'dataset_id': dataset_id
                }
        
        self.logger.info(f"Extracted {len(datasets)} datasets")
        return list(datasets.values())
    
    def extract_all_entities(self, paper_data: Dict) -> Dict[str, List[Dict]]:
        """
        Extract all entity types from paper
        
        Args:
            paper_data: Paper data from Phase 2.1 extraction
            
        Returns:
            Dictionary with entity types as keys and lists of entities as values
        """
        return {
            'authors': self.extract_authors(paper_data),
            'concepts': self.extract_concepts(paper_data),
            'methods': self.extract_methods(paper_data),
            'datasets': self.extract_datasets(paper_data)
        }
    
    # Helper methods
    
    def _generate_author_id(self, name: str) -> str:
        """Generate unique ID for author"""
        return f"author_{name.lower().replace(' ', '_')}"
    
    def _generate_concept_id(self, concept: str) -> str:
        """Generate unique ID for concept"""
        return f"concept_{concept.lower().replace(' ', '_')}"
    
    def _generate_method_id(self, method: str) -> str:
        """Generate unique ID for method"""
        return f"method_{method.lower().replace(' ', '_')}"
    
    def _generate_dataset_id(self, dataset: str) -> str:
        """Generate unique ID for dataset"""
        return f"dataset_{dataset.lower().replace(' ', '_').replace('-', '_')}"
    
    def _extract_authors_from_text(self, paper_data: Dict) -> List[Dict[str, Any]]:
        """Extract authors from paper text (fallback method)"""
        authors = []
        
        # Look for author patterns in sections
        if 'sections' in paper_data:
            sections = paper_data['sections']
            text = ''
            
            # Handle both list and dict formats
            if isinstance(sections, list) and len(sections) > 0:
                first_section = sections[0]
                text = first_section.get('content') or first_section.get('text', '')
            elif isinstance(sections, dict):
                # Try common section names for introduction
                for section_key in ['introduction', 'abstract', 'methodology']:
                    if section_key in sections:
                        text = sections[section_key]
                        break
            
            if text:
                # Simple pattern: look for capitalized names
                # (In production, would use NER)
                name_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b'
                potential_names = re.findall(name_pattern, str(text)[:1000])
                
                # Filter to likely author names (appears near beginning)
                for name in potential_names[:5]:  # Limit to first 5 names
                    authors.append({
                        'name': name,
                        'author_id': self._generate_author_id(name)
                    })
        
        return authors
    
    def _extract_key_phrases(self, text: str, min_freq: int = 2) -> Dict[str, int]:
        """Extract key phrases using simple frequency analysis"""
        # Tokenize into bigrams and trigrams
        words = re.findall(r'\b[a-z]+\b', text.lower())
        
        phrases = {}
        
        # Bigrams
        for i in range(len(words) - 1):
            phrase = f"{words[i]} {words[i+1]}"
            phrases[phrase] = phrases.get(phrase, 0) + 1
        
        # Trigrams
        for i in range(len(words) - 2):
            phrase = f"{words[i]} {words[i+1]} {words[i+2]}"
            phrases[phrase] = phrases.get(phrase, 0) + 1
        
        # Filter by minimum frequency
        return {k: v for k, v in phrases.items() if v >= min_freq}
