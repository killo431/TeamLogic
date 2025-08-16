"""
Knowledge Base GUI Application
A comprehensive GUI for managing knowledge graphs with AI integration
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
import threading
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import os
import sys

# Import our knowledge base modules
from data_ingestion import JSONProcessor, DataIngestionError
from knowledge_graph import KnowledgeGraph, Entity, Relationship
from vector_embedding import VectorEmbedder, SemanticSearchEngine
from ai_agent import AIAgent, get_available_models

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class ProgressDialog:
    """Progress dialog for long-running operations"""
    
    def __init__(self, parent, title="Processing..."):
        self.parent = parent
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x150")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (parent.winfo_screenwidth() // 2) - (400 // 2)
        y = (parent.winfo_screenheight() // 2) - (150 // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        # Create widgets
        self.label = ttk.Label(self.dialog, text="Processing...", font=('Arial', 12))
        self.label.pack(pady=20)
        
        self.progress = ttk.Progressbar(
            self.dialog, 
            mode='indeterminate', 
            length=300
        )
        self.progress.pack(pady=10)
        
        self.detail_label = ttk.Label(self.dialog, text="", font=('Arial', 10))
        self.detail_label.pack(pady=5)
        
        self.cancel_button = ttk.Button(
            self.dialog, 
            text="Cancel", 
            command=self.cancel
        )
        self.cancel_button.pack(pady=10)
        
        self.cancelled = False
        self.progress.start(10)
        
    def update_text(self, text: str, detail: str = ""):
        """Update progress text"""
        self.label.config(text=text)
        self.detail_label.config(text=detail)
        self.dialog.update()
        
    def cancel(self):
        """Cancel operation"""
        self.cancelled = True
        self.close()
        
    def close(self):
        """Close dialog"""
        self.progress.stop()
        self.dialog.grab_release()
        self.dialog.destroy()


class SettingsManager:
    """Manages application settings persistence"""
    
    def __init__(self, settings_file: Path = None):
        self.settings_file = settings_file or Path("kb_settings.json")
        self.settings = self.load_settings()
        
    def load_settings(self) -> Dict[str, Any]:
        """Load settings from file"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Error loading settings: {e}")
                
        return self.default_settings()
        
    def save_settings(self):
        """Save settings to file"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving settings: {e}")
            
    def default_settings(self) -> Dict[str, Any]:
        """Default application settings"""
        return {
            'window_geometry': '1200x800',
            'last_directory': str(Path.home()),
            'ai_model': 'distilbert-base-uncased',
            'entity_types': {
                'person': ['name', 'email', 'phone', 'title', 'department'],
                'organization': ['name', 'address', 'website', 'industry'],
                'project': ['name', 'description', 'status', 'deadline'],
                'task': ['title', 'description', 'assignee', 'priority', 'due_date'],
                'document': ['title', 'content', 'author', 'created_date']
            },
            'graph_layout': 'spring',
            'search_results_limit': 20,
            'auto_save': True,
            'auto_save_interval': 300  # 5 minutes
        }
        
    def get(self, key: str, default=None):
        """Get setting value"""
        return self.settings.get(key, default)
        
    def set(self, key: str, value: Any):
        """Set setting value"""
        self.settings[key] = value
        if self.settings.get('auto_save', True):
            self.save_settings()


class KnowledgeBaseGUI:
    """Main GUI application class"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.settings = SettingsManager()
        
        # Initialize components
        self.json_processor = JSONProcessor()
        self.knowledge_graph = KnowledgeGraph()
        self.vector_embedder = VectorEmbedder()
        self.search_engine = SemanticSearchEngine(self.vector_embedder)
        self.ai_agent = None
        
        # GUI variables
        self.current_file = None
        self.processing_thread = None
        
        # Initialize GUI
        self.setup_gui()
        self.setup_menu()
        self.load_settings()
        
        # Initialize AI agent in background
        self.init_ai_agent_async()
        
    def setup_gui(self):
        """Set up the main GUI layout"""
        self.root.title("Knowledge Base Manager")
        self.root.geometry(self.settings.get('window_geometry', '1200x800'))
        
        # Create main notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.setup_import_tab()
        self.setup_graph_tab()
        self.setup_search_tab()
        self.setup_ai_tab()
        self.setup_settings_tab()
        
        # Status bar
        self.status_bar = ttk.Label(
            self.root, 
            text="Ready", 
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def setup_menu(self):
        """Set up the application menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Import JSON Files...", command=self.import_json_files)
        file_menu.add_separator()
        file_menu.add_command(label="Save Knowledge Graph...", command=self.save_knowledge_graph)
        file_menu.add_command(label="Load Knowledge Graph...", command=self.load_knowledge_graph)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Refresh Graph", command=self.refresh_graph_view)
        view_menu.add_command(label="Graph Statistics", command=self.show_graph_stats)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        
    def setup_import_tab(self):
        """Set up the JSON import tab"""
        import_frame = ttk.Frame(self.notebook)
        self.notebook.add(import_frame, text="Import Data")
        
        # File selection section
        file_section = ttk.LabelFrame(import_frame, text="File Selection", padding=10)
        file_section.pack(fill=tk.X, padx=10, pady=5)
        
        self.file_path_var = tk.StringVar()
        ttk.Label(file_section, text="JSON File:").pack(anchor=tk.W)
        
        file_frame = ttk.Frame(file_section)
        file_frame.pack(fill=tk.X, pady=5)
        
        ttk.Entry(file_frame, textvariable=self.file_path_var, width=60).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )
        ttk.Button(file_frame, text="Browse...", command=self.browse_json_file).pack(
            side=tk.RIGHT, padx=(5, 0)
        )
        
        # Configuration section
        config_section = ttk.LabelFrame(import_frame, text="Entity Configuration", padding=10)
        config_section.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Entity types configuration
        ttk.Label(config_section, text="Entity Types and Fields:").pack(anchor=tk.W)
        
        # Create tree view for entity configuration
        self.entity_config_tree = ttk.Treeview(
            config_section, 
            columns=('fields',), 
            height=8
        )
        self.entity_config_tree.heading('#0', text='Entity Type')
        self.entity_config_tree.heading('fields', text='Fields')
        self.entity_config_tree.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Populate entity configuration
        self.populate_entity_config()
        
        # Control buttons
        button_frame = ttk.Frame(config_section)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="Add Entity Type", command=self.add_entity_type).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Button(button_frame, text="Edit Selected", command=self.edit_entity_type).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="Remove Selected", command=self.remove_entity_type).pack(
            side=tk.LEFT, padx=5
        )
        
        # Process button
        process_frame = ttk.Frame(import_frame)
        process_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.process_button = ttk.Button(
            process_frame, 
            text="Process JSON File", 
            command=self.process_json_file
        )
        self.process_button.pack(side=tk.RIGHT)
        
    def setup_graph_tab(self):
        """Set up the knowledge graph visualization tab"""
        graph_frame = ttk.Frame(self.notebook)
        self.notebook.add(graph_frame, text="Knowledge Graph")
        
        # Control panel
        control_panel = ttk.LabelFrame(graph_frame, text="Graph Controls", padding=10)
        control_panel.pack(fill=tk.X, padx=10, pady=5)
        
        control_frame = ttk.Frame(control_panel)
        control_frame.pack(fill=tk.X)
        
        ttk.Button(control_frame, text="Refresh", command=self.refresh_graph_view).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Button(control_frame, text="Auto-detect Relations", command=self.auto_detect_relations).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(control_frame, text="Export Graph", command=self.export_graph).pack(
            side=tk.LEFT, padx=5
        )
        
        # Layout selection
        ttk.Label(control_frame, text="Layout:").pack(side=tk.LEFT, padx=(20, 5))
        self.layout_var = tk.StringVar(value=self.settings.get('graph_layout', 'spring'))
        layout_combo = ttk.Combobox(
            control_frame, 
            textvariable=self.layout_var,
            values=['spring', 'circular', 'random', 'shell'],
            state='readonly',
            width=10
        )
        layout_combo.pack(side=tk.LEFT, padx=5)
        layout_combo.bind('<<ComboboxSelected>>', self.on_layout_changed)
        
        # Graph display area (placeholder)
        graph_display = ttk.LabelFrame(graph_frame, text="Graph Visualization", padding=10)
        graph_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # For now, use a text widget as placeholder for graph visualization
        self.graph_text = scrolledtext.ScrolledText(graph_display, wrap=tk.WORD, height=20)
        self.graph_text.pack(fill=tk.BOTH, expand=True)
        
        # Entity/Relationship details panel
        details_panel = ttk.LabelFrame(graph_frame, text="Details", padding=10)
        details_panel.pack(fill=tk.X, padx=10, pady=5)
        
        self.details_text = scrolledtext.ScrolledText(details_panel, wrap=tk.WORD, height=6)
        self.details_text.pack(fill=tk.BOTH, expand=True)
        
    def setup_search_tab(self):
        """Set up the semantic search tab"""
        search_frame = ttk.Frame(self.notebook)
        self.notebook.add(search_frame, text="Search")
        
        # Search input section
        search_section = ttk.LabelFrame(search_frame, text="Semantic Search", padding=10)
        search_section.pack(fill=tk.X, padx=10, pady=5)
        
        # Search query
        ttk.Label(search_section, text="Search Query:").pack(anchor=tk.W)
        
        query_frame = ttk.Frame(search_section)
        query_frame.pack(fill=tk.X, pady=5)
        
        self.search_query_var = tk.StringVar()
        self.search_entry = ttk.Entry(
            query_frame, 
            textvariable=self.search_query_var, 
            font=('Arial', 12)
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.search_entry.bind('<Return>', self.perform_search)
        
        ttk.Button(query_frame, text="Search", command=self.perform_search).pack(
            side=tk.RIGHT, padx=(5, 0)
        )
        
        # Search filters
        filter_frame = ttk.Frame(search_section)
        filter_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(filter_frame, text="Entity Type:").pack(side=tk.LEFT)
        self.search_type_var = tk.StringVar(value="All")
        type_combo = ttk.Combobox(
            filter_frame, 
            textvariable=self.search_type_var,
            values=["All"] + list(self.settings.get('entity_types', {}).keys()),
            state='readonly',
            width=15
        )
        type_combo.pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Label(filter_frame, text="Max Results:").pack(side=tk.LEFT)
        self.max_results_var = tk.StringVar(value=str(self.settings.get('search_results_limit', 20)))
        ttk.Spinbox(
            filter_frame, 
            from_=5, to=100, increment=5,
            textvariable=self.max_results_var,
            width=10
        ).pack(side=tk.LEFT, padx=5)
        
        # Search results
        results_section = ttk.LabelFrame(search_frame, text="Search Results", padding=10)
        results_section.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Results tree
        self.results_tree = ttk.Treeview(
            results_section,
            columns=('score', 'type', 'details'),
            height=15
        )
        self.results_tree.heading('#0', text='Entity ID')
        self.results_tree.heading('score', text='Score')
        self.results_tree.heading('type', text='Type')
        self.results_tree.heading('details', text='Details')
        
        # Configure column widths
        self.results_tree.column('#0', width=200)
        self.results_tree.column('score', width=80)
        self.results_tree.column('type', width=100)
        self.results_tree.column('details', width=400)
        
        # Scrollbar for results
        results_scrollbar = ttk.Scrollbar(results_section, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=results_scrollbar.set)
        
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double-click to show entity details
        self.results_tree.bind('<Double-1>', self.show_entity_details)
        
    def setup_ai_tab(self):
        """Set up the AI agent interaction tab"""
        ai_frame = ttk.Frame(self.notebook)
        self.notebook.add(ai_frame, text="AI Assistant")
        
        # Model selection section
        model_section = ttk.LabelFrame(ai_frame, text="AI Model Configuration", padding=10)
        model_section.pack(fill=tk.X, padx=10, pady=5)
        
        model_frame = ttk.Frame(model_section)
        model_frame.pack(fill=tk.X)
        
        ttk.Label(model_frame, text="Model:").pack(side=tk.LEFT)
        self.ai_model_var = tk.StringVar(value=self.settings.get('ai_model', 'distilbert-base-uncased'))
        
        # Get available models
        available_models = list(get_available_models().keys())
        model_combo = ttk.Combobox(
            model_frame,
            textvariable=self.ai_model_var,
            values=available_models,
            state='readonly',
            width=30
        )
        model_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(model_frame, text="Load Model", command=self.load_ai_model).pack(
            side=tk.LEFT, padx=10
        )
        
        self.ai_status_label = ttk.Label(model_frame, text="Model not loaded", foreground='red')
        self.ai_status_label.pack(side=tk.LEFT, padx=10)
        
        # Chat interface
        chat_section = ttk.LabelFrame(ai_frame, text="AI Chat", padding=10)
        chat_section.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Chat history
        self.chat_history = scrolledtext.ScrolledText(
            chat_section, 
            wrap=tk.WORD, 
            height=15,
            state=tk.DISABLED
        )
        self.chat_history.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Chat input
        input_frame = ttk.Frame(chat_section)
        input_frame.pack(fill=tk.X)
        
        self.chat_input_var = tk.StringVar()
        chat_entry = ttk.Entry(
            input_frame,
            textvariable=self.chat_input_var,
            font=('Arial', 12)
        )
        chat_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        chat_entry.bind('<Return>', self.send_chat_message)
        
        ttk.Button(input_frame, text="Send", command=self.send_chat_message).pack(
            side=tk.RIGHT, padx=(5, 0)
        )
        
        # Chat controls
        control_frame = ttk.Frame(chat_section)
        control_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(control_frame, text="Clear History", command=self.clear_chat_history).pack(
            side=tk.LEFT
        )
        ttk.Button(control_frame, text="Process Entities with AI", command=self.process_entities_with_ai).pack(
            side=tk.RIGHT
        )
        
    def setup_settings_tab(self):
        """Set up the settings configuration tab"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="Settings")
        
        # Create a canvas with scrollbar for settings
        canvas = tk.Canvas(settings_frame)
        scrollbar = ttk.Scrollbar(settings_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # General settings
        general_section = ttk.LabelFrame(scrollable_frame, text="General Settings", padding=10)
        general_section.pack(fill=tk.X, padx=10, pady=5)
        
        # Auto-save settings
        self.auto_save_var = tk.BooleanVar(value=self.settings.get('auto_save', True))
        ttk.Checkbutton(
            general_section, 
            text="Auto-save settings", 
            variable=self.auto_save_var
        ).pack(anchor=tk.W)
        
        # Search settings
        search_section = ttk.LabelFrame(scrollable_frame, text="Search Settings", padding=10)
        search_section.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(search_section, text="Default search results limit:").pack(anchor=tk.W)
        self.search_limit_var = tk.StringVar(value=str(self.settings.get('search_results_limit', 20)))
        ttk.Spinbox(
            search_section, 
            from_=5, to=100, increment=5,
            textvariable=self.search_limit_var,
            width=10
        ).pack(anchor=tk.W, pady=2)
        
        # Graph settings
        graph_section = ttk.LabelFrame(scrollable_frame, text="Graph Settings", padding=10)
        graph_section.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(graph_section, text="Default graph layout:").pack(anchor=tk.W)
        self.default_layout_var = tk.StringVar(value=self.settings.get('graph_layout', 'spring'))
        ttk.Combobox(
            graph_section,
            textvariable=self.default_layout_var,
            values=['spring', 'circular', 'random', 'shell'],
            state='readonly'
        ).pack(anchor=tk.W, pady=2)
        
        # AI settings
        ai_section = ttk.LabelFrame(scrollable_frame, text="AI Settings", padding=10)
        ai_section.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(ai_section, text="Default AI model:").pack(anchor=tk.W)
        self.default_ai_model_var = tk.StringVar(value=self.settings.get('ai_model', 'distilbert-base-uncased'))
        ttk.Combobox(
            ai_section,
            textvariable=self.default_ai_model_var,
            values=list(get_available_models().keys()),
            state='readonly'
        ).pack(anchor=tk.W, pady=2)
        
        # Save settings button
        ttk.Button(
            scrollable_frame, 
            text="Save Settings", 
            command=self.save_settings
        ).pack(pady=20)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def populate_entity_config(self):
        """Populate entity configuration tree view"""
        # Clear existing items
        for item in self.entity_config_tree.get_children():
            self.entity_config_tree.delete(item)
            
        # Add entity types from settings
        entity_types = self.settings.get('entity_types', {})
        for entity_type, fields in entity_types.items():
            fields_str = ', '.join(fields)
            self.entity_config_tree.insert('', 'end', text=entity_type, values=(fields_str,))
            
    def browse_json_file(self):
        """Browse for JSON file to import"""
        file_path = filedialog.askopenfilename(
            title="Select JSON File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=self.settings.get('last_directory', str(Path.home()))
        )
        
        if file_path:
            self.file_path_var.set(file_path)
            self.settings.set('last_directory', str(Path(file_path).parent))
            
    def process_json_file(self):
        """Process the selected JSON file"""
        file_path = self.file_path_var.get()
        if not file_path or not Path(file_path).exists():
            messagebox.showerror("Error", "Please select a valid JSON file")
            return
            
        # Update JSON processor configuration
        entity_config = {}
        for item in self.entity_config_tree.get_children():
            entity_type = self.entity_config_tree.item(item, 'text')
            fields_str = self.entity_config_tree.item(item, 'values')[0]
            fields = [f.strip() for f in fields_str.split(',')]
            entity_config[entity_type] = fields
            
        config = {'entity_types': entity_config}
        self.json_processor.update_config(config)
        
        # Process file in background thread
        self.processing_thread = threading.Thread(
            target=self._process_file_background,
            args=(Path(file_path),)
        )
        self.processing_thread.start()
        
    def _process_file_background(self, file_path: Path):
        """Background thread for processing JSON file"""
        progress_dialog = ProgressDialog(self.root, "Processing JSON File")
        
        try:
            # Set up progress callback
            def progress_callback(current, total):
                if not progress_dialog.cancelled:
                    progress_dialog.update_text(
                        f"Processing entities... {current}/{total}",
                        f"File: {file_path.name}"
                    )
                    
            self.json_processor.set_progress_callback(progress_callback)
            
            # Process the file
            progress_dialog.update_text("Loading JSON file...", f"File: {file_path.name}")
            entities = self.json_processor.process_file(file_path)
            
            if progress_dialog.cancelled:
                return
                
            progress_dialog.update_text("Adding entities to knowledge graph...", f"Found {len(entities)} entities")
            
            # Add entities to knowledge graph
            for entity in entities:
                if progress_dialog.cancelled:
                    break
                try:
                    self.knowledge_graph.add_entity(entity)
                except Exception as e:
                    logging.error(f"Error adding entity {entity.get('id', 'unknown')}: {e}")
                    
            if not progress_dialog.cancelled:
                # Auto-detect relationships
                progress_dialog.update_text("Detecting relationships...", "")
                relationship_count = self.knowledge_graph.auto_detect_relationships()
                
                # Fit embeddings
                progress_dialog.update_text("Generating embeddings...", "")
                entities_list = [entity.to_dict() for entity in self.knowledge_graph.entities.values()]
                self.vector_embedder.fit_embeddings(entities_list)
                
                # Update UI
                self.root.after(0, lambda: self._process_complete(len(entities), relationship_count))
                
        except Exception as e:
            logging.error(f"Error processing file: {e}")
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error processing file: {e}"))
            
        finally:
            self.root.after(0, progress_dialog.close)
            
    def _process_complete(self, entity_count, relationship_count):
        """Called when processing is complete"""
        self.status_bar.config(text=f"Processed {entity_count} entities, {relationship_count} relationships")
        self.refresh_graph_view()
        messagebox.showinfo("Success", f"Successfully processed {entity_count} entities and detected {relationship_count} relationships")
        
    def refresh_graph_view(self):
        """Refresh the graph visualization"""
        try:
            stats = self.knowledge_graph.get_graph_stats()
            
            # Update graph text display (simplified visualization)
            graph_info = f"Knowledge Graph Statistics:\n\n"
            graph_info += f"Total Entities: {stats['total_entities']}\n"
            graph_info += f"Total Relationships: {stats['total_relationships']}\n"
            graph_info += f"Graph Density: {stats['graph_density']:.3f}\n"
            graph_info += f"Connected Components: {stats['connected_components']}\n\n"
            
            graph_info += "Entity Types:\n"
            for entity_type, count in stats['entity_types'].items():
                graph_info += f"  {entity_type}: {count}\n"
                
            graph_info += "\nRelationship Types:\n"
            for rel_type, count in stats['relationship_types'].items():
                graph_info += f"  {rel_type}: {count}\n"
                
            # Add sample entities
            graph_info += "\nSample Entities:\n"
            for i, (entity_id, entity) in enumerate(list(self.knowledge_graph.entities.items())[:10]):
                graph_info += f"  {entity_id} ({entity.type})\n"
                if i >= 9:
                    break
                    
            self.graph_text.delete(1.0, tk.END)
            self.graph_text.insert(1.0, graph_info)
            
        except Exception as e:
            logging.error(f"Error refreshing graph view: {e}")
            
    def perform_search(self, event=None):
        """Perform semantic search"""
        query = self.search_query_var.get().strip()
        if not query:
            return
            
        try:
            # Get search parameters
            entity_type = self.search_type_var.get()
            if entity_type == "All":
                entity_type = None
                
            max_results = int(self.max_results_var.get())
            
            # Perform search
            results = self.search_engine.search(
                query, 
                entity_type=entity_type,
                top_k=max_results
            )
            
            # Clear previous results
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
                
            # Add new results
            for result in results:
                entity_id = result['entity_id']
                score = f"{result['similarity_score']:.3f}"
                
                # Get entity details
                entity = self.knowledge_graph.entities.get(entity_id)
                if entity:
                    entity_type = entity.type
                    # Get first few attributes for details
                    details_parts = []
                    for key, value in list(entity.attributes.items())[:3]:
                        if isinstance(value, str) and len(value) < 50:
                            details_parts.append(f"{key}: {value}")
                    details = "; ".join(details_parts)
                else:
                    entity_type = "unknown"
                    details = ""
                    
                self.results_tree.insert(
                    '', 'end',
                    text=entity_id,
                    values=(score, entity_type, details)
                )
                
            self.status_bar.config(text=f"Found {len(results)} results for '{query}'")
            
        except Exception as e:
            logging.error(f"Error in search: {e}")
            messagebox.showerror("Error", f"Search error: {e}")
            
    def show_entity_details(self, event):
        """Show details for selected entity"""
        selection = self.results_tree.selection()
        if not selection:
            return
            
        item = selection[0]
        entity_id = self.results_tree.item(item, 'text')
        
        entity = self.knowledge_graph.entities.get(entity_id)
        if entity:
            details = f"Entity: {entity_id}\n"
            details += f"Type: {entity.type}\n"
            details += f"Created: {entity.created_at}\n"
            details += f"Updated: {entity.updated_at}\n\n"
            
            details += "Attributes:\n"
            for key, value in entity.attributes.items():
                if isinstance(value, list):
                    details += f"  {key}: {', '.join(map(str, value))}\n"
                else:
                    details += f"  {key}: {value}\n"
                    
            # Show relationships
            relationships = self.knowledge_graph.find_relationships(entity_id)
            if relationships:
                details += f"\nRelationships ({len(relationships)}):\n"
                for rel in relationships[:10]:  # Show first 10
                    if rel.source_id == entity_id:
                        details += f"  → {rel.target_id} ({rel.type})\n"
                    else:
                        details += f"  ← {rel.source_id} ({rel.type})\n"
                        
            self.details_text.delete(1.0, tk.END)
            self.details_text.insert(1.0, details)
            
    def init_ai_agent_async(self):
        """Initialize AI agent in background"""
        def init_ai():
            try:
                model_name = self.settings.get('ai_model', 'distilbert-base-uncased')
                self.ai_agent = AIAgent(model_name)
                self.root.after(0, lambda: self.ai_status_label.config(text="Model loaded", foreground='green'))
                self.root.after(0, lambda: self.status_bar.config(text="AI model loaded successfully"))
            except Exception as e:
                logging.error(f"Error loading AI model: {e}")
                self.root.after(0, lambda: self.ai_status_label.config(
                    text="Model failed to load", 
                    foreground='red'
                ))
                
        threading.Thread(target=init_ai, daemon=True).start()
        
    def load_ai_model(self):
        """Load selected AI model"""
        model_name = self.ai_model_var.get()
        if not model_name:
            return
            
        self.ai_status_label.config(text="Loading model...", foreground='orange')
        
        def load_model():
            try:
                self.ai_agent = AIAgent(model_name)
                self.root.after(0, lambda: self.ai_status_label.config(text="Model loaded", foreground='green'))
                self.root.after(0, lambda: self.settings.set('ai_model', model_name))
            except Exception as e:
                logging.error(f"Error loading AI model: {e}")
                self.root.after(0, lambda: self.ai_status_label.config(
                    text="Model failed to load", 
                    foreground='red'
                ))
                self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to load model: {e}"))
                
        threading.Thread(target=load_model, daemon=True).start()
        
    def send_chat_message(self, event=None):
        """Send message to AI agent"""
        if not self.ai_agent:
            messagebox.showwarning("Warning", "AI model not loaded")
            return
            
        message = self.chat_input_var.get().strip()
        if not message:
            return
            
        # Clear input
        self.chat_input_var.set("")
        
        # Add user message to chat
        self._add_chat_message("You", message)
        
        # Get AI response in background
        def get_response():
            try:
                # Get some context entities
                context_entities = list(self.knowledge_graph.entities.values())[:5]
                context_entities = [entity.to_dict() for entity in context_entities]
                
                response = self.ai_agent.query_knowledge(message, context_entities)
                ai_response = response.get('conversational_response', 'No response generated')
                
                self.root.after(0, lambda: self._add_chat_message("AI", ai_response))
                
            except Exception as e:
                logging.error(f"Error getting AI response: {e}")
                self.root.after(0, lambda: self._add_chat_message("AI", f"Error: {e}"))
                
        threading.Thread(target=get_response, daemon=True).start()
        
    def _add_chat_message(self, sender: str, message: str):
        """Add message to chat history"""
        self.chat_history.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.chat_history.insert(tk.END, f"[{timestamp}] {sender}: {message}\n\n")
        self.chat_history.config(state=tk.DISABLED)
        self.chat_history.see(tk.END)
        
    def clear_chat_history(self):
        """Clear chat history"""
        self.chat_history.config(state=tk.NORMAL)
        self.chat_history.delete(1.0, tk.END)
        self.chat_history.config(state=tk.DISABLED)
        
        if self.ai_agent and hasattr(self.ai_agent, 'conversational_agent'):
            self.ai_agent.conversational_agent.clear_history()
            
    def process_entities_with_ai(self):
        """Process existing entities with AI"""
        if not self.ai_agent:
            messagebox.showwarning("Warning", "AI model not loaded")
            return
            
        if not self.knowledge_graph.entities:
            messagebox.showinfo("Info", "No entities to process")
            return
            
        def process_entities():
            progress_dialog = ProgressDialog(self.root, "Processing Entities with AI")
            
            try:
                entities_list = [entity.to_dict() for entity in self.knowledge_graph.entities.values()]
                progress_dialog.update_text(f"Processing {len(entities_list)} entities with AI...")
                
                processed_entities = self.ai_agent.process_entities(entities_list)
                
                # Update entities with AI enhancements
                for processed_entity in processed_entities:
                    entity_id = processed_entity['id']
                    if entity_id in self.knowledge_graph.entities:
                        # Add AI-generated attributes
                        ai_attrs = {}
                        for key in ['ai_extracted_entities', 'ai_summary', 'ai_classification']:
                            if key in processed_entity:
                                ai_attrs[key] = processed_entity[key]
                                
                        if ai_attrs:
                            self.knowledge_graph.update_entity(entity_id, ai_attrs)
                            
                self.root.after(0, lambda: messagebox.showinfo("Success", "Entities processed with AI successfully"))
                self.root.after(0, self.refresh_graph_view)
                
            except Exception as e:
                logging.error(f"Error processing entities with AI: {e}")
                self.root.after(0, lambda: messagebox.showerror("Error", f"AI processing error: {e}"))
                
            finally:
                self.root.after(0, progress_dialog.close)
                
        threading.Thread(target=process_entities, daemon=True).start()
        
    def auto_detect_relations(self):
        """Auto-detect relationships in knowledge graph"""
        try:
            relationship_count = self.knowledge_graph.auto_detect_relationships()
            self.refresh_graph_view()
            messagebox.showinfo("Success", f"Detected {relationship_count} new relationships")
        except Exception as e:
            logging.error(f"Error auto-detecting relationships: {e}")
            messagebox.showerror("Error", f"Error detecting relationships: {e}")
            
    def on_layout_changed(self, event):
        """Handle layout selection change"""
        layout = self.layout_var.get()
        self.settings.set('graph_layout', layout)
        self.refresh_graph_view()
        
    def add_entity_type(self):
        """Add new entity type configuration"""
        # Simple dialog for adding entity type
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Entity Type")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Entity Type:").pack(pady=5)
        type_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=type_var, width=30).pack(pady=5)
        
        ttk.Label(dialog, text="Fields (comma-separated):").pack(pady=5)
        fields_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=fields_var, width=50).pack(pady=5)
        
        def add_type():
            entity_type = type_var.get().strip()
            fields_str = fields_var.get().strip()
            
            if entity_type and fields_str:
                fields = [f.strip() for f in fields_str.split(',')]
                
                # Update settings
                entity_types = self.settings.get('entity_types', {})
                entity_types[entity_type] = fields
                self.settings.set('entity_types', entity_types)
                
                # Update tree
                self.populate_entity_config()
                dialog.destroy()
                
        ttk.Button(dialog, text="Add", command=add_type).pack(pady=10)
        
    def edit_entity_type(self):
        """Edit selected entity type"""
        selection = self.entity_config_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Please select an entity type to edit")
            return
            
        # Implementation similar to add_entity_type but with pre-filled values
        pass
        
    def remove_entity_type(self):
        """Remove selected entity type"""
        selection = self.entity_config_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Please select an entity type to remove")
            return
            
        item = selection[0]
        entity_type = self.entity_config_tree.item(item, 'text')
        
        if messagebox.askyesno("Confirm", f"Remove entity type '{entity_type}'?"):
            entity_types = self.settings.get('entity_types', {})
            if entity_type in entity_types:
                del entity_types[entity_type]
                self.settings.set('entity_types', entity_types)
                self.populate_entity_config()
                
    def save_knowledge_graph(self):
        """Save knowledge graph to file"""
        file_path = filedialog.asksaveasfilename(
            title="Save Knowledge Graph",
            filetypes=[("JSON files", "*.json"), ("Pickle files", "*.pkl")],
            defaultextension=".json"
        )
        
        if file_path:
            try:
                self.knowledge_graph.save_to_file(Path(file_path))
                messagebox.showinfo("Success", f"Knowledge graph saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Error saving knowledge graph: {e}")
                
    def load_knowledge_graph(self):
        """Load knowledge graph from file"""
        file_path = filedialog.askopenfilename(
            title="Load Knowledge Graph",
            filetypes=[("JSON files", "*.json"), ("Pickle files", "*.pkl"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                self.knowledge_graph.load_from_file(Path(file_path))
                
                # Refit embeddings
                entities_list = [entity.to_dict() for entity in self.knowledge_graph.entities.values()]
                if entities_list:
                    self.vector_embedder.fit_embeddings(entities_list)
                    
                self.refresh_graph_view()
                messagebox.showinfo("Success", f"Knowledge graph loaded from {file_path}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error loading knowledge graph: {e}")
                
    def export_graph(self):
        """Export graph visualization"""
        # This would export the graph as an image - placeholder for now
        messagebox.showinfo("Info", "Graph export feature coming soon")
        
    def show_graph_stats(self):
        """Show detailed graph statistics"""
        try:
            stats = self.knowledge_graph.get_graph_stats()
            embedding_stats = self.vector_embedder.get_embedding_stats()
            
            stats_text = "Knowledge Graph Statistics\n\n"
            stats_text += f"Entities: {stats['total_entities']}\n"
            stats_text += f"Relationships: {stats['total_relationships']}\n"
            stats_text += f"Density: {stats['graph_density']:.4f}\n"
            stats_text += f"Connected Components: {stats['connected_components']}\n\n"
            
            stats_text += "Entity Types:\n"
            for entity_type, count in stats['entity_types'].items():
                stats_text += f"  {entity_type}: {count}\n"
                
            stats_text += "\nRelationship Types:\n"
            for rel_type, count in stats['relationship_types'].items():
                stats_text += f"  {rel_type}: {count}\n"
                
            if embedding_stats:
                stats_text += f"\nEmbedding Statistics:\n"
                stats_text += f"  Embedded Entities: {embedding_stats['total_entities']}\n"
                stats_text += f"  Embedding Dimension: {embedding_stats['embedding_dimension']}\n"
                stats_text += f"  Sparsity: {embedding_stats['sparsity']:.3f}\n"
                
            # Create dialog to show stats
            dialog = tk.Toplevel(self.root)
            dialog.title("Graph Statistics")
            dialog.geometry("400x600")
            
            text_widget = scrolledtext.ScrolledText(dialog, wrap=tk.WORD)
            text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            text_widget.insert(1.0, stats_text)
            text_widget.config(state=tk.DISABLED)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error getting statistics: {e}")
            
    def save_settings(self):
        """Save application settings"""
        try:
            # Update settings from GUI
            self.settings.set('auto_save', self.auto_save_var.get())
            self.settings.set('search_results_limit', int(self.search_limit_var.get()))
            self.settings.set('graph_layout', self.default_layout_var.get())
            self.settings.set('ai_model', self.default_ai_model_var.get())
            
            # Save to file
            self.settings.save_settings()
            messagebox.showinfo("Success", "Settings saved successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error saving settings: {e}")
            
    def load_settings(self):
        """Load application settings"""
        try:
            # Restore window geometry
            geometry = self.settings.get('window_geometry', '1200x800')
            self.root.geometry(geometry)
            
        except Exception as e:
            logging.error(f"Error loading settings: {e}")
            
    def show_about(self):
        """Show about dialog"""
        about_text = """Knowledge Base Manager v1.0

A comprehensive GUI application for managing knowledge graphs 
with AI integration and semantic search capabilities.

Features:
• JSON data import and processing
• Knowledge graph visualization
• Semantic search with vector embeddings
• Local AI model integration
• Relationship auto-detection
• Settings persistence

Built with Python, tkinter, NetworkX, and Transformers."""
        
        messagebox.showinfo("About", about_text)
        
    def on_closing(self):
        """Handle application closing"""
        # Save current window geometry
        self.settings.set('window_geometry', self.root.geometry())
        self.settings.save_settings()
        
        # Stop any running threads
        if self.processing_thread and self.processing_thread.is_alive():
            # Could add cancellation logic here
            pass
            
        self.root.destroy()
        
    def run(self):
        """Run the GUI application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Set initial status
        self.status_bar.config(text="Ready - Import JSON files to get started")
        
        # Start the GUI event loop
        self.root.mainloop()


def main():
    """Main entry point"""
    try:
        app = KnowledgeBaseGUI()
        app.run()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        print(f"Fatal error: {e}")


if __name__ == "__main__":
    main()