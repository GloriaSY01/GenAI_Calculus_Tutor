import ReactECharts from 'echarts-for-react'
import { useLang } from '../i18n.jsx'

export function Card({ title, sub, right, children, className = '', icon }) {
  return (
    <section className={'card ' + className}>
      {(title || right) && (
        <div className="card-head">
          <div>
            {title && <div className="card-title">{icon && <span>{icon}</span>}{title}</div>}
            {sub && <div className="card-sub">{sub}</div>}
          </div>
          {right}
        </div>
      )}
      {children}
    </section>
  )
}

export function Kpi({ label, value, unit, delta, sub }) {
  const dir = delta > 0 ? 'up' : delta < 0 ? 'down' : 'flat'
  const arrow = delta > 0 ? '▲' : delta < 0 ? '▼' : '—'
  const pct = delta != null ? `${Math.abs(delta * 100).toFixed(1)}%` : ''
  const { t } = useLang()
  return (
    <div className="card kpi fade-in">
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">
        {value}{unit && <span className="unit">{unit}</span>}
      </div>
      {delta != null && (
        <div className={'kpi-delta ' + dir}>
          <span>{arrow}</span>{pct} <span className="muted" style={{ fontWeight: 600 }}>{t('kpi_vs_last')}</span>
        </div>
      )}
      {sub && <div className="kpi-sub">{sub}</div>}
    </div>
  )
}

/* Compact stat strip — small secondary metrics under the KPI row */
export function StatStrip({ items }) {
  return (
    <div className="stat-strip">
      {items.map((it, i) => (
        <div className="stat-item" key={i}>
          <span className="stat-label">{it.label}</span>
          <span className="stat-value">{it.value}</span>
        </div>
      ))}
    </div>
  )
}

export function Badge({ level = 'neutral', children }) {
  return <span className={'badge ' + level}>{children}</span>
}

export function Bar({ value, tone }) {
  const cls = tone || (value >= 0.75 ? 'ok' : value >= 0.55 ? 'warn' : 'bad')
  return <div className={'bar ' + cls}><span style={{ width: `${Math.round(value * 100)}%` }} /></div>
}

export function Loading({ rows = 3 }) {
  return (
    <div className="stack">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="skeleton" style={{ height: 84 }} />
      ))}
    </div>
  )
}

export function Empty({ icon = '🗂️', children }) {
  return <div className="empty"><div className="ico">{icon}</div>{children}</div>
}

export function MockPill({ show }) {
  if (!show) return null
  return (
    <span className="badge warn" title="Backend unreachable — showing demo data">
      ● demo data
    </span>
  )
}

/* ---- Chart theme helper: reads CSS vars so charts match light/dark ---- */
function cssVar(name, fallback) {
  if (typeof window === 'undefined') return fallback
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
  return v || fallback
}

export function Chart({ option, height = 300 }) {
  const text = cssVar('--text-2', '#4a5570')
  const grid = cssVar('--border', '#e6e9f2')
  const merged = {
    color: ['#3b66f0', '#7c5cff', '#17b26a', '#f79009', '#f04438', '#5d89fb'],
    textStyle: { fontFamily: 'Inter, sans-serif', color: text },
    grid: { left: 8, right: 16, top: 24, bottom: 8, containLabel: true },
    ...option,
    xAxis: option.xAxis && (Array.isArray(option.xAxis) ? option.xAxis : {
      axisLine: { lineStyle: { color: grid } },
      axisLabel: { color: text },
      splitLine: { show: false },
      ...option.xAxis,
    }),
    yAxis: option.yAxis && (Array.isArray(option.yAxis) ? option.yAxis : {
      axisLine: { show: false },
      axisLabel: { color: text },
      splitLine: { lineStyle: { color: grid, type: 'dashed' } },
      ...option.yAxis,
    }),
  }
  return <ReactECharts option={merged} style={{ height }} notMerge lazyUpdate opts={{ renderer: 'svg' }} />
}
