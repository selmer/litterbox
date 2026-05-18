import { format } from 'date-fns'
import Icon from './Icon'
import { EmptyState, StatusBadge } from './ui'

function formatDuration(seconds) {
  if (!seconds) return '-'
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

function getCatName(visit, catMap) {
  if (!visit.cat_id) return 'Unknown cat'
  return catMap[visit.cat_id]?.name || `Cat #${visit.cat_id}`
}

function VisitActions({ visit, onReassign, onDelete }) {
  if (!onReassign && !onDelete) return null

  return (
    <div className="visit-actions">
      {onReassign && (
        <button className="btn btn-secondary btn-sm" onClick={() => onReassign(visit)}>
          reassign
        </button>
      )}
      {onDelete && (
        <button className="btn btn-secondary btn-sm text-danger" onClick={() => onDelete(visit)}>
          delete
        </button>
      )}
    </div>
  )
}

function VisitMobileCard({ visit, catMap, onReassign, onDelete, showId = true }) {
  const catName = getCatName(visit, catMap)

  return (
    <article className="visit-card">
      <div className="visit-card__header">
        <div className="visit-card__cat">
          <span className={`visit-card__marker ${visit.cat_id ? '' : 'is-unidentified'}`} />
          <span>{catName}</span>
        </div>
        <div className="visit-card__meta">
          {showId && <span className="visit-id text-mono">#{visit.id}</span>}
          <IdentificationBadge identifiedBy={visit.identified_by} catId={visit.cat_id} />
        </div>
      </div>
      <dl className="visit-card__details">
        <div>
          <dt>Started</dt>
          <dd>{format(new Date(visit.started_at), 'dd MMM, HH:mm')}</dd>
        </div>
        <div>
          <dt>Duration</dt>
          <dd>{formatDuration(visit.duration_seconds)}</dd>
        </div>
        <div>
          <dt>Weight</dt>
          <dd>{visit.weight_kg ? `${visit.weight_kg.toFixed(3)} kg` : '-'}</dd>
        </div>
      </dl>
      <VisitActions visit={visit} onReassign={onReassign} onDelete={onDelete} />
    </article>
  )
}

export default function VisitsList({ visits, cats = [], onReassign, onDelete, emptyMessage = 'No visits recorded yet', showIds = true }) {
  const catMap = Object.fromEntries(cats.map(c => [c.id, c]))

  if (!visits?.length) {
    return <EmptyState icon={<Icon name="cat" />} message={emptyMessage} compact />
  }

  return (
    <>
      <div className="card card--flush visits-table-card">
        <table className="table visits-table">
          <colgroup>
            {showIds && <col className="visits-table__id-col" />}
            <col className="visits-table__cat-col" />
            <col className="visits-table__started-col" />
            <col className="visits-table__duration-col" />
            <col className="visits-table__weight-col" />
            <col className="visits-table__source-col" />
            {(onReassign || onDelete) && <col className="visits-table__actions-col" />}
          </colgroup>
          <thead>
            <tr>
              {showIds && <th>ID</th>}
              <th>Cat</th>
              <th>Started</th>
              <th>Duration</th>
              <th>Weight</th>
              <th>Source</th>
              {(onReassign || onDelete) && <th>Actions</th>}
            </tr>
          </thead>
          <tbody>
            {visits.map(visit => (
              <tr key={visit.id} className={`visit-row ${visit.cat_id ? '' : 'visit-row--unidentified'}`}>
                {showIds && <td className="visit-id text-mono table-small">#{visit.id}</td>}
                <td className="visit-cat text-primary">
                  {getCatName(visit, catMap)}
                </td>
                <td className="text-mono table-small">
                  {format(new Date(visit.started_at), 'dd MMM, HH:mm')}
                </td>
                <td>{formatDuration(visit.duration_seconds)}</td>
                <td className="text-primary">
                  {visit.weight_kg ? `${visit.weight_kg.toFixed(3)} kg` : '-'}
                </td>
                <td>
                  <IdentificationBadge identifiedBy={visit.identified_by} catId={visit.cat_id} />
                </td>
                {(onReassign || onDelete) && (
                  <td>
                    <VisitActions visit={visit} onReassign={onReassign} onDelete={onDelete} />
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="visit-card-list" aria-label="Visit list">
        {visits.map(visit => (
          <VisitMobileCard
            key={visit.id}
            visit={visit}
            catMap={catMap}
            onReassign={onReassign}
            onDelete={onDelete}
            showId={showIds}
          />
        ))}
      </div>
    </>
  )
}
