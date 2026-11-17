# PDF Merger Suite

A clean, professional PDF merger built in Python with both a desktop graphical interface (GUI) and a scriptable command-line interface (CLI).

## Features

- **Clean Graphical Interface**: Modern Tkinter/ttk layout with intuitive controls.
- **Flexible Input**: Import individual PDF files or ingest entire directories recursively.
- **Custom Reordering**: Move files up or down in the sequence with a single click.
- **Granular Page Selection**: Merge entire documents or select specific pages (e.g., `1-3, 5, 8-10`).
- **Automatic Bookmarks**: Optionally generate an outline / table of contents matching input file names.
- **CLI Support**: Merge PDFs from the terminal or shell scripts without launching the GUI.
- **Robust Validation**: Detects corrupt files, password protection, and zero-page selections before merging.

## Project Structure

```text
.
├── pdf_merger/
│   ├── __init__.py
│   ├── core.py       # Core PDF processing and validation
│   └── gui.py        # Desktop UI implementation (Tkinter)
├── tests/
│   └── test_main.py  # Unit and integration tests
├── main.py           # Application entry point (GUI/CLI)
├── requirements.txt
└── README.md
```

## Installation

1. Ensure you have Python 3.9+ installed.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Graphical User Interface (Default)

Run:
```bash
python main.py
```

- Click **Add Files** or **Add Folder** to populate the queue.
- Highlight items and use **Move Up** / **Move Down** to alter order.
- Double-click or select an item to change page ranges (e.g. `all` or `1-4, 7`).
- Click **Merge PDFs** and choose your destination path.

### Command Line Interface (CLI)

```bash
# Basic merge
python main.py -i file1.pdf file2.pdf -o merged.pdf

# Merge with page ranges
python main.py -i file1.pdf file2.pdf --ranges "1-3" "all" -o output.pdf

# Include bookmarks
python main.py -i doc1.pdf doc2.pdf -o combined.pdf --bookmarks
```

## Running Tests

```bash
pytest
```
