import { useState } from 'react'
import { formatDistanceToNow } from 'date-fns'
import CatPhotoUpload from './CatPhotoUpload'
import Icon, { CatAvatarIcon } from './Icon'
import { uploadCatPhoto, deleteCatPhoto } from '../api/client'

function getCatId(cat) {
  return cat.cat_id || cat.id
}

function formatDuration(seconds) {
  if (!seconds) return '—'
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  if (m === 0) return `${s}s`
  return `${m}m ${s}s`
}

function CatAvatar({ photo, name }) {
  return photo ? <img src={photo} alt={name} /> : <CatAvatarIcon />
}

function SummaryMetric({ icon, label, value, accent = false }) {
  return (
    <div className="summary-metric">
      <span className="summary-metric__icon" aria-hidden="true">{icon}</span>
      <span className="summary-metric__label">{label}</span>
      <span className={`summary-metric__value ${accent ? 'accent' : ''}`}>{value}</span>
    </div>
  )
}

export default function CatCard({ cat, isPlaceholder = false, onAddVisit, onPhotoChange }) {
  const catId = getCatId(cat)
  const displayName = cat.cat_name || cat.name
  const [photo, setPhoto] = useState(cat.photo_url || null)
  const [showUpload, setShowUpload] = useState(false)
  const [uploading, setUploading] = useState(false)

  async function handleSavePhoto(dataUrl) {
    const catIdValue = catId
    if (dataUrl === null) {
      try {
        setUploading(true)
        const updated = await deleteCatPhoto(catIdValue)
        setPhoto(updated.photo_url ? `${updated.photo_url}?v=${Date.now()}` : null)
        onPhotoChange?.(updated)
      } finally {
        setUploading(false)
      }
    } else {
      try {
        setUploading(true)
        const updated = await uploadCatPhoto(catIdValue, dataUrl)
        setPhoto(updated.photo_url ? `${updated.photo_url}?v=${Date.now()}` : null)
        onPhotoChange?.(updated)
      } finally {
        setUploading(false)
      }
    }
    setShowUpload(false)
  }

  if (isPlaceholder) {
    return (
      <div className="card cat-card cat-card--placeholder">
        <div className="cat-card__photo cat-card__photo--placeholder">
          <CatAvatar photo={photo} name={cat.name} />
        </div>
        <div className="cat-card__body">
          <div className="cat-card__name">{cat.name}</div>
          <div className="cat-card__placeholder-text">No visits yet</div>
        </div>
        {onAddVisit && (
          <div className="cat-card__placeholder-actions">
            <button className="btn btn-secondary btn-sm" onClick={() => onAddVisit(cat)}>
              + Add visit
            </button>
          </div>
        )}
      </div>
    )
  }

  const lastVisitAgo = cat.last_visit_at
    ? formatDistanceToNow(new Date(cat.last_visit_at), { addSuffix: true })
    : null
  const weightKg = cat.last_visit_weight_kg || cat.reference_weight_kg
  const weightDeltaKg = cat.last_visit_weight_kg && cat.reference_weight_kg
    ? cat.last_visit_weight_kg - cat.reference_weight_kg
    : null
  const weightDeltaLabel = weightDeltaKg === null
    ? (cat.last_visit_weight_kg ? 'latest' : 'reference')
    : `${weightDeltaKg >= 0 ? '+' : ''}${weightDeltaKg.toFixed(2)} kg`

  return (
    <>
    <div className="card cat-card cat-summary-card">
      <div className="cat-card__topline">
        <div
          className="cat-card__photo cat-card__photo--clickable"
          onClick={() => !uploading && setShowUpload(true)}
          title="Click to change photo"
          role="button"
          tabIndex={0}
          onKeyDown={e => e.key === 'Enter' && !uploading && setShowUpload(true)}
        >
          <CatAvatar photo={photo} name={displayName} />
        </div>

        <div className="cat-card__identity">
          <div className="cat-card__name">{displayName}</div>
          <div className="cat-card__breed">{cat.breed || 'Cat profile'}</div>
        </div>

        {weightKg && (
          <div className="cat-card__weight-block">
            <div className="cat-card__weight">
              {weightKg.toFixed(3)}
              <span> kg</span>
            </div>
            <div className={`cat-card__delta ${weightDeltaKg !== null && weightDeltaKg < 0 ? 'negative' : ''}`}>
              {weightDeltaLabel}
            </div>
          </div>
        )}
      </div>

      <div className="summary-metrics">
        <SummaryMetric icon={<Icon name="visits" size={16} />} label="Visits today" value={cat.visits_today} accent={cat.visits_today > 0} />
        <SummaryMetric icon={<Icon name="timer" size={16} />} label="Time in box" value={formatDuration(cat.time_in_box_today_seconds)} />
        <SummaryMetric icon={<Icon name="clock" size={16} />} label="Last visit" value={lastVisitAgo || '—'} />
        <SummaryMetric icon={<Icon name="activity" size={16} />} label="Duration" value={formatDuration(cat.last_visit_duration_seconds)} />
      </div>

      {onAddVisit && (
        <div className="cat-card__actions">
          <button className="btn btn-primary btn-sm" onClick={() => onAddVisit(cat)}>
            + Add visit
          </button>
        </div>
      )}
    </div>

    {showUpload && (
      <CatPhotoUpload catName={displayName} onClose={() => setShowUpload(false)} onSave={handleSavePhoto} />
    )}
    </>
  )
}
