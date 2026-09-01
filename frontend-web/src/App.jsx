import { useEffect, useState } from 'react'
import { Routes, Route, NavLink, Navigate, useLocation } from 'react-router-dom'
import { useLang } from './i18n.jsx'
import Overview from './pages/Overview.jsx'
import Diagnose from './pages/Diagnose.jsx'
import Assign from './pages/Assign.jsx'
import Assistant from './pages/Assistant.jsx'
import StudentApp from './pages/StudentApp.jsx'

const NAV = [
  { to: '/overview',  key: 'nav_overview',  ic: '📊', group: 'main' },
  { to: '/diagnose',  key: 'nav_diagnose',  ic: '🔬', group: 'main' },
  { to: '/assign',    key: 'nav_assign',    ic: '📝', group: 'tools' },
  { to: '/assistant', key: 'nav_assistant', ic: '💬', group: 'tools' },
]

function useTheme() {
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'light')
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('theme', theme)
  }, [theme])
  return [theme, setTheme]
}

const TITLES = {
  '/overview': 'overview_title',
  '/diagnose': 'diagnose_title',
  '/assign': 'assign_title',
  '/assistant': 'assistant_title',
}

/* Shared footer controls: role switch + theme + language. */
function ShellControls({ role, setRole, theme, setTheme }) {
  const { t, lang, setLang } = useLang()
  return (
    <>
      <div className="divider" />
      <div className="role-switch">
        <button className={'role-btn' + (role === 'teacher' ? ' active' : '')} onClick={() => setRole('teacher')}>
          🧑‍🏫 {t('role_teacher')}
        </button>
        <button className={'role-btn' + (role === 'student' ? ' active' : '')} onClick={() => setRole('student')}>
          🎓 {t('role_student')}
        </button>
      </div>
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <span className="muted" style={{ fontSize: 13, fontWeight: 600 }}>
          {theme === 'dark' ? t('theme_dark') : t('theme_light')}
        </span>
        <button className={'switch' + (theme === 'dark' ? ' on' : '')}
          onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')} aria-label="toggle theme" />
      </div>
      <div className="row" style={{ gap: 6 }}>
        {['zh', 'en'].map((l) => (
          <button key={l} className="chip" onClick={() => setLang(l)}
            style={lang === l ? { borderColor: 'var(--brand-300)', color: 'var(--brand-700)', background: 'var(--brand-50)' } : {}}>
            {l === 'zh' ? '中文' : 'EN'}
          </button>
        ))}
      </div>
    </>
  )
}

export default function App() {
  const [role, setRole] = useState(() => localStorage.getItem('role') || 'teacher')
  const [theme, setTheme] = useTheme()
  const setRoleP = (r) => { setRole(r); localStorage.setItem('role', r) }

  const controls = <ShellControls role={role} setRole={setRoleP} theme={theme} setTheme={setTheme} />

  if (role === 'student') return <StudentApp topbar={controls} />
  return <TeacherApp controls={controls} />
}

function TeacherApp({ controls }) {
  const { t } = useLang()
  const loc = useLocation()
  const titleKey = TITLES[loc.pathname] || 'app_title'

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-logo">∫</div>
          <div>
            <div className="brand-name">{t('app_title')}</div>
            <div className="brand-sub">{t('app_sub')}</div>
          </div>
        </div>

        <div className="nav-group-label">{t('nav_group_main')}</div>
        {NAV.filter((n) => n.group === 'main').map((n) => (
          <NavLink key={n.to} to={n.to} className={({ isActive }) => 'nav-item' + (isActive ? ' active' : '')}>
            <span className="ic">{n.ic}</span>{t(n.key)}
          </NavLink>
        ))}

        <div className="nav-group-label">{t('nav_group_tools')}</div>
        {NAV.filter((n) => n.group === 'tools').map((n) => (
          <NavLink key={n.to} to={n.to} className={({ isActive }) => 'nav-item' + (isActive ? ' active' : '')}>
            <span className="ic">{n.ic}</span>{t(n.key)}
          </NavLink>
        ))}

        <div className="sidebar-foot">{controls}</div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <div className="crumb">{t('app_sub')}</div>
            <h1>{t(titleKey)}</h1>
          </div>
          <div className="topbar-spacer" />
        </header>

        <div className="content" key={loc.pathname}>
          <Routes>
            <Route path="/" element={<Navigate to="/overview" replace />} />
            <Route path="/overview" element={<Overview />} />
            <Route path="/diagnose" element={<Diagnose />} />
            <Route path="/assign" element={<Assign />} />
            <Route path="/assistant" element={<Assistant />} />
            <Route path="*" element={<Navigate to="/overview" replace />} />
          </Routes>
        </div>
      </main>
    </div>
  )
}
