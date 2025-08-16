# JSON File Selector - TeamLogic Knowledge Base

A user-friendly GUI application for importing JSON files into the TeamLogic knowledge base system.

## Features

- **File Browser**: Navigate your local filesystem and select JSON files with built-in filtering
- **JSON Validation**: Automatic validation to ensure selected files have proper .json extension and valid JSON format
- **Preview Panel**: Display the first 20 lines of JSON content to confirm file selection
- **Error Handling**: Comprehensive error messages for invalid files, permission issues, and parsing errors
- **Cross-Platform**: Built with Python tkinter, works on Windows, macOS, and Linux

## Requirements

- Python 3.6 or higher (included with Windows 10+ and most Linux distributions)
- tkinter (usually included with Python)
- Standard library modules: json, os, sys, typing

## Installation

No installation required! Simply download the `json_file_selector.py` file.

## Usage

### Running the Application

1. **Command Line**: 
   ```bash
   python json_file_selector.py
   ```

2. **Windows**: Double-click `json_file_selector.py` (if Python is properly installed)

3. **From PowerShell** (fits with other TeamLogic tools):
   ```powershell
   python .\json_file_selector.py
   ```

### Using the Interface

1. **Select File**: Click "Browse JSON Files" to open the file dialog
2. **Preview**: Review the JSON content in the preview panel
3. **Validate**: Click "Validate JSON" to see detailed structure analysis
4. **Import**: Click "Import JSON File" to add the file to your knowledge base
5. **Clear**: Use "Clear" to reset and select a different file

### File Requirements

- Files must have a `.json` extension
- Files must contain valid JSON format
- Files must be readable (proper permissions)

## Testing

Run the test suite to verify functionality:

```bash
python test_json_selector.py
```

This will run unit tests and validate core functionality without requiring GUI interaction.

## Sample Files

The repository includes sample files for testing:

- `sample_knowledge_base.json` - Valid JSON file with knowledge base structure
- `invalid_test.json` - Invalid JSON file for testing error handling

## Error Handling

The application handles various error scenarios:

- **Invalid Extension**: Files without .json extension are rejected
- **File Not Found**: Missing files are detected and reported
- **Permission Errors**: Unreadable files show appropriate error messages
- **Invalid JSON**: Malformed JSON files display parsing errors with line numbers
- **Large Files**: File size is displayed; very large files are handled gracefully

## Integration with TeamLogic

This tool is designed to work with the TeamLogic knowledge base system. The import functionality provides a standardized interface for adding JSON data to your knowledge base.

### JSON Structure

The application works with any valid JSON structure. For TeamLogic knowledge base files, the recommended format includes:

```json
{
  "knowledge_base": {
    "version": "1.0",
    "categories": [
      {
        "name": "Category Name",
        "articles": [
          {
            "title": "Article Title",
            "content": "Article content",
            "tags": ["tag1", "tag2"]
          }
        ]
      }
    ]
  }
}
```

## Screenshots

The interface includes:
- Clean, professional layout with labeled sections
- File browser with JSON filtering
- Real-time preview panel
- Status indicators for file validation
- Action buttons for import workflow

## Troubleshooting

### Common Issues

1. **"Python not found"**: Ensure Python is installed and in your system PATH
2. **"tkinter not available"**: Install tkinter package (usually included with Python)
3. **File permission errors**: Check that you have read access to the selected file
4. **Invalid JSON errors**: Use the preview panel to identify formatting issues

### Getting Help

- Check the preview panel for file content
- Use the "Validate JSON" button for detailed error information
- Ensure file permissions allow reading
- Verify JSON format using online validators if needed

## Development

### File Structure
```
TeamLogic/
├── json_file_selector.py          # Main GUI application
├── test_json_selector.py          # Test suite
├── sample_knowledge_base.json     # Sample valid JSON
├── invalid_test.json              # Sample invalid JSON
└── README.md                      # This file
```

### Extending the Application

The `JSONFileSelector` class can be extended to:
- Add custom JSON schema validation
- Implement different import formats
- Connect to database systems
- Add file conversion features

## License

This tool is part of the TeamLogic system administration toolkit.