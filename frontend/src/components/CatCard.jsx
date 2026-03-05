import { formatDistanceToNow } from 'date-fns'

const PLACEHOLDER_EMOJI = '🐱'

function formatDuration(seconds) {
  if (!seconds) return '—'
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  if (m === 0) return `${s}s`
  return `${m}m ${s}s`
}

export default function CatCard({ cat, isPlaceholder = false, onAddVisit }) {
  if (isPlaceholder) {
    return (
      <div className="card cat-card cat-card--placeholder">
        <div className="cat-card__photo cat-card__photo--placeholder">
          <span>{PLACEHOLDER_EMOJI}</span>
        </div>
        <div className="cat-card__body">
          <div className="cat-card__name">{cat.name}</div>
          <div className="cat-card__placeholder-text">arriving soon</div>
        </div>
      </div>
    )
  }

  const lastVisitAgo = cat.last_visit_at
    ? formatDistanceToNow(new Date(cat.last_visit_at), { addSuffix: true })
    : null

  return (
    <div className="card cat-card" style={{ flexDirection: 'column' }}>
      <div style={{ display: 'flex', gap: 'var(--space-4)', alignItems: 'flex-start', width: '100%' }}>
        <div className="cat-card__photo">
          <span>{PLACEHOLDER_EMOJI}</span>
        </div>

        <div className="cat-card__body">
          <div className="flex-between mb-2">
            <div className="cat-card__name">{cat.cat_name || cat.name}</div>
            {(cat.last_visit_weight_kg || cat.reference_weight_kg) && (
              <div className="cat-card__weight">
                {(cat.last_visit_weight_kg || cat.reference_weight_kg).toFixed(3)}
                <span> kg</span>
                {!cat.last_visit_weight_kg && (
                  <span style={{ fontSize: 10, color: 'var(--text-muted)', marginLeft: 4 }}>ref</span>
                )}
              </div>
            )}
          </div>

          <div className="stat-row">
            <span className="stat-label">Visits today</span>
            <span className={`stat-value ${cat.visits_today > 0 ? 'accent' : ''}`}>
              {cat.visits_today}
            </span>
          </div>

          <div className="stat-row">
            <span className="stat-label">Time in box</span>
            <span className="stat-value">
              {formatDuration(cat.time_in_box_today_seconds)}
            </span>
          </div>

          <div className="stat-row">
            <span className="stat-label">Last visit</span>
            <span className="stat-value">
              {lastVisitAgo || '—'}
            </span>
          </div>

          {cat.last_visit_duration_seconds && (
            <div className="stat-row">
              <span className="stat-label">Duration</span>
              <span className="stat-value">
                {formatDuration(cat.last_visit_duration_seconds)}
              </span>
            </div>
          )}
        </div>
      </div>

      {onAddVisit && (
        <button
          className="btn btn-secondary btn-sm w-full"
          style={{ marginTop: 'var(--space-3)' }}
          onClick={() => onAddVisit(cat)}
        >
          + Add visit
        </button>
      )}
    </div>
  )
}
