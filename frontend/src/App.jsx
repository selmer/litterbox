import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Visits from './pages/Visits'
import Cats from './pages/Cats'
import { ToastProvider } from './components/Toast'
import './index.css'
import './App.css'

function Sidebar({ darkMode, onToggleDarkMode }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <h1>litterbox</h1>
        <p>cat health monitor</p>
      </div>

      <nav className="sidebar-nav">
        <NavLink to="/" end className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <span className="nav-icon">📊</span>
          Dashboard
        </NavLink>
        <NavLink to="/visits" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <span className="nav-icon">📋</span>
          Visits
        </NavLink>
        <NavLink to="/cats" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <span className="nav-icon">🐱</span>
          Cats
        </NavLink>
      </nav>

      <div className="sidebar-footer">
        <button
          className="btn btn-secondary btn-sm w-full"
          onClick={onToggleDarkMode}
          style={{ justifyContent: 'center' }}
        >
          {darkMode ? '☀️ Light mode' : '🌙 Dark mode'}
        </button>
      </div>
    </aside>
  )
}

function AppShell() {
  const [darkMode, setDarkMode] = useState(() => {
    return localStorage.getItem('theme') === 'dark'
  })

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', darkMode ? 'dark' : 'light')
    localStorage.setItem('theme', darkMode ? 'dark' : 'light')
  }, [darkMode])

  return (
    <div className="app-shell">
      <header className="mobile-header">
        <span className="mobile-logo">litterbox</span>
        <button
          className="btn btn-secondary btn-sm"
          onClick={() => setDarkMode(d => !d)}
          aria-label="Toggle dark mode"
        >
          {darkMode ? '☀️' : '🌙'}
        </button>
      </header>

      <Sidebar
        darkMode={darkMode}
        onToggleDarkMode={() => setDarkMode(d => !d)}
      />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/visits" element={<Visits />} />
          <Route path="/cats" element={<Cats />} />
        </Routes>
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
