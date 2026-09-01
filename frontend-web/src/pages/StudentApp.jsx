import { useEffect, useState } from 'react'
import { useLang } from '../i18n.jsx'
import { api } from '../api.js'
import Concept from './student/Concept.jsx'
import Practice from './student/Practice.jsx'
import Tutor from './student/Tutor.jsx'
import Favorites from './student/Favorites.jsx'
import { PRESETS } from './student/prompts.js'

const STAGES = [
  { key: 'concept',  ic: '📖', labelKey: 'stage_concept',  hintKey: 'stage_concept_hint' },
  { key: 'practice', ic: '✍️', labelKey: 'stage_practice', hintKey: 'stage_practice_hint' },
  { key: 'tutor',    ic: '💬', labelKey: 'stage_tutor',    hintKey: 'stage_tutor_hint' },
]

export default function StudentApp({ topbar }) {
  const { t, lang } = useLang()

  // identity
  const [studentId, setStudentId] = useState(() => localStorage.getItem('stu_name') || '')
  const [classId, setClassId] = useState('')
  const [classes, setClasses] = useState([])

  // catalog / topic
  const [catalog, setCatalog] = useState(null)
  const [topic, setTopic] = useState('')

  // learning flow
  const [view, setView] = useState('learning')   // 'learning' | 'favorites'
  const [stage, setStage] = useState('concept')   // 'concept' | 'practice' | 'tutor'
  const [difficulty, setDifficulty] = useState('easy')
  const [qtype, setQtype] = useState('single_choice')

  // tutor context
  const [tutorEntry, setTutorEntry] = useState(null)
  const [tutorProblem, setTutorProblem] = useState(null)
  const [tutorSeed, setTutorSeed] = useState(null)

  // favorites
  const [favorites, setFavorites] = useState([])

  useEffect(() => {
    api.getClasses().then((r) => {
      const list = r.classes || []
      setClasses(list)
      setClassId((c) => c || list[0]?.id || '')
    })
    api.getCatalog().then((c) => {
      setCatalog(c)
      const first = c.chapters?.[0]?.sections?.[0]?.title
      if (first) setTopic((tp) => tp || first)
    })
  }, [])

  useEffect(() => {
    if (!studentId) { setFavorites([]); return }
    api.getFavorites(studentId).then((r) => setFavorites(r.favorites || []))
  }, [studentId])

  const saveName = (v) => { setStudentId(v); localStorage.setItem('stu_name', v) }

  // ----- stage transitions -----
  const goConcept = () => { setStage('concept'); setView('learning') }
  const goPractice = () => { setStage('practice'); setView('learning') }
  const goTutor = (entry, { problem = null, seed = null } = {}) => {
    setTutorEntry(entry); setTutorProblem(problem); setTutorSeed(seed)
    setStage('tutor'); setView('learning')
  }

  const pickTopic = (title) => { setTopic(title); setStage('concept'); setView('learning') }

  // ----- favorites -----
  const toggleFavorite = async (q, isFav) => {
    if (!studentId) return
    if (isFav) {
      await api.deleteFavorite(q.id, studentId)
      setFavorites((f) => f.filter((x) => x.question_id !== q.id))
    } else {
      await api.addFavorite({ student_id: studentId, class_id: classId, question_id: q.id })
      setFavorites((f) => [
        { question_id: q.id, student_id: studentId, class_id: classId, topic: q.topic, stem: q.stem,
          type: q.type, difficulty: q.difficulty, instructions: q.instructions || '', options: q.options,
          steps: q.steps, n_blanks: q.n_blanks, saved_at: Date.now() / 1000 }, ...f,
      ])
    }
  }
  const removeFavorite = async (qid) => {
    await api.deleteFavorite(qid, studentId)
    setFavorites((f) => f.filter((x) => x.question_id !== qid))
  }
  const practiceFavorite = (f) => { setTopic(f.topic); setQtype(f.type); setDifficulty(f.difficulty); goPractice() }

  const stageIndex = STAGES.findIndex((s) => s.key === stage)

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-logo">∫</div>
          <div>
            <div className="brand-name">{t('stu_app_title')}</div>
            <div className="brand-sub">{t('stu_app_sub')}</div>
          </div>
        </div>

        <div className="stu-field">
          <label className="ctrl-label">{t('stu_name')}</label>
          <input className="inp" placeholder={t('stu_name_ph')} value={studentId} onChange={(e) => saveName(e.target.value)} />
        </div>
        <div className="stu-field">
          <label className="ctrl-label">{t('stu_class')}</label>
          <select className="inp" value={classId} onChange={(e) => setClassId(e.target.value)}>
            {classes.map((c) => <option key={c.id} value={c.id}>{c.label}</option>)}
          </select>
        </div>

        <button className={'nav-item' + (view === 'favorites' ? ' active' : '')} style={{ marginTop: 6 }}
          onClick={() => setView('favorites')}>
          <span className="ic">⭐</span>{t('stu_favorites')}
          {favorites.length > 0 && <span className="fav-count">{favorites.length}</span>}
        </button>

        <div className="nav-group-label">{t('stu_catalog')}</div>
        <div className="catalog-scroll">
          {(catalog?.chapters || []).map((ch) => (
            <div key={ch.id} className="cat-chapter">
              <div className="cat-chapter-title">{ch.title}</div>
              {ch.sections.map((sec) => (
                <button key={sec.id} className={'cat-sec' + (topic === sec.title && view === 'learning' ? ' active' : '')}
                  onClick={() => pickTopic(sec.title)}>
                  {sec.label && <span className="cat-sec-label">{sec.label}</span>}{sec.title}
                </button>
              ))}
            </div>
          ))}
        </div>

        <div className="sidebar-foot">{topbar}</div>
      </aside>

      <main className="main">
        <div className="content">
          {view === 'favorites' ? (
            <Favorites favorites={favorites} onRemove={removeFavorite} onPractice={practiceFavorite} onBack={goConcept} />
          ) : (
            <>
              {/* stepper */}
              <div className="stepper">
                {STAGES.map((s, i) => (
                  <button key={s.key} className={'step' + (s.key === stage ? ' active' : '') + (i < stageIndex ? ' done' : '')}
                    onClick={() => setStage(s.key)}>
                    <span className="step-ic">{s.ic}</span>
                    <span className="step-label">{t(s.labelKey)}</span>
                  </button>
                ))}
              </div>
              <div className="stepper-hint muted">{t(STAGES[stageIndex]?.hintKey)}</div>

              {stage === 'concept' && topic && (
                <Concept topic={topic}
                  onAskTutor={() => goTutor('concept', { seed: PRESETS.explain_concept(topic) })}
                  onStartPractice={goPractice} />
              )}
              {stage === 'practice' && (
                <Practice topic={topic} difficulty={difficulty} qtype={qtype}
                  setDifficulty={setDifficulty} setQtype={setQtype}
                  studentId={studentId} classId={classId} lang={lang}
                  favorites={favorites} onToggleFavorite={toggleFavorite}
                  onBackConcept={goConcept}
                  onStuck={(q) => goTutor('practice', { problem: toProblem(q), seed: PRESETS.im_stuck() })}
                  onExplainCorrect={(q) => goTutor('practice', { problem: toProblem(q), seed: PRESETS.my_reasoning() })}
                  onGetHint={(q) => goTutor('practice', { problem: toProblem(q), seed: PRESETS.hint_first() })}
                  onFirstStep={(q) => goTutor('practice', { problem: toProblem(q), seed: PRESETS.im_stuck() })} />
              )}
              {stage === 'tutor' && (
                <Tutor topic={topic} tutorEntry={tutorEntry} problem={tutorProblem} sessionSeed={tutorSeed} lang={lang}
                  studentId={studentId} classId={classId}
                  onBackPractice={goPractice} onBackConcept={goConcept} />
              )}
            </>
          )}
        </div>
      </main>
    </div>
  )
}

function toProblem(q) {
  if (!q) return null
  return { id: q.id, statement: q.stem, topic: q.topic, difficulty: q.difficulty }
}
