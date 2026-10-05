import { useCallback, useEffect, useRef } from 'react'
import { useLang } from '../i18n.jsx'
import { api } from '../api.js'
import FloatingAgent from '../components/FloatingAgent.jsx'

const PROMPTS = {
  zh: ['我没看懂题目，应该先关注什么？', '检查我现在的思路，不要直接给答案', '给我一个最小提示', '我应该怎样验证答案？'],
  en: ['What should I notice first?', 'Check my reasoning without giving the answer', 'Give me one minimal hint', 'How should I verify my answer?'],
}

export default function StudentAgent({ topic, problem, studentId, classId }) {
  const { lang } = useLang()
  const zh = lang === 'zh'
  const sessionRef = useRef(null)
  const contextKey = `${problem?.id || topic || 'general'}:${studentId}:${classId}:${lang}`

  useEffect(() => { sessionRef.current = null }, [contextKey])

  const ask = useCallback(async (question) => {
    if (!sessionRef.current) {
      const session = await api.startSession({
        problem_id: problem?.id || null,
        topic: topic || problem?.topic || 'Calculus 1',
        student_id: studentId || 'anon',
        class_id: classId || null,
        language: lang,
        condition: 'explain',
      })
      sessionRef.current = session.session_id
    }
    const turn = await api.sendMessage(sessionRef.current, question, lang, { topic: topic || problem?.topic })
    return {
      content: turn.tutor_message,
      citations: turn.citations,
      note: turn._mock ? (zh ? '导师服务未连接，当前为演示回复。' : 'Tutor service is unavailable; this is a demo reply.') : '',
    }
  }, [classId, lang, problem, studentId, topic, zh])

  return <FloatingAgent
    title={zh ? '学习 Agent' : 'Learning Agent'}
    subtitle={topic || problem?.topic || (zh ? '微积分学习' : 'Calculus learning')}
    welcome={zh ? '告诉我你正在想什么。我会追问思路并给最小必要提示，不会直接代替你解题。' : 'Tell me what you are thinking. I will ask about your reasoning and give only the help you need.'}
    prompts={PROMPTS[lang]}
    suggestionsLabel={zh ? '可以这样问' : 'Try asking'}
    placeholder={zh ? '写下你的思路或卡住的位置…' : 'Write your reasoning or where you are stuck…'}
    sendLabel={zh ? '发送问题' : 'Send question'}
    openLabel={zh ? '打开学习 Agent' : 'Open Learning Agent'}
    closeLabel={zh ? '关闭学习 Agent' : 'Close Learning Agent'}
    resetKey={contextKey}
    onAsk={ask}
  />
}
