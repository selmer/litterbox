import { useState, useEffect } from 'react'
import { getVisits, getCats, updateVisit } from '../api/client'
import VisitsList from '../components/VisitsList'

export default function Visits() {
  const [visits, setVisits] = useState([])
  const [cats, setCats] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedCat, setSelectedCat] = useState(null)
  const [reassigning, setReassigning] = useState(null) // visit being reassigned

  useEffect(() => {
    async function fetch() {
      setLoading(true)
      try {
        const [v, c] = await Promise.all([getVisits({ limit: 100 }), getCats()])
        setVisits(v)
        setCats(c)
      } finally {
        setLoading(false)
      }
    }
    fetch()
  }, [])

  async function handleReassign(visit) {
    setReassigning(visit)
  }

  async function confirmReassign(catId) {
    if (!reassigning) return
    try {
      const updated = await updateVisit(reassigning.id, { cat_id: catId })
      setVisits(prev => prev.map(v => v.id === updated.id ? updated : v))
    } catch (e) {
      console.error('Failed to reassign visit', e)
    } finally {
      setReassigning(null)
    }
  }

  const filteredVisits = selectedCat
    ? visits.filter(v => v.cat_id === selectedCat)
    : visits

  if (loading) return <div className="loading">Loading…</div>

  return (
    <div>
      <div className="page-header">
        <h2>Visits</h2>
        <p>Full history of litterbox visits</p>
      </div>

      {/* Filter bar */}
      <div className="flex-center gap-2 mb-6">
        <button
          className={`btn btn-sm ${selectedCat === null ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setSelectedCat(null)}
        >
          All
        </button>
        {cats.map(cat => (
          <button
            key={cat.id}
            className={`btn btn-sm ${selectedCat === cat.id ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setSelectedCat(cat.id)}
          >
            {cat.name}
          </button>
        ))}
        <button
          className={`btn btn-sm ${selectedCat === 'unidentified' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setSelectedCat('unidentified')}
        >
          Unidentified
        </button>
      </div>

      <VisitsList
        visits={selectedCat === 'unidentified'
          ? visits.filter(v => !v.cat_id)
          : filteredVisits
        }
        cats={cats}
        onReassign={handleReassign}
      />

      {/* Reassign modal */}
      {reassigning && (
        <div className="modal-overlay" onClick={() => setReassigning(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-title">Reassign visit</div>
            <p className="text-muted" style={{ fontSize: 13, marginBottom: 16 }}>
              Who used the litterbox at{' '}
              {new Date(reassigning.started_at).toLocaleTimeString('en-GB', {
                hour: '2-digit', minute: '2-digit'
              })}
              {reassigning.weight_kg && ` · ${reassigning.weight_kg.toFixed(3)} kg`}?
            </p>
            <div className="flex-col gap-2">
              {cats.map(cat => (
                <button
                  key={cat.id}
                  className="btn btn-secondary w-full"
                  style={{ justifyContent: 'flex-start' }}
                  onClick={() => confirmReassign(cat.id)}
                >
                  🐱 {cat.name}
                  {cat.reference_weight_kg && (
                    <span className="text-muted" style={{ marginLeft: 'auto', fontSize: 11 }}>
                      ref: {cat.reference_weight_kg.toFixed(2)} kg
                    </span>
                  )}
                </button>
              ))}
              <button
                className="btn btn-secondary w-full"
                style={{ justifyContent: 'flex-start', color: 'var(--text-muted)' }}
                onClick={() => confirmReassign(null)}
              >
                Mark as visitor cat
              </button>
            </div>
            <button
              className="btn btn-secondary w-full mt-4"
              onClick={() => setReassigning(null)}
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
