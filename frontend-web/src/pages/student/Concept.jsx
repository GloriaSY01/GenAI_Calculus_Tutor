import { useEffect, useState } from 'react'
import { useLang } from '../../i18n.jsx'
import { api } from '../../api.js'
import { Card, Loading, MockPill } from '../../components/ui.jsx'
import { Formula, MathText } from '../../components/math.jsx'

export default function Concept({ topic, onAskTutor, onStartPractice }) {
  const { t } = useLang()
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

  if (loading) return <Loading rows={3} />
  if (!card) return null

  const blocks = card.content || []

  return (
    <div className="stack fade-in">
      <div className="row" style={{ justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div className="section-step">{t('stage_concept')}</div>
          <h2 className="section-head">{card.title || topic}</h2>
          {card.chapter && <p className="muted" style={{ margin: '4px 0 0' }}>{card.chapter}</p>}
        </div>
        <MockPill show={mock} />
      </div>

      {mock && <div className="note-tip">{t('concept_unavailable')}</div>}

      <Card>
        <div className="stack" style={{ gap: 18 }}>
          {card.summary && <MathText as="p" style={{ margin: 0, fontSize: 15, lineHeight: 1.7 }}>{card.summary}</MathText>}

          {blocks.length > 0 ? blocks.map((b) => (
            <div key={b.id} className="concept-block">
              <div className="concept-block-kind">{b.heading || b.subtype}</div>
              {b.text && <MathText as="p" style={{ margin: '6px 0', lineHeight: 1.7 }}>{b.text}</MathText>}
              {(b.formulas || []).map((f, i) => (
                <Formula key={i}>{f}</Formula>
              ))}
              {(b.figures || []).map((fig) => (
                <figure key={fig.id} style={{ margin: '10px 0' }}>
                  <img src={fig.url} alt={fig.caption} style={{ maxWidth: '100%', borderRadius: 12, border: '1px solid var(--border)' }} />
                  {(fig.figure_number || fig.caption) && (
                    <figcaption className="muted" style={{ fontSize: 12.5, marginTop: 4 }}>
                      {[fig.figure_number, fig.caption].filter(Boolean).join(' — ')}
                    </figcaption>
                  )}
                </figure>
              ))}
              {b.printed_page != null && <div className="muted" style={{ fontSize: 12 }}>p.{b.printed_page}</div>}
            </div>
          )) : (
            <div className="stack" style={{ gap: 14 }}>
              {card.definition && <ConceptSection title={t('concept_definition')} text={card.definition} formulas={card.formulas} />}
              {card.example && <ConceptSection title={t('concept_example')} text={card.example} />}
              {card.pitfalls && <ConceptSection title={t('concept_pitfalls')} text={card.pitfalls} />}
            </div>
          )}

          {(card.source || card.source_url || card.publisher || card.license) && (
            <div className="concept-source">
              <span className="muted" style={{ fontWeight: 700 }}>{t('concept_source')}:</span>{' '}
              {card.source_url
                ? <a href={card.source_url} target="_blank" rel="noreferrer" style={{ color: 'var(--brand-600)' }}>{card.source || card.publisher || card.source_url}</a>
                : (card.source || card.publisher)}
              {card.license && <span className="muted"> · {card.license}</span>}
            </div>
          )}
        </div>
      </Card>

      <div className="cta-bar">
        <button className="btn" onClick={onAskTutor}>💬 {t('concept_ask_tutor')}</button>
        <div className="spacer" />
        <button className="btn primary" onClick={onStartPractice}>{t('concept_start_practice')} →</button>
      </div>
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
