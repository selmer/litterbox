import { useState, useEffect, lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import Icon from './components/Icon'
import { ToastProvider } from './components/Toast'
import { LanguageProvider } from './i18n/LanguageContext'
import { useLanguage } from './i18n/useLanguage'
import './index.css'
import './App.css'

const Dashboard = lazy(() => import('./pages/Dashboard'))
const Visits    = lazy(() => import('./pages/Visits'))
const Cats      = lazy(() => import('./pages/Cats'))
const CatDetail = lazy(() => import('./pages/CatDetail'))
const Diagnostics = lazy(() => import('./pages/Diagnostics'))
const Admin = lazy(() => import('./pages/Admin'))

const LIGHT_THEME = 'light-professional'
const DARK_THEME = 'dark-elegant'

function Sidebar({ theme, onToggleTheme }) {
  const { t } = useLanguage()
  const darkTheme = theme === DARK_THEME
  const targetThemeLabel = darkTheme ? t('theme.lightProfessional') : t('theme.darkElegant')

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-mark" aria-hidden="true">
          <Icon name="cat" size={20} />
        </div>
        <div>
          <h1>{t('app.name')}</h1>
          <p>{t('app.tagline')}</p>
        </div>
      </div>

      <nav className="sidebar-nav">
        <NavLink to="/" end className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <Icon name="dashboard" className="nav-icon" />
          {t('nav.dashboard')}
        </NavLink>
        <NavLink to="/visits" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <Icon name="visits" className="nav-icon" />
          {t('nav.visits')}
        </NavLink>
        <NavLink to="/cats" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <Icon name="cat" className="nav-icon" />
          {t('nav.cats')}
        </NavLink>
        <NavLink to="/diagnostics" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <Icon name="activity" className="nav-icon" />
          {t('nav.diagnostics')}
        </NavLink>
        <NavLink to="/admin" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <Icon name="archive" className="nav-icon" />
          {t('nav.admin')}
        </NavLink>
      </nav>

      <div className="sidebar-footer">
        <button
          className="btn btn-secondary btn-sm w-full theme-toggle"
          onClick={onToggleTheme}
          aria-label={t('theme.switchTo', { theme: targetThemeLabel })}
        >
          <Icon name={darkTheme ? 'sun' : 'moon'} size={15} />
          {targetThemeLabel}
        </button>
      </div>
    </aside>
  )
}

function AppShell() {
  const { t } = useLanguage()
  const [theme, setTheme] = useState(() => {
    const storedTheme = localStorage.getItem('cat-health-monitor-theme') || localStorage.getItem('theme')
    return storedTheme === DARK_THEME || storedTheme === 'dark' ? DARK_THEME : LIGHT_THEME
  })

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('cat-health-monitor-theme', theme)
  }, [theme])

  const darkTheme = theme === DARK_THEME
  const targetThemeLabel = darkTheme ? t('theme.lightProfessional') : t('theme.darkElegant')
  const toggleTheme = () => setTheme(current => current === DARK_THEME ? LIGHT_THEME : DARK_THEME)

  return (
    <div className="app-shell">
      <header className="mobile-header">
        <span className="mobile-logo">{t('app.name')}</span>
        <button
          className="btn btn-secondary btn-sm mobile-theme-toggle"
          onClick={toggleTheme}
          aria-label={t('theme.switchTo', { theme: targetThemeLabel })}
        >
          <Icon name={darkTheme ? 'sun' : 'moon'} size={15} />
        </button>
      </header>

      <Sidebar theme={theme} onToggleTheme={toggleTheme} />
      <main className="main-content">
        <Suspense fallback={<div className="loading">{t('state.loading')}</div>}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/visits" element={<Visits />} />
            <Route path="/cats" element={<Cats />} />
            <Route path="/cats/:catId" element={<CatDetail />} />
            <Route path="/diagnostics" element={<Diagnostics />} />
            <Route path="/admin" element={<Admin />} />
          </Routes>
        </Suspense>
      </main>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <LanguageProvider>
        <ToastProvider>
          <AppShell />
        </ToastProvider>
      </LanguageProvider>
    </BrowserRouter>
  )
}
