#!/usr/bin/env python3
"""
Emsys Anti-Ransomware Identifier - Modern GUI Version
A sleek, modern graphical interface for identifying ransomware types.
Uses CustomTkinter for a contemporary flat design aesthetic.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import threading
from collections import defaultdict

# Import the core analysis functions from ransom_id.py
try:
    from ransom_id import analyze_extension, analyze_ransom_note, check_file_magic, RANSOMWARE_DB, NOTE_SIGNATURES
except ImportError:
    RANSOMWARE_DB = {}
    NOTE_SIGNATURES = {}

    def analyze_extension(filename):
        return None

    def analyze_ransom_note(filepath):
        return []

    def check_file_magic(filepath):
        return None


# Emsys brand colors
EMSYS_TEAL = "#30b090"
EMSYS_DARK = "#2c3e50"
EMSYS_LIGHT = "#f8f9fa"
EMSYS_CARD = "#ffffff"
EMSYS_BORDER = "#e9ecef"
EMSYS_TEXT = "#495057"
EMSYS_SUCCESS = "#2ecc71"
EMSYS_WARNING = "#f39c12"
EMSYS_DANGER = "#e74c3c"
EMSYS_INFO = "#3498db"


class RansomwareIdentifierApp(ctk.CTk):
    def __init__(self, initial_tab=0):
        super().__init__()
        
        # Configure app appearance
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        self.title("Emsys | Anti-Ransomware Identifier")
        self.geometry("1000x750")
        self.minsize(800, 600)
        
        # Configure colors
        self.configure(fg_color=EMSYS_LIGHT)
        
        # Create layout
        self.create_header()
        self.create_main_content(initial_tab)
        self.create_status_bar()
    
    def create_header(self):
        """Create modern header with logo and title."""
        header = ctk.CTkFrame(self, height=80, corner_radius=0, fg_color=EMSYS_TEAL)
        header.pack(fill="x", padx=0, pady=0)
        
        # Logo placeholder (circle with E)
        logo_frame = ctk.CTkFrame(header, width=50, height=50, corner_radius=25,
                                 fg_color="white")
        logo_frame.pack(side="left", padx=20, pady=15)
        
        logo_label = ctk.CTkLabel(logo_frame, text="E", font=ctk.CTkFont(
            size=24, weight="bold"), text_color=EMSYS_TEAL)
        logo_label.pack()
        
        # Title and subtitle
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left", padx=10)
        
        title = ctk.CTkLabel(title_frame, text="Emsys Anti-Ransomware Identifier",
                           font=ctk.CTkFont(size=20, weight="bold"),
                           text_color="white")
        title.pack(anchor="w")
        
        subtitle = ctk.CTkLabel(title_frame,
                               text="Powered by Emsys - Center for Data Recovery & Digital Forensics | emsys.ir",
                               font=ctk.CTkFont(size=10),
                               text_color="#d5f5e3")
        subtitle.pack(anchor="w")
    
    def create_main_content(self, initial_tab):
        """Create tabbed main content area."""
        # Tab container with rounded corners
        tab_container = ctk.CTkFrame(self, corner_radius=12, fg_color=EMSYS_CARD)
        tab_container.pack(fill="both", expand=True, padx=20, pady=15)
        
        # Custom tab buttons (modern pill-style tabs)
        tab_buttons_frame = ctk.CTkFrame(tab_container, fg_color=EMSYS_LIGHT,
                                        corner_radius=12)
        tab_buttons_frame.pack(fill="x")
        
        self.tab_buttons = []
        tab_names = ["📄 File Analysis", "📁 Directory Scan", "📝 Ransom Note"]
        
        for i, name in enumerate(tab_names):
            btn = ctk.CTkButton(
                tab_buttons_frame,
                text=name,
                font=ctk.CTkFont(size=13, weight="bold"),
                corner_radius=20,
                fg_color="transparent",
                hover_color="#e8f5e9",
                text_color=EMSYS_TEXT,
                command=lambda idx=i: self.switch_tab(idx)
            )
            btn.pack(side="left", padx=10, pady=10)
            self.tab_buttons.append(btn)
        
        # Highlight initial tab
        self.switch_tab(initial_tab)
        
        # Tab content area
        self.content_frame = ctk.CTkFrame(tab_container, fg_color=EMSYS_CARD,
                                         corner_radius=(0, 0, 12, 12))
        self.content_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        # Create tab content
        self.file_tab_content = self.create_file_analysis_tab()
        self.dir_tab_content = self.create_directory_scan_tab()
        self.note_tab_content = self.create_ransom_note_tab()
    
    def switch_tab(self, index):
        """Switch between tabs."""
        # Update button styles
        for i, btn in enumerate(self.tab_buttons):
            if i == index:
                btn.configure(fg_color=EMSYS_TEAL, text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color=EMSYS_TEXT)
        
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Show selected tab
        if index == 0:
            self.file_tab_content.pack(fill="both", expand=True, padx=15, pady=15)
        elif index == 1:
            self.dir_tab_content.pack(fill="both", expand=True, padx=15, pady=15)
        else:
            self.note_tab_content.pack(fill="both", expand=True, padx=15, pady=15)
    
    def create_file_analysis_tab(self):
        """Create modern file analysis tab."""
        container = ctk.CTkFrame(ctk.CTkFrame(), fg_color="transparent")
        
        # Section title
        title = ctk.CTkLabel(container, text="Analyze Encrypted File",
                           font=ctk.CTkFont(size=18, weight="bold"),
                           text_color=EMSYS_DARK)
        title.pack(anchor="w", pady=(0, 5))
        
        desc = ctk.CTkLabel(container, text="Select an encrypted file to identify the ransomware family",
                          font=ctk.CTkFont(size=12), text_color="#7f8c8d")
        desc.pack(anchor="w", pady=(0, 15))
        
        # File selection card
        select_card = ctk.CTkFrame(container, corner_radius=10, fg_color=EMSYS_LIGHT)
        select_card.pack(fill="x", pady=(0, 10))
        
        self.file_path_var = ctk.StringVar()
        file_entry = ctk.CTkEntry(
            select_card,
            textvariable=self.file_path_var,
            placeholder_text="Select an encrypted file...",
            font=ctk.CTkFont(size=12),
            corner_radius=8,
            fg_color="white"
        )
        file_entry.pack(side="left", fill="x", expand=True, padx=15, pady=10)
        
        browse_btn = ctk.CTkButton(
            select_card,
            text="Browse",
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=8,
            fg_color=EMSYS_TEAL,
            hover_color="#27a385",
            command=self.browse_file
        )
        browse_btn.pack(side="right", padx=10, pady=10)
        
        # Analyze button
        analyze_btn = ctk.CTkButton(
            container,
            text="🔍 Analyze File",
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=10,
            fg_color=EMSYS_TEAL,
            hover_color="#27a385",
            command=self.analyze_single_file
        )
        analyze_btn.pack(fill="x", pady=(0, 15))
        
        # Results card
        results_card = ctk.CTkFrame(container, corner_radius=10,
                                  fg_color="#f8f9fa", border_width=1,
                                  border_color=EMSYS_BORDER)
        results_card.pack(fill="both", expand=True)
        
        results_title = ctk.CTkLabel(
            results_card,
            text="Analysis Results",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=EMSYS_DARK
        )
        results_title.pack(anchor="w", padx=15, pady=(10, 5))
        
        self.file_results_text = ctk.CTkTextbox(
            results_card,
            font=ctk.CTkFont(family="Consolas", size=11),
            corner_radius=8,
            fg_color="white",
            border_width=0
        )
        self.file_results_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        return container
    
    def create_directory_scan_tab(self):
        """Create modern directory scan tab."""
        container = ctk.CTkFrame(ctk.CTkFrame(), fg_color="transparent")
        
        # Section title
        title = ctk.CTkLabel(container, text="Scan Directory",
                           font=ctk.CTkFont(size=18, weight="bold"),
                           text_color=EMSYS_DARK)
        title.pack(anchor="w", pady=(0, 5))
        
        desc = ctk.CTkLabel(container,
                          text="Recursively scan a directory for encrypted files and ransom notes",
                          font=ctk.CTkFont(size=12), text_color="#7f8c8d")
        desc.pack(anchor="w", pady=(0, 15))
        
        # Directory selection card
        select_card = ctk.CTkFrame(container, corner_radius=10, fg_color=EMSYS_LIGHT)
        select_card.pack(fill="x", pady=(0, 10))
        
        self.dir_path_var = ctk.StringVar()
        dir_entry = ctk.CTkEntry(
            select_card,
            textvariable=self.dir_path_var,
            placeholder_text="Select a directory to scan...",
            font=ctk.CTkFont(size=12),
            corner_radius=8,
            fg_color="white"
        )
        dir_entry.pack(side="left", fill="x", expand=True, padx=15, pady=10)
        
        browse_btn = ctk.CTkButton(
            select_card,
            text="Browse",
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=8,
            fg_color=EMSYS_TEAL,
            hover_color="#27a385",
            command=self.browse_directory
        )
        browse_btn.pack(side="right", padx=10, pady=10)
        
        # Scan button
        scan_btn = ctk.CTkButton(
            container,
            text="📊 Scan Directory",
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=10,
            fg_color=EMSYS_TEAL,
            hover_color="#27a385",
            command=self.scan_directory
        )
        scan_btn.pack(fill="x", pady=(0, 10))
        
        # Progress bar
        self.progress = ctk.CTkProgressBar(container, mode="indeterminate",
                                          corner_radius=8)
        self.progress.pack(fill="x", pady=(0, 15))
        self.progress.hide()
        
        # Results card
        results_card = ctk.CTkFrame(container, corner_radius=10,
                                  fg_color="#f8f9fa", border_width=1,
                                  border_color=EMSYS_BORDER)
        results_card.pack(fill="both", expand=True)
        
        results_title = ctk.CTkLabel(
            results_card,
            text="Scan Results",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=EMSYS_DARK
        )
        results_title.pack(anchor="w", padx=15, pady=(10, 5))
        
        self.dir_results_text = ctk.CTkTextbox(
            results_card,
            font=ctk.CTkFont(family="Consolas", size=11),
            corner_radius=8,
            fg_color="white",
            border_width=0
        )
        self.dir_results_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        return container
    
    def create_ransom_note_tab(self):
        """Create modern ransom note analyzer tab."""
        container = ctk.CTkFrame(ctk.CTkFrame(), fg_color="transparent")
        
        # Section title
        title = ctk.CTkLabel(container, text="Analyze Ransom Note",
                           font=ctk.CTkFont(size=18, weight="bold"),
                           text_color=EMSYS_DARK)
        title.pack(anchor="w", pady=(0, 5))
        
        desc = ctk.CTkLabel(container,
                          text="Upload a ransom note to identify the ransomware family",
                          font=ctk.CTkFont(size=12), text_color="#7f8c8d")
        desc.pack(anchor="w", pady=(0, 15))
        
        # Note selection card
        select_card = ctk.CTkFrame(container, corner_radius=10, fg_color=EMSYS_LIGHT)
        select_card.pack(fill="x", pady=(0, 10))
        
        self.note_path_var = ctk.StringVar()
        note_entry = ctk.CTkEntry(
            select_card,
            textvariable=self.note_path_var,
            placeholder_text="Select a ransom note file...",
            font=ctk.CTkFont(size=12),
            corner_radius=8,
            fg_color="white"
        )
        note_entry.pack(side="left", fill="x", expand=True, padx=15, pady=10)
        
        browse_btn = ctk.CTkButton(
            select_card,
            text="Browse",
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=8,
            fg_color=EMSYS_TEAL,
            hover_color="#27a385",
            command=self.browse_ransom_note
        )
        browse_btn.pack(side="right", padx=10, pady=10)
        
        # Analyze button
        analyze_btn = ctk.CTkButton(
            container,
            text="🔎 Analyze Note",
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=10,
            fg_color=EMSYS_TEAL,
            hover_color="#27a385",
            command=self.analyze_ransom_note_file
        )
        analyze_btn.pack(fill="x", pady=(0, 15))
        
        # Results card
        results_card = ctk.CTkFrame(container, corner_radius=10,
                                  fg_color="#f8f9fa", border_width=1,
                                  border_color=EMSYS_BORDER)
        results_card.pack(fill="both", expand=True)
        
        results_title = ctk.CTkLabel(
            results_card,
            text="Note Analysis Results",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=EMSYS_DARK
        )
        results_title.pack(anchor="w", padx=15, pady=(10, 5))
        
        self.note_results_text = ctk.CTkTextbox(
            results_card,
            font=ctk.CTkFont(family="Consolas", size=11),
            corner_radius=8,
            fg_color="white",
            border_width=0
        )
        self.note_results_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        return container
    
    def create_status_bar(self):
        """Create modern status bar."""
        status = ctk.CTkFrame(self, height=35, corner_radius=0,
                            fg_color=EMSYS_DARK)
        status.pack(fill="x", side="bottom")
        
        self.status_label = ctk.CTkLabel(
            status,
            text="Ready - Select a file or directory to analyze",
            font=ctk.CTkFont(size=11),
            text_color="#ecf0f1"
        )
        self.status_label.pack(side="left", padx=15, pady=8)
    
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
        
        thread = threading.Thread(target=self._analyze_file_thread, args=(filepath,))
        thread.daemon = True
        thread.start()
    
    def _analyze_file_thread(self, filepath):
        """Thread-safe file analysis."""
        results = []
        
        ext_result = analyze_extension(filepath)
        if ext_result:
            for family, variant, url in ext_result:
                self.append_text(self.file_results_text, f"✅ EXTENSION MATCH: {family}")
                if variant:
                    self.append_text(self.file_results_text, f"   Variant: {variant}")
                self.append_text(self.file_results_text, f"   Decryptor info: {url}")
                results.append((family, variant))
        else:
            self.append_text(self.file_results_text, "❌ No ransomware extension match found")
        
        magic_result = check_file_magic(filepath)
        if magic_result:
            self.append_text(self.file_results_text, f"\n🔐 FILE SIGNATURE: {magic_result}")
        else:
            self.append_text(self.file_results_text, "\n📄 No special file signature detected")
        
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
        self.progress.appear()
        self.progress.start()
        
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
        
        self.append_text(self.dir_results_text, f"\nTotal files scanned: {total_files}")
        self.append_text(self.dir_results_text, f"Suspicious files found: {suspicious_files}")
        
        if extensions_found:
            self.append_text(self.dir_results_text, "\n" + "=" * 60)
            self.append_text(self.dir_results_text, "RANSOMWARE IDENTIFICATION RESULTS")
            self.append_text(self.dir_results_text, "=" * 60)
            
            for (family, variant), files in extensions_found.items():
                self.append_text(self.dir_results_text, f"\n✅ Family: {family}")
                if variant:
                    self.append_text(self.dir_results_text, f"   Variant: {variant}")
                self.append_text(self.dir_results_text, f"   Files affected: {len(files)}")
                for f in files[:3]:
                    self.append_text(self.dir_results_text, f"     - {f}")
                if len(files) > 3:
                    self.append_text(self.dir_results_text, f"     ... and {len(files) - 3} more")
        
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
        self.progress.hide()
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
                self.append_text(self.note_results_text, f"\n✅ MATCH: {family}")
                self.append_text(self.note_results_text, f"   Keyword found: {keyword}")
        else:
            self.append_text(self.note_results_text, "\n❌ No known ransomware signatures found in note.")
            self.append_text(self.note_results_text, "\n💡 Try uploading to NoMoreRansom.org's Crypto Sheriff tool:")
            self.append_text(self.note_results_text, "   https://nomoreransom.org/crypto-sheriff/")
        
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
        self.status_label.configure(text=message)
    
    def clear_text(self, text_widget):
        """Clear text widget content."""
        text_widget.delete("1.0", "end")
    
    def append_text(self, text_widget, text):
        """Append text to text widget (thread-safe)."""
        self.after(0, self._append_text_internal, text_widget, text)
    
    def _append_text_internal(self, text_widget, text):
        """Internal thread-safe text appending."""
        text_widget.insert("end", text + "\n")
        text_widget.see("end")


def main():
    import sys
    
    initial_tab = 0
    if len(sys.argv) > 1:
        try:
            initial_tab = int(sys.argv[1])
        except ValueError:
            pass
    
    app = RansomwareIdentifierApp(initial_tab)
    app.mainloop()


if __name__ == "__main__":
    main()
