import { useEffect, useState } from 'react'
import { translateTexts } from './api.js'
import textbookLabels from './textbook-labels.json'
import textbookChinese from './textbook-zh.json'
const cache = new Map()
const pending = new Map()
export function useTranslatedContent(texts, lang) {
  const values = [...new Set(texts.filter(v => typeof v === 'string' && v.trim()))]
  const key = JSON.stringify([lang, values])
  const [, setRevision] = useState(0)
  const [failed, setFailed] = useState('')
  const [attempt, setAttempt] = useState(0)
  const known = value => {
    if (!value) return value
    if (lang === 'en' && !/[\u4e00-\u9fff]/.test(value)) return value
    if (lang === 'zh' && (textbookLabels[value] || textbookChinese[value])) return textbookLabels[value] || textbookChinese[value]
    const prose = value.replace(/\$\$[\s\S]*?\$\$|\$(?:\\.|[^$])*?\$/g, '')
    if (lang === 'zh' && !/[a-zA-Z]/.test(prose)) return value
    if (!/[a-zA-Z\u4e00-\u9fff]/.test(prose)) return value
    return cache.get(JSON.stringify([lang, value]))
  }
  const missing = values.filter(v => known(v) === undefined)
  useEffect(() => {
    let active = true
    if (!missing.length) return
    setFailed('')
    if (!pending.has(key)) {
      pending.set(key, (async () => {
        for (let i = 0; i < missing.length; i += 20) {
          const batch = missing.slice(i, i + 20)
          const result = await translateTexts(batch, lang)
          for (const original of batch) {
            if (typeof result.translations?.[original] !== 'string') throw new Error('Incomplete translation')
            cache.set(JSON.stringify([lang, original]), result.translations[original])
          }
        }
      })().finally(() => pending.delete(key)))
    }
    pending.get(key).then(() => { if (active) setRevision(n => n + 1) }).catch(() => { if (active) setFailed(key) })
    return () => { active = false }
  }, [key, attempt])
  return { translate: value => known(value) ?? (lang === 'zh' ? '正在翻译…' : 'Translating…'), loading: missing.length > 0 && failed !== key, error: failed === key, retry: () => setAttempt(n => n + 1) }
}
export function conceptTexts(card) {
  if (!card) return []
  return [card.title, card.chapter, card.summary, card.definition, card.example, card.pitfalls,
    ...(card.content || []).flatMap(b => [b.heading, b.text, ...(b.figures || []).flatMap(f => [f.caption, f.figure_number])])]
}
