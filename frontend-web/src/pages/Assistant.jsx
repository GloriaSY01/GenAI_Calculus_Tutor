import { useState, useRef, useEffect } from 'react'
import { useLang } from '../i18n.jsx'
import { api } from '../api.js'
import { Card } from '../components/ui.jsx'

const SUGGESTIONS = {
  zh: [
    '哪个知识点最需要关注？',
    '本周正确率变化如何？',
    '有助教的学生表现更好吗？',
    '给薄弱知识点推荐一套练习',
  ],
  en: [
    'Which topic needs the most attention?',
    'How did accuracy change this week?',
    'Do tutor-assisted students do better?',
    'Suggest a practice set for weak topics',
  ],
}

export default function Assistant() {
  const { t, lang } = useLang()
  const [msgs, setMsgs] = useState([])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const scrollRef = useRef(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [msgs, busy])

  const send = async (q) => {
    const question = (q ?? input).trim()
    if (!question || busy) return
    setInput('')
    setMsgs(m => [...m, { role: 'user', text: question }])
    setBusy(true)
    const res = await api.ask(question)
    setBusy(false)
    setMsgs(m => [...m, { role: 'bot', text: res.answer, mock: res._mock }])
  }

  return (
    <div className="stack fade-in">
      <p className="muted" style={{ margin: 0 }}>{t('assistant_sub')}</p>

      <Card className="pad-lg" >
        <div ref={scrollRef} className="chat-scroll">
          {msgs.length === 0 && (
            <div className="empty" style={{ padding: '32px 12px' }}>
              <div className="ico">💬</div>
              <div style={{ fontWeight: 700, color: 'var(--text)', marginBottom: 4 }}>{t('assistant_title')}</div>
              <div>{t('assistant_sub')}</div>
            </div>
          )}

          {msgs.map((m, i) => (
            <div key={i} className={'bubble-row ' + m.role}>
              {m.role === 'bot' && <div className="avatar">∫</div>}
              <div className={'bubble ' + m.role}>
                {m.text.split('\n').map((line, j) => <p key={j} style={{ margin: j ? '8px 0 0' : 0 }}>{renderMd(line)}</p>)}
              </div>
            </div>
          ))}

          {busy && (
            <div className="bubble-row bot">
              <div className="avatar">∫</div>
              <div className="bubble bot"><span className="typing"><i /><i /><i /></span></div>
            </div>
          )}
        </div>

        {msgs.length === 0 && (
          <>
            <div className="muted" style={{ fontSize: 13, fontWeight: 700, margin: '8px 2px' }}>
              {t('assistant_suggest')}
            </div>
            <div className="row wrap" style={{ gap: 8, marginBottom: 12 }}>
              {(SUGGESTIONS[lang] || SUGGESTIONS.en).map((s, i) => (
                <button key={i} className="chip" onClick={() => send(s)}>{s}</button>
              ))}
            </div>
          </>
        )}

        <div className="composer">
          <input className="composer-inp" value={input}
            placeholder={t('assistant_ph')}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && send()} />
          <button className="btn primary" onClick={() => send()} disabled={busy || !input.trim()}>
            {t('assistant_send')} ➤
          </button>
        </div>
      </Card>

      <style>{`
        .chat-scroll { max-height: 52vh; overflow-y: auto; padding: 4px; margin-bottom: 8px; }
        .bubble-row { display: flex; gap: 10px; margin-bottom: 14px; align-items: flex-end; }
        .bubble-row.user { flex-direction: row-reverse; }
        .avatar { width: 32px; height: 32px; flex: 0 0 32px; border-radius: 9px; display: grid; place-items: center;
          color: #fff; font-weight: 800; background: linear-gradient(135deg, var(--brand-500), var(--accent)); }
        .bubble { max-width: 76%; padding: 12px 15px; border-radius: 16px; font-size: 14.5px; line-height: 1.55; }
        .bubble.bot { background: var(--surface-2); border: 1px solid var(--border); border-bottom-left-radius: 5px; }
        .bubble.user { background: linear-gradient(135deg, var(--brand-500), var(--brand-600));
          color: #fff; border-bottom-right-radius: 5px; }
        .bubble.user code { background: rgba(255,255,255,.2); }
        .bubble code { background: var(--bg-2); padding: 1px 6px; border-radius: 6px; font-size: 13px; }
        .composer { display: flex; gap: 10px; padding-top: 10px; border-top: 1px solid var(--border); }
        .composer-inp { flex: 1; padding: 12px 15px; border-radius: 999px; border: 1px solid var(--border-2);
          background: var(--surface-2); color: var(--text); font-size: 14.5px; font-family: inherit; }
        .composer-inp:focus { outline: none; border-color: var(--brand-400); box-shadow: 0 0 0 3px var(--brand-50); }
        .typing { display: inline-flex; gap: 4px; padding: 2px 0; }
        .typing i { width: 7px; height: 7px; border-radius: 50%; background: var(--muted);
          animation: blink 1.2s infinite ease-in-out; }
        .typing i:nth-child(2) { animation-delay: .2s; } .typing i:nth-child(3) { animation-delay: .4s; }
        @keyframes blink { 0%,80%,100% { opacity:.3; transform: translateY(0); } 40% { opacity:1; transform: translateY(-3px); } }
      `}</style>
    </div>
  )
}

/* minimal **bold** / `code` rendering */
function renderMd(line) {
  const parts = []
  let rest = line, key = 0
  const re = /(\*\*[^*]+\*\*|`[^`]+`)/
  let m
  while ((m = re.exec(rest))) {
    if (m.index > 0) parts.push(rest.slice(0, m.index))
    const tok = m[0]
    if (tok.startsWith('**')) parts.push(<strong key={key++}>{tok.slice(2, -2)}</strong>)
    else parts.push(<code key={key++}>{tok.slice(1, -1)}</code>)
    rest = rest.slice(m.index + tok.length)
  }
  parts.push(rest)
  return parts
}
