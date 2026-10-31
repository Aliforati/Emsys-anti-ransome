#!/usr/bin/env python3
"""
Emsys Anti-Ransomware Identifier
Examines input files to identify possible ransomware type.
Uses extension matching, ransom note analysis, and file signature detection.
"""

import os
import sys
import re
import argparse
from collections import defaultdict

# Known ransomware database: {extension: [(family, variant, decryptor_url)]}
RANSOMWARE_DB = {
    ".lockbit": [("LockBit", "3.0/4.0", "https://nomoreransom.org/ransomware-lookup/")],
    ".lockbit2": [("LockBit", "2.0", "https://www.emsisoft.com/en/ransomware-decryption/lockbit/")],
    ".sodinokibi": [("REvil/Sodinokibi", None, "https://www.kaspersky.com/resources/free-tools/noransom")],
    ".revil": [("REvil/Sodinokibi", None, "https://www.kaspersky.com/resources/free-tools/noransom")],
    ".dharma": [("Dharma/CrySiS", None, "https://www.emsisoft.com/en/ransomware-decryption/dharma/")],
    ".dh": [("Dharma/CrySiS", None, "https://www.emsisoft.com/en/ransomware-decryption/dharma/")],
    ".crysis": [("Dharma/CrySiS", None, "https://www.emsisoft.com/en/ransomware-decryption/dharma/")],
    ".darkside": [("DarkSide", None, "https://nomoreransom.org/ransomware-lookup/")],
    ".ds": [("DarkSide", None, "https://nomoreransom.org/ransomware-lookup/")],
    ".conti": [("Conti", None, "https://www.kaspersky.com/resources/free-tools/noransom")],
    ".conti2021": [("Conti", "2021", "https://www.kaspersky.com/resources/free-tools/noransom")],
    ".netwalker": [("NetWalker", None, "https://nomoreransom.org/ransomware-lookup/")],
    ".nw": [("NetWalker", None, "https://nomoreransom.org/ransomware-lookup/")],
    ".babuk": [("Babuk", None, "https://www.emsisoft.com/en/ransomware-decryption/babuk/")],
    ".wanna": [("WannaCry", None, "https://www.kaspersky.com/resources/free-tools/noransom")],
    ".wnry": [("WannaCry", None, "https://www.kaspersky.com/resources/free-tools/noransom")],
    ".wncrypt": [("WannaCry", None, "https://www.kaspersky.com/resources/free-tools/noransom")],
    ".petya": [("NotPetya/Petya", None, "https://nomoreransom.org/ransomware-lookup/")],
    ".pete": [("Petya", None, "https://www.emsisoft.com/en/ransomware-decryption/petya/")],
    ".goldeneye": [("GoldenEye", None, "https://nomoreransom.org/ransomware-lookup/")],
    ".ge": [("GoldenEye", None, "https://nomoreransom.org/ransomware-lookup/")],
    ".crypto": [("CryptoLocker", None, "https://www.emsisoft.com/en/ransomware-decryption/cryptolocker/")],
    ".encrypted": [("Generic", None, "https://nomoreransom.org/ransomware-lookup/")],
    ".locked": [("Generic", None, "https://nomoreransom.org/ransomware-lookup/")],
    ".rns": [("Ragnar/Other", None, "https://nomoreransom.org/ransomware-lookup/")],
    ".lock": [("Generic/GandCrab", None, "https://www.emsisoft.com/en/ransomware-decryption/gandcrab/")],
    ".gkrz": [("GandCrab", None, "https://www.emsisoft.com/en/ransomware-decryption/gandcrab/")],
    ".kkk": [("GandCrab", None, "https://www.emsisoft.com/en/ransomware-decryption/gandcrab/")],
    ".zzzzz": [("GandCrab", None, "https://www.emsisoft.com/en/ransomware-decryption/gandcrab/")],
    ".djvu": [("STOP/DjVu", None, "https://www.emsisoft.com/en/ransomware-decryption/stopdjvu/")],
    ".stop": [("STOP/DjVu", None, "https://www.emsisoft.com/en/ransomware-decryption/stopdjvu/")],
    ".zzzzz": [("GandCrab", None, "https://www.emsisoft.com/en/ransomware-decryption/gandcrab/")],
    ".phobos": [("Phobos", None, "https://nomoreransom.org/ransomware-lookup/")],
    ".8base": [("8-Base", None, "https://nomoreransom.org/ransomware-lookup/")],
    ".gentleman": [("The Gentlemen", None, "https://nomoreransom.org/ransomware-lookup/")],
    ".beelzebub": [("Beelzebub", None, "https://www.emsisoft.com/en/ransomware-decryption/beelzebub/")],
}

# Ransom note keywords mapped to families
NOTE_SIGNATURES = {
    "lockbit": ["LockBit", "lockbit3", "lockbit4"],
    "sodinokibi": ["Sodinokibi", "REvil", "revil"],
    "darkside": ["DarkSide", "darkside"],
    "conti": ["Conti", "conti"],
    "netwalker": ["NetWalker", "netwalker"],
    "wanna": ["WannaCry", "wannacry", "WNCRY"],
    "petya": ["Petya", "NotPetya", "pete.exe"],
    "gandcrab": ["GandCrab", "gandcrab"],
    "phobos": ["Phobos", "phobos"],
}


def analyze_extension(filename):
    """Check if file extension matches known ransomware patterns."""
    _, ext = os.path.splitext(filename)
    ext_lower = ext.lower()
    
    # Check exact match first
    if ext_lower in RANSOMWARE_DB:
        return RANSOMWARE_DB[ext_lower]
    
    # Check for common patterns: .ext-id, .ext-[id], etc.
    match = re.match(r'^\.([a-z0-9]+)-', ext_lower)
    if match:
        base_ext = "." + match.group(1)
        if base_ext in RANSOMWARE_DB:
            return [("Possible " + family, variant or "", url) for family, variant, url in RANSOMWARE_DB[base_ext]]
    
    # Check for numeric suffix patterns
    match = re.match(r'^\.([a-z]+)-[0-9a-f]{8,}$', ext_lower)
    if match:
        base_ext = "." + match.group(1)
        if base_ext in RANSOMWARE_DB:
            return [("Possible " + family, variant or "", url) for family, variant, url in RANSOMWARE_DB[base_ext]]
    
    return None


def analyze_ransom_note(filepath):
    """Analyze ransom note content for ransomware signatures."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read().lower()
        
        matches = []
        for family, keywords in NOTE_SIGNATURES.items():
            for keyword in keywords:
                if keyword.lower() in content:
                    matches.append((family, "ransom note keyword: " + keyword))
                    break
        
        return matches
    except (IOError, OSError) as e:
        print(f"Warning: Could not read ransom note '{filepath}': {e}")
        return []


def check_file_magic(filepath):
    """Check file magic bytes for encrypted file signatures."""
    try:
        with open(filepath, 'rb') as f:
            header = f.read(64)
        
        # Check for common encrypted file headers
        if header[:8] == b'\x1a\x07\xa1\x9b\xd3\x50\x5e\x6c':
            return "Possible CryptoLocker (magic bytes detected)"
        
        # High entropy check (encrypted files have high randomness)
        if len(header) >= 16:
            byte_counts = [0] * 256
            for b in header:
                byte_counts[b] += 1
            
            # Simple entropy estimate
            import math
            entropy = 0.0
            for count in byte_counts:
                if count > 0:
                    p = count / len(header)
                    entropy -= p * math.log2(p)
            
            if entropy > 7.5:  # Very high entropy suggests encryption
                return "High entropy detected (possible encryption)"
        
        return None
    except (IOError, OSError):
        return None


def scan_directory(directory):
    """Scan a directory for encrypted files and ransom notes."""
    print(f"\nScanning directory: {directory}")
    print("=" * 60)
    
    extensions_found = defaultdict(list)
    ransom_notes = []
    total_files = 0
    suspicious_files = 0
    
    for root, dirs, files in os.walk(directory):
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
    
    print(f"Total files scanned: {total_files}")
    print(f"Suspicious files found: {suspicious_files}")
    
    # Report extension matches
    if extensions_found:
        print("\n" + "=" * 60)
        print("RANSOMWARE IDENTIFICATION RESULTS")
        print("=" * 60)
        
        for (family, variant), files in extensions_found.items():
            print(f"\nFamily: {family}")
            if variant:
                print(f"Variant: {variant}")
            print(f"Files affected: {len(files)}")
            # Show first few files
            for f in files[:3]:
                print(f"  - {f}")
            if len(files) > 3:
                print(f"  ... and {len(files) - 3} more")
    
    # Analyze ransom notes
    if ransom_notes:
        print("\n" + "=" * 60)
        print("RANSOM NOTE ANALYSIS")
        print("=" * 60)
        
        for note in ransom_notes:
            print(f"\nAnalyzing: {note}")
            matches = analyze_ransom_note(note)
            if matches:
                for family, keyword in matches:
                    print(f"  MATCH: {family} (keyword: {keyword})")
            else:
                print("  No known ransomware signatures found")
    
    # Check magic bytes on first suspicious file
    if extensions_found:
        first_file = list(extensions_found.values())[0][0]
        print(f"\nChecking file signature of: {first_file}")
        magic_result = check_file_magic(first_file)
        if magic_result:
            print(f"  {magic_result}")
    
    return extensions_found, ransom_notes


def identify_single_file(filepath):
    """Identify ransomware type for a single file."""
    print(f"\nAnalyzing file: {filepath}")
    print("=" * 60)
    
    results = []
    
    # Check extension
    ext_result = analyze_extension(filepath)
    if ext_result:
        for family, variant, url in ext_result:
            print(f"Extension match: {family}")
            if variant:
                print(f"  Variant: {variant}")
            print(f"  Decryptor info: {url}")
            results.append((family, variant, "extension"))
    
    # Check if it's a ransom note
    base_name = os.path.splitext(filepath)[0].lower()
    note_names = ['readme', 'decrypt', 'ransom', 'how_to', 'instructions', 'help']
    if any(base_name == name or base_name.startswith(name + '_') for name in note_names):
        print("\nPossible ransom note detected. Analyzing content...")
        matches = analyze_ransom_note(filepath)
        if matches:
            for family, keyword in matches:
                print(f"  Content match: {family} (keyword: {keyword})")
                results.append((family, "", "note content"))
    
    # Check magic bytes
    magic_result = check_file_magic(filepath)
    if magic_result:
        print(f"\nFile signature: {magic_result}")
    
    if not results:
        print("\nNo ransomware signatures identified.")
        print("Try uploading to NoMoreRansom.org's Crypto Sheriff tool:")
        print("https://nomoreransom.org/crypto-sheriff/")
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Emsys Anti-Ransomware Identifier - Identify ransomware type from files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s file.txt              Analyze single file
  %(prog)s /path/to/folder       Scan directory for encrypted files
  %(prog)s --note readme.txt     Analyze ransom note specifically
"""
    )
    parser.add_argument("target", help="File or directory to analyze")
    parser.add_argument("--note", action="store_true", help="Force ransom note analysis mode")
    
    args = parser.parse_args()
    
    print("Emsys Anti-Ransomware Identifier")
    print("Based on NoMoreRansom.org and vendor decryptor databases")
    
    if os.path.isdir(args.target):
        scan_directory(args.target)
    elif os.path.isfile(args.target):
        if args.note:
            matches = analyze_ransom_note(args.target)
            if matches:
                for family, keyword in matches:
                    print(f"MATCH: {family} (keyword: {keyword})")
            else:
                print("No known ransomware signatures found in note.")
        else:
            identify_single_file(args.target)
    else:
        print(f"Error: '{args.target}' does not exist")
        sys.exit(1)


if __name__ == "__main__":
    main()
