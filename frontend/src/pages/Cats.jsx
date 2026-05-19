import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { getCats, createCat, updateCat } from '../api/client'
import Icon, { CatAvatarIcon } from '../components/Icon'
import { useToast } from '../components/ToastContext'
import { useLanguage } from '../i18n/useLanguage'
import { EmptyState, PageHeader, StatusBadge } from '../components/ui'

function CatAvatar({ cat }) {
  return (
    <div className="cat-profile__avatar">
      {cat.photo_url ? <img src={cat.photo_url} alt={cat.name} /> : <CatAvatarIcon />}
    </div>
  )
}

function ReferenceWeight({ weight, t }) {
  if (weight == null) return <StatusBadge tone="muted">{t('common.notSet')}</StatusBadge>
  return <strong>{weight.toFixed(3)} kg</strong>
}


function formatBirthInfo(birthDate, locale, t) {
  if (!birthDate) return <StatusBadge tone="muted">{t('common.notSet')}</StatusBadge>
  const date = new Date(`${birthDate}T00:00:00`)
  if (Number.isNaN(date.getTime())) return <StatusBadge tone="muted">{t('common.notSet')}</StatusBadge>
  const now = new Date()
  let years = now.getFullYear() - date.getFullYear()
  const hadBirthdayThisYear =
    now.getMonth() > date.getMonth() ||
    (now.getMonth() === date.getMonth() && now.getDate() >= date.getDate())
  if (!hadBirthdayThisYear) years -= 1
  const label = date.toLocaleDateString(locale, { day: '2-digit', month: 'short', year: 'numeric' })
  return <strong>{years >= 0 ? `${t('common.yearsShort', { count: years })} · ${label}` : label}</strong>
}

function CatForm({ initial, onSave, onCancel, t }) {
  const [name, setName] = useState(initial?.name || '')
  const [weight, setWeight] = useState(initial?.reference_weight_kg ?? '')
  const [birthDate, setBirthDate] = useState(initial?.birth_date || '')
  const [saving, setSaving] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setSaving(true)
    try {
      await onSave({
        name,
        reference_weight_kg: weight ? parseFloat(weight) : null,
        birth_date: birthDate || null,
      })
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="cat-form cat-profile-form">
      <div className="cat-profile-form__grid">
        <div className="form-field">
          <label className="form-label">{t('field.name')}</label>
          <input
            className="form-input"
            value={name}
            onChange={e => setName(e.target.value)}
            placeholder="e.g. Griezeltje"
            required
          />
        </div>
        <div className="form-field">
          <label className="form-label">{t('field.referenceWeightKg')}</label>
          <input
            className="form-input"
            type="number"
            step="0.001"
            min="0"
            max="20"
            value={weight}
            onChange={e => setWeight(e.target.value)}
            placeholder="e.g. 4.200"
          />
        </div>
        <div className="form-field">
          <label className="form-label">{t('field.birthday')}</label>
          <input
            className="form-input"
            type="date"
            value={birthDate}
            onChange={e => setBirthDate(e.target.value)}
          />
        </div>
      </div>
      <p className="form-hint">
        {t('cats.formHint')}
      </p>
      <div className="action-row">
        <button type="submit" className="btn btn-primary" disabled={saving}>
          {saving ? t('common.saving') : (initial ? t('common.saveChanges') : t('common.addCat'))}
        </button>
        {onCancel && (
          <button type="button" className="btn btn-secondary" onClick={onCancel}>
            {t('common.cancel')}
          </button>
        )}
      </div>
    </form>
  )
}

function CatProfileRow({ cat, editing, onEdit, onCancelEdit, onSave, onToggleActive, locale, t }) {
  if (editing) {
    return (
      <section className={`card cat-profile-card cat-profile-card--editing ${!cat.active ? 'cat-profile-card--inactive' : ''}`}>
        <div className="cat-profile-card__edit-header">
          <CatAvatar cat={cat} />
          <div>
            <div className="card-label">{t('cats.editing', { name: cat.name })}</div>
            <p className="text-muted text-small">{t('cats.editDescription')}</p>
          </div>
        </div>
        <CatForm initial={cat} onSave={onSave} onCancel={onCancelEdit} t={t} />
      </section>
    )
  }

  return (
    <section className={`card cat-profile-card ${!cat.active ? 'cat-profile-card--inactive' : ''}`}>
      <div className="cat-profile">
        <CatAvatar cat={cat} />
        <div className="cat-profile__main">
          <div className="cat-profile__title-row">
            <h3>
              <Link to={`/cats/${cat.id}`} className="cat-profile__name-link">{cat.name}</Link>
            </h3>
            {cat.active ? <StatusBadge tone="green">{t('status.active')}</StatusBadge> : <StatusBadge tone="muted">{t('status.inactive')}</StatusBadge>}
          </div>
          <div className="cat-profile__meta-grid">
            <div className="cat-profile__meta-item">
              <span>{t('field.referenceWeight')}</span>
              <ReferenceWeight weight={cat.reference_weight_kg} t={t} />
            </div>
            <div className="cat-profile__meta-item">
              <span>{t('field.birthday')}</span>
              {formatBirthInfo(cat.birth_date, locale, t)}
            </div>
            <div className="cat-profile__meta-item">
              <span>{t('field.added')}</span>
              <strong>{new Date(cat.created_at).toLocaleDateString(locale)}</strong>
            </div>
          </div>
        </div>
        <div className="cat-profile__actions">
          <Link className="btn btn-secondary btn-sm" to={`/cats/${cat.id}`}>
            {t('common.view')}
          </Link>
          <button className="btn btn-secondary btn-sm" onClick={onEdit}>
            {t('common.editDisplay')}
          </button>
          <details className="cat-profile__more">
            <summary className="btn btn-secondary btn-sm cat-profile__more-trigger">
              {t('common.more')}
            </summary>
            <div className="cat-profile__more-menu">
              <button className="cat-profile__more-item" onClick={onToggleActive}>
                {cat.active ? t('common.deactivate') : t('common.reactivate')}
              </button>
            </div>
          </details>
        </div>
      </div>
    </section>
  )
}

export default function Cats() {
  const [cats, setCats] = useState([])
  const [loading, setLoading] = useState(true)
  const [adding, setAdding] = useState(false)
  const [editing, setEditing] = useState(null)
  const toast = useToast()
  const { locale, t } = useLanguage()

  useEffect(() => {
    async function fetch() {
      setLoading(true)
      try {
        const data = await getCats(true)
        setCats(data)
      } finally {
        setLoading(false)
      }
    }
    fetch()
  }, [])

  async function handleCreate(data) {
    try {
      const cat = await createCat(data)
      setCats(prev => [...prev, cat])
      setAdding(false)
      toast(t('cats.toast.added', { name: cat.name }), 'success')
    } catch (e) {
      console.error('Failed to create cat', e)
      toast(t('cats.error.add'))
    }
  }

  async function handleUpdate(id, data) {
    try {
      const cat = await updateCat(id, data)
      setCats(prev => prev.map(c => c.id === id ? cat : c))
      setEditing(null)
      toast(t('cats.toast.changesSaved'), 'success')
    } catch (e) {
      console.error('Failed to update cat', e)
      toast(t('cats.error.save'))
    }
  }

  async function handleToggleActive(cat) {
    try {
      const updated = await updateCat(cat.id, { active: !cat.active })
      setCats(prev => prev.map(c => c.id === cat.id ? updated : c))
    } catch (e) {
      console.error('Failed to update cat', e)
      toast(t('cats.error.toggle', { action: cat.active ? t('common.deactivate').toLowerCase() : t('common.reactivate').toLowerCase() }))
    }
  }

  if (loading) return <div className="loading">{t('state.loading')}</div>

  return (
    <div>
      <PageHeader
        title={t('cats.title')}
        subtitle={t('cats.subtitle')}
        actions={!adding && (
          <button className="btn btn-primary" onClick={() => setAdding(true)}>
            {t('common.addCat')}
          </button>
        )}
      />

      {adding && (
        <section className="card cat-profile-card cat-profile-card--new mb-6">
          <div className="cat-profile-card__edit-header">
            <div className="cat-profile__avatar cat-profile__avatar--new">
              <Icon name="cat" size={28} />
            </div>
            <div>
              <div className="card-label">{t('cats.newCat')}</div>
              <p className="text-muted text-small">{t('cats.newCatDescription')}</p>
            </div>
          </div>
          <CatForm onSave={handleCreate} onCancel={() => setAdding(false)} t={t} />
        </section>
      )}

      <div className="cat-profile-list">
        {cats.map(cat => (
          <CatProfileRow
            key={cat.id}
            cat={cat}
            editing={editing === cat.id}
            onEdit={() => setEditing(cat.id)}
            onCancelEdit={() => setEditing(null)}
            onSave={(data) => handleUpdate(cat.id, data)}
            onToggleActive={() => handleToggleActive(cat)}
            locale={locale}
            t={t}
          />
        ))}

        {cats.length === 0 && !adding && (
          <div className="card">
            <EmptyState icon={<Icon name="cat" />} message={t('cats.noCats')}>
              <button className="btn btn-primary" onClick={() => setAdding(true)}>
                {t('common.addCat')}
              </button>
            </EmptyState>
          </div>
        )}
      </div>
    </div>
  )
}
