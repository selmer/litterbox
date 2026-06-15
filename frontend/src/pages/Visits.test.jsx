import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import Visits from './Visits'
import { ToastProvider } from '../components/Toast'
import * as client from '../api/client'

vi.mock('../api/client')
vi.mock('../components/VisitsList', () => ({
  default: ({ visits, onDelete, onEdit }) => (
    <ul>
      {visits.map(v => (
        <li key={v.id}>
          Visit {v.id}
          <button onClick={() => onEdit(v)}>Edit {v.id}</button>
          <button onClick={() => onDelete(v)}>Delete {v.id}</button>
        </li>
      ))}
    </ul>
  ),
}))

const PAGE_SIZE = 50

const mockVisits = [
  { id: 1, cat_id: 10, started_at: '2024-01-01T10:00:00Z', duration_seconds: 125, weight_kg: 4.2, weight_confidence: 'normal' },
  { id: 2, cat_id: null, started_at: '2024-01-01T11:00:00Z', duration_seconds: null, weight_kg: null, weight_confidence: 'normal' },
]
const mockCats = [{ id: 10, name: 'Mochi', reference_weight_kg: 4.1 }]
const mockSummaries = [
  {
    bucket: 'day',
    bucket_start: '2024-01-01T00:00:00+01:00',
    bucket_end: '2024-01-02T00:00:00+01:00',
    visit_count: 2,
    identified_visit_count: 1,
    unidentified_visit_count: 1,
    average_visits_per_day: 2,
    average_duration_seconds: 125,
    latest_visit_at: '2024-01-01T11:00:00Z',
    cats: [
      { cat_id: 10, cat_name: 'Mochi', visit_count: 1, average_duration_seconds: 125, average_weight_kg: 4.2, latest_visit_at: '2024-01-01T10:00:00Z' },
      { cat_id: null, cat_name: null, visit_count: 1, average_duration_seconds: null, average_weight_kg: null, latest_visit_at: '2024-01-01T11:00:00Z' },
    ],
  },
]

function makeLargePage() {
  return Array.from({ length: PAGE_SIZE + 1 }, (_, i) => ({
    id: i + 1,
    cat_id: 10,
    started_at: '2024-01-01T10:00:00Z',
    weight_kg: 4.2,
  }))
}

function makeLargeSummaryPage() {
  return Array.from({ length: PAGE_SIZE + 1 }, (_, i) => {
    const start = new Date(Date.UTC(2024, 0, i + 1, 0, 0, 0))
    const end = new Date(Date.UTC(2024, 0, i + 2, 0, 0, 0))
    return {
      ...mockSummaries[0],
      bucket_start: start.toISOString(),
      bucket_end: end.toISOString(),
    }
  })
}

function renderVisits() {
  return render(
    <ToastProvider>
      <Visits />
    </ToastProvider>
  )
}

async function switchToDetails() {
  fireEvent.click(await screen.findByRole('button', { name: 'Details' }))
  await waitFor(() => expect(client.getVisits).toHaveBeenCalled())
}

describe('Visits page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers({ shouldAdvanceTime: true })
    client.getVisitSummary.mockResolvedValue(mockSummaries)
    client.getVisits.mockResolvedValue(mockVisits)
    client.getCats.mockResolvedValue(mockCats)
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('loads daily summaries by default', async () => {
    renderVisits()

    await waitFor(() => expect(client.getVisitSummary).toHaveBeenCalledWith(
      expect.objectContaining({ bucket: 'day', offset: 0 })
    ))
    expect((await screen.findAllByText('Mochi: 1')).length).toBeGreaterThan(0)
    expect(screen.getAllByText('1 unidentified').length).toBeGreaterThan(0)
    expect(client.getVisits).not.toHaveBeenCalled()
  })

  it('switches summary buckets', async () => {
    renderVisits()
    fireEvent.click(await screen.findByRole('button', { name: 'Per week' }))

    await waitFor(() => expect(client.getVisitSummary).toHaveBeenLastCalledWith(
      expect.objectContaining({ bucket: 'week', offset: 0 })
    ))
  })

  it('opens summary details as a bounded details query', async () => {
    renderVisits()
    fireEvent.click((await screen.findAllByRole('button', { name: 'View details' }))[0])

    await waitFor(() => expect(client.getVisits).toHaveBeenCalledWith(
      expect.objectContaining({
        fromDate: expect.any(Date),
        toDate: expect.any(Date),
        offset: 0,
      })
    ))
  })

  it('loads and displays visits in details mode', async () => {
    renderVisits()
    await switchToDetails()
    await waitFor(() => expect(screen.getByText('Visit 1')).toBeInTheDocument())
    expect(screen.getByText('Visit 2')).toBeInTheDocument()
  })

  it('edits visit fields from the correction modal', async () => {
    const updatedVisit = { ...mockVisits[0], weight_kg: 4.25, weight_confidence: 'ignored' }
    client.updateVisit.mockResolvedValue(updatedVisit)
    renderVisits()
    await switchToDetails()
    await waitFor(() => screen.getByText('Edit 1'))

    fireEvent.click(screen.getByText('Edit 1'))
    await waitFor(() => screen.getByText('Edit visit'))
    fireEvent.change(screen.getByLabelText('Weight (kg)'), { target: { value: '4.25' } })
    fireEvent.change(screen.getByLabelText('Confidence'), { target: { value: 'ignored' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save visit' }))

    await waitFor(() => expect(client.updateVisit).toHaveBeenCalledWith(1, expect.objectContaining({
      cat_id: 10,
      duration_seconds: 125,
      weight_kg: 4.25,
      weight_confidence: 'ignored',
    })))
  })

  describe('handleDelete', () => {
    it('removes the visit from the list on success', async () => {
      client.deleteVisit.mockResolvedValue()
      renderVisits()
      await switchToDetails()
      await waitFor(() => screen.getByText('Delete 1'))

      fireEvent.click(screen.getByText('Delete 1'))
      fireEvent.click(await screen.findByRole('button', { name: 'Delete visit' }))
      await waitFor(() => expect(screen.queryByText('Visit 1')).toBeNull())
      expect(screen.getByText('Visit 2')).toBeInTheDocument()
    })

    it('shows an error toast when delete fails', async () => {
      client.deleteVisit.mockRejectedValue(new Error('Network error'))
      renderVisits()
      await switchToDetails()
      await waitFor(() => screen.getByText('Delete 1'))

      fireEvent.click(screen.getByText('Delete 1'))
      fireEvent.click(await screen.findByRole('button', { name: 'Delete visit' }))
      await waitFor(() =>
        expect(screen.getByRole('alert')).toHaveTextContent('Failed to delete visit')
      )
      expect(screen.getByText('Visit 1')).toBeInTheDocument()
    })
  })

  describe('pagination', () => {
    it('hides pagination controls when there is only one summary page', async () => {
      renderVisits()
      await waitFor(() => expect(screen.getAllByText('Mochi: 1').length).toBeGreaterThan(0))

      expect(screen.queryByText('Previous')).toBeNull()
      expect(screen.queryByText('Next')).toBeNull()
    })

    it('shows Next button when there are more summary pages', async () => {
      client.getVisitSummary.mockResolvedValue(makeLargeSummaryPage())
      renderVisits()

      await waitFor(() => screen.getByText('Next'))
      expect(screen.queryByText('Previous')).toBeInTheDocument()
    })

    it('advances to the next details page when Next is clicked', async () => {
      const page2Visits = [{ id: 99, cat_id: 10, started_at: '2024-01-02T10:00:00Z', weight_kg: 4.3 }]
      client.getVisits
        .mockResolvedValueOnce(makeLargePage())
        .mockResolvedValueOnce(page2Visits)
      renderVisits()
      await switchToDetails()

      await waitFor(() => screen.getByText('Next'))
      fireEvent.click(screen.getByText('Next'))

      await waitFor(() => expect(client.getVisits).toHaveBeenCalledWith(
        expect.objectContaining({ offset: PAGE_SIZE })
      ))
    })

    it('resets to page 1 when the cat filter changes in details mode', async () => {
      client.getVisits
        .mockResolvedValueOnce(makeLargePage())
        .mockResolvedValueOnce(makeLargePage())
        .mockResolvedValueOnce(mockVisits)
      renderVisits()
      await switchToDetails()

      await waitFor(() => screen.getByText('Next'))
      fireEvent.click(screen.getByText('Next'))
      await waitFor(() =>
        screen.getByText((_, element) =>
          element?.textContent?.startsWith('Page 2 ·')
        )
      )

      fireEvent.click(screen.getAllByText('Mochi')[0])
      await waitFor(() => expect(client.getVisits).toHaveBeenCalledWith(
        expect.objectContaining({ offset: 0, catId: 10 })
      ))
    })

    it('passes unidentified=true when Unidentified filter is selected in summary mode', async () => {
      renderVisits()
      await waitFor(() => expect(screen.getAllByText('Mochi: 1').length).toBeGreaterThan(0))

      fireEvent.click(screen.getByText('Unidentified'))
      await waitFor(() => expect(client.getVisitSummary).toHaveBeenCalledWith(
        expect.objectContaining({ unidentified: true, offset: 0 })
      ))
    })

    it('passes catId when a cat filter is selected in summary mode', async () => {
      renderVisits()
      await waitFor(() => expect(screen.getAllByText('Mochi: 1').length).toBeGreaterThan(0))

      fireEvent.click(screen.getAllByText('Mochi')[0])
      await waitFor(() => expect(client.getVisitSummary).toHaveBeenCalledWith(
        expect.objectContaining({ catId: 10, offset: 0 })
      ))
    })
  })
})
