import { useEffect, useState } from 'react'
import { useLang } from './i18n.jsx'
import StudentApp from './pages/StudentWorkspace.jsx'

function useTheme() {
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'light')
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('theme', theme)
  }, [theme])
  return [theme, setTheme]
}

const TEACHER_DASHBOARD_URL = import.meta.env.VITE_TEACHER_DASHBOARD_URL || 'http://127.0.0.1:8502/'

function teacherDashboardUrl(lang) {
  const url = new URL(TEACHER_DASHBOARD_URL)
  url.searchParams.set('lang', lang || 'zh')
  return url.toString()
}

/* Shared footer controls: role switch + theme + language. */
function ShellControls({ role, setRole, theme, setTheme }) {
  const { t, lang, setLang } = useLang()
  return (
    <>
      <div className="divider" />
      <div className="role-switch">
        <button className="role-btn" onClick={() => setRole('teacher', lang)}>
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
  const [role, setRole] = useState('student')
  const [theme, setTheme] = useTheme()
  const setRoleP = (r, lang) => {
    localStorage.setItem('role', r)
    if (r === 'teacher') {
      window.location.href = teacherDashboardUrl(lang)
      return
    }
    setRole(r)
  }

  const controls = <ShellControls role={role} setRole={setRoleP} theme={theme} setTheme={setTheme} />

  return <StudentApp topbar={controls} />
}
