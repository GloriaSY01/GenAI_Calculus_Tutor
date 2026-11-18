import { preloadTranslatedContent, useTranslatedContent } from '../useTranslatedContent.js'
import { useEffect, useMemo, useRef, useState } from 'react'
import { ArrowRight, BookOpenCheck, GraduationCap, IdCard, LogOut, Sparkles, UserRound, UsersRound } from 'lucide-react'
import { useLang } from '../i18n.jsx'
import { api } from '../api.js'
import { MathText, Formula } from '../components/math.jsx'
import { Loading } from '../components/ui.jsx'
import { displayLabel } from '../localization.js'
import { AnswerControls } from './student/Practice.jsx'
import Concept from './student/Concept.jsx'
import Favorites from './student/Favorites.jsx'
import StudentAgent from './StudentAgent.jsx'
import { createLearningClient } from '../learning.js'
import { hasAnswer, challengePlan, roundSummary } from './student/study.js'
import './student/workspace.css'

const TYPES = ['single_choice', 'multiple_choice', 'fill_blank', 'drag_order']
const DIFFS = ['easy', 'medium', 'hard']
const STUDY_STATE_VERSION = 6
const PRACTICE_BEHAVIOR_VERSION = 6
const fresh = () => ({ chapter: '', section: '', view: 'home', active: '', rounds: {}, difficulty: 'easy', type: 'single_choice' })
function sanitizeSavedState(savedState) {
  const rounds = Object.fromEntries(
    Object.entries(savedState.rounds || {}).filter(([, round]) =>
      (round.items || []).every(item => item.q?.quality_version >= 2),
    ).map(([key, round]) => [key, { ...round, items: round.items.map(item => ({ ...item, trackingId: item.trackingId || crypto.randomUUID() })) }]),
  )
  const active = rounds[savedState.active] ? savedState.active : ''
  const view = savedState.active && !active ? 'home' : savedState.view
  return { ...savedState, rounds, active, view }
}
function read(key) {
  try { const saved = JSON.parse(localStorage.getItem(key)); return saved?.version === STUDY_STATE_VERSION && saved.state?.rounds ? { ...fresh(), ...sanitizeSavedState(saved.state) } : fresh() }
  catch { return fresh() }
}
export default function StudentWorkspace({ topbar }) {
  const { t, lang } = useLang()
  const [student, setStudent] = useState(() => localStorage.getItem('stu_name') || '')
  const [studentNumber, setStudentNumber] = useState(() => localStorage.getItem('stu_number') || '')
  const [classId, setClassId] = useState(() => localStorage.getItem('stu_class') || '')
  const [profile, setProfile] = useState(null)
  const [catalog, setCatalog] = useState(null)
  const [classes, setClasses] = useState([])
  const [classStatus, setClassStatus] = useState('loading')
  const [classError, setClassError] = useState('')
  const [classReload, setClassReload] = useState(0)
  useEffect(() => {
    api.getCatalog().then(setCatalog)
  }, [])
  useEffect(() => {
    let current = true
    setClassStatus('loading'); setClassError('')
    api.learningClasses().then(options => {
      if (!current) return
      setClasses(options)
      setClassId(previous => {
        // Never silently assign an obsolete/demo identifier to a real class.
        const selected = options.some(c => c.id === previous) ? previous : ''
        localStorage.setItem('stu_class', selected)
        return selected
      })
      setClassStatus('ready')
    }).catch(e => { if (current) { setClassError(e.message); setClassStatus('error') } })
    return () => { current = false }
  }, [classReload])
  function signIn() {
    const name = student.trim()
    const number = studentNumber.trim().toUpperCase()
    if (!name || !number || !classes.some(item => item.id === classId)) return
    localStorage.setItem('stu_name', name)
    localStorage.setItem('stu_number', number)
    localStorage.setItem('stu_class', classId)
    setStudent(name); setStudentNumber(number)
    setProfile({ student: name, studentNumber: number, classId, signedInAt: Date.now() })
  }
  if (!profile) return <StudentSignIn {...{
    lang, student, studentNumber, classId, classes, classStatus, classError,
    setStudent, setStudentNumber, setClassId, signIn,
  }} onReload={() => setClassReload(n => n + 1)} />
  const scope = JSON.stringify([profile.studentNumber, profile.classId])
  const classLabel = displayLabel(classes.find(item => item.id === profile.classId)?.label || profile.classId, lang)
  return <Workspace key={`${profile.signedInAt}:practice-${PRACTICE_BEHAVIOR_VERSION}`} {...{ topbar, t, lang, ...profile, classes, classLabel, catalog, scope }}
    onReloadClasses={() => setClassReload(n => n + 1)} onSignOut={() => setProfile(null)} />
}

function StudentSignIn({ lang, student, studentNumber, classId, classes, classStatus, classError, setStudent, setStudentNumber, setClassId, signIn, onReload }) {
  const zh = lang === 'zh'
  const valid = student.trim() && studentNumber.trim() && classes.some(item => item.id === classId)
  return <main className="student-login">
    <section className="student-login-shell" aria-labelledby="student-login-title">
      <div className="student-login-welcome">
        <span className="student-login-kicker">WELCOME</span>
        <div className="student-login-mark" aria-hidden="true">∫</div>
        <h1>{zh ? '欢迎来到微积分学习伙伴' : 'Welcome to Calculus Companion'}</h1>
        <p>{zh ? '和导学 Agent 一起理解概念、梳理解题思路，并通过练习逐步巩固。' : 'Learn concepts, reason through problems, and strengthen your understanding with a guided calculus agent.'}</p>
        <div className="student-login-agent"><Sparkles aria-hidden="true" /><div><strong>{zh ? '微积分导学 Agent' : 'Calculus Learning Agent'}</strong><span>{zh ? '先理解，再提示，陪你把思路讲清楚' : 'Understand first, then guide your reasoning'}</span></div></div>
        <div className="student-login-path" aria-label={zh ? '学习路径' : 'Learning path'}><span><BookOpenCheck />{zh ? '理解概念' : 'Learn'}</span><span><GraduationCap />{zh ? '练习方法' : 'Practice'}</span><span><Sparkles />{zh ? '获得引导' : 'Get guidance'}</span></div>
      </div>
      <form className="student-login-form" onSubmit={event => { event.preventDefault(); signIn() }}>
        <div className="student-login-form-head"><span>{zh ? '学生登录' : 'Student sign in'}</span><h2 id="student-login-title">{zh ? '开始今天的学习' : 'Start learning today'}</h2><p>{zh ? '请填写真实信息，学习进度和做题记录将保存到你的账户。' : 'Enter your details so your progress and answers can be saved.'}</p></div>
        <label><span>{zh ? '姓名' : 'Name'}</span><div className="student-login-input"><UserRound aria-hidden="true" /><input autoFocus autoComplete="name" value={student} onChange={event => setStudent(event.target.value)} placeholder={zh ? '请输入姓名' : 'Enter your name'} required /></div></label>
        <label><span>{zh ? '学号' : 'Student number'}</span><div className="student-login-input"><IdCard aria-hidden="true" /><input autoComplete="username" value={studentNumber} onChange={event => setStudentNumber(event.target.value)} placeholder={zh ? '请输入学号' : 'Enter your student number'} required /></div></label>
        <label><span>{zh ? '班级' : 'Class'}</span><div className="student-login-input"><UsersRound aria-hidden="true" /><select value={classId} onChange={event => setClassId(event.target.value)} disabled={classStatus !== 'ready'} required><option value="">{classStatus === 'loading' ? (zh ? '正在读取班级…' : 'Loading classes…') : (zh ? '请选择班级' : 'Select your class')}</option>{classes.map(item => <option key={item.id} value={item.id}>{displayLabel(item.label, lang)}</option>)}</select></div></label>
        {classStatus === 'error' && <div className="student-login-error" role="alert">{zh ? '班级列表加载失败，请重试。' : 'Could not load classes. Please retry.'} <button type="button" onClick={onReload}>{zh ? '重新加载' : 'Reload'}</button><small>{classError}</small></div>}
        <button className="student-login-submit" type="submit" disabled={!valid}>{zh ? '进入学习空间' : 'Enter learning space'}<ArrowRight aria-hidden="true" /></button>
        <p className="student-login-note">{zh ? '本次登录时间、学习进度、作答与 Agent 对话将与该学号关联保存。' : 'Your login time, progress, answers, and Agent conversations will be linked to this student number.'}</p>
      </form>
    </section>
  </main>
}

function Workspace({ topbar, t, lang, student, studentNumber, classId, classes, classLabel, signedInAt, catalog, scope, onSignOut, onReloadClasses }) {
  const text = (zh, en) => lang === 'zh' ? zh : en
  const storageKey = `calculus-study-v${STUDY_STATE_VERSION}:` + scope
  const [state, setState] = useState(() => read(storageKey))
  const [busy, setBusy] = useState(false)
  const [confirmingSubmit, setConfirmingSubmit] = useState(false)
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')
  const [storageError, setStorageError] = useState(false)
  const learning = useMemo(() => createLearningClient(studentNumber, classId, signedInAt), [studentNumber, classId, signedInAt])
  const classConfirmed = classes.some(c => c.id === classId)
  const [runInfo, setRunInfo] = useState(null)
  const [connecting, setConnecting] = useState(false)
  const [trackingError, setTrackingError] = useState('')
  const [trackingRetry, setTrackingRetry] = useState(0)
  const [favorites, setFavorites] = useState([])
  const favoriteOwner = runInfo?.student_id
  const lock = useRef(false)
  const prefetched = useRef(null)
  const alive = useRef(true)
  useEffect(() => { alive.current = true; return () => { alive.current = false } }, [])
  useEffect(() => {
    let current = true
    if (!classConfirmed) return () => { current = false }
    setConnecting(true)
    learning.connect({ studentName: student, studentNumber }).then(result => { if (current) setRunInfo(result) })
      .catch(e => { if (current) { setError(e.message); if (e.code === 'UNKNOWN_CLASS') onReloadClasses() } })
      .finally(() => { if (current) setConnecting(false) })
    return () => { current = false }
  }, [learning, classConfirmed])
  useEffect(() => {
    try { localStorage.setItem(storageKey, JSON.stringify({ version: STUDY_STATE_VERSION, state })); setStorageError(false) }
    catch { setStorageError(true) }
  }, [state, storageKey])
  useEffect(() => { let current = true; if (favoriteOwner) api.getFavorites(favoriteOwner).then(r => { if (current) setFavorites(r.favorites || []) }); return () => { current = false } }, [favoriteOwner])
  const chapters = catalog?.chapters || []
  const chapter = chapters.find(c => c.id === state.chapter) || chapters[0]
  const sections = chapter?.sections || []
  const selected = sections.find(s => s.id === state.section) || (state.section === 'all' ? null : sections[0])
  const activeRound = chapter && state.active.startsWith(chapter.id + ':') ? state.rounds[state.active] : null
  const studyKey = chapter?.id + ':free:' + (selected?.id || 'all')
  const prefetchKey = studyKey + ':' + state.difficulty + ':' + state.type + ':' + lang
  const challengeKey = chapter?.id + ':challenge'
  const roundKey = state.view === 'study' ? studyKey : state.active
  const round = state.view === 'study' ? state.rounds[studyKey] : activeRound
  const item = round?.items[round.cursor]
  const challenge = round?.mode === 'challenge'
  const reviewing = challenge && !!round.submitted
  const questionVisible = !!item && ['study', 'challenge', 'review'].includes(state.view) &&
    (!challenge || round.items.length === round.plan.length)
  useEffect(() => {
    if (!round || challenge || state.view !== 'study' || round.cursor < round.items.length - 1) return
    if (prefetched.current?.key === prefetchKey) return
    const base = { ...round, difficulty: state.difficulty, type: state.type }
    prefetched.current = {
      key: prefetchKey,
      promise: generate(base).then(async added => {
        await preloadTranslatedContent([
          added.q.stem, added.q.instructions, ...(added.q.options || []),
          ...(added.q.steps || []), ...(added.q.citations || []).map(c => c.title),
        ], lang)
        return added
      }).catch(() => null),
    }
  }, [item?.trackingId, prefetchKey, state.view, challenge])
  useEffect(() => {
    let current = true
    const recordPresentation = () => {
      if (!runInfo || !questionVisible || document.visibilityState !== 'visible') return
      learning.expose(item, round.mode).then(() => { if (current) setTrackingError('') })
        .catch(e => { if (current) setTrackingError(e.message) })
    }
    recordPresentation()
    document.addEventListener('visibilitychange', recordPresentation)
    return () => { current = false; document.removeEventListener('visibilitychange', recordPresentation) }
  }, [learning, runInfo, item?.trackingId, questionVisible, round?.mode, trackingRetry])
  const patch = fields => setState(s => ({ ...s, ...fields }))
  const updateRound = (key, fn) => setState(s => ({ ...s, rounds: { ...s.rounds, [key]: fn(s.rounds[key]) } }))
  const updateItem = (key, index, fields) => updateRound(key, r => ({ ...r, items: r.items.map((x, i) => i === index ? { ...x, ...fields } : x) }))
  async function task(fn) {
    if (lock.current) return
    lock.current = true; setBusy(true); setError('')
    try { await fn() } catch (e) { if (alive.current) setError(
      e.code === 'QUESTION_GENERATION_EXHAUSTED'
        ? text('当前设置暂时没有更多新题，请重试或切换题型、难度。', 'No more new questions are available for these settings. Retry or change the type or difficulty.')
        : e.message
    ) }
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
    const excluded = [...(r.previousStems || []), ...r.items.map(x => x.q.stem)].slice(-50)
    let q
    try {
      q = await api.generateQuestion({ topic: sec.title, type, difficulty: r.difficulty, language: lang, purpose: r.mode === 'challenge' ? 'challenge' : 'practice', exclude_stems: excluded })
    } catch (generationError) {
      if (generationError.code !== 'QUESTION_GENERATION_EXHAUSTED') throw generationError
      // A remote generator may have a smaller pool than the local authored
      // bank. Keep the flow moving while still preventing an immediate repeat.
      q = await api.generateQuestion({ topic: sec.title, type, difficulty: r.difficulty, language: lang, purpose: r.mode === 'challenge' ? 'challenge' : 'practice', exclude_stems: excluded.slice(-1) })
    }
    const previousStem = r.items.at(-1)?.q.stem
    if (!q?.id || !q.stem || q.stem === previousStem) throw new Error(text('新题生成失败，请再点一次下一题。', 'The next question could not be generated. Please try once more.'))
    const generated = { q, trackingId: crypto.randomUUID(), section: sec.id, answer: {}, grade: null, first: null, assisted: false, chat: [] }
    await learning.expose(generated, r.mode, false)
    return generated
  }
  function nextFree() {
    task(async () => {
      const base = round || { mode: 'free', section: selected?.id || '', title: selected?.title || chapter.title, items: [], cursor: 0 }
      if (base.cursor < base.items.length - 1) { updateRound(roundKey, r => ({ ...r, cursor: r.cursor + 1 })); return }
      const next = { ...base, difficulty: state.difficulty, type: state.type }
      let added = null
      if (prefetched.current?.key === prefetchKey) {
        added = await prefetched.current.promise
        prefetched.current = null
      }
      if (!added) added = await generate(next)
      if (alive.current) setState(s => ({ ...s, active: studyKey, rounds: { ...s.rounds, [studyKey]: { ...next, items: [...next.items, added], cursor: next.items.length } } }))
    })
  }
  function changePracticeSetting(key, value) {
    const settings = { difficulty: state.difficulty, type: state.type, [key]: value }
    setState(s => ({ ...s, ...settings }))
    prefetched.current = null
    if (!round || busy) return
    task(async () => {
      const base = {
        mode: 'free', section: selected?.id || '', title: selected?.title || chapter.title,
        items: [], cursor: 0, ...settings,
        previousStems: [...(round.previousStems || []), ...round.items.map(entry => entry.q.stem)].slice(-50),
      }
      const added = await generate(base)
      if (alive.current) setState(s => ({ ...s, ...settings, active: studyKey, view: 'study',
        rounds: { ...s.rounds, [studyKey]: { ...base, items: [added], cursor: 0 } } }))
    })
  }
  function startChallenge(restart = false) {
    const saved = state.rounds[challengeKey]
    if (saved && !restart) {
      patch({ active: challengeKey, view: saved.submitted ? 'result' : 'challenge' })
      if (!saved.submitted && saved.items.length < saved.plan.length) prepareChallenge(saved)
      return
    }
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
    return learning.submit(x, round.mode)
  }
  function submitFree() {
    if (lock.current) return
    lock.current = true; setBusy(true); setError('')
    grade(item).then(result => {
      if (alive.current && result.recovered) setError(text('已恢复上次提交的答案与结果；若要修改答案，请重新选择后提交。', 'Recovered the previous submission and answer. Select your revised answer to submit a new attempt.'))
      if (alive.current) updateItem(roundKey, round.cursor, { grade: result, answer: result.submitted_answer,
        attemptNo: result.attempt_no, assisted: result.assistance_status === 'received', gradeError: null,
        first: item.first ?? { correct: result.correct, assisted: result.assistance_status === 'received' } })
      if (result.correct && !challenge && prefetched.current?.key !== prefetchKey) {
        const nextRound = { ...round, items: round.items.map((entry, index) => index === round.cursor ? { ...entry, grade: result } : entry) }
        prefetched.current = {
          key: prefetchKey,
          promise: generate(nextRound).catch(() => null),
        }
      }
    }).catch(e => {
      if (!alive.current) return
      setError(e.message)
      if (e.status === 404 || e.code === 'QUESTION_EXPIRED') {
        updateItem(roundKey, round.cursor, { gradeError: 'expired' })
      } else {
        updateItem(roundKey, round.cursor, { gradeError: 'unavailable' })
      }
    }).finally(() => {
      lock.current = false
      if (alive.current) { setBusy(false); setStatus('') }
    })
  }
  function replaceCurrentQuestion() {
    task(async () => {
      const previousStem = item.q.stem
      const base = {
        ...round,
        items: round.items.filter((_, index) => index !== round.cursor),
        previousStems: [...(round.previousStems || []), previousStem],
      }
      const replacement = await generate(base)
      if (!alive.current) return
      updateRound(roundKey, current => ({
        ...current,
        previousStems: base.previousStems,
        items: current.items.map((entry, index) => index === current.cursor ? replacement : entry),
      }))
    })
  }
  function finishChallenge() {
    setConfirmingSubmit(false)
    task(async () => {
      updateRound(roundKey, r => ({ ...r, grading: true }))
      const response = await learning.challenge(round, hasAnswer)
      if (!alive.current) return
      updateRound(roundKey, r => ({ ...r, submitted: true, grading: false,
        items: r.items.map((x, i) => ({ ...x, grade: response.results[i], answer: response.entries[i].answer || response.entries[i].draft_answer || {},
          attemptNo: response.results[i]?.attempt_no || 0,
          first: response.results[i] ? { correct: response.results[i].correct, assisted: response.results[i].assistance_status === 'received' } : null })) }))
      patch({ view: 'result' })
    })
  }
  async function favorite() {
    task(async () => {
      const saved = favorites.find(f => f.question_id === item.q.id)
      const result = saved ? await api.deleteFavorite(item.q.id, favoriteOwner) : await api.addFavorite({ question_id: item.q.id, student_id: favoriteOwner, class_id: classId })
      if (result._mock) throw new Error(text('收藏失败，请重试。', 'Could not save favorite.'))
      setFavorites(f => saved ? f.filter(x => x.question_id !== item.q.id) : [...f, { ...item.q, question_id: item.q.id }])
    })
  }
  const savedChallenge = state.rounds[challengeKey]
  const summary = roundSummary(round)
  const localized = useTranslatedContent(item ? [item.q.stem, item.q.instructions, ...(item.q.options || []), ...(item.q.steps || []), item.grade?.feedback, item.grade?.correct_answer, ...(item.q.citations || []).map(c => c.title)] : [], lang, item?.q?.language)
  const tr = localized.translate
  const questionPanel = item && <>
    {localized.loading && <p role="status" className="note-tip">{text('正在翻译题目，完成后会自动更新。', 'Translating the question; it will update automatically.')}</p>}
    <div className="sw-questionnav" aria-label={text('本轮题目', 'Questions')}>{round.items.map((x, i) => <button key={x.q.id} disabled={busy} aria-current={i === round.cursor ? 'step' : undefined} className={i === round.cursor ? 'active' : ''} onClick={() => updateRound(roundKey, r => ({ ...r, cursor: i }))}>{i + 1}{hasAnswer(x) ? ' ·' : ''}</button>)}</div>
    <section className="sw-panel sw-question">
      <div className="sw-questionmeta"><span className="badge neutral">{t('diff_' + item.q.difficulty)}</span><span className="badge neutral">{t('qtype_' + item.q.type)}</span>
        <strong>{text('本题小节：', 'Section: ')}{displayLabel(item.q.topic, lang)}</strong>
        {(!challenge || reviewing) && <button className="btn sm ghost" disabled={busy} onClick={favorite}>{favorites.some(f => f.question_id === item.q.id) ? t('practice_unfavorite') : t('practice_favorite')}</button>}</div>
      <MathText as="div" className="sw-stem">{tr(item.q.stem)}</MathText>
      {item.q.instructions && <MathText as="p" className="muted">{tr(item.q.instructions)}</MathText>}
      <div className="sw-answer"><h3>{t('practice_your_answer')}</h3><AnswerControls q={item.q} displayText={tr} answer={item.answer} disabled={busy || reviewing || round.grading || (!challenge && item.grade?.correct)} setAnswer={answer => updateItem(roundKey, round.cursor, { answer, grade: null, gradeError: null })} />
        {item.q.type === 'drag_order' && !hasAnswer(item) && !reviewing && <button className="btn sm" disabled={busy || round.grading} onClick={() => updateItem(roundKey, round.cursor, { answer: { order: [...item.q.steps] } })}>{text('确认当前顺序', 'Use this order')}</button>}</div>
      {item.grade && (!challenge || reviewing) && <div role="status" className={'grade-box ' + (item.grade.correct ? 'ok' : 'bad')}><MathText>{tr(item.grade.feedback)}</MathText>{item.grade.correct_answer && <MathText as="p">{tr(item.grade.correct_answer)}</MathText>}</div>}
      {item.gradeError && <div role="alert" className="grade-box bad sw-grade-error"><strong>{item.gradeError === 'expired' ? text('这道旧题的判分记录已失效', 'This saved question has expired') : text('暂时无法批改', 'Grading is temporarily unavailable')}</strong><p>{item.gradeError === 'expired' ? text('服务更新前保存的题目无法安全判分。你的选择仍保留，请换一道新题。', 'Questions saved before the service update cannot be graded safely. Your answer is preserved; replace this question to continue.') : text('你的答案已保留，请稍后重新提交。', 'Your answer is saved. Please submit again shortly.')}</p>{item.gradeError === 'expired' && !challenge && <button className="btn sm" disabled={busy} onClick={replaceCurrentQuestion}>{text('换一道新题', 'Replace question')}</button>}</div>}
      {reviewing && !hasAnswer(item) && <p className="note-tip">{text('本题未作答。可以向导师询问解题思路。', 'Unanswered. Ask your tutor how to approach it.')}</p>}
      <div className="sw-actions">{!challenge ? <><button className="btn" disabled={busy} onClick={() => nextFree()}>{text('下一题', 'Next question')}</button><button className="btn primary" disabled={busy || !hasAnswer(item) || item.grade?.correct} onClick={submitFree}>{item.grade?.correct ? text('已答对', 'Correct') : t('practice_submit')}</button></> : <>
        <button className="btn" disabled={busy || round.cursor === 0} onClick={() => updateRound(roundKey, r => ({ ...r, cursor: r.cursor - 1 }))}>{text('上一题', 'Previous')}</button>
        {round.cursor < round.items.length - 1 && <button className="btn primary" disabled={busy} onClick={() => updateRound(roundKey, r => ({ ...r, cursor: r.cursor + 1 }))}>{text('下一题', 'Next question')}</button>}
        {reviewing ? <button className="btn" onClick={() => patch({ view: 'result' })}>{text('返回结果', 'Back to results')}</button> : <button className="btn" disabled={busy} onClick={() => round.grading ? finishChallenge() : setConfirmingSubmit(true)}>{round.grading ? text('继续批改', 'Retry grading') : text('交卷', 'Submit challenge')}</button>}
      </>}</div>
      {challenge && !reviewing && confirmingSubmit && <div className="sw-inline-confirm" role="dialog" aria-labelledby="challenge-submit-title">
        <div><strong id="challenge-submit-title">{text('确认提交本次章节挑战？', 'Submit this chapter challenge?')}</strong><p>{round.items.filter(x => !hasAnswer(x)).length ? text(`还有 ${round.items.filter(x => !hasAnswer(x)).length} 道题未作答。提交后本次答案不能修改。`, `${round.items.filter(x => !hasAnswer(x)).length} questions are unanswered. Answers cannot be changed after submission.`) : text('所有题目均已作答。提交后本次答案不能修改。', 'All questions are answered. Answers cannot be changed after submission.')}</p></div>
        <div className="sw-inline-confirm-actions"><button className="btn" disabled={busy} onClick={() => setConfirmingSubmit(false)}>{text('继续作答', 'Keep answering')}</button><button className="btn primary" disabled={busy} onClick={finishChallenge}>{text('确认交卷', 'Confirm submission')}</button></div>
      </div>}
      {(!challenge || reviewing) && item.q.citations?.length > 0 && <details className="sw-sources"><summary>{t('practice_citations')}</summary>{item.q.citations.map((c, i) => <p key={i}>{tr(c.title)} {c.page != null ? ' · p.' + c.page : ''}</p>)}</details>}
    </section>
    {reviewing && <button className="btn sw-start" onClick={() => learn(sections.find(s => s.id === item.section))}>{text('去这个小节学习与练习', 'Learn and practice this section')}</button>}
  </>
  return <div className="sw">
    <header className="sw-header"><button className="sw-brand" disabled={busy} onClick={home}><span>∫</span><div>{text('微积分学习伙伴', 'Calculus Companion')}<small>{text('理解概念，练会方法', 'Understand the ideas. Practice the methods.')}</small></div></button>
      <div className="sw-account"><div className="sw-user-summary"><UserRound aria-hidden="true" /><div><strong>{student}</strong><span>{classLabel} · {studentNumber}</span></div></div><button type="button" className="sw-signout" onClick={onSignOut}><LogOut aria-hidden="true" />{text('切换学生', 'Switch student')}</button><details className="sw-preferences"><summary>{text('设置', 'Settings')}</summary><div>{topbar}</div></details></div></header>
    {!runInfo ? <main className="sw-main"><section className="sw-panel sw-connecting" aria-live="polite">
      <span className="student-login-spinner" aria-hidden="true" />
      <h1>{error ? text('暂时无法进入学习空间', 'Could not enter the learning space') : text('正在进入学习空间', 'Entering your learning space')}</h1>
      <p>{error || text('正在为你连接班级并保存本次登录时间…', 'Connecting your class and saving this login time…')}</p>
      {error && <button className="btn" onClick={onSignOut}>{text('返回登录页', 'Back to sign in')}</button>}
    </section></main> : <main className="sw-main">
      {trackingError && <p role="alert" className="note-tip">{text('题目显示记录未同步：', 'Question display not synced: ')}{trackingError} <button className="btn sm" onClick={() => setTrackingRetry(n => n + 1)}>{text('重试', 'Retry')}</button></p>}
      <div className="sw-chapterbar"><label><span className="sw-eyebrow">{text('当前章节', 'YOUR CHAPTER')}</span><select aria-label={text('选择章节', 'Choose chapter')} disabled={busy} value={chapter?.id || ''} onChange={e => { patch({ chapter: e.target.value, section: '', view: 'home' }); setError('') }}>{chapters.map(c => <option key={c.id} value={c.id}>{displayLabel(c.title, lang)}</option>)}</select></label><nav aria-label={text('章节导航', 'Chapter navigation')}><button className="btn" disabled={busy} onClick={home}>{text('章节首页', 'Chapter home')}</button><button className="btn" disabled={busy} onClick={() => patch({ view: 'favorites' })}>{t('stu_favorites')}</button></nav></div>
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
            <div className="sw-entry-action">{savedChallenge?.submitted ? <><button className="btn sw-challenge-button" disabled={busy} onClick={() => startChallenge()}>{text('查看上次挑战结果', 'View last results')} <span aria-hidden="true">→</span></button><button className="btn" disabled={busy || !sections.length || catalog?._mock} onClick={() => startChallenge(true)}>{text('重新挑战', 'Start a new challenge')} <span aria-hidden="true">↻</span></button></> : <button className="btn sw-challenge-button" disabled={busy || !sections.length} onClick={() => patch({ view: 'challenge-intro' })}>{savedChallenge ? text('继续挑战', 'Resume challenge') : text('开始章节挑战', 'Start chapter challenge')} <span aria-hidden="true">→</span></button>}<span className="sw-entry-context">{text('不计时，可中途暂停', 'No timer. Pause anytime.')}</span></div>
          </section>
        </div>
        <p className="sw-footnote">{text('学习记录已与当前学号和班级关联，浏览器同时保留本地进度。', 'Learning records are linked to this student number and class, with progress also cached in this browser.')}</p>
      </> : state.view === 'study' ? <div className="sw-study-layout"><aside className="sw-section-sidebar"><h2>{text('学习小节', 'Sections')}</h2>{sections.map(sec => <button key={sec.id} disabled={busy} aria-current={selected?.id === sec.id ? 'page' : undefined} onClick={() => learn(sec)}>{displayLabel(sec.title, lang)}</button>)}<button disabled={busy} aria-current={!selected ? 'page' : undefined} onClick={() => learn(null)}>{text('全章综合练习', 'Mixed chapter practice')}</button></aside><div className="sw-study-content">
        <span className="sw-eyebrow">{text('学习与练习', 'LEARN & PRACTICE')}</span><h1>{selected ? displayLabel(selected.title, lang) : text('全章综合练习', 'Mixed chapter practice')}</h1>
        {selected && <StudyNotes key={selected.id} topic={selected.title} lang={lang} />}
        {!selected && <p className="note-tip">{text('题目依次覆盖本章小节，每题都标明来源小节。', 'Questions rotate through this chapter, with the section shown on each question.')}</p>}
        <div className="sw-practice-heading"><h2>{text('做题练习', 'Practice')}</h2><label>{t('practice_difficulty')} <select className="inp" disabled={busy} value={state.difficulty} onChange={e => changePracticeSetting('difficulty', e.target.value)}>{DIFFS.map(d => <option key={d} value={d}>{t('diff_' + d)}</option>)}</select></label></div>
        <details className="sw-settings"><summary>{text('练习设置', 'Practice settings')}</summary><label>{t('practice_qtype')} <select className="inp" disabled={busy} value={state.type} onChange={e => changePracticeSetting('type', e.target.value)}><option value="mixed">{text('混合题型', 'Mixed formats')}</option>{TYPES.map(type => <option key={type} value={type}>{t('qtype_' + type)}</option>)}</select></label><p className="sw-small">{text('切换题型或难度后，会在当前区域直接生成对应的新题。', 'Changing the format or difficulty immediately loads a matching question here.')}</p></details>
        {item ? questionPanel : <section className="sw-panel sw-empty"><h3>{text('准备好，练一道？', 'Ready to try a question?')}</h3><p className="muted">{text('可以直接做题，也可以先看看上面的概念。', 'Start now, or explore the concept above first.')}</p><button className="btn primary" disabled={busy || catalog?._mock} onClick={() => nextFree()}>{text('开始练习', 'Start practicing')}</button></section>}
      </div></div> : state.view === 'challenge-intro' ? <section className="sw-panel sw-focus"><span className="sw-eyebrow">{text('章节挑战', 'CHAPTER CHALLENGE')}</span><h2>{displayLabel(chapter.title, lang)}</h2><p>{text(`共 ${sections.length} 道题，每小节抽取一道，中等难度、混合题型。`, `${sections.length} questions, one per section, at medium difficulty with mixed formats.`)}</p><p>{text('独立作答，可以跳过和返回修改；交卷后开放反馈、教材和导师。可以随时返回学习，挑战进度会保留。', 'Work independently. Skip and revisit questions before submitting. Feedback, textbook and tutor become available after submission. You can leave to study and resume later.')}</p><p className="note-tip">{text('这是一次学习自检，不代表整章掌握程度。当前不设通过分数。', 'This is a learning check, not a certification of chapter mastery. No pass threshold is set.')}</p><div className="sw-actions"><button className="btn" onClick={home}>{text('返回学习', 'Back to learning')}</button>{savedChallenge?.submitted ? <><button className="btn" disabled={busy} onClick={() => startChallenge()}>{text('查看上次结果', 'View last results')}</button><button className="btn primary" disabled={busy || !sections.length || catalog?._mock} onClick={() => startChallenge(true)}>{text('重新挑战', 'Start a new challenge')}</button></> : <button className="btn primary" disabled={busy || !sections.length || catalog?._mock} onClick={() => startChallenge()}>{savedChallenge ? text('继续挑战', 'Resume challenge') : text('开始挑战', 'Start challenge')}</button>}</div></section>
      : state.view === 'favorites' ? <Favorites favorites={favorites} onBack={home} onRemove={id => task(async () => { const r = await api.deleteFavorite(id, favoriteOwner); if (r._mock) throw new Error(text('删除失败，请重试。', 'Could not remove favorite.')); setFavorites(f => f.filter(x => x.question_id !== id)) })} onPractice={f => {
        const ch = chapters.find(c => c.sections.some(s => s.title === f.topic)); const sec = ch?.sections.find(s => s.title === f.topic)
        if (!ch || !sec) { setError(text('未找到此题对应的小节。', 'The section for this question was not found.')); return }
        const key = ch.id + ':free:' + sec.id
        setState(s => { const base = s.rounds[key] || { mode: 'free', section: sec.id, title: sec.title, items: [] }; const index = base.items.findIndex(x => x.q.id === f.question_id); const items = index >= 0 ? base.items : [...base.items, { trackingId: crypto.randomUUID(), q: { ...f, id: f.question_id }, section: sec.id, answer: {}, chat: [] }]; return { ...s, chapter: ch.id, section: sec.id, view: 'study', active: key, rounds: { ...s.rounds, [key]: { ...base, items, cursor: index >= 0 ? index : items.length - 1 } } } })
      }} /> : challenge ? <div className="sw-focus"><div className="sw-focushead"><button className="btn ghost" disabled={busy} onClick={home}>← {text('返回学习（保留进度）', 'Back to learning (progress saved)')}</button><span>{text('章节挑战', 'Chapter challenge')}</span></div><h2>{displayLabel(round.title, lang)}</h2>
        {state.view === 'result' && reviewing ? <section className="sw-panel sw-result"><h2>{text('看看这次的表现', 'Review this attempt')}</h2><p>{text('结果只反映这组题目的表现，不能代表整个小节或整章的掌握程度。', 'These results describe this set of questions, not mastery of a section or chapter.')}</p><div className="sw-resultstats"><div><b>{summary.correct}</b>{text('答对', 'Correct')}</div><div><b>{summary.incorrect}</b>{text('答错', 'Incorrect')}</div><div><b>{summary.unanswered}</b>{text('未作答', 'Unanswered')}</div></div>{round.items.map((x, i) => <div className="sw-result-row" key={x.q.id}><button className="sw-reviewrow" onClick={() => { updateRound(roundKey, r => ({ ...r, cursor: i })); patch({ view: 'review' }) }}><span>{i + 1}. {displayLabel(x.q.topic, lang)}</span><strong>{!hasAnswer(x) ? text('未作答', 'Unanswered') : x.grade?.correct ? text('答对', 'Correct') : text('答错', 'Incorrect')} →</strong></button>{!x.grade?.correct && <button className="btn sm ghost" onClick={() => learn(sections.find(s => s.id === x.section))}>{text('去这个小节练习', 'Practice this section')}</button>}</div>)}<div className="sw-actions"><button className="btn" onClick={() => startChallenge(true)}>{text('重新挑战', 'New challenge')}</button><button className="btn primary" onClick={home}>{text('返回学习', 'Back to learning')}</button></div></section>
        : round.items.length < round.plan.length ? <section className="sw-panel"><h3>{text('正在准备整章题目', 'Preparing your chapter challenge')}</h3><p>{round.items.length} / {round.plan.length} {text('道已准备。准备完后统一开始。', 'ready. Your challenge starts when all questions are ready.')}</p><button className="btn" disabled={busy} onClick={() => prepareChallenge()}>{text('继续准备', 'Continue preparation')}</button><button className="btn ghost" disabled={busy} onClick={() => startChallenge(true)}>{text('重新准备', 'Start over')}</button></section>
        : <>{!reviewing && <p className="note-tip">{text(`已作答 ${round.items.filter(hasAnswer).length} / ${round.items.length}。可以返回修改；交卷后再看反馈和询问导师。`, `${round.items.filter(hasAnswer).length} / ${round.items.length} answered. Revisit before submitting; feedback and tutor follow submission.`)}</p>}{questionPanel}{round.grading && <p role="alert">{text('已确认交卷，答案已锁定。若批改中断，请点击“继续批改”。', 'Submission confirmed; answers are locked. If interrupted, use Retry grading.')}</p>}{!reviewing && <button className="btn ghost" disabled={busy} onClick={() => startChallenge(true)}>{text('放弃本轮并重新开始', 'Discard this attempt and restart')}</button>}</>}
      </div> : <button className="btn" onClick={home}>{text('返回章节首页', 'Back to chapter')}</button>}
    </main>}
    {runInfo && !(questionVisible && challenge && !reviewing) && <StudentAgent
      key={questionVisible ? item.trackingId : 'general'}
      learning={learning} item={questionVisible ? item : null} mode={round?.mode || 'free'}
      topic={(questionVisible && item?.q?.topic) || selected?.title || chapter?.title}
      problem={questionVisible ? item.q : null}
      submittedAnswer={item?.grade && (!challenge || reviewing) ? item.answer : null}
      studentId={student}
      classId={classId}
    />}
  </div>
}
function StudyNotes({ topic, lang }) {
  const [card, setCard] = useState(null)
  const [expanded, setExpanded] = useState(false)
  useEffect(() => { let alive = true; api.getConcept(topic).then(c => { if (alive) setCard(c) }); return () => { alive = false } }, [topic])
  const zh = lang === 'zh'
  const translated = useTranslatedContent(card ? [card.summary, card.definition] : [], lang)
  if (!card || translated.loading) return <Loading rows={2} />
  if (card._mock) return <p className="note-tip">{zh ? '教材暂时无法读取，请检查后端后刷新。' : 'Textbook unavailable. Check the backend and refresh.'}</p>
  const formulas = card.content?.find(b => b.content_type === 'concept')?.formulas || card.formulas || []
  return <section className="sw-concept-preview"><span className="sw-eyebrow">{zh ? '核心概念' : 'CORE IDEA'}</span><MathText as="p">{translated.translate(card.summary || card.definition)}</MathText>{formulas.slice(0, 2).map((f, i) => <Formula key={i}>{f}</Formula>)}<details onToggle={e => setExpanded(e.currentTarget.open)}><summary>{zh ? '查看教材、例题与插图' : 'Explore the textbook, examples and figures'}</summary>{expanded && <div className="sw-material"><Concept topic={topic} embedded /></div>}</details></section>
}
