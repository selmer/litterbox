import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import Visits from './Visits'
import { ToastProvider } from '../components/Toast'
import * as client from '../api/client'

vi.mock('../api/client')
vi.mock('../components/VisitsList', () => ({
  default: ({ visits, onDelete, onReassign }) => (
    <ul>
      {visits.map(v => (
        <li key={v.id}>
          Visit {v.id}
          <button onClick={() => onDelete(v)}>Delete {v.id}</button>
          <button onClick={() => onReassign(v)}>Reassign {v.id}</button>
        </li>
      ))}
    </ul>
  ),
}))

const PAGE_SIZE = 50

const mockVisits = [
  { id: 1, cat_id: 10, started_at: '2024-01-01T10:00:00Z', weight_kg: 4.2 },
  { id: 2, cat_id: null, started_at: '2024-01-01T11:00:00Z', weight_kg: null },
]
const mockCats = [{ id: 10, name: 'Mochi', reference_weight_kg: 4.1 }]

// Returns PAGE_SIZE + 1 visits to simulate there being a next page
function makeLargePage() {
  return Array.from({ length: PAGE_SIZE + 1 }, (_, i) => ({
    id: i + 1,
    cat_id: 10,
    started_at: '2024-01-01T10:00:00Z',
    weight_kg: 4.2,
  }))
}

function renderVisits() {
  return render(
    <ToastProvider>
      <Visits />
    </ToastProvider>
  )
}

describe('Visits page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
    client.getVisits.mockResolvedValue(mockVisits)
    client.getCats.mockResolvedValue(mockCats)
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('loads and displays visits', async () => {
    renderVisits()
    await waitFor(() => expect(screen.getByText('Visit 1')).toBeInTheDocument())
    expect(screen.getByText('Visit 2')).toBeInTheDocument()
  })

  describe('handleDelete', () => {
    it('removes the visit from the list on success', async () => {
      client.deleteVisit.mockResolvedValue()
      renderVisits()
      await waitFor(() => screen.getByText('Delete 1'))

      fireEvent.click(screen.getByText('Delete 1'))
      await waitFor(() => expect(screen.queryByText('Visit 1')).toBeNull())
      expect(screen.getByText('Visit 2')).toBeInTheDocument()
    })

    it('shows an error toast when delete fails', async () => {
      client.deleteVisit.mockRejectedValue(new Error('Network error'))
      renderVisits()
      await waitFor(() => screen.getByText('Delete 1'))

      fireEvent.click(screen.getByText('Delete 1'))
      await waitFor(() =>
        expect(screen.getByRole('alert')).toHaveTextContent('Failed to delete visit')
      )
      // Visit should still be in the list
      expect(screen.getByText('Visit 1')).toBeInTheDocument()
    })
  })

  describe('confirmReassign', () => {
    it('updates the visit in the list on successful reassign', async () => {
      const updatedVisit = { ...mockVisits[1], cat_id: 10, id: 2 }
      client.updateVisit.mockResolvedValue(updatedVisit)
      renderVisits()
      await waitFor(() => screen.getByText('Reassign 2'))

      fireEvent.click(screen.getByText('Reassign 2'))
      // Reassign modal should appear with cat button
      await waitFor(() => screen.getByText('🐱 Mochi'))
      fireEvent.click(screen.getByText('🐱 Mochi'))

      await waitFor(() =>
        expect(client.updateVisit).toHaveBeenCalledWith(2, { cat_id: 10 })
      )
    })

    it('shows an error toast when reassign fails', async () => {
      client.updateVisit.mockRejectedValue(new Error('Network error'))
      renderVisits()
      await waitFor(() => screen.getByText('Reassign 2'))

      fireEvent.click(screen.getByText('Reassign 2'))
      await waitFor(() => screen.getByText('🐱 Mochi'))
      fireEvent.click(screen.getByText('🐱 Mochi'))

      await waitFor(() =>
        expect(screen.getByRole('alert')).toHaveTextContent('Failed to reassign visit')
      )
    })

    it('closes the reassign modal even when reassign fails', async () => {
      client.updateVisit.mockRejectedValue(new Error('Network error'))
      renderVisits()
      await waitFor(() => screen.getByText('Reassign 2'))

      fireEvent.click(screen.getByText('Reassign 2'))
      await waitFor(() => screen.getByText('Reassign visit'))
      fireEvent.click(screen.getByText('🐱 Mochi'))

      await waitFor(() =>
        expect(screen.queryByText('Reassign visit')).toBeNull()
      )
    })
  })

  describe('pagination', () => {
    it('hides pagination controls when there is only one page', async () => {
      renderVisits()
      await waitFor(() => screen.getByText('Visit 1'))

      expect(screen.queryByText('← Previous')).toBeNull()
      expect(screen.queryByText('Next →')).toBeNull()
    })

    it('shows Next button when there are more pages', async () => {
      client.getVisits.mockResolvedValue(makeLargePage())
      renderVisits()

      await waitFor(() => screen.getByText('Next →'))
      expect(screen.queryByText('← Previous')).toBeInTheDocument()
    })

    it('Next button is disabled on the last page', async () => {
      renderVisits()
      await waitFor(() => screen.getByText('Visit 1'))
      // no next page — hasMore is false with only 2 visits
      expect(screen.queryByText('Next →')).toBeNull()
    })

    it('advances to the next page when Next is clicked', async () => {
      const page2Visits = [{ id: 99, cat_id: 10, started_at: '2024-01-02T10:00:00Z', weight_kg: 4.3 }]
      client.getVisits
        .mockResolvedValueOnce(makeLargePage())
        .mockResolvedValueOnce(page2Visits)
      renderVisits()

      await waitFor(() => screen.getByText('Next →'))
      fireEvent.click(screen.getByText('Next →'))

      await waitFor(() => expect(client.getVisits).toHaveBeenCalledWith(
        expect.objectContaining({ offset: PAGE_SIZE })
      ))
    })

    it('goes back to the previous page when Previous is clicked', async () => {
      const page2Visits = [{ id: 99, cat_id: 10, started_at: '2024-01-02T10:00:00Z', weight_kg: 4.3 }]
      client.getVisits
        .mockResolvedValueOnce(makeLargePage())
        .mockResolvedValueOnce(page2Visits)
        .mockResolvedValueOnce(mockVisits)
      renderVisits()

      await waitFor(() => screen.getByText('Next →'))
      fireEvent.click(screen.getByText('Next →'))
      await waitFor(() => screen.getByText('Visit 99'))

      fireEvent.click(screen.getByText('← Previous'))
      await waitFor(() => expect(client.getVisits).toHaveBeenLastCalledWith(
        expect.objectContaining({ offset: 0 })
      ))
    })

    it('resets to page 1 when the cat filter changes', async () => {
      client.getVisits
        .mockResolvedValueOnce(makeLargePage())  // initial load
        .mockResolvedValueOnce(makeLargePage())  // after next
        .mockResolvedValueOnce(mockVisits)       // after filter change
      renderVisits()

      await waitFor(() => screen.getByText('Next →'))
      fireEvent.click(screen.getByText('Next →'))
      await waitFor(() => screen.getByText('Page 2'))

      fireEvent.click(screen.getByText('Mochi'))
      await waitFor(() => expect(client.getVisits).toHaveBeenCalledWith(
        expect.objectContaining({ offset: 0, catId: 10 })
      ))
    })

    it('passes unidentified=true when Unidentified filter is selected', async () => {
      renderVisits()
      await waitFor(() => screen.getByText('Visit 1'))

      fireEvent.click(screen.getByText('Unidentified'))
      await waitFor(() => expect(client.getVisits).toHaveBeenCalledWith(
        expect.objectContaining({ unidentified: true, offset: 0 })
      ))
    })

    it('passes catId when a cat filter is selected', async () => {
      renderVisits()
      await waitFor(() => screen.getByText('Visit 1'))

      fireEvent.click(screen.getByText('Mochi'))
      await waitFor(() => expect(client.getVisits).toHaveBeenCalledWith(
        expect.objectContaining({ catId: 10, offset: 0 })
      ))
    })
  })
})
