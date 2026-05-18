import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  createCatEvent,
  deleteCatEvent,
  getCat,
  getCatEvents,
  updateCatEvent,
} from '../api/client'
import Icon, { CatAvatarIcon } from '../components/Icon'
import { useToast } from '../components/ToastContext'
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

const EVENT_LABELS = Object.fromEntries(EVENT_TYPES)

function toDateInputValue(value) {
  if (!value) return ''
  const date = new Date(`${value}`.slice(0, 10) + 'T00:00:00')
  if (Number.isNaN(date.getTime())) return ''
  const year = date.getFullYear()
  const month = `${date.getMonth() + 1}`.padStart(2, '0')
  const day = `${date.getDate()}`.padStart(2, '0')
  return `${year}-${month}-${day}`
}

function formatEventDate(value) {
  return formatBirthDate(`${value}`.slice(0, 10))
}

function formatBirthDate(value) {
  if (!value) return 'Not set'
  return new Date(`${value}T00:00:00`).toLocaleDateString('en-GB', {
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

function EventForm({ initial, onSave, onCancel }) {
  const [eventType, setEventType] = useState(initial?.event_type || 'vet_visit')
  const [occurredAt, setOccurredAt] = useState(toDateInputValue(initial?.occurred_at) || toDateInputValue(new Date()))
  const [title, setTitle] = useState(initial?.title || '')
  const [notes, setNotes] = useState(initial?.notes || '')
  const [costAmount, setCostAmount] = useState(initial?.cost_amount ?? '')
  const [costCurrency, setCostCurrency] = useState(initial?.cost_currency || 'EUR')
  const [saving, setSaving] = useState(false)
  const formId = initial ? `cat-event-edit-${initial.id}` : 'cat-event-new'

  async function handleSubmit(e) {
    e.preventDefault()
    setSaving(true)
    try {
      await onSave({
        event_type: eventType,
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
          <label className="form-label" htmlFor={`${formId}-type`}>Type</label>
          <select id={`${formId}-type`} className="form-input" value={eventType} onChange={e => setEventType(e.target.value)}>
            {EVENT_TYPES.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </div>
        <div className="form-field">
          <label className="form-label" htmlFor={`${formId}-occurred-at`}>Date</label>
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
          <label className="form-label" htmlFor={`${formId}-title`}>Title</label>
          <input
            id={`${formId}-title`}
            className="form-input"
            value={title}
            onChange={e => setTitle(e.target.value)}
            placeholder="e.g. Annual checkup"
            required
          />
        </div>
        <div className="form-field">
          <label className="form-label" htmlFor={`${formId}-cost`}>Cost</label>
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
          <label className="form-label" htmlFor={`${formId}-currency`}>Currency</label>
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
        <label className="form-label" htmlFor={`${formId}-notes`}>Notes</label>
        <textarea
          id={`${formId}-notes`}
          className="form-input cat-event-form__notes"
          value={notes}
          onChange={e => setNotes(e.target.value)}
          placeholder="Optional context"
        />
      </div>
      <div className="action-row">
        <button type="submit" className="btn btn-primary" disabled={saving}>
          {saving ? 'Saving...' : (initial ? 'Save event' : 'Add event')}
        </button>
        {onCancel && <button type="button" className="btn btn-secondary" onClick={onCancel}>Cancel</button>}
      </div>
    </form>
  )
}

export default function CatDetail() {
  const { catId } = useParams()
  const [cat, setCat] = useState(null)
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [editingEvent, setEditingEvent] = useState(null)
  const toast = useToast()

  useEffect(() => {
    const controller = new AbortController()
    async function fetchData() {
      setLoading(true)
      setError(null)
      try {
        const [catData, eventData] = await Promise.all([
          getCat(catId),
          getCatEvents(catId, { signal: controller.signal }),
        ])
        setCat(catData)
        setEvents(eventData)
      } catch (e) {
        if (e.name !== 'CanceledError') {
          console.error('Failed to load cat detail', e)
          setError('Failed to load cat details')
        }
      } finally {
        setLoading(false)
      }
    }
    fetchData()
    return () => controller.abort()
  }, [catId])

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
      toast('Event added', 'success')
    } catch (e) {
      console.error('Failed to add cat event', e)
      toast('Failed to add event. Please try again.')
    }
  }

  async function handleUpdateEvent(data) {
    try {
      const updated = await updateCatEvent(catId, editingEvent.id, data)
      setEvents(prev => prev.map(event => event.id === updated.id ? updated : event))
      setEditingEvent(null)
      toast('Event updated', 'success')
    } catch (e) {
      console.error('Failed to update cat event', e)
      toast('Failed to update event. Please try again.')
    }
  }

  async function handleDeleteEvent(event) {
    try {
      await deleteCatEvent(catId, event.id)
      setEvents(prev => prev.filter(item => item.id !== event.id))
      toast('Event deleted', 'success')
    } catch (e) {
      console.error('Failed to delete cat event', e)
      toast('Failed to delete event. Please try again.')
    }
  }

  if (loading) return <div className="loading">Loading...</div>
  if (error || !cat) {
    return (
      <div>
        <PageHeader title="Cat" subtitle="Lifecycle events" actions={<Link className="btn btn-secondary" to="/cats">Back to cats</Link>} />
        <div className="card"><EmptyState icon={<Icon name="cat" />} message={error || 'Cat not found'} /></div>
      </div>
    )
  }

  return (
    <div>
      <PageHeader
        title={cat.name}
        subtitle="Lifecycle events and profile context"
        actions={<Link className="btn btn-secondary" to="/cats">Back to cats</Link>}
      />

      <section className="card cat-detail-card mb-6">
        <CatAvatar cat={cat} />
        <div className="cat-detail-card__main">
          <div className="cat-detail-card__title-row">
            <h2>{cat.name}</h2>
            {cat.active ? <StatusBadge tone="green">active</StatusBadge> : <StatusBadge tone="muted">inactive</StatusBadge>}
          </div>
          <div className="cat-profile__meta-grid">
            <div className="cat-profile__meta-item">
              <span>Reference weight</span>
              <strong>{cat.reference_weight_kg == null ? 'not set' : `${cat.reference_weight_kg.toFixed(3)} kg`}</strong>
            </div>
            <div className="cat-profile__meta-item">
              <span>Birthday</span>
              <strong>{formatBirthDate(cat.birth_date)}</strong>
            </div>
            <div className="cat-profile__meta-item">
              <span>Age</span>
              <strong>{age == null ? 'not set' : `${age} years`}</strong>
            </div>
          </div>
        </div>
      </section>

      <section className="card cat-event-panel mb-6">
        <div className="section-heading-row">
          <div>
            <h2>Events</h2>
            <p className="text-muted text-small">Track vet visits, medication, diet changes, milestones, and notes.</p>
          </div>
        </div>
        <EventForm onSave={handleCreateEvent} />
      </section>

      {editingEvent && (
        <section className="card cat-event-panel mb-6">
          <div className="section-heading-row">
            <h2>Edit event</h2>
          </div>
          <EventForm initial={editingEvent} onSave={handleUpdateEvent} onCancel={() => setEditingEvent(null)} />
        </section>
      )}

      <section className="card card--flush cat-event-table-card">
        <table className="table cat-event-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Type</th>
              <th>Title</th>
              <th>Notes</th>
              <th>Cost</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {timelineRows.map(row => {
              if (row.kind === 'birthday') {
                return (
                  <tr key="birthday" className="cat-event-row cat-event-row--birthday">
                    <td data-label="Date">{formatBirthDate(cat.birth_date)}</td>
                    <td data-label="Type"><StatusBadge tone="accent">Birthday</StatusBadge></td>
                    <td data-label="Title">Born</td>
                    <td data-label="Notes">Profile birthday</td>
                    <td data-label="Cost">-</td>
                    <td data-label="Actions">-</td>
                  </tr>
                )
              }
              const { event } = row
              return (
                <tr key={event.id} className="cat-event-row">
                  <td data-label="Date">{formatEventDate(event.occurred_at)}</td>
                  <td data-label="Type"><StatusBadge tone="muted">{EVENT_LABELS[event.event_type] || event.event_type}</StatusBadge></td>
                  <td data-label="Title" className="text-primary">{event.title}</td>
                  <td data-label="Notes">{event.notes || '-'}</td>
                  <td data-label="Cost">{formatCost(event)}</td>
                  <td data-label="Actions">
                    <div className="cat-event-actions">
                      <button className="btn btn-secondary btn-sm" onClick={() => setEditingEvent(event)}>Edit</button>
                      <button className="btn btn-secondary btn-sm text-danger" onClick={() => handleDeleteEvent(event)}>Delete</button>
                    </div>
                  </td>
                </tr>
              )
            })}
            {timelineRows.length === 0 && (
              <tr>
                <td colSpan="6">
                  <EmptyState icon={<Icon name="cat" />} message="No lifecycle events yet" compact />
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </section>
    </div>
  )
}
