import { useTranslatedContent } from '../useTranslatedContent.js'
import { useEffect, useRef, useState } from 'react'
import { useLang } from '../i18n.jsx'
import { api } from '../api.js'
import { MathText, Formula } from '../components/math.jsx'
import { Loading } from '../components/ui.jsx'
import { displayLabel } from '../localization.js'
import { AnswerControls } from './student/Practice.jsx'
import Concept from './student/Concept.jsx'
import Favorites from './student/Favorites.jsx'
import { hasAnswer, challengePlan, roundSummary } from './student/study.js'
import './student/workspace.css'

const TYPES = ['single_choice', 'multiple_choice', 'fill_blank', 'drag_order']
const DIFFS = ['easy', 'medium', 'hard']
const fresh = () => ({ chapter: '', section: '', view: 'home', active: '', rounds: {}, difficulty: 'easy', type: 'mixed' })
function read(key) {
  try { const saved = JSON.parse(localStorage.getItem(key)); return saved?.version === 2 && saved.state?.rounds ? { ...fresh(), ...saved.state } : fresh() }
  catch { return fresh() }
}
export default function StudentWorkspace({ topbar }) {
  const { t, lang } = useLang()
  const [student, setStudent] = useState(() => localStorage.getItem('stu_name') || '')
  const [classId, setClassId] = useState(() => localStorage.getItem('stu_class') || '')
  const [catalog, setCatalog] = useState(null)
  const [classes, setClasses] = useState([])
  useEffect(() => {
    api.getClasses().then(r => { setClasses(r.classes || []); setClassId(current => r.classes?.some(c => c.id === current) ? current : r.classes?.[0]?.id || '') })
    api.getCatalog().then(setCatalog)
  }, [])
  const scope = JSON.stringify([student || 'guest', classId])
  return <Workspace key={scope} {...{ topbar, t, lang, student, classId, classes, catalog, scope }}
    onStudent={v => { setStudent(v); localStorage.setItem('stu_name', v) }} onClass={v => { setClassId(v); localStorage.setItem('stu_class', v) }} />
}
function Workspace({ topbar, t, lang, student, classId, classes, catalog, scope, onStudent, onClass }) {
  const text = (zh, en) => lang === 'zh' ? zh : en
  const storageKey = 'calculus-study-v2:' + scope
  const [state, setState] = useState(() => read(storageKey))
  const [busy, setBusy] = useState(false)
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')
  const [storageError, setStorageError] = useState(false)
  const [favorites, setFavorites] = useState([])
  const lock = useRef(false)
  const alive = useRef(true)
  useEffect(() => { alive.current = true; return () => { alive.current = false } }, [])
  useEffect(() => {
    try { localStorage.setItem(storageKey, JSON.stringify({ version: 2, state })); setStorageError(false) }
    catch { setStorageError(true) }
  }, [state, storageKey])
  useEffect(() => { let current = true; if (student) api.getFavorites(student).then(r => { if (current) setFavorites(r.favorites || []) }); return () => { current = false } }, [student])
  const chapters = catalog?.chapters || []
  const chapter = chapters.find(c => c.id === state.chapter) || chapters[0]
  const sections = chapter?.sections || []
  const selected = sections.find(s => s.id === state.section) || (state.section === 'all' ? null : sections[0])
  const activeRound = chapter && state.active.startsWith(chapter.id + ':') ? state.rounds[state.active] : null
  const studyKey = chapter?.id + ':free:' + (selected?.id || 'all')
  const challengeKey = chapter?.id + ':challenge'
  const roundKey = state.view === 'study' ? studyKey : state.active
  const round = state.view === 'study' ? state.rounds[studyKey] : activeRound
  const item = round?.items[round.cursor]
  const challenge = round?.mode === 'challenge'
  const reviewing = challenge && !!round.submitted
  const patch = fields => setState(s => ({ ...s, ...fields }))
  const updateRound = (key, fn) => setState(s => ({ ...s, rounds: { ...s.rounds, [key]: fn(s.rounds[key]) } }))
  const updateItem = (key, index, fields) => updateRound(key, r => ({ ...r, items: r.items.map((x, i) => i === index ? { ...x, ...fields } : x) }))
  async function task(fn) {
    if (lock.current) return
    lock.current = true; setBusy(true); setError('')
    try { await fn() } catch (e) { if (alive.current) setError(e.message) }
    finally { lock.current = false; if (alive.current) { setBusy(false); setStatus('') } }
  }
  const home = () => { patch({ view: 'home' }); setError('') }
  function learn(sec = selected) { patch({ section: sec?.id || 'all', view: 'study' }); setError('') }
  async function generate(r) {
    const n = r.items.length
    const pool = r.section ? sections.filter(s => s.id === r.section) : sections
    const sec = r.plan ? sections.find(s => s.id === r.plan[n]) : pool[n % pool.length]
    if (!sec) throw new Error(text('没有可用的小节。', 'No section is available.'))
    const candidates = TYPES.filter(type => type !== r.items.at(-1)?.q.type)
    const type = r.type === 'mixed' ? candidates[Math.floor(Math.random() * candidates.length)] : r.type
    const q = await api.generateQuestion({ topic: sec.title, type, difficulty: r.difficulty, language: lang, exclude_stems: [...(r.previousStems || []), ...r.items.map(x => x.q.stem)].slice(-50) })
    if (!q?.id || !q.stem || r.items.some(x => x.q.stem === q.stem)) throw new Error(text('未获取到新题，请重试。', 'No new question returned. Please retry.'))
    return { q, section: sec.id, answer: {}, grade: null, first: null, assisted: false, chat: [] }
  }
  function nextFree(restart = false) {
    if (restart && round && !window.confirm(text('重新开始此范围的练习？当前这轮记录将被替换。', 'Start over for this scope? This replaces the current round.'))) return
    task(async () => {
      const base = !restart && round ? round : { mode: 'free', section: selected?.id || '', title: selected?.title || chapter.title, items: [], cursor: 0 }
      if (!restart && base.cursor < base.items.length - 1) { updateRound(roundKey, r => ({ ...r, cursor: r.cursor + 1 })); return }
      const next = { ...base, difficulty: state.difficulty, type: state.type }
      const added = await generate(next)
      if (alive.current) setState(s => ({ ...s, active: studyKey, rounds: { ...s.rounds, [studyKey]: { ...next, items: [...next.items, added], cursor: next.items.length } } }))
    })
  }
  function startChallenge(restart = false) {
    const saved = state.rounds[challengeKey]
    if (saved && !restart) { patch({ active: challengeKey, view: saved.submitted ? 'result' : 'challenge' }); return }
    if (saved && !window.confirm(text('开始新的章节挑战？将替换上一轮记录。', 'Start a new challenge? This replaces the previous round.'))) return
    const next = { mode: 'challenge', title: chapter.title, difficulty: 'medium', type: 'mixed', plan: challengePlan(sections), items: [], cursor: 0, submitted: false, previousStems: saved?.items.map(x => x.q.stem) || [] }
    setState(s => ({ ...s, active: challengeKey, view: 'challenge', rounds: { ...s.rounds, [challengeKey]: next } }))
    prepareChallenge(next)
  }
  function prepareChallenge(base = round) {
    task(async () => {
      let work = base
      while (work.items.length < work.plan.length) {
        setStatus(text('正在准备题目 ', 'Preparing questions ') + (work.items.length + 1) + ' / ' + work.plan.length)
        const added = await generate(work)
        if (!alive.current) return
        work = { ...work, items: [...work.items, added] }
        const saved = work
        updateRound(challengeKey, () => saved)
      }
    })
  }
  async function grade(x) {
    const result = await api.gradeAnswer({ question_id: x.q.id, student_id: student || 'anon', class_id: classId, ...x.answer,
      ...(x.q.type === 'drag_order' ? { order: x.answer.order } : {}) })
    if (result._mock) throw new Error(text('批改暂不可用，答案已保留。若后端已重启，请开始新一轮。', 'Grading unavailable. Answers are saved. Start a new round if the backend restarted.'))
    return result
  }
  function submitFree() {
    task(async () => {
      const result = await grade(item)
      if (alive.current) updateItem(roundKey, round.cursor, { grade: result, first: item.first ?? { correct: result.correct, assisted: item.assisted } })
    })
  }
  function finishChallenge() {
    const missing = round.items.filter(x => !hasAnswer(x)).length
    if (!round.grading && !window.confirm(text(`确认交卷？还有 ${missing} 道未作答，交卷后不能修改本次答案。`, `Submit? ${missing} unanswered. Answers cannot be changed after submission.`))) return
    task(async () => {
      updateRound(roundKey, r => ({ ...r, grading: true }))
      for (let i = 0; i < round.items.length; i++) {
        const x = round.items[i]
        if (!hasAnswer(x) || x.grade) continue
        setStatus(text('正在批改 ', 'Checking ') + (i + 1) + ' / ' + round.items.length)
        const result = await grade(x)
        if (!alive.current) return
        updateItem(roundKey, i, { grade: result, first: { correct: result.correct, assisted: false } })
      }
      updateRound(roundKey, r => ({ ...r, submitted: true, grading: false }))
      patch({ view: 'result' })
    })
  }
  async function favorite() {
    task(async () => {
      const saved = favorites.find(f => f.question_id === item.q.id)
      const result = saved ? await api.deleteFavorite(item.q.id, student) : await api.addFavorite({ question_id: item.q.id, student_id: student, class_id: classId })
      if (result._mock) throw new Error(text('收藏失败，请重试。', 'Could not save favorite.'))
      setFavorites(f => saved ? f.filter(x => x.question_id !== item.q.id) : [...f, { ...item.q, question_id: item.q.id }])
    })
  }
  const savedChallenge = state.rounds[challengeKey]
  const summary = roundSummary(round)
  const localized = useTranslatedContent(item ? [item.q.stem, item.q.instructions, ...(item.q.options || []), ...(item.q.steps || []), item.grade?.feedback, item.grade?.correct_answer, ...(item.q.citations || []).map(c => c.title)] : [], lang)
  const tr = localized.translate
  const questionPanel = item && <>
    {localized.error && <p role="alert" className="note-tip">{text('翻译暂不可用，答案已保留。', 'Translation unavailable. Your answer is saved.')} <button className="btn sm" onClick={localized.retry}>{text('重试', 'Retry')}</button></p>}
    {localized.loading && <p role="status">{text('正在切换题目语言，答案保持不变…', 'Updating question language; your answer is unchanged…')}</p>}
    <div className="sw-questionnav" aria-label={text('本轮题目', 'Questions')}>{round.items.map((x, i) => <button key={x.q.id} disabled={busy} aria-current={i === round.cursor ? 'step' : undefined} className={i === round.cursor ? 'active' : ''} onClick={() => updateRound(roundKey, r => ({ ...r, cursor: i }))}>{i + 1}{hasAnswer(x) ? ' ·' : ''}</button>)}</div>
    <section className="sw-panel sw-question">
      <div className="sw-questionmeta"><span className="badge neutral">{t('diff_' + item.q.difficulty)}</span><span className="badge neutral">{t('qtype_' + item.q.type)}</span>
        <strong>{text('本题小节：', 'Section: ')}{displayLabel(item.q.topic, lang)}</strong>
        {(!challenge || reviewing) && <button className="btn sm ghost" disabled={busy || !student} onClick={favorite}>{favorites.some(f => f.question_id === item.q.id) ? t('practice_unfavorite') : t('practice_favorite')}</button>}</div>
      <MathText as="div" className="sw-stem">{tr(item.q.stem)}</MathText>
      {item.q.instructions && <MathText as="p" className="muted">{tr(item.q.instructions)}</MathText>}
      <div className="sw-answer"><h3>{t('practice_your_answer')}</h3><AnswerControls q={item.q} displayText={tr} answer={item.answer} disabled={localized.loading || localized.error || busy || reviewing || round.grading || (!challenge && item.grade?.correct)} setAnswer={answer => updateItem(roundKey, round.cursor, { answer, grade: null })} />
        {item.q.type === 'drag_order' && !hasAnswer(item) && !reviewing && <button className="btn sm" disabled={busy || round.grading} onClick={() => updateItem(roundKey, round.cursor, { answer: { order: [...item.q.steps] } })}>{text('确认当前顺序', 'Use this order')}</button>}</div>
      {item.grade && (!challenge || reviewing) && <div role="status" className={'grade-box ' + (item.grade.correct ? 'ok' : 'bad')}><MathText>{tr(item.grade.feedback)}</MathText>{item.grade.correct_answer && <MathText as="p">{tr(item.grade.correct_answer)}</MathText>}</div>}
      {reviewing && !hasAnswer(item) && <p className="note-tip">{text('本题未作答。可以向导师询问解题思路。', 'Unanswered. Ask your tutor how to approach it.')}</p>}
      <div className="sw-actions">{!challenge ? <><button className="btn" disabled={busy} onClick={() => nextFree()}>{text('下一题', 'Next question')}</button><button className="btn primary" disabled={localized.loading || localized.error || busy || !hasAnswer(item) || item.grade?.correct} onClick={submitFree}>{item.grade?.correct ? text('已答对', 'Correct') : t('practice_submit')}</button></> : <>
        <button className="btn" disabled={busy || round.cursor === 0} onClick={() => updateRound(roundKey, r => ({ ...r, cursor: r.cursor - 1 }))}>{text('上一题', 'Previous')}</button>
        {round.cursor < round.items.length - 1 && <button className="btn primary" disabled={busy} onClick={() => updateRound(roundKey, r => ({ ...r, cursor: r.cursor + 1 }))}>{text('下一题', 'Next question')}</button>}
        {reviewing ? <button className="btn" onClick={() => patch({ view: 'result' })}>{text('返回结果', 'Back to results')}</button> : <button className="btn" disabled={busy} onClick={finishChallenge}>{round.grading ? text('继续批改', 'Retry grading') : text('交卷', 'Submit challenge')}</button>}
      </>}</div>
      {(!challenge || reviewing) && item.q.citations?.length > 0 && <details className="sw-sources"><summary>{t('practice_citations')}</summary>{item.q.citations.map((c, i) => <p key={i}>{tr(c.title)} {c.page != null ? ' · p.' + c.page : ''}</p>)}</details>}
    </section>
    {(!challenge || reviewing) && <details className="sw-tutor-toggle" key={item.q.id}><summary>{text('问导师 · 卡住时在这里提问', 'Ask your tutor · get help with this question')}</summary><QuestionHelp {...{ item, lang, student, classId, busy, task }} onChange={fields => updateItem(roundKey, round.cursor, fields)} /></details>}
    {reviewing && <button className="btn sw-start" onClick={() => learn(sections.find(s => s.id === item.section))}>{text('去这个小节学习与练习', 'Learn and practice this section')}</button>}
  </>
  return <div className="sw">
    <header className="sw-header"><button className="sw-brand" disabled={busy} onClick={home}><span>∫</span><div>{text('微积分学习伙伴', 'Calculus Companion')}<small>{text('理解概念，练会方法', 'Understand the ideas. Practice the methods.')}</small></div></button>
      <div className="sw-account"><input className="inp" aria-label={t('stu_name')} placeholder={t('stu_name_ph')} defaultValue={student} disabled={busy} onBlur={e => onStudent(e.target.value.trim())} /><select className="inp" aria-label={t('stu_class')} value={classId} disabled={busy} onChange={e => onClass(e.target.value)}>{classes.map(c => <option key={c.id} value={c.id}>{displayLabel(c.label, lang)}</option>)}</select><details className="sw-preferences"><summary>{text('设置', 'Settings')}</summary><div>{topbar}</div></details></div></header>
    <main className="sw-main"><div className="sw-chapterbar"><label><span className="sw-eyebrow">{text('当前章节', 'YOUR CHAPTER')}</span><select aria-label={text('选择章节', 'Choose chapter')} disabled={busy} value={chapter?.id || ''} onChange={e => { patch({ chapter: e.target.value, section: '', view: 'home' }); setError('') }}>{chapters.map(c => <option key={c.id} value={c.id}>{displayLabel(c.title, lang)}</option>)}</select></label><nav aria-label={text('章节导航', 'Chapter navigation')}><button className="btn" disabled={busy} onClick={home}>{text('章节首页', 'Chapter home')}</button><button className="btn" disabled={busy} onClick={() => patch({ view: 'favorites' })}>{t('stu_favorites')}</button></nav></div>
      {catalog?._mock && <p role="alert" className="note-tip">{text('教材服务未连接，暂时展示示例目录。请启动后端并刷新。', 'Textbook service unavailable. Showing a sample catalog; start the backend and refresh.')}</p>}
      {storageError && <p role="alert">{text('浏览器无法保存进度。', 'Browser progress could not be saved.')}</p>}
      {error && <p role="alert" className="grade-box bad">{error}</p>}
      {busy && <p role="status">{status || text('正在处理，请稍候。', 'Working, please wait.')}</p>}
      {!chapter ? <Loading rows={2} /> : state.view === 'home' ? <>
        <section className="sw-intro sw-home-intro"><div><span className="sw-eyebrow">{text('你的章节学习空间', 'YOUR CHAPTER WORKSPACE')}</span><h1>{text('学懂概念，检验收获。', 'Build understanding. Check your progress.')}</h1><p>{text('从小节开始学与练，或直接挑战本章。按自己的节奏选择。', 'Learn and practice a section, or check the chapter. Choose what you need today.')}</p></div></section>
        <div className="sw-entry-grid">
          <section className="sw-entry sw-entry-learn" aria-labelledby="learn-entry-title">
            <div className="sw-entry-top"><span className="sw-entry-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"><path d="M12 5v15M3 4c3-1 6-1 9 1 3-2 6-2 9-1v15c-3-1-6-1-9 1-3-2-6-2-9-1z" /></svg></span><span className="sw-entry-label">{text('边学边练', 'LEARN AT YOUR PACE')}</span></div>
            <h2 id="learn-entry-title">{text('学习与练习', 'Learn & practice')}</h2><p className="sw-entry-description">{text('选择一个小节，直接看概念、做练习。遇到困难，随时问导师。', 'Choose a section to explore concepts and practice. Ask your tutor whenever you get stuck.')}</p>
            <div className="sw-section-directory sw-inline-directory" aria-label={text('选择学习小节', 'Choose a section to learn')}>
          <div className="sw-section-grid">{sections.map((sec, i) => <button className={'sw-section-card ' + (state.section === sec.id ? 'selected' : '')} key={sec.id} disabled={busy} onClick={() => learn(sec)}><span className="sw-section-number" aria-hidden="true">{String(i + 1).padStart(2, '0')}</span><div><strong>{displayLabel(sec.title, lang)}</strong><span>{state.rounds[chapter.id + ':free:' + sec.id] ? text('继续上次练习', 'Resume your practice') : text('概念 · 例题 · 练习', 'Concepts · examples · practice')}</span></div><span className="sw-section-arrow" aria-hidden="true">→</span></button>)}</div>
            </div>
            <button className="btn sw-mixed-entry" disabled={busy} onClick={() => learn(null)}>{text('全章综合练习', 'Mixed chapter practice')} <span aria-hidden="true">→</span></button>
          </section>
          <section className="sw-entry sw-entry-challenge" aria-labelledby="challenge-entry-title">
            <div className="sw-entry-top"><span className="sw-entry-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"><path d="M7 3h10v5a5 5 0 0 1-10 0zM7 5H3v2a4 4 0 0 0 5 4M17 5h4v2a4 4 0 0 1-5 4M12 13v5M8 21h8M9 18h6v3H9z" /></svg></span><span className="sw-entry-label">{text('独立检验', 'CHECK YOUR UNDERSTANDING')}</span>{savedChallenge && <span className="sw-entry-status">{savedChallenge.submitted ? text('已有结果', 'Results ready') : text('进行中', 'In progress')}</span>}</div>
            <h2 id="challenge-entry-title">{text('章节挑战', 'Chapter challenge')}</h2><p className="sw-entry-description">{text('用一组题检验本章学习成果。先独立作答，交卷后查看反馈。', 'Put this chapter into practice independently. Submit your answers, then review your feedback.')}</p>
            <div className="sw-entry-tags"><span>{text(`${sections.length} 道题 · 每小节一道`, `${sections.length} questions · one per section`)}</span><span>{text('交卷后开放导师', 'Tutor after submission')}</span></div>
            <div className="sw-entry-action"><button className="btn sw-challenge-button" disabled={busy || !sections.length} onClick={() => patch({ view: 'challenge-intro' })}>{savedChallenge?.submitted ? text('查看挑战结果', 'View results') : savedChallenge ? text('继续挑战', 'Resume challenge') : text('开始章节挑战', 'Start chapter challenge')} <span aria-hidden="true">→</span></button><span className="sw-entry-context">{text('不计时，可中途暂停', 'No timer. Pause anytime.')}</span></div>
          </section>
        </div>
        <p className="sw-footnote">{text('进度保存在当前浏览器，按姓名和班级分别记录。', 'Progress is saved in this browser for each name and class.')}</p>
      </> : state.view === 'study' ? <div className="sw-study-layout"><aside className="sw-section-sidebar"><h2>{text('学习小节', 'Sections')}</h2>{sections.map(sec => <button key={sec.id} disabled={busy} aria-current={selected?.id === sec.id ? 'page' : undefined} onClick={() => learn(sec)}>{displayLabel(sec.title, lang)}</button>)}<button disabled={busy} aria-current={!selected ? 'page' : undefined} onClick={() => learn(null)}>{text('全章综合练习', 'Mixed chapter practice')}</button></aside><div className="sw-study-content">
        <span className="sw-eyebrow">{text('学习与练习', 'LEARN & PRACTICE')}</span><h1>{selected ? displayLabel(selected.title, lang) : text('全章综合练习', 'Mixed chapter practice')}</h1>
        {selected && <StudyNotes key={selected.id} topic={selected.title} lang={lang} />}
        {!selected && <p className="note-tip">{text('题目依次覆盖本章小节，每题都标明来源小节。', 'Questions rotate through this chapter, with the section shown on each question.')}</p>}
        <div className="sw-practice-heading"><h2>{text('做题练习', 'Practice')}</h2><label>{t('practice_difficulty')} <select className="inp" disabled={busy} value={state.difficulty} onChange={e => patch({ difficulty: e.target.value })}>{DIFFS.map(d => <option key={d} value={d}>{t('diff_' + d)}</option>)}</select></label></div>
        <details className="sw-settings"><summary>{text('练习设置', 'Practice settings')}</summary><label>{t('practice_qtype')} <select className="inp" disabled={busy} value={state.type} onChange={e => patch({ type: e.target.value })}><option value="mixed">{text('混合题型', 'Mixed formats')}</option>{TYPES.map(type => <option key={type} value={type}>{t('qtype_' + type)}</option>)}</select></label><p className="sw-small">{text('设置应用于下一道新题，当前答案保留。', 'Settings apply to the next new question. Your current answer is kept.')}</p>{round && <button className="btn sm" disabled={busy} onClick={() => nextFree(true)}>{text('重新开始本范围练习', 'Start this practice over')}</button>}</details>
        {item ? questionPanel : <section className="sw-panel sw-empty"><h3>{text('准备好，练一道？', 'Ready to try a question?')}</h3><p className="muted">{text('可以直接做题，也可以先看看上面的概念。', 'Start now, or explore the concept above first.')}</p><button className="btn primary" disabled={busy || catalog?._mock} onClick={() => nextFree()}>{text('开始练习', 'Start practicing')}</button></section>}
      </div></div> : state.view === 'challenge-intro' ? <section className="sw-panel sw-focus"><span className="sw-eyebrow">{text('章节挑战', 'CHAPTER CHALLENGE')}</span><h2>{displayLabel(chapter.title, lang)}</h2><p>{text(`共 ${sections.length} 道题，每小节抽取一道，中等难度、混合题型。`, `${sections.length} questions, one per section, at medium difficulty with mixed formats.`)}</p><p>{text('独立作答，可以跳过和返回修改；交卷后开放反馈、教材和导师。可以随时返回学习，挑战进度会保留。', 'Work independently. Skip and revisit questions before submitting. Feedback, textbook and tutor become available after submission. You can leave to study and resume later.')}</p><p className="note-tip">{text('这是一次学习自检，不代表整章掌握程度。当前不设通过分数。', 'This is a learning check, not a certification of chapter mastery. No pass threshold is set.')}</p><div className="sw-actions"><button className="btn" onClick={home}>{text('返回学习', 'Back to learning')}</button><button className="btn primary" disabled={busy || !sections.length || catalog?._mock} onClick={() => startChallenge()}>{savedChallenge?.submitted ? text('查看结果', 'View results') : savedChallenge ? text('继续挑战', 'Resume challenge') : text('开始挑战', 'Start challenge')}</button></div></section>
      : state.view === 'favorites' ? <Favorites favorites={favorites} onBack={home} onRemove={id => task(async () => { const r = await api.deleteFavorite(id, student); if (r._mock) throw new Error(text('删除失败，请重试。', 'Could not remove favorite.')); setFavorites(f => f.filter(x => x.question_id !== id)) })} onPractice={f => {
        const ch = chapters.find(c => c.sections.some(s => s.title === f.topic)); const sec = ch?.sections.find(s => s.title === f.topic)
        if (!ch || !sec) { setError(text('未找到此题对应的小节。', 'The section for this question was not found.')); return }
        const key = ch.id + ':free:' + sec.id
        setState(s => { const base = s.rounds[key] || { mode: 'free', section: sec.id, title: sec.title, items: [] }; const index = base.items.findIndex(x => x.q.id === f.question_id); const items = index >= 0 ? base.items : [...base.items, { q: { ...f, id: f.question_id }, section: sec.id, answer: {}, chat: [] }]; return { ...s, chapter: ch.id, section: sec.id, view: 'study', active: key, rounds: { ...s.rounds, [key]: { ...base, items, cursor: index >= 0 ? index : items.length - 1 } } } })
      }} /> : challenge ? <div className="sw-focus"><div className="sw-focushead"><button className="btn ghost" disabled={busy} onClick={home}>← {text('返回学习（保留进度）', 'Back to learning (progress saved)')}</button><span>{text('章节挑战', 'Chapter challenge')}</span></div><h2>{displayLabel(round.title, lang)}</h2>
        {state.view === 'result' && reviewing ? <section className="sw-panel sw-result"><h2>{text('看看这次的表现', 'Review this attempt')}</h2><p>{text('结果只反映这组题目的表现，不能代表整个小节或整章的掌握程度。', 'These results describe this set of questions, not mastery of a section or chapter.')}</p><div className="sw-resultstats"><div><b>{summary.correct}</b>{text('答对', 'Correct')}</div><div><b>{summary.incorrect}</b>{text('答错', 'Incorrect')}</div><div><b>{summary.unanswered}</b>{text('未作答', 'Unanswered')}</div></div>{round.items.map((x, i) => <div className="sw-result-row" key={x.q.id}><button className="sw-reviewrow" onClick={() => { updateRound(roundKey, r => ({ ...r, cursor: i })); patch({ view: 'review' }) }}><span>{i + 1}. {displayLabel(x.q.topic, lang)}</span><strong>{!hasAnswer(x) ? text('未作答', 'Unanswered') : x.grade?.correct ? text('答对', 'Correct') : text('答错', 'Incorrect')} →</strong></button>{!x.grade?.correct && <button className="btn sm ghost" onClick={() => learn(sections.find(s => s.id === x.section))}>{text('去这个小节练习', 'Practice this section')}</button>}</div>)}<div className="sw-actions"><button className="btn" onClick={() => startChallenge(true)}>{text('重新挑战', 'New challenge')}</button><button className="btn primary" onClick={home}>{text('返回学习', 'Back to learning')}</button></div></section>
        : round.items.length < round.plan.length ? <section className="sw-panel"><h3>{text('正在准备整章题目', 'Preparing your chapter challenge')}</h3><p>{round.items.length} / {round.plan.length} {text('道已准备。准备完后统一开始。', 'ready. Your challenge starts when all questions are ready.')}</p><button className="btn" disabled={busy} onClick={() => prepareChallenge()}>{text('继续准备', 'Continue preparation')}</button><button className="btn ghost" disabled={busy} onClick={() => startChallenge(true)}>{text('重新准备', 'Start over')}</button></section>
        : <>{!reviewing && <p className="note-tip">{text(`已作答 ${round.items.filter(hasAnswer).length} / ${round.items.length}。可以返回修改；交卷后再看反馈和询问导师。`, `${round.items.filter(hasAnswer).length} / ${round.items.length} answered. Revisit before submitting; feedback and tutor follow submission.`)}</p>}{questionPanel}{round.grading && <p role="alert">{text('已确认交卷，答案已锁定。若批改中断，请点击“继续批改”。', 'Submission confirmed; answers are locked. If interrupted, use Retry grading.')}</p>}{!reviewing && <button className="btn ghost" disabled={busy} onClick={() => startChallenge(true)}>{text('放弃本轮并重新开始', 'Discard this attempt and restart')}</button>}</>}
      </div> : <button className="btn" onClick={home}>{text('返回章节首页', 'Back to chapter')}</button>}
    </main>
  </div>
}
function StudyNotes({ topic, lang }) {
  const [card, setCard] = useState(null)
  const [expanded, setExpanded] = useState(false)
  useEffect(() => { let alive = true; api.getConcept(topic).then(c => { if (alive) setCard(c) }); return () => { alive = false } }, [topic])
  const zh = lang === 'zh'
  const translated = useTranslatedContent(card ? [card.summary, card.definition] : [], lang)
  if (translated.error) return <p role="alert">{zh ? '概念翻译暂不可用。' : 'Concept translation unavailable.'} <button className="btn" onClick={translated.retry}>{zh ? '重试' : 'Retry'}</button></p>
  if (!card || translated.loading) return <Loading rows={2} />
  if (card._mock) return <p className="note-tip">{zh ? '教材暂时无法读取，请检查后端后刷新。' : 'Textbook unavailable. Check the backend and refresh.'}</p>
  const formulas = card.content?.find(b => b.content_type === 'concept')?.formulas || card.formulas || []
  return <section className="sw-concept-preview"><span className="sw-eyebrow">{zh ? '核心概念' : 'CORE IDEA'}</span><MathText as="p">{translated.translate(card.summary || card.definition)}</MathText>{formulas.slice(0, 2).map((f, i) => <Formula key={i}>{f}</Formula>)}<details onToggle={e => setExpanded(e.currentTarget.open)}><summary>{zh ? '查看教材、例题与插图' : 'Explore the textbook, examples and figures'}</summary>{expanded && <div className="sw-material"><Concept topic={topic} embedded /></div>}</details></section>
}
function QuestionHelp({ item, lang, student, classId, busy, task, onChange }) {
  const zh = lang === 'zh'
  const chatTranslations = useTranslatedContent((item.chat || []).filter(m => m.role === 'assistant').flatMap(m => [m.content, ...(m.citations || []).map(c => c.title)]), lang)
  const input = item.helpDraft || ''
  const setInput = helpDraft => onChange({ helpDraft })
  const [open, setOpen] = useState(false)
  async function ask(message) {
    if (!message.trim()) return
    await task(async () => {
      onChange({ assisted: true })
      let sid = item.sid
      if (!sid) {
        const start = await api.startSession({ problem_id: item.q.id || null, topic: item.q.topic, student_id: student || 'anon', class_id: classId, language: lang, condition: 'explain' })
        if (start._mock) throw new Error(zh ? '导师暂不可用，请稍后重试。' : 'Tutor unavailable. Please retry later.')
        sid = start.session_id
        onChange({ sid, assisted: true })
      }
      const context = JSON.stringify({ question: item.q.stem, options: item.q.options, steps: item.q.steps, current_answer: item.answer, grading_feedback: item.grade?.feedback, question_from_student: message })
      const reply = await api.sendMessage(sid, context, lang, { topic: item.q.topic })
      if (reply._mock) { onChange({ sid: null }); throw new Error(zh ? '导师回复失败，输入已保留，请重试。' : 'Tutor reply failed. Your input is kept; please retry.') }
      onChange({ sid, assisted: true, chat: [...(item.chat || []), { role: 'user', content: message }, { role: 'assistant', content: reply.tutor_message, citations: reply.citations }] })
      setInput(''); setOpen(true)
    })
  }
  return <section className="sw-help"><div className="sw-helphead"><span className="sw-modeicon">✧</span><div><h3>{zh ? '对这道题有疑问？' : 'A question about this problem?'}</h3><p>{zh ? '告诉导师你卡在哪一步，答案会留在上面。' : 'Tell your tutor where you got stuck. Your answer stays above.'}</p></div>
    {!!item.chat?.length && <button className="btn sm" onClick={() => setOpen(!open)} aria-expanded={open}>{open ? (zh ? '收起讨论' : 'Collapse') : (zh ? '查看讨论' : 'Show discussion')}</button>}</div>
    <div className="row wrap">{[zh ? '给我一点提示' : 'Give me a hint', zh ? '帮我检查当前思路' : 'Check my current reasoning'].map(p => <button key={p} className="chip" disabled={busy} onClick={() => ask(p)}>{p}</button>)}</div>
    {chatTranslations.error && <p role="alert">{zh ? '回复翻译暂不可用。' : 'Reply translation unavailable.'}<button className="btn sm" onClick={chatTranslations.retry}>{zh ? '重试' : 'Retry'}</button></p>}
    {open && <div className="sw-discussion" aria-live="polite">{item.chat?.map((m, i) => <div key={i} className={'sw-message ' + m.role}><strong>{m.role === 'user' ? (zh ? '我' : 'You') : (zh ? '导师' : 'Tutor')}</strong><MathText as="div">{m.role === 'assistant' ? chatTranslations.translate(m.content) : m.content}</MathText>{m.citations?.map((c, j) => <small key={j}>{chatTranslations.translate(c.title)} {c.page != null ? ' · p.' + c.page : ''}</small>)}</div>)}</div>}
    <form className="sw-helpinput" onSubmit={e => { e.preventDefault(); ask(input) }}><textarea className="inp" rows={2} aria-label={zh ? '向导师提问' : 'Ask the tutor'} placeholder={zh ? '说说你卡在哪一步……' : 'Where did you get stuck?'} value={input} onChange={e => setInput(e.target.value)} disabled={busy} /><button className="btn primary" disabled={busy || !input.trim()}>{zh ? '发送' : 'Send'}</button></form>
    {!!item.chat?.length && <small className="muted">{zh ? '参考提示后，可以回到上方修改答案并重新提交。导师讨论不会改变判题结果。' : 'Use the hint to revise and resubmit above. Discussion does not change your recorded result.'}</small>}
  </section>
}
