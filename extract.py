#!/usr/bin/env python3
"""Extract text from a .docx file in 'P{paragraph}.S{sentence}' format."""
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def extract_paragraphs(docx_path):
    with zipfile.ZipFile(docx_path) as z:
        with z.open("word/document.xml") as f:
            tree = ET.parse(f)
    root = tree.getroot()
    paragraphs = []
    for p in root.iter(f"{{{NS['w']}}}p"):
        texts = []
        for node in p.iter():
            tag = node.tag.split("}", 1)[-1]
            if tag == "t" and node.text:
                texts.append(node.text)
            elif tag == "tab":
                texts.append("\t")
            elif tag == "br":
                texts.append("\n")
        paragraphs.append("".join(texts))
    return paragraphs


def split_sentences(text):
    text = text.strip()
    if not text:
        return []
    # Split on sentence-ending punctuation followed by whitespace.
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in parts if s.strip()]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "C1.docx"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "C1.txt"
    paragraphs = extract_paragraphs(path)
    lines = []
    for p_idx, para in enumerate(paragraphs):
        sentences = split_sentences(para)
        for s_idx, sent in enumerate(sentences):
            lines.append(f"=== P{p_idx}.S{s_idx} ===")
            lines.append(sent)
    output = "\n".join(lines) + "\n"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(output)
    print(f"Wrote {out_path} ({len(paragraphs)} paragraphs)")


if __name__ == "__main__":
    main()
