#!/usr/bin/env python3
"""
Validate that the JSON File Selector GUI can be created and initialized properly.
This test doesn't require a display but verifies the GUI components can be instantiated.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_gui_creation():
    """Test that the GUI can be created without errors."""
    try:
        import tkinter as tk
        from json_file_selector import JSONFileSelector
        
        print("Testing GUI creation...")
        
        # Create root window (won't be displayed)
        root = tk.Tk()
        root.withdraw()  # Hide the window
        
        # Create the application instance
        app = JSONFileSelector(root)
        
        print("✓ GUI application created successfully")
        print("✓ All tkinter components initialized")
        
        # Test that key components exist
        assert hasattr(app, 'selected_file_path')
        assert hasattr(app, 'file_content') 
        assert hasattr(app, 'file_path_var')
        assert hasattr(app, 'file_info_var')
        assert hasattr(app, 'preview_text')
        assert hasattr(app, 'import_button')
        assert hasattr(app, 'validate_button')
        
        print("✓ All required attributes exist")
        
        # Test methods exist
        assert callable(app.browse_file)
        assert callable(app.load_file)
        assert callable(app.validate_json)
        assert callable(app.import_file)
        assert callable(app.clear_selection)
        
        print("✓ All required methods exist")
        
        # Cleanup
        root.destroy()
        
        print("✓ GUI validation complete - application is ready to run")
        return True
        
    except Exception as e:
        print(f"✗ GUI validation failed: {e}")
        return False

if __name__ == "__main__":
    success = test_gui_creation()
    if success:
        print("\n=== GUI Application Ready ===")
        print("The JSON File Selector GUI is properly configured and ready to use.")
        print("Run 'python json_file_selector.py' to start the application.")
        sys.exit(0)
    else:
        print("\n=== GUI Application Issues ===") 
        print("There are issues with the GUI configuration.")
        sys.exit(1)