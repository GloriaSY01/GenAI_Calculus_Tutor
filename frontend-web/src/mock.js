/* Demo data.
   `analyticsBackend` mirrors the RAW FastAPI backend response
   (backend/schemas.py ClassAnalytics) so it flows through the same
   normalizeAnalytics() path as live data — keeping mock and real identical. */

export const MOCK = {
  // RAW backend shape (0-1 rates, 0-4 reasoning, dict distribution, severity insights)
  analyticsBackend: {
    n_sessions: 214,
    n_students: 128,
    n_turns: 1560,
    solve_rate: 0.742,
    avg_reasoning: 2.9,
    avg_final_mastery: 71.5,
    avg_turns_per_session: 7.3,
    gaming_rate: 0.14,
    guardrail_rate: 0.05,
    by_topic: [
      { topic: 'Limits',         attempts: 54, solve_rate: 0.86, avg_reasoning: 3.3, avg_final_mastery: 82, gaming_rate: 0.05 },
      { topic: 'Derivatives',    attempts: 72, solve_rate: 0.78, avg_reasoning: 3.0, avg_final_mastery: 76, gaming_rate: 0.08 },
      { topic: 'Chain Rule',     attempts: 41, solve_rate: 0.61, avg_reasoning: 2.4, avg_final_mastery: 63, gaming_rate: 0.20 },
      { topic: 'Integrals',      attempts: 38, solve_rate: 0.55, avg_reasoning: 2.2, avg_final_mastery: 58, gaming_rate: 0.18 },
      { topic: 'U-Substitution', attempts: 26, solve_rate: 0.48, avg_reasoning: 1.9, avg_final_mastery: 51, gaming_rate: 0.27 },
      { topic: 'Series',         attempts: 30, solve_rate: 0.69, avg_reasoning: 2.8, avg_final_mastery: 70, gaming_rate: 0.10 },
    ],
    reasoning_distribution: { none: 0.06, weak: 0.14, partial: 0.30, adequate: 0.32, strong: 0.18 },
    insights: [
      { kind: 'weak_topic', severity: 'warning', title: 'Class struggles most with U-Substitution',
        detail: 'Solve rate 48% and average reasoning 1.9/4 across 26 sessions. Consider a short review or easier practice on this topic.' },
      { kind: 'gaming', severity: 'info', title: 'Some low-effort turns detected',
        detail: '14% of sessions had rushed or empty replies. Worth watching but not widespread.' },
      { kind: 'positive', severity: 'info', title: 'Strong start on Limits',
        detail: 'Limits shows an 86% solve rate with solid reasoning (3.3/4).' },
    ],
  },

  topics: [
    { id: 'limits', name: 'Limits' },
    { id: 'derivatives', name: 'Derivatives' },
    { id: 'chain_rule', name: 'Chain Rule' },
    { id: 'integrals', name: 'Integrals' },
    { id: 'u_sub', name: 'U-Substitution' },
    { id: 'series', name: 'Series' },
  ],

  // UI-shaped assignments (already normalized)
  assignments: [
    { id: 'a1', title: '极限复习综合', note: '', items: [
      { topic: 'Limits', qtype: 'single_choice', difficulty: 'easy', count: 3 },
      { topic: 'Limits', qtype: 'single_choice', difficulty: 'easy', count: 3 },
      { topic: 'Limits', qtype: 'single_choice', difficulty: 'easy', count: 3 },
    ] },
    { id: 'a2', title: '「导数」巩固练习', note: '', items: [
      { topic: 'Derivatives', qtype: 'single_choice', difficulty: 'easy', count: 4 },
      { topic: 'Derivatives', qtype: 'fill_blank', difficulty: 'easy', count: 3 },
      { topic: 'Derivatives', qtype: 'single_choice', difficulty: 'easy', count: 3 },
    ] },
  ],

  askAnswer: (q) =>
    `Based on the current class data, **U-Substitution** needs the most attention: ` +
    `solve rate is 48% and reasoning there skews weak (1.9/4). I'd suggest a short ` +
    `targeted set of 6–8 problems on choosing u and computing du.\n\n` +
    `(Demo answer — the model was unreachable, so this is a rule-based summary for: "${q}")`,

  // ---------------- Student side ----------------
  classes: [
    { id: 'class-a', label: 'Calculus 1 · Section A' },
    { id: 'class-b', label: 'Calculus 1 · Section B' },
  ],

  catalog: {
    source: 'MIT OpenCourseWare',
    attribution: 'MIT 18.01 Single Variable Calculus',
    license: 'CC BY-NC-SA 4.0',
    url: 'https://ocw.mit.edu',
    default_section_id: 'sec-limits',
    chapters: [
      { id: 'ch1', title: '1 · Limits & Continuity', sections: [
        { id: 'sec-limits', label: '1.1', title: 'Limits', url: 'https://ocw.mit.edu' },
        { id: 'sec-continuity', label: '1.2', title: 'Continuity', url: 'https://ocw.mit.edu' },
      ] },
      { id: 'ch2', title: '2 · Derivatives', sections: [
        { id: 'sec-deriv', label: '2.1', title: 'Derivatives', url: 'https://ocw.mit.edu' },
        { id: 'sec-chain', label: '2.2', title: 'Chain Rule', url: 'https://ocw.mit.edu' },
      ] },
      { id: 'ch3', title: '3 · Integrals', sections: [
        { id: 'sec-integrals', label: '3.1', title: 'Integrals', url: 'https://ocw.mit.edu' },
        { id: 'sec-usub', label: '3.2', title: 'U-Substitution', url: 'https://ocw.mit.edu' },
      ] },
    ],
  },

  concept: (topic) => ({
    topic,
    title: topic,
    chapter: 'MIT 18.01 · Single Variable Calculus',
    summary: `${topic} is a core idea in Calculus 1. This is a demo concept card shown because the local textbook index is not connected.`,
    definition: `Intuitively, ${topic} describes how a quantity behaves as its input changes. The formal definition uses limits to make this precise.`,
    formulas: ['\\lim_{x \\to a} f(x) = L', "f'(x) = \\lim_{h\\to 0} \\frac{f(x+h)-f(x)}{h}"],
    example: `For example, applying ${topic} to f(x) = x² gives a clean, well-known result you can verify by hand.`,
    pitfalls: 'A common mistake is to skip checking the conditions before applying the rule.',
    source: 'MIT OpenCourseWare',
    publisher: 'MIT',
    license: 'CC BY-NC-SA 4.0',
    source_url: 'https://ocw.mit.edu',
    term: topic,
    content: [
      { id: 'c1', content_type: 'concept', subtype: 'definition', heading: 'Definition',
        text: `${topic} is defined using the limit of a function as the input approaches a chosen value.`,
        formulas: ['\\lim_{x \\to a} f(x) = L'], order: 1, figures: [], printed_page: 12 },
      { id: 'c2', content_type: 'concept', subtype: 'key idea', heading: 'Key idea',
        text: 'The value the function *approaches* can differ from the value it actually takes at that point.',
        formulas: [], order: 2, figures: [], printed_page: 13 },
      { id: 'c3', content_type: 'example', subtype: 'example', heading: 'Worked example',
        text: 'Evaluate the limit of (x²−1)/(x−1) as x→1 by factoring the numerator first.',
        formulas: ['\\frac{x^2-1}{x-1} = x+1'], order: 3, figures: [], printed_page: 14 },
    ],
    citations: [
      { number: 1, source: 'MIT OCW', title: 'Single Variable Calculus', section: topic, url: 'https://ocw.mit.edu', page: 12 },
    ],
  }),

  question: (type, topic, difficulty) => {
    const base = { id: 'q-demo-' + Math.random().toString(36).slice(2, 8), type, topic, difficulty,
      source: 'generated', section_id: 'sec-demo',
      instructions: '', citations: [{ number: 1, source: 'MIT OCW', title: 'Single Variable Calculus', section: topic, url: 'https://ocw.mit.edu', page: 15 }] }
    if (type === 'single_choice')
      return { ...base, stem: `(${difficulty}) What is the limit of (x²−1)/(x−1) as x→1?`, options: ['0', '1', '2', 'Does not exist'] }
    if (type === 'multiple_choice')
      return { ...base, stem: `(${difficulty}) Which statements about ${topic} are true? (select all)`,
        instructions: 'Select all that apply.', options: ['It is defined via limits', 'It requires continuity everywhere', 'It can be computed by factoring', 'It never exists for rational functions'] }
    if (type === 'fill_blank')
      return { ...base, stem: `(${difficulty}) Fill in the blanks: the limit of x+1 as x→1 equals ___, and the derivative of x² is ___.`, n_blanks: 2 }
    return { ...base, stem: `(${difficulty}) Put the solution steps in the correct order.`,
      steps: ['Factor the numerator', 'Cancel the common factor', 'Substitute x = 1', 'Simplify to get the answer'] }
  },

  grade: (payload) => {
    // Demo grader: single_choice index 2 ("2") is "correct"; others get gentle feedback.
    const correct = payload.single === 2 || (payload.blanks && payload.blanks[0]?.trim() === '2')
    return correct
      ? { correct: true, feedback: 'Correct! The numerator factors as (x−1)(x+1), so the limit is 2.', correct_answer: '2', attempts: 1, answer_revealed: false }
      : { correct: false, feedback: 'Not quite — try factoring the numerator before substituting. (Demo grader)', correct_answer: null, attempts: 1, answer_revealed: false }
  },

  tutorOpening: (topic) =>
    `Hi! Let's work through ${topic || 'this problem'} together. Rather than giving the answer, I'll guide you with questions. What's your first thought on how to start? (Demo tutor — backend unreachable.)`,

  tutorReply: (text, state) => {
    const mastery = Math.min(100, (state?.mastery ?? 0) + (/solve|answer|done|got it/i.test(text) ? 25 : 10))
    const solved = mastery >= 100 || /got it|i see|solved/i.test(text)
    return {
      tutor_message: solved
        ? 'Nice reasoning — that\'s exactly right! You factored and simplified correctly. Want to try a harder one?'
        : `Good start. You said "${text.slice(0, 40)}…". What happens if you factor the numerator first? What common factor do you see?`,
      reasoning_assessment: solved ? 'strong' : 'partial',
      action: solved ? 'complete' : 'probe',
      asks_for_explanation: !solved,
      hint_level: (state?.hint_level ?? 0) + (/hint|stuck|不会/i.test(text) ? 1 : 0),
      mastery,
      is_solved: solved,
      citations: [{ number: 1, source: 'MIT OCW', title: 'Single Variable Calculus', section: state?.topic || 'Limits', url: 'https://ocw.mit.edu', page: 12 }],
      engagement_flag: null,
      safety_event: null,
    }
  },

  favorites: [
    { question_id: 'fav-1', student_id: 'demo', class_id: 'class-a', topic: 'Limits',
      stem: 'What is the limit of (x²−1)/(x−1) as x→1?', type: 'single_choice', difficulty: 'easy',
      instructions: '', options: ['0', '1', '2', 'Does not exist'], steps: null, n_blanks: null, saved_at: Date.now() / 1000 - 3600 },
  ],
}
