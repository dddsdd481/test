#!/usr/bin/env python3
"""
Extract text from a DOCX file in sectioned format, preserving Word
equations (OMML) by converting them to LaTeX inline with surrounding text.

Output format (same as extract_docx.py):
    === P{paragraphIndex}.S{sentenceIndex} ===
    {text with LaTeX formulas, no $ delimiters}

Usage:
    python3 extract_docx_math.py C1.docx C1.math.txt

No third-party dependencies required (uses stdlib zipfile + xml.etree).
"""

import sys
import re
import zipfile
import xml.etree.ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
M = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"


# ---------- OMML -> LaTeX ----------

OPERATOR_MAP = {
    "\u2211": r"\sum",
    "\u220F": r"\prod",
    "\u222B": r"\int",
    "\u222C": r"\iint",
    "\u222D": r"\iiint",
    "\u222E": r"\oint",
    "\u22C3": r"\bigcup",
    "\u22C2": r"\bigcap",
    "\u2A00": r"\bigodot",
    "\u2A01": r"\bigoplus",
    "\u2A02": r"\bigotimes",
    "\u2208": r"\in",
    "\u2209": r"\notin",
    "\u2282": r"\subset",
    "\u2286": r"\subseteq",
    "\u2283": r"\supset",
    "\u2287": r"\supseteq",
    "\u00B1": r"\pm",
    "\u2213": r"\mp",
    "\u00D7": r"\times",
    "\u00F7": r"\div",
    "\u2217": r"\ast",
    "\u22C5": r"\cdot",
    "\u2218": r"\circ",
    "\u2260": r"\neq",
    "\u2264": r"\leq",
    "\u2265": r"\geq",
    "\u2248": r"\approx",
    "\u2261": r"\equiv",
    "\u221E": r"\infty",
    "\u2192": r"\rightarrow",
    "\u2190": r"\leftarrow",
    "\u2194": r"\leftrightarrow",
    "\u21D2": r"\Rightarrow",
    "\u21D0": r"\Leftarrow",
    "\u21D4": r"\Leftrightarrow",
    "\u2200": r"\forall",
    "\u2203": r"\exists",
    "\u2202": r"\partial",
    "\u2207": r"\nabla",
    "\u221A": r"\sqrt",
    "\u03B1": r"\alpha", "\u03B2": r"\beta", "\u03B3": r"\gamma",
    "\u03B4": r"\delta", "\u03B5": r"\epsilon", "\u03B6": r"\zeta",
    "\u03B7": r"\eta", "\u03B8": r"\theta", "\u03B9": r"\iota",
    "\u03BA": r"\kappa", "\u03BB": r"\lambda", "\u03BC": r"\mu",
    "\u03BD": r"\nu", "\u03BE": r"\xi", "\u03C0": r"\pi",
    "\u03C1": r"\rho", "\u03C3": r"\sigma", "\u03C4": r"\tau",
    "\u03C5": r"\upsilon", "\u03C6": r"\phi", "\u03C7": r"\chi",
    "\u03C8": r"\psi", "\u03C9": r"\omega",
    "\u0393": r"\Gamma", "\u0394": r"\Delta", "\u0398": r"\Theta",
    "\u039B": r"\Lambda", "\u039E": r"\Xi", "\u03A0": r"\Pi",
    "\u03A3": r"\Sigma", "\u03A6": r"\Phi", "\u03A8": r"\Psi",
    "\u03A9": r"\Omega",
}

NARY_OPS = {
    "\u2211": r"\sum", "\u220F": r"\prod", "\u222B": r"\int",
    "\u222C": r"\iint", "\u222D": r"\iiint", "\u222E": r"\oint",
    "\u22C3": r"\bigcup", "\u22C2": r"\bigcap",
}

ACCENT_MAP = {
    "\u0302": r"\widehat", "^": r"\widehat",
    "\u0303": r"\widetilde", "~": r"\widetilde",
    "\u0304": r"\overline", "\u00AF": r"\overline",
    "\u2192": r"\overrightarrow", "\u20D7": r"\overrightarrow",
    "\u02D9": r"\dot", "\u00B7": r"\dot",
    "\u00A8": r"\ddot",
    "\u030C": r"\check",
    "\u0306": r"\breve",
}


def map_text(s: str) -> str:
    if not s:
        return ""
    out = []
    for ch in s:
        if ch in OPERATOR_MAP:
            tok = OPERATOR_MAP[ch]
            # space-separate latex commands from following letters
            out.append(tok + (" " if tok.startswith("\\") else ""))
        else:
            out.append(ch)
    return "".join(out)


def get_text(elem) -> str:
    """Concatenate all m:t descendants."""
    parts = []
    for t in elem.iter(M + "t"):
        if t.text:
            parts.append(t.text)
    # also include w:t inside math (rare)
    for t in elem.iter(W + "t"):
        if t.text:
            parts.append(t.text)
    return "".join(parts)


def render_children(elem) -> str:
    return "".join(render_node(c) for c in list(elem))


def wrap_brace(s: str) -> str:
    s = s.strip()
    # always brace for safety
    return "{" + s + "}"


def render_node(node) -> str:
    tag = node.tag
    if not tag.startswith(M):
        # ignore non-math children
        return ""
    name = tag[len(M):]

    if name == "r":
        return map_text(get_text(node))

    if name == "t":
        return map_text(node.text or "")

    if name == "f":  # fraction
        num = node.find(M + "num")
        den = node.find(M + "den")
        n = render_children(num) if num is not None else ""
        d = render_children(den) if den is not None else ""
        return r"\frac" + wrap_brace(n) + wrap_brace(d)

    if name == "sSub":
        e = node.find(M + "e")
        sub = node.find(M + "sub")
        base = render_children(e) if e is not None else ""
        s = render_children(sub) if sub is not None else ""
        return wrap_brace(base) + "_" + wrap_brace(s)

    if name == "sSup":
        e = node.find(M + "e")
        sup = node.find(M + "sup")
        base = render_children(e) if e is not None else ""
        s = render_children(sup) if sup is not None else ""
        return wrap_brace(base) + "^" + wrap_brace(s)

    if name == "sSubSup":
        e = node.find(M + "e")
        sub = node.find(M + "sub")
        sup = node.find(M + "sup")
        base = render_children(e) if e is not None else ""
        sb = render_children(sub) if sub is not None else ""
        sp = render_children(sup) if sup is not None else ""
        return wrap_brace(base) + "_" + wrap_brace(sb) + "^" + wrap_brace(sp)

    if name == "sPre":
        e = node.find(M + "e")
        sub = node.find(M + "sub")
        sup = node.find(M + "sup")
        base = render_children(e) if e is not None else ""
        sb = render_children(sub) if sub is not None else ""
        sp = render_children(sup) if sup is not None else ""
        return "{}_" + wrap_brace(sb) + "^" + wrap_brace(sp) + wrap_brace(base)

    if name == "rad":  # radical
        deg = node.find(M + "deg")
        e = node.find(M + "e")
        body = render_children(e) if e is not None else ""
        d = render_children(deg) if deg is not None else ""
        if d.strip():
            return r"\sqrt[" + d + "]" + wrap_brace(body)
        return r"\sqrt" + wrap_brace(body)

    if name == "d":  # delimiter
        pr = node.find(M + "dPr")
        beg, end = "(", ")"
        if pr is not None:
            b = pr.find(M + "begChr")
            e_ = pr.find(M + "endChr")
            if b is not None:
                beg = b.attrib.get(M + "val", beg)
            if e_ is not None:
                end = e_.attrib.get(M + "val", end)
        # collect e children (may be multiple separated by m:sepChr)
        inner_parts = [render_children(e) for e in node.findall(M + "e")]
        inner = ",".join(inner_parts) if len(inner_parts) > 1 else (inner_parts[0] if inner_parts else "")
        # map special braces
        def mapb(c):
            if c == "{": return r"\{"
            if c == "}": return r"\}"
            if c == "|": return "|"
            if c == "": return "."
            return c
        return r"\left" + mapb(beg) + inner + r"\right" + mapb(end)

    if name == "func":  # named function
        fname_el = node.find(M + "fName")
        e = node.find(M + "e")
        fname = render_children(fname_el) if fname_el is not None else ""
        body = render_children(e) if e is not None else ""
        # known functions get backslash form
        plain = fname.strip()
        known = {"sin","cos","tan","cot","sec","csc","log","ln","exp","lim","max","min","arg","det","gcd","lcm","sup","inf"}
        if plain in known:
            return "\\" + plain + wrap_brace(body)
        return fname + wrap_brace(body)

    if name == "fName":
        return render_children(node)

    if name == "limLow":  # base under
        e = node.find(M + "e")
        lim = node.find(M + "lim")
        base = render_children(e) if e is not None else ""
        l = render_children(lim) if lim is not None else ""
        # If base is a known operator like \lim, use _
        return wrap_brace(base) + "_" + wrap_brace(l)

    if name == "limUpp":
        e = node.find(M + "e")
        lim = node.find(M + "lim")
        base = render_children(e) if e is not None else ""
        l = render_children(lim) if lim is not None else ""
        return wrap_brace(base) + "^" + wrap_brace(l)

    if name == "nary":
        pr = node.find(M + "naryPr")
        op = "\u222B"
        if pr is not None:
            chr_el = pr.find(M + "chr")
            if chr_el is not None:
                op = chr_el.attrib.get(M + "val", op)
        sub = node.find(M + "sub")
        sup = node.find(M + "sup")
        e = node.find(M + "e")
        op_tex = NARY_OPS.get(op, map_text(op).strip())
        sb = render_children(sub) if sub is not None else ""
        sp = render_children(sup) if sup is not None else ""
        body = render_children(e) if e is not None else ""
        out = op_tex
        if sb.strip():
            out += "_" + wrap_brace(sb)
        if sp.strip():
            out += "^" + wrap_brace(sp)
        return out + " " + body

    if name == "acc":
        pr = node.find(M + "accPr")
        ch = "\u0302"
        if pr is not None:
            c = pr.find(M + "chr")
            if c is not None:
                ch = c.attrib.get(M + "val", ch)
        e = node.find(M + "e")
        body = render_children(e) if e is not None else ""
        cmd = ACCENT_MAP.get(ch, r"\widehat")
        return cmd + wrap_brace(body)

    if name == "bar":
        pr = node.find(M + "barPr")
        pos = "top"
        if pr is not None:
            p = pr.find(M + "pos")
            if p is not None:
                pos = p.attrib.get(M + "val", pos)
        e = node.find(M + "e")
        body = render_children(e) if e is not None else ""
        return (r"\overline" if pos == "top" else r"\underline") + wrap_brace(body)

    if name == "groupChr":
        e = node.find(M + "e")
        return render_children(e) if e is not None else ""

    if name == "box" or name == "borderBox":
        e = node.find(M + "e")
        return render_children(e) if e is not None else ""

    if name == "m":  # matrix
        rows = []
        for mr in node.findall(M + "mr"):
            cells = [render_children(e) for e in mr.findall(M + "e")]
            rows.append(" & ".join(cells))
        body = " \\\\ ".join(rows)
        return r"\begin{matrix} " + body + r" \end{matrix}"

    if name == "eqArr":
        rows = [render_children(e) for e in node.findall(M + "e")]
        return r"\begin{aligned} " + " \\\\ ".join(rows) + r" \end{aligned}"

    if name in ("e", "num", "den", "sub", "sup", "lim", "deg"):
        return render_children(node)

    # default: walk children
    return render_children(node)


def omml_to_latex(omath_elem) -> str:
    text = render_children(omath_elem)
    # collapse repeated spaces
    text = re.sub(r"[ \t]+", " ", text).strip()
    return text


# ---------- DOCX paragraph extraction ----------

def extract_paragraph_text(p_elem) -> str:
    """Walk a w:p in document order, collecting text and converting math."""
    parts = []

    def walk(elem):
        tag = elem.tag
        # math block or inline
        if tag == M + "oMathPara":
            for om in elem.findall(M + "oMath"):
                latex = omml_to_latex(om)
                if latex:
                    parts.append(latex)
            return
        if tag == M + "oMath":
            latex = omml_to_latex(elem)
            if latex:
                parts.append(latex)
            return
        # plain text run
        if tag == W + "t":
            if elem.text:
                parts.append(elem.text)
            return
        if tag == W + "tab":
            parts.append("\t")
            return
        if tag == W + "br":
            parts.append("\n")
            return
        # recurse into children
        for child in list(elem):
            walk(child)

    walk(p_elem)
    return "".join(parts)


def split_sentences(text: str):
    """Split by . ! ? while keeping LaTeX tokens (\\... and {...}) intact."""
    # Mask backslash-commands and braces to avoid splitting inside them.
    # Simpler: split, but join back if a piece looks unbalanced w.r.t. braces.
    raw = re.split(r"(?<=[\.\!\?])\s+", text)
    out = []
    buf = ""
    depth = 0
    for piece in raw:
        candidate = (buf + " " + piece).strip() if buf else piece
        # update brace depth on the whole candidate vs buf alone
        seg = piece
        depth += seg.count("{") - seg.count("}")
        if depth > 0:
            buf = candidate
        else:
            out.append(candidate)
            buf = ""
            depth = 0
    if buf:
        out.append(buf)
    return [s.strip() for s in out if s.strip()]


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 extract_docx_math.py <input.docx> <output.txt>", file=sys.stderr)
        sys.exit(1)

    src, dst = sys.argv[1], sys.argv[2]

    with zipfile.ZipFile(src) as z:
        with z.open("word/document.xml") as f:
            tree = ET.parse(f)

    root = tree.getroot()
    body = root.find(W + "body")
    if body is None:
        print("No w:body found", file=sys.stderr)
        sys.exit(1)

    lines = []
    p_index = 0
    for p in body.findall(W + "p"):
        text = extract_paragraph_text(p)
        text = text.strip()
        if text:
            sentences = split_sentences(text)
            if not sentences:
                sentences = [text]
            for s_idx, s in enumerate(sentences):
                lines.append(f"=== P{p_index}.S{s_idx} ===")
                lines.append(s)
        p_index += 1

    with open(dst, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Wrote {dst} ({p_index} paragraphs scanned)")


if __name__ == "__main__":
    main()
