"""
Knowledge Graph Module for Knowledge Base Framework
Manages entities, relationships and graph structure
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime
import networkx as nx
import pickle
from pathlib import Path


class KnowledgeGraphError(Exception):
    """Custom exception for knowledge graph operations"""
    pass


class Entity:
    """Represents an entity in the knowledge graph"""
    
    def __init__(self, entity_id: str, entity_type: str, attributes: Dict[str, Any]):
        self.id = entity_id
        self.type = entity_type
        self.attributes = attributes
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        
    def update_attributes(self, new_attributes: Dict[str, Any]):
        """Update entity attributes"""
        self.attributes.update(new_attributes)
        self.updated_at = datetime.now()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary"""
        return {
            'id': self.id,
            'type': self.type,
            'attributes': self.attributes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Entity':
        """Create entity from dictionary"""
        entity = cls(data['id'], data['type'], data['attributes'])
        entity.created_at = datetime.fromisoformat(data['created_at'])
        entity.updated_at = datetime.fromisoformat(data['updated_at'])
        return entity


class Relationship:
    """Represents a relationship between entities"""
    
    def __init__(self, source_id: str, target_id: str, relation_type: str, 
                 attributes: Optional[Dict[str, Any]] = None, confidence: float = 1.0):
        self.source_id = source_id
        self.target_id = target_id
        self.type = relation_type
        self.attributes = attributes or {}
        self.confidence = confidence
        self.created_at = datetime.now()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert relationship to dictionary"""
        return {
            'source_id': self.source_id,
            'target_id': self.target_id,
            'type': self.type,
            'attributes': self.attributes,
            'confidence': self.confidence,
            'created_at': self.created_at.isoformat()
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Relationship':
        """Create relationship from dictionary"""
        rel = cls(
            data['source_id'], 
            data['target_id'], 
            data['type'], 
            data['attributes'], 
            data['confidence']
        )
        rel.created_at = datetime.fromisoformat(data['created_at'])
        return rel


class KnowledgeGraph:
    """Main knowledge graph class"""
    
    def __init__(self):
        self.graph = nx.MultiDiGraph()  # Directed multigraph for complex relationships
        self.entities: Dict[str, Entity] = {}
        self.relationships: List[Relationship] = []
        self.logger = logging.getLogger(__name__)
        
    def add_entity(self, entity_data: Dict[str, Any]) -> Entity:
        """Add entity to the knowledge graph"""
        entity_id = entity_data.get('id')
        if not entity_id:
            raise KnowledgeGraphError("Entity must have an 'id' field")
            
        entity = Entity(
            entity_id,
            entity_data.get('type', 'unknown'),
            entity_data.get('attributes', {})
        )
        
        # Add to entities dict
        self.entities[entity_id] = entity
        
        # Add to graph
        self.graph.add_node(entity_id, **entity.to_dict())
        
        self.logger.info(f"Added entity: {entity_id} (type: {entity.type})")
        return entity
        
    def update_entity(self, entity_id: str, new_attributes: Dict[str, Any]):
        """Update existing entity"""
        if entity_id not in self.entities:
            raise KnowledgeGraphError(f"Entity {entity_id} not found")
            
        self.entities[entity_id].update_attributes(new_attributes)
        
        # Update graph node
        self.graph.nodes[entity_id].update(self.entities[entity_id].to_dict())
        
        self.logger.info(f"Updated entity: {entity_id}")
        
    def remove_entity(self, entity_id: str):
        """Remove entity and all its relationships"""
        if entity_id not in self.entities:
            raise KnowledgeGraphError(f"Entity {entity_id} not found")
            
        # Remove from entities dict
        del self.entities[entity_id]
        
        # Remove from graph (this also removes all edges)
        self.graph.remove_node(entity_id)
        
        # Remove from relationships list
        self.relationships = [
            rel for rel in self.relationships 
            if rel.source_id != entity_id and rel.target_id != entity_id
        ]
        
        self.logger.info(f"Removed entity: {entity_id}")
        
    def add_relationship(self, source_id: str, target_id: str, relation_type: str,
                        attributes: Optional[Dict[str, Any]] = None, confidence: float = 1.0) -> Relationship:
        """Add relationship between entities"""
        if source_id not in self.entities:
            raise KnowledgeGraphError(f"Source entity {source_id} not found")
        if target_id not in self.entities:
            raise KnowledgeGraphError(f"Target entity {target_id} not found")
            
        relationship = Relationship(source_id, target_id, relation_type, attributes, confidence)
        self.relationships.append(relationship)
        
        # Add to graph
        self.graph.add_edge(
            source_id, 
            target_id, 
            **relationship.to_dict()
        )
        
        self.logger.info(f"Added relationship: {source_id} --{relation_type}--> {target_id}")
        return relationship
        
    def find_relationships(self, entity_id: str, relation_type: Optional[str] = None) -> List[Relationship]:
        """Find all relationships for an entity"""
        if entity_id not in self.entities:
            return []
            
        relationships = []
        
        # Outgoing relationships
        for target_id in self.graph.successors(entity_id):
            edges = self.graph[entity_id][target_id]
            for edge_data in edges.values():
                if not relation_type or edge_data.get('type') == relation_type:
                    relationships.append(Relationship.from_dict(edge_data))
                    
        # Incoming relationships
        for source_id in self.graph.predecessors(entity_id):
            edges = self.graph[source_id][entity_id]
            for edge_data in edges.values():
                if not relation_type or edge_data.get('type') == relation_type:
                    relationships.append(Relationship.from_dict(edge_data))
                    
        return relationships
        
    def auto_detect_relationships(self):
        """Automatically detect relationships based on entity attributes"""
        detected_count = 0
        
        entities_list = list(self.entities.values())
        
        for i, entity1 in enumerate(entities_list):
            for entity2 in entities_list[i+1:]:
                relationships = self._detect_relationship_between(entity1, entity2)
                for rel_type, confidence in relationships:
                    try:
                        self.add_relationship(entity1.id, entity2.id, rel_type, confidence=confidence)
                        detected_count += 1
                    except KnowledgeGraphError:
                        continue  # Relationship might already exist
                        
        self.logger.info(f"Auto-detected {detected_count} relationships")
        return detected_count
        
    def _detect_relationship_between(self, entity1: Entity, entity2: Entity) -> List[Tuple[str, float]]:
        """Detect relationships between two entities"""
        relationships = []
        
        # Same type entities might be related
        if entity1.type == entity2.type:
            relationships.append(("similar_to", 0.3))
            
        # Person to organization relationships
        if entity1.type == "person" and entity2.type == "organization":
            # Check if person works for organization
            if self._check_employment_relationship(entity1, entity2):
                relationships.append(("works_for", 0.8))
                
        # Person to person relationships
        if entity1.type == "person" and entity2.type == "person":
            if self._check_colleague_relationship(entity1, entity2):
                relationships.append(("colleague_of", 0.7))
                
        # Project relationships
        if "project" in [entity1.type, entity2.type]:
            if self._check_project_involvement(entity1, entity2):
                relationships.append(("involved_in", 0.6))
                
        # Email domain relationships
        emails1 = entity1.attributes.get('emails', [])
        emails2 = entity2.attributes.get('emails', [])
        if emails1 and emails2:
            domains1 = set(email.split('@')[1] for email in emails1 if '@' in email)
            domains2 = set(email.split('@')[1] for email in emails2 if '@' in email)
            if domains1.intersection(domains2):
                relationships.append(("same_domain", 0.5))
                
        return relationships
        
    def _check_employment_relationship(self, person: Entity, organization: Entity) -> bool:
        """Check if person works for organization"""
        person_attrs = person.attributes
        org_attrs = organization.attributes
        
        # Check if organization name appears in person's company/department
        org_name = org_attrs.get('name', '').lower()
        person_company = person_attrs.get('department', '').lower()
        
        return org_name in person_company if org_name and person_company else False
        
    def _check_colleague_relationship(self, person1: Entity, person2: Entity) -> bool:
        """Check if two people are colleagues"""
        dept1 = person1.attributes.get('department', '').lower()
        dept2 = person2.attributes.get('department', '').lower()
        
        return dept1 == dept2 and dept1 != ''
        
    def _check_project_involvement(self, entity1: Entity, entity2: Entity) -> bool:
        """Check if entities are involved in same project"""
        # Simple heuristic - can be improved
        if entity1.type == "person" and entity2.type == "project":
            assignee = entity2.attributes.get('assignee', '').lower()
            person_name = entity1.attributes.get('name', '').lower()
            return person_name in assignee
        return False
        
    def search_entities(self, query: str, entity_type: Optional[str] = None) -> List[Entity]:
        """Search entities by query string"""
        query_lower = query.lower()
        results = []
        
        for entity in self.entities.values():
            if entity_type and entity.type != entity_type:
                continue
                
            # Search in entity ID
            if query_lower in entity.id.lower():
                results.append(entity)
                continue
                
            # Search in attributes
            for key, value in entity.attributes.items():
                if isinstance(value, str) and query_lower in value.lower():
                    results.append(entity)
                    break
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, str) and query_lower in item.lower():
                            results.append(entity)
                            break
                            
        return results
        
    def get_connected_entities(self, entity_id: str, max_depth: int = 2) -> Set[str]:
        """Get all entities connected to the given entity within max_depth"""
        if entity_id not in self.entities:
            return set()
            
        connected = set()
        current_level = {entity_id}
        
        for depth in range(max_depth):
            next_level = set()
            for node in current_level:
                # Get neighbors (both successors and predecessors)
                neighbors = set(self.graph.successors(node)) | set(self.graph.predecessors(node))
                next_level.update(neighbors)
                
            connected.update(next_level)
            current_level = next_level - connected
            
            if not current_level:
                break
                
        return connected
        
    def get_graph_stats(self) -> Dict[str, Any]:
        """Get knowledge graph statistics"""
        stats = {
            'total_entities': len(self.entities),
            'total_relationships': len(self.relationships),
            'entity_types': {},
            'relationship_types': {},
            'graph_density': nx.density(self.graph),
            'connected_components': nx.number_weakly_connected_components(self.graph)
        }
        
        # Count entities by type
        for entity in self.entities.values():
            stats['entity_types'][entity.type] = stats['entity_types'].get(entity.type, 0) + 1
            
        # Count relationships by type
        for rel in self.relationships:
            stats['relationship_types'][rel.type] = stats['relationship_types'].get(rel.type, 0) + 1
            
        return stats
        
    def export_to_dict(self) -> Dict[str, Any]:
        """Export knowledge graph to dictionary"""
        return {
            'entities': [entity.to_dict() for entity in self.entities.values()],
            'relationships': [rel.to_dict() for rel in self.relationships],
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'stats': self.get_graph_stats()
            }
        }
        
    def import_from_dict(self, data: Dict[str, Any]):
        """Import knowledge graph from dictionary"""
        # Clear existing data
        self.entities.clear()
        self.relationships.clear()
        self.graph.clear()
        
        # Import entities
        for entity_data in data.get('entities', []):
            entity = Entity.from_dict(entity_data)
            self.entities[entity.id] = entity
            self.graph.add_node(entity.id, **entity.to_dict())
            
        # Import relationships
        for rel_data in data.get('relationships', []):
            rel = Relationship.from_dict(rel_data)
            self.relationships.append(rel)
            if rel.source_id in self.entities and rel.target_id in self.entities:
                self.graph.add_edge(rel.source_id, rel.target_id, **rel.to_dict())
                
        self.logger.info(f"Imported {len(self.entities)} entities and {len(self.relationships)} relationships")
        
    def save_to_file(self, file_path: Path):
        """Save knowledge graph to file"""
        data = self.export_to_dict()
        
        if file_path.suffix.lower() == '.json':
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        elif file_path.suffix.lower() == '.pkl':
            with open(file_path, 'wb') as f:
                pickle.dump(data, f)
        else:
            raise KnowledgeGraphError(f"Unsupported file format: {file_path.suffix}")
            
        self.logger.info(f"Saved knowledge graph to {file_path}")
        
    def load_from_file(self, file_path: Path):
        """Load knowledge graph from file"""
        if not file_path.exists():
            raise KnowledgeGraphError(f"File not found: {file_path}")
            
        if file_path.suffix.lower() == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        elif file_path.suffix.lower() == '.pkl':
            with open(file_path, 'rb') as f:
                data = pickle.load(f)
        else:
            raise KnowledgeGraphError(f"Unsupported file format: {file_path.suffix}")
            
        self.import_from_dict(data)
        self.logger.info(f"Loaded knowledge graph from {file_path}")


if __name__ == "__main__":
    # Example usage
    kg = KnowledgeGraph()
    
    # Add some example entities
    person = {
        'id': 'person_john_doe',
        'type': 'person',
        'attributes': {
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'department': 'Engineering'
        }
    }
    
    project = {
        'id': 'project_website',
        'type': 'project',
        'attributes': {
            'name': 'Company Website',
            'assignee': 'John Doe',
            'status': 'active'
        }
    }
    
    kg.add_entity(person)
    kg.add_entity(project)
    kg.auto_detect_relationships()
    
    print("Graph stats:", kg.get_graph_stats())