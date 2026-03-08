import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Cats from './Cats'
import { ToastProvider } from '../components/Toast'
import * as client from '../api/client'

vi.mock('../api/client')

const mockCats = [
  { id: 1, name: 'Mochi', active: true, reference_weight_kg: 4.1, created_at: '2024-01-01T00:00:00Z' },
  { id: 2, name: 'Biscuit', active: false, reference_weight_kg: null, created_at: '2024-02-01T00:00:00Z' },
]

function renderCats() {
  return render(
    <ToastProvider>
      <Cats />
    </ToastProvider>
  )
}

describe('Cats page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers({ shouldAdvanceTime: true })
    client.getCats.mockResolvedValue(mockCats)
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('loads and displays cats', async () => {
    renderCats()
    await waitFor(() => expect(screen.getByText(/Mochi/)).toBeInTheDocument())
    expect(screen.getByText(/Biscuit/)).toBeInTheDocument()
  })

  describe('handleCreate', () => {
    it('adds a new cat to the list on success', async () => {
      const newCat = { id: 3, name: 'Whisker', active: true, reference_weight_kg: null, created_at: '2024-03-01T00:00:00Z' }
      client.createCat.mockResolvedValue(newCat)

      renderCats()
      await waitFor(() => screen.getByText('+ Add cat'))

      fireEvent.click(screen.getByText('+ Add cat'))
      await userEvent.type(screen.getByPlaceholderText('e.g. Griezeltje'), 'Whisker')
      fireEvent.click(screen.getByText('Add cat'))

      await waitFor(() => expect(screen.getByText(/Whisker/)).toBeInTheDocument())
      expect(client.createCat).toHaveBeenCalledWith({ name: 'Whisker', reference_weight_kg: null })
    })

    it('shows an error toast when create fails', async () => {
      client.createCat.mockRejectedValue(new Error('Server error'))

      renderCats()
      await waitFor(() => screen.getByText('+ Add cat'))

      fireEvent.click(screen.getByText('+ Add cat'))
      await userEvent.type(screen.getByPlaceholderText('e.g. Griezeltje'), 'Whisker')
      fireEvent.click(screen.getByText('Add cat'))

      await waitFor(() =>
        expect(screen.getByRole('alert')).toHaveTextContent('Failed to add cat')
      )
      // Form should still be visible (not closed on error)
      expect(screen.getByPlaceholderText('e.g. Griezeltje')).toBeInTheDocument()
    })
  })

  describe('handleUpdate', () => {
    it('updates the cat in the list on success', async () => {
      const updatedCat = { ...mockCats[0], name: 'Mochi Updated' }
      client.updateCat.mockResolvedValue(updatedCat)

      renderCats()
      await waitFor(() => screen.getAllByText('Edit')[0])

      fireEvent.click(screen.getAllByText('Edit')[0])
      const nameInput = screen.getByDisplayValue('Mochi')
      await userEvent.clear(nameInput)
      await userEvent.type(nameInput, 'Mochi Updated')
      fireEvent.click(screen.getByText('Save changes'))

      await waitFor(() =>
        expect(client.updateCat).toHaveBeenCalledWith(1, expect.objectContaining({ name: 'Mochi Updated' }))
      )
    })

    it('shows an error toast when update fails', async () => {
      client.updateCat.mockRejectedValue(new Error('Server error'))

      renderCats()
      await waitFor(() => screen.getAllByText('Edit')[0])

      fireEvent.click(screen.getAllByText('Edit')[0])
      fireEvent.click(screen.getByText('Save changes'))

      await waitFor(() =>
        expect(screen.getByRole('alert')).toHaveTextContent('Failed to save changes')
      )
    })
  })

  describe('handleToggleActive', () => {
    it('toggles the active state on success', async () => {
      const deactivated = { ...mockCats[0], active: false }
      client.updateCat.mockResolvedValue(deactivated)

      renderCats()
      await waitFor(() => screen.getByText('Deactivate'))

      fireEvent.click(screen.getByText('Deactivate'))

      await waitFor(() =>
        expect(client.updateCat).toHaveBeenCalledWith(1, { active: false })
      )
    })

    it('shows an error toast when deactivate fails', async () => {
      client.updateCat.mockRejectedValue(new Error('Server error'))

      renderCats()
      await waitFor(() => screen.getByText('Deactivate'))

      fireEvent.click(screen.getByText('Deactivate'))

      await waitFor(() =>
        expect(screen.getByRole('alert')).toHaveTextContent('Failed to deactivate cat')
      )
    })

    it('shows an error toast when reactivate fails', async () => {
      client.updateCat.mockRejectedValue(new Error('Server error'))

      renderCats()
      await waitFor(() => screen.getByText('Reactivate'))

      fireEvent.click(screen.getByText('Reactivate'))

      await waitFor(() =>
        expect(screen.getByRole('alert')).toHaveTextContent('Failed to reactivate cat')
      )
    })
  })
})
