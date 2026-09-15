import { displayLabel, localizeInsight } from '../localization.js'
import { useNavigate } from 'react-router-dom'
import { useLang } from '../i18n.jsx'
import { useAnalytics } from '../components/hooks.js'
import { Card, Kpi, Badge, Bar, Loading, MockPill, StatStrip } from '../components/ui.jsx'

export default function Overview() {
  const { t, lang } = useLang()
  const navigate = useNavigate()
  const { loading, data, error, reload } = useAnalytics()

  if (loading) return <Loading rows={2} />
  if (error) return (
    <Card>
      <div className="empty">
        <div className="ico">⚠️</div>{t('error_load')}
        <div style={{ marginTop: 14 }}>
          <button className="btn primary" onClick={reload}>{t('retry')}</button>
        </div>
      </div>
    </Card>
  )

  const k = data.kpis || {}
  const rMax = k.reasoning_score_max || data.reasoning_max || 4
  const topics = data.by_topic || []
  const ex = data.extra || {}

  const pct = (v) => `${Math.round((v || 0) * 100)}%`

  return (
    <div className="stack fade-in">
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <p className="muted" style={{ margin: 0 }}>{t('overview_sub')}</p>
        <MockPill show={data._mock} />
      </div>

      <div className="grid cols-3">
        <Kpi label={t('kpi_accuracy')}  value={((k.avg_accuracy ?? 0) * 100).toFixed(0)} unit="%" delta={k.avg_accuracy_delta} sub={t('kpi_solve_sub')} />
        <Kpi label={t('kpi_students')}  value={k.active_students ?? 0} delta={k.active_students_delta} sub={t('kpi_students_sub')} />
        <Kpi label={t('kpi_sessions')}  value={(k.problems_solved ?? 0).toLocaleString()} delta={k.problems_solved_delta} sub={t('kpi_sessions_sub').replace('{n}', (ex.n_turns ?? 0).toLocaleString())} />
      </div>

      <StatStrip items={[
        { label: t('kpi_reasoning'), value: `${(k.reasoning_score ?? 0).toFixed(1)}/${rMax}` },
        { label: t('kpi_turns'),     value: (ex.avg_turns_per_session ?? 0).toFixed(1) },
        { label: t('kpi_gaming'),    value: pct(ex.gaming_rate) },
        { label: t('kpi_guardrail'), value: pct(ex.guardrail_rate) },
      ]} />

      <div className="grid cols-2">
        <Card title={t('insights_title')} icon="✨" sub={t('overview_title')}>
          {(!data.insights || data.insights.length === 0)
            ? <div className="muted">{t('insights_empty')}</div>
            : <div className="stack" style={{ gap: 14 }}>
                {data.insights.map(it => localizeInsight(it, lang)).map((it, i) => (
                  <div key={i} className="row" style={{ alignItems: 'start', gap: 12 }}>
                    <Badge level={it.level}>
                      {it.level === 'bad' ? '!' : it.level === 'warn' ? '~' : '✓'}
                    </Badge>
                    <div style={{ lineHeight: 1.5 }}>
                      {it.title && <div style={{ fontWeight: 700 }}>{it.title}</div>}
                      <div className={it.title ? 'muted' : ''} style={{ fontSize: it.title ? 13.5 : 14 }}>{it.text}</div>
                    </div>
                  </div>
                ))}
              </div>}
        </Card>

        <Card title={t('guide_title')} icon="🧭" sub={t('guide_sub')}>
          <GuideRow icon="🩺" name={t('nav_diagnose')} desc={t('guide_diagnose')}
            cta={t('guide_go').replace('{name}', t('nav_diagnose'))} onClick={() => navigate('/diagnose')} />
          <GuideRow icon="📝" name={t('nav_assign')} desc={t('guide_assign')}
            cta={t('guide_go').replace('{name}', t('nav_assign'))} onClick={() => navigate('/assign')} />
          <GuideRow icon="💬" name={t('nav_assistant')} desc={t('guide_assistant')}
            cta={t('guide_go').replace('{name}', t('nav_assistant'))} onClick={() => navigate('/assistant')} />
        </Card>
      </div>

      <Card title={t('topic_health')} icon="🩺" sub={t('topic_health_sub')}>
        <table className="tbl">
          <thead>
            <tr>
              <th>{t('assign_topic')}</th>
              <th style={{ width: '42%' }}>{t('kpi_accuracy')}</th>
              <th>{t('attempts')}</th>
              <th>{t('kpi_reasoning')}</th>
              <th>{t('gaming')}</th>
            </tr>
          </thead>
          <tbody>
            {topics.map((row) => (
              <tr key={displayLabel(row.topic, lang)}>
                <td style={{ fontWeight: 700 }}>{displayLabel(row.topic, lang)}</td>
                <td>
                  <div className="row" style={{ gap: 10 }}>
                    <div style={{ flex: 1 }}><Bar value={row.accuracy} /></div>
                    <span style={{ fontVariantNumeric: 'tabular-nums', fontWeight: 700 }}>
                      {(row.accuracy * 100).toFixed(0)}%
                    </span>
                  </div>
                </td>
                <td className="muted">{row.attempts}</td>
                <td className="muted">{(row.reasoning ?? 0).toFixed(1)}/{rMax}</td>
                <td>
                  <Badge level={row.gaming >= 0.25 ? 'bad' : row.gaming >= 0.15 ? 'warn' : 'ok'}>
                    {Math.round((row.gaming ?? 0) * 100)}%
                  </Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  )
}

function GuideRow({ icon, name, desc, cta, onClick }) {
  return (
    <div className="guide-row">
      <span className="guide-ic">{icon}</span>
      <div className="guide-body">
        <div className="guide-name">{name}</div>
        <div className="guide-desc">{desc}</div>
      </div>
      <button className="btn sm" onClick={onClick}>{cta} →</button>
    </div>
  )
}
