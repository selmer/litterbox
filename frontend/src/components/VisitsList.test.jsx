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
    weight_confidence: 'ignored',
  },
]

describe('VisitsList', () => {
  it('renders stable desktop columns and mobile visit cards', () => {
    render(<VisitsList visits={visits} cats={cats} />)

    const headers = screen.getAllByRole('columnheader').map(header => header.textContent.trim())
    expect(headers).toEqual(['ID', 'Cat', 'Started', 'Duration', 'Weight', 'Source'])
    expect(screen.getAllByText('#1')).toHaveLength(2)
    expect(screen.getAllByText('#2')).toHaveLength(2)

    const mobileList = screen.getByLabelText('Visit list')
    expect(within(mobileList).getByText('Mochi')).toBeInTheDocument()
    expect(within(mobileList).getByText('Unknown cat')).toBeInTheDocument()
    expect(within(mobileList).getByText('#1')).toBeInTheDocument()
    expect(within(mobileList).getByText('#2')).toBeInTheDocument()
    expect(within(mobileList).getByText('unidentified')).toBeInTheDocument()
    expect(screen.getAllByText('ignored').length).toBeGreaterThan(0)
  })

  it('can hide visit IDs for compact dashboard usage', () => {
    render(<VisitsList visits={visits} cats={cats} showIds={false} />)

    expect(screen.queryByRole('columnheader', { name: 'ID' })).toBeNull()
    expect(screen.queryByText('#1')).toBeNull()
    expect(screen.queryByText('#2')).toBeNull()
    expect(screen.getByRole('columnheader', { name: 'Source' })).toBeInTheDocument()
    expect(screen.getByLabelText('Visit list')).toBeInTheDocument()
  })

  it('can show diagnostics links for the full visits screen', () => {
    render(<VisitsList visits={visits} cats={cats} showDiagnosticsLinks />)

    expect(screen.getByRole('columnheader', { name: 'Actions' })).toBeInTheDocument()
    expect(screen.getAllByRole('link', { name: 'diagnostics' })[0]).toHaveAttribute('href', '/diagnostics?visit=1')
  })

  it('keeps row actions in an edit menu without inline delete confirmation', () => {
    const onEdit = vi.fn()
    const onDelete = vi.fn()
    render(<VisitsList visits={[visits[0]]} cats={cats} onEdit={onEdit} onDelete={onDelete} />)

    expect(screen.getAllByText('edit')).toHaveLength(2)
    expect(screen.getAllByRole('button', { name: 'Edit visit' })).toHaveLength(2)
    expect(screen.queryByRole('button', { name: 'Reassign' })).toBeNull()
    expect(screen.getAllByRole('button', { name: 'Delete' })).toHaveLength(2)
    expect(screen.queryByText('Yes, delete')).toBeNull()
  })

  it('uses a filter-aware empty message', () => {
    render(<VisitsList visits={[]} cats={cats} emptyMessage="No visits match this filter" />)
    expect(screen.getByText('No visits match this filter')).toBeInTheDocument()
  })
})
