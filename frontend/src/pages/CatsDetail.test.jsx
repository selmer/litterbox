import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import CatDetail from './CatDetail'
import { ToastProvider } from '../components/Toast'
import * as client from '../api/client'

vi.mock('../api/client')

const mockCat = {
  id: 1,
  name: 'Plurk',
  active: true,
  reference_weight_kg: 3.86,
  birth_date: '2020-05-18',
  photo_url: null,
  created_at: '2024-01-01T00:00:00Z',
}

const mockCats = [
  mockCat,
  {
    id: 2,
    name: 'Miez',
    active: true,
    reference_weight_kg: 4.2,
    birth_date: null,
    photo_url: null,
    created_at: '2024-01-02T00:00:00Z',
  },
]

const mockEvents = [
  {
    id: 10,
    cat_id: 1,
    cat_ids: [1],
    cat_names: ['Plurk'],
    event_type: 'vet_visit',
    occurred_at: '2026-05-18',
    title: 'Annual checkup',
    notes: 'All good',
    cost_amount: '45.50',
    cost_currency: 'EUR',
    created_at: '2026-05-18T14:31:00Z',
    updated_at: '2026-05-18T14:31:00Z',
  },
]

function renderCatDetail() {
  return render(
    <MemoryRouter initialEntries={['/cats/1']}>
      <ToastProvider>
        <Routes>
          <Route path="/cats/:catId" element={<CatDetail />} />
        </Routes>
      </ToastProvider>
    </MemoryRouter>
  )
}

describe('CatDetail page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    client.getCat.mockResolvedValue(mockCat)
    client.getCatEvents.mockResolvedValue(mockEvents)
    client.getCats.mockResolvedValue(mockCats)
  })

  it('loads cat profile and events', async () => {
    renderCatDetail()

    await waitFor(() => expect(screen.getAllByRole('heading', { name: 'Plurk' }).length).toBeGreaterThanOrEqual(1))
    expect(screen.getByText('3.860 kg')).toBeInTheDocument()
    expect(screen.getAllByText('18 May 2020').length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('Annual checkup')).toBeInTheDocument()
    expect(screen.getByText('EUR 45.50')).toBeInTheDocument()
    expect(screen.getByText('Born')).toBeInTheDocument()
  })

  it('creates an event from the form', async () => {
    const created = {
      ...mockEvents[0],
      id: 11,
      event_type: 'medication',
      title: 'Started medication',
      occurred_at: '2026-05-18',
      notes: null,
      cost_amount: '12',
      cat_ids: [1],
      cat_names: ['Plurk'],
    }
    client.createCatEvent.mockResolvedValue(created)
    renderCatDetail()
    await waitFor(() => screen.getByText('Annual checkup'))

    fireEvent.change(screen.getByLabelText('Type'), { target: { value: 'medication' } })
    fireEvent.change(screen.getByLabelText('Date'), { target: { value: '2026-05-18' } })
    await userEvent.type(screen.getByPlaceholderText('e.g. Annual checkup'), 'Started medication')
    await userEvent.type(screen.getByPlaceholderText('0.00'), '12.00')
    fireEvent.click(screen.getByRole('button', { name: 'Add event' }))

    await waitFor(() => expect(client.createCatEvent).toHaveBeenCalledWith('1', expect.objectContaining({
      event_type: 'medication',
      title: 'Started medication',
      occurred_at: '2026-05-18',
      cost_amount: '12',
      cost_currency: 'EUR',
      cat_ids: [1],
    })))
    await waitFor(() => expect(screen.getByText('Started medication')).toBeInTheDocument())
  })


  it('creates a shared event for another selected cat', async () => {
    const created = {
      ...mockEvents[0],
      id: 12,
      title: 'Shared vaccination',
      cat_ids: [1, 2],
      cat_names: ['Miez', 'Plurk'],
    }
    client.createCatEvent.mockResolvedValue(created)
    renderCatDetail()
    await waitFor(() => screen.getByText('Annual checkup'))

    fireEvent.change(screen.getByLabelText('Date'), { target: { value: '2026-05-18' } })
    await userEvent.type(screen.getByPlaceholderText('e.g. Annual checkup'), 'Shared vaccination')
    const miezCheckbox = screen.getByLabelText('Miez')
    await userEvent.click(miezCheckbox)
    await waitFor(() => expect(miezCheckbox).toBeChecked())
    await userEvent.click(screen.getByRole('button', { name: 'Add event' }))

    await waitFor(() => expect(client.createCatEvent).toHaveBeenCalledWith('1', expect.objectContaining({
      title: 'Shared vaccination',
      cat_ids: [1, 2],
    })))
  })

  it('shows shared context for events linked to another cat', async () => {
    client.getCatEvents.mockResolvedValue([
      {
        ...mockEvents[0],
        cat_ids: [1, 2],
        cat_names: ['Miez', 'Plurk'],
      },
    ])

    renderCatDetail()

    await waitFor(() => expect(screen.getByText('Shared with Miez')).toBeInTheDocument())
  })

  it('deletes an event', async () => {
    client.deleteCatEvent.mockResolvedValue()
    renderCatDetail()
    await waitFor(() => screen.getByText('Annual checkup'))

    fireEvent.click(screen.getByRole('button', { name: 'Delete' }))

    await waitFor(() => expect(client.deleteCatEvent).toHaveBeenCalledWith('1', 10))
    await waitFor(() => expect(screen.queryByText('Annual checkup')).toBeNull())
  })

  it('shows an empty state when there are no events or birthday', async () => {
    client.getCat.mockResolvedValue({ ...mockCat, birth_date: null })
    client.getCatEvents.mockResolvedValue([])

    renderCatDetail()

    await waitFor(() => expect(screen.getByText('No lifecycle events yet')).toBeInTheDocument())
  })

  it('shows an error state when loading fails', async () => {
    client.getCat.mockRejectedValue(new Error('Nope'))

    renderCatDetail()

    await waitFor(() => expect(screen.getByText('Failed to load cat details')).toBeInTheDocument())
  })
})
