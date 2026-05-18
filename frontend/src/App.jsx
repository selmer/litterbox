import { useState, useEffect, lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import Icon from './components/Icon'
import { ToastProvider } from './components/Toast'
import './index.css'
import './App.css'

const Dashboard = lazy(() => import('./pages/Dashboard'))
const Visits    = lazy(() => import('./pages/Visits'))
const Cats      = lazy(() => import('./pages/Cats'))
const CatDetail = lazy(() => import('./pages/CatDetail'))

const LIGHT_THEME = 'light-professional'
const DARK_THEME = 'dark-elegant'

function Sidebar({ theme, onToggleTheme }) {
  const darkTheme = theme === DARK_THEME
  const targetThemeLabel = darkTheme ? 'light professional' : 'dark elegant'

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-mark" aria-hidden="true">
          <Icon name="cat" size={20} />
        </div>
        <div>
          <h1>Cat health monitor</h1>
          <p>litterbox insights</p>
        </div>
      </div>

      <nav className="sidebar-nav">
        <NavLink to="/" end className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <Icon name="dashboard" className="nav-icon" />
          Dashboard
        </NavLink>
        <NavLink to="/visits" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <Icon name="visits" className="nav-icon" />
          Visits
        </NavLink>
        <NavLink to="/cats" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <Icon name="cat" className="nav-icon" />
          Cats
        </NavLink>
      </nav>

      <div className="sidebar-footer">
        <button
          className="btn btn-secondary btn-sm w-full theme-toggle"
          onClick={onToggleTheme}
          aria-label={`Switch to ${targetThemeLabel} theme`}
        >
          <Icon name={darkTheme ? 'sun' : 'moon'} size={15} />
          {darkTheme ? 'Light professional' : 'Dark elegant'}
        </button>
      </div>
    </aside>
  )
}

function AppShell() {
  const [theme, setTheme] = useState(() => {
    const storedTheme = localStorage.getItem('cat-health-monitor-theme') || localStorage.getItem('theme')
    return storedTheme === DARK_THEME || storedTheme === 'dark' ? DARK_THEME : LIGHT_THEME
  })

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('cat-health-monitor-theme', theme)
  }, [theme])

  const darkTheme = theme === DARK_THEME
  const targetThemeLabel = darkTheme ? 'light professional' : 'dark elegant'
  const toggleTheme = () => setTheme(current => current === DARK_THEME ? LIGHT_THEME : DARK_THEME)

  return (
    <div className="app-shell">
      <header className="mobile-header">
        <span className="mobile-logo">Cat health monitor</span>
        <button
          className="btn btn-secondary btn-sm mobile-theme-toggle"
          onClick={toggleTheme}
          aria-label={`Switch to ${targetThemeLabel} theme`}
        >
          <Icon name={darkTheme ? 'sun' : 'moon'} size={15} />
        </button>
      </header>

      <Sidebar theme={theme} onToggleTheme={toggleTheme} />
      <main className="main-content">
        <Suspense fallback={<div className="loading">Loading…</div>}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/visits" element={<Visits />} />
            <Route path="/cats" element={<Cats />} />
            <Route path="/cats/:catId" element={<CatDetail />} />
          </Routes>
        </Suspense>
      </main>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <AppShell />
      </ToastProvider>
    </BrowserRouter>
  )
}
