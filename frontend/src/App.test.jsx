import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import App from './App'

vi.mock('./api/client', () => ({
  getApiErrorMessage: error => error.message || 'API error',
  getDashboard: vi.fn(() => Promise.resolve({
    cats: [],
    unidentified_visits_today: 0,
    cleaning_cycles_today: 0,
    poller_healthy: true,
    poller_last_successful_at: null,
    poller_last_attempted_at: null,
    poller_last_error: null,
    generated_at: '2026-06-08T12:00:00Z',
  })),
  getWeightHistory: vi.fn(() => Promise.resolve([])),
  getVisits: vi.fn(() => Promise.resolve([])),
  getCats: vi.fn(() => Promise.resolve([])),
  createVisit: vi.fn(),
}))

describe('App navigation', () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  it('keeps diagnostics out of the primary sidebar navigation', () => {
    render(<App />)

    expect(screen.getByRole('link', { name: 'Dashboard' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Visits' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Cats' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Admin' })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Diagnostics' })).not.toBeInTheDocument()
  })
  it('selects and persists the Commodore 64 theme', () => {
    render(<App />)

    fireEvent.click(screen.getAllByRole('button', { name: 'C64' })[0])

    expect(document.documentElement).toHaveAttribute('data-theme', 'commodore-64')
    expect(window.localStorage.getItem('cat-health-monitor-theme')).toBe('commodore-64')
  })

  it('restores a stored Commodore 64 theme', () => {
    window.localStorage.setItem('cat-health-monitor-theme', 'commodore-64')

    render(<App />)

    expect(document.documentElement).toHaveAttribute('data-theme', 'commodore-64')
    expect(screen.getAllByRole('button', { name: 'C64' })[0]).toHaveAttribute('aria-pressed', 'true')
  })

  it('falls back to the light theme for unknown stored themes', () => {
    window.localStorage.setItem('cat-health-monitor-theme', 'unknown-theme')

    render(<App />)

    expect(document.documentElement).toHaveAttribute('data-theme', 'light-professional')
    expect(window.localStorage.getItem('cat-health-monitor-theme')).toBe('light-professional')
  })

})
