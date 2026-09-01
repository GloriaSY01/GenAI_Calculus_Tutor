import { useLang } from '../i18n.jsx'
import { useAnalytics } from '../components/hooks.js'
import { Card, Loading, MockPill, Chart, Badge } from '../components/ui.jsx'

export default function Diagnose() {
  const { t } = useLang()
  const { loading, data, error, reload } = useAnalytics()

  if (loading) return <Loading rows={2} />
  if (error) return (
    <Card><div className="empty"><div className="ico">⚠️</div>{t('error_load')}
      <div style={{ marginTop: 14 }}><button className="btn primary" onClick={reload}>{t('retry')}</button></div>
    </div></Card>
  )

  const topics = data.by_topic || []
  const dist = data.reasoning_distribution || []
  const practice = data.practice || []
  const distColors = { Excellent: '#17b26a', Good: '#5d89fb', Fair: '#f79009', Weak: '#f04438', None: '#c2c8d6' }

  return (
    <div className="stack fade-in">
      <div className="row" style={{ justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div className="section-step">{t('diag_step')}</div>
          <h2 className="section-head">{t('diag_head')}</h2>
          <p className="muted" style={{ margin: '4px 0 0' }}>{t('diag_head_sub')}</p>
        </div>
        <MockPill show={data._mock} />
      </div>

      <div className="grid cols-2">
        <Card title={t('topic_need')} icon="🩺" sub={t('topic_need_sub')}>
          <Chart height={320} option={{
            tooltip: { trigger: 'axis', valueFormatter: (v) => v + '%' },
            xAxis: { type: 'value', max: 100 },
            yAxis: { type: 'category', data: topics.map(x => x.topic).reverse(), axisLine: { show: false } },
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
          }} />
        </Card>

        <Card title={t('reasoning_explain')} icon="🧠" sub={t('reasoning_explain_sub')}>
          <Chart height={320} option={{
            tooltip: { trigger: 'item' },
            legend: { bottom: 0 },
            series: [{
              type: 'pie', radius: ['52%', '74%'], center: ['50%', '44%'],
              itemStyle: { borderRadius: 8, borderColor: 'var(--surface)', borderWidth: 3 },
              label: { show: true, formatter: '{b}\n{d}%', color: 'var(--text-2)' },
              data: dist.map(d => ({ name: d.grade, value: d.count, itemStyle: { color: distColors[d.grade] } })),
            }],
          }} />
        </Card>
      </div>

      <Card title={t('quiz_scores')} icon="📝" sub={t('quiz_scores_sub')}>
        {practice.length > 0 ? (
          <table className="tbl">
            <thead>
              <tr><th>Session</th><th>Solved</th><th style={{ width: '40%' }}>Progress</th><th>Avg time</th></tr>
            </thead>
            <tbody>
              {practice.map((p, i) => {
                const ratio = p.solved / p.total
                return (
                  <tr key={i}>
                    <td style={{ fontWeight: 700 }}>{p.session}</td>
                    <td className="muted">{p.solved}/{p.total}</td>
                    <td>
                      <div className="row" style={{ gap: 10 }}>
                        <div style={{ flex: 1 }} className={'bar ' + (ratio >= 0.75 ? 'ok' : ratio >= 0.5 ? 'warn' : 'bad')}>
                          <span style={{ width: `${ratio * 100}%` }} />
                        </div>
                        <span style={{ fontWeight: 700 }}>{Math.round(ratio * 100)}%</span>
                      </div>
                    </td>
                    <td><Badge level="neutral">{p.avg_time}</Badge></td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        ) : (
          <div className="empty">
            <div className="ico">🧾</div>
            <div style={{ maxWidth: 560, lineHeight: 1.6 }}>{t('quiz_empty')}</div>
          </div>
        )}
      </Card>
    </div>
  )
}
