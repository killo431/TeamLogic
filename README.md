# Knowledge Base Manager

A comprehensive GUI application for managing knowledge graphs with AI integration and semantic search capabilities.

## Features

- **JSON Data Import**: Import and process JSON files with automatic entity extraction
- **Knowledge Graph Management**: Visualize and manage entities and their relationships
- **Semantic Search**: Search entities using vector embeddings and semantic similarity
- **AI Integration**: Local AI model integration for enhanced knowledge processing
- **Relationship Detection**: Automatic detection of relationships between entities
- **Settings Persistence**: Save and restore application settings between sessions
- **Modern GUI**: Intuitive tabbed interface built with tkinter

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Install Dependencies

```bash
pip install -r requirements.txt
```

**Note**: The initial installation may take some time as it downloads AI models. The first time you run the application, it will download the default AI model (~500MB).

### Optional: Install PyTorch with GPU support

For better performance with AI models, install PyTorch with CUDA support:

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## Quick Start

1. **Run the Application**:
   ```bash
   python knowledge_base_gui.py
   ```

2. **Import Sample Data**:
   - Go to the "Import Data" tab
   - Click "Browse..." and select `example_data.json`
   - Click "Process JSON File"

3. **Explore the Knowledge Graph**:
   - Go to the "Knowledge Graph" tab to see statistics and entity information
   - Click "Auto-detect Relations" to find relationships between entities

4. **Search Entities**:
   - Go to the "Search" tab
   - Enter search queries like "software engineer", "website", or "high priority"
   - View results with similarity scores

5. **Use AI Assistant**:
   - Go to the "AI Assistant" tab
   - Wait for the model to load (status will show "Model loaded")
   - Ask questions about your data like "What projects is John working on?"

## Usage Guide

### Importing JSON Data

The application can process JSON files and automatically extract entities based on configurable rules:

1. **Select File**: Browse and select a JSON file
2. **Configure Entity Types**: Define what types of entities to extract and their key fields
3. **Process**: The application will:
   - Parse the JSON structure
   - Extract entities based on configuration
   - Detect relationships between entities
   - Generate vector embeddings for semantic search

### Entity Types Configuration

The application supports configurable entity types with custom fields:

- **Person**: name, email, phone, title, department
- **Organization**: name, address, website, industry  
- **Project**: name, description, status, deadline
- **Task**: title, description, assignee, priority, due_date
- **Document**: title, content, author, created_date

You can add, edit, or remove entity types in the Import Data tab.

### Knowledge Graph

The Knowledge Graph tab provides:

- **Statistics**: Total entities, relationships, graph density
- **Entity Breakdown**: Count by entity type
- **Relationship Types**: Different types of relationships detected
- **Sample Entities**: Preview of entities in the graph

### Semantic Search

The Search tab offers powerful semantic search capabilities:

- **Query Input**: Enter natural language queries
- **Entity Type Filter**: Limit search to specific entity types
- **Results Limit**: Control maximum number of results
- **Similarity Scores**: See how closely results match your query
- **Entity Details**: Double-click results to see full entity information

### AI Assistant

The AI Assistant provides:

- **Model Selection**: Choose from available AI models
- **Chat Interface**: Ask questions about your knowledge base
- **Context-Aware Responses**: AI uses your imported data to answer questions
- **Entity Processing**: Enhance entities with AI-generated summaries and classifications

### Settings

Customize the application in the Settings tab:

- **General Settings**: Auto-save preferences
- **Search Settings**: Default result limits
- **Graph Settings**: Visualization layout options
- **AI Settings**: Default AI model selection

## Supported File Formats

### Input Files
- **JSON**: Primary format for data import
- Nested JSON structures are supported
- Arrays and objects are processed recursively

### Export Formats
- **JSON**: Save knowledge graphs in JSON format
- **Pickle**: Save knowledge graphs in Python pickle format

## AI Models

The application supports various AI models:

- **DistilBERT Base** (Default): Fast, lightweight, good for general use
- **BERT Base**: More accurate, slower processing
- **GPT-2**: Text generation and conversational AI
- **BART Large CNN**: Specialized for text summarization

### Model Requirements

- **CPU**: All models work on CPU (slower)
- **GPU**: CUDA-compatible GPU recommended for better performance
- **Memory**: 4-8GB RAM recommended depending on model size

## Example Data

The included `example_data.json` contains sample data with:

- **Team Members**: Software engineers, product managers, designers
- **Projects**: Website redesign, API development, mobile app
- **Organization**: Company information
- **Meetings**: Team meetings and project kickoffs  
- **Documents**: Technical requirements, research reports
- **Tasks**: Development tasks with assignments and priorities

This sample data demonstrates various entity types and relationships that the application can detect and manage.

## Troubleshooting

### Common Issues

1. **"Transformers library not available"**:
   ```bash
   pip install transformers torch
   ```

2. **Model loading fails**:
   - Check internet connection (models download on first use)
   - Try a different model (some require more memory)
   - Restart the application

3. **Search returns no results**:
   - Make sure you've imported and processed data
   - Check that embeddings were generated (visible in graph statistics)
   - Try different search terms

4. **GUI feels slow**:
   - Install PyTorch with GPU support
   - Choose a smaller AI model (DistilBERT recommended)
   - Process smaller JSON files

### Performance Tips

- Use DistilBERT for best balance of speed and accuracy
- Install GPU support for faster AI processing
- Limit entity types to those you actually need
- Use specific search terms for better results

## Architecture

The application consists of several key components:

- **data_ingestion.py**: JSON parsing and entity extraction
- **knowledge_graph.py**: Graph management using NetworkX
- **vector_embedding.py**: Semantic embeddings with scikit-learn
- **ai_agent.py**: AI integration with Transformers library
- **knowledge_base_gui.py**: Main GUI application with tkinter

## Contributing

To extend the application:

1. **Add Entity Types**: Modify the default configuration in `SettingsManager`
2. **Custom AI Models**: Add model configurations in `ai_agent.py`
3. **New Visualizations**: Extend the graph display in the GUI
4. **Additional File Formats**: Add parsers in `data_ingestion.py`

## License

This project is provided as-is for educational and development purposes.

## System Requirements

- **Python**: 3.8+
- **RAM**: 4GB minimum, 8GB+ recommended
- **Storage**: 2GB for models and dependencies
- **OS**: Windows, macOS, Linux (tkinter support required)