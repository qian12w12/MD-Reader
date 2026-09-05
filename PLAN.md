# Plan: MD Reader (Python + PySide6)

## Context

Build a lightweight, single-window Markdown editor/previewer using Python + PySide6. The app should have:
- A text editor pane (left) for writing/editing Markdown
- A rendered preview pane (right) showing the formatted output
- A view toggle: **Preview Only** (hides editor, fills window) and **Normal** (side-by-side)
- Clean, native-looking UI — no fancy animations, compact layout, all controls visible without scrolling
- Fixed dark theme throughout

## Approach

Single-file implementation (`md_reader.py`) with minimal dependencies:
- `PySide6` for the GUI
- `PySide6WebEngine` for accurate HTML rendering
- `markdown` library for MD → HTML conversion

## Files to create

| File | Purpose |
|------|---------|
| `md_reader.py` | Main application — all logic in one file (~250 lines) |

No additional files needed.

## Implementation details

### Core structure (single file):

```
md_reader.py
├── imports (PySide6, markdown, sys)
├── MainWindow class (QMainWindow)
│   ├── __init__
│   │   ├── setup dark theme palette
│   │   ├── setup UI
│   │   │   ├── QTextEdit (left, for MD input)
│   │   │   ├── QWebEngineView (right, for preview)
│   │   │   ├── QSplitter (between editor and preview)
│   │   │   ├── toolbar: Normal / Preview-Only toggle buttons
│   │   │   └── menu bar: File → Open / Save / Exit
│   │   ├── connect signals
│   │   │   ├── textChanged → update_preview()
│   │   │   ├── button clicks → toggle_view()
│   │   │   ├── menu actions → open_file() / save_file()
│   │   └── helper methods
│   │       ├── update_preview() — convert MD→HTML, load into QWebEngineView
│   │       ├── toggle_view() — switch between Normal and Preview-Only
│   │       ├── open_file() — QFileDialog → load into editor
│   │       └── save_file() — QFileDialog → write from editor
└── if __name__ == "__main__"
```

### Key design decisions:
- **Layout**: QSplitter between editor and preview (draggable divider in Normal mode)
- **Toggle**: Toolbar with two buttons — "Normal" and "Preview Only"
  - Normal: splitter visible, both panes shown (default split ratio ~50/50)
  - Preview Only: splitter removed from layout, preview widget expanded to fill
- **Auto-preview**: Editor's `textChanged` signal triggers live preview update
- **File I/O**: Open and Save via QFileDialog (no recent files list)
- **Theme**: Fixed dark — dark background on editor and preview, light text
- **Default content**: Minimal sample Markdown template covering headings, bold/italic, code blocks, tables, lists
- **CSS injection**: Embed dark-themed CSS into the HTML before loading it into QWebEngineView

### Sample default Markdown:
```markdown
# MD Reader

This is a **simple** Markdown editor.

## Features
- *Live preview* as you type
- Toggle between Normal and Preview-Only view
- Open and save `.md` files

## Code example
```python
print("Hello, world!")
```

| Feature | Status |
|---------|--------|
| Edit     | ✅      |
| Preview  | ✅      |
```

### Memory safety:
- No stray timers or unbound connections
- Standard PySide6 parent-child ownership handles cleanup
- No global state beyond the main window

## Status

**IMPLEMENTED** — `md_reader.py` written and syntax verified.

## Verification

- ✅ Syntax check passed (`py_compile`)
- ✅ All imports verified (PySide6, PySide6WebEngine, markdown)
- Run `python md_reader.py` to launch the app

## PyInstaller command

```bash
pip install pyinstaller markdown PySide6 PySide6WebEngine
pyinstaller --onefile --windowed --name="MD-Reader" md_reader.py
```

- `--onefile`: single .exe
- `--windowed`: no console window
- Output: `dist/MD-Reader.exe`
