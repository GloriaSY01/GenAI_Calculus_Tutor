import { useEffect, useRef, useState } from 'react'
import { useLang } from '../../i18n.jsx'
import { api } from '../../api.js'
import { Card } from '../../components/ui.jsx'
import { MathText } from '../../components/math.jsx'
import { getQuickPrompts } from './prompts.js'

export default function Tutor({
  topic, tutorEntry, problem, sessionSeed, lang,
  studentId, classId,
  onBackPractice, onBackConcept,
}) {
  const { t } = useLang()
  const [sid, setSid] = useState(null)
  const [messages, setMessages] = useState([])   // { role, content, citations }
  const [lastTurn, setLastTurn] = useState({ mastery: 0, hint_level: 0, is_solved: false, action: null, asks_for_explanation: false })
  const [sending, setSending] = useState(false)
  const [input, setInput] = useState('')
  const scrollRef = useRef(null)

  const hasProblem = !!problem

  // start a session whenever the entry context changes
  useEffect(() => {
    let alive = true
    setMessages([]); setLastTurn({ mastery: 0, hint_level: 0, is_solved: false, action: null, asks_for_explanation: false })
    api.startSession({
      problem_id: problem?.id || null,
      condition: 'explain',
      student_id: studentId || 'anon',
      class_id: classId,
      topic,
      language: lang,
    }).then((res) => {
      if (!alive) return
      setSid(res.session_id)
      setMessages([{ role: 'assistant', content: res.opening_message, citations: [] }])
      // optional preset auto-send
      if (sessionSeed) setTimeout(() => send(sessionSeed, res.session_id), 120)
    })
    return () => { alive = false }
  }, [sessionSeed, problem?.id, topic]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, sending])

  const send = async (text, sessionId = sid) => {
    const msg = (text ?? '').trim()
    if (!msg || !sessionId) return
    setInput('')
    setMessages((m) => [...m, { role: 'user', content: msg, citations: [] }])
    setSending(true)
    const turn = await api.sendMessage(sessionId, msg, lang, { ...lastTurn, topic })
    setMessages((m) => [...m, { role: 'assistant', content: turn.tutor_message, citations: turn.citations || [] }])
    setLastTurn(turn)
    setSending(false)
  }

  const prompts = getQuickPrompts({
    topic, tutorEntry, hasProblem,
    isSolved: lastTurn.is_solved,
    action: lastTurn.action,
    hintLevel: lastTurn.hint_level,
    asksForExplanation: lastTurn.asks_for_explanation,
  })

  const mastery = Math.max(0, Math.min(100, lastTurn.mastery || 0))

  return (
    <div className="stack fade-in">
      <div>
        <div className="section-step">{t('stage_tutor')}</div>
        <h2 className="section-head">{t('tutor_heading')}</h2>
      </div>

      {/* context + progress */}
      <Card>
        <div className="row" style={{ justifyContent: 'space-between', gap: 12 }}>
          <div className="muted" style={{ fontSize: 13, fontWeight: 600 }}>
            {hasProblem ? t('tutor_context_practice') : t('tutor_context_concept')}{topic ? ` · ${topic}` : ''}
          </div>
          <div style={{ minWidth: 180, flex: '0 0 220px' }}>
            <div className="row" style={{ justifyContent: 'space-between', fontSize: 12.5 }}>
              <span className="muted">{t('tutor_progress')}</span>
              <span style={{ fontWeight: 700 }}>{mastery}%</span>
            </div>
            <div className="bar" style={{ marginTop: 4 }}><span style={{ width: mastery + '%' }} /></div>
          </div>
        </div>
        {problem?.statement && <MathText as="p" style={{ margin: '12px 0 0', lineHeight: 1.6 }}>{problem.statement}</MathText>}

        {lastTurn.is_solved && <div className="grade-box ok" style={{ marginTop: 12 }}>{t('tutor_solved')}</div>}
        {lastTurn.action === 'blocked' && <div className="note-tip" style={{ marginTop: 12 }}>{t('tutor_blocked')}</div>}
      </Card>

      {/* chat */}
      <Card>
        <div className="chat-scroll" ref={scrollRef}>
          {messages.map((m, i) => (
            <div key={i} className={'chat-msg ' + m.role}>
              <div className="chat-bubble">
                <MathText>{m.content}</MathText>
                {m.citations?.length > 0 && (
                  <div className="chat-cite">
                    {t('tutor_sources')}: {m.citations.map((c) => `${c.title}${c.page != null ? ' p.' + c.page : ''}`).join(' · ')}
                  </div>
                )}
              </div>
            </div>
          ))}
          {sending && <div className="chat-msg assistant"><div className="chat-bubble muted">{t('tutor_thinking')}</div></div>}
        </div>

        {/* suggested prompts */}
        {prompts.length > 0 && (
          <div className="sp-row">
            {prompts.map((p) => (
              <button key={p.key} className="chip" disabled={sending} onClick={() => send(p.text)}>{t(p.labelKey)}</button>
            ))}
          </div>
        )}

        {/* input */}
        <form className="chat-input" onSubmit={(e) => { e.preventDefault(); send(input) }}>
          <textarea className="inp" rows={2} placeholder={t('tutor_input_ph')} value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(input) } }} />
          <button className="btn primary" type="submit" disabled={sending || !input.trim()}>{t('tutor_send')}</button>
        </form>
      </Card>

      <div className="cta-bar">
        {tutorEntry === 'practice'
          ? <button className="btn" onClick={onBackPractice}>{t('tutor_back_practice')}</button>
          : <button className="btn" onClick={onBackConcept}>{t('tutor_back_concept')}</button>}
      </div>
    </div>
  )
}
