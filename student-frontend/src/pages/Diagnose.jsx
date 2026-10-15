import { useState } from 'react'
import { displayLabel } from '../localization.js'
import { useLang } from '../i18n.jsx'
import { useAnalytics, useAsync } from '../components/hooks.js'
import { useTeacherClass } from '../components/TeacherClass.jsx'
import { api } from '../api.js'
import { Card, Loading, MockPill, Chart, Badge } from '../components/ui.jsx'

export default function Diagnose() {
  const { t, lang } = useLang()
  const classId = useTeacherClass()
  const { loading, data, error, reload } = useAnalytics()
  const assignmentState = useAsync(() => api.getAssignmentResults(classId), [classId])
  const [expandedId, setExpandedId] = useState(null)

  if (loading) return <Loading rows={2} />
  if (error) return (
    <Card><div className="empty"><div className="ico">!</div>{t('error_load')}
      <div style={{ marginTop: 14 }}><button className="btn primary" onClick={reload}>{t('retry')}</button></div>
    </div></Card>
  )

  const topics = [...(data.by_topic || [])].sort((a, b) => a.accuracy - b.accuracy || b.attempts - a.attempts)
  const dist = data.reasoning_distribution || []
  const assignments = assignmentState.data?.results || []
  const distColors = { Excellent: '#17b26a', Good: '#5d89fb', Fair: '#f79009', Weak: '#f04438', None: '#c2c8d6' }
  const percent = (value) => `${Math.round((value || 0) * 100)}%`
  const firstAccuracy = (assignment) => assignment.first_attempt_accuracy ?? (
    assignment.first_attempt_attempted
      ? assignment.first_attempt_correct / assignment.first_attempt_attempted
      : 0
  )

  return (
    <div className="stack fade-in">
      <div className="row" style={{ justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div className="section-step">{t('diag_step')}</div>
          <h2 className="section-head">{t('diag_head')}</h2>
          <p className="muted" style={{ margin: '4px 0 0' }}>{t('diag_head_sub')}</p>
        </div>
        <MockPill show={data._mock || assignmentState.data?._mock} />
      </div>

      <div className="grid cols-2">
        <Card title={t('topic_need')} icon="!" sub={t('topic_need_sub')}>
          <div style={{ maxHeight: 420, overflowY: 'auto' }}><Chart height={Math.max(280, topics.length * 42)} option={{
            tooltip: { trigger: 'axis', valueFormatter: (v) => v + '%' },
            xAxis: { type: 'value', max: 100 },
            yAxis: { type: 'category', data: topics.map(x => displayLabel(x.topic, lang)).reverse(), axisLine: { show: false } },
            series: [{
              type: 'bar', barWidth: 18,
              data: topics.map(x => ({
                value: +(x.accuracy * 100).toFixed(0),
                itemStyle: {
                  borderRadius: [0, 6, 6, 0],
                  color: x.accuracy >= 0.75 ? '#17b26a' : x.accuracy >= 0.55 ? '#f79009' : '#f04438',
                },
              })).reverse(),
              label: { show: true, position: 'right', formatter: '{c}%', color: 'var(--text-2)' },
            }],
          }} /></div>
        </Card>

        <Card title={t('reasoning_explain')} icon="?" sub={t('reasoning_explain_sub')}>
          <Chart height={320} option={{
            tooltip: { trigger: 'item' },
            legend: { bottom: 0 },
            series: [{
              type: 'pie', radius: ['52%', '74%'], center: ['50%', '44%'],
              itemStyle: { borderRadius: 8, borderColor: 'var(--surface)', borderWidth: 3 },
              label: { show: true, formatter: '{b}\n{d}%', color: 'var(--text-2)' },
              data: dist.map(d => ({ name: displayLabel(d.grade, lang), value: d.count, itemStyle: { color: distColors[d.grade] } })),
            }],
          }} />
        </Card>
      </div>

      <Card title={t('quiz_scores')} icon="▣" sub={t('quiz_scores_sub')} right={<MockPill show={assignmentState.data?._mock} />}>
        {assignmentState.loading ? <Loading rows={2} /> : assignments.length > 0 ? (
          <div className="stack" style={{ gap: 12 }}>
            <div className="note-tip">{t('quiz_scope_note')}</div>
            {assignments.map((assignment) => {
              const completion = assignment.assigned_students
                ? assignment.completed_students / assignment.assigned_students
                : 0
              const accuracy = firstAccuracy(assignment)
              const expanded = expandedId === assignment.id
              return (
                <div key={assignment.id} style={{ border: '1px solid var(--border)', borderRadius: 12, padding: 16 }}>
                  <div className="row" style={{ justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }}>
                    <div>
                      <div style={{ fontWeight: 750, fontSize: 16 }}>{lang === 'zh' && assignment.title_zh ? assignment.title_zh : assignment.title}</div>
                      <div className="muted" style={{ marginTop: 4 }}>{t('quiz_first_attempts')}: {assignment.first_attempt_correct ?? 0}/{assignment.first_attempt_attempted ?? 0}</div>
                    </div>
                    <Badge level={completion >= 0.75 ? 'ok' : completion >= 0.5 ? 'warn' : 'bad'}>{percent(completion)}</Badge>
                  </div>

                  <div className="grid cols-3" style={{ marginTop: 14 }}>
                    <div className="stat-item">
                      <span className="stat-label">{t('quiz_completion')}</span>
                      <span className="stat-value">{assignment.completed_students ?? 0}/{assignment.assigned_students ?? 0}</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label">{t('quiz_started')}</span>
                      <span className="stat-value">{assignment.started_students ?? 0}/{assignment.assigned_students ?? 0}</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label">{t('quiz_first_accuracy')}</span>
                      <span className="stat-value">{percent(accuracy)}</span>
                    </div>
                  </div>

                  <div style={{ marginTop: 14 }}>
                    <div className="row" style={{ justifyContent: 'space-between', marginBottom: 6 }}>
                      <span className="muted">{t('quiz_completion')}</span>
                      <span className="muted">{assignment.completed_students ?? 0}/{assignment.assigned_students ?? 0}</span>
                    </div>
                    <div className={'bar ' + (completion >= 0.75 ? 'ok' : completion >= 0.5 ? 'warn' : 'bad')}>
                      <span style={{ width: percent(completion) }} />
                    </div>
                  </div>

                  <div className="row" style={{ justifyContent: 'flex-end', marginTop: 14 }}>
                    <button className="btn secondary" onClick={() => setExpandedId(expanded ? null : assignment.id)}>
                      {expanded ? t('quiz_hide_details') : t('quiz_view_details')}
                    </button>
                  </div>

                  {expanded && (
                    <div style={{ marginTop: 14, paddingTop: 14, borderTop: '1px solid var(--border)' }}>
                      <div style={{ fontWeight: 700, marginBottom: 10 }}>{t('quiz_topic_breakdown')}</div>
                      {assignment.topics?.length ? assignment.topics.map((topic) => (
                        <div key={topic.topic} style={{ marginTop: 10 }}>
                          <div className="row" style={{ justifyContent: 'space-between', marginBottom: 5 }}>
                            <span>{displayLabel(topic.topic, lang)}</span>
                            <span className="muted">{topic.correct ?? 0}/{topic.attempted ?? 0} · {percent(topic.accuracy)}</span>
                          </div>
                          <div className={'bar ' + (topic.accuracy >= 0.75 ? 'ok' : topic.accuracy >= 0.55 ? 'warn' : 'bad')}>
                            <span style={{ width: percent(topic.accuracy) }} />
                          </div>
                        </div>
                      )) : <div className="muted">{t('quiz_no_details')}</div>}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        ) : (
          <div className="empty">
            <div className="ico">▣</div>
            <div style={{ maxWidth: 560, lineHeight: 1.6 }}>{t('quiz_empty')}</div>
          </div>
        )}
      </Card>
    </div>
  )
}
