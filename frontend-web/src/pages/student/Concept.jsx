import { useTranslatedContent, conceptTexts } from '../../useTranslatedContent.js'
import { useEffect, useState } from 'react'
import { useLang } from '../../i18n.jsx'
import { api } from '../../api.js'
import { Card, Loading, MockPill } from '../../components/ui.jsx'
import { Formula, MathText } from '../../components/math.jsx'

export default function Concept({ topic, onAskTutor, onStartPractice, embedded = false }) {
  const { t, lang } = useLang()
  const [loading, setLoading] = useState(true)
  const [card, setCard] = useState(null)
  const [mock, setMock] = useState(false)

  useEffect(() => {
    let alive = true
    setLoading(true)
    api.getConcept(topic).then((c) => {
      if (!alive) return
      setCard(c); setMock(!!c._mock); setLoading(false)
    })
    return () => { alive = false }
  }, [topic])

  const translated = useTranslatedContent(conceptTexts(card), lang)
  const tr = translated.translate
  if (translated.error) return <p role="alert">{lang === 'zh' ? '教材翻译暂不可用。' : 'Textbook translation unavailable.'} <button className="btn" onClick={translated.retry}>{lang === 'zh' ? '重试' : 'Retry'}</button></p>
  if (loading || translated.loading) return <Loading rows={3} />
  if (!card) return null

  const blocks = card.content || []

  return (
    <div className="stack fade-in">
      <div className="row" style={{ justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div className="section-step">{t('stage_concept')}</div>
          <h2 className="section-head">{tr(card.title || topic)}</h2>
          {card.chapter && <p className="muted" style={{ margin: '4px 0 0' }}>{tr(card.chapter)}</p>}
        </div>
        <MockPill show={mock} />
      </div>

      {mock && <div className="note-tip">{t('concept_unavailable')}</div>}

      {!mock && <div className="note-tip">{lang === 'zh' ? '正文与图注为中文译文；插图保留教材原图，图内文字可能为英文。' : 'Textbook notes and captions in English; figures retain their original labels.'}</div>}
      <Card>
        <div className="stack" style={{ gap: 18 }}>
          {!blocks.length && card.summary && <MathText as="p" style={{ margin: 0, fontSize: 15, lineHeight: 1.7 }}>{tr(card.summary)}</MathText>}

          {blocks.length > 0 ? blocks.map((b) => (
            <div key={b.id} className={'concept-block' + (b.subtype === 'illustrated_concept' ? ' concept-illustrated' : '')}>
              <div className="concept-block-kind">{tr(b.heading) || b.subtype}</div>
              {b.text && <MathText as="p" style={{ margin: '6px 0', lineHeight: 1.7 }}>{tr(b.text)}</MathText>}
              {(b.formulas || []).map((f, i) => (
                <Formula key={i}>{f}</Formula>
              ))}
              {(b.figures || []).some(fig => fig.available === false) && <p className="muted">{t("figure_missing")}</p>}
              {(b.figures || []).filter(fig => fig.available !== false).map((fig) => (
                <figure key={fig.id} style={{ margin: '10px 0' }}>
                  <a href={fig.url} target="_blank" rel="noreferrer"><TextbookImage fig={{ ...fig, caption: tr(fig.caption) }} style={{ maxWidth: '100%', maxHeight: 420, objectFit: 'contain', borderRadius: 12, border: '1px solid var(--border)', background: '#fff' }} /></a>
                  {(fig.figure_number || fig.caption) && (
                    <figcaption className="muted" style={{ fontSize: 12.5, marginTop: 4 }}>
                      {[tr(fig.figure_number), tr(fig.caption)].filter(Boolean).join(' — ')}
                    </figcaption>
                  )}
                </figure>
              ))}
              {b.printed_page != null && <div className="muted" style={{ fontSize: 12 }}>p.{b.printed_page}</div>}
            </div>
          )) : (
            <div className="stack" style={{ gap: 14 }}>
              {card.definition && <ConceptSection title={t('concept_definition')} text={tr(card.definition)} formulas={card.formulas} />}
              {card.example && <ConceptSection title={t('concept_example')} text={tr(card.example)} />}
              {card.pitfalls && <ConceptSection title={t('concept_pitfalls')} text={tr(card.pitfalls)} />}
            </div>
          )}

          {(card.source || card.source_url || card.publisher || card.license) && (
            <div className="concept-source">
              <span className="muted" style={{ fontWeight: 700 }}>{t('concept_source')}:</span>{' '}
              {card.source_url
                ? <a href={card.source_url} target="_blank" rel="noreferrer" style={{ color: 'var(--brand-600)' }}>{lang === 'zh' ? 'MIT《微积分》— 吉尔伯特·斯特朗' : (card.source || card.publisher || card.source_url)}</a>
                : (card.source || card.publisher)}
              {card.license && <span className="muted"> · {card.license}</span>}
            </div>
          )}
        </div>
      </Card>

      {!embedded && <div className="cta-bar">
        <button className="btn" onClick={onAskTutor}>💬 {t('concept_ask_tutor')}</button>
        <div className="spacer" />
        <button className="btn primary" onClick={onStartPractice}>{t('concept_start_practice')} →</button>
      </div>}
    </div>
  )
}

function ConceptSection({ title, text, formulas }) {
  return (
    <div className="concept-block">
      <div className="concept-block-kind">{title}</div>
      <MathText as="p" style={{ margin: '6px 0', lineHeight: 1.7 }}>{text}</MathText>
      {(formulas || []).map((f, i) => <Formula key={i}>{f}</Formula>)}
    </div>
  )
}

function TextbookImage({ fig, style }) {
  const { t } = useLang()
  const [failed, setFailed] = useState(false)
  useEffect(() => setFailed(false), [fig.url])
  return failed ? <span role="status" className="muted">{t('image_load_failed')}</span>
    : <img src={fig.url} alt={fig.caption || t('source_page')} loading="lazy" onError={() => setFailed(true)} style={style} />
}
