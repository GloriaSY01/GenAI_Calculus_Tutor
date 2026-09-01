import { useEffect, useState } from 'react'
import { useLang } from '../../i18n.jsx'
import { api } from '../../api.js'
import { Card, Loading, MockPill, Badge } from '../../components/ui.jsx'
import { MathText } from '../../components/math.jsx'

const QTYPES = ['single_choice', 'multiple_choice', 'fill_blank', 'drag_order']
const DIFFS = ['easy', 'medium', 'hard']

export default function Practice({
  topic, difficulty, qtype, setDifficulty, setQtype,
  studentId, classId, lang,
  onBackConcept, onStuck, onExplainCorrect, onGetHint, onFirstStep,
  favorites, onToggleFavorite,
}) {
  const { t } = useLang()
  const [loading, setLoading] = useState(true)
  const [q, setQ] = useState(null)
  const [mock, setMock] = useState(false)
  const [answer, setAnswer] = useState({})
  const [grade, setGrade] = useState(null)
  const [grading, setGrading] = useState(false)

  const load = () => {
    setLoading(true); setGrade(null); setAnswer({})
    api.generateQuestion({ type: qtype, topic, difficulty, language: lang }).then((res) => {
      setQ(res); setMock(!!res._mock); setLoading(false)
    })
  }
  // regenerate on topic/qtype/difficulty change
  useEffect(load, [topic, qtype, difficulty]) // eslint-disable-line react-hooks/exhaustive-deps

  const isFav = q && favorites.some((f) => f.question_id === q.id)

  const submit = async () => {
    if (!q) return
    setGrading(true)
    const payload = { question_id: q.id, student_id: studentId || 'anon', class_id: classId, ...answer }
    const res = await api.gradeAnswer(payload)
    setGrade(res); setGrading(false)
  }

  const diffLabel = (d) => t('diff_' + d)
  const qtypeLabel = (x) => t('qtype_' + x)

  return (
    <div className="stack fade-in">
      <div className="row" style={{ justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div className="section-step">{t('stage_practice')}</div>
          <h2 className="section-head">{t('practice_heading')}</h2>
          <p className="muted" style={{ margin: '4px 0 0' }}>{topic}</p>
        </div>
        <MockPill show={mock} />
      </div>

      {/* difficulty + type controls */}
      <div className="row wrap" style={{ gap: 18 }}>
        <div>
          <div className="ctrl-label">{t('practice_difficulty')}</div>
          <div className="row" style={{ gap: 8 }}>
            {DIFFS.map((d) => (
              <button key={d} className={'chip' + (difficulty === d ? ' sel' : '')} onClick={() => setDifficulty(d)}
                style={difficulty === d ? { borderColor: 'var(--brand-400)', color: 'var(--brand-700)', background: 'var(--brand-50)' } : {}}>
                {diffLabel(d)}
              </button>
            ))}
          </div>
        </div>
        <div>
          <div className="ctrl-label">{t('practice_qtype')}</div>
          <select className="inp" style={{ width: 200 }} value={qtype} onChange={(e) => setQtype(e.target.value)}>
            {QTYPES.map((x) => <option key={x} value={x}>{qtypeLabel(x)}</option>)}
          </select>
        </div>
      </div>

      {loading ? <Loading rows={2} /> : q && (
        <Card>
          <div className="row" style={{ justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div className="row" style={{ gap: 8 }}>
              <Badge level="neutral">{diffLabel(q.difficulty)}</Badge>
              <Badge level="neutral">{qtypeLabel(q.type)}</Badge>
            </div>
            <button className="btn sm ghost" title={studentId ? '' : t('practice_need_name')}
              disabled={!studentId} onClick={() => onToggleFavorite(q, isFav)}>
              {isFav ? '★ ' + t('practice_unfavorite') : '☆ ' + t('practice_favorite')}
            </button>
          </div>

          <MathText as="p" style={{ fontSize: 15.5, lineHeight: 1.7, margin: '12px 0' }}>{q.stem}</MathText>
          <div className="muted" style={{ fontSize: 12.5 }}>
            {q.source === 'textbook' ? t('practice_source_textbook') : t('practice_source_generated')}
          </div>
          {q.instructions && <MathText as="div" className="muted" style={{ fontSize: 13, marginTop: 4 }}>{q.instructions}</MathText>}

          {/* answer controls */}
          <div style={{ marginTop: 16 }}>
            <div className="ctrl-label">{t('practice_your_answer')}</div>
            <AnswerControls q={q} answer={answer} setAnswer={setAnswer} disabled={grade?.correct} />
          </div>

          {q.citations?.length > 0 && (
            <details style={{ marginTop: 14 }}>
              <summary className="muted" style={{ cursor: 'pointer', fontSize: 13 }}>{t('practice_citations')}</summary>
              <ul className="muted" style={{ fontSize: 12.5, marginTop: 6 }}>
                {q.citations.map((c, i) => (
                  <li key={i}>{c.title}{c.section ? ' · ' + c.section : ''}{c.page != null ? ' · p.' + c.page : ''}</li>
                ))}
              </ul>
            </details>
          )}

          {grade && (
            <div className={'grade-box ' + (grade.correct ? 'ok' : 'bad')} style={{ marginTop: 16 }}>
              <div style={{ fontWeight: 700 }}>{grade.correct ? '✓' : '✗'} <MathText>{grade.feedback}</MathText></div>
              {!grade.correct && <div className="muted" style={{ fontSize: 12.5, marginTop: 4 }}>{t('practice_attempt').replace('{n}', grade.attempts ?? 1)}</div>}
            </div>
          )}
        </Card>
      )}

      {/* CTA bar */}
      <div className="cta-bar">
        <button className="btn" onClick={onBackConcept}>{t('practice_back_concept')}</button>
        <div className="spacer" />
        {grade?.correct ? (
          <>
            <button className="btn" onClick={() => onExplainCorrect(q)}>{t('practice_explain_correct')}</button>
            <button className="btn primary" onClick={load}>{t('practice_next')} →</button>
          </>
        ) : grade ? (
          <>
            <button className="btn" onClick={() => onGetHint(q)}>{t('practice_get_hint')}</button>
            <button className="btn" onClick={() => onFirstStep(q)}>{t('practice_first_step')}</button>
            <button className="btn" onClick={() => setGrade(null)}>{t('practice_retry')}</button>
          </>
        ) : (
          <>
            <button className="btn" onClick={() => onStuck(q)}>{t('practice_stuck')}</button>
            <button className="btn primary" disabled={grading} onClick={submit}>
              {grading ? t('loading') : t('practice_submit')}
            </button>
          </>
        )}
      </div>
    </div>
  )
}

function AnswerControls({ q, answer, setAnswer, disabled }) {
  if (q.type === 'single_choice') {
    return (
      <div className="stack" style={{ gap: 8 }}>
        {(q.options || []).map((opt, i) => (
          <label key={i} className={'opt-row' + (answer.single === i ? ' sel' : '')}>
            <input type="radio" name="single" disabled={disabled} checked={answer.single === i}
              onChange={() => setAnswer({ single: i })} />
            <MathText>{opt}</MathText>
          </label>
        ))}
      </div>
    )
  }
  if (q.type === 'multiple_choice') {
    const chosen = answer.multiple || []
    const toggle = (i) => setAnswer({ multiple: chosen.includes(i) ? chosen.filter((x) => x !== i) : [...chosen, i] })
    return (
      <div className="stack" style={{ gap: 8 }}>
        {(q.options || []).map((opt, i) => (
          <label key={i} className={'opt-row' + (chosen.includes(i) ? ' sel' : '')}>
            <input type="checkbox" disabled={disabled} checked={chosen.includes(i)} onChange={() => toggle(i)} />
            <MathText>{opt}</MathText>
          </label>
        ))}
      </div>
    )
  }
  if (q.type === 'fill_blank') {
    const blanks = answer.blanks || Array(q.n_blanks || 1).fill('')
    const setBlank = (i, v) => { const nb = [...blanks]; nb[i] = v; setAnswer({ blanks: nb }) }
    return (
      <div className="stack" style={{ gap: 8 }}>
        {Array.from({ length: q.n_blanks || 1 }).map((_, i) => (
          <input key={i} className="inp" placeholder={`#${i + 1}`} disabled={disabled}
            value={blanks[i] || ''} onChange={(e) => setBlank(i, e.target.value)} />
        ))}
      </div>
    )
  }
  // drag_order — simple up/down reordering (no external dnd dep)
  const order = answer.order || q.steps || []
  const move = (i, dir) => {
    const j = i + dir
    if (j < 0 || j >= order.length) return
    const no = [...order];[no[i], no[j]] = [no[j], no[i]]; setAnswer({ order: no })
  }
  return (
    <div className="stack" style={{ gap: 6 }}>
      {order.map((step, i) => (
        <div key={i} className="order-row">
          <span className="order-idx">{i + 1}</span>
          <MathText style={{ flex: 1 }}>{step}</MathText>
          <button className="btn sm ghost" disabled={disabled || i === 0} onClick={() => move(i, -1)}>↑</button>
          <button className="btn sm ghost" disabled={disabled || i === order.length - 1} onClick={() => move(i, 1)}>↓</button>
        </div>
      ))}
    </div>
  )
}
