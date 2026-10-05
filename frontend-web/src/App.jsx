import { useEffect, useState } from 'react'
import { Navigate, NavLink, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { ChartNoAxesCombined, ClipboardPlus, GraduationCap, LayoutDashboard, Moon, School, Sun } from 'lucide-react'
import { useLang } from './i18n.jsx'
import { api } from './api.js'
import { TeacherClassContext } from './components/TeacherClass.jsx'
import Assign from './pages/Assign.jsx'
import Diagnose from './pages/Diagnose.jsx'
import Overview from './pages/Overview.jsx'
import StudentWorkspace from './pages/StudentWorkspace.jsx'
import TeacherAgent from './pages/TeacherAgent.jsx'

const NAV = [
  { to: '/overview', key: 'nav_overview', icon: LayoutDashboard },
  { to: '/diagnose', key: 'nav_diagnose', icon: ChartNoAxesCombined },
  { to: '/assign', key: 'nav_assign', icon: ClipboardPlus },
]

const TITLES = {
  '/overview': 'overview_title',
  '/diagnose': 'diagnose_title',
  '/assign': 'assign_title',
}

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
  return role === 'student' ? <StudentWorkspace topbar={controls} /> : <TeacherApp controls={controls} />
}

function TeacherApp({ controls }) {
  const { t, lang } = useLang()
  const location = useLocation()
  const [classId, setClassId] = useState('')
  const [classes, setClasses] = useState([])

  useEffect(() => {
    let active = true
    api.getClasses().then((result) => {
      if (!active) return
      const nextClasses = result.classes || []
      setClasses(nextClasses)
      setClassId((current) => current || nextClasses[0]?.id || '')
    })
    return () => { active = false }
  }, [])

  const classLabel = classes.find((item) => item.id === classId)?.label
  const titleKey = TITLES[location.pathname] || 'overview_title'

  return <div className="app-shell teacher-shell">
    <aside className="sidebar teacher-sidebar">
      <div className="brand"><div className="brand-logo">∫</div><div>
        <div className="brand-name">{t('app_title')}</div>
        <div className="brand-sub">{t('app_sub')}</div>
      </div></div>

      <div className="nav-group-label">{lang === 'zh' ? '教师工作台' : 'TEACHER WORKSPACE'}</div>
      <label className="teacher-class-picker">
        <span className="ctrl-label">{lang === 'zh' ? '当前班级' : 'Current class'}</span>
        <select className="inp" value={classId} onChange={(event) => setClassId(event.target.value)}>
          <option value="">{lang === 'zh' ? '全部记录（含未分班）' : 'All records (including unassigned)'}</option>
          {classes.map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}
        </select>
      </label>

      <nav aria-label={lang === 'zh' ? '教师端导航' : 'Teacher navigation'}>
        {NAV.map((item) => <NavLink key={item.to} to={item.to}
          className={({ isActive }) => 'nav-item' + (isActive ? ' active' : '')}>
          <span className="ic"><item.icon size={18} /></span>{t(item.key)}
        </NavLink>)}
      </nav>
      <div className="sidebar-foot">{controls}</div>
    </aside>

    <main className="main">
      <header className="topbar"><div><div className="crumb">{t('app_sub')}</div><h1>{t(titleKey)}</h1></div></header>
      <TeacherClassContext.Provider value={classId}>
        <div className="content" key={location.pathname + classId}>
          <Routes>
            <Route path="/" element={<Navigate to="/overview" replace />} />
            <Route path="/overview" element={<Overview />} />
            <Route path="/diagnose" element={<Diagnose />} />
            <Route path="/assign" element={<Assign />} />
            <Route path="*" element={<Navigate to="/overview" replace />} />
          </Routes>
        </div>
      </TeacherClassContext.Provider>
    </main>

    <TeacherAgent classId={classId} classLabel={classLabel} />
  </div>
}
