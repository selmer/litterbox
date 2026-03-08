import { useState, useEffect } from 'react'
import { getVisits, getCats, updateVisit, deleteVisit } from '../api/client'
import VisitsList from '../components/VisitsList'
import { useToast } from '../components/Toast'

const PAGE_SIZE = 50

export default function Visits() {
  const [visits, setVisits] = useState([])
  const [cats, setCats] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedCat, setSelectedCat] = useState(null)
  const [page, setPage] = useState(0)
  const [hasMore, setHasMore] = useState(false)
  const [reassigning, setReassigning] = useState(null) // visit being reassigned
  const toast = useToast()

  useEffect(() => {
    getCats().then(setCats)
  }, [])

  useEffect(() => {
    async function fetchVisits() {
      setLoading(true)
      try {
        const params = { limit: PAGE_SIZE + 1, offset: page * PAGE_SIZE }
        if (selectedCat === 'unidentified') {
          params.unidentified = true
        } else if (selectedCat !== null) {
          params.catId = selectedCat
        }
        const v = await getVisits(params)
        setHasMore(v.length > PAGE_SIZE)
        setVisits(v.slice(0, PAGE_SIZE))
      } finally {
        setLoading(false)
      }
    }
    fetchVisits()
  }, [selectedCat, page])

  function selectFilter(cat) {
    setSelectedCat(cat)
    setPage(0)
  }

  async function handleDelete(visit) {
    try {
      await deleteVisit(visit.id)
      setVisits(prev => prev.filter(v => v.id !== visit.id))
    } catch (e) {
      console.error('Failed to delete visit', e)
      toast('Failed to delete visit. Please try again.')
    }
  }

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
      toast('Failed to reassign visit. Please try again.')
    } finally {
      setReassigning(null)
    }
  }

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
          onClick={() => selectFilter(null)}
        >
          All
        </button>
        {cats.map(cat => (
          <button
            key={cat.id}
            className={`btn btn-sm ${selectedCat === cat.id ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => selectFilter(cat.id)}
          >
            {cat.name}
          </button>
        ))}
        <button
          className={`btn btn-sm ${selectedCat === 'unidentified' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => selectFilter('unidentified')}
        >
          Unidentified
        </button>
      </div>

      <VisitsList
        visits={visits}
        cats={cats}
        onReassign={handleReassign}
        onDelete={handleDelete}
      />

      {/* Pagination controls */}
      {(page > 0 || hasMore) && (
        <div className="flex-center gap-2 mt-4">
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => setPage(p => p - 1)}
            disabled={page === 0}
          >
            ← Previous
          </button>
          <span className="text-muted" style={{ fontSize: 13 }}>Page {page + 1}</span>
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => setPage(p => p + 1)}
            disabled={!hasMore}
          >
            Next →
          </button>
        </div>
      )}

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
