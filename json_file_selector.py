#!/usr/bin/env python3
"""
JSON File Selector GUI
A user-friendly file selection interface for importing JSON files into the knowledge base application.

Features:
- File browser with JSON file filtering
- JSON file validation 
- Preview panel showing file content
- Comprehensive error handling
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
import os
import sys
from typing import Optional, Dict, Any


class JSONFileSelector:
    """GUI application for selecting and previewing JSON files."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("JSON File Selector - TeamLogic Knowledge Base")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Selected file path
        self.selected_file_path: Optional[str] = None
        self.file_content: Optional[Dict[Any, Any]] = None
        
        self.setup_gui()
        self.center_window()
    
    def setup_gui(self):
        """Set up the GUI components."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="JSON File Import Tool", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # File selection section
        file_frame = ttk.LabelFrame(main_frame, text="File Selection", padding="10")
        file_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        # Browse button
        browse_button = ttk.Button(file_frame, text="Browse JSON Files", 
                                 command=self.browse_file, width=20)
        browse_button.grid(row=0, column=0, padx=(0, 10))
        
        # File path display
        self.file_path_var = tk.StringVar()
        file_path_entry = ttk.Entry(file_frame, textvariable=self.file_path_var, 
                                   state='readonly', width=50)
        file_path_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # Clear button
        clear_button = ttk.Button(file_frame, text="Clear", 
                                command=self.clear_selection, width=10)
        clear_button.grid(row=0, column=2)
        
        # File info section
        info_frame = ttk.Frame(file_frame)
        info_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        info_frame.columnconfigure(1, weight=1)
        
        # File size and validation status
        self.file_info_var = tk.StringVar()
        info_label = ttk.Label(info_frame, textvariable=self.file_info_var, 
                             foreground="blue")
        info_label.grid(row=0, column=0, sticky=tk.W)
        
        # Preview section
        preview_frame = ttk.LabelFrame(main_frame, text="JSON Preview", padding="10")
        preview_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        
        # Preview text widget with scrollbars
        self.preview_text = scrolledtext.ScrolledText(preview_frame, height=15, width=70, 
                                                     wrap=tk.WORD, state=tk.DISABLED,
                                                     font=('Consolas', 10))
        self.preview_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=(0, 10))
        
        # Import button
        self.import_button = ttk.Button(button_frame, text="Import JSON File", 
                                       command=self.import_file, state=tk.DISABLED,
                                       width=20)
        self.import_button.grid(row=0, column=0, padx=(0, 10))
        
        # Validate button
        self.validate_button = ttk.Button(button_frame, text="Validate JSON", 
                                         command=self.validate_json, state=tk.DISABLED,
                                         width=15)
        self.validate_button.grid(row=0, column=1, padx=(0, 10))
        
        # Exit button
        exit_button = ttk.Button(button_frame, text="Exit", command=self.root.quit, width=10)
        exit_button.grid(row=0, column=2)
        
    def center_window(self):
        """Center the window on the screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def browse_file(self):
        """Open file dialog to select a JSON file."""
        try:
            file_path = filedialog.askopenfilename(
                title="Select JSON File",
                filetypes=[
                    ("JSON files", "*.json"),
                    ("All files", "*.*")
                ],
                initialdir=os.getcwd()
            )
            
            if file_path:
                self.load_file(file_path)
                
        except Exception as e:
            self.show_error(f"Error opening file dialog: {str(e)}")
    
    def load_file(self, file_path: str):
        """Load and validate the selected JSON file."""
        try:
            # Validate file extension
            if not file_path.lower().endswith('.json'):
                self.show_error("Invalid file type. Please select a JSON file (.json extension required).")
                return
            
            # Check if file exists and is readable
            if not os.path.exists(file_path):
                self.show_error(f"File not found: {file_path}")
                return
                
            if not os.access(file_path, os.R_OK):
                self.show_error(f"Cannot read file: {file_path}\nCheck file permissions.")
                return
            
            # Get file info
            file_size = os.path.getsize(file_path)
            file_size_mb = file_size / (1024 * 1024)
            
            # Read and validate JSON content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Try to parse JSON
            try:
                json_data = json.loads(content)
                self.file_content = json_data
                
                # Update GUI
                self.selected_file_path = file_path
                self.file_path_var.set(file_path)
                
                # Show file info
                info_text = f"File size: {file_size_mb:.2f} MB | Valid JSON ✓"
                self.file_info_var.set(info_text)
                
                # Show preview (first 20 lines)
                self.show_preview(content)
                
                # Enable buttons
                self.import_button.config(state=tk.NORMAL)
                self.validate_button.config(state=tk.NORMAL)
                
                # Show success message
                messagebox.showinfo("File Loaded", f"JSON file loaded successfully!\n\nFile: {os.path.basename(file_path)}\nSize: {file_size_mb:.2f} MB")
                
            except json.JSONDecodeError as e:
                self.show_error(f"Invalid JSON format in file: {file_path}\n\nError: {str(e)}\n\nPlease check the file content and ensure it contains valid JSON.")
                self.show_preview(content, is_valid=False)
                
        except Exception as e:
            self.show_error(f"Error loading file: {str(e)}")
    
    def show_preview(self, content: str, is_valid: bool = True):
        """Display preview of the file content."""
        try:
            lines = content.split('\n')
            preview_lines = lines[:20]  # Show first 20 lines
            
            # Add indicator if file is truncated
            if len(lines) > 20:
                preview_lines.append(f"\n... (showing first 20 lines of {len(lines)} total lines)")
            
            preview_content = '\n'.join(preview_lines)
            
            # Update preview text
            self.preview_text.config(state=tk.NORMAL)
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(1.0, preview_content)
            
            # Color code based on validity
            if is_valid:
                self.preview_text.config(bg='white', fg='black')
            else:
                self.preview_text.config(bg='#ffe6e6', fg='darkred')
                
            self.preview_text.config(state=tk.DISABLED)
            
        except Exception as e:
            self.show_error(f"Error displaying preview: {str(e)}")
    
    def validate_json(self):
        """Validate the JSON structure and show detailed information."""
        if not self.file_content:
            messagebox.showwarning("No File", "Please select a JSON file first.")
            return
            
        try:
            # Analyze JSON structure
            def analyze_json(obj, path="root"):
                info = []
                if isinstance(obj, dict):
                    info.append(f"{path}: Object with {len(obj)} properties")
                    for key, value in list(obj.items())[:5]:  # Show first 5 properties
                        info.extend(analyze_json(value, f"{path}.{key}"))
                elif isinstance(obj, list):
                    info.append(f"{path}: Array with {len(obj)} items")
                    if obj:  # If array is not empty
                        info.extend(analyze_json(obj[0], f"{path}[0]"))
                elif isinstance(obj, str):
                    info.append(f"{path}: String (length: {len(obj)})")
                elif isinstance(obj, (int, float)):
                    info.append(f"{path}: Number ({obj})")
                elif isinstance(obj, bool):
                    info.append(f"{path}: Boolean ({obj})")
                elif obj is None:
                    info.append(f"{path}: null")
                    
                return info[:10]  # Limit to 10 items to avoid overwhelming display
            
            analysis = analyze_json(self.file_content)
            analysis_text = "\n".join(analysis)
            
            messagebox.showinfo("JSON Validation", 
                              f"JSON file is valid! ✓\n\nStructure Analysis:\n{analysis_text}")
                              
        except Exception as e:
            self.show_error(f"Error validating JSON: {str(e)}")
    
    def import_file(self):
        """Import the selected JSON file (placeholder for actual import logic)."""
        if not self.selected_file_path:
            messagebox.showwarning("No File", "Please select a JSON file first.")
            return
            
        try:
            # This is a placeholder for the actual import logic
            # In a real application, this would integrate with the knowledge base system
            
            result = messagebox.askyesno("Import JSON", 
                                       f"Import this JSON file to the knowledge base?\n\n"
                                       f"File: {os.path.basename(self.selected_file_path)}\n"
                                       f"Size: {os.path.getsize(self.selected_file_path) / 1024:.1f} KB\n\n"
                                       f"This will add the JSON data to your knowledge base.")
            
            if result:
                # Simulate import process
                messagebox.showinfo("Import Complete", 
                                  f"JSON file imported successfully!\n\n"
                                  f"File: {os.path.basename(self.selected_file_path)}\n"
                                  f"Status: Ready for processing")
                                  
                # Clear selection after successful import
                self.clear_selection()
                
        except Exception as e:
            self.show_error(f"Error importing file: {str(e)}")
    
    def clear_selection(self):
        """Clear the current file selection."""
        self.selected_file_path = None
        self.file_content = None
        self.file_path_var.set("")
        self.file_info_var.set("")
        
        # Clear preview
        self.preview_text.config(state=tk.NORMAL)
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.config(state=tk.DISABLED, bg='white', fg='black')
        
        # Disable buttons
        self.import_button.config(state=tk.DISABLED)
        self.validate_button.config(state=tk.DISABLED)
    
    def show_error(self, message: str):
        """Display error message to user."""
        messagebox.showerror("Error", message)


def main():
    """Main entry point for the application."""
    try:
        # Create main window
        root = tk.Tk()
        
        # Create and run the application
        app = JSONFileSelector(root)
        
        # Start the GUI event loop
        root.mainloop()
        
    except Exception as e:
        # Handle any unexpected errors
        error_msg = f"An unexpected error occurred: {str(e)}"
        if tk._default_root:
            messagebox.showerror("Fatal Error", error_msg)
        else:
            print(f"ERROR: {error_msg}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()