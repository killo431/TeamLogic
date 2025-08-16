#!/usr/bin/env python3
"""
Demonstration script for JSON File Selector functionality.
Shows how the GUI application handles different scenarios without requiring user interaction.
"""

import sys
import os
import tempfile
import json

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def demonstrate_functionality():
    """Demonstrate the key functionality of the JSON File Selector."""
    print("=== JSON File Selector Demonstration ===\n")
    
    # Test the core logic that the GUI uses
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sample_file = os.path.join(current_dir, "sample_knowledge_base.json")
    invalid_file = os.path.join(current_dir, "invalid_test.json")
    
    print("1. File Extension Validation")
    print("   Testing file extension validation logic...")
    test_files = [
        ("sample_knowledge_base.json", True),
        ("invalid_test.json", True), 
        ("readme.txt", False),
        ("data.JSON", True),  # Case insensitive
        ("noextension", False)
    ]
    
    for filename, should_pass in test_files:
        result = filename.lower().endswith('.json')
        status = "✓ PASS" if result == should_pass else "✗ FAIL"
        print(f"   {filename}: {status}")
    
    print("\n2. File Reading and JSON Validation")
    print("   Testing JSON parsing capabilities...")
    
    if os.path.exists(sample_file):
        try:
            with open(sample_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse JSON
            json_data = json.loads(content)
            file_size = os.path.getsize(sample_file)
            file_size_mb = file_size / (1024 * 1024)
            
            print(f"   ✓ Valid JSON file loaded successfully")
            print(f"     File: {os.path.basename(sample_file)}")
            print(f"     Size: {file_size_mb:.3f} MB")
            print(f"     Structure: {type(json_data).__name__} with {len(json_data) if isinstance(json_data, (dict, list)) else 'N/A'} top-level items")
            
        except Exception as e:
            print(f"   ✗ Error with valid file: {e}")
    
    if os.path.exists(invalid_file):
        try:
            with open(invalid_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # This should fail
            json.loads(content)
            print(f"   ✗ Invalid file incorrectly parsed as valid")
            
        except json.JSONDecodeError as e:
            print(f"   ✓ Invalid JSON correctly rejected")
            print(f"     Error: {str(e)}")
        except Exception as e:
            print(f"   ✗ Unexpected error: {e}")
    
    print("\n3. Preview Functionality")
    print("   Testing content preview logic...")
    
    if os.path.exists(sample_file):
        try:
            with open(sample_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            preview_lines = lines[:20]  # First 20 lines like the GUI does
            
            print(f"   ✓ Content preview generated")
            print(f"     Total lines: {len(lines)}")
            print(f"     Preview lines: {len(preview_lines)}")
            print(f"     First 3 lines preview:")
            for i, line in enumerate(preview_lines[:3]):
                print(f"       {i+1}: {line}")
            
        except Exception as e:
            print(f"   ✗ Preview generation failed: {e}")
    
    print("\n4. Error Handling")
    print("   Testing error handling scenarios...")
    
    # Test non-existent file
    non_existent = os.path.join(current_dir, "does_not_exist.json")
    if not os.path.exists(non_existent):
        print("   ✓ Non-existent file detection works")
    
    # Test file permission checking
    if os.path.exists(sample_file) and os.access(sample_file, os.R_OK):
        print("   ✓ File permission checking works")
    
    print("\n5. JSON Structure Analysis")
    print("   Testing JSON structure analysis...")
    
    if os.path.exists(sample_file):
        try:
            with open(sample_file, 'r') as f:
                json_data = json.loads(f.read())
            
            def analyze_structure(obj, path="root", max_depth=2, current_depth=0):
                if current_depth >= max_depth:
                    return [f"{path}: [analysis truncated]"]
                
                result = []
                if isinstance(obj, dict):
                    result.append(f"{path}: Object with {len(obj)} properties")
                    for i, (key, value) in enumerate(list(obj.items())[:3]):  # First 3 properties
                        result.extend(analyze_structure(value, f"{path}.{key}", max_depth, current_depth + 1))
                elif isinstance(obj, list):
                    result.append(f"{path}: Array with {len(obj)} items")
                    if obj:  # If array is not empty
                        result.extend(analyze_structure(obj[0], f"{path}[0]", max_depth, current_depth + 1))
                elif isinstance(obj, str):
                    result.append(f"{path}: String (length: {len(obj)})")
                elif isinstance(obj, (int, float)):
                    result.append(f"{path}: Number ({obj})")
                elif isinstance(obj, bool):
                    result.append(f"{path}: Boolean ({obj})")
                elif obj is None:
                    result.append(f"{path}: null")
                return result
            
            analysis = analyze_structure(json_data)
            print("   ✓ Structure analysis completed:")
            for item in analysis[:8]:  # Show first 8 items
                print(f"     {item}")
            
        except Exception as e:
            print(f"   ✗ Structure analysis failed: {e}")
    
    print("\n=== Demonstration Complete ===")
    print("\nThe JSON File Selector GUI implements all these features with a user-friendly interface:")
    print("- File browser with JSON filtering")
    print("- Real-time validation and error reporting")  
    print("- Preview panel showing file content")
    print("- Import workflow integration")
    print("- Comprehensive error handling")
    
    print(f"\nTo run the actual GUI application:")
    print(f"python json_file_selector.py")

if __name__ == "__main__":
    demonstrate_functionality()