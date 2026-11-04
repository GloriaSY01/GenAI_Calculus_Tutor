import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChartNoAxesCombined, ClipboardPlus, GraduationCap, LayoutDashboard, Moon, School, Sun } from 'lucide-react'
import { useLang } from './i18n.jsx'
import { api } from './api.js'
import StudentWorkspace from './pages/StudentWorkspace.jsx'
import LegacyDashboard from './pages/teacher/LegacyDashboard.jsx'

function useTheme() {
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'light')
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('theme', theme)
  }, [theme])
  return [theme, setTheme]
}

function ShellControls({ role, setRole, theme, setTheme }) {
  const { t, lang, setLang } = useLang()
  return <>
    <div className="divider" />
    <div className="role-switch">
      <button className={'role-btn' + (role === 'teacher' ? ' active' : '')} onClick={() => setRole('teacher')}>
        <School size={15} /> {t('role_teacher')}
      </button>
      <button className={'role-btn' + (role === 'student' ? ' active' : '')} onClick={() => setRole('student')}>
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
  const navigate = useNavigate()
  const [role, setRole] = useState(() => localStorage.getItem('role') || 'student')
  const [theme, setTheme] = useTheme()

  function switchRole(nextRole) {
    setRole(nextRole)
    localStorage.setItem('role', nextRole)
    navigate(nextRole === 'teacher' ? '/overview' : '/')
  }

  const controls = <ShellControls role={role} setRole={switchRole} theme={theme} setTheme={setTheme} />
  return role === 'student' ? <StudentWorkspace topbar={controls} /> : <LegacyDashboard theme={theme} setTheme={setTheme} onStudent={() => switchRole('student')} />
}
