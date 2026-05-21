#!/usr/bin/env node
/**
 * extract_docx_math.js
 *
 * Extract text from a .docx, converting Word equations (OMML / m:oMath)
 * to LaTeX inline with surrounding text. Output uses the same sectioned
 * format as the previous script:
 *
 *   === P{paragraphIndex}.S{sentenceIndex} ===
 *   {text}
 *
 * Usage:  node extract_docx_math.js <input.docx> [output.txt]
 *
 * Dependencies: adm-zip, fast-xml-parser
 */

const fs = require("fs")
const path = require("path")
const AdmZip = require("adm-zip")
const { XMLParser } = require("fast-xml-parser")

// ---------- OMML -> LaTeX ----------
// Walks an OMML subtree (in preserveOrder form from fast-xml-parser) and
// emits a LaTeX string. Covers the common Word equation constructs.

function tagOf(node) {
  // preserveOrder nodes look like { "m:r": [...], ":@": {...} }
  // We return the first key that isn't ":@".
  for (const k of Object.keys(node)) {
    if (k !== ":@") return k
  }
  return null
}

function childrenOf(node) {
  const t = tagOf(node)
  if (!t) return []
  const v = node[t]
  return Array.isArray(v) ? v : []
}

function textOf(node) {
  // For #text nodes
  if (node["#text"] !== undefined) return String(node["#text"])
  return ""
}

// Render a sequence of OMML children
function renderOmmlChildren(children) {
  let out = ""
  for (const child of children) {
    out += renderOmml(child)
  }
  return out
}

// Find the first child with a given tag
function findChild(children, tag) {
  return children.find((c) => tagOf(c) === tag)
}

// Render a single OMML node
function renderOmml(node) {
  const tag = tagOf(node)
  if (!tag) {
    // text-only node
    return escapeLatexText(textOf(node))
  }
  const kids = childrenOf(node)

  switch (tag) {
    case "#text":
      return escapeLatexText(textOf(node))

    case "m:t": {
      // Math text run
      const inner = kids.map((c) => textOf(c)).join("")
      return mapMathSymbols(inner)
    }

    case "m:r": {
      // Math run: concatenate any m:t inside
      let s = ""
      for (const c of kids) {
        if (tagOf(c) === "m:t") s += renderOmml(c)
        else if (tagOf(c) === "m:rPr") {
          // ignore
        } else {
          s += renderOmml(c)
        }
      }
      return s
    }

    case "m:e":
    case "m:num":
    case "m:den":
    case "m:sub":
    case "m:sup":
    case "m:deg":
    case "m:lim":
    case "m:fName":
      return renderOmmlChildren(kids)

    case "m:sSub": {
      const e = findChild(kids, "m:e")
      const sub = findChild(kids, "m:sub")
      return `${wrapBraces(renderOmml(e))}_${wrapBraces(renderOmml(sub))}`
    }
    case "m:sSup": {
      const e = findChild(kids, "m:e")
      const sup = findChild(kids, "m:sup")
      return `${wrapBraces(renderOmml(e))}^${wrapBraces(renderOmml(sup))}`
    }
    case "m:sSubSup": {
      const e = findChild(kids, "m:e")
      const sub = findChild(kids, "m:sub")
      const sup = findChild(kids, "m:sup")
      return `${wrapBraces(renderOmml(e))}_${wrapBraces(renderOmml(sub))}^${wrapBraces(renderOmml(sup))}`
    }
    case "m:sPre": {
      const sub = findChild(kids, "m:sub")
      const sup = findChild(kids, "m:sup")
      const e = findChild(kids, "m:e")
      return `{}_${wrapBraces(renderOmml(sub))}^${wrapBraces(renderOmml(sup))}${wrapBraces(renderOmml(e))}`
    }

    case "m:f": {
      const num = findChild(kids, "m:num")
      const den = findChild(kids, "m:den")
      return `\\frac{${renderOmml(num)}}{${renderOmml(den)}}`
    }

    case "m:rad": {
      const deg = findChild(kids, "m:deg")
      const e = findChild(kids, "m:e")
      const degStr = deg ? renderOmml(deg).trim() : ""
      if (degStr) return `\\sqrt[${degStr}]{${renderOmml(e)}}`
      return `\\sqrt{${renderOmml(e)}}`
    }

    case "m:d": {
      // delimiter: read m:dPr begChr/endChr if present
      const dPr = findChild(kids, "m:dPr")
      let beg = "("
      let end = ")"
      if (dPr) {
        const dKids = childrenOf(dPr)
        const begChr = findChild(dKids, "m:begChr")
        const endChr = findChild(dKids, "m:endChr")
        if (begChr && begChr[":@"] && begChr[":@"]["@_m:val"] !== undefined)
          beg = begChr[":@"]["@_m:val"]
        if (endChr && endChr[":@"] && endChr[":@"]["@_m:val"] !== undefined)
          end = endChr[":@"]["@_m:val"]
      }
      // Render all m:e children, separated by sep (default "|")
      const inner = kids
        .filter((c) => tagOf(c) === "m:e")
        .map((c) => renderOmml(c))
        .join(",")
      return `\\left${latexDelim(beg)}${inner}\\right${latexDelim(end)}`
    }

    case "m:func": {
      const fName = findChild(kids, "m:fName")
      const e = findChild(kids, "m:e")
      const name = fName ? renderOmml(fName) : ""
      return `${name}\\left(${e ? renderOmml(e) : ""}\\right)`
    }

    case "m:acc": {
      const e = findChild(kids, "m:e")
      const accPr = findChild(kids, "m:accPr")
      let chr = "\u0302" // default hat
      if (accPr) {
        const ck = findChild(childrenOf(accPr), "m:chr")
        if (ck && ck[":@"] && ck[":@"]["@_m:val"]) chr = ck[":@"]["@_m:val"]
      }
      const cmd = accentCommand(chr)
      return `${cmd}{${renderOmml(e)}}`
    }

    case "m:bar": {
      const e = findChild(kids, "m:e")
      const barPr = findChild(kids, "m:barPr")
      let pos = "top"
      if (barPr) {
        const pk = findChild(childrenOf(barPr), "m:pos")
        if (pk && pk[":@"] && pk[":@"]["@_m:val"]) pos = pk[":@"]["@_m:val"]
      }
      return pos === "bot"
        ? `\\underline{${renderOmml(e)}}`
        : `\\overline{${renderOmml(e)}}`
    }

    case "m:nary": {
      const naryPr = findChild(kids, "m:naryPr")
      let chr = "\u222B" // integral default
      if (naryPr) {
        const ck = findChild(childrenOf(naryPr), "m:chr")
        if (ck && ck[":@"] && ck[":@"]["@_m:val"]) chr = ck[":@"]["@_m:val"]
      }
      const op = naryOperator(chr)
      const sub = findChild(kids, "m:sub")
      const sup = findChild(kids, "m:sup")
      const e = findChild(kids, "m:e")
      let s = op
      if (sub) s += `_{${renderOmml(sub)}}`
      if (sup) s += `^{${renderOmml(sup)}}`
      s += `${e ? renderOmml(e) : ""}`
      return s
    }

    case "m:limLow": {
      const e = findChild(kids, "m:e")
      const lim = findChild(kids, "m:lim")
      return `\\underset{${lim ? renderOmml(lim) : ""}}{${e ? renderOmml(e) : ""}}`
    }
    case "m:limUpp": {
      const e = findChild(kids, "m:e")
      const lim = findChild(kids, "m:lim")
      return `\\overset{${lim ? renderOmml(lim) : ""}}{${e ? renderOmml(e) : ""}}`
    }

    case "m:m": {
      // matrix
      const rows = kids
        .filter((c) => tagOf(c) === "m:mr")
        .map((row) =>
          childrenOf(row)
            .filter((c) => tagOf(c) === "m:e")
            .map((c) => renderOmml(c))
            .join(" & "),
        )
      return `\\begin{matrix}${rows.join(" \\\\ ")}\\end{matrix}`
    }

    case "m:groupChr":
    case "m:box":
    case "m:borderBox":
    case "m:phant": {
      const e = findChild(kids, "m:e")
      return e ? renderOmml(e) : ""
    }

    case "m:eqArr": {
      const lines = kids
        .filter((c) => tagOf(c) === "m:e")
        .map((c) => renderOmml(c))
      return `\\begin{aligned}${lines.join(" \\\\ ")}\\end{aligned}`
    }

    // Skip property/markup-only nodes
    case "m:rPr":
    case "m:ctrlPr":
    case "m:dPr":
    case "m:fPr":
    case "m:radPr":
    case "m:sSubPr":
    case "m:sSupPr":
    case "m:sSubSupPr":
    case "m:funcPr":
    case "m:naryPr":
    case "m:barPr":
    case "m:accPr":
    case "m:limLowPr":
    case "m:limUppPr":
    case "m:mPr":
    case "m:eqArrPr":
    case "m:groupChrPr":
    case "m:boxPr":
    case "m:borderBoxPr":
    case "m:phantPr":
      return ""

    default:
      // Fallback: render any children
      return renderOmmlChildren(kids)
  }
}

function wrapBraces(s) {
  if (s === undefined || s === null) return "{}"
  // Always wrap to be safe; LaTeX engines tolerate extra braces.
  return `{${s}}`
}

function escapeLatexText(s) {
  // Inside math, plain text should usually be wrapped in \text{}.
  // But for inline letters/numbers from m:t, we usually want them raw.
  // We keep raw and only escape backslashes/braces minimally.
  return s.replace(/\\/g, "\\backslash ").replace(/\{/g, "\\{").replace(/\}/g, "\\}")
}

// Map common Unicode math chars in m:t to LaTeX-friendly equivalents.
function mapMathSymbols(s) {
  const map = {
    "×": "\\times ",
    "÷": "\\div ",
    "−": "-",
    "·": "\\cdot ",
    "≤": "\\le ",
    "≥": "\\ge ",
    "≠": "\\ne ",
    "≈": "\\approx ",
    "→": "\\to ",
    "∞": "\\infty ",
    "π": "\\pi ",
    "θ": "\\theta ",
    "α": "\\alpha ",
    "β": "\\beta ",
    "γ": "\\gamma ",
    "δ": "\\delta ",
    "λ": "\\lambda ",
    "μ": "\\mu ",
    "σ": "\\sigma ",
    "Σ": "\\Sigma ",
    "Δ": "\\Delta ",
    "∑": "\\sum ",
    "∫": "\\int ",
    "∏": "\\prod ",
    "∂": "\\partial ",
    "∇": "\\nabla ",
    "√": "\\sqrt ",
    "±": "\\pm ",
    "∈": "\\in ",
    "∉": "\\notin ",
    "⊂": "\\subset ",
    "⊃": "\\supset ",
    "∪": "\\cup ",
    "∩": "\\cap ",
  }
  let out = ""
  for (const ch of s) {
    out += map[ch] !== undefined ? map[ch] : ch
  }
  return out
}

function latexDelim(c) {
  if (!c) return "."
  if (c === "{") return "\\{"
  if (c === "}") return "\\}"
  if (c === "|") return "|"
  if (c === "(" || c === ")" || c === "[" || c === "]") return c
  return c
}

function accentCommand(chr) {
  // Map common combining/standalone accent chars to LaTeX commands.
  switch (chr) {
    case "\u0302":
    case "^":
      return "\\widehat"
    case "\u00AF":
    case "\u0304":
      return "\\overline"
    case "\u0303":
    case "~":
      return "\\widetilde"
    case "\u02D9":
    case "\u0307":
      return "\\dot"
    case "\u00A8":
    case "\u0308":
      return "\\ddot"
    case "\u20D7":
    case "\u2192":
      return "\\vec"
    default:
      return "\\widehat"
  }
}

function naryOperator(chr) {
  switch (chr) {
    case "\u2211":
      return "\\sum"
    case "\u220F":
      return "\\prod"
    case "\u2210":
      return "\\coprod"
    case "\u222B":
      return "\\int"
    case "\u222C":
      return "\\iint"
    case "\u222D":
      return "\\iiint"
    case "\u222E":
      return "\\oint"
    case "\u22C3":
      return "\\bigcup"
    case "\u22C2":
      return "\\bigcap"
    default:
      return "\\sum"
  }
}

// ---------- Document walking ----------
// Walk a paragraph in document order, emitting plain text from w:t runs and
// LaTeX (wrapped in $...$ or $$...$$) from m:oMath / m:oMathPara.

function walkParagraph(pNode) {
  // pNode is a preserveOrder node like { "w:p": [children], ":@": {...} }
  const children = childrenOf(pNode)
  let out = ""
  for (const child of children) {
    out += walkInline(child)
  }
  // Collapse runs of whitespace but preserve single newlines from <w:br/>
  out = out.replace(/[ \t]+/g, " ").replace(/\s*\n\s*/g, "\n")
  return out.trim()
}

function walkInline(node) {
  const tag = tagOf(node)
  if (!tag) return ""
  const kids = childrenOf(node)

  if (tag === "w:r") {
    let s = ""
    for (const c of kids) {
      const ct = tagOf(c)
      if (ct === "w:t") {
        const text = childrenOf(c)
          .map((x) => textOf(x))
          .join("")
        s += text
      } else if (ct === "w:tab") {
        s += "\t"
      } else if (ct === "w:br" || ct === "w:cr") {
        s += "\n"
      } else if (ct === "w:noBreakHyphen") {
        s += "-"
      }
    }
    return s
  }

  if (tag === "m:oMath") {
    const latex = renderOmmlChildren(kids).trim()
    if (!latex) return ""
    return ` $${latex}$ `
  }

  if (tag === "m:oMathPara") {
    // Block math: render any inner m:oMath as $$...$$
    let pieces = []
    for (const c of kids) {
      if (tagOf(c) === "m:oMath") {
        const inner = renderOmmlChildren(childrenOf(c)).trim()
        if (inner) pieces.push(inner)
      }
    }
    if (!pieces.length) return ""
    return `\n$$${pieces.join(" ")}$$\n`
  }

  if (tag === "w:hyperlink" || tag === "w:smartTag" || tag === "w:sdt" || tag === "w:sdtContent" || tag === "mc:AlternateContent" || tag === "mc:Choice" || tag === "mc:Fallback") {
    // Recurse into containers that may hold more runs / math
    let s = ""
    for (const c of kids) s += walkInline(c)
    return s
  }

  if (tag === "w:ins" || tag === "w:del") {
    // Track changes containers; recurse but skip deletions
    if (tag === "w:del") return ""
    let s = ""
    for (const c of kids) s += walkInline(c)
    return s
  }

  // Property nodes etc.
  return ""
}

// Sentence splitter mirroring the previous script: split on . ! ? boundaries
function splitSentences(text) {
  if (!text) return []
  // Keep math segments intact: temporarily replace $...$ blocks
  const placeholders = []
  const protectedText = text.replace(/\$\$[\s\S]*?\$\$|\$[^$\n]*\$/g, (m) => {
    placeholders.push(m)
    return `\u0001${placeholders.length - 1}\u0001`
  })
  const parts = protectedText
    .split(/(?<=[.!?])\s+(?=[A-Z\u0001])/)
    .map((s) => s.trim())
    .filter(Boolean)
  return parts.map((p) =>
    p.replace(/\u0001(\d+)\u0001/g, (_, i) => placeholders[Number(i)]),
  )
}

// ---------- Main ----------
function main() {
  const [, , inPath, outPathArg] = process.argv
  if (!inPath) {
    console.error("Usage: node extract_docx_math.js <input.docx> [output.txt]")
    process.exit(1)
  }
  const outPath =
    outPathArg ||
    path.join(
      path.dirname(inPath),
      path.basename(inPath, path.extname(inPath)) + ".math.txt",
    )

  const zip = new AdmZip(inPath)
  const entry = zip.getEntry("word/document.xml")
  if (!entry) {
    console.error("word/document.xml not found in", inPath)
    process.exit(1)
  }
  const xml = entry.getData().toString("utf8")

  const parser = new XMLParser({
    ignoreAttributes: false,
    attributeNamePrefix: "@_",
    preserveOrder: true,
    trimValues: false,
    parseTagValue: false,
    parseAttributeValue: false,
  })
  const tree = parser.parse(xml)

  // Find w:document -> w:body
  function find(nodes, name) {
    for (const n of nodes) {
      if (tagOf(n) === name) return n
    }
    return null
  }

  const docNode = find(tree, "w:document")
  if (!docNode) {
    console.error("No w:document found")
    process.exit(1)
  }
  const body = find(childrenOf(docNode), "w:body")
  if (!body) {
    console.error("No w:body found")
    process.exit(1)
  }

  const lines = []
  let pIndex = 0
  for (const node of childrenOf(body)) {
    const tag = tagOf(node)
    if (tag === "w:p") {
      const text = walkParagraph(node)
      if (text) {
        const sentences = splitSentences(text)
        if (sentences.length === 0) {
          lines.push(`=== P${pIndex}.S0 ===`)
          lines.push(text)
        } else {
          sentences.forEach((s, i) => {
            lines.push(`=== P${pIndex}.S${i} ===`)
            lines.push(s)
          })
        }
      }
      pIndex++
    } else if (tag === "w:tbl") {
      // Walk paragraphs inside tables too
      const stack = [node]
      while (stack.length) {
        const cur = stack.pop()
        for (const c of childrenOf(cur)) {
          if (tagOf(c) === "w:p") {
            const text = walkParagraph(c)
            if (text) {
              const sentences = splitSentences(text)
              if (sentences.length === 0) {
                lines.push(`=== P${pIndex}.S0 ===`)
                lines.push(text)
              } else {
                sentences.forEach((s, i) => {
                  lines.push(`=== P${pIndex}.S${i} ===`)
                  lines.push(s)
                })
              }
            }
            pIndex++
          } else {
            stack.push(c)
          }
        }
      }
    } else {
      // Other body-level nodes: skip but still advance? Match previous script:
      // it counted only paragraphs, so do not increment for non-paragraph nodes.
    }
  }

  fs.writeFileSync(outPath, lines.join("\n") + "\n", "utf8")
  console.log(`Wrote ${outPath} (${pIndex} paragraphs scanned)`)
}

main()
