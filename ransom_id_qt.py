#!/usr/bin/env python3
"""
Emsys Anti-Ransomware Identifier - Modern Qt GUI
A stylish, modern interface for identifying ransomware types.
"""

import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QTabWidget, QTextEdit,
    QFileDialog, QProgressBar, QFrame, QMessageBox, QToolButton
)
from PySide6.QtCore import Qt, QSize, QTimer, QThread, Signal
from PySide6.QtGui import QFont, QIcon, QColor, QPainter, QLinearGradient, QBrush
import re
from collections import defaultdict

# Import core analysis functions
sys.path.insert(0, os.path.dirname(__file__))
try:
    from ransom_id import analyze_extension, analyze_ransom_note, check_file_magic
except ImportError:
    def analyze_extension(filename):
        return None
    def analyze_ransom_note(filepath):
        return []
    def check_file_magic(filepath):
        return None

# Emsys Brand Colors
EMSYS_TEAL = "#30b090"
EMSYS_DARK_TEAL = "#278a74"
EMSYS_LIGHT_TEAL = "#e8f8f5"
BG_DARK = "#1a1d21"
BG_CARD = "#23272c"
BG_INPUT = "#2c3036"
TEXT_PRIMARY = "#ffffff"
TEXT_SECONDARY = "#a0aab4"
TEXT_MUTED = "#6b7280"
BORDER_COLOR = "#373d44"
SUCCESS_GREEN = "#27ae60"
WARNING_ORANGE = "#f39c12"
DANGER_RED = "#e74c3c"


class ModernButton(QPushButton):
    """Custom styled modern button."""
    
    def __init__(self, text, primary=False, icon=None, parent=None):
        super().__init__(text, parent)
        self.primary = primary
        self.icon = icon
        self.init_style()
    
    def init_style(self):
        if self.primary:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {EMSYS_TEAL};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-size: 14px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {EMSYS_DARK_TEAL};
                }}
                QPushButton:pressed {{
                    background-color: #1f6b5a;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {BG_INPUT};
                    color: {TEXT_PRIMARY};
                    border: 1px solid {BORDER_COLOR};
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-size: 13px;
                }}
                QPushButton:hover {{
                    background-color: #373d44;
                    border-color: {EMSYS_TEAL};
                }}
            """)


class ModernLineEdit(QLineEdit):
    """Custom styled input field."""
    
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {BG_INPUT};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER_COLOR};
                border-radius: 8px;
                padding: 12px 16px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: {EMSYS_TEAL};
                outline: none;
            }}
            QLineEdit::placeholder {{
                color: {TEXT_MUTED};
            }}
        """)


class ModernTabWidget(QTabWidget):
    """Custom styled tab widget."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background-color: transparent;
            }}
            QTabBar::tab {{
                background-color: {BG_INPUT};
                color: {TEXT_SECONDARY};
                border: 1px solid {BORDER_COLOR};
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 10px 24px;
                margin-right: 4px;
                font-size: 13px;
            }}
            QTabBar::tab:selected {{
                background-color: {EMSYS_TEAL};
                color: white;
                border-color: {EMSYS_TEAL};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: #373d44;
            }}
        """)


class ModernTextEdit(QTextEdit):
    """Custom styled text output area."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: {BG_INPUT};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER_COLOR};
                border-radius: 8px;
                padding: 16px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
            }}
        """)


class CardFrame(QFrame):
    """Card-style container with subtle styling."""
    
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.title = title
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER_COLOR};
                border-radius: 12px;
                padding: 20px;
            }}
        """)


class AnalysisWorker(QThread):
    """Background worker for file analysis."""
    finished = Signal(str)
    
    def __init__(self, filepath):
        super().__init__()
        self.filepath = filepath
    
    def run(self):
        results = []
        
        # Extension analysis
        ext_result = analyze_extension(self.filepath)
        if ext_result:
            for family, variant, url in ext_result:
                results.append(f"✅ EXTENSION MATCH: {family}")
                if variant:
                    results.append(f"   Variant: {variant}")
                results.append(f"   Decryptor info: {url}")
        else:
            results.append("❌ No ransomware extension match found")
        
        # Magic bytes check
        magic_result = check_file_magic(self.filepath)
        if magic_result:
            results.append(f"\n🔐 FILE SIGNATURE: {magic_result}")
        else:
            results.append("\n📄 No special file signature detected")
        
        # File info
        try:
            size = os.path.getsize(self.filepath)
            results.append(f"\n📊 File size: {size:,} bytes")
        except OSError:
            pass
        
        self.finished.emit("\n".join(results))


class DirectoryScanWorker(QThread):
    """Background worker for directory scanning."""
    finished = Signal(str)
    
    def __init__(self, dirpath):
        super().__init__()
        self.dirpath = dirpath
    
    def run(self):
        results = []
        extensions_found = defaultdict(list)
        ransom_notes = []
        total_files = 0
        suspicious_files = 0
        
        for root, dirs, files in os.walk(self.dirpath):
            for filename in files:
                filepath = os.path.join(root, filename)
                total_files += 1
                
                ext_result = analyze_extension(filename)
                if ext_result:
                    suspicious_files += 1
                    for family, variant, url in ext_result:
                        extensions_found[(family, variant)].append(filepath)
                
                note_names = ['readme', 'decrypt', 'ransom', 'how_to', 'instructions', 'help']
                base_name = os.path.splitext(filename)[0].lower()
                if any(base_name == name or base_name.startswith(name + '_') for name in note_names):
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in ['.txt', '.html', '.doc', '']:
                        ransom_notes.append(filepath)
        
        results.append(f"Total files scanned: {total_files}")
        results.append(f"Suspicious files found: {suspicious_files}\n")
        
        if extensions_found:
            results.append("=" * 60)
            results.append("RANSOMWARE IDENTIFICATION RESULTS")
            results.append("=" * 60 + "\n")
            
            for (family, variant), files in extensions_found.items():
                results.append(f"✅ Family: {family}")
                if variant:
                    results.append(f"   Variant: {variant}")
                results.append(f"   Files affected: {len(files)}")
                for f in files[:3]:
                    results.append(f"     - {f}")
                if len(files) > 3:
                    results.append(f"     ... and {len(files) - 3} more")
                results.append("")
        
        if ransom_notes:
            results.append("=" * 60)
            results.append("RANSOM NOTE ANALYSIS")
            results.append("=" * 60 + "\n")
            
            for note in ransom_notes:
                results.append(f"📝 Analyzing: {note}")
                matches = analyze_ransom_note(note)
                if matches:
                    for family, keyword in matches:
                        results.append(f"   ✅ MATCH: {family} (keyword: {keyword})")
                else:
                    results.append("   No known ransomware signatures found")
        
        if not extensions_found and not ransom_notes:
            results.append("✅ No ransomware indicators found in this directory.")
        
        self.finished.emit("\n".join(results))


class RansomwareIdentifierWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Emsys | Anti-Ransomware Identifier")
        self.setMinimumSize(1000, 750)
        self.resize(1100, 800)
        
        # Set window icon (use Emsys logo if available)
        logo_path = os.path.join(os.path.dirname(__file__), "emsys_logo.png")
        if os.path.exists(logo_path):
            try:
                self.setWindowIcon(QIcon(logo_path))
            except Exception:
                pass
        
        self.init_ui()
    
    def init_ui(self):
        # Central widget with dark background
        central = QWidget()
        central.setStyleSheet(f"background-color: {BG_DARK};")
        self.setCentralWidget(central)
        
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Content area with tabs
        content_container = QWidget()
        content_container.setStyleSheet("background-color: transparent;")
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(24, 16, 24, 24)
        
        self.tabs = ModernTabWidget()
        self.tabs.addTab(self.create_file_tab(), "📄 File Analysis")
        self.tabs.addTab(self.create_directory_tab(), "📁 Directory Scan")
        self.tabs.addTab(self.create_note_tab(), "📝 Ransom Note")
        
        content_layout.addWidget(self.tabs)
        main_layout.addWidget(content_container, 1)
    
    def create_header(self):
        """Create modern header with logo and branding."""
        header = QWidget()
        header.setFixedHeight(80)
        header.setStyleSheet(f"background-color: {BG_CARD}; border-bottom: 1px solid {BORDER_COLOR};")
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 0, 24, 0)
        
        # Logo
        logo_label = QLabel()
        logo_path = os.path.join(os.path.dirname(__file__), "emsys_logo.png")
        if os.path.exists(logo_path):
            try:
                from PySide6.QtGui import QPixmap
                pixmap = QPixmap(logo_path).scaled(48, 48, Qt.KeepAspectRatio)
                logo_label.setPixmap(pixmap)
            except Exception:
                logo_label.setText("🛡️")
                logo_label.setStyleSheet("font-size: 36px;")
        else:
            logo_label.setText("🛡️")
            logo_label.setStyleSheet("font-size: 36px;")
        
        # Title
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        
        title = QLabel("Emsys Anti-Ransomware Identifier")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet(f"color: {TEXT_PRIMARY};")
        
        subtitle = QLabel("Powered by Emsys - Center for Data Recovery & Digital Forensics | emsys.ir")
        subtitle.setFont(QFont("Segoe UI", 10))
        subtitle.setStyleSheet(f"color: {TEXT_SECONDARY};")
        
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        
        layout.addWidget(logo_label, 0, Qt.AlignVCenter)
        layout.addSpacing(16)
        layout.addLayout(title_layout, 1)
        
        return header
    
    def create_file_tab(self):
        """Create File Analysis tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)
        
        # File selection card
        file_card = CardFrame("Select Encrypted File")
        file_layout = QHBoxLayout(file_card)
        
        self.file_input = ModernLineEdit("Browse for encrypted file...")
        self.file_input.setReadOnly(True)
        file_layout.addWidget(self.file_input, 1)
        
        browse_btn = ModernButton("📂 Browse", primary=False)
        browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(browse_btn)
        
        layout.addWidget(file_card)
        
        # Analyze button
        analyze_btn = ModernButton("🔍 Analyze File", primary=True)
        analyze_btn.setFixedHeight(48)
        analyze_btn.clicked.connect(self.analyze_file)
        layout.addWidget(analyze_btn)
        
        # Results card
        results_card = CardFrame("Analysis Results")
        results_layout = QVBoxLayout(results_card)
        
        self.file_results = ModernTextEdit()
        self.file_results.setPlaceholderText("Analysis results will appear here...")
        results_layout.addWidget(self.file_results)
        
        layout.addWidget(results_card, 1)
        
        return tab
    
    def create_directory_tab(self):
        """Create Directory Scan tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)
        
        # Directory selection card
        dir_card = CardFrame("Select Directory to Scan")
        dir_layout = QHBoxLayout(dir_card)
        
        self.dir_input = ModernLineEdit("Browse for directory...")
        self.dir_input.setReadOnly(True)
        dir_layout.addWidget(self.dir_input, 1)
        
        browse_btn = ModernButton("📂 Browse", primary=False)
        browse_btn.clicked.connect(self.browse_directory)
        dir_layout.addWidget(browse_btn)
        
        layout.addWidget(dir_card)
        
        # Scan button
        scan_btn = ModernButton("📊 Scan Directory", primary=True)
        scan_btn.setFixedHeight(48)
        scan_btn.clicked.connect(self.scan_directory)
        layout.addWidget(scan_btn)
        
        # Progress bar
        self.scan_progress = QProgressBar()
        self.scan_progress.setVisible(False)
        self.scan_progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: {BG_INPUT};
                border: 1px solid {BORDER_COLOR};
                border-radius: 8px;
                height: 8px;
            }}
            QProgressBar::chunk {{
                background-color: {EMSYS_TEAL};
                border-radius: 6px;
            }}
        """)
        layout.addWidget(self.scan_progress)
        
        # Results card
        results_card = CardFrame("Scan Results")
        results_layout = QVBoxLayout(results_card)
        
        self.dir_results = ModernTextEdit()
        self.dir_results.setPlaceholderText("Scan results will appear here...")
        results_layout.addWidget(self.dir_results)
        
        layout.addWidget(results_card, 1)
        
        return tab
    
    def create_note_tab(self):
        """Create Ransom Note tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)
        
        # Note selection card
        note_card = CardFrame("Select Ransom Note")
        note_layout = QHBoxLayout(note_card)
        
        self.note_input = ModernLineEdit("Browse for ransom note...")
        self.note_input.setReadOnly(True)
        note_layout.addWidget(self.note_input, 1)
        
        browse_btn = ModernButton("📂 Browse", primary=False)
        browse_btn.clicked.connect(self.browse_note)
        note_layout.addWidget(browse_btn)
        
        layout.addWidget(note_card)
        
        # Analyze button
        analyze_btn = ModernButton("🔎 Analyze Note", primary=True)
        analyze_btn.setFixedHeight(48)
        analyze_btn.clicked.connect(self.analyze_note)
        layout.addWidget(analyze_btn)
        
        # Results card
        results_card = CardFrame("Note Analysis Results")
        results_layout = QVBoxLayout(results_card)
        
        self.note_results = ModernTextEdit()
        self.note_results.setPlaceholderText("Note analysis results will appear here...")
        results_layout.addWidget(self.note_results)
        
        layout.addWidget(results_card, 1)
        
        return tab
    
    def browse_file(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Select Encrypted File", "", "All Files (*.*)")
        if filepath:
            self.file_input.setText(filepath)
    
    def browse_directory(self):
        dirpath = QFileDialog.getExistingDirectory(self, "Select Directory to Scan")
        if dirpath:
            self.dir_input.setText(dirpath)
    
    def browse_note(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Select Ransom Note", "",
            "Text Files (*.txt *.html);;All Files (*.*)"
        )
        if filepath:
            self.note_input.setText(filepath)
    
    def analyze_file(self):
        filepath = self.file_input.text()
        if not filepath or not os.path.exists(filepath):
            QMessageBox.warning(self, "No File", "Please select a valid file to analyze.")
            return
        
        self.file_results.clear()
        self.file_results.append("⏳ Analyzing...")
        
        worker = AnalysisWorker(filepath)
        worker.finished.connect(lambda result: self.file_results.setText(result))
        worker.start()
    
    def scan_directory(self):
        dirpath = self.dir_input.text()
        if not dirpath or not os.path.exists(dirpath):
            QMessageBox.warning(self, "No Directory", "Please select a valid directory to scan.")
            return
        
        self.dir_results.clear()
        self.dir_results.append("⏳ Scanning...")
        self.scan_progress.setVisible(True)
        self.scan_progress.setRange(0, 0)  # Indeterminate
        
        worker = DirectoryScanWorker(dirpath)
        worker.finished.connect(lambda result: self.on_scan_finished(result))
        worker.start()
    
    def on_scan_finished(self, result):
        self.dir_results.setText(result)
        self.scan_progress.setVisible(False)
    
    def analyze_note(self):
        filepath = self.note_input.text()
        if not filepath or not os.path.exists(filepath):
            QMessageBox.warning(self, "No File", "Please select a valid ransom note file.")
            return
        
        results = []
        results.append(f"Analyzing ransom note: {filepath}")
        results.append("=" * 60)
        
        matches = analyze_ransom_note(filepath)
        if matches:
            for family, keyword in matches:
                results.append(f"✅ MATCH: {family}")
                results.append(f"   Keyword found: {keyword}")
        else:
            results.append("❌ No known ransomware signatures found in note.")
            results.append("\n💡 Try uploading to NoMoreRansom.org's Crypto Sheriff tool:")
            results.append("   https://nomoreransom.org/crypto-sheriff/")
        
        # Show note preview
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(500)
            results.append("\n📄 Note preview (first 500 chars):")
            results.append("-" * 40)
            results.append(content)
        except IOError as e:
            results.append(f"\n⚠️ Could not read note: {e}")
        
        self.note_results.setText("\n".join(results))


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Emsys Anti-Ransomware Identifier")
    
    # Set application-wide font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    window = RansomwareIdentifierWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
