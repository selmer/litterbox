import { useState, useEffect } from 'react'
import { formatDistanceToNow } from 'date-fns'
import CatPhotoUpload from './CatPhotoUpload'

const PLACEHOLDER_EMOJI = '🐱'

function getCatId(cat) {
  return cat.cat_id || cat.id
}

function getStoredPhoto(catId) {
  if (!catId) return null
  return localStorage.getItem(`cat_photo_${catId}`) || null
}

function storePhoto(catId, dataUrl) {
  if (!catId) return
  if (dataUrl === null) {
    localStorage.removeItem(`cat_photo_${catId}`)
  } else {
    localStorage.setItem(`cat_photo_${catId}`, dataUrl)
  }
}

function formatDuration(seconds) {
  if (!seconds) return '—'
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  if (m === 0) return `${s}s`
  return `${m}m ${s}s`
}

export default function CatCard({ cat, isPlaceholder = false, onAddVisit }) {
  const catId = getCatId(cat)
  const [photo, setPhoto] = useState(() => getStoredPhoto(catId))
  const [showUpload, setShowUpload] = useState(false)

  useEffect(() => {
    setPhoto(getStoredPhoto(catId))
  }, [catId])

  function handleSavePhoto(dataUrl) {
    storePhoto(catId, dataUrl)
    setPhoto(dataUrl)
    setShowUpload(false)
  }

  if (isPlaceholder) {
    return (
      <div className="card cat-card cat-card--placeholder">
        <div className="cat-card__photo cat-card__photo--placeholder">
          {photo ? <img src={photo} alt={cat.name} /> : <span>{PLACEHOLDER_EMOJI}</span>}
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
    <>
    <div className="card cat-card" style={{ flexDirection: 'column' }}>
      <div style={{ display: 'flex', gap: 'var(--space-4)', alignItems: 'flex-start', width: '100%' }}>
        <div
          className="cat-card__photo cat-card__photo--clickable"
          onClick={() => setShowUpload(true)}
          title="Click to change photo"
          role="button"
          tabIndex={0}
          onKeyDown={e => e.key === 'Enter' && setShowUpload(true)}
        >
          {photo ? <img src={photo} alt={cat.cat_name || cat.name} /> : <span>{PLACEHOLDER_EMOJI}</span>}
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

    {showUpload && (
      <CatPhotoUpload
        catName={cat.cat_name || cat.name}
        onClose={() => setShowUpload(false)}
        onSave={handleSavePhoto}
      />
    )}
    </>
  )
}
