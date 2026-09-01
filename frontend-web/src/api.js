/* ------------------------------------------------------------------
   API layer — talks to the existing FastAPI backend.
   In dev, Vite proxies /api -> http://localhost:8000 (see vite.config.js).
   If the backend is unreachable, we fall back to demo data so the UI
   still renders — controlled by the returned `._mock` flag.

   The backend (see backend/schemas.py) returns a different shape than the
   UI components want, so every response goes through a `normalize*` step
   that maps backend fields -> a stable UI shape. This is the single place
   that knows about the backend's field names.
------------------------------------------------------------------- */
import { MOCK } from './mock.js'

const BASE = import.meta.env.VITE_API_BASE || '/api'

async function req(path, opts = {}) {
  const res = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

/* ------------------------------------------------------------------ *
 * Normalizers: backend shape -> UI shape
 * ------------------------------------------------------------------ */

// reasoning_assessment is a 0-4 scale on the backend; UI shows a 0-5 style
// "/5"-ish score. We keep it on the backend's /4 scale but label it /4.
const REASONING_MAX = 4

// backend reasoning_distribution: { none, weak, partial, adequate, strong } -> share (0-1)
const DIST_LABELS = {
  strong: 'Excellent',
  adequate: 'Good',
  partial: 'Fair',
  weak: 'Weak',
  none: 'None',
}
const DIST_ORDER = ['strong', 'adequate', 'partial', 'weak', 'none']

// severity (info/warning/critical) -> UI level (ok/warn/bad)
const SEVERITY_LEVEL = { info: 'ok', warning: 'warn', critical: 'bad' }

function normalizeAnalytics(raw) {
  // Support both the real backend shape and the mock's pre-shaped data.
  if (raw && raw.kpis) return raw // already UI-shaped (mock)

  const byTopic = (raw.by_topic || []).map((t) => ({
    topic: t.topic,
    accuracy: t.solve_rate ?? 0,          // UI uses `accuracy` (0-1)
    attempts: t.attempts ?? 0,
    reasoning: t.avg_reasoning ?? 0,
    mastery: t.avg_final_mastery ?? 0,
    gaming: t.gaming_rate ?? 0,
    trend: null,                          // backend has no week-over-week trend
  }))

  const distTotalShare = DIST_ORDER.reduce(
    (s, k) => s + (raw.reasoning_distribution?.[k] || 0), 0) || 1
  const reasoning_distribution = DIST_ORDER
    .filter((k) => (raw.reasoning_distribution?.[k] || 0) > 0 || k !== 'none')
    .map((k) => ({
      grade: DIST_LABELS[k],
      // store as a percentage-ish count so the pie shows shares; keep 1 decimal
      count: Math.round(((raw.reasoning_distribution?.[k] || 0) / distTotalShare) * 1000) / 10,
    }))
    .filter((d) => d.grade !== 'None' || d.count > 0)

  const insights = (raw.insights || []).map((i) => ({
    level: SEVERITY_LEVEL[i.severity] || 'neutral',
    title: i.title,
    text: i.detail || i.title,
  }))

  return {
    kpis: {
      active_students: raw.n_students ?? 0,
      active_students_delta: null,
      // UI shows avg accuracy as a %; backend solve_rate is 0-1
      avg_accuracy: raw.solve_rate ?? 0,
      avg_accuracy_delta: null,
      // backend has no "problems_solved"; closest signal is sessions/turns
      problems_solved: raw.n_sessions ?? 0,
      problems_solved_label_key: 'kpi_sessions',
      problems_solved_delta: null,
      reasoning_score: raw.avg_reasoning ?? 0,
      reasoning_score_max: REASONING_MAX,
      reasoning_score_delta: null,
    },
    extra: {
      n_turns: raw.n_turns ?? 0,
      avg_turns_per_session: raw.avg_turns_per_session ?? 0,
      gaming_rate: raw.gaming_rate ?? 0,
      guardrail_rate: raw.guardrail_rate ?? 0,
      avg_final_mastery: raw.avg_final_mastery ?? 0,
    },
    by_topic: byTopic,
    reasoning_distribution,
    conditions: [],   // backend doesn't expose tutor-vs-solo here
    practice: [],      // backend has no per-set practice breakdown here
    insights,
    reasoning_max: REASONING_MAX,
  }
}

// backend assignment: { id, title, note, items:[{topic,qtype,difficulty,count}], created_at }
// UI table wants one row per assignment with a topic/count/difficulty summary.
function normalizeAssignment(a) {
  if (a.items === undefined && a.topic !== undefined) return a // mock shape
  const items = a.items || []
  const totalCount = items.reduce((s, it) => s + (it.count || 0), 0)
  const topics = [...new Set(items.map((it) => it.topic))]
  const diffs = [...new Set(items.map((it) => it.difficulty))]
  return {
    id: a.id,
    title: a.title,
    note: a.note || '',
    topic: topics.length === 1 ? topics[0] : `${topics.length} topics`,
    count: totalCount || items.length,
    difficulty: diffs.length === 1 ? cap(diffs[0]) : 'Mixed',
    due: a.due || null,
    items,
    created_at: a.created_at,
  }
}
const cap = (s) => (s ? s[0].toUpperCase() + s.slice(1) : s)

/* ------------------------------------------------------------------ */

async function withFallback(fn, mockShaped) {
  try {
    const data = await fn()
    return { ...data, _mock: false }
  } catch (e) {
    console.warn('[api] falling back to mock:', e.message)
    return { ...structuredClone(mockShaped), _mock: true }
  }
}

export const api = {
  getClassAnalytics: () =>
    withFallback(
      async () => normalizeAnalytics(await req('/analytics/class')),
      normalizeAnalytics(MOCK.analyticsBackend)
    ),

  getTopics: () =>
    withFallback(
      async () => {
        const data = await req('/topics')
        // backend may return ["Limits", ...] or [{id,name}]; normalize
        const arr = Array.isArray(data) ? data : data.topics || []
        const topics = arr.map((x, i) =>
          typeof x === 'string' ? { id: String(i), name: x } : { id: x.id ?? String(i), name: x.name ?? x.topic ?? String(x) })
        return { topics }
      },
      { topics: MOCK.topics }
    ),

  getAssignments: () =>
    withFallback(
      async () => {
        const data = await req('/assignments')
        const arr = Array.isArray(data) ? data : data.assignments || []
        return { assignments: arr.map(normalizeAssignment) }
      },
      { assignments: MOCK.assignments }
    ),

  // UI collects question blocks; backend wants { title, note, items:[...] }.
  createAssignment: (payload) => {
    const items = (payload.items && payload.items.length)
      ? payload.items.map((it) => ({
          topic: it.topic || 'General',
          qtype: it.qtype || 'single_choice',
          difficulty: (it.difficulty || 'medium').toLowerCase(),
          count: it.count || 1,
        }))
      : [{
          topic: payload.topic || 'General',
          qtype: payload.qtype || 'single_choice',
          difficulty: (payload.difficulty || 'medium').toLowerCase(),
          count: payload.count || 1,
        }]
    const body = { title: payload.title, note: payload.note || '', items }
    return req('/assignments', { method: 'POST', body: JSON.stringify(body) })
      .then(normalizeAssignment)
      .catch(() => ({ ...normalizeAssignment({ ...body, id: 'local-' + Date.now(), created_at: Date.now() / 1000 }), _mock: true }))
  },

  deleteAssignment: (id) =>
    req(`/assignments/${id}`, { method: 'DELETE' }).catch(() => ({ ok: true, _mock: true })),

  // backend: POST /analytics/ask { question } -> { answer, llm_available, grounded_on }
  ask: (question) =>
    req('/analytics/ask', { method: 'POST', body: JSON.stringify({ question }) })
      .then((r) => ({ answer: r.answer, llm_available: r.llm_available !== false }))
      .catch(() => ({ answer: MOCK.askAnswer(question), _mock: true, llm_available: false })),

  /* ---------------- Student side ---------------- */

  // GET /classes -> [{ id, label }]
  getClasses: () =>
    withFallback(async () => ({ classes: await req('/classes') }), { classes: MOCK.classes }),

  // GET /catalog -> CatalogResponse (chapters -> sections)
  getCatalog: () =>
    withFallback(async () => await req('/catalog'), MOCK.catalog),

  // GET /concept?topic= -> ConceptCard (503 when RAG index not ready)
  getConcept: (topic) =>
    withFallback(async () => await req('/concept?topic=' + encodeURIComponent(topic)), MOCK.concept(topic)),

  // POST /generate { type, topic, difficulty, language } -> GeneratedQuestionPublic
  generateQuestion: ({ type, topic, difficulty, language = 'en' }) =>
    withFallback(
      async () => await req('/generate', { method: 'POST', body: JSON.stringify({ type, topic, difficulty, language }) }),
      MOCK.question(type, topic, difficulty),
    ),

  // POST /grade { question_id, single|multiple|blanks|order, student_id, class_id } -> GradeResponse
  gradeAnswer: (payload) =>
    withFallback(
      async () => await req('/grade', { method: 'POST', body: JSON.stringify(payload) }),
      MOCK.grade(payload),
    ),

  // POST /session/start -> { session_id, problem, condition, opening_message }
  startSession: (body) =>
    withFallback(
      async () => await req('/session/start', { method: 'POST', body: JSON.stringify(body) }),
      { session_id: 'demo-' + Date.now(), problem: null, condition: body.condition || 'explain',
        opening_message: MOCK.tutorOpening(body.topic) },
    ),

  // POST /session/{sid}/message { text, language } -> TutorTurn
  sendMessage: (sid, text, language, state) =>
    withFallback(
      async () => await req(`/session/${sid}/message`, { method: 'POST', body: JSON.stringify({ text, language }) }),
      MOCK.tutorReply(text, state),
    ),

  // GET /favorites?student_id= -> [Favorite]
  getFavorites: (studentId) =>
    withFallback(
      async () => ({ favorites: await req('/favorites?student_id=' + encodeURIComponent(studentId)) }),
      { favorites: MOCK.favorites },
    ),

  // POST /favorites { student_id, class_id, question_id } -> Favorite
  addFavorite: (body) =>
    req('/favorites', { method: 'POST', body: JSON.stringify(body) }).catch(() => ({ ...body, _mock: true })),

  // DELETE /favorites/{qid}?student_id=
  deleteFavorite: (questionId, studentId) =>
    req(`/favorites/${questionId}?student_id=` + encodeURIComponent(studentId), { method: 'DELETE' })
      .catch(() => ({ removed: true, _mock: true })),
}
