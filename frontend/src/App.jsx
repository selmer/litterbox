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
const C64_THEME = 'commodore-64'

const THEME_OPTIONS = [
  { id: LIGHT_THEME, labelKey: 'theme.lightProfessional', shortLabelKey: 'theme.lightShort' },
  { id: DARK_THEME, labelKey: 'theme.darkElegant', shortLabelKey: 'theme.darkShort' },
  { id: C64_THEME, labelKey: 'theme.commodore64', shortLabelKey: 'theme.c64Short' },
]

function normalizeTheme(value) {
  if (value === DARK_THEME || value === 'dark') return DARK_THEME
  if (value === C64_THEME) return C64_THEME
  return LIGHT_THEME
}

function ThemeSelector({ theme, onThemeChange, compact = false }) {
  const { t } = useLanguage()

  return (
    <div className={`theme-selector ${compact ? 'theme-selector--compact' : ''}`} role="group" aria-label={t('theme.selectTheme')}>
      {THEME_OPTIONS.map(option => (
        <button
          key={option.id}
          type="button"
          className={`theme-option ${theme === option.id ? 'active' : ''}`}
          onClick={() => onThemeChange(option.id)}
          aria-pressed={theme === option.id}
          title={t(option.labelKey)}
        >
          {t(compact ? option.shortLabelKey : option.labelKey)}
        </button>
      ))}
    </div>
  )
}

function Sidebar({ theme, onThemeChange }) {
  const { t } = useLanguage()

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
        <NavLink to="/admin" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <Icon name="archive" className="nav-icon" />
          {t('nav.admin')}
        </NavLink>
      </nav>

      <div className="sidebar-footer">
        <ThemeSelector theme={theme} onThemeChange={onThemeChange} />
      </div>
    </aside>
  )
}

function AppShell() {
  const { t } = useLanguage()
  const [theme, setTheme] = useState(() => {
    const storedTheme = localStorage.getItem('cat-health-monitor-theme') || localStorage.getItem('theme')
    return normalizeTheme(storedTheme)
  })

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('cat-health-monitor-theme', theme)
  }, [theme])

  return (
    <div className="app-shell">
      <header className="mobile-header">
        <span className="mobile-logo">{t('app.name')}</span>
        <ThemeSelector theme={theme} onThemeChange={setTheme} compact />
      </header>

      <Sidebar theme={theme} onThemeChange={setTheme} />
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
