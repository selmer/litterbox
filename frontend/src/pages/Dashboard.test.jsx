import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Dashboard from './Dashboard'
import { ToastProvider } from '../components/Toast'
import * as client from '../api/client'

vi.mock('../api/client')

const dashboardBase = {
  generated_at: '2026-05-17T08:00:00Z',
  poller_healthy: true,
  poller_last_successful_at: '2026-05-17T07:58:00Z',
  poller_last_error: null,
  cats: [],
  unidentified_visits_today: 0,
  cleaning_cycles_today: 0,
  health_signals: [],
  device_faults: [],
  device_fault_code: null,
}

function renderDashboard() {
  return render(
    <MemoryRouter>
      <ToastProvider>
        <Dashboard />
      </ToastProvider>
    </MemoryRouter>
  )
}

describe('Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    client.getDashboard.mockResolvedValue(dashboardBase)
    client.getWeightHistory.mockResolvedValue([])
    client.getVisits.mockResolvedValue([])
    client.getCats.mockResolvedValue([])
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('shows a compact no-cats empty state', async () => {
    renderDashboard()

    await waitFor(() => expect(screen.getByText('No cats yet')).toBeInTheDocument())
    expect(screen.getByRole('link', { name: 'Add a cat' })).toHaveAttribute('href', '/cats')
  })

  it('shows active cats without visits as contextual placeholders', async () => {
    client.getCats.mockResolvedValue([
      { id: 1, name: 'Mochi', active: true, reference_weight_kg: 4.1, created_at: '2026-01-01T00:00:00Z' },
    ])

    renderDashboard()

    await waitFor(() => expect(screen.getByText('Mochi')).toBeInTheDocument())
    expect(screen.getByText('No visits yet')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Add visit' }))
    expect(screen.getByText('Manual visit for Mochi')).toBeInTheDocument()
  })

  it('does not show a device fault banner when there are no faults', async () => {
    renderDashboard()

    await waitFor(() => expect(screen.getByText('No cats yet')).toBeInTheDocument())
    expect(screen.queryByText(/Device fault/)).not.toBeInTheDocument()
  })

  it('shows a device fault banner with a diagnostics link', async () => {
    client.getDashboard.mockResolvedValue({
      ...dashboardBase,
      device_faults: ['motor_fault'],
      device_fault_code: 1,
    })

    renderDashboard()

    await waitFor(() => expect(screen.getByText(/Device fault: Motor fault/)).toBeInTheDocument())
    expect(screen.getByRole('link', { name: 'View diagnostics' })).toHaveAttribute('href', '/diagnostics')
  })

  it('shows multiple device faults readably', async () => {
    client.getDashboard.mockResolvedValue({
      ...dashboardBase,
      device_faults: ['motor_fault', 'g_sensor_fault', 'unknown_fault_code_8'],
      device_fault_code: 13,
    })

    renderDashboard()

    await waitFor(() => {
      expect(screen.getByText(/Device faults: Motor fault, G-sensor fault, Unknown fault code 8/)).toBeInTheDocument()
    })
  })

  it('shows poller offline and device fault banners together', async () => {
    client.getDashboard.mockResolvedValue({
      ...dashboardBase,
      poller_healthy: false,
      poller_last_error: 'Tuya offline',
      device_faults: ['program_fault'],
      device_fault_code: 2,
    })

    renderDashboard()

    await waitFor(() => expect(screen.getByText('Tuya offline')).toBeInTheDocument())
    expect(screen.getByText(/Device fault: Program fault/)).toBeInTheDocument()
  })

  it('surfaces an unhealthy poller without replacing the dashboard', async () => {
    client.getDashboard.mockResolvedValue({
      ...dashboardBase,
      poller_healthy: false,
      poller_last_error: 'Tuya offline',
    })

    renderDashboard()

    await waitFor(() => expect(screen.getByText('Tuya offline')).toBeInTheDocument())
    expect(screen.getByText('Recent visits')).toBeInTheDocument()
  })

  it("shows health signals on the dashboard and cat card", async () => {
    const signal = {
      id: "cat:1:weight_1m:down",
      type: "weight_down",
      severity: "watch",
      cat_id: 1,
      cat_name: "Mochi",
      message: "Weight is down compared with 1 month ago.",
      detail: "4.700 kg now vs 5.000 kg around 1 month ago.",
      metadata: {},
    }
    client.getDashboard.mockResolvedValue({
      ...dashboardBase,
      health_signals: [signal],
      cats: [{
        cat_id: 1,
        cat_name: "Mochi",
        reference_weight_kg: 5.0,
        photo_url: null,
        visits_today: 1,
        time_in_box_today_seconds: 120,
        last_visit_at: "2026-05-17T07:30:00Z",
        last_visit_weight_kg: 4.7,
        last_visit_duration_seconds: 120,
        health_signal: signal,
      }],
    })
    client.getCats.mockResolvedValue([
      { id: 1, name: "Mochi", active: true, reference_weight_kg: 5.0, created_at: "2026-01-01T00:00:00Z" },
    ])

    renderDashboard()

    await waitFor(() => expect(screen.getByText("Health signals")).toBeInTheDocument())
    expect(screen.getByText(/Mochi:/)).toBeInTheDocument()
    expect(screen.getAllByText("Weight is down compared with 1 month ago.")).toHaveLength(2)
    expect(screen.getAllByText("4.700 kg now vs 5.000 kg around 1 month ago.")).toHaveLength(2)
  })

})
