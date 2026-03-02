import { useRef, useState } from 'react'
import { formatDistanceToNow } from 'date-fns'
import { uploadCatPhoto } from '../api/client'

const PLACEHOLDER_EMOJI = '🐱'

function formatDuration(seconds) {
  if (!seconds) return '—'
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  if (m === 0) return `${s}s`
  return `${m}m ${s}s`
}

export default function CatCard({ cat, isPlaceholder = false, onPhotoUploaded }) {
  const fileInputRef = useRef(null)
  const [uploading, setUploading] = useState(false)

  const catId = cat.cat_id || cat.id

  async function handleFileChange(e) {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    try {
      await uploadCatPhoto(catId, file)
      onPhotoUploaded?.()
    } catch (err) {
      console.error('Failed to upload photo', err)
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

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

  const canUpload = !!onPhotoUploaded

  return (
    <div className="card cat-card">
      <div
        className={`cat-card__photo${canUpload ? ' cat-card__photo--uploadable' : ''}`}
        onClick={() => canUpload && fileInputRef.current?.click()}
        title={canUpload ? 'Click to upload a photo' : undefined}
      >
        {uploading ? (
          <span className="cat-card__photo-uploading">⏳</span>
        ) : cat.photo_url ? (
          <img src={cat.photo_url} alt={cat.name} />
        ) : (
          <span>{PLACEHOLDER_EMOJI}</span>
        )}
        {canUpload && !uploading && (
          <div className="cat-card__photo-overlay">
            <span>📷</span>
          </div>
        )}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          style={{ display: 'none' }}
          onChange={handleFileChange}
        />
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
  )
}
