import textbookLabels from './textbook-labels.json'
const labels = {"Limits": "极限", "Derivatives": "导数", "Integrals": "积分", "Chain Rule": "链式法则", "U-Substitution": "换元积分", "Series": "级数", "Excellent": "充分", "Good": "良好", "Fair": "部分", "Weak": "薄弱", "None": "无推理", "explain": "助教辅导", "control": "自主练习"}
Object.assign(labels, {"Applications of Derivatives": "导数的应用", "Applications of the Derivative": "导数的应用", "Continuity": "连续性", "Continuous Functions": "连续函数", "Related Rates": "相关变化率", "General / Free chat": "综合问题 / 自由问答", "A Review of Trigonometry": "三角函数复习"})
Object.assign(labels, textbookLabels)
const normalizedLabels = Object.fromEntries(
  Object.entries(labels).map(([key, value]) => [key.toLowerCase(), value])
)
export function displayLabel(value, lang) {
  if (lang !== 'zh' || typeof value !== 'string') return value
  const name = value.trim().replace(/\s+/g, ' ')
  const direct = normalizedLabels[name.toLowerCase()]
  if (direct) return direct
  // Retain textbook section numbers while translating the title.
  const section = name.match(/^(\d+(?:\.\d+)*)\s+(.+)$/)
  const translated = section && normalizedLabels[section[2].toLowerCase()]
  return translated ? `${section[1]} ${translated}` : value
}
export function localizeInsight(item, lang) {
  if (lang !== 'zh') return item
  const p = item.params || {}
  const pct = v => `${Math.floor(v * 100)}%`
  let title, text
  switch (item.kind) {
    case 'weak_topic':
      title = '需要重点关注的知识点'
      text = p.topic ? `${displayLabel(p.topic, lang)}：正确率 ${pct(p.solve_rate)}，平均推理得分 ${p.avg_reasoning}/4，共 ${p.attempts} 次练习。建议先复习相关概念。` : '请结合知识点数据确认复习重点。'
      break
    case 'gaming':
      title = '需关注作答投入程度'
      text = p.gaming_rate != null ? `${pct(p.gaming_rate)} 的练习会话出现仓促作答或解释不足等信号，建议结合作答记录核查。` : '请结合作答记录核查低投入信号。'
      break
    case 'engagement':
      title = '推理解释需要加强'
      text = `平均推理得分 ${p.avg_reasoning ?? '—'}/4。建议引导学生说明每一步的理由。`
      break
    case 'coverage':
      title = '当前数据较少'
      text = `已记录 ${p.n_sessions ?? '—'} 次练习会话，需要更多数据才能判断稳定趋势。`
      break
    case 'positive':
      title = '学习表现积极'
      text = p.topic ? `${displayLabel(p.topic, lang)}：正确率 ${pct(p.solve_rate)}，平均推理得分 ${p.avg_reasoning}/4。` : p.avg_reasoning != null ? `全班平均推理得分 ${p.avg_reasoning}/4，思路解释表现良好。` : '当前数据未显示明显的薄弱点或低投入信号。'
      break
    default: return { ...item, title: '数据发现（原文）' }
  }
  return { ...item, title, text }
}
