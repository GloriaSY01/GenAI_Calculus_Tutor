import { useEffect, useRef, useState } from 'react'
import { Bot, Send, X } from 'lucide-react'
import { MathText } from './math.jsx'

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
  const generation = useRef(0)
  const acknowledged = useRef(new Set())
  const [deliveryError, setDeliveryError] = useState(false)
  const [deliveryRetry, setDeliveryRetry] = useState(0)

  useEffect(() => {
    generation.current += 1
    setMessages([{ role: 'assistant', content: welcome, welcome: true }])
    setInput('')
    setSending(false)
    setDeliveryError(false)
    return () => { generation.current += 1 }
  }, [resetKey, welcome])

  useEffect(() => {
    if (!open) return
    let active = true
    // Effects run after the reply is committed to the visible chat. Hidden tabs
    // must wait until foregrounded before acknowledging presentation.
    async function acknowledge() {
      if (document.visibilityState !== 'visible') return
      for (const message of messages) {
        if (!message.ack || acknowledged.current.has(message)) continue
        try {
          await message.ack()
          acknowledged.current.add(message)
          if (active) setDeliveryError(false)
        } catch { if (active) setDeliveryError(true) }
      }
    }
    acknowledge()
    document.addEventListener('visibilitychange', acknowledge)
    return () => { active = false; document.removeEventListener('visibilitychange', acknowledge) }
  }, [messages, open, deliveryRetry])

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
    const currentGeneration = generation.current
    try {
      const reply = await onAsk(question, history)
      if (generation.current !== currentGeneration) return
      setMessages((current) => [...current, {
        role: 'assistant',
        content: reply.content,
        note: reply.note,
        citations: reply.citations || [],
        ack: reply.ack,
      }])
    } catch (error) {
      if (generation.current !== currentGeneration) return
      setInput(question)
      setMessages((current) => [...current, {
        role: 'assistant',
        content: error?.message || 'Agent unavailable. Please try again.',
        error: true,
      }])
    } finally {
      if (generation.current === currentGeneration) setSending(false)
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
        {deliveryError && <p role="alert">显示记录未同步 / Display record not synced. <button type="button" onClick={() => setDeliveryRetry(n => n + 1)}>重试 / Retry</button></p>}
        {messages.map((message, index) => <div key={index} className={'agent-message ' + message.role}>
          <div className={'agent-bubble' + (message.error ? ' error' : '')}>
            {message.note && <small className="agent-note">{message.note}</small>}
            <MathText as="div" className="agent-message-content">{message.content}</MathText>
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
