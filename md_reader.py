import sys
from pathlib import Path
from PySide6.QtWebEngineWidgets import QWebEngineView

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit,
    QSplitter, QToolBar, QFileDialog, QMessageBox, QStatusBar, QLabel,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QKeySequence, QFontDatabase, QPalette, QColor

import markdown


DEFAULT_CONTENT = """\
# MD 阅读器

这是一个 **简洁** 的 Markdown 编辑器。

## 功能
- *实时预览*，边写边看
- 「预览模式」切换，专注阅读
- 支持打开和保存 `.md` 文件

## 代码示例
```python
print("你好，世界！")
```

## 表格示例

| 功能     | 状态 |
|----------|------|
| 编辑     | ✅   |
| 预览     | ✅   |
| 深色主题 | ✅   |
"""

PREVIEW_CSS = """
<style>
body {
    background: #1a1a2e;
    color: #cdd6f4;
    font-family: 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
    font-size: 15px;
    line-height: 1.8;
    padding: 24px 28px;
    margin: 0;
}
h1 {
    font-size: 1.9em;
    color: #89b4fa;
    border-bottom: 2px solid #313244;
    padding-bottom: 6px;
    margin-top: 0;
}
h2 {
    font-size: 1.4em;
    color: #a6e3a1;
    border-bottom: 1px solid #313244;
    padding-bottom: 4px;
    margin-top: 1.2em;
}
h3 { color: #f9e2af; font-size: 1.15em; margin-top: 1em; }
h4, h5, h6 { color: #cba6f7; }
p  { margin: 0.7em 0; }
a  { color: #89dceb; text-decoration: none; }
a:hover { text-decoration: underline; color: #94e2d5; }
strong { color: #f38ba8; }
em { color: #fab387; }
code {
    background: #1e1e2e;
    padding: 2px 7px;
    border-radius: 4px;
    color: #f38ba8;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 0.92em;
}
pre {
    background: #1e1e2e;
    border: 1px solid #313244;
    border-radius: 8px;
    padding: 14px 16px;
    overflow-x: auto;
    margin: 1em 0;
}
pre code { background: none; padding: 0; color: #cdd6f4; font-size: 13px; }
blockquote {
    border-left: 4px solid #a6e3a1;
    margin: 0.8em 0;
    padding: 4px 16px;
    color: #6c7086;
    background: #1e1e2e;
    border-radius: 0 6px 6px 0;
}
table {
    border-collapse: collapse;
    width: 100%;
    margin: 1em 0;
    font-size: 0.95em;
}
th, td {
    border: 1px solid #313244;
    padding: 8px 14px;
    text-align: left;
}
th {
    background: #1e1e2e;
    color: #89b4fa;
    font-weight: 600;
}
tr:nth-child(even) { background: #1e1e2e; }
ul, ol { padding-left: 1.6em; }
li { margin: 0.3em 0; }
hr { border: none; border-top: 1px solid #313244; margin: 1.5em 0; }
img { max-width: 100%; border-radius: 6px; }
</style>
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MD 阅读器")
        self.resize(1200, 750)
        self.current_file: Path | None = None
        self._modified = False

        self._setup_ui()
        self._connect_signals()
        self._apply_default_content()

    # ── UI 搭建 ───────────────────────────────────────────────

    def _setup_ui(self):
        self._setup_editor()
        self._setup_preview()
        self._setup_splitter()
        self._setup_toolbar()
        self._setup_statusbar()

    def _setup_editor(self):
        self.editor = QTextEdit()
        self.editor.setTabStopDistance(24)
        font = QFontDatabase.systemFont(QFontDatabase.GeneralFont)
        font.setFamily("Consolas")
        font.setPointSize(13)
        self.editor.setFont(font)
        self.editor.setStyleSheet("""
            QTextEdit {
                background: #1e1e2e;
                color: #cdd6f4;
                border: none;
                padding: 4px;
            }
        """)

    def _setup_preview(self):
        self.preview = QWebEngineView()
        self.preview.setMinimumWidth(200)
        self.preview.setStyleSheet("QWebEngineView { background: transparent; border: none; }")

    def _setup_splitter(self):
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(4)
        self.splitter.setStyleSheet("""
            QSplitter::handle:horizontal {
                background: #313244;
            }
            QSplitter::handle:horizontal:hover {
                background: #89b4fa;
            }
        """)
        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.preview)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 1)
        self.setCentralWidget(self.splitter)

    def _setup_toolbar(self):
        toolbar = QToolBar("工具栏")
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.setIconSize(QSize(18, 18))
        self.addToolBar(toolbar)
        toolbar.setStyleSheet("""
            QToolBar {
                background: #1e1e2e;
                border-bottom: 1px solid #313244;
                padding: 4px 8px;
                spacing: 4px;
            }
            QToolBar::separator {
                width: 1px;
                background: #313244;
                margin: 4px 6px;
            }
            QToolButton {
                background: transparent;
                color: #cdd6f4;
                border: none;
                border-radius: 4px;
                padding: 5px 12px;
                font-size: 13px;
            }
            QToolButton:hover {
                background: #313244;
            }
            QToolButton:checked {
                background: #89b4fa;
                color: #1e1e2e;
                font-weight: bold;
            }
        """)

        # 文件操作
        act_open = toolbar.addAction("打开")
        act_open.setShortcut(QKeySequence.Open)
        act_open.setToolTip("打开 Markdown 文件（Ctrl+O）")

        btn_new = toolbar.addAction("新建文件")
        btn_new.setShortcut(QKeySequence.New)
        btn_new.setToolTip("新建文件（Ctrl+N）")

        act_save = toolbar.addAction("保存")
        act_save.setShortcut(QKeySequence.Save)
        act_save.setToolTip("保存当前文件（Ctrl+S）")

        act_saveas = toolbar.addAction("另存为")
        act_saveas.setShortcut(QKeySequence(Qt.CTRL | Qt.SHIFT | Qt.Key_S))
        act_saveas.setToolTip("另存为新文件（Ctrl+Shift+S）")

        toolbar.addSeparator()

        btn_preview = toolbar.addAction("预览模式")
        btn_preview.setCheckable(True)
        btn_preview.setToolTip("隐藏编辑器，仅显示预览")

        self._btn_new = btn_new
        self._btn_preview = btn_preview
        self._act_open = act_open
        self._act_save = act_save
        self._act_saveas = act_saveas

    def _setup_statusbar(self):
        self.statusbar = QStatusBar()
        self.statusbar.setStyleSheet("""
            QStatusBar {
                background: #1e1e2e;
                color: #6c7086;
                border-top: 1px solid #313244;
                font-size: 12px;
            }
            QStatusBar::item {
                border: none;
            }
        """)
        self.setStatusBar(self.statusbar)
        self._sb_file = QLabel("")
        self.statusbar.addPermanentWidget(self._sb_file)
        self._sb_modified = QLabel("")
        self.statusbar.addPermanentWidget(self._sb_modified)
        self._sb_pos = QLabel("")
        self.statusbar.addPermanentWidget(self._sb_pos)
        self.editor.textChanged.connect(self._update_status)

    # ── 信号连接 ──────────────────────────────────────────────

    def _connect_signals(self):
        self.editor.textChanged.connect(self._mark_modified)
        self.editor.textChanged.connect(self._update_preview)
        self._btn_new.triggered.connect(self._new_file)
        self._btn_preview.triggered.connect(self._toggle_view)
        self._act_open.triggered.connect(self._open_file)
        self._act_save.triggered.connect(self._save_file)
        self._act_saveas.triggered.connect(self._save_as_file)

    # ── 业务逻辑 ──────────────────────────────────────────────

    def _apply_default_content(self):
        self.editor.setPlainText(DEFAULT_CONTENT)
        self._update_preview()

    def _mark_modified(self):
        self._modified = True
        self._update_status()

    def _update_preview(self):
        md_text = self.editor.toPlainText()
        html_body = markdown.markdown(md_text, extensions=["fenced_code", "tables"])
        html = f"<html><head>{PREVIEW_CSS}</head><body>{html_body}</body></html>"
        self.preview.setHtml(html)

    def _update_status(self):
        cursor = self.editor.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        pos_text = f"第 {line} 行  第 {col} 列"
        self._sb_pos.setText(pos_text)

        mod_text = "●" if self._modified else ""
        self._sb_modified.setText(mod_text)

        if self.current_file:
            self._sb_file.setText(self.current_file.name)
        else:
            self._sb_file.setText("未命名")

    def _toggle_view(self):
        if self._btn_preview.isChecked():
            self.editor.hide()
        else:
            self.editor.show()

    def _new_file(self):
        if self._modified:
            btn = QMessageBox.question(
                self, "保存？",
                "当前文件有未保存的更改，是否保存？",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            )
            if btn == QMessageBox.Cancel:
                return
            if btn == QMessageBox.Yes:
                self._save_file()
                if self._modified:
                    return
        self.editor.setPlainText(DEFAULT_CONTENT)
        self.current_file = None
        self._modified = False
        self.setWindowTitle("MD 阅读器")
        self.editor.show()
        self._update_status()

    def _open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "打开 Markdown 文件", "", "Markdown 文件 (*.md);;所有文件 (*)"
        )
        if not path:
            return
        try:
            content = Path(path).read_text(encoding="utf-8")
            self.editor.setPlainText(content)
            self.current_file = Path(path).resolve()
            self._modified = False
            self.setWindowTitle(f"MD 阅读器 — {self.current_file.name}")
            self._update_preview()
            self.editor.show()
            self._update_status()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法打开文件：\n{e}")

    def _save_file(self):
        if self.current_file:
            self._do_save(self.current_file)
        else:
            self._save_as_file()

    def _save_as_file(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "保存 Markdown 文件", "", "Markdown 文件 (*.md);;所有文件 (*)"
        )
        if not path:
            return
        self._do_save(Path(path))

    def _do_save(self, path: Path):
        try:
            self._modified = False
            path.write_text(self.editor.toPlainText(), encoding="utf-8")
            self.current_file = path.resolve()
            self.setWindowTitle(f"MD 阅读器 — {self.current_file.name}")
            self._update_status()
            QMessageBox.information(self, "已保存", f"文件已保存：\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法保存文件：\n{e}")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # 深色主题调色板
    palette = QPalette()
    c = palette.ColorRole
    palette.setColor(c.Window,          QColor(30, 30, 46))
    palette.setColor(c.WindowText,      QColor(205, 214, 244))
    palette.setColor(c.Base,            QColor(25, 25, 40))
    palette.setColor(c.AlternateBase,   QColor(34, 34, 52))
    palette.setColor(c.Text,            QColor(205, 214, 244))
    palette.setColor(c.Button,          QColor(34, 34, 52))
    palette.setColor(c.ButtonText,      QColor(205, 214, 244))
    palette.setColor(c.Highlight,       QColor(137, 180, 250))
    palette.setColor(c.HighlightedText, QColor(30, 30, 46))
    palette.setColor(c.PlaceholderText, QColor(108, 112, 134))
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
