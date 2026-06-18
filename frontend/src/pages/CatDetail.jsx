import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  createCatEvent,
  deleteCatEvent,
  getCat,
  getCatEvents,
  getCats,
  updateCatEvent,
} from '../api/client'
import Icon, { CatAvatarIcon } from '../components/Icon'
import { useToast } from '../components/ToastContext'
import { useLanguage } from '../i18n/useLanguage'
import { EmptyState, PageHeader, StatusBadge } from '../components/ui'

const EVENT_TYPES = [
  ['vet_visit', 'Vet visit'],
  ['medication', 'Medication'],
  ['diet_change', 'Diet change'],
  ['grooming', 'Grooming'],
  ['health_note', 'Health note'],
  ['milestone', 'Milestone'],
  ['other', 'Other'],
]

function toDateInputValue(value) {
  if (!value) return ''
  const date = new Date(`${value}`.slice(0, 10) + 'T00:00:00')
  if (Number.isNaN(date.getTime())) return ''
  const year = date.getFullYear()
  const month = `${date.getMonth() + 1}`.padStart(2, '0')
  const day = `${date.getDate()}`.padStart(2, '0')
  return `${year}-${month}-${day}`
}

function formatEventDate(value, locale, t) {
  return formatBirthDate(`${value}`.slice(0, 10), locale, t)
}

function formatBirthDate(value, locale, t) {
  if (!value) return t('common.notSet')
  return new Date(`${value}T00:00:00`).toLocaleDateString(locale, {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

function calculateAge(value) {
  if (!value) return null
  const birthDate = new Date(`${value}T00:00:00`)
  if (Number.isNaN(birthDate.getTime())) return null
  const now = new Date()
  let years = now.getFullYear() - birthDate.getFullYear()
  const hadBirthdayThisYear =
    now.getMonth() > birthDate.getMonth() ||
    (now.getMonth() === birthDate.getMonth() && now.getDate() >= birthDate.getDate())
  if (!hadBirthdayThisYear) years -= 1
  return years >= 0 ? years : null
}

function formatCost(event) {
  if (event.cost_amount == null) return '-'
  return `${event.cost_currency || 'EUR'} ${Number(event.cost_amount).toFixed(2)}`
}

function CatAvatar({ cat }) {
  return (
    <div className="cat-detail__avatar">
      {cat.photo_url ? <img src={cat.photo_url} alt={cat.name} /> : <CatAvatarIcon />}
    </div>
  )
}

function EventForm({ initial, onSave, onCancel, cats = [], currentCatId, t }) {
  const [eventType, setEventType] = useState(initial?.event_type || 'vet_visit')
  const [occurredAt, setOccurredAt] = useState(toDateInputValue(initial?.occurred_at) || toDateInputValue(new Date()))
  const [title, setTitle] = useState(initial?.title || '')
  const [notes, setNotes] = useState(initial?.notes || '')
  const [costAmount, setCostAmount] = useState(initial?.cost_amount ?? '')
  const initialCatIds = initial?.cat_ids?.length ? initial.cat_ids : [Number(currentCatId)]
  const normalizedInitialCatIds = Array.from(new Set([...initialCatIds.map(Number), Number(currentCatId)])).sort((a, b) => a - b)
  const [selectedCatIds, setSelectedCatIds] = useState(normalizedInitialCatIds)
  const [costCurrency, setCostCurrency] = useState(initial?.cost_currency || 'EUR')
  const [saving, setSaving] = useState(false)
  const formId = initial ? `cat-event-edit-${initial.id}` : 'cat-event-new'

  function isCatSelected(catId) {
    return selectedCatIds.includes(Number(catId))
  }

  function toggleCat(catId) {
    const normalizedCatId = Number(catId)
    const normalizedCurrentCatId = Number(currentCatId)
    if (normalizedCatId === normalizedCurrentCatId) return
    setSelectedCatIds(current => {
      const withoutCurrent = current.filter(id => id !== normalizedCurrentCatId)
      const next = withoutCurrent.includes(normalizedCatId)
        ? withoutCurrent.filter(id => id !== normalizedCatId)
        : [...withoutCurrent, normalizedCatId]
      return [normalizedCurrentCatId, ...next].sort((a, b) => a - b)
    })
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setSaving(true)
    try {
      await onSave({
        event_type: eventType,
        cat_ids: selectedCatIds,
        occurred_at: occurredAt,
        title,
        notes: notes || null,
        cost_amount: costAmount === '' ? null : costAmount,
        cost_currency: costCurrency || 'EUR',
      })
      if (!initial) {
        setTitle('')
        setNotes('')
        setCostAmount('')
      }
    } finally {
      setSaving(false)
    }
  }

  return (
    <form className="cat-event-form" onSubmit={handleSubmit}>
      <div className="cat-event-form__grid">
        <div className="form-field">
          <label className="form-label" htmlFor={`${formId}-type`}>{t('field.type')}</label>
          <select id={`${formId}-type`} className="form-input" value={eventType} onChange={e => setEventType(e.target.value)}>
            {EVENT_TYPES.map(([value]) => <option key={value} value={value}>{t(`event.${value}`)}</option>)}
          </select>
        </div>
        <div className="form-field">
          <label className="form-label" htmlFor={`${formId}-occurred-at`}>{t('field.date')}</label>
          <input
            id={`${formId}-occurred-at`}
            className="form-input"
            type="date"
            value={occurredAt}
            onChange={e => setOccurredAt(e.target.value)}
            required
          />
        </div>
        <div className="form-field cat-event-form__title">
          <label className="form-label" htmlFor={`${formId}-title`}>{t('field.title')}</label>
          <input
            id={`${formId}-title`}
            className="form-input"
            value={title}
            onChange={e => setTitle(e.target.value)}
            placeholder={t('catDetail.annualCheckupExample')}
            required
          />
        </div>
        <div className="form-field">
          <label className="form-label" htmlFor={`${formId}-cost`}>{t('field.cost')}</label>
          <input
            id={`${formId}-cost`}
            className="form-input"
            type="number"
            step="0.01"
            min="0"
            value={costAmount}
            onChange={e => setCostAmount(e.target.value)}
            placeholder="0.00"
          />
        </div>
        <div className="form-field">
          <label className="form-label" htmlFor={`${formId}-currency`}>{t('field.currency')}</label>
          <input
            id={`${formId}-currency`}
            className="form-input"
            value={costCurrency}
            onChange={e => setCostCurrency(e.target.value.toUpperCase())}
            maxLength={3}
          />
        </div>
      </div>
      <div className="form-field">
        <label className="form-label" htmlFor={`${formId}-notes`}>{t('field.notes')}</label>
        <textarea
          id={`${formId}-notes`}
          className="form-input cat-event-form__notes"
          value={notes}
          onChange={e => setNotes(e.target.value)}
          placeholder={t('catDetail.optionalContext')}
        />
      </div>
      {cats.length > 0 && (
        <fieldset className="cat-event-form__cats">
          <legend className="form-label">{t('catDetail.appliesTo')}</legend>
          <div className="cat-event-form__cat-options">
            {cats.map(option => {
              const optionId = Number(option.id)
              const isCurrent = optionId === Number(currentCatId)
              return (
                <label key={option.id} className="cat-event-form__cat-option">
                  <input
                    type="checkbox"
                    checked={isCatSelected(optionId)}
                    disabled={isCurrent}
                    onChange={() => toggleCat(optionId)}
                  />
                  <span>{option.name}</span>
                </label>
              )
            })}
          </div>
        </fieldset>
      )}
      <div className="action-row">
        <button type="submit" className="btn btn-primary" disabled={saving}>
          {saving ? t('common.saving') : (initial ? t('catDetail.saveEvent') : t('catDetail.addEvent'))}
        </button>
        {onCancel && <button type="button" className="btn btn-secondary" onClick={onCancel}>{t('common.cancel')}</button>}
      </div>
    </form>
  )
}

function getSharedCatLabel(event, currentCatName, t) {
  if ((event.cat_names || []).length <= 1) return null
  const names = event.cat_names.filter(name => name !== currentCatName).join(', ') || t('catDetail.multipleCats')
  return t('catDetail.sharedWith', { names })
}

function CatEventMobileCard({ row, cat, locale, t, onEdit, onDelete }) {
  if (row.kind === 'birthday') {
    return (
      <article className="cat-event-card cat-event-card--birthday" role="listitem">
        <div className="cat-event-card__header">
          <div>
            <span className="cat-event-card__date">{formatBirthDate(cat.birth_date, locale, t)}</span>
            <h3>{t('catDetail.born')}</h3>
          </div>
          <StatusBadge tone="accent">{t('catDetail.birthday')}</StatusBadge>
        </div>
        <p>{t('catDetail.profileBirthday')}</p>
      </article>
    )
  }

  const { event } = row
  const sharedLabel = getSharedCatLabel(event, cat.name, t)

  return (
    <article className="cat-event-card" role="listitem">
      <div className="cat-event-card__header">
        <div>
          <span className="cat-event-card__date">{formatEventDate(event.occurred_at, locale, t)}</span>
          <h3>{event.title}</h3>
          {sharedLabel && <div className="cat-event-shared-label">{sharedLabel}</div>}
        </div>
        <StatusBadge tone="muted">{t(`event.${event.event_type}`)}</StatusBadge>
      </div>
      <dl className="cat-event-card__details">
        <div>
          <dt>{t('field.notes')}</dt>
          <dd>{event.notes || '-'}</dd>
        </div>
        <div>
          <dt>{t('field.cost')}</dt>
          <dd>{formatCost(event)}</dd>
        </div>
      </dl>
      <div className="cat-event-actions">
        <button className="btn btn-secondary btn-sm" onClick={() => onEdit(event)}>{t('common.editDisplay')}</button>
        <button className="btn btn-secondary btn-sm text-danger" onClick={() => onDelete(event)}>{t('common.delete')}</button>
      </div>
    </article>
  )
}


export default function CatDetail() {
  const { catId } = useParams()
  const [cat, setCat] = useState(null)
  const [events, setEvents] = useState([])
  const [cats, setCats] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [editingEvent, setEditingEvent] = useState(null)
  const toast = useToast()
  const { locale, t } = useLanguage()

  useEffect(() => {
    const controller = new AbortController()
    async function fetchData() {
      setLoading(true)
      setError(null)
      try {
        const [catData, eventData, catsData] = await Promise.all([
          getCat(catId),
          getCatEvents(catId, { signal: controller.signal }),
          getCats(true, { signal: controller.signal }),
        ])
        setCat(catData)
        setEvents(eventData)
        setCats(catsData)
      } catch (e) {
        if (e.name !== 'CanceledError') {
          console.error('Failed to load cat detail', e)
          setError(t('catDetail.loadFailed'))
        }
      } finally {
        setLoading(false)
      }
    }
    fetchData()
    return () => controller.abort()
  }, [catId, t])

  const age = useMemo(() => calculateAge(cat?.birth_date), [cat?.birth_date])
  const timelineRows = useMemo(() => {
    const rows = events.map(event => ({ kind: 'event', occurredAt: event.occurred_at, event }))
    if (cat?.birth_date) {
      rows.push({ kind: 'birthday', occurredAt: cat.birth_date, event: null })
    }
    return rows.sort((a, b) => b.occurredAt.localeCompare(a.occurredAt) || ((b.event?.id || 0) - (a.event?.id || 0)))
  }, [cat?.birth_date, events])

  async function handleCreateEvent(data) {
    try {
      const created = await createCatEvent(catId, data)
      setEvents(prev => [created, ...prev].sort((a, b) => b.occurred_at.localeCompare(a.occurred_at) || b.id - a.id))
      toast(t('catDetail.eventAdded'), 'success')
    } catch (e) {
      console.error('Failed to add cat event', e)
      toast(t('catDetail.addFailed'))
    }
  }

  async function handleUpdateEvent(data) {
    try {
      const updated = await updateCatEvent(catId, editingEvent.id, data)
      setEvents(prev => prev.map(event => event.id === updated.id ? updated : event))
      setEditingEvent(null)
      toast(t('catDetail.eventUpdated'), 'success')
    } catch (e) {
      console.error('Failed to update cat event', e)
      toast(t('catDetail.updateFailed'))
    }
  }

  async function handleDeleteEvent(event) {
    const isShared = (event.cat_ids || []).length > 1
    if (isShared && !window.confirm(t('catDetail.deleteSharedConfirm'))) {
      return
    }
    try {
      await deleteCatEvent(catId, event.id)
      setEvents(prev => prev.filter(item => item.id !== event.id))
      toast(t('catDetail.eventDeleted'), 'success')
    } catch (e) {
      console.error('Failed to delete cat event', e)
      toast(t('catDetail.deleteFailed'))
    }
  }

  if (loading) return <div className="loading">{t('state.loading')}</div>
  if (error || !cat) {
    return (
      <div>
        <PageHeader title={t('catDetail.catTitle')} subtitle={t('field.lifecycleEvents')} actions={<Link className="btn btn-secondary" to="/cats">{t('catDetail.back')}</Link>} />
        <div className="card"><EmptyState icon={<Icon name="cat" />} message={error || t('catDetail.notFound')} /></div>
      </div>
    )
  }

  return (
    <div>
      <PageHeader
        title={cat.name}
        subtitle={t('catDetail.subtitle')}
        actions={<Link className="btn btn-secondary" to="/cats">{t('catDetail.back')}</Link>}
      />

      <section className="card cat-detail-card mb-6">
        <CatAvatar cat={cat} />
        <div className="cat-detail-card__main">
          <div className="cat-detail-card__title-row">
            <h2>{cat.name}</h2>
            {cat.active ? <StatusBadge tone="green">{t('status.active')}</StatusBadge> : <StatusBadge tone="muted">{t('status.inactive')}</StatusBadge>}
          </div>
          <div className="cat-profile__meta-grid">
            <div className="cat-profile__meta-item">
              <span>{t('field.referenceWeight')}</span>
              <strong>{cat.reference_weight_kg == null ? t('common.notSet') : `${cat.reference_weight_kg.toFixed(3)} kg`}</strong>
            </div>
            <div className="cat-profile__meta-item">
              <span>{t('field.birthday')}</span>
              <strong>{formatBirthDate(cat.birth_date, locale, t)}</strong>
            </div>
            <div className="cat-profile__meta-item">
              <span>{t('catDetail.age')}</span>
              <strong>{age == null ? t('common.notSet') : t('common.yearsShort', { count: age })}</strong>
            </div>
          </div>
        </div>
      </section>

      <section className="card cat-event-panel mb-6">
        <div className="section-heading-row">
          <div>
            <h2>{t('catDetail.events')}</h2>
            <p className="text-muted text-small">{t('catDetail.eventsDescription')}</p>
          </div>
        </div>
        <EventForm onSave={handleCreateEvent} cats={cats} currentCatId={catId} t={t} />
      </section>

      {editingEvent && (
        <section className="card cat-event-panel mb-6">
          <div className="section-heading-row">
            <h2>{t('catDetail.editEvent')}</h2>
          </div>
          <EventForm initial={editingEvent} onSave={handleUpdateEvent} onCancel={() => setEditingEvent(null)} cats={cats} currentCatId={catId} t={t} />
        </section>
      )}

      <section className="card card--flush cat-event-table-card">
        <table className="table cat-event-table">
          <thead>
            <tr>
              <th>{t('field.date')}</th>
              <th>{t('field.type')}</th>
              <th>{t('field.title')}</th>
              <th>{t('field.notes')}</th>
              <th>{t('field.cost')}</th>
              <th>{t('field.actions')}</th>
            </tr>
          </thead>
          <tbody>
            {timelineRows.map(row => {
              if (row.kind === 'birthday') {
                return (
                  <tr key="birthday" className="cat-event-row cat-event-row--birthday">
                    <td>{formatBirthDate(cat.birth_date, locale, t)}</td>
                    <td><StatusBadge tone="accent">{t('catDetail.birthday')}</StatusBadge></td>
                    <td>{t('catDetail.born')}</td>
                    <td>{t('catDetail.profileBirthday')}</td>
                    <td>-</td>
                    <td>-</td>
                  </tr>
                )
              }
              const { event } = row
              const sharedLabel = getSharedCatLabel(event, cat.name, t)
              return (
                <tr key={event.id} className="cat-event-row">
                  <td>{formatEventDate(event.occurred_at, locale, t)}</td>
                  <td><StatusBadge tone="muted">{t(`event.${event.event_type}`)}</StatusBadge></td>
                  <td className="text-primary">
                    <div>{event.title}</div>
                    {sharedLabel && <div className="cat-event-shared-label">{sharedLabel}</div>}
                  </td>
                  <td>{event.notes || '-'}</td>
                  <td>{formatCost(event)}</td>
                  <td>
                    <div className="cat-event-actions">
                      <button className="btn btn-secondary btn-sm" onClick={() => setEditingEvent(event)}>{t('common.editDisplay')}</button>
                      <button className="btn btn-secondary btn-sm text-danger" onClick={() => handleDeleteEvent(event)}>{t('common.delete')}</button>
                    </div>
                  </td>
                </tr>
              )
            })}
            {timelineRows.length === 0 && (
              <tr>
                <td colSpan="6">
                  <EmptyState icon={<Icon name="cat" />} message={t('catDetail.noEvents')} compact />
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </section>

      {timelineRows.length > 0 && (
        <div className="cat-event-card-list" role="list" aria-label={t('catDetail.events')}>
          {timelineRows.map(row => (
            <CatEventMobileCard
              key={row.kind === 'birthday' ? 'birthday-card' : row.event.id}
              row={row}
              cat={cat}
              locale={locale}
              t={t}
              onEdit={setEditingEvent}
              onDelete={handleDeleteEvent}
            />
          ))}
        </div>
      )}
    </div>
  )
}
