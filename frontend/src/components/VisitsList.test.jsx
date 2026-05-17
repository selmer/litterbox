import { describe, expect, it, vi } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import VisitsList from './VisitsList'

const cats = [{ id: 10, name: 'Mochi' }]
const visits = [
  {
    id: 1,
    cat_id: 10,
    started_at: '2024-01-01T10:00:00Z',
    duration_seconds: 125,
    weight_kg: 4.2,
    identified_by: 'auto',
  },
  {
    id: 2,
    cat_id: null,
    started_at: '2024-01-01T11:00:00Z',
    duration_seconds: null,
    weight_kg: null,
    identified_by: null,
  },
]

describe('VisitsList', () => {
  it('renders stable desktop columns and mobile visit cards', () => {
    render(<VisitsList visits={visits} cats={cats} />)

    expect(screen.getByRole('columnheader', { name: 'Cat' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Started' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Duration' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Weight' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'ID' })).toBeInTheDocument()

    const mobileList = screen.getByLabelText('Visit list')
    expect(within(mobileList).getByText('Mochi')).toBeInTheDocument()
    expect(within(mobileList).getByText('Unknown cat')).toBeInTheDocument()
    expect(within(mobileList).getByText('unidentified')).toBeInTheDocument()
  })

  it('groups row actions for each visit without inline delete confirmation', () => {
    const onReassign = vi.fn()
    const onDelete = vi.fn()
    render(<VisitsList visits={[visits[0]]} cats={cats} onReassign={onReassign} onDelete={onDelete} />)

    const actionButtons = screen.getAllByRole('button')
    expect(actionButtons.map(button => button.textContent.trim())).toEqual([
      'reassign',
      'delete',
      'reassign',
      'delete',
    ])
    expect(screen.queryByText('Yes, delete')).toBeNull()
  })

  it('uses a filter-aware empty message', () => {
    render(<VisitsList visits={[]} cats={cats} emptyMessage="No visits match this filter" />)
    expect(screen.getByText('No visits match this filter')).toBeInTheDocument()
  })
})
