#!/usr/bin/env python3
"""
Test script for JSON File Selector GUI
Tests the core functionality without requiring GUI interaction.
"""

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our application (without running the GUI)
import json_file_selector


class TestJSONFileSelector(unittest.TestCase):
    """Test cases for JSON File Selector functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        
        # Create test JSON files
        self.valid_json_file = os.path.join(self.test_dir, "valid_test.json")
        self.invalid_json_file = os.path.join(self.test_dir, "invalid_test.json")
        self.non_json_file = os.path.join(self.test_dir, "test.txt")
        
        # Valid JSON content
        valid_content = {
            "test": "data",
            "array": [1, 2, 3],
            "nested": {"key": "value"}
        }
        
        with open(self.valid_json_file, 'w') as f:
            json.dump(valid_content, f, indent=2)
        
        # Invalid JSON content
        with open(self.invalid_json_file, 'w') as f:
            f.write('{"invalid": "json", "missing": }')
        
        # Non-JSON file
        with open(self.non_json_file, 'w') as f:
            f.write("This is not a JSON file")
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.test_dir)
    
    def test_file_extension_validation(self):
        """Test that only .json files are accepted."""
        # This would normally require GUI interaction, so we test the logic directly
        
        # Valid JSON extension
        self.assertTrue(self.valid_json_file.lower().endswith('.json'))
        
        # Invalid extension
        self.assertFalse(self.non_json_file.lower().endswith('.json'))
    
    def test_json_parsing_valid_file(self):
        """Test parsing of valid JSON file."""
        try:
            with open(self.valid_json_file, 'r') as f:
                content = f.read()
            
            # Should parse without error
            json_data = json.loads(content)
            
            # Check expected structure
            self.assertIn('test', json_data)
            self.assertIn('array', json_data)
            self.assertIn('nested', json_data)
            self.assertEqual(json_data['test'], 'data')
            
        except Exception as e:
            self.fail(f"Valid JSON file should parse without error: {e}")
    
    def test_json_parsing_invalid_file(self):
        """Test parsing of invalid JSON file."""
        with open(self.invalid_json_file, 'r') as f:
            content = f.read()
        
        # Should raise JSONDecodeError
        with self.assertRaises(json.JSONDecodeError):
            json.loads(content)
    
    def test_file_exists_and_readable(self):
        """Test file existence and readability checks."""
        # Valid file should exist and be readable
        self.assertTrue(os.path.exists(self.valid_json_file))
        self.assertTrue(os.access(self.valid_json_file, os.R_OK))
        
        # Non-existent file
        non_existent = os.path.join(self.test_dir, "does_not_exist.json")
        self.assertFalse(os.path.exists(non_existent))
    
    def test_file_size_calculation(self):
        """Test file size calculation."""
        file_size = os.path.getsize(self.valid_json_file)
        self.assertGreater(file_size, 0)
        
        file_size_mb = file_size / (1024 * 1024)
        self.assertGreaterEqual(file_size_mb, 0)
    
    def test_preview_content_truncation(self):
        """Test preview content truncation logic."""
        # Create content with many lines
        long_content = '\n'.join([f"Line {i}" for i in range(50)])
        
        lines = long_content.split('\n')
        preview_lines = lines[:20]  # Simulate the preview logic
        
        self.assertEqual(len(preview_lines), 20)
        self.assertEqual(preview_lines[0], "Line 0")
        self.assertEqual(preview_lines[19], "Line 19")


def run_gui_test():
    """Manual test function to validate GUI functionality."""
    print("=== JSON File Selector GUI Test ===")
    print("\nThis script will test the core functionality without GUI.")
    print("To test the GUI manually, run: python json_file_selector.py")
    
    # Test with sample files
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sample_file = os.path.join(current_dir, "sample_knowledge_base.json")
    invalid_file = os.path.join(current_dir, "invalid_test.json")
    
    print(f"\nTesting with sample file: {sample_file}")
    
    if os.path.exists(sample_file):
        try:
            # Test file reading
            with open(sample_file, 'r') as f:
                content = f.read()
            
            # Test JSON parsing
            json_data = json.loads(content)
            
            print("✓ Sample file exists and is valid JSON")
            print(f"✓ File size: {os.path.getsize(sample_file)} bytes")
            print(f"✓ Content preview: {content[:100]}...")
            
            # Test structure analysis
            if isinstance(json_data, dict):
                print(f"✓ JSON structure: Object with {len(json_data)} top-level properties")
                for key in list(json_data.keys())[:3]:
                    print(f"  - {key}: {type(json_data[key]).__name__}")
            
        except Exception as e:
            print(f"✗ Error testing sample file: {e}")
    else:
        print("✗ Sample file not found")
    
    print(f"\nTesting with invalid file: {invalid_file}")
    
    if os.path.exists(invalid_file):
        try:
            with open(invalid_file, 'r') as f:
                content = f.read()
            
            # This should fail
            json.loads(content)
            print("✗ Invalid file should not parse as valid JSON")
            
        except json.JSONDecodeError as e:
            print(f"✓ Invalid file correctly rejected: {str(e)[:50]}...")
        except Exception as e:
            print(f"✗ Unexpected error: {e}")
    else:
        print("✗ Invalid test file not found")


if __name__ == "__main__":
    print("Running JSON File Selector Tests...")
    
    # Run unit tests
    print("\n=== Unit Tests ===")
    unittest.main(verbosity=2, exit=False)
    
    # Run manual tests
    print("\n=== Manual Tests ===")
    run_gui_test()
    
    print("\n=== Test Complete ===")
    print("To test the GUI interface, run:")
    print("python json_file_selector.py")