import { useState, useEffect } from 'react'
import { getApiErrorMessage, getVisits, getCats, updateVisit, deleteVisit } from '../api/client'
import VisitsList from '../components/VisitsList'
import { useToast } from '../components/ToastContext'
import { ModalShell, PageHeader } from '../components/ui'

const PAGE_SIZE = 50

function isCanceled(error) {
  return error?.code === 'ERR_CANCELED' || error?.name === 'CanceledError'
}

export default function Visits() {
  const [visits, setVisits] = useState([])
  const [cats, setCats] = useState([])
  const [initialLoading, setInitialLoading] = useState(true)
  const [fetching, setFetching] = useState(false)
  const [selectedCat, setSelectedCat] = useState(null)
  const [page, setPage] = useState(0)
  const [hasMore, setHasMore] = useState(false)
  const [loadError, setLoadError] = useState(null)
  const [reloadNonce, setReloadNonce] = useState(0)
  const [reassigning, setReassigning] = useState(null)
  const toast = useToast()

  useEffect(() => {
    getCats().then(setCats).catch(e => {
      console.error('Failed to load cats', e)
      toast('Failed to load cats. Please try again.')
    })
  }, [toast])

  useEffect(() => {
    let canceled = false
    const controller = new AbortController()

    async function fetchVisits() {
      setFetching(true)
      setLoadError(null)
      try {
        const params = { limit: PAGE_SIZE + 1, offset: page * PAGE_SIZE, signal: controller.signal }
        if (selectedCat === 'unidentified') {
          params.unidentified = true
        } else if (selectedCat !== null) {
          params.catId = selectedCat
        }
        const v = await getVisits(params)
        if (canceled) return
        setHasMore(v.length > PAGE_SIZE)
        setVisits(v.slice(0, PAGE_SIZE))
      } catch (e) {
        if (!canceled && !isCanceled(e)) {
          setLoadError(getApiErrorMessage(e))
        }
      } finally {
        if (!canceled) {
          setInitialLoading(false)
          setFetching(false)
        }
      }
    }
    fetchVisits()
    return () => {
      canceled = true
      controller.abort()
    }
  }, [selectedCat, page, reloadNonce])

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

  if (initialLoading) return <div className="loading">Loading…</div>

  return (
    <div>
      <PageHeader title="Visits" subtitle="Full history of litterbox visits" />

      <div className="filter-bar">
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
        <span className="filter-divider" aria-hidden="true" />
        <button
          className={`btn btn-sm ${selectedCat === 'unidentified' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => selectFilter('unidentified')}
        >
          Unidentified
        </button>
      </div>

      <div className={`fetch-state ${fetching ? 'is-fetching' : ''}`}>
        {loadError && (
          <div className="alert alert-yellow mb-4">
            {loadError}
            <button className="btn btn-secondary btn-sm alert__action" onClick={() => setReloadNonce(n => n + 1)}>
              Retry
            </button>
          </div>
        )}
        <VisitsList visits={visits} cats={cats} onReassign={handleReassign} onDelete={handleDelete} />
      </div>

      {(page > 0 || hasMore) && (
        <div className="pagination">
          <button className="btn btn-secondary btn-sm" onClick={() => setPage(p => p - 1)} disabled={page === 0}>
            ← Previous
          </button>
          <span className="pagination__label">
            Page {page + 1} · Visits {page * PAGE_SIZE + 1}–{page * PAGE_SIZE + visits.length}
          </span>
          <button className="btn btn-secondary btn-sm" onClick={() => setPage(p => p + 1)} disabled={!hasMore}>
            Next →
          </button>
        </div>
      )}

      {reassigning && (
        <ModalShell
          title="Reassign visit"
          onClose={() => setReassigning(null)}
          description={(
            <>
              Who used the litterbox at{' '}
              {new Date(reassigning.started_at).toLocaleTimeString('en-GB', {
                hour: '2-digit', minute: '2-digit'
              })}
              {reassigning.weight_kg && ` · ${reassigning.weight_kg.toFixed(3)} kg`}?
            </>
          )}
        >
          <p className="modal-description modal-description--tight">
            Currently:{' '}
            {reassigning.cat_id
              ? <strong>{cats.find(c => c.id === reassigning.cat_id)?.name ?? `Cat #${reassigning.cat_id}`}</strong>
              : <em>unidentified</em>
            }
          </p>
          <div className="flex-col gap-2">
            {cats.map(cat => (
              <button
                key={cat.id}
                className={`btn w-full btn-align-start ${cat.id === reassigning.cat_id ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => confirmReassign(cat.id)}
              >
                🐱 {cat.name}
                {cat.reference_weight_kg && (
                  <span className="button-meta">ref: {cat.reference_weight_kg.toFixed(2)} kg</span>
                )}
              </button>
            ))}
            <button
              className="btn btn-secondary w-full btn-align-start text-muted"
              onClick={() => confirmReassign(null)}
            >
              Mark as visitor cat
            </button>
          </div>
          <button className="btn btn-secondary w-full mt-4" onClick={() => setReassigning(null)}>
            Cancel
          </button>
        </ModalShell>
      )}
    </div>
  )
}
