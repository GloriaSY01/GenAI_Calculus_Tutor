import { useCallback } from 'react'
import { useLang } from '../i18n.jsx'
import { api } from '../api.js'
import FloatingAgent from '../components/FloatingAgent.jsx'

const PROMPTS = {
  zh: ['哪个知识点最需要关注？', '学生的推理过程有什么共性问题？', '下一步适合布置什么练习？', '总结当前班级情况'],
  en: ['Which topic needs attention?', 'What reasoning problems do students share?', 'What practice should I assign next?', 'Summarize this class'],
}

export default function TeacherAgent({ classId, classLabel }) {
  const { lang } = useLang()
  const zh = lang === 'zh'
  const ask = useCallback(async (question, history) => {
    const result = await api.ask(question, lang, classId, history)
    return {
      content: result.answer,
      note: result.llm_available === false
        ? (zh ? '模型暂不可用，以下为基于班级数据的规则摘要。' : 'The model is unavailable; this is a rule-based class summary.')
        : '',
    }
  }, [classId, lang, zh])

  return <FloatingAgent
    title={zh ? '教学 Agent' : 'Teaching Agent'}
    subtitle={classLabel || (zh ? '全部班级' : 'All classes')}
    welcome={zh ? '可以询问班级薄弱知识点、推理质量和下一步教学行动。' : 'Ask about weak topics, reasoning quality, and the next teaching action.'}
    prompts={PROMPTS[lang]}
    suggestionsLabel={zh ? '可以这样问' : 'Try asking'}
    placeholder={zh ? '询问班级情况或教学决策…' : 'Ask about the class or a teaching decision…'}
    sendLabel={zh ? '发送问题' : 'Send question'}
    openLabel={zh ? '打开教学 Agent' : 'Open Teaching Agent'}
    closeLabel={zh ? '关闭教学 Agent' : 'Close Teaching Agent'}
    resetKey={`${classId}:${lang}`}
    onAsk={ask}
  />
}
