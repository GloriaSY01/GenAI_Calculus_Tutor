import { useEffect, useState } from 'react'
import { GraduationCap, Moon, School, Sun } from 'lucide-react'
import { useLang } from './i18n.jsx'
import StudentWorkspace from './pages/StudentWorkspace.jsx'

// Single teacher interface = the Streamlit dashboard on a fixed port.
// The React app is student-only; the "Teacher" control opens that dashboard,
// carrying the current language. No in-app React teacher views are kept.
const TEACHER_DASHBOARD_URL = 'http://127.0.0.1:8503/'

function useTheme() {
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'light')
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('theme', theme)
  }, [theme])
  return [theme, setTheme]
}

function ShellControls() {
  const { t, lang, setLang } = useLang()
  const [theme, setTheme] = useTheme()

  function openTeacher() {
    const url = new URL(TEACHER_DASHBOARD_URL)
    url.searchParams.set('lang', lang)
    window.location.href = url.toString()
  }

  return <>
    <div className="divider" />
    <div className="role-switch">
      <button className="role-btn" onClick={openTeacher}>
        <School size={15} /> {t('role_teacher')}
      </button>
      <button className="role-btn active">
        <GraduationCap size={15} /> {t('role_student')}
      </button>
    </div>
    <div className="row" style={{ justifyContent: 'space-between' }}>
      <span className="muted theme-label">
        {theme === 'dark' ? <Moon size={14} /> : <Sun size={14} />}
        {theme === 'dark' ? t('theme_dark') : t('theme_light')}
      </span>
      <button className={'switch' + (theme === 'dark' ? ' on' : '')}
        onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
        aria-label={theme === 'dark' ? t('theme_light') : t('theme_dark')} />
    </div>
    <div className="row" style={{ gap: 6 }}>
      {['zh', 'en'].map((language) => <button key={language} className="chip"
        onClick={() => setLang(language)} aria-pressed={lang === language}
        style={lang === language ? { borderColor: 'var(--brand-300)', color: 'var(--brand-700)', background: 'var(--brand-50)' } : {}}>
        {language === 'zh' ? '中文' : 'EN'}
      </button>)}
    </div>
  </>
}

export default function App() {
  return <StudentWorkspace topbar={<ShellControls />} />
}
