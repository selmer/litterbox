import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Diagnostics from './Diagnostics'
import * as client from '../api/client'

vi.mock('../api/client')

const summary = {
  generated_at: '2026-05-18T21:00:00Z',
  poller: {
    mode: 'polling',
    healthy: true,
    last_successful_at: '2026-05-18T20:59:00Z',
    last_attempted_at: '2026-05-18T21:00:00Z',
    last_error: null,
    interval_seconds: 300,
    healthy_threshold_seconds: 900,
  },
  open_visits: {
    count: 1,
    oldest_started_at: '2026-05-18T20:55:00Z',
    oldest_age_seconds: 300,
    visits: [
      {
        id: 73,
        cat_id: 1,
        identified_by: 'auto',
        started_at: '2026-05-18T20:55:00Z',
        age_seconds: 300,
        weight_kg: 3.83,
        last_weight_at: '2026-05-18T20:55:00Z',
        duration_source: 'unknown',
      },
    ],
  },
  reconciliation: {
    reconciliation_attempts: 2,
    report_logs_fetched: 1,
    pending_retries: 1,
    completion_matches: 0,
    hard_timeouts: 0,
    latest_event_at: '2026-05-18T20:59:00Z',
  },
  recent_diagnostics: [
    {
      id: 1,
      visit_id: 73,
      event_type: 'reconciliation_attempt',
      payload: { elapsed_seconds: 300 },
      recorded_at: '2026-05-18T20:59:00Z',
    },
  ],
  display: {
    generated_at: '2026-05-18T21:00:00Z',
    refresh_after_seconds: 3600,
    status: { label: 'Polling', healthy: true, last_successful_at: '2026-05-18T20:59:00Z', message: null },
    latest_visit: { cat_name: 'Plurk', identified: true, started_at: '2026-05-18T20:55:00Z', time_ago_label: '5 minutes ago', duration_seconds: null, weight_kg: 3.83, identified_by: 'auto' },
    today: { visits: 3, time_in_box_seconds: 0, cleaning_cycles: 0, unidentified_visits: 0 },
    chart: null,
    cats: [{ name: 'Plurk', visits_today: 3, last_weight_kg: 3.83, latest_weight_kg: 3.83, latest_weight_at: '2026-05-18T20:55:00Z', sparkline: [3.8, 3.83] }],
    alert: null,
  },
  endpoints: [
    { label: 'Diagnostics summary', method: 'GET', path: '/diagnostics/summary' },
    { label: 'Visit diagnostics', method: 'GET', path: '/visits/{visit_id}/diagnostics' },
  ],
}

function renderDiagnostics(initialEntry = '/diagnostics') {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Diagnostics />
    </MemoryRouter>
  )
}

describe('Diagnostics page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    client.getDiagnosticsSummary.mockResolvedValue(summary)
  })

  it('loads operational sections from the diagnostics summary', async () => {
    renderDiagnostics()

    expect(await screen.findByRole('heading', { name: 'Diagnostics' })).toBeInTheDocument()
    expect(screen.getAllByText('Healthy').length).toBeGreaterThan(0)
    expect(screen.getByText('Open visits')).toBeInTheDocument()
    expect(screen.getAllByText('#73').length).toBeGreaterThan(0)
    expect(screen.getByText('reconciliation_attempt')).toBeInTheDocument()
    expect(screen.getByText('/diagnostics/summary')).toBeInTheDocument()
    expect(client.getDiagnosticsSummary).toHaveBeenCalled()
  })

  it('highlights a selected visit from the query string', async () => {
    renderDiagnostics('/diagnostics?visit=73')

    await waitFor(() => expect(screen.getByText(/Showing recent diagnostics for visit/)).toBeInTheDocument())
    expect(screen.getByText(/1 event\(s\) highlighted below/)).toBeInTheDocument()
  })

  it('renders an error state cleanly', async () => {
    client.getDiagnosticsSummary.mockRejectedValue(new Error('API down'))
    renderDiagnostics()

    expect(await screen.findByText('API down')).toBeInTheDocument()
  })
})
