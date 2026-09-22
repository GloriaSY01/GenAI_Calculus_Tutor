// Keep the challenge snapshot separate from post-submission tutor activity.
export function hasAnswer(item) {
  const a = item?.answer || {}, q = item?.q || {}
  if (q.type === 'single_choice') return Number.isInteger(a.single)
  if (q.type === 'multiple_choice') return !!a.multiple?.length
  if (q.type === 'fill_blank') return Array.from({ length: q.n_blanks || 1 }, (_, i) => !!a.blanks?.[i]?.trim()).every(Boolean)
  if (q.type === 'drag_order') return !!a.order?.length && a.order.length === q.steps?.length
  return false
}
export function challengePlan(sections) { return sections.map(s => s.id) }
export function roundSummary(round) {
  return (round?.items || []).reduce((sum, x) => {
    if (!hasAnswer(x)) sum.unanswered++
    else if (x.first?.correct) sum.correct++
    else sum.incorrect++
    return sum
  }, { correct: 0, incorrect: 0, unanswered: 0 })
}
