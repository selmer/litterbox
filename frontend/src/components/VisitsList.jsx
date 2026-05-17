import { useState } from 'react'
import { format } from 'date-fns'
import Icon from './Icon'
import { EmptyState, StatusBadge } from './ui'

function formatDuration(seconds) {
  if (!seconds) return '—'
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  if (m === 0) return `${s}s`
  return `${m}m ${s}s`
}

function IdentificationBadge({ identifiedBy, catId }) {
  if (!catId) return <StatusBadge tone="yellow">unidentified</StatusBadge>
  if (identifiedBy === 'manual') return <StatusBadge tone="accent">manual</StatusBadge>
  return <StatusBadge tone="green">auto</StatusBadge>
}

export default function VisitsList({ visits, cats = [], onReassign, onDelete }) {
  const [pendingDelete, setPendingDelete] = useState(null)
  const catMap = Object.fromEntries(cats.map(c => [c.id, c]))

  if (!visits?.length) {
    return <EmptyState icon={<Icon name="cat" />} message="No visits recorded yet" compact />
  }

  return (
    <div className="card card--flush">
      <table className="table">
        <thead>
          <tr>
            <th>Cat</th>
            <th>Started</th>
            <th>Duration</th>
            <th>Weight</th>
            <th>ID</th>
            {onReassign && <th></th>}
            {onDelete && <th></th>}
          </tr>
        </thead>
        <tbody>
          {visits.map(visit => (
            <tr key={visit.id} className="visit-row">
              <td data-label="Cat" className="visit-cat text-primary">
                {visit.cat_id ? (catMap[visit.cat_id]?.name || `Cat #${visit.cat_id}`) : '—'}
              </td>
              <td data-label="Started" className="text-mono table-small">
                {format(new Date(visit.started_at), 'dd MMM, HH:mm')}
              </td>
              <td data-label="Duration">{formatDuration(visit.duration_seconds)}</td>
              <td data-label="Weight" className="text-primary">
                {visit.weight_kg ? `${visit.weight_kg.toFixed(3)} kg` : '—'}
              </td>
              <td data-label="ID">
                <IdentificationBadge identifiedBy={visit.identified_by} catId={visit.cat_id} />
              </td>
              {onReassign && (
                <td data-label="Actions">
                  <button className="btn btn-secondary btn-sm" onClick={() => onReassign(visit)}>
                    reassign
                  </button>
                </td>
              )}
              {onDelete && (
                <td data-label={onReassign ? '' : 'Actions'}>
                  {pendingDelete === visit.id ? (
                    <span className="action-row">
                      <button
                        className="btn btn-secondary btn-sm text-danger no-wrap"
                        onClick={() => { onDelete(visit); setPendingDelete(null) }}
                      >
                        Yes, delete
                      </button>
                      <button className="btn btn-secondary btn-sm" onClick={() => setPendingDelete(null)}>
                        Cancel
                      </button>
                    </span>
                  ) : (
                    <button
                      className="btn btn-secondary btn-sm text-danger"
                      onClick={() => setPendingDelete(visit.id)}
                    >
                      delete
                    </button>
                  )}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
