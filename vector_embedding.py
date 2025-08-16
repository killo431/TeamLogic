"""
Vector Embedding Module for Knowledge Base Framework
Handles semantic search and vector operations for entities
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import json
import pickle
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import PCA
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
except:
    pass


class VectorEmbeddingError(Exception):
    """Custom exception for vector embedding operations"""
    pass


class TextPreprocessor:
    """Handles text preprocessing for embedding generation"""
    
    def __init__(self):
        self.stemmer = PorterStemmer()
        try:
            self.stop_words = set(stopwords.words('english'))
        except LookupError:
            self.stop_words = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'])
        self.logger = logging.getLogger(__name__)
        
    def preprocess_text(self, text: str) -> str:
        """Clean and preprocess text for embedding"""
        if not isinstance(text, str):
            return ""
            
        # Convert to lowercase
        text = text.lower()
        
        # Tokenize
        try:
            tokens = word_tokenize(text)
        except LookupError:
            # Fallback tokenization if NLTK punkt is not available
            tokens = text.split()
            
        # Remove stop words and stem
        processed_tokens = []
        for token in tokens:
            if token.isalpha() and token not in self.stop_words:
                stemmed_token = self.stemmer.stem(token)
                processed_tokens.append(stemmed_token)
                
        return ' '.join(processed_tokens)
        
    def extract_text_from_entity(self, entity_data: Dict[str, Any]) -> str:
        """Extract searchable text from entity attributes"""
        text_parts = []
        
        # Add entity ID and type
        text_parts.append(entity_data.get('id', ''))
        text_parts.append(entity_data.get('type', ''))
        
        # Extract text from attributes
        attributes = entity_data.get('attributes', {})
        for key, value in attributes.items():
            if isinstance(value, str):
                text_parts.append(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        text_parts.append(item)
            elif isinstance(value, dict):
                # Extract text from nested dict
                text_parts.extend(self._extract_text_from_dict(value))
                
        # Join all text parts
        combined_text = ' '.join(text_parts)
        return self.preprocess_text(combined_text)
        
    def _extract_text_from_dict(self, data: Dict[str, Any]) -> List[str]:
        """Recursively extract text from nested dictionary"""
        text_parts = []
        for key, value in data.items():
            if isinstance(value, str):
                text_parts.append(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        text_parts.append(item)
            elif isinstance(value, dict):
                text_parts.extend(self._extract_text_from_dict(value))
        return text_parts


class VectorEmbedder:
    """Generates and manages vector embeddings for entities"""
    
    def __init__(self, embedding_method: str = "tfidf", max_features: int = 1000):
        self.embedding_method = embedding_method
        self.max_features = max_features
        self.preprocessor = TextPreprocessor()
        self.vectorizer = None
        self.embeddings: Dict[str, np.ndarray] = {}
        self.entity_texts: Dict[str, str] = {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize vectorizer
        self._initialize_vectorizer()
        
    def _initialize_vectorizer(self):
        """Initialize the vectorizer based on embedding method"""
        if self.embedding_method == "tfidf":
            self.vectorizer = TfidfVectorizer(
                max_features=self.max_features,
                ngram_range=(1, 2),  # Use both unigrams and bigrams
                min_df=1,
                max_df=0.95,
                stop_words='english'
            )
        else:
            raise VectorEmbeddingError(f"Unsupported embedding method: {self.embedding_method}")
            
    def fit_embeddings(self, entities: List[Dict[str, Any]]):
        """Fit embeddings on a collection of entities"""
        if not entities:
            raise VectorEmbeddingError("No entities provided for fitting")
            
        # Extract text from all entities
        entity_texts = []
        entity_ids = []
        
        for entity in entities:
            entity_id = entity.get('id')
            if not entity_id:
                continue
                
            text = self.preprocessor.extract_text_from_entity(entity)
            if text.strip():  # Only add non-empty texts
                entity_texts.append(text)
                entity_ids.append(entity_id)
                self.entity_texts[entity_id] = text
                
        if not entity_texts:
            raise VectorEmbeddingError("No valid text found in entities")
            
        # Fit vectorizer and generate embeddings
        self.logger.info(f"Fitting embeddings for {len(entity_texts)} entities using {self.embedding_method}")
        
        if self.embedding_method == "tfidf":
            vectors = self.vectorizer.fit_transform(entity_texts)
            
            # Store embeddings
            for i, entity_id in enumerate(entity_ids):
                self.embeddings[entity_id] = vectors[i].toarray().flatten()
                
        self.logger.info(f"Generated embeddings for {len(self.embeddings)} entities")
        
    def add_entity_embedding(self, entity: Dict[str, Any]) -> Optional[np.ndarray]:
        """Add embedding for a single entity"""
        entity_id = entity.get('id')
        if not entity_id:
            return None
            
        text = self.preprocessor.extract_text_from_entity(entity)
        if not text.strip():
            return None
            
        if self.vectorizer is None:
            # If vectorizer hasn't been fitted, we need to fit it first
            self.fit_embeddings([entity])
            return self.embeddings.get(entity_id)
            
        # Transform text using existing vectorizer
        try:
            vector = self.vectorizer.transform([text])
            embedding = vector.toarray().flatten()
            
            self.embeddings[entity_id] = embedding
            self.entity_texts[entity_id] = text
            
            self.logger.info(f"Added embedding for entity: {entity_id}")
            return embedding
            
        except Exception as e:
            self.logger.error(f"Error adding embedding for {entity_id}: {e}")
            return None
            
    def update_entity_embedding(self, entity: Dict[str, Any]) -> Optional[np.ndarray]:
        """Update embedding for an existing entity"""
        return self.add_entity_embedding(entity)
        
    def remove_entity_embedding(self, entity_id: str):
        """Remove embedding for an entity"""
        if entity_id in self.embeddings:
            del self.embeddings[entity_id]
        if entity_id in self.entity_texts:
            del self.entity_texts[entity_id]
        self.logger.info(f"Removed embedding for entity: {entity_id}")
        
    def semantic_search(self, query: str, top_k: int = 10, threshold: float = 0.1) -> List[Tuple[str, float]]:
        """Perform semantic search using vector similarity"""
        if not self.embeddings:
            return []
            
        # Preprocess query
        processed_query = self.preprocessor.preprocess_text(query)
        if not processed_query.strip():
            return []
            
        try:
            # Transform query using vectorizer
            query_vector = self.vectorizer.transform([processed_query]).toarray().flatten()
            
            # Calculate similarities
            similarities = []
            for entity_id, embedding in self.embeddings.items():
                similarity = cosine_similarity([query_vector], [embedding])[0][0]
                if similarity >= threshold:
                    similarities.append((entity_id, float(similarity)))
                    
            # Sort by similarity and return top_k
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:top_k]
            
        except Exception as e:
            self.logger.error(f"Error in semantic search: {e}")
            return []
            
    def find_similar_entities(self, entity_id: str, top_k: int = 5, threshold: float = 0.3) -> List[Tuple[str, float]]:
        """Find entities similar to the given entity"""
        if entity_id not in self.embeddings:
            return []
            
        target_embedding = self.embeddings[entity_id]
        similarities = []
        
        for other_id, other_embedding in self.embeddings.items():
            if other_id != entity_id:
                similarity = cosine_similarity([target_embedding], [other_embedding])[0][0]
                if similarity >= threshold:
                    similarities.append((other_id, float(similarity)))
                    
        # Sort by similarity and return top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
        
    def cluster_entities(self, n_clusters: int = 5, method: str = "kmeans") -> Dict[int, List[str]]:
        """Cluster entities based on their embeddings"""
        if not self.embeddings:
            return {}
            
        entity_ids = list(self.embeddings.keys())
        embeddings_matrix = np.array([self.embeddings[eid] for eid in entity_ids])
        
        if method == "kmeans":
            from sklearn.cluster import KMeans
            kmeans = KMeans(n_clusters=min(n_clusters, len(entity_ids)), random_state=42)
            cluster_labels = kmeans.fit_predict(embeddings_matrix)
        else:
            raise VectorEmbeddingError(f"Unsupported clustering method: {method}")
            
        # Group entities by cluster
        clusters = {}
        for i, cluster_id in enumerate(cluster_labels):
            if cluster_id not in clusters:
                clusters[cluster_id] = []
            clusters[cluster_id].append(entity_ids[i])
            
        self.logger.info(f"Clustered {len(entity_ids)} entities into {len(clusters)} clusters")
        return clusters
        
    def reduce_dimensions(self, n_components: int = 2) -> Dict[str, np.ndarray]:
        """Reduce embedding dimensions for visualization"""
        if not self.embeddings or n_components <= 0:
            return {}
            
        entity_ids = list(self.embeddings.keys())
        embeddings_matrix = np.array([self.embeddings[eid] for eid in entity_ids])
        
        # Use PCA for dimensionality reduction
        pca = PCA(n_components=min(n_components, embeddings_matrix.shape[1]))
        reduced_embeddings = pca.fit_transform(embeddings_matrix)
        
        # Return reduced embeddings
        reduced_dict = {}
        for i, entity_id in enumerate(entity_ids):
            reduced_dict[entity_id] = reduced_embeddings[i]
            
        self.logger.info(f"Reduced embeddings to {n_components} dimensions for {len(entity_ids)} entities")
        return reduced_dict
        
    def get_embedding_stats(self) -> Dict[str, Any]:
        """Get statistics about embeddings"""
        if not self.embeddings:
            return {}
            
        embeddings_array = np.array(list(self.embeddings.values()))
        
        stats = {
            'total_entities': len(self.embeddings),
            'embedding_dimension': embeddings_array.shape[1],
            'mean_norm': float(np.mean(np.linalg.norm(embeddings_array, axis=1))),
            'std_norm': float(np.std(np.linalg.norm(embeddings_array, axis=1))),
            'sparsity': float(np.mean(embeddings_array == 0)),
            'embedding_method': self.embedding_method
        }
        
        return stats
        
    def save_embeddings(self, file_path: Path):
        """Save embeddings to file"""
        data = {
            'embeddings': {eid: emb.tolist() for eid, emb in self.embeddings.items()},
            'entity_texts': self.entity_texts,
            'embedding_method': self.embedding_method,
            'max_features': self.max_features,
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'stats': self.get_embedding_stats()
            }
        }
        
        if file_path.suffix.lower() == '.json':
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        elif file_path.suffix.lower() == '.pkl':
            # For pickle format, include the vectorizer
            data['vectorizer'] = self.vectorizer
            with open(file_path, 'wb') as f:
                pickle.dump(data, f)
        else:
            raise VectorEmbeddingError(f"Unsupported file format: {file_path.suffix}")
            
        self.logger.info(f"Saved embeddings to {file_path}")
        
    def load_embeddings(self, file_path: Path):
        """Load embeddings from file"""
        if not file_path.exists():
            raise VectorEmbeddingError(f"File not found: {file_path}")
            
        if file_path.suffix.lower() == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        elif file_path.suffix.lower() == '.pkl':
            with open(file_path, 'rb') as f:
                data = pickle.load(f)
        else:
            raise VectorEmbeddingError(f"Unsupported file format: {file_path.suffix}")
            
        # Load embeddings
        self.embeddings = {eid: np.array(emb) for eid, emb in data['embeddings'].items()}
        self.entity_texts = data['entity_texts']
        self.embedding_method = data['embedding_method']
        self.max_features = data['max_features']
        
        # Load vectorizer
        if 'vectorizer' in data and data['vectorizer'] is not None:
            if file_path.suffix.lower() == '.pkl':
                self.vectorizer = data['vectorizer']
            else:
                # For JSON files, recreate the vectorizer
                self._initialize_vectorizer()
        else:
            self._initialize_vectorizer()
            
        self.logger.info(f"Loaded embeddings from {file_path}")


class SemanticSearchEngine:
    """High-level semantic search interface"""
    
    def __init__(self, embedder: VectorEmbedder):
        self.embedder = embedder
        self.logger = logging.getLogger(__name__)
        
    def search(self, query: str, entity_type: Optional[str] = None, 
               top_k: int = 10, threshold: float = 0.1) -> List[Dict[str, Any]]:
        """Search entities with optional type filtering"""
        # Get semantic search results
        results = self.embedder.semantic_search(query, top_k=top_k * 2, threshold=threshold)  # Get more results for filtering
        
        # Filter by entity type if specified
        if entity_type:
            filtered_results = []
            for entity_id, score in results:
                # Check if entity type matches (assuming entity_id format includes type)
                if entity_type in entity_id.lower():
                    filtered_results.append((entity_id, score))
            results = filtered_results[:top_k]
        else:
            results = results[:top_k]
            
        # Convert to detailed format
        detailed_results = []
        for entity_id, score in results:
            result = {
                'entity_id': entity_id,
                'similarity_score': score,
                'query': query,
                'entity_text': self.embedder.entity_texts.get(entity_id, '')
            }
            detailed_results.append(result)
            
        self.logger.info(f"Found {len(detailed_results)} results for query: '{query}'")
        return detailed_results
        
    def find_related_entities(self, entity_id: str, relation_strength: float = 0.3, 
                            max_results: int = 10) -> List[Dict[str, Any]]:
        """Find entities related to the given entity"""
        similar_entities = self.embedder.find_similar_entities(
            entity_id, 
            top_k=max_results, 
            threshold=relation_strength
        )
        
        detailed_results = []
        for related_id, score in similar_entities:
            result = {
                'source_entity': entity_id,
                'related_entity': related_id,
                'similarity_score': score,
                'relation_type': 'semantic_similarity'
            }
            detailed_results.append(result)
            
        return detailed_results


if __name__ == "__main__":
    # Example usage
    embedder = VectorEmbedder()
    
    # Example entities
    entities = [
        {
            'id': 'person_john_doe',
            'type': 'person',
            'attributes': {
                'name': 'John Doe',
                'email': 'john.doe@example.com',
                'department': 'Engineering',
                'title': 'Software Engineer'
            }
        },
        {
            'id': 'project_website',
            'type': 'project',
            'attributes': {
                'name': 'Company Website',
                'description': 'Build new company website using modern technologies',
                'status': 'active'
            }
        }
    ]
    
    # Fit embeddings
    embedder.fit_embeddings(entities)
    
    # Search example
    search_engine = SemanticSearchEngine(embedder)
    results = search_engine.search("software development")
    
    print(f"Found {len(results)} results")
    for result in results:
        print(f"- {result['entity_id']}: {result['similarity_score']:.3f}")