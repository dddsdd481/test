#!/usr/bin/env python3
"""
Extract text from DOCX file and format as P{page}.S{sentence}

Features:
- Intelligent sentence splitting with abbreviation handling
- Avoids splitting on common abbreviations (Mr., Dr., etc.)
- Handles decimal numbers and special punctuation
"""

import re
import sys
from pathlib import Path
from typing import List
from docx import Document

# Find candidate sentence boundaries: punctuation (. ! ?) followed by whitespace
# and a capital letter / digit / opening quote.
_BOUNDARY_RE = re.compile(r'([.!?]["\')\]]?)\s+(?=[A-Z0-9"\'(\[])')

# Common abbreviations that should NOT end a sentence even though they end in '.'
ABBREVIATIONS = {
    "mr", "mrs", "ms", "dr", "sr", "jr", "st", "vs", "etc",
    "e.g", "i.e", "fig", "no", "vol", "eq", "approx", "inc", "ltd",
    "prof", "rev", "hon", "gen", "col", "maj", "capt", "lt", "sgt",
}


def split_sentences(text: str) -> List[str]:
    """
    Split a paragraph into sentences while avoiding common abbreviations.
    
    Args:
        text: Input paragraph text
        
    Returns:
        List of sentences
    """
    text = text.strip()
    if not text:
        return []
    
    sentences: List[str] = []
    buf = ""
    last = 0
    
    for m in _BOUNDARY_RE.finditer(text):
        end = m.end()
        chunk = text[last:m.end(1)]  # include the punctuation
        candidate = (buf + chunk).strip()
        
        # Get the last "word" before the punctuation to check abbreviation list
        last_word = re.split(r"[\s]", candidate.rstrip(".!?\"')]"))[-1].lower()
        
        if last_word in ABBREVIATIONS:
            buf = buf + text[last:end]  # keep accumulating, not a real boundary
        else:
            sentences.append(candidate)
            buf = ""
        
        last = end
    
    tail = (buf + text[last:]).strip()
    if tail:
        sentences.append(tail)
    
    return sentences


def extract(docx_path: Path) -> str:
    """
    Extract text from DOCX and format as === P{page}.S{sentence} ===
    
    Args:
        docx_path: Path to DOCX file
        
    Returns:
        Formatted text output
    """
    doc = Document(str(docx_path))
    lines: List[str] = []
    
    for p_idx, paragraph in enumerate(doc.paragraphs):
        text = paragraph.text.strip()
        
        if not text:
            continue
        
        # Split into sentences
        sentences = split_sentences(text)
        
        # Add each sentence with P{page}.S{sentence} format
        for s_idx, sentence in enumerate(sentences):
            if sentence:
                lines.append(f"=== P{p_idx}.S{s_idx} ===")
                lines.append(sentence)
    
    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 extract_docx.py <input.docx> [output.txt]")
        print("\nExample:")
        print("  python3 extract_docx.py C1.docx output.txt")
        sys.exit(1)
    
    docx_path = Path(sys.argv[1])
    
    if not docx_path.exists():
        print(f"Error: File not found: {docx_path}", file=sys.stderr)
        sys.exit(1)
    
    output = extract(docx_path)
    
    if len(sys.argv) >= 3:
        out_path = Path(sys.argv[2])
        out_path.write_text(output, encoding="utf-8")
        print(f"✓ Wrote {out_path} ({output.count(chr(10))} lines)")
    else:
        sys.stdout.write(output)


if __name__ == "__main__":
    main()