#!/usr/bin/env python3
"""
Emsys Anti-Ransomware Identifier - GUI Version
A graphical interface for identifying ransomware types from files and directories.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import re
import threading
from collections import defaultdict

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None

# Import the core analysis functions from ransom_id.py
try:
    from ransom_id import analyze_extension, analyze_ransom_note, check_file_magic, RANSOMWARE_DB, NOTE_SIGNATURES
except ImportError:
    # Fallback if running standalone - include minimal database
    RANSOMWARE_DB = {}
    NOTE_SIGNATURES = {}

    def analyze_extension(filename):
        return None

    def analyze_ransom_note(filepath):
        return []

    def check_file_magic(filepath):
        return None


class RansomwareIdentifierApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Emsys | Anti-Ransomware Identifier")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # Style configuration
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Emsys brand colors (from logo analysis)
        bg_color = "#f0f0f0"
        header_bg = "#30b090"  # Primary teal from Emsys logo
        header_fg = "white"
        accent_color = "#30b090"  # Primary brand color
        success_color = "#27ae60"
        warning_color = "#f39c12"
        danger_color = "#e74c3c"
        
        self.style.configure('TFrame', background=bg_color)
        self.style.configure('Header.TLabel', font=('Segoe UI', 16, 'bold'),
                           foreground=header_fg, background=header_bg)
        self.style.configure('SubHeader.TLabel', font=('Segoe UI', 12, 'bold'),
                           foreground="#34495e", background=bg_color)
        self.style.configure('Result.TLabel', font=('Segoe UI', 10))
        self.style.configure('Status.TLabel', font=('Segoe UI', 9, 'italic'),
                           foreground="#7f8c8d", background=bg_color)
        self.style.configure('Accent.TButton', font=('Segoe UI', 10, 'bold'),
                           foreground="white", background=accent_color)
        
        # Create main container
        self.container = ttk.Frame(root, padding=10)
        self.container.pack(fill=tk.BOTH, expand=True)
        
        # Header
        self.create_header(header_bg, header_fg)
        
        # Main content area with tabs
        self.notebook = ttk.Notebook(self.container)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Tab 1: Single File Analysis
        self.file_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.file_tab, text="📄 File Analysis")
        self.create_file_analysis_tab()
        
        # Tab 2: Directory Scan
        self.dir_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.dir_tab, text="📁 Directory Scan")
        self.create_directory_scan_tab()
        
        # Tab 3: Ransom Note Analyzer
        self.note_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.note_tab, text="📝 Ransom Note")
        self.create_ransom_note_tab()
        
        # Status bar
        self.status_bar = ttk.Label(self.container,
                                   text="Ready - Select a file or directory to analyze",
                                   style='Status.TLabel', anchor=tk.W)
        self.status_bar.pack(fill=tk.X, pady=(5, 0))
    
    def create_header(self, bg_color, fg_color):
        """Create application header with logo."""
        # Try to load and display Emsys logo
        self.logo_image = None
        try:
            logo_path = os.path.join(os.path.dirname(__file__), "emsys_logo.png")
            if os.path.exists(logo_path) and Image is not None:
                img = Image.open(logo_path)
                img = img.resize((40, 40), Image.Resampling.LANCZOS)
                self.logo_image = ImageTk.PhotoImage(img)
        except Exception:
            pass
        
        header_frame = ttk.Frame(self.container)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Header with logo and title
        inner_frame = ttk.Frame(header_frame)
        inner_frame.pack(fill=tk.X)
        
        if self.logo_image:
            logo_label = ttk.Label(inner_frame, image=self.logo_image)
            logo_label.pack(side=tk.LEFT, padx=(0, 10))
        
        title_label = ttk.Label(inner_frame,
                               text="Emsys Anti-Ransomware Identifier",
                               style='Header.TLabel', anchor=tk.W)
        title_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        subtitle = ttk.Label(self.container,
                           text="Powered by Emsys - Center for Data Recovery & Digital Forensics | emsys.ir",
                           style='Status.TLabel', anchor=tk.W)
        subtitle.pack(fill=tk.X, pady=(0, 5))
    
    def create_file_analysis_tab(self):
        """Create single file analysis tab."""
        # File selection frame
        select_frame = ttk.LabelFrame(self.file_tab, text="Select Encrypted File", padding=10)
        select_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.file_path_var = tk.StringVar()
        file_entry = ttk.Entry(select_frame, textvariable=self.file_path_var, state='readonly')
        file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        browse_btn = ttk.Button(select_frame, text="Browse...", command=self.browse_file)
        browse_btn.pack(side=tk.RIGHT)
        
        analyze_btn = ttk.Button(self.file_tab, text="🔍 Analyze File",
                                command=self.analyze_single_file,
                                style='Accent.TButton')
        analyze_btn.pack(fill=tk.X, pady=(0, 10))
        
        # Results frame
        results_frame = ttk.LabelFrame(self.file_tab, text="Analysis Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        self.file_results_text = scrolledtext.ScrolledText(results_frame,
                                                          wrap=tk.WORD,
                                                          font=('Consolas', 10),
                                                          state='disabled')
        self.file_results_text.pack(fill=tk.BOTH, expand=True)
    
    def create_directory_scan_tab(self):
        """Create directory scan tab."""
        # Directory selection frame
        select_frame = ttk.LabelFrame(self.dir_tab, text="Select Directory to Scan", padding=10)
        select_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.dir_path_var = tk.StringVar()
        dir_entry = ttk.Entry(select_frame, textvariable=self.dir_path_var, state='readonly')
        dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        browse_btn = ttk.Button(select_frame, text="Browse...", command=self.browse_directory)
        browse_btn.pack(side=tk.RIGHT)
        
        scan_btn = ttk.Button(self.dir_tab, text="📊 Scan Directory",
                             command=self.scan_directory,
                             style='Accent.TButton')
        scan_btn.pack(fill=tk.X, pady=(0, 10))
        
        # Progress bar
        self.progress = ttk.Progressbar(self.dir_tab, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=5)
        
        # Results frame
        results_frame = ttk.LabelFrame(self.dir_tab, text="Scan Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        self.dir_results_text = scrolledtext.ScrolledText(results_frame,
                                                         wrap=tk.WORD,
                                                         font=('Consolas', 10),
                                                         state='disabled')
        self.dir_results_text.pack(fill=tk.BOTH, expand=True)
    
    def create_ransom_note_tab(self):
        """Create ransom note analyzer tab."""
        # Note selection frame
        select_frame = ttk.LabelFrame(self.note_tab, text="Select Ransom Note", padding=10)
        select_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.note_path_var = tk.StringVar()
        note_entry = ttk.Entry(select_frame, textvariable=self.note_path_var, state='readonly')
        note_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        browse_btn = ttk.Button(select_frame, text="Browse...", command=self.browse_ransom_note)
        browse_btn.pack(side=tk.RIGHT)
        
        analyze_btn = ttk.Button(self.note_tab, text="🔎 Analyze Note",
                                command=self.analyze_ransom_note_file,
                                style='Accent.TButton')
        analyze_btn.pack(fill=tk.X, pady=(0, 10))
        
        # Results frame
        results_frame = ttk.LabelFrame(self.note_tab, text="Note Analysis Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        self.note_results_text = scrolledtext.ScrolledText(results_frame,
                                                          wrap=tk.WORD,
                                                          font=('Consolas', 10),
                                                          state='disabled')
        self.note_results_text.pack(fill=tk.BOTH, expand=True)
    
    def browse_file(self):
        """Open file browser dialog."""
        filepath = filedialog.askopenfilename(
            title="Select Encrypted File",
            filetypes=[("All Files", "*.*")]
        )
        if filepath:
            self.file_path_var.set(filepath)
    
    def browse_directory(self):
        """Open directory browser dialog."""
        dirpath = filedialog.askdirectory(title="Select Directory to Scan")
        if dirpath:
            self.dir_path_var.set(dirpath)
    
    def browse_ransom_note(self):
        """Open ransom note browser dialog."""
        filepath = filedialog.askopenfilename(
            title="Select Ransom Note",
            filetypes=[("Text Files", "*.txt *.html *.doc"), ("All Files", "*.*")]
        )
        if filepath:
            self.note_path_var.set(filepath)
    
    def analyze_single_file(self):
        """Analyze a single encrypted file."""
        filepath = self.file_path_var.get()
        if not filepath or not os.path.exists(filepath):
            messagebox.showwarning("No File", "Please select a valid file to analyze.")
            return
        
        self.set_status(f"Analyzing: {os.path.basename(filepath)}")
        self.clear_text(self.file_results_text)
        
        # Run analysis in separate thread
        thread = threading.Thread(target=self._analyze_file_thread, args=(filepath,))
        thread.daemon = True
        thread.start()
    
    def _analyze_file_thread(self, filepath):
        """Thread-safe file analysis."""
        results = []
        
        # Extension analysis
        ext_result = analyze_extension(filepath)
        if ext_result:
            for family, variant, url in ext_result:
                self.append_text(self.file_results_text,
                               f"✅ EXTENSION MATCH: {family}")
                if variant:
                    self.append_text(self.file_results_text, f"   Variant: {variant}")
                self.append_text(self.file_results_text, f"   Decryptor info: {url}")
                results.append((family, variant))
        else:
            self.append_text(self.file_results_text, "❌ No ransomware extension match found")
        
        # Magic bytes check
        magic_result = check_file_magic(filepath)
        if magic_result:
            self.append_text(self.file_results_text, f"\n🔐 FILE SIGNATURE: {magic_result}")
        else:
            self.append_text(self.file_results_text, "\n📄 No special file signature detected")
        
        # File info
        try:
            size = os.path.getsize(filepath)
            self.append_text(self.file_results_text, f"\n📊 File size: {size:,} bytes")
        except OSError:
            pass
        
        if not results:
            self.append_text(self.file_results_text, "\n💡 Tip: Try uploading to NoMoreRansom.org's Crypto Sheriff tool")
            self.append_text(self.file_results_text, "   https://nomoreransom.org/crypto-sheriff/")
        
        self.set_status("Analysis complete")
    
    def scan_directory(self):
        """Scan a directory for encrypted files."""
        dirpath = self.dir_path_var.get()
        if not dirpath or not os.path.exists(dirpath):
            messagebox.showwarning("No Directory", "Please select a valid directory to scan.")
            return
        
        self.set_status(f"Scanning: {dirpath}")
        self.clear_text(self.dir_results_text)
        self.progress.start()
        
        # Run scan in separate thread
        thread = threading.Thread(target=self._scan_directory_thread, args=(dirpath,))
        thread.daemon = True
        thread.start()
    
    def _scan_directory_thread(self, dirpath):
        """Thread-safe directory scanning."""
        self.append_text(self.dir_results_text, f"Scanning directory: {dirpath}")
        self.append_text(self.dir_results_text, "=" * 60)
        
        extensions_found = defaultdict(list)
        ransom_notes = []
        total_files = 0
        suspicious_files = 0
        
        for root, dirs, files in os.walk(dirpath):
            for filename in files:
                filepath = os.path.join(root, filename)
                total_files += 1
                
                # Check extension
                ext_result = analyze_extension(filename)
                if ext_result:
                    suspicious_files += 1
                    for family, variant, url in ext_result:
                        extensions_found[(family, variant)].append(filepath)
                
                # Check for ransom notes
                note_names = ['readme', 'decrypt', 'ransom', 'how_to', 'instructions', 'help']
                base_name = os.path.splitext(filename)[0].lower()
                if any(base_name == name or base_name.startswith(name + '_') for name in note_names):
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in ['.txt', '.html', '.doc', '']:
                        ransom_notes.append(filepath)
        
        self.append_text(self.dir_results_text, f"\nTotal files scanned: {total_files}")
        self.append_text(self.dir_results_text, f"Suspicious files found: {suspicious_files}")
        
        # Report extension matches
        if extensions_found:
            self.append_text(self.dir_results_text, "\n" + "=" * 60)
            self.append_text(self.dir_results_text, "RANSOMWARE IDENTIFICATION RESULTS")
            self.append_text(self.dir_results_text, "=" * 60)
            
            for (family, variant), files in extensions_found.items():
                self.append_text(self.dir_results_text, f"\n✅ Family: {family}")
                if variant:
                    self.append_text(self.dir_results_text, f"   Variant: {variant}")
                self.append_text(self.dir_results_text, f"   Files affected: {len(files)}")
                # Show first few files
                for f in files[:3]:
                    self.append_text(self.dir_results_text, f"     - {f}")
                if len(files) > 3:
                    self.append_text(self.dir_results_text, f"     ... and {len(files) - 3} more")
        
        # Analyze ransom notes
        if ransom_notes:
            self.append_text(self.dir_results_text, "\n" + "=" * 60)
            self.append_text(self.dir_results_text, "RANSOM NOTE ANALYSIS")
            self.append_text(self.dir_results_text, "=" * 60)
            
            for note in ransom_notes:
                self.append_text(self.dir_results_text, f"\n📝 Analyzing: {note}")
                matches = analyze_ransom_note(note)
                if matches:
                    for family, keyword in matches:
                        self.append_text(self.dir_results_text,
                                       f"   ✅ MATCH: {family} (keyword: {keyword})")
                else:
                    self.append_text(self.dir_results_text, "   No known ransomware signatures found")
        
        if not extensions_found and not ransom_notes:
            self.append_text(self.dir_results_text, "\n✅ No ransomware indicators found in this directory.")
        
        self.progress.stop()
        self.set_status("Directory scan complete")
    
    def analyze_ransom_note_file(self):
        """Analyze a ransom note file."""
        filepath = self.note_path_var.get()
        if not filepath or not os.path.exists(filepath):
            messagebox.showwarning("No File", "Please select a valid ransom note file.")
            return
        
        self.set_status(f"Analyzing ransom note: {os.path.basename(filepath)}")
        self.clear_text(self.note_results_text)
        
        thread = threading.Thread(target=self._analyze_note_thread, args=(filepath,))
        thread.daemon = True
        thread.start()
    
    def _analyze_note_thread(self, filepath):
        """Thread-safe ransom note analysis."""
        self.append_text(self.note_results_text, f"Analyzing ransom note: {filepath}")
        self.append_text(self.note_results_text, "=" * 60)
        
        matches = analyze_ransom_note(filepath)
        if matches:
            for family, keyword in matches:
                self.append_text(self.note_results_text,
                               f"\n✅ MATCH: {family}")
                self.append_text(self.note_results_text, f"   Keyword found: {keyword}")
        else:
            self.append_text(self.note_results_text, "\n❌ No known ransomware signatures found in note.")
            self.append_text(self.note_results_text, "\n💡 Try uploading to NoMoreRansom.org's Crypto Sheriff tool:")
            self.append_text(self.note_results_text, "   https://nomoreransom.org/crypto-sheriff/")
        
        # Show note preview
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(500)
            self.append_text(self.note_results_text, "\n📄 Note preview (first 500 chars):")
            self.append_text(self.note_results_text, "-" * 40)
            self.append_text(self.note_results_text, content)
        except IOError as e:
            self.append_text(self.note_results_text, f"\n⚠️ Could not read note: {e}")
        
        self.set_status("Ransom note analysis complete")
    
    def set_status(self, message):
        """Update status bar."""
        self.status_bar.config(text=message)
    
    def clear_text(self, text_widget):
        """Clear text widget content."""
        text_widget.config(state='normal')
        text_widget.delete(1.0, tk.END)
        text_widget.config(state='disabled')
    
    def append_text(self, text_widget, text):
        """Append text to text widget (thread-safe)."""
        self.root.after(0, self._append_text_internal, text_widget, text)
    
    def _append_text_internal(self, text_widget, text):
        """Internal thread-safe text appending."""
        text_widget.config(state='normal')
        text_widget.insert(tk.END, text + "\n")
        text_widget.see(tk.END)
        text_widget.config(state='disabled')


def main():
    import sys
    
    # Check for tab selection argument
    initial_tab = 0  # Default: File Analysis
    if len(sys.argv) > 1:
        try:
            initial_tab = int(sys.argv[1])
        except ValueError:
            pass
    
    root = tk.Tk()
    app = RansomwareIdentifierApp(root)
    
    # Select initial tab if specified
    if initial_tab > 0 and initial_tab < 3:
        app.notebook.select(initial_tab)
    
    root.mainloop()


if __name__ == "__main__":
    main()
