import { useState } from 'react'
import { useLang } from '../i18n.jsx'
import { useAsync } from '../components/hooks.js'
import { api } from '../api.js'
import { Card, Loading, MockPill, Empty } from '../components/ui.jsx'

const QTYPES = ['single_choice', 'multiple_choice', 'fill_blank', 'drag_order']
const DIFFS = ['easy', 'medium', 'hard']
const MAX_BLOCKS = 8

// One-click worksheet templates: [qtype, difficulty, count]
const TEMPLATES = {
  foundation: [['single_choice', 'easy', 4], ['fill_blank', 'easy', 3], ['single_choice', 'medium', 2]],
  mixed:      [['single_choice', 'medium', 3], ['multiple_choice', 'medium', 2], ['fill_blank', 'medium', 3], ['drag_order', 'medium', 2]],
  challenge:  [['multiple_choice', 'medium', 2], ['fill_blank', 'hard', 3], ['drag_order', 'hard', 2]],
}

// Rough minutes per question, scaled by difficulty, for the time estimate.
const EST_MIN = { single_choice: 1.5, multiple_choice: 2.0, fill_blank: 3.0, drag_order: 3.0 }
const DIFF_MULT = { easy: 0.8, medium: 1.0, hard: 1.4 }

// Topic display map (backend topics are English keys).
const TOPIC_ZH = { Limits: '极限', Derivatives: '导数', Integrals: '积分', 'Chain Rule': '链式法则', 'U-Substitution': '换元' }

let _bid = 0
const newBlock = (topic, qtype = 'single_choice', difficulty = 'easy', count = 3) =>
  ({ id: 'b' + (++_bid), topic, qtype, difficulty, count })

const totalQuestions = (items) => items.reduce((s, i) => s + (+i.count || 0), 0)
const estimateMinutes = (items) =>
  Math.max(1, Math.round(items.reduce((s, i) => s + EST_MIN[i.qtype] * DIFF_MULT[i.difficulty] * (+i.count || 0), 0)))

export default function Assign() {
  const { t, lang } = useLang()
  const topicsQ = useAsync(() => api.getTopics(), [])
  const listQ = useAsync(() => api.getAssignments(), [])

  const topics = topicsQ.data?.topics || []
  const topicNames = topics.map(tp => tp.name)
  const assignments = listQ.data?.assignments || []

  const topicLabel = (name) => (lang === 'zh' ? (TOPIC_ZH[name] || name) : name)
  const qtypeLabel = (q) => t('qtype_' + q)
  const diffLabel = (d) => t('diff_' + d)

  const [title, setTitle] = useState('')
  const [note, setNote] = useState('')
  const [blocks, setBlocks] = useState([newBlock(topicNames[0] || 'Limits')])
  const [saving, setSaving] = useState(false)
  const [warn, setWarn] = useState('')

  const baseTopic = () => blocks[blocks.length - 1]?.topic || topicNames[0] || 'Limits'
  const applyTemplate = (kind) => {
    const bt = blocks[0]?.topic || topicNames[0] || 'Limits'
    setBlocks(TEMPLATES[kind].map(([q, d, c]) => newBlock(bt, q, d, c)))
  }
  const addBlock = () => { if (blocks.length < MAX_BLOCKS) setBlocks([...blocks, newBlock(baseTopic())]) }
  const removeBlock = (id) => setBlocks(blocks.filter(b => b.id !== id))
  const updBlock = (id, patch) => setBlocks(blocks.map(b => b.id === id ? { ...b, ...patch } : b))

  const submit = async () => {
    if (!title.trim()) { setWarn(t('assign_need_title')); return }
    if (blocks.length === 0) { setWarn(t('assign_need_items')); return }
    setWarn(''); setSaving(true)
    await api.createAssignment({ title: title.trim(), note: note.trim(), items: blocks })
    setSaving(false)
    setTitle(''); setNote(''); setBlocks([newBlock(topicNames[0] || 'Limits')])
    listQ.reload()
  }
  const remove = async (id) => { await api.deleteAssignment(id); listQ.reload() }

  const totalStr = t('assign_total')
    .replace('{n}', totalQuestions(blocks))
    .replace('{m}', estimateMinutes(blocks))

  return (
    <div className="stack fade-in">
      <div className="row" style={{ justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div className="section-step">{t('assign_step')}</div>
          <h2 className="section-head">{t('assign_head')}</h2>
          <p className="muted" style={{ margin: '4px 0 0' }}>{t('assign_head_sub')}</p>
        </div>
        <MockPill show={listQ.data?._mock} />
      </div>

      <div className="grid cols-2 assign-grid">
        {/* ---------- Left: builder ---------- */}
        <Card title={t('assign_new')} icon="✏️" sub={t('assign_new_caption')} className="pad-lg">
          <div className="stack" style={{ gap: 16 }}>
            <Field label={t('assign_title_label')}>
              <input className="inp" value={title} placeholder={t('assign_title_hint')}
                onChange={e => setTitle(e.target.value)} />
            </Field>

            <div>
              <div className="field-cap">{t('assign_templates')}：</div>
              <div className="tpl-row">
                <button type="button" className="tpl-btn" onClick={() => applyTemplate('foundation')}>{t('tpl_foundation')}</button>
                <button type="button" className="tpl-btn" onClick={() => applyTemplate('mixed')}>{t('tpl_mixed')}</button>
                <button type="button" className="tpl-btn" onClick={() => applyTemplate('challenge')}>{t('tpl_challenge')}</button>
              </div>
            </div>

            <div>
              <div className="field-cap">{t('assign_items_heading')}</div>
              <div className="blk-head">
                <span>{t('assign_topic')}</span>
                <span>{t('assign_format')}</span>
                <span>{t('assign_difficulty')}</span>
                <span>{t('assign_num')}</span>
                <span></span>
              </div>
              <div className="stack" style={{ gap: 8 }}>
                {blocks.map(b => (
                  <div className="blk-row" key={b.id}>
                    <select className="inp" value={b.topic} onChange={e => updBlock(b.id, { topic: e.target.value })}>
                      {topicNames.map(n => <option key={n} value={n}>{topicLabel(n)}</option>)}
                    </select>
                    <select className="inp" value={b.qtype} onChange={e => updBlock(b.id, { qtype: e.target.value })}>
                      {QTYPES.map(q => <option key={q} value={q}>{qtypeLabel(q)}</option>)}
                    </select>
                    <select className="inp" value={b.difficulty} onChange={e => updBlock(b.id, { difficulty: e.target.value })}>
                      {DIFFS.map(d => <option key={d} value={d}>{diffLabel(d)}</option>)}
                    </select>
                    <input className="inp" type="number" min={1} max={10} value={b.count}
                      onChange={e => updBlock(b.id, { count: +e.target.value })} />
                    <button type="button" className="blk-del" title={t('assign_delete')}
                      onClick={() => removeBlock(b.id)}>✕</button>
                  </div>
                ))}
              </div>

              {blocks.length < MAX_BLOCKS && (
                <button type="button" className="btn ghost add-blk" onClick={addBlock}>{t('assign_add_block')}</button>
              )}
            </div>

            {blocks.length > 0 && (
              <div className="stat-strip" style={{ gridTemplateColumns: '1fr' }}>
                <div className="stat-item"><span className="stat-label">{totalStr}</span></div>
              </div>
            )}

            <Field label={t('note')}>
              <textarea className="inp" rows={2} value={note} onChange={e => setNote(e.target.value)} />
            </Field>

            {warn && <div className="warn-note">{warn}</div>}

            <button className="btn primary" disabled={saving || !title.trim()} onClick={submit}>
              {saving ? t('loading') : t('assign_btn')}
            </button>
          </div>
        </Card>

        {/* ---------- Right: current assignments ---------- */}
        <Card title={t('current_assignments')} icon="📋" sub={t('assign_not_connected')}>
          {listQ.loading ? <Loading rows={2} /> :
            assignments.length === 0 ? <Empty icon="📭">{t('no_assignments')}</Empty> :
            <div className="stack asg-list" style={{ gap: 12 }}>
              {assignments.map(a => {
                const items = a.items || []
                const total = t('assign_total')
                  .replace('{n}', totalQuestions(items))
                  .replace('{m}', estimateMinutes(items))
                return (
                  <div className="asg-card" key={a.id}>
                    <div className="row" style={{ justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <div style={{ fontWeight: 800 }}>{a.title}</div>
                      <button className="btn sm ghost" onClick={() => remove(a.id)}>{t('assign_delete')}</button>
                    </div>
                    <div className="muted" style={{ fontSize: 13, margin: '6px 0 8px' }}>
                      {total} · {t('assign_completion')}: -
                    </div>
                    <div className="stack" style={{ gap: 3 }}>
                      {items.map((it, i) => (
                        <div className="asg-blk" key={i}>
                          · {topicLabel(it.topic)} · {it.count}× {qtypeLabel(it.qtype)} · {diffLabel(it.difficulty)}
                        </div>
                      ))}
                    </div>
                    {a.note && <div className="muted" style={{ fontSize: 12.5, marginTop: 6 }}>📝 {a.note}</div>}
                  </div>
                )
              })}
            </div>}
        </Card>
      </div>

      <style>{`
        .inp { width: 100%; padding: 10px 12px; border-radius: var(--r-md);
          border: 1px solid var(--border-2); background: var(--surface-2); color: var(--text);
          font-size: 14px; font-family: inherit; transition: border-color .15s, box-shadow .15s; }
        .inp:focus { outline: none; border-color: var(--brand-400); box-shadow: 0 0 0 3px var(--brand-50); }
        select.inp { cursor: pointer; }
        .field-cap { font-size: 13px; font-weight: 700; color: var(--text-2); margin-bottom: 8px; }
        .tpl-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
        .tpl-btn { padding: 12px 10px; border-radius: var(--r-md); border: 1px solid var(--border-2);
          background: var(--surface-2); color: var(--text); font-weight: 700; font-size: 14px; cursor: pointer;
          transition: all .15s ease; }
        .tpl-btn:hover { border-color: var(--brand-400); color: var(--brand-700); background: var(--brand-50); }
        .blk-head, .blk-row { display: grid; grid-template-columns: 1.4fr 1.4fr 1fr .8fr 34px; gap: 8px; align-items: center; }
        .blk-head { margin-bottom: 6px; }
        .blk-head span { font-size: 12.5px; font-weight: 700; color: var(--text-2); }
        .blk-del { width: 34px; height: 38px; border-radius: var(--r-md); border: 1px solid var(--border);
          background: var(--surface-2); color: var(--muted); cursor: pointer; font-size: 13px; transition: all .15s; }
        .blk-del:hover { border-color: var(--bad, #f04438); color: var(--bad, #f04438); background: #fff1f0; }
        .add-blk { width: 100%; margin-top: 10px; }
        .warn-note { color: var(--bad, #f04438); font-size: 13px; font-weight: 600; }
        .asg-list { max-height: 560px; overflow: auto; }
        .asg-card { border: 1px solid var(--border); border-radius: var(--r-lg); padding: 14px 16px; background: var(--surface-2); }
        .asg-blk { font-size: 13px; color: var(--text-2); }
        @media (max-width: 720px) {
          .blk-head { display: none; }
          .blk-row { grid-template-columns: 1fr 1fr; grid-auto-rows: auto; }
          .blk-row .blk-del { grid-column: 2; justify-self: end; }
        }
      `}</style>
    </div>
  )
}

function Field({ label, children }) {
  return (
    <label style={{ display: 'block' }}>
      <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-2)', marginBottom: 6 }}>{label}</div>
      {children}
    </label>
  )
}
