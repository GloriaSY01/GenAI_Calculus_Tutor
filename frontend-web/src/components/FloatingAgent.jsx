import { useEffect, useRef, useState } from 'react'
import { Bot, Send, X } from 'lucide-react'

export default function FloatingAgent({
  title,
  subtitle,
  welcome,
  prompts,
  suggestionsLabel,
  placeholder,
  sendLabel,
  openLabel,
  closeLabel,
  resetKey,
  onAsk,
}) {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const scrollRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    setMessages([{ role: 'assistant', content: welcome, welcome: true }])
    setInput('')
  }, [resetKey, welcome])

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, sending])

  useEffect(() => {
    if (open) inputRef.current?.focus()
  }, [open])

  async function send() {
    const question = input.trim()
    if (!question || sending) return
    const history = messages
      .filter((message) => !message.welcome)
      .map(({ role, content }) => ({ role, content }))
    setInput('')
    setMessages((current) => [...current, { role: 'user', content: question }])
    setSending(true)
    try {
      const reply = await onAsk(question, history)
      setMessages((current) => [...current, {
        role: 'assistant',
        content: reply.content,
        note: reply.note,
        citations: reply.citations || [],
      }])
    } catch (error) {
      setInput(question)
      setMessages((current) => [...current, {
        role: 'assistant',
        content: error?.message || 'Agent unavailable. Please try again.',
        error: true,
      }])
    } finally {
      setSending(false)
    }
  }

  return <>
    {open && <section className="floating-agent" role="dialog" aria-modal="false" aria-labelledby="floating-agent-title">
      <header className="floating-agent-head">
        <span className="floating-agent-avatar" aria-hidden="true"><Bot size={21} /></span>
        <div><h2 id="floating-agent-title">{title}</h2><span>{subtitle}</span></div>
        <button type="button" className="floating-agent-icon" onClick={() => setOpen(false)} aria-label={closeLabel} title={closeLabel}><X size={18} /></button>
      </header>

      <div className="floating-agent-chat" ref={scrollRef} aria-live="polite">
        {messages.map((message, index) => <div key={index} className={'agent-message ' + message.role}>
          <div className={'agent-bubble' + (message.error ? ' error' : '')}>
            {message.note && <small className="agent-note">{message.note}</small>}
            <p>{message.content}</p>
            {!!message.citations?.length && <small>{message.citations.map((citation) => citation.title).join(' · ')}</small>}
          </div>
        </div>)}
        {sending && <div className="agent-message assistant"><div className="agent-bubble agent-thinking"><span /><span /><span /></div></div>}
      </div>

      <div className="floating-agent-prompts" aria-label={title}>
        <span className="floating-agent-prompt-label">{suggestionsLabel}</span>
        {prompts.map((prompt) => <button key={prompt} type="button" className="chip" disabled={sending}
          onClick={() => { setInput(prompt); inputRef.current?.focus() }}>{prompt}</button>)}
      </div>

      <form className="floating-agent-input" onSubmit={(event) => { event.preventDefault(); send() }}>
        <textarea ref={inputRef} className="inp" rows={2} value={input} placeholder={placeholder}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault()
              send()
            }
          }} />
        <button className="floating-agent-icon send" type="submit" disabled={sending || !input.trim()}
          aria-label={sendLabel} title={sendLabel}><Send size={18} /></button>
      </form>
    </section>}

    <button type="button" className={'floating-agent-fab' + (open ? ' open' : '')}
      onClick={() => setOpen((current) => !current)} aria-expanded={open}
      aria-label={open ? closeLabel : openLabel} title={open ? closeLabel : openLabel}>
      {open ? <X size={25} /> : <Bot size={27} />}
      {!open && <span className="floating-agent-pulse" aria-hidden="true" />}
    </button>
  </>
}
