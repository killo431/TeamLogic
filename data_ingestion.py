"""
Data Ingestion Module for Knowledge Base Framework
Handles importing and processing JSON files for entity extraction
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
import re
from datetime import datetime


class DataIngestionError(Exception):
    """Custom exception for data ingestion errors"""
    pass


class JSONProcessor:
    """Processes JSON files and extracts entities based on configuration"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._default_config()
        self.logger = logging.getLogger(__name__)
        self.progress_callback: Optional[Callable[[int, int], None]] = None
        
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration for entity extraction"""
        return {
            'entity_types': {
                'person': ['name', 'email', 'phone', 'title', 'department'],
                'organization': ['name', 'address', 'website', 'industry'],
                'project': ['name', 'description', 'status', 'deadline'],
                'task': ['title', 'description', 'assignee', 'priority', 'due_date'],
                'document': ['title', 'content', 'author', 'created_date']
            },
            'extraction_rules': {
                'email_pattern': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                'phone_pattern': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
                'date_patterns': [
                    r'\d{4}-\d{2}-\d{2}',
                    r'\d{2}/\d{2}/\d{4}',
                    r'\d{2}-\d{2}-\d{4}'
                ]
            }
        }
    
    def set_progress_callback(self, callback: Callable[[int, int], None]):
        """Set callback function for progress updates"""
        self.progress_callback = callback
    
    def load_json_file(self, file_path: Path) -> Dict[str, Any]:
        """Load and validate JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                self.logger.info(f"Successfully loaded JSON file: {file_path}")
                return data
        except json.JSONDecodeError as e:
            raise DataIngestionError(f"Invalid JSON format in {file_path}: {e}")
        except FileNotFoundError:
            raise DataIngestionError(f"File not found: {file_path}")
        except Exception as e:
            raise DataIngestionError(f"Error loading file {file_path}: {e}")
    
    def extract_entities(self, data: Any, parent_path: str = "") -> List[Dict[str, Any]]:
        """Extract entities from JSON data based on configuration"""
        entities = []
        
        if isinstance(data, dict):
            entities.extend(self._extract_from_dict(data, parent_path))
        elif isinstance(data, list):
            entities.extend(self._extract_from_list(data, parent_path))
            
        return entities
    
    def _extract_from_dict(self, data: Dict[str, Any], parent_path: str) -> List[Dict[str, Any]]:
        """Extract entities from dictionary data"""
        entities = []
        
        # Try to identify entity type based on keys
        entity_type = self._identify_entity_type(data)
        
        if entity_type:
            entity = {
                'type': entity_type,
                'id': self._generate_entity_id(data, entity_type),
                'path': parent_path,
                'attributes': {},
                'extracted_at': datetime.now().isoformat()
            }
            
            # Extract relevant fields based on entity type
            for field in self.config['entity_types'][entity_type]:
                if field in data:
                    entity['attributes'][field] = data[field]
            
            # Extract additional patterns (emails, phones, dates)
            entity['attributes'].update(self._extract_patterns(data))
            
            entities.append(entity)
        
        # Recursively process nested objects
        for key, value in data.items():
            new_path = f"{parent_path}.{key}" if parent_path else key
            entities.extend(self.extract_entities(value, new_path))
            
        return entities
    
    def _extract_from_list(self, data: List[Any], parent_path: str) -> List[Dict[str, Any]]:
        """Extract entities from list data"""
        entities = []
        
        for i, item in enumerate(data):
            new_path = f"{parent_path}[{i}]"
            entities.extend(self.extract_entities(item, new_path))
            
            # Update progress if callback is set
            if self.progress_callback and len(data) > 10:
                self.progress_callback(i + 1, len(data))
                
        return entities
    
    def _identify_entity_type(self, data: Dict[str, Any]) -> Optional[str]:
        """Identify entity type based on available keys"""
        data_keys = set(data.keys())
        
        best_match = None
        best_score = 0
        
        for entity_type, required_fields in self.config['entity_types'].items():
            # Calculate match score based on how many required fields are present
            matching_fields = len(data_keys.intersection(set(required_fields)))
            score = matching_fields / len(required_fields)
            
            if score > 0.5 and score > best_score:  # At least 50% match required
                best_match = entity_type
                best_score = score
                
        return best_match
    
    def _generate_entity_id(self, data: Dict[str, Any], entity_type: str) -> str:
        """Generate unique ID for entity"""
        # Use primary identifier if available
        primary_fields = {
            'person': ['email', 'name'],
            'organization': ['name'],
            'project': ['name'],
            'task': ['title'],
            'document': ['title']
        }
        
        for field in primary_fields.get(entity_type, ['name']):
            if field in data:
                # Create ID from field value
                id_base = str(data[field]).lower().replace(' ', '_')
                id_base = re.sub(r'[^\w\-_]', '', id_base)
                return f"{entity_type}_{id_base}"
        
        # Fallback to hash-based ID
        import hashlib
        data_str = json.dumps(data, sort_keys=True)
        hash_id = hashlib.md5(data_str.encode()).hexdigest()[:8]
        return f"{entity_type}_{hash_id}"
    
    def _extract_patterns(self, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Extract patterns like emails, phones, dates from text fields"""
        patterns = {}
        
        # Convert data to searchable text
        text_content = json.dumps(data, ensure_ascii=False)
        
        # Extract emails
        email_pattern = self.config['extraction_rules']['email_pattern']
        emails = re.findall(email_pattern, text_content, re.IGNORECASE)
        if emails:
            patterns['emails'] = list(set(emails))
        
        # Extract phone numbers
        phone_pattern = self.config['extraction_rules']['phone_pattern']
        phones = re.findall(phone_pattern, text_content)
        if phones:
            patterns['phones'] = list(set(phones))
        
        # Extract dates
        dates = []
        for date_pattern in self.config['extraction_rules']['date_patterns']:
            found_dates = re.findall(date_pattern, text_content)
            dates.extend(found_dates)
        if dates:
            patterns['dates'] = list(set(dates))
            
        return patterns
    
    def process_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Main method to process a JSON file and extract entities"""
        self.logger.info(f"Starting processing of file: {file_path}")
        
        # Load JSON data
        data = self.load_json_file(file_path)
        
        # Extract entities
        entities = self.extract_entities(data)
        
        self.logger.info(f"Extracted {len(entities)} entities from {file_path}")
        return entities
    
    def process_directory(self, directory_path: Path) -> List[Dict[str, Any]]:
        """Process all JSON files in a directory"""
        all_entities = []
        json_files = list(directory_path.glob("*.json"))
        
        for i, file_path in enumerate(json_files):
            try:
                entities = self.process_file(file_path)
                all_entities.extend(entities)
                
                # Update progress
                if self.progress_callback:
                    self.progress_callback(i + 1, len(json_files))
                    
            except DataIngestionError as e:
                self.logger.error(f"Error processing {file_path}: {e}")
                continue
        
        return all_entities
    
    def update_config(self, new_config: Dict[str, Any]):
        """Update processing configuration"""
        self.config.update(new_config)
        self.logger.info("Configuration updated")
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        return self.config.copy()


# Utility functions
def validate_json_structure(data: Any, schema: Optional[Dict[str, Any]] = None) -> bool:
    """Validate JSON data structure against optional schema"""
    if schema is None:
        return True
    
    # Basic schema validation (can be extended)
    try:
        if 'type' in schema:
            expected_type = schema['type']
            if expected_type == 'object' and not isinstance(data, dict):
                return False
            elif expected_type == 'array' and not isinstance(data, list):
                return False
                
        if 'required' in schema and isinstance(data, dict):
            for required_field in schema['required']:
                if required_field not in data:
                    return False
                    
        return True
    except Exception:
        return False


if __name__ == "__main__":
    # Example usage
    processor = JSONProcessor()
    
    # Example: process a single file
    # entities = processor.process_file(Path("example.json"))
    # print(f"Found {len(entities)} entities")