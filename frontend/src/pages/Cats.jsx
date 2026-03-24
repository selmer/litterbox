import { useState, useEffect } from 'react'
import { getCats, createCat, updateCat } from '../api/client'
import { useToast } from '../components/Toast'

function CatForm({ initial, onSave, onCancel }) {
  const [name, setName] = useState(initial?.name || '')
  const [weight, setWeight] = useState(initial?.reference_weight_kg || '')
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
    <form onSubmit={handleSubmit} className="cat-form">
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
        <p className="form-hint">
          Used to automatically identify this cat from weight readings.
          Leave blank if unknown — you can set it later.
        </p>
      </div>
      <div className="flex-center gap-2" style={{ marginTop: 16 }}>
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

export default function Cats() {
  const [cats, setCats] = useState([])
  const [loading, setLoading] = useState(true)
  const [adding, setAdding] = useState(false)
  const [editing, setEditing] = useState(null) // cat id being edited
  const toast = useToast()

  useEffect(() => {
    async function fetch() {
      setLoading(true)
      try {
        const data = await getCats(true) // include inactive
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
      <div className="page-header">
        <div className="flex-between">
          <div>
            <h2>Cats</h2>
            <p>Manage cats and their reference weights</p>
          </div>
          {!adding && (
            <button className="btn btn-primary" onClick={() => setAdding(true)}>
              + Add cat
            </button>
          )}
        </div>
      </div>

      {adding && (
        <div className="card mb-6">
          <div className="card-label">New cat</div>
          <CatForm
            onSave={handleCreate}
            onCancel={() => setAdding(false)}
          />
        </div>
      )}

      <div className="flex-col gap-4">
        {cats.map(cat => (
          <div key={cat.id} className={`card ${!cat.active ? 'cat-inactive' : ''}`}>
            {editing === cat.id ? (
              <>
                <div className="card-label">Editing {cat.name}</div>
                <CatForm
                  initial={cat}
                  onSave={(data) => handleUpdate(cat.id, data)}
                  onCancel={() => setEditing(null)}
                />
              </>
            ) : (
              <div className="flex-between">
                <div>
                  <div className="flex-center gap-2">
                    <span style={{ fontWeight: 500, fontSize: 15 }}>🐱 {cat.name}</span>
                    {!cat.active && <span className="badge badge-muted">inactive</span>}
                  </div>
                  <div className="text-muted mt-1" style={{ fontSize: 12 }}>
                    Reference weight:{' '}
                    {cat.reference_weight_kg
                      ? <strong>{cat.reference_weight_kg.toFixed(3)} kg</strong>
                      : <em>not set</em>
                    }
                    {' · '}Added {new Date(cat.created_at).toLocaleDateString('en-GB')}
                  </div>
                </div>
                <div className="flex-center gap-2">
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => setEditing(cat.id)}
                  >
                    Edit
                  </button>
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => handleToggleActive(cat)}
                  >
                    {cat.active ? 'Deactivate' : 'Reactivate'}
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}

        {cats.length === 0 && !adding && (
          <div className="empty-state">
            <div className="empty-icon">🐱</div>
            <p>No cats yet. Add one to get started.</p>
          </div>
        )}
      </div>
    </div>
  )
}
