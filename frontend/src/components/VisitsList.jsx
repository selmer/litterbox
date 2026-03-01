import { format } from 'date-fns'

function formatDuration(seconds) {
  if (!seconds) return '—'
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  if (m === 0) return `${s}s`
  return `${m}m ${s}s`
}

function IdentificationBadge({ identifiedBy, catId }) {
  if (!catId) return <span className="badge badge-yellow">unidentified</span>
  if (identifiedBy === 'manual') return <span className="badge badge-accent">manual</span>
  return <span className="badge badge-green">auto</span>
}

export default function VisitsList({ visits, cats = [], onReassign }) {
  const catMap = Object.fromEntries(cats.map(c => [c.id, c]))

  if (!visits?.length) {
    return (
      <div className="empty-state">
        <div className="empty-icon">🐱</div>
        <p>No visits recorded yet</p>
      </div>
    )
  }

  return (
    <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
      <table className="table">
        <thead>
          <tr>
            <th>Cat</th>
            <th>Started</th>
            <th>Duration</th>
            <th>Weight</th>
            <th>ID</th>
            {onReassign && <th></th>}
          </tr>
        </thead>
        <tbody>
          {visits.map(visit => (
            <tr key={visit.id}>
              <td style={{ color: 'var(--text-primary)', fontWeight: 500 }}>
                {visit.cat_id ? (catMap[visit.cat_id]?.name || `Cat #${visit.cat_id}`) : '—'}
              </td>
              <td className="text-mono" style={{ fontSize: 12 }}>
                {format(new Date(visit.started_at), 'dd MMM, HH:mm')}
              </td>
              <td>{formatDuration(visit.duration_seconds)}</td>
              <td style={{ color: 'var(--text-primary)' }}>
                {visit.weight_kg ? `${visit.weight_kg.toFixed(3)} kg` : '—'}
              </td>
              <td>
                <IdentificationBadge
                  identifiedBy={visit.identified_by}
                  catId={visit.cat_id}
                />
              </td>
              {onReassign && (
                <td>
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => onReassign(visit)}
                  >
                    reassign
                  </button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
