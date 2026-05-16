import { useState, useEffect, lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import { ToastProvider } from './components/Toast'
import './index.css'
import './App.css'

const Dashboard = lazy(() => import('./pages/Dashboard'))
const Visits    = lazy(() => import('./pages/Visits'))
const Cats      = lazy(() => import('./pages/Cats'))

const LIGHT_THEME = 'light-professional'
const DARK_THEME = 'dark-elegant'

function Sidebar({ theme, onToggleTheme }) {
  const darkTheme = theme === DARK_THEME

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-mark" aria-hidden="true">🐱</div>
        <div>
          <h1>Cat health monitor</h1>
          <p>litterbox insights</p>
        </div>
      </div>

      <nav className="sidebar-nav">
        <NavLink to="/" end className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <span className="nav-icon">▦</span>
          Dashboard
        </NavLink>
        <NavLink to="/visits" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <span className="nav-icon">□</span>
          Visits
        </NavLink>
        <NavLink to="/cats" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <span className="nav-icon">◇</span>
          Cats
        </NavLink>
      </nav>

      <div className="sidebar-footer">
        <button
          className="btn btn-secondary btn-sm w-full theme-toggle"
          onClick={onToggleTheme}
          aria-label={`Switch to ${darkTheme ? 'light professional' : 'dark elegant'} theme`}
        >
          <span aria-hidden="true">{darkTheme ? '☼' : '◐'}</span>
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
  const toggleTheme = () => setTheme(current => current === DARK_THEME ? LIGHT_THEME : DARK_THEME)

  return (
    <div className="app-shell">
      <header className="mobile-header">
        <span className="mobile-logo">Cat health monitor</span>
        <button
          className="btn btn-secondary btn-sm"
          onClick={toggleTheme}
          aria-label={`Switch to ${darkTheme ? 'light professional' : 'dark elegant'} theme`}
        >
          {darkTheme ? '☼' : '◐'}
        </button>
      </header>

      <Sidebar
        theme={theme}
        onToggleTheme={toggleTheme}
      />
      <main className="main-content">
        <Suspense fallback={<div className="loading">Loading…</div>}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/visits" element={<Visits />} />
            <Route path="/cats" element={<Cats />} />
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
