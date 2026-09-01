import { useMemo } from 'react'
import katex from 'katex'

/* ============================================================
   Math rendering
   ------------------------------------------------------------
   The backend serves two flavours of math:
     1. Real LaTeX  (mock data + LLM-generated questions):
          \lim_{x\to a} f(x) = L      \frac{a}{b}
     2. Plain-text math (verified textbook content):
          v = (f(t2) - f(t1))/(t2 - t1)     f: domain -> range
   KaTeX only helps flavour (1). Forcing it on flavour (2) makes
   things worse, so we detect LaTeX and otherwise fall back to a
   lightweight prettifier that renders REAL <sup>/<sub> tags
   (not limited Unicode glyphs) + refined typography.
   ============================================================ */

function renderTeX(tex, displayMode) {
  try {
    return katex.renderToString(tex, {
      displayMode,
      throwOnError: false,
      strict: false,
      output: 'htmlAndMathml',
      trust: false,
    })
  } catch {
    return null
  }
}

// Heuristic: does this string contain genuine LaTeX markup?
export function looksLikeLatex(s) {
  return /\\[a-zA-Z]+|\^\{|_\{|\\frac|\\sqrt|\\lim|\\sum|\\int|\\begin/.test(s)
}

const GREEK = {
  alpha: 'α', beta: 'β', gamma: 'γ', delta: 'δ', Delta: 'Δ', epsilon: 'ε',
  theta: 'θ', lambda: 'λ', mu: 'μ', pi: 'π', rho: 'ρ', sigma: 'σ', Sigma: 'Σ',
  tau: 'τ', phi: 'φ', omega: 'ω', Omega: 'Ω', infty: '∞', infinity: '∞',
}

const GREEK_RE = /\b(Delta|Sigma|Omega|alpha|beta|gamma|delta|epsilon|theta|lambda|mu|pi|rho|sigma|tau|phi|omega|infty|infinity)\b/g

// Symbol-level cleanup that does NOT touch ^ _ { } (so script parsing still works).
function prettifySymbols(input) {
  let s = String(input ?? '')

  // greek + named symbols (whole words only)
  s = s.replace(GREEK_RE, (m) => GREEK[m] || m)

  // sqrt(...) -> √(...)
  s = s.replace(/\bsqrt\s*/g, '√')

  // relational / arrow operators
  s = s
    .replace(/<->/g, '↔')
    .replace(/->/g, '→')
    .replace(/<-/g, '←')
    .replace(/<=/g, '≤')
    .replace(/>=/g, '≥')
    .replace(/!=/g, '≠')
    .replace(/~=/g, '≈')
    .replace(/\+-|-\+/g, '±')

  // multiplication dot (only when spaced, to avoid touching markdown emphasis)
  s = s.replace(/ \* /g, ' · ')
  // typographic minus between operands
  s = s.replace(/ - /g, ' − ')

  return s
}

// Normalise implicit subscripts (t2 -> t_{2}) and stray superscript glyphs
// (x² -> x^{2}) into explicit ^{}/_{} so the parser handles them uniformly.
const UNI_SUP = { '⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4', '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9', 'ⁿ': 'n', 'ⁱ': 'i', '⁺': '+', '⁻': '-' }
const UNI_SUB = { '₀': '0', '₁': '1', '₂': '2', '₃': '3', '₄': '4', '₅': '5', '₆': '6', '₇': '7', '₈': '8', '₉': '9', '₊': '+', '₋': '-' }

function normaliseScripts(s) {
  // stray Unicode super/subscript glyphs -> explicit markup
  s = s.replace(/[⁰¹²³⁴⁵⁶⁷⁸⁹ⁿⁱ⁺⁻]+/g, (run) => '^{' + [...run].map((c) => UNI_SUP[c] ?? c).join('') + '}')
  s = s.replace(/[₀₁₂₃₄₅₆₇₈₉₊₋]+/g, (run) => '_{' + [...run].map((c) => UNI_SUB[c] ?? c).join('') + '}')
  // variable followed by 1-2 digits (t2 -> t_{2}), but not part of a longer token
  s = s.replace(/([a-zA-Z])([0-9]{1,2})(?![0-9a-zA-Z_{}])/g, '$1_{$2}')
  return s
}

// Parse a plain-text math string into React nodes with real <sup>/<sub>.
export function prettifyMathNodes(input, keyPrefix = 'm') {
  const s = normaliseScripts(String(input ?? ''))
  const nodes = []
  let buf = ''
  let i = 0
  let k = 0

  const flush = () => {
    if (buf) {
      nodes.push(prettifySymbols(buf))
      buf = ''
    }
  }

  const readArg = (start) => {
    // returns [content, nextIndex] or null
    if (s[start] === '{') {
      const end = s.indexOf('}', start + 1)
      if (end === -1) return null
      return [s.slice(start + 1, end), end + 1]
    }
    const m = /^-?[0-9a-zA-Z+.]+/.exec(s.slice(start))
    if (!m) return null
    return [m[0], start + m[0].length]
  }

  while (i < s.length) {
    const ch = s[i]
    if (ch === '^' || ch === '_') {
      const arg = readArg(i + 1)
      if (arg) {
        flush()
        const Tag = ch === '^' ? 'sup' : 'sub'
        nodes.push(<Tag key={`${keyPrefix}-${k++}`}>{prettifySymbols(arg[0])}</Tag>)
        i = arg[1]
        continue
      }
    }
    buf += ch
    i += 1
  }
  flush()
  return nodes
}

// String-only prettifier kept for callers that need plain text.
export function prettifyMath(input) {
  return prettifySymbols(normaliseScripts(String(input ?? '')).replace(/[\^_]\{([^}]*)\}/g, '$1').replace(/[\^_](-?[0-9a-zA-Z+.]+)/g, '$1'))
}

/* Block-level formula (one entry from a `formulas` array). */
export function Formula({ children }) {
  const raw = String(children ?? '')
  const html = useMemo(() => (looksLikeLatex(raw) ? renderTeX(raw, true) : null), [raw])
  const nodes = useMemo(() => (html == null ? prettifyMathNodes(raw, 'f') : null), [raw, html])
  if (html != null) {
    return <div className="formula formula-tex" dangerouslySetInnerHTML={{ __html: html }} />
  }
  return <div className="formula formula-plain">{nodes}</div>
}

/* Rich text that may embed inline/display math via delimiters.
   Text outside delimiters keeps its prose but still gets light math
   prettifying so stray ^ / _ / t2 render as proper super/subscripts. */
const DELIM_RE = /\$\$([\s\S]+?)\$\$|\\\[([\s\S]+?)\\\]|\\\(([\s\S]+?)\\\)|\$([^$\n]+?)\$/g

export function MathText({ children, as: Tag = 'span', ...rest }) {
  const text = String(children ?? '')
  const parts = useMemo(() => {
    const out = []
    let last = 0
    let m
    DELIM_RE.lastIndex = 0
    while ((m = DELIM_RE.exec(text)) !== null) {
      if (m.index > last) out.push({ t: 'text', v: text.slice(last, m.index) })
      const display = m[1] != null || m[2] != null
      const tex = m[1] ?? m[2] ?? m[3] ?? m[4] ?? ''
      out.push({ t: 'math', v: tex, display, raw: m[0] })
      last = m.index + m[0].length
    }
    if (last < text.length) out.push({ t: 'text', v: text.slice(last) })
    return out
  }, [text])

  return (
    <Tag {...rest}>
      {parts.map((p, i) => {
        if (p.t === 'text') return <span key={i} className="math-plain-inline">{prettifyMathNodes(p.v, `t${i}`)}</span>
        const html = renderTeX(p.v, p.display)
        if (html == null) return <span key={i}>{p.raw}</span>
        return (
          <span
            key={i}
            className={p.display ? 'katex-display-wrap' : 'katex-inline'}
            dangerouslySetInnerHTML={{ __html: html }}
          />
        )
      })}
    </Tag>
  )
}
