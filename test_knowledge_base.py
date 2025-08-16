#!/usr/bin/env python3
"""
Command-line test script for Knowledge Base Framework
Tests the core functionality without the GUI
"""

import json
import logging
from pathlib import Path
from data_ingestion import JSONProcessor
from knowledge_graph import KnowledgeGraph
from vector_embedding import VectorEmbedder, SemanticSearchEngine

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_knowledge_base():
    """Test the complete knowledge base functionality"""
    
    print("=" * 60)
    print("KNOWLEDGE BASE FRAMEWORK TEST")
    print("=" * 60)
    
    # Test 1: JSON Processing
    print("\n1. Testing JSON Processing...")
    processor = JSONProcessor()
    entities = processor.process_file(Path('example_data.json'))
    print(f"   ✓ Extracted {len(entities)} entities")
    
    # Show some example entities
    print("   Sample entities:")
    for entity in entities[:3]:
        print(f"     - {entity['id']} ({entity['type']})")
    
    # Test 2: Knowledge Graph
    print("\n2. Testing Knowledge Graph...")
    kg = KnowledgeGraph()
    
    for entity in entities:
        kg.add_entity(entity)
    
    print(f"   ✓ Added {len(kg.entities)} entities to knowledge graph")
    
    # Auto-detect relationships
    relationships = kg.auto_detect_relationships()
    print(f"   ✓ Auto-detected {relationships} relationships")
    
    # Show graph statistics
    stats = kg.get_graph_stats()
    print("   Graph Statistics:")
    print(f"     - Total entities: {stats['total_entities']}")
    print(f"     - Total relationships: {stats['total_relationships']}")
    print(f"     - Graph density: {stats['graph_density']:.3f}")
    
    print("   Entity types:")
    for entity_type, count in stats['entity_types'].items():
        print(f"     - {entity_type}: {count}")
        
    # Test 3: Vector Embeddings
    print("\n3. Testing Vector Embeddings...")
    embedder = VectorEmbedder()
    entities_list = [entity.to_dict() for entity in kg.entities.values()]
    embedder.fit_embeddings(entities_list)
    
    print(f"   ✓ Generated embeddings for {len(embedder.embeddings)} entities")
    
    embedding_stats = embedder.get_embedding_stats()
    print(f"   ✓ Embedding dimension: {embedding_stats['embedding_dimension']}")
    print(f"   ✓ Mean norm: {embedding_stats['mean_norm']:.3f}")
    
    # Test 4: Semantic Search
    print("\n4. Testing Semantic Search...")
    search_engine = SemanticSearchEngine(embedder)
    
    # Test various queries
    test_queries = [
        "software engineer",
        "website project", 
        "high priority",
        "design system",
        "John Doe"
    ]
    
    for query in test_queries:
        results = search_engine.search(query, top_k=3)
        print(f"   Query: '{query}' -> {len(results)} results")
        for result in results[:2]:  # Show top 2 results
            print(f"     - {result['entity_id']}: {result['similarity_score']:.3f}")
    
    # Test 5: Entity Relationships
    print("\n5. Testing Relationship Detection...")
    
    # Find relationships for a specific entity
    sample_entity_id = list(kg.entities.keys())[0]
    relationships = kg.find_relationships(sample_entity_id)
    print(f"   Entity '{sample_entity_id}' has {len(relationships)} relationships:")
    
    for rel in relationships[:3]:  # Show first 3
        if rel.source_id == sample_entity_id:
            print(f"     - {rel.source_id} --{rel.type}--> {rel.target_id}")
        else:
            print(f"     - {rel.source_id} --{rel.type}--> {sample_entity_id}")
    
    # Test 6: Similar Entities
    print("\n6. Testing Similar Entity Detection...")
    similar_entities = embedder.find_similar_entities(sample_entity_id, top_k=3)
    print(f"   Entities similar to '{sample_entity_id}':")
    for entity_id, score in similar_entities:
        print(f"     - {entity_id}: {score:.3f}")
        
    # Test 7: Save and Load
    print("\n7. Testing Persistence...")
    
    # Save knowledge graph
    kg_file = Path("test_knowledge_graph.json")
    kg.save_to_file(kg_file)
    print(f"   ✓ Saved knowledge graph to {kg_file}")
    
    # Save embeddings
    emb_file = Path("test_embeddings.json")
    embedder.save_embeddings(emb_file)
    print(f"   ✓ Saved embeddings to {emb_file}")
    
    # Test loading
    new_kg = KnowledgeGraph()
    new_kg.load_from_file(kg_file)
    print(f"   ✓ Loaded knowledge graph: {len(new_kg.entities)} entities")
    
    new_embedder = VectorEmbedder()
    new_embedder.load_embeddings(emb_file)
    print(f"   ✓ Loaded embeddings: {len(new_embedder.embeddings)} vectors")
    
    # Cleanup
    kg_file.unlink()
    emb_file.unlink()
    print("   ✓ Cleaned up test files")
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED! ✓")
    print("Knowledge Base Framework is working correctly.")
    print("=" * 60)

def demonstrate_ai_features():
    """Demonstrate AI features if available"""
    print("\n8. Testing AI Integration...")
    
    try:
        from ai_agent import AIAgent, get_available_models
        
        models = get_available_models()
        print(f"   Available AI models: {len(models)}")
        for model_name, info in list(models.items())[:3]:
            print(f"     - {info['name']}: {info['description']}")
            
        print("   ✓ AI features available (requires transformers library)")
        print("   Note: AI model loading requires internet connection and may take time")
        
    except ImportError as e:
        print(f"   ⚠ AI features not available: {e}")
        print("   Install with: pip install transformers torch")

if __name__ == "__main__":
    try:
        test_knowledge_base()
        demonstrate_ai_features()
        
    except FileNotFoundError:
        print("Error: example_data.json not found!")
        print("Make sure you're running this script from the correct directory.")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        logging.error(f"Test failed: {e}")
        
    print("\nFor full GUI experience, run: python knowledge_base_gui.py")
    print("(Note: Requires tkinter support)")