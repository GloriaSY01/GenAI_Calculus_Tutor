import fs from 'node:fs'
import assert from 'node:assert/strict'
import katex from 'katex'

const root = new URL('../../data/textbook/mit-calculus/', import.meta.url)
const read = name => JSON.parse(fs.readFileSync(new URL(name, root), 'utf8'))
const rows = read('verified_content.json')
const overrides = { ...read('formula_overrides.json'), ...read('formula_overrides_remaining.json') }
const texts = read('text_overrides.json')
let count = 0
for (const row of rows) {
  const formulas = overrides[row.id]
  assert.ok(formulas, `Missing formulas for ${row.id}`)
  assert.equal(formulas.length, row.formulas.length, row.id)
  for (const tex of formulas) {
    katex.renderToString(tex, { throwOnError: true, strict: 'error', displayMode: true, trust: false })
    count++
  }
}
let inline = 0
for (const [id, text] of Object.entries(texts)) {
  assert.ok(rows.some(row => row.id === id), id)
  const formulas = [...text.matchAll(/\\\(([\s\S]*?)\\\)/g)]
  for (const [, tex] of formulas) {
    katex.renderToString(tex, { throwOnError: true, strict: 'error', trust: false })
    inline++
  }
  assert.equal((text.match(/\\\(/g) || []).length, formulas.length, id)
  assert.equal((text.match(/\\\)/g) || []).length, formulas.length, id)
}
console.log(`${rows.length} blocks, ${count} display formulas and ${inline} inline formulas passed strict KaTeX validation`)
