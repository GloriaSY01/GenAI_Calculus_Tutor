/* Suggested prompts logic — ported from frontend/quick_prompts.py + presets.py.
   Decides which prompt buttons to show based on the tutor stage/state, and
   maps each button to the actual text sent to the tutor. */

// Preset message bodies (what actually gets sent). Kept in English so the
// tutor model behaves the same as the streamlit version; button labels are i18n'd.
export const PRESETS = {
  explain_concept: (topic) => `Please explain the concept of ${topic || 'this topic'}: what problem it solves, and give a simple example.`,
  give_example: (topic) => `Give me one simple worked example for ${topic || 'this topic'}.`,
  common_mistakes: (topic) => `What are the common mistakes students make when learning ${topic || 'this topic'}?`,
  how_used: (topic) => `How is ${topic || 'this concept'} typically used when solving problems?`,
  hint_first: () => 'Give me a hint for the first step, but do not give the full answer.',
  why_method: () => 'Why do we use this method here?',
  im_stuck: () => "I'm stuck. Please guide me from the first step — you can ask me questions, but don't give the full answer.",
  review_concept: (topic) => `Can you review the underlying concept of ${topic || 'this topic'} for me?`,
  next_hint: () => 'Can you give me a little more of a hint?',
  check_reasoning: () => 'Here is my reasoning — can you check if it is right and what I should think about next?',
  why_step: () => 'Why is this step correct?',
  still_confused: () => "I'm still confused. Can you explain it a simpler way?",
  full_solution: () => 'Now walk me through the full solution step by step, emphasizing the reasoning.',
  why_works: () => 'Why does this method work?',
  my_reasoning: () => "Here's my reasoning, please check it.",
}

// Returns an array of { key, labelKey, text } — at most 4 (or 2 when blocked).
export function getQuickPrompts(state) {
  const { topic, tutorEntry, hasProblem, isSolved, action, hintLevel, asksForExplanation } = state
  let out = []

  if (isSolved) {
    // 5. Wrap-up
    out = [
      { key: 'full_solution', labelKey: 'sp_full_solution', text: PRESETS.full_solution() },
      { key: 'why_works', labelKey: 'sp_why_works', text: PRESETS.why_works() },
    ]
  } else if (tutorEntry === 'concept' || !hasProblem) {
    // 1. Concept stage
    out = [
      { key: 'explain_concept', labelKey: 'sp_explain_concept', text: PRESETS.explain_concept(topic) },
      { key: 'give_example', labelKey: 'sp_give_example', text: PRESETS.give_example(topic) },
      { key: 'common_mistakes', labelKey: 'sp_common_mistakes', text: PRESETS.common_mistakes(topic) },
      { key: 'how_used', labelKey: 'sp_how_used', text: PRESETS.how_used(topic) },
    ]
  } else if (action === 'blocked') {
    // 4. Blocked — only 2 buttons
    out = [
      { key: 'next_hint', labelKey: 'sp_next_hint', text: PRESETS.next_hint() },
      { key: 'still_confused', labelKey: 'sp_still_confused', text: PRESETS.still_confused() },
    ]
  } else if ((hintLevel ?? 0) === 0) {
    // 2. Practice early
    out = [
      { key: 'hint_first', labelKey: 'sp_hint_first', text: PRESETS.hint_first() },
      { key: 'why_method', labelKey: 'sp_why_method', text: PRESETS.why_method() },
      { key: 'im_stuck', labelKey: 'sp_im_stuck', text: PRESETS.im_stuck() },
      { key: 'review_concept', labelKey: 'sp_review_concept', text: PRESETS.review_concept(topic) },
    ]
  } else {
    // 3. Practice in progress
    out = [
      { key: 'next_hint', labelKey: 'sp_next_hint', text: PRESETS.next_hint() },
      { key: 'check_reasoning', labelKey: 'sp_check_reasoning', text: PRESETS.check_reasoning() },
      { key: 'why_step', labelKey: 'sp_why_step', text: PRESETS.why_step() },
      { key: 'still_confused', labelKey: 'sp_still_confused', text: PRESETS.still_confused() },
    ]
  }

  // 6. Insert "Here's my reasoning" at the front when requested (unsolved + has problem)
  if (asksForExplanation && !isSolved && hasProblem) {
    out = [{ key: 'my_reasoning', labelKey: 'sp_my_reasoning', text: PRESETS.my_reasoning() }, ...out]
    const seen = new Set()
    out = out.filter((p) => (seen.has(p.key) ? false : (seen.add(p.key), true)))
    out = out.slice(0, 4)
  }

  return out
}
