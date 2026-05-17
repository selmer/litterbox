import { useState, useEffect } from 'react'
import { getCats, createCat, updateCat } from '../api/client'
import Icon, { CatAvatarIcon } from '../components/Icon'
import { useToast } from '../components/ToastContext'
import { EmptyState, PageHeader, StatusBadge } from '../components/ui'

function CatAvatar({ cat }) {
  return (
    <div className="cat-profile__avatar">
      {cat.photo_url ? <img src={cat.photo_url} alt={cat.name} /> : <CatAvatarIcon />}
    </div>
  )
}

function ReferenceWeight({ weight }) {
  if (weight == null) return <StatusBadge tone="muted">not set</StatusBadge>
  return <strong>{weight.toFixed(3)} kg</strong>
}

function CatForm({ initial, onSave, onCancel }) {
  const [name, setName] = useState(initial?.name || '')
  const [weight, setWeight] = useState(initial?.reference_weight_kg ?? '')
  const [saving, setSaving] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setSaving(true)
    try {
      await onSave({
        name,
        reference_weight_kg: weight ? parseFloat(weight) : null,
      })
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="cat-form cat-profile-form">
      <div className="cat-profile-form__grid">
        <div className="form-field">
          <label className="form-label">Name</label>
          <input
            className="form-input"
            value={name}
            onChange={e => setName(e.target.value)}
            placeholder="e.g. Griezeltje"
            required
          />
        </div>
        <div className="form-field">
          <label className="form-label">Reference weight (kg)</label>
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
      </div>
      <p className="form-hint">
        Used to automatically identify this cat from weight readings. Leave blank if unknown.
      </p>
      <div className="action-row">
        <button type="submit" className="btn btn-primary" disabled={saving}>
          {saving ? 'Saving…' : (initial ? 'Save changes' : 'Add cat')}
        </button>
        {onCancel && (
          <button type="button" className="btn btn-secondary" onClick={onCancel}>
            Cancel
          </button>
        )}
      </div>
    </form>
  )
}

function CatProfileRow({ cat, editing, onEdit, onCancelEdit, onSave, onToggleActive }) {
  if (editing) {
    return (
      <section className={`card cat-profile-card cat-profile-card--editing ${!cat.active ? 'cat-profile-card--inactive' : ''}`}>
        <div className="cat-profile-card__edit-header">
          <CatAvatar cat={cat} />
          <div>
            <div className="card-label">Editing {cat.name}</div>
            <p className="text-muted text-small">Update identity matching details.</p>
          </div>
        </div>
        <CatForm initial={cat} onSave={onSave} onCancel={onCancelEdit} />
      </section>
    )
  }

  return (
    <section className={`card cat-profile-card ${!cat.active ? 'cat-profile-card--inactive' : ''}`}>
      <div className="cat-profile">
        <CatAvatar cat={cat} />
        <div className="cat-profile__main">
          <div className="cat-profile__title-row">
            <h3>{cat.name}</h3>
            {cat.active ? <StatusBadge tone="green">active</StatusBadge> : <StatusBadge tone="muted">inactive</StatusBadge>}
          </div>
          <div className="cat-profile__meta-grid">
            <div className="cat-profile__meta-item">
              <span>Reference weight</span>
              <ReferenceWeight weight={cat.reference_weight_kg} />
            </div>
            <div className="cat-profile__meta-item">
              <span>Added</span>
              <strong>{new Date(cat.created_at).toLocaleDateString('en-GB')}</strong>
            </div>
          </div>
        </div>
        <div className="cat-profile__actions">
          <button className="btn btn-secondary btn-sm" onClick={onEdit}>
            Edit
          </button>
          <button className="btn btn-secondary btn-sm" onClick={onToggleActive}>
            {cat.active ? 'Deactivate' : 'Reactivate'}
          </button>
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
      toast(`${cat.name} added`, 'success')
    } catch (e) {
      console.error('Failed to create cat', e)
      toast('Failed to add cat. Please try again.')
    }
  }

  async function handleUpdate(id, data) {
    try {
      const cat = await updateCat(id, data)
      setCats(prev => prev.map(c => c.id === id ? cat : c))
      setEditing(null)
      toast('Changes saved', 'success')
    } catch (e) {
      console.error('Failed to update cat', e)
      toast('Failed to save changes. Please try again.')
    }
  }

  async function handleToggleActive(cat) {
    try {
      const updated = await updateCat(cat.id, { active: !cat.active })
      setCats(prev => prev.map(c => c.id === cat.id ? updated : c))
    } catch (e) {
      console.error('Failed to update cat', e)
      toast(`Failed to ${cat.active ? 'deactivate' : 'reactivate'} cat. Please try again.`)
    }
  }

  if (loading) return <div className="loading">Loading…</div>

  return (
    <div>
      <PageHeader
        title="Cats"
        subtitle="Manage cats and their reference weights"
        actions={!adding && (
          <button className="btn btn-primary" onClick={() => setAdding(true)}>
            + Add cat
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
              <div className="card-label">New cat</div>
              <p className="text-muted text-small">Add a cat profile for weight-based identification.</p>
            </div>
          </div>
          <CatForm onSave={handleCreate} onCancel={() => setAdding(false)} />
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
          />
        ))}

        {cats.length === 0 && !adding && (
          <div className="card">
            <EmptyState icon={<Icon name="cat" />} message="No cats yet. Add one to get started.">
              <button className="btn btn-primary" onClick={() => setAdding(true)}>
                + Add cat
              </button>
            </EmptyState>
          </div>
        )}
      </div>
    </div>
  )
}
