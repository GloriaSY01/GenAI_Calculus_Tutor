import assert from 'node:assert/strict'
import test from 'node:test'
import React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { createServer } from 'vite'

test('translation routing checks actual content despite a matching API locale', async () => {
  const server = await createServer({ server: { middlewareMode: true, hmr: false }, appType: 'custom' })
  try {
    const { useTranslatedContent } = await server.ssrLoadModule('/src/useTranslatedContent.js')
    function inspect(text, lang, sourceLang) {
      let result
      function Probe() {
        result = useTranslatedContent([text], lang, sourceLang)
        return null
      }
      renderToStaticMarkup(React.createElement(Probe))
      return result
    }
    // Regression: a saved English stem labelled zh must request translation.
    assert.equal(inspect('Which linear function has slope $6$ and satisfies $f(1)=4$?', 'zh', 'zh').loading, true)
    assert.equal(inspect('求函数的导数。', 'zh', 'zh').loading, false)
    const formula = String.raw`$\frac{x^2}{2}$`
    const pureMath = inspect(formula, 'zh', 'zh')
    assert.equal(pureMath.loading, false)
    assert.equal(pureMath.translate(formula), formula)
    assert.equal(inspect('求函数的导数。', 'en', 'en').loading, true)
    assert.equal(inspect('Find the derivative.', 'en', 'en').loading, false)
  } finally {
    await server.close()
  }
})
