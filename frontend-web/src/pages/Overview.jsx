import { useNavigate } from 'react-router-dom'
import { useLang } from '../i18n.jsx'
import { useAnalytics } from '../components/hooks.js'
import { Card, Kpi, Badge, Bar, Loading, MockPill, Chart, StatStrip } from '../components/ui.jsx'

export default function Overview() {
  const { t } = useLang()
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
  const cond = data.conditions || []
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

      <div className="grid cols-4">
        <Kpi label={t('kpi_accuracy')}  value={((k.avg_accuracy ?? 0) * 100).toFixed(0)} unit="%" delta={k.avg_accuracy_delta} sub={t('kpi_solve_sub')} />
        <Kpi label={t('kpi_mastery')}   value={(ex.avg_final_mastery ?? 0).toFixed(1)} delta={null} sub={t('kpi_mastery_sub')} />
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
                {data.insights.map((it, i) => (
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

      {cond.length > 0 ? (
        <Card title={t('condition_compare')} icon="⚖️" sub={t('condition_sub')}>
          <Chart height={260} option={{
            tooltip: { trigger: 'axis' },
            legend: { data: [t('kpi_accuracy'), t('kpi_reasoning')], bottom: 0 },
            xAxis: { type: 'category', data: cond.map(c => c.condition) },
            yAxis: [{ type: 'value', max: 100, name: '%' }, { type: 'value', max: rMax, name: `/${rMax}` }],
            series: [
              { name: t('kpi_accuracy'), type: 'bar', barWidth: 34, itemStyle: { borderRadius: [6, 6, 0, 0] },
                data: cond.map(c => +(c.accuracy * 100).toFixed(1)) },
              { name: t('kpi_reasoning'), type: 'line', yAxisIndex: 1, smooth: true, symbolSize: 8,
                data: cond.map(c => c.reasoning) },
            ],
          }} />
        </Card>
      ) : (
        <Card title={t('mastery_vs_reasoning')} icon="🎯" sub={t('mastery_vs_reasoning_sub')}>
          <Chart height={280} option={{
            tooltip: {
              trigger: 'item',
              formatter: (p) => `${p.data[2]}<br/>${t('kpi_reasoning')}: ${p.data[0]}/${rMax}<br/>${t('kpi_mastery')}: ${p.data[1]}`,
            },
            xAxis: { type: 'value', name: t('kpi_reasoning'), max: rMax, min: 0 },
            yAxis: { type: 'value', name: t('kpi_mastery'), max: 100, min: 0 },
            series: [{
              type: 'scatter', symbolSize: (d) => 14 + Math.sqrt(d[3] || 1) * 3,
              data: topics.map(x => [x.reasoning, x.mastery, x.topic, x.attempts]),
              itemStyle: { color: '#3b66f0', opacity: .8 },
              label: { show: true, formatter: (p) => p.data[2], position: 'top', color: 'var(--text-2)', fontSize: 11 },
            }],
          }} />
        </Card>
      )}

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
              <tr key={row.topic}>
                <td style={{ fontWeight: 700 }}>{row.topic}</td>
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
