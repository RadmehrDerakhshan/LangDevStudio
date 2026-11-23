"""LangDev Studio — visual language builder.
Copyright (C) 2026 Radmehr Derakhshan.
"""
import json
import os
import random
import sys
import time
import traceback
from datetime import datetime

from PyQt6.QtCore import Qt, QRect, QSize, QTimer, QSettings, pyqtSignal
from PyQt6.QtGui import (QAction, QColor, QFont, QIcon, QKeySequence,
                         QPainter, QSyntaxHighlighter, QTextCharFormat,
                         QTextFormat)
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QDialog, QFileDialog, QFrame, QGridLayout,
    QHBoxLayout, QInputDialog, QLabel, QLineEdit, QListWidget,
    QMainWindow, QMessageBox, QPlainTextEdit, QPushButton, QScrollArea,
    QSplitter, QStackedWidget, QStatusBar, QTabWidget, QTextBrowser,
    QTextEdit, QVBoxLayout, QWidget
)

from engine import Language, compile_handlers, spec_to_python, LDSX_ENCODING


APP_NAME = "LangDev Studio"
VERSION  = "1.3.0"
AUTHOR   = "Radmehr Derakhshan"
YEAR     = "2026"


# --------------------------- engines ---------------------------
# You will probably build it.
ENGINES = ["Python", "C++", "JavaScript", "Rust"]

ENGINE_FILE = {
    "Python":     "engine.py",
    "C++":        "engine.hpp",
    "JavaScript": "engine.js",
    "Rust":       "engine.rs",
}


# --------------------------- settings file ---------------------------

def _config_dir():
    home = os.path.expanduser("~")
    path = os.path.join(home, ".langdevstudio")
    os.makedirs(path, exist_ok=True)
    return path


def load_recent():
    path = os.path.join(_config_dir(), "recent.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return [p for p in data if isinstance(p, str) and os.path.exists(p)]
    except Exception:
        pass
    return []


def save_recent(items):
    path = os.path.join(_config_dir(), "recent.json")
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


# --------------------------- themes ---------------------------

DARK = {
    "name": "dark",
    "BG_DEEP":   "#0f1216",
    "BG_PANEL":  "#161a20",
    "BG_EDITOR": "#0b0e12",
    "BG_HOVER":  "#1e242c",
    "BORDER":    "#232a33",
    "FG_TEXT":   "#cdd6e0",
    "FG_DIM":    "#6b7683",
    "ACCENT":    "#7aa2c8",
    "ACCENT_2":  "#9d7fb8",
    "ACCENT_3":  "#8fb996",
    "STR_COLOR": "#ff6b6b",
    "STR_BG":    "#2a1414",
    "LINE_NUM":  "#3a4250",
    "GUTTER":    "#0a0d10",
    "SUCCESS":   "#8fb996",
    "ERROR":     "#ff6b6b",
    "PY_KW":     "#c586c0",
    "PY_STR":    "#ce9178",
    "PY_CMT":    "#6a9955",
    "PY_NUM":    "#b5cea8",
    "PY_FN":     "#dcdcaa",
    "JSON_KEY":  "#79c0ff",
    "JSON_STR":  "#a5d6ff",
    "JSON_NUM":  "#b5cea8",
    "JSON_BOOL": "#ff79c6",
    "TERM_BG":   "#0c0c0c",
    "TERM_FG":   "#cccccc",
    "TERM_PROMPT": "#16c60c",
    "TERM_DIM":  "#767676",
    "CPP_KW":    "#569cd6",
    "CPP_STR":   "#ce9178",
    "CPP_CMT":   "#6a9955",
    "CPP_NUM":   "#b5cea8",
    "JS_KW":     "#c586c0",
    "JS_STR":    "#ce9178",
    "JS_CMT":    "#6a9955",
    "JS_NUM":    "#b5cea8",
    "RS_KW":     "#ff7b72",
    "RS_STR":    "#a5d6ff",
    "RS_CMT":    "#6a9955",
    "RS_NUM":    "#b5cea8",
}

LIGHT = {
    "name": "light",
    "BG_DEEP":   "#f5f6f8",
    "BG_PANEL":  "#eceef2",
    "BG_EDITOR": "#ffffff",
    "BG_HOVER":  "#e2e6ec",
    "BORDER":    "#c8cdd6",
    "FG_TEXT":   "#2a2f38",
    "FG_DIM":    "#7a8290",
    "ACCENT":    "#3a6ea5",
    "ACCENT_2":  "#7a4a9d",
    "ACCENT_3":  "#4a8a5c",
    "STR_COLOR": "#cc3333",
    "STR_BG":    "#ffe6e6",
    "LINE_NUM":  "#b0b6c0",
    "GUTTER":    "#f0f1f4",
    "SUCCESS":   "#4a8a5c",
    "ERROR":     "#cc3333",
    "PY_KW":     "#0000ff",
    "PY_STR":    "#a31515",
    "PY_CMT":    "#008000",
    "PY_NUM":    "#098658",
    "PY_FN":     "#795e26",
    "JSON_KEY":  "#0451a5",
    "JSON_STR":  "#a31515",
    "JSON_NUM":  "#098658",
    "JSON_BOOL": "#0000ff",
    "TERM_BG":   "#ffffff",
    "TERM_FG":   "#1f1f1f",
    "TERM_PROMPT": "#107c10",
    "TERM_DIM":  "#7a7a7a",
    "CPP_KW":    "#0000ff",
    "CPP_STR":   "#a31515",
    "CPP_CMT":   "#008000",
    "CPP_NUM":   "#098658",
    "JS_KW":     "#0000ff",
    "JS_STR":    "#a31515",
    "JS_CMT":    "#008000",
    "JS_NUM":    "#098658",
    "RS_KW":     "#0000ff",
    "RS_STR":    "#a31515",
    "RS_CMT":    "#008000",
    "RS_NUM":    "#098658",
}

DEFAULT_FONT = "Consolas"
DEFAULT_SIZE = 12


def build_qss(t):
    return f"""
QMainWindow, QWidget {{
    background: {t['BG_DEEP']};
    color: {t['FG_TEXT']};
    font-family: 'Segoe UI', sans-serif;
}}
QMenuBar {{
    background: {t['BG_PANEL']};
    color: {t['FG_TEXT']};
    border-bottom: 1px solid {t['BORDER']};
}}
QMenuBar::item {{ padding: 5px 12px; background: transparent; }}
QMenuBar::item:selected {{ background: {t['BG_HOVER']}; color: {t['ACCENT']}; }}
QMenu {{
    background: {t['BG_PANEL']};
    color: {t['FG_TEXT']};
    border: 1px solid {t['BORDER']};
    padding: 4px;
}}
QMenu::item {{ padding: 6px 26px 6px 20px; border-radius: 4px; }}
QMenu::item:selected {{ background: {t['BG_HOVER']}; color: {t['ACCENT']}; }}
QMenu::separator {{ height:1px; background:{t['BORDER']}; margin:4px 8px; }}
QTabWidget::pane {{ border: 1px solid {t['BORDER']}; background: {t['BG_PANEL']}; }}
QTabBar::tab {{
    background: {t['BG_DEEP']};
    color: {t['FG_DIM']};
    padding: 7px 16px;
    border: 1px solid {t['BORDER']};
    border-bottom: none;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background: {t['BG_PANEL']};
    color: {t['ACCENT']};
    border-bottom: 2px solid {t['ACCENT']};
}}
QTabBar::tab:hover {{ color: {t['FG_TEXT']}; }}
QListWidget {{
    background: {t['BG_EDITOR']};
    color: {t['FG_TEXT']};
    border: 1px solid {t['BORDER']};
    padding: 4px;
    outline: none;
}}
QListWidget::item {{ padding: 5px 8px; border-radius: 4px; }}
QListWidget::item:selected {{ background: {t['BG_HOVER']}; color: {t['ACCENT']}; }}
QListWidget::item:hover {{ background: {t['BG_HOVER']}; }}
QLineEdit {{
    background: {t['BG_EDITOR']};
    color: {t['FG_TEXT']};
    border: 1px solid {t['BORDER']};
    padding: 6px 8px;
    border-radius: 4px;
    selection-background-color: {t['ACCENT_2']};
}}
QLineEdit:focus {{ border: 1px solid {t['ACCENT']}; }}
QPlainTextEdit {{
    background: {t['BG_EDITOR']};
    color: {t['FG_TEXT']};
    border: 1px solid {t['BORDER']};
    selection-background-color: {t['ACCENT_2']};
    padding: 6px;
}}
QPlainTextEdit:focus {{ border: 1px solid {t['ACCENT']}; }}
QPushButton {{
    background: {t['BG_HOVER']};
    color: {t['FG_TEXT']};
    padding: 7px 14px;
    border: 1px solid {t['BORDER']};
    border-radius: 5px;
    font-weight: 600;
}}
QPushButton:hover {{ border: 1px solid {t['ACCENT']}; color: {t['ACCENT']}; }}
QPushButton:pressed {{ background: {t['BG_EDITOR']}; border: 1px solid {t['ACCENT_2']}; }}
QPushButton:disabled {{ background: {t['BG_DEEP']}; color: {t['FG_DIM']}; }}
QStatusBar {{
    background: {t['BG_PANEL']};
    color: {t['ACCENT']};
    border-top: 1px solid {t['BORDER']};
    font-family: 'Consolas', monospace;
}}
QLabel {{ color: {t['FG_DIM']}; }}
QTextBrowser {{
    background: {t['BG_DEEP']};
    color: {t['FG_TEXT']};
    border: none;
    padding: 14px;
    selection-background-color: {t['ACCENT_2']};
}}
QScrollBar:vertical {{ background: {t['BG_DEEP']}; width: 12px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {t['BORDER']}; min-height: 24px; border-radius: 6px; }}
QScrollBar::handle:vertical:hover {{ background: {t['ACCENT_2']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{ background: {t['BG_DEEP']}; height: 12px; margin: 0; }}
QScrollBar::handle:horizontal {{ background: {t['BORDER']}; min-width: 24px; border-radius: 6px; }}
QScrollBar::handle:horizontal:hover {{ background: {t['ACCENT_2']}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
QSplitter::handle {{ background: {t['BORDER']}; }}
QSplitter::handle:horizontal {{ width: 2px; }}
QSplitter::handle:vertical {{ height: 2px; }}
QMessageBox {{ background: {t['BG_PANEL']}; color: {t['FG_TEXT']}; }}
QMessageBox QPushButton {{ min-width: 70px; }}
QInputDialog {{ background: {t['BG_PANEL']}; color: {t['FG_TEXT']}; }}
QDialog {{ background: {t['BG_DEEP']}; color: {t['FG_TEXT']}; }}
QCheckBox {{ color: {t['FG_TEXT']}; spacing: 8px; }}
QScrollArea {{ background: transparent; border: none; }}
"""


EMPTY_SPEC = {
    "name": "Untitled",
    "engine": "Python",
    "tokens": [],
    "keywords": {},
    "funcs": {},
    "handlers": {},
}


# --------------------------- splash ---------------------------

class SplashScreen(QWidget):
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint |
                            Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(600, 340)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.container = QWidget()
        self.container.setObjectName("splash-container")
        self.container.setStyleSheet(f"""
            #splash-container {{
                background: {DARK['BG_DEEP']};
                border: 2px solid {DARK['BORDER']};
                border-radius: 16px;
            }}
        """)

        c = QVBoxLayout(self.container)
        c.setContentsMargins(40, 40, 40, 40)
        c.setSpacing(20)

        title = QLabel(APP_NAME)
        title.setStyleSheet(f"color: {DARK['ACCENT']}; font-size: 28px; font-weight: 700; letter-spacing: 2px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel(f"Visual Language Builder — v{VERSION}")
        subtitle.setStyleSheet(f"color: {DARK['FG_DIM']}; font-size: 13px; letter-spacing: 1px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.progress_bar = QFrame()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet(f"background: {DARK['BORDER']}; border-radius: 3px;")

        self.progress_fill = QFrame(self.progress_bar)
        self.progress_fill.setFixedHeight(6)
        self.progress_fill.setFixedWidth(0)
        self.progress_fill.setStyleSheet(f"background: {DARK['ACCENT']}; border-radius: 3px;")

        self.status_label = QLabel("Initializing...")
        self.status_label.setStyleSheet(f"color: {DARK['FG_DIM']}; font-size: 11px; font-family: 'Consolas', monospace;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        c.addStretch()
        c.addWidget(title)
        c.addWidget(subtitle)
        c.addSpacing(30)
        c.addWidget(self.progress_bar)
        c.addWidget(self.status_label)
        c.addStretch()

        layout.addWidget(self.container)
        self.center()

        self.progress_value = 0
        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self._update_progress)

        self._speed_ms = 30
        self._paused_until = 0

        self._messages = [
            "Initializing...",
            "Loading language definitions...",
            "Preparing editor...",
            "Loading themes...",
            "Warming up...",
            "Almost ready...",
            "Ready!",
        ]

    def center(self):
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - self.width()) // 2,
                  (screen.height() - self.height()) // 2)

    def _update_progress(self):
        if time.time() < self._paused_until:
            return

        self.progress_value += 1
        if self.progress_value > 100:
            self.progress_value = 100
        width = int(self.progress_bar.width() * (self.progress_value / 100))
        self.progress_fill.setFixedWidth(width)

        if self.progress_value < 15:
            self.status_label.setText(self._messages[0])
        elif self.progress_value < 35:
            self.status_label.setText(self._messages[1])
        elif self.progress_value < 55:
            self.status_label.setText(self._messages[2])
        elif self.progress_value < 70:
            self.status_label.setText(self._messages[3])
        elif self.progress_value < 85:
            self.status_label.setText(self._messages[4])
        elif self.progress_value < 100:
            self.status_label.setText(self._messages[5])
        else:
            self.status_label.setText(self._messages[6])
            self.progress_timer.stop()
            QTimer.singleShot(400, self.finished.emit)
            return

        r = random.random()
        if r < 0.10:
            self._paused_until = time.time() + random.uniform(0.15, 0.5)
        elif r < 0.30:
            self._speed_ms = random.randint(60, 90)
        else:
            self._speed_ms = random.randint(15, 35)

        self.progress_timer.start(self._speed_ms)

    def start(self):
        self.show()
        self.progress_timer.start(self._speed_ms)


# --------------------------- language highlighter (multi) ---------------------------

class LanguageHighlighter(QSyntaxHighlighter):
    def __init__(self, doc, theme):
        super().__init__(doc)
        self.theme = theme
        self.engine = "Python"
        self._apply()

    def _apply(self):
        t = self.theme
        self._fmts = {}

        def fmt(color, bold=False, italic=False):
            f = QTextCharFormat()
            f.setForeground(QColor(color))
            if bold:
                f.setFontWeight(QFont.Weight.Bold)
            if italic:
                f.setFontItalic(True)
            return f

        eng = self.engine
        if eng == "Python":
            self._kws = [
                "def", "class", "return", "if", "elif", "else", "while", "for",
                "in", "import", "from", "as", "try", "except", "finally", "with",
                "pass", "break", "continue", "raise", "lambda", "yield", "global",
                "nonlocal", "assert", "del", "is", "not", "and", "or", "True",
                "False", "None"
            ]
            self._f_kw = fmt(t["PY_KW"], bold=True)
            self._f_str = fmt(t["PY_STR"])
            self._f_cmt = fmt(t["PY_CMT"], italic=True)
            self._f_num = fmt(t["PY_NUM"])
        elif eng == "C++":
            self._kws = [
                "int", "float", "double", "char", "bool", "void", "class",
                "struct", "return", "if", "else", "while", "for", "do",
                "switch", "case", "break", "continue", "public", "private",
                "protected", "namespace", "using", "include", "const",
                "static", "new", "delete", "this", "true", "false", "nullptr",
                "auto", "template", "typename", "virtual", "override"
            ]
            self._f_kw = fmt(t["CPP_KW"], bold=True)
            self._f_str = fmt(t["CPP_STR"])
            self._f_cmt = fmt(t["CPP_CMT"], italic=True)
            self._f_num = fmt(t["CPP_NUM"])
        elif eng == "JavaScript":
            self._kws = [
                "function", "return", "if", "else", "while", "for", "do",
                "switch", "case", "break", "continue", "var", "let", "const",
                "class", "new", "this", "true", "false", "null", "undefined",
                "async", "await", "import", "export", "from", "typeof",
                "instanceof", "in", "of", "try", "catch", "finally", "throw"
            ]
            self._f_kw = fmt(t["JS_KW"], bold=True)
            self._f_str = fmt(t["JS_STR"])
            self._f_cmt = fmt(t["JS_CMT"], italic=True)
            self._f_num = fmt(t["JS_NUM"])
        elif eng == "Rust":
            self._kws = [
                "fn", "let", "mut", "const", "static", "struct", "enum",
                "trait", "impl", "for", "while", "loop", "if", "else",
                "match", "return", "break", "continue", "use", "mod", "pub",
                "crate", "self", "super", "true", "false", "as", "in",
                "where", "type", "move", "ref", "async", "await"
            ]
            self._f_kw = fmt(t["RS_KW"], bold=True)
            self._f_str = fmt(t["RS_STR"])
            self._f_cmt = fmt(t["RS_CMT"], italic=True)
            self._f_num = fmt(t["RS_NUM"])
        else:
            self._kws = []
            self._f_kw = fmt(t["FG_TEXT"])
            self._f_str = fmt(t["FG_TEXT"])
            self._f_cmt = fmt(t["FG_DIM"], italic=True)
            self._f_num = fmt(t["FG_TEXT"])

    def set_theme(self, theme):
        self.theme = theme
        self._apply()
        self.rehighlight()

    def set_engine(self, engine):
        self.engine = engine
        self._apply()
        self.rehighlight()

    def highlightBlock(self, text):
        import re
        comment_marker = "#" if self.engine == "Python" else "//"

        i = text.find(comment_marker)
        if i >= 0:
            self.setFormat(i, len(text) - i, self._f_cmt)

        for m in re.finditer(r'"[^"]*"|\'[^\']*\'', text):
            self.setFormat(m.start(), m.end() - m.start(), self._f_str)

        for kw in self._kws:
            for m in re.finditer(rf"\b{re.escape(kw)}\b", text):
                self.setFormat(m.start(), m.end() - m.start(), self._f_kw)

        for m in re.finditer(r"\b\d+(\.\d+)?\b", text):
            self.setFormat(m.start(), m.end() - m.start(), self._f_num)


# --------------------------- JSON highlighter ---------------------------

class JsonHighlighter(QSyntaxHighlighter):
    def __init__(self, doc, theme):
        super().__init__(doc)
        self.theme = theme
        self._apply()

    def _apply(self):
        t = self.theme
        self.key_fmt = QTextCharFormat()
        self.key_fmt.setForeground(QColor(t["JSON_KEY"]))
        self.key_fmt.setFontWeight(700)

        self.str_fmt = QTextCharFormat()
        self.str_fmt.setForeground(QColor(t["JSON_STR"]))

        self.num_fmt = QTextCharFormat()
        self.num_fmt.setForeground(QColor(t["JSON_NUM"]))

        self.bool_fmt = QTextCharFormat()
        self.bool_fmt.setForeground(QColor(t["JSON_BOOL"]))
        self.bool_fmt.setFontWeight(700)

    def set_theme(self, theme):
        self.theme = theme
        self._apply()
        self.rehighlight()

    def highlightBlock(self, text):
        import re
        for m in re.finditer(r'"([^"\\]|\\.)*"(?=\s*:)', text):
            self.setFormat(m.start(), m.end() - m.start(), self.key_fmt)
        for m in re.finditer(r'(?<=:\s)"([^"\\]|\\.)*"', text):
            self.setFormat(m.start(), m.end() - m.start(), self.str_fmt)
        for m in re.finditer(r'(?<=:\s)-?\d+(\.\d+)?', text):
            self.setFormat(m.start(), m.end() - m.start(), self.num_fmt)
        for m in re.finditer(r'(?<=:\s)(true|false|null)', text):
            self.setFormat(m.start(), m.end() - m.start(), self.bool_fmt)


# --------------------------- user language highlighter ---------------------------

class Highlighter(QSyntaxHighlighter):
    def __init__(self, doc, lang, theme):
        super().__init__(doc)
        self.lang = lang
        self.theme = theme
        self._apply()

    def _apply(self):
        t = self.theme
        self.kw  = QTextCharFormat(); self.kw.setForeground(QColor(t["ACCENT_2"])); self.kw.setFontWeight(700)
        self.num = QTextCharFormat(); self.num.setForeground(QColor(t["ACCENT_3"]))
        self.str = QTextCharFormat(); self.str.setForeground(QColor(t["STR_COLOR"]))
        self.str.setBackground(QColor(t["STR_BG"]))
        self.cmt = QTextCharFormat(); self.cmt.setForeground(QColor(t["FG_DIM"])); self.cmt.setFontItalic(True)
        self.op  = QTextCharFormat(); self.op.setForeground(QColor(t["ACCENT"]))

    def set_theme(self, theme):
        self.theme = theme
        self._apply()
        self.rehighlight()

    def highlightBlock(self, text):
        import re
        string_ranges = []
        for m in re.finditer(r'"[^"]*"|\'[^\']*\'', text):
            self.setFormat(m.start(), m.end() - m.start(), self.str)
            string_ranges.append((m.start(), m.end()))

        def in_string(pos):
            return any(a <= pos < b for a, b in string_ranges)

        for w in self.lang.spec.get("keywords", {}):
            for m in re.finditer(rf"\b{re.escape(w)}\b", text):
                if not in_string(m.start()):
                    self.setFormat(m.start(), m.end() - m.start(), self.kw)
        for m in re.finditer(r"\d+(\.\d+)?", text):
            if not in_string(m.start()):
                self.setFormat(m.start(), m.end() - m.start(), self.num)
        for m in re.finditer(r"[+\-*/=<>!&|%]+", text):
            if not in_string(m.start()):
                self.setFormat(m.start(), m.end() - m.start(), self.op)
        for m in re.finditer(r"#.*", text):
            self.setFormat(m.start(), m.end() - m.start(), self.cmt)


# --------------------------- handler dialog ---------------------------

class HandlerDialog(QDialog):
    def __init__(self, parent, keyword, engine, current_code):
        super().__init__(parent)
        self.setWindowTitle(f"{engine} Handler — {keyword}")
        self.resize(800, 600)
        self.setStyleSheet(parent.styleSheet())
        self.theme = parent.theme
        self.engine = engine

        self.editor = QPlainTextEdit()
        self.editor.setFont(QFont("Consolas", 12))
        self.editor.setPlainText(current_code)
        self.highlighter = LanguageHighlighter(self.editor.document(), self.theme)
        self.highlighter.set_engine(engine)

        ok = QPushButton("Save")
        ok.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme['ACCENT']};
                color: {self.theme['BG_DEEP']};
                font-weight: 700;
                padding: 8px 20px;
                border: none;
                border-radius: 5px;
            }}
            QPushButton:hover {{ background: {self.theme['ACCENT_2']}; }}
        """)
        ok.clicked.connect(self.accept)

        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)

        bottom = QHBoxLayout()
        bottom.addStretch()
        bottom.addWidget(cancel)
        bottom.addWidget(ok)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.addWidget(self.editor, 1)
        lay.addLayout(bottom)

    def get_code(self):
        return self.editor.toPlainText()


# --------------------------- manual LDSX editor ---------------------------

class LdsxEditorDialog(QDialog):
    def __init__(self, parent, current_json):
        super().__init__(parent)
        self.setWindowTitle("Edit .ldsx manually")
        self.resize(800, 600)
        self.setStyleSheet(parent.styleSheet())
        self.theme = parent.theme

        self.editor = QPlainTextEdit()
        self.editor.setFont(QFont("Consolas", 12))
        self.editor.setPlainText(current_json)
        self.highlighter = JsonHighlighter(self.editor.document(), self.theme)

        ok = QPushButton("OK")
        ok.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme['ACCENT']};
                color: {self.theme['BG_DEEP']};
                font-weight: 700;
                padding: 8px 20px;
                border: none;
                border-radius: 5px;
            }}
            QPushButton:hover {{ background: {self.theme['ACCENT_2']}; }}
        """)
        ok.clicked.connect(self.accept)

        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)

        bottom = QHBoxLayout()
        bottom.addStretch()
        bottom.addWidget(cancel)
        bottom.addWidget(ok)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.addWidget(self.editor, 1)
        lay.addLayout(bottom)

    def get_text(self):
        return self.editor.toPlainText()


# --------------------------- docs ---------------------------

DOCS_HTML = """
<html><body style="line-height: 1.6;">
<h1>LangDev Studio — Documentation</h1>
<p>Build your own programming language.</p>

<h2>New Project</h2>
<p>When you create a new project, you choose a <b>name</b> and an
<b>engine</b> (Python, C++, JavaScript, Rust). The engine determines
which handler is unlocked.</p>

<h2>Tokens</h2>
<ol>
<li>Open <b>Tokens</b>.</li>
<li>Fill Name and Regex.</li>
<li>Click <b>Add</b>.</li>
</ol>

<h2>Keywords</h2>
<ol>
<li>Open <b>Keywords</b>.</li>
<li>Fill Word.</li>
<li>Click <b>Add</b>.</li>
<li>Use the handler buttons to write the parser for the chosen engine.
Handlers of other engines are disabled.</li>
</ol>

<h2>Preview</h2>
<p>The <b>.ldsx JSON</b> panel shows the exact file that will be saved.
Click <b>Edit manually…</b> to modify it.</p>

<h2>Edit menu</h2>
<ul>
<li>Undo / Redo</li>
<li>Search in keywords, tokens, playground, handlers, LDSX</li>
</ul>
</body></html>
"""


class DocsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Documentation")
        self.resize(900, 700)
        view = QTextBrowser()
        view.setOpenExternalLinks(True)
        view.setHtml(DOCS_HTML)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(view)


# --------------------------- search widget ---------------------------

class SearchPanel(QWidget):
    closed = pyqtSignal()

    def __init__(self, placeholder, theme):
        super().__init__()
        self.theme = theme
        self._placeholder = placeholder

        self.input = QLineEdit()
        self.input.setPlaceholderText(placeholder)
        self.input.textChanged.connect(self._on_text)

        close_btn = QPushButton("✕")
        close_btn.setFixedWidth(36)
        close_btn.clicked.connect(self.closed.emit)

        self.results = QListWidget()
        self.results.itemDoubleClicked.connect(self._on_pick)

        top = QHBoxLayout()
        top.setContentsMargins(6, 6, 6, 0)
        top.addWidget(self.input)
        top.addWidget(close_btn)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addLayout(top)
        lay.addWidget(self.results, 1)

        self._on_pick_cb = None

    def _on_text(self, text):
        self._refresh(text)

    def _refresh(self, text):
        self.results.clear()
        if not text:
            return
        try:
            items = self._search_cb(text)
        except Exception:
            items = []
        for label, payload in items:
            it = QListWidget(label)
            it.setData(Qt.ItemDataRole.UserRole, payload)
            self.results.addItem(it)

    def set_search_callback(self, fn):
        self._search_cb = fn

    def set_pick_callback(self, fn):
        self._on_pick_cb = fn

    def _on_pick(self, item):
        if self._on_pick_cb:
            self._on_pick_cb(item.data(Qt.ItemDataRole.UserRole))

    def set_theme(self, theme):
        self.theme = theme


# --------------------------- tabs ---------------------------

class KeywordsTab(QWidget):
    def __init__(self, spec, on_change, theme, get_engine):
        super().__init__()
        self.spec = spec
        self.on_change = on_change
        self.theme = theme
        self.get_engine = get_engine

        self.list = QListWidget()
        self.list.currentItemChanged.connect(self.load_selected)

        self.word_edit = QLineEdit()
        self.word_edit.setPlaceholderText("keyword (e.g. print)")

        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_keyword)
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_selected)
        del_btn = QPushButton("Delete")
        del_btn.clicked.connect(self.delete_selected)

        # handler buttons (one per engine)
        self.handler_buttons = {}
        handlers_box = QHBoxLayout()
        handlers_box.setSpacing(4)
        for eng in ENGINES:
            b = QPushButton(eng)
            b.clicked.connect(lambda checked, e=eng: self.open_handler(e))
            handlers_box.addWidget(b)
            self.handler_buttons[eng] = b

        left = QVBoxLayout()
        left.addWidget(QLabel("Keywords"))
        left.addWidget(self.list)
        left.addWidget(QLabel("Word"))
        left.addWidget(self.word_edit)

        row = QHBoxLayout()
        row.addWidget(add_btn)
        row.addWidget(save_btn)
        row.addWidget(del_btn)
        left.addLayout(row)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {theme['BORDER']}; border: none;")
        left.addWidget(sep)

        left.addLayout(handlers_box)
        left.addStretch()

        lay = QHBoxLayout(self)
        lw = QWidget(); lw.setLayout(left)
        lay.addWidget(lw, 1)
        self.refresh()

    def set_theme(self, theme):
        self.theme = theme

    def refresh_engine_buttons(self):
        current = self.get_engine()
        for eng, btn in self.handler_buttons.items():
            btn.setEnabled(eng == current)
            btn.setToolTip(
                "" if eng == current
                else f"This project uses {current}. Only {current} handler is available."
            )

    def refresh(self):
        self.list.blockSignals(True)
        self.list.clear()
        for kw in self.spec["keywords"]:
            self.list.addItem(kw)
        self.list.blockSignals(False)
        self.refresh_engine_buttons()

    def load_selected(self, item):
        if not item:
            return
        kw = item.text()
        self.word_edit.setText(kw)

    def add_keyword(self):
        word = self.word_edit.text().strip()
        if not word:
            word = "NEW"
            idx = 1
            while word in self.spec["keywords"]:
                word = f"NEW_{idx}"
                idx += 1

        if word in self.spec["keywords"]:
            QMessageBox.warning(self, "Exists", f"'{word}' already exists.")
            return

        self.spec["keywords"][word] = word
        self.spec["funcs"][word] = "def run(i):\n    pass\n"
        self.spec.setdefault("handlers", {}).setdefault(word, {})[self.get_engine()] = "def run(i):\n    pass\n"
        self.refresh()
        self.on_change()

    def save_selected(self):
        item = self.list.currentItem()
        if not item:
            return
        old = item.text()
        new = self.word_edit.text().strip()
        if not new:
            return
        if new != old:
            if new in self.spec["keywords"]:
                QMessageBox.warning(self, "Exists", f"'{new}' already exists.")
                return
            self.spec["keywords"][new] = self.spec["keywords"].pop(old)
            self.spec["funcs"][new] = self.spec["funcs"].pop(old)
            h = self.spec.get("handlers", {})
            if old in h:
                h[new] = h.pop(old)
        self.refresh()
        self.on_change()

    def delete_selected(self):
        item = self.list.currentItem()
        if not item:
            return
        kw = item.text()
        self.spec["keywords"].pop(kw, None)
        self.spec["funcs"].pop(kw, None)
        self.spec.get("handlers", {}).pop(kw, None)
        self.refresh()
        self.on_change()

    def open_handler(self, engine):
        item = self.list.currentItem()
        if not item:
            QMessageBox.information(self, "Select", "Select a keyword first.")
            return
        if engine != self.get_engine():
            QMessageBox.warning(
                self, "Engine locked",
                f"This project uses {self.get_engine()}.\n"
                f"Only {self.get_engine()} handlers can be edited."
            )
            return

        kw = item.text()

        # load current code for this engine
        h = self.spec.get("handlers", {}).get(kw, {})
        current = h.get(engine, "")
        if not current:
            # migrate legacy `funcs`
            if engine == "Python":
                current = self.spec["funcs"].get(kw, "")
            else:
                current = "// run function stub\n"

        dlg = HandlerDialog(self.window(), kw, engine, current)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            code = dlg.get_code()
            self.spec.setdefault("handlers", {}).setdefault(kw, {})[engine] = code
            if engine == "Python":
                self.spec["funcs"][kw] = code
            self.on_change()


class TokensTab(QWidget):
    def __init__(self, spec, on_change, theme):
        super().__init__()
        self.spec = spec
        self.on_change = on_change
        self.theme = theme

        self.list = QListWidget()
        self.list.currentItemChanged.connect(self.load_selected)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("NAME")
        self.pattern_edit = QLineEdit()
        self.pattern_edit.setPlaceholderText(r"regex e.g. \d+")

        add = QPushButton("Add"); add.clicked.connect(self.add_token)
        save = QPushButton("Save"); save.clicked.connect(self.save_selected)
        dele = QPushButton("Delete"); dele.clicked.connect(self.delete_selected)

        form = QVBoxLayout()
        form.addWidget(QLabel("Tokens"))
        form.addWidget(self.list)
        form.addWidget(QLabel("Name"))
        form.addWidget(self.name_edit)
        form.addWidget(QLabel("Regex Pattern"))
        form.addWidget(self.pattern_edit)
        row = QHBoxLayout()
        row.addWidget(add); row.addWidget(save); row.addWidget(dele)
        form.addLayout(row)

        lw = QWidget(); lw.setLayout(form)

        lay = QHBoxLayout(self)
        lay.addWidget(lw, 1)
        self.refresh()

    def set_theme(self, theme):
        self.theme = theme

    def refresh(self):
        self.list.blockSignals(True)
        self.list.clear()
        for t in self.spec["tokens"]:
            self.list.addItem(f"{t['name']}  ->  {t['pattern']}")
        self.list.blockSignals(False)

    def load_selected(self, item):
        if not item:
            return
        idx = self.list.currentRow()
        if idx < 0 or idx >= len(self.spec["tokens"]):
            return
        t = self.spec["tokens"][idx]
        self.name_edit.setText(t["name"])
        self.pattern_edit.setText(t["pattern"])

    def add_token(self):
        name = self.name_edit.text().strip()
        pattern = self.pattern_edit.text().strip()
        if not name:
            name = "NEW"
            idx = 1
            while any(x["name"] == name for x in self.spec["tokens"]):
                name = f"NEW_{idx}"
                idx += 1
        if not pattern:
            pattern = r"\w+"
        self.spec["tokens"].append({"name": name, "pattern": pattern})
        self.refresh()
        self.on_change()

    def save_selected(self):
        idx = self.list.currentRow()
        if idx < 0 or idx >= len(self.spec["tokens"]):
            return
        name = self.name_edit.text().strip() or "NEW"
        pattern = self.pattern_edit.text().strip() or r"\w+"
        self.spec["tokens"][idx] = {"name": name, "pattern": pattern}
        self.refresh()
        self.on_change()

    def delete_selected(self):
        idx = self.list.currentRow()
        if idx < 0 or idx >= len(self.spec["tokens"]):
            return
        self.spec["tokens"].pop(idx)
        self.refresh()
        self.on_change()


# --------------------------- welcome ---------------------------

class ProjectButton(QPushButton):
    def __init__(self, name, path, theme):
        super().__init__()
        self.name = name
        self.path = path
        self.theme = theme
        self.setFixedSize(130, 130)
        self.setToolTip(path)
        self.setText(name)
        self._style()

    def _style(self):
        t = self.theme
        self.setStyleSheet(f"""
            QPushButton {{
                background: {t['BG_PANEL']};
                color: {t['FG_TEXT']};
                border: 2px solid {t['BORDER']};
                border-radius: 15px;
                font-size: 13px;
                font-weight: 700;
                padding: 10px;
            }}
            QPushButton:hover {{
                background: {t['BG_HOVER']};
                border: 2px solid {t['ACCENT']};
                color: {t['ACCENT']};
            }}
        """)


class NewProjectButton(QPushButton):
    def __init__(self, theme):
        super().__init__()
        self.theme = theme
        self.setFixedSize(130, 130)
        self.setText("+ New Project")
        self._style()

    def _style(self):
        t = self.theme
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {t['ACCENT']};
                border: 2px dashed {t['ACCENT']};
                border-radius: 15px;
                font-size: 13px;
                font-weight: 700;
                padding: 10px;
            }}
            QPushButton:hover {{
                background: {t['BG_HOVER']};
                border: 2px solid {t['ACCENT_2']};
                color: {t['ACCENT_2']};
            }}
        """)

# I did it out of respect for you.
class WelcomeScreen(QWidget):
    new_project = pyqtSignal()
    open_project = pyqtSignal()
    open_recent = pyqtSignal(str)

    def __init__(self, recent_projects, theme):
        super().__init__()
        self.recent_projects = recent_projects
        self.theme = theme

        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(0, 0, 0, 0)

        self._content = QWidget()
        self._outer.addWidget(self._content)

        self._build_content()

    def _build_content(self):
        t = self.theme

        old = self._outer.takeAt(0)
        if old and old.widget():
            old.widget().deleteLater()

        self._content = QWidget()
        self._outer.addWidget(self._content)

        lay = QVBoxLayout(self._content)
        lay.setContentsMargins(60, 50, 60, 50)
        lay.setSpacing(24)

        title = QLabel(f"Welcome to {APP_NAME}")
        title.setStyleSheet(f"color: {t['ACCENT']}; font-size: 36px; font-weight: 800; letter-spacing: 1px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sub = QLabel("Build your own programming language — no code required for the basics.")
        sub.setStyleSheet(f"color: {t['FG_DIM']}; font-size: 14px;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lay.addWidget(title)
        lay.addWidget(sub)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(20)

        new_btn = QPushButton("New Project")
        new_btn.setFixedHeight(50)
        new_btn.setStyleSheet(f"""
            QPushButton {{
                background: {t['ACCENT']}; color: {t['BG_DEEP']};
                font-size: 16px; font-weight: 700;
                border: none; border-radius: 10px;
                padding: 10px 30px;
            }}
            QPushButton:hover {{ background: {t['ACCENT_2']}; }}
        """)
        new_btn.clicked.connect(self.new_project.emit)

        open_btn = QPushButton("Open Project")
        open_btn.setFixedHeight(50)
        open_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {t['FG_TEXT']};
                font-size: 16px; font-weight: 700;
                border: 2px solid {t['BORDER']}; border-radius: 10px;
                padding: 10px 30px;
            }}
            QPushButton:hover {{ border: 2px solid {t['ACCENT']}; color: {t['ACCENT']}; }}
        """)
        open_btn.clicked.connect(self.open_project.emit)

        btn_row.addStretch()
        btn_row.addWidget(new_btn)
        btn_row.addWidget(open_btn)
        btn_row.addStretch()
        lay.addLayout(btn_row)
        lay.addSpacing(20)

        recent_title = QLabel("Recent Projects")
        recent_title.setStyleSheet(f"color: {t['FG_TEXT']}; font-size: 18px; font-weight: 700; padding-bottom: 6px;")
        lay.addWidget(recent_title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        grid = QGridLayout(content)
        grid.setSpacing(20)

        new_tile = NewProjectButton(t)
        new_tile.clicked.connect(self.new_project.emit)
        grid.addWidget(new_tile, 0, 0)

        for idx, path in enumerate(self.recent_projects):
            name = os.path.splitext(os.path.basename(path))[0]
            btn = ProjectButton(name, path, t)
            btn.clicked.connect(lambda checked, p=path: self.open_recent.emit(p))
            i = idx + 1
            grid.addWidget(btn, i // 8, i % 8)

        grid.setRowStretch(grid.rowCount(), 1)
        grid.setColumnStretch(8, 1)

        scroll.setWidget(content)
        lay.addWidget(scroll, 1)

        if not self.recent_projects:
            hint = QLabel("No recent projects yet — start by creating a new one.")
            hint.setStyleSheet(f"color: {t['FG_DIM']}; font-size: 12px; padding-top: 6px;")
            hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(hint)

    def set_theme(self, theme):
        self.theme = theme
        self._build_content()


# --------------------------- run dialog ---------------------------

class RunResultDialog(QDialog):
    def __init__(self, parent, success, elapsed, log_text):
        super().__init__(parent)
        self.setWindowTitle("Run result")
        self.resize(620, 480)
        self.setStyleSheet(parent.styleSheet())

        t = parent.theme
        title = "Executed successfully" if success else "Execution failed"
        color = t["SUCCESS"] if success else t["ERROR"]

        header = QLabel(title)
        header.setStyleSheet(
            f"color: {color}; font-size: 16px; font-weight: 700; "
            f"padding: 12px 16px; background: {t['BG_PANEL']}; "
            f"border-bottom: 1px solid {t['BORDER']};"
        )

        info = QLabel(f"Completed in {elapsed:.3f} s")
        info.setStyleSheet(
            f"color: {t['FG_DIM']}; padding: 8px 16px; "
            f"background: {t['BG_PANEL']}; font-family: Consolas;"
        )

        log = QPlainTextEdit()
        log.setReadOnly(True)
        log.setPlainText(log_text)
        log.setFont(QFont("Consolas", 11))
        log.setStyleSheet(
            f"background: {t['BG_EDITOR']}; color: {t['FG_TEXT']}; "
            f"border: 1px solid {t['BORDER']}; border-radius: 4px; margin: 8px;"
        )

        self.dont_show = QCheckBox("Don't show this dialog again")
        self.dont_show.setStyleSheet(f"color: {t['FG_DIM']}; padding: 4px 8px;")

        close = QPushButton("Close")
        close.clicked.connect(self.accept)

        bottom = QHBoxLayout()
        bottom.addWidget(self.dont_show)
        bottom.addStretch()
        bottom.addWidget(close)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(header)
        lay.addWidget(info)
        lay.addWidget(log, 1)
        wrapper = QWidget()
        wrapper.setLayout(bottom)
        wrapper.setStyleSheet(f"background: {t['BG_PANEL']};")
        lay.addWidget(wrapper)


# --------------------------- main studio ---------------------------

class Studio(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)

        self.theme = DARK
        self.font_name = DEFAULT_FONT
        self.font_size = DEFAULT_SIZE
        self.show_run_dialog = True
        self.is_dirty = False
        self.recent_projects = load_recent()

        self.settings = QSettings("Radmehr", "LangDevStudio")
        self._load_settings()

        self.spec = json.loads(json.dumps(EMPTY_SPEC))
        self.current_path = None
        self.lang = Language(self.spec)
        self.lang.bind(compile_handlers(self.lang))

        self.welcome = WelcomeScreen(self.recent_projects, self.theme)
        self.welcome.new_project.connect(self.new_project)
        self.welcome.open_project.connect(self.open_project)
        self.welcome.open_recent.connect(self.load_path)

        self.editor_view = self._build_editor_view()

        self.main_stack = QStackedWidget()
        self.main_stack.addWidget(self.welcome)
        self.main_stack.addWidget(self.editor_view)
        self.setCentralWidget(self.main_stack)

        self._build_menu()
        self.setStatusBar(QStatusBar())
        self._apply_font()
        self._apply_theme()
        self._update_title()
        self.statusBar().showMessage(f"{APP_NAME} {VERSION} ready")

    # -------- editor view --------

    def _build_editor_view(self):
        self.tabs = QTabWidget()
        self.kw_tab = KeywordsTab(self.spec, self.rebuild, self.theme,
                                   lambda: self.spec.get("engine", "Python"))
        self.tk_tab = TokensTab(self.spec, self.rebuild, self.theme)
        self.tabs.addTab(self.tk_tab, "Tokens")
        self.tabs.addTab(self.kw_tab, "Keywords")

        # preview
        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setFont(QFont("Consolas", 11))
        self.json_hl = JsonHighlighter(self.preview.document(), self.theme)

        edit_ldsx_btn = QPushButton("Edit manually…")
        edit_ldsx_btn.clicked.connect(self.edit_ldsx_manually)

        preview_box = QWidget()
        pv = QVBoxLayout(preview_box)
        pv.setContentsMargins(0, 0, 0, 0)
        pv.setSpacing(4)
        pv.addWidget(self.preview, 1)
        pv.addWidget(edit_ldsx_btn)

        # playground
        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("Write a program in your language here…")
        self.editor.textChanged.connect(self.mark_dirty)
        self.hl = Highlighter(self.editor.document(), self.lang, self.theme)

        # output
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setFont(QFont("Consolas", 11))
        self._update_output_style()

        # left side
        self.left_stack = QStackedWidget()
        builder = QWidget()
        bl = QHBoxLayout(builder)
        bl.setContentsMargins(0, 0, 0, 0)
        left_split = QSplitter(Qt.Orientation.Horizontal)
        left_split.addWidget(self._card("Language Builder", self.tabs))
        left_split.addWidget(self._card("Preview (.ldsx JSON)", preview_box))
        left_split.setSizes([500, 400])
        bl.addWidget(left_split)

        # search panels
        self.search_panels = {}
        for key in ("keywords", "tokens", "playground", "handlers", "ldsx"):
            p = SearchPanel(f"Search in {key}…", self.theme)
            self.search_panels[key] = p
            p.closed.connect(self._close_search)
            self.left_stack.addWidget(p)

        self.left_stack.addWidget(builder)
        self._builder_index = self.left_stack.count() - 1
        self.left_stack.setCurrentIndex(self._builder_index)

        right = QSplitter(Qt.Orientation.Vertical)
        right.addWidget(self._card("Playground", self.editor))
        right.addWidget(self._card("Output", self.output))
        right.setSizes([460, 240])

        main = QSplitter(Qt.Orientation.Horizontal)
        main.addWidget(self.left_stack)
        main.addWidget(right)
        main.setSizes([900, 720])
        return main

    def _card(self, title, widget):
        box = QFrame()
        lay = QVBoxLayout(box)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        lbl = QLabel(title)
        lbl.setObjectName("card-title")
        self._style_card_title(lbl)

        lay.addWidget(lbl)
        lay.addWidget(widget)
        return box

    def _style_card_title(self, lbl):
        t = self.theme
        lbl.setStyleSheet(
            f"background: {t['BG_PANEL']}; color: {t['ACCENT']}; "
            f"padding: 8px 12px; font-weight: 700; font-size: 12px; "
            f"letter-spacing: 1px;"
        )

    def _update_output_style(self):
        t = self.theme
        self.output.setStyleSheet(
            f"background: {t['TERM_BG']}; color: {t['TERM_FG']}; "
            f"border: 1px solid {t['BORDER']}; "
            f"font-family: 'Consolas', 'Courier New', monospace;"
        )

    # -------- menu --------

    def _act(self, menu, text, shortcut, slot):
        a = QAction(text, self)
        if shortcut:
            a.setShortcut(QKeySequence(shortcut))
        a.triggered.connect(slot)
        menu.addAction(a)
        return a

    def _build_menu(self):
        mb = self.menuBar()

        f = mb.addMenu("&File")
        self._act(f, "New Project", "Ctrl+N", self.new_project)
        self._act(f, "Open Project…", "Ctrl+O", self.open_project)
        self._act(f, "Save Project", "Ctrl+S", self.save_project)
        self._act(f, "Save Project As…", "Ctrl+Shift+S", self.save_project_as)
        f.addSeparator()
        self.recent_menu = f.addMenu("Recent Projects")
        self._populate_recent_menu()
        f.addSeparator()

        export_menu = f.addMenu("Export")
        self._act(export_menu, "Export Python…", "Ctrl+E+P", self.export_py)
        self._act(export_menu, "Export C++…", "Ctrl+E+C", self.export_cpp)
        self._act(export_menu, "Export JavaScript…", "Ctrl+E+J", self.export_js)
        self._act(export_menu, "Export Rust…", "Ctrl+E+R", self.export_rs)

        f.addSeparator()
        self._act(f, "Back to Welcome", "Ctrl+W", self.back_to_welcome)
        f.addSeparator()
        self._act(f, "Quit", "Ctrl+Q", self.close)

        # ---- Edit menu ----
        e = mb.addMenu("&Edit")
        self._act(e, "Undo", "Ctrl+Z", self._undo)
        self._act(e, "Redo", "Ctrl+Y", self._redo)
        e.addSeparator()
        self._act(e, "Search in keywords", "Ctrl+Shift+K", lambda: self.open_search("keywords"))
        self._act(e, "Search in tokens", "Ctrl+Shift+T", lambda: self.open_search("tokens"))
        self._act(e, "Search in playground", "Ctrl+Shift+P", lambda: self.open_search("playground"))
        self._act(e, "Search in handlers", "Ctrl+Shift+H", lambda: self.open_search("handlers"))
        self._act(e, "Search in LDSX", "Ctrl+Shift+L", lambda: self.open_search("ldsx"))

        r = mb.addMenu("&Run")
        self._act(r, "Run", "Ctrl+R", self.run_code)
        self._act(r, "Clear Output", "Ctrl+L", self.output_clear)

        s = mb.addMenu("&Settings")
        self._act(s, "Font…", "Ctrl+Shift+F", self.change_font)
        self._act(s, "Toggle Theme", "Ctrl+T", self.toggle_theme)

        h = mb.addMenu("&Help")
        self._act(h, "Documentation", "F1", self.show_docs)
        self._act(h, "About", None, self.show_about)

    def _populate_recent_menu(self):
        self.recent_menu.clear()
        if not self.recent_projects:
            act = QAction("(No recent projects)", self)
            act.setEnabled(False)
            self.recent_menu.addAction(act)
        else:
            for path in self.recent_projects:
                act = QAction(os.path.basename(path), self)
                act.triggered.connect(lambda checked, p=path: self.load_path(p))
                self.recent_menu.addAction(act)

    def output_clear(self):
        self.output.clear()

    # -------- undo / redo --------

    def _undo(self):
        w = QApplication.focusWidget()
        if isinstance(w, QPlainTextEdit):
            w.undo()

    def _redo(self):
        w = QApplication.focusWidget()
        if isinstance(w, QPlainTextEdit):
            w.redo()

    # -------- search --------

    def open_search(self, kind):
        self.left_stack.setCurrentWidget(self.search_panels[kind])
        panel = self.search_panels[kind]

        if kind == "keywords":
            panel.set_search_callback(self._search_keywords)
            panel.set_pick_callback(self._pick_keyword)
        elif kind == "tokens":
            panel.set_search_callback(self._search_tokens)
            panel.set_pick_callback(self._pick_token)
        elif kind == "playground":
            panel.set_search_callback(self._search_playground)
            panel.set_pick_callback(self._pick_playground)
        elif kind == "handlers":
            panel.set_search_callback(self._search_handlers)
            panel.set_pick_callback(self._pick_handler)
        elif kind == "ldsx":
            panel.set_search_callback(self._search_ldsx)
            panel.set_pick_callback(self._pick_ldsx)

        panel.input.setFocus()

    def _close_search(self):
        self.left_stack.setCurrentIndex(self._builder_index)

    def _search_keywords(self, text):
        t = text.lower()
        return [(kw, kw) for kw in self.spec["keywords"] if t in kw.lower()]

    def _pick_keyword(self, kw):
        self.tabs.setCurrentWidget(self.kw_tab)
        for i in range(self.kw_tab.list.count()):
            if self.kw_tab.list.item(i).text() == kw:
                self.kw_tab.list.setCurrentRow(i)
                break
        self._close_search()

    def _search_tokens(self, text):
        t = text.lower()
        return [(tk["name"], tk["name"]) for tk in self.spec["tokens"] if t in tk["name"].lower()]

    def _pick_token(self, name):
        self.tabs.setCurrentWidget(self.tk_tab)
        for i in range(self.tk_tab.list.count()):
            if self.tk_tab.list.item(i).text().startswith(name):
                self.tk_tab.list.setCurrentRow(i)
                break
        self._close_search()

    def _search_playground(self, text):
        code = self.editor.toPlainText()
        results = []
        pos = 0
        while True:
            pos = code.lower().find(text.lower(), pos)
            if pos == -1:
                break
            line = code.count("\n", 0, pos) + 1
            snippet = code.splitlines()[line - 1] if line <= code.count("\n") + 1 else ""
            results.append((f"Line {line}: {snippet.strip()}", (pos, len(text))))
            pos += len(text)
        return results

    def _pick_playground(self, payload):
        pos, length = payload
        cursor = self.editor.textCursor()
        cursor.setPosition(pos)
        cursor.setPosition(pos + length, cursor.MoveMode.KeepAnchor)
        self.editor.setTextCursor(cursor)
        self.editor.setFocus()
        self._close_search()

    def _search_handlers(self, text):
        t = text.lower()
        results = []
        for kw, hmap in self.spec.get("handlers", {}).items():
            if t in kw.lower():
                for eng, code in hmap.items():
                    results.append((f"{kw} [{eng}]", (kw, eng)))
        return results

    def _pick_handler(self, payload):
        kw, eng = payload
        self.tabs.setCurrentWidget(self.kw_tab)
        for i in range(self.kw_tab.list.count()):
            if self.kw_tab.list.item(i).text() == kw:
                self.kw_tab.list.setCurrentRow(i)
                break
        self._close_search()

    def _search_ldsx(self, text):
        try:
            raw = json.dumps(self.spec, indent=2, ensure_ascii=False)
        except Exception:
            raw = "{}"
        results = []
        pos = 0
        while True:
            pos = raw.lower().find(text.lower(), pos)
            if pos == -1:
                break
            line = raw.count("\n", 0, pos) + 1
            results.append((f"Line {line}", pos))
            pos += len(text)
        return results

    def _pick_ldsx(self, pos):
        cursor = self.preview.textCursor()
        cursor.setPosition(min(pos, len(self.preview.toPlainText())))
        self.preview.setTextCursor(cursor)
        self._close_search()

    # -------- preview refresh --------

    def refresh_preview(self):
        try:
            text = json.dumps(self.spec, indent=2, ensure_ascii=False)
        except Exception:
            text = "{}"
        self.preview.setPlainText(text)
        self.json_hl.rehighlight()

    def edit_ldsx_manually(self):
        try:
            raw = json.dumps(self.spec, indent=2, ensure_ascii=False)
        except Exception:
            raw = "{}"
        dlg = LdsxEditorDialog(self, raw)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                new_spec = json.loads(dlg.get_text())
            except Exception as e:
                QMessageBox.critical(self, "Invalid JSON", str(e))
                return
            self.spec.clear()
            self.spec.update(new_spec)
            self.spec.setdefault("engine", "Python")
            self.spec.setdefault("handlers", {})
            self.kw_tab.refresh()
            self.tk_tab.refresh()
            self.rebuild()

    # -------- rebuild --------

    def rebuild(self):
        self.lang = Language(self.spec)
        self.lang.bind(compile_handlers(self.lang))
        self.hl.lang = self.lang
        self.hl.rehighlight()
        self.refresh_preview()
        self.kw_tab.refresh_engine_buttons()
        self.mark_dirty()
        self.statusBar().showMessage(
            f"engine={self.spec.get('engine','?')}  "
            f"tokens={len(self.spec['tokens'])}  "
            f"keywords={len(self.spec['keywords'])}"
        )

    # -------- dirty --------

    def mark_dirty(self, *args, **kwargs):
        if not self.is_dirty:
            self.is_dirty = True
            self._update_title()

    def mark_clean(self):
        self.is_dirty = False
        self._update_title()

    def _update_title(self):
        path = self.current_path or APP_NAME
        star = " *" if self.is_dirty else ""
        self.setWindowTitle(f"{path}{star}")

    def closeEvent(self, event):
        if not self.is_dirty:
            event.accept()
            return

        reply = QMessageBox.question(
            self, "Unsaved changes",
            "You have unsaved changes. Save before closing?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )

        if reply == QMessageBox.StandardButton.Save:
            self.save_project()
            if self.is_dirty:
                event.ignore()
            else:
                event.accept()
        elif reply == QMessageBox.StandardButton.Discard:
            event.accept()
        else:
            event.ignore()

    # -------- font & theme --------

    def _apply_font(self):
        code_font = QFont(self.font_name, self.font_size)
        code_font.setStyleHint(QFont.StyleHint.Monospace)
        self.editor.setFont(code_font)
        self.output.setFont(QFont(self.font_name, max(9, self.font_size - 1)))
        self.preview.setFont(QFont(self.font_name, max(9, self.font_size - 1)))

    def _apply_theme(self):
        t = self.theme
        QApplication.instance().setStyleSheet(build_qss(t))
        self.hl.set_theme(t)
        self.json_hl.set_theme(t)
        self.welcome.set_theme(t)
        self._update_output_style()
        for w in self.findChildren(QLabel):
            if w.objectName() == "card-title":
                self._style_card_title(w)

    def change_font(self):
        name, ok = QInputDialog.getText(
            self, "Font",
            "Font name (e.g. Consolas, JetBrains Mono):",
            text=self.font_name,
        )
        if not ok or not name.strip():
            return
        name = name.strip()

        size, ok = QInputDialog.getInt(
            self, "Font size", "Size:",
            value=self.font_size, min=8, max=48,
        )
        if not ok:
            return

        self.font_name = name
        self.font_size = int(size)
        self._apply_font()
        self._save_settings()
        self.statusBar().showMessage(f"Font: {name} {size}")

    def toggle_theme(self):
        self.theme = LIGHT if self.theme["name"] == "dark" else DARK
        self._apply_theme()
        self._save_settings()
        self.statusBar().showMessage(f"Theme: {self.theme['name']}")

    # -------- project --------

    def new_project(self):
        # ask name
        name, ok = QInputDialog.getText(
            self, "New Project", "Language name:"
        )
        if not ok or not name.strip():
            return
        name = name.strip()

        # ask engine
        engine, ok = QInputDialog.getItem(
            self, "New Project", "Engine:",
            ENGINES, 0, False,
        )
        if not ok:
            return

        self.spec.clear()
        self.spec.update(json.loads(json.dumps(EMPTY_SPEC)))
        self.spec["name"] = name
        self.spec["engine"] = engine

        self.kw_tab.refresh()
        self.tk_tab.refresh()
        self.editor.blockSignals(True)
        self.editor.clear()
        self.editor.blockSignals(False)
        self.output.clear()
        self.current_path = None
        self.lang = Language(self.spec)
        self.lang.bind(compile_handlers(self.lang))
        self.hl.lang = self.lang
        self.hl.rehighlight()
        self.refresh_preview()
        self.mark_clean()
        self._show_editor()

    def open_project(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open", "", "LangDev Studio (*.ldsx);;All files (*)"
        )
        if path:
            self.load_path(path)

    def load_path(self, path):
        try:
            with open(path, "r", encoding=LDSX_ENCODING) as f:
                data = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Open failed", str(e))
            return

        self.spec.clear()
        # Magical JSON!
        self.spec.update({
            "name": data.get("name", "Untitled"),
            "engine": data.get("engine", "Python"),
            "tokens": data.get("tokens", []),
            "keywords": data.get("keywords", {}),
            "funcs": data.get("funcs", {}),
            "handlers": data.get("handlers", {}),
        })
        self.kw_tab.refresh()
        self.tk_tab.refresh()
        self.current_path = path
        self.lang = Language(self.spec)
        self.lang.bind(compile_handlers(self.lang))
        self.hl.lang = self.lang
        self.hl.rehighlight()
        self.refresh_preview()
        self.mark_clean()
        self._add_recent(path)
        self._show_editor()

    def _add_recent(self, path):
        path = os.path.abspath(path)
        if path in self.recent_projects:
            self.recent_projects.remove(path)
        self.recent_projects.insert(0, path)
        self.recent_projects = self.recent_projects[:16]
        save_recent(self.recent_projects)
        self._populate_recent_menu()

    def _write_project(self, path):
        with open(path, "w", encoding=LDSX_ENCODING) as f:
            json.dump(self.spec, f, indent=2, ensure_ascii=False)
        self.current_path = path
        self.mark_clean()
        self._add_recent(path)
        self.statusBar().showMessage(f"Saved {path}")

    def save_project(self):
        if self.current_path:
            try:
                self._write_project(self.current_path)
            except Exception as e:
                QMessageBox.critical(self, "Save failed", str(e))
            return
        self.save_project_as()

    def save_project_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save", "", "LangDev Studio (*.ldsx);;All files (*)"
        )
        if not path:
            return
        if not path.endswith(".ldsx"):
            path += ".ldsx"
        try:
            self._write_project(path)
        except Exception as e:
            QMessageBox.critical(self, "Save failed", str(e))

    # -------- export --------

    def export_py(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Python Module", "", "Python (*.py);;All files (*)"
        )
        if not path:
            return
        if not path.endswith(".py"):
            path += ".py"
        try:
            code = spec_to_python(self.spec,
                                  module_name=self.spec.get("name", "my_lang"))
            with open(path, "w", encoding="utf-8") as f:
                f.write(code)
        except Exception as e:
            QMessageBox.critical(self, "Export failed", str(e))
            return
        self.statusBar().showMessage(f"Exported {path}")

    def export_cpp(self):
        self._export_other("C++", "engine.hpp")

    def export_js(self):
        self._export_other("JavaScript", "engine.js")

    def export_rs(self):
        self._export_other("Rust", "engine.rs")

    def _export_other(self, engine, filename):
        # writes the raw spec so it can be fed to engine.<ext>
        path, _ = QFileDialog.getSaveFileName(
            self, f"Export {engine} spec", filename,
            f"{engine} (*{os.path.splitext(filename)[1]});;All files (*)"
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.spec, f, indent=2, ensure_ascii=False)
        except Exception as e:
            QMessageBox.critical(self, "Export failed", str(e))
            return
        self.statusBar().showMessage(f"Exported {path}")

    def back_to_welcome(self):
        if self.is_dirty:
            reply = QMessageBox.question(
                self, "Unsaved changes",
                "You have unsaved changes. Save before going back?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save,
            )
            if reply == QMessageBox.StandardButton.Save:
                self.save_project()
                if self.is_dirty:
                    return
            elif reply == QMessageBox.StandardButton.Cancel:
                return
        self._show_welcome()

    def _show_welcome(self):
        self.welcome.recent_projects = self.recent_projects
        self.welcome.set_theme(self.theme)
        self.main_stack.setCurrentWidget(self.welcome)

    def _show_editor(self):
        self.main_stack.setCurrentWidget(self.editor_view)

    # -------- run --------

    def _term_write(self, text):
        self.output.appendPlainText(text)
        max_lines = 500
        doc = self.output.document()
        if doc.blockCount() > max_lines:
            cursor = self.output.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.movePosition(cursor.MoveOperation.Down,
                                cursor.MoveMode.KeepAnchor,
                                doc.blockCount() - max_lines)
            cursor.removeSelectedText()
            cursor.deleteChar()

    def run_code(self):
        if self.spec.get("engine", "Python") != "Python":
            QMessageBox.information(
                self, "Engine not available",
                f"This project uses {self.spec.get('engine')}.\n"
                f"Running is only available for Python right now."
            )
            return

        timestamp = datetime.now().strftime("%H:%M:%S")
        code = self.editor.toPlainText()

        self._term_write("engine initialize...")
        self._term_write(f"[{timestamp}] running...")

        self.lang._out = lambda *args: self._term_write(" ".join(str(a) for a in args))

        start = time.perf_counter()
        success = True
        error_log = ""

        try:
            self.lang.env = {}
            for s in self.lang.parse(self.lang.lex(code)):
                s(self.lang)
            self.statusBar().showMessage("OK")
        except Exception as e:
            success = False
            error_log = traceback.format_exc()
            self._term_write(f"{type(e).__name__}: {e}")
            self.statusBar().showMessage("Error")

        elapsed = time.perf_counter() - start

        if success:
            self._term_write(f"[{timestamp}] done in {elapsed*1000:.1f} ms")
        else:
            self._term_write(f"[{timestamp}] failed in {elapsed*1000:.1f} ms")
        self._term_write("")

        if not self.show_run_dialog:
            return
        log_lines = [
            "--- Execution log ---",
            f"Status: {'OK' if success else 'FAILED'}",
            f"Elapsed: {elapsed:.4f} s",
            "",
        ]
        log_lines.append("No errors." if success else error_log)

        # TODO: nothing to do
        dlg = RunResultDialog(self, success, elapsed, "\n".join(log_lines))
        dlg.exec()
        if dlg.dont_show.isChecked():
            self.show_run_dialog = False
            self.statusBar().showMessage("Run dialog disabled")

    # -------- settings --------

    def _load_settings(self):
        self.recent_projects = load_recent()
        theme_name = self.settings.value("theme", "dark")
        self.theme = DARK if theme_name == "dark" else LIGHT
        self.font_name = self.settings.value("font", DEFAULT_FONT)
        self.font_size = int(self.settings.value("size", DEFAULT_SIZE))

    def _save_settings(self):
        save_recent(self.recent_projects)
        self.settings.setValue("theme", self.theme["name"])
        self.settings.setValue("font", self.font_name)
        self.settings.setValue("size", self.font_size)

    # -------- help --------

    def show_docs(self):
        DocsWindow(self).exec()

    def show_about(self):
        QMessageBox.about(
            self, f"About {APP_NAME}",
            f"<b>{APP_NAME}</b> {VERSION}<br><br>"
            f"Visual builder for small languages.<br>"
            f"Define tokens and keywords; Python only when needed.<br><br>"
            f"© {YEAR} {AUTHOR}"
        )


# --------------------------- entry point ---------------------------

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(build_qss(DARK))

    splash = SplashScreen()
    splash.start()

    studio = Studio()

    def on_loaded():
        studio.setWindowIcon(QIcon("LangDevStudio.ico"))
        studio.showMaximized()
        splash.close()

    splash.finished.connect(on_loaded)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

# My motto: the fewest possible file
# long live `main.py`!
# Sorry if some of the words are incorrect. My English isn't very good.