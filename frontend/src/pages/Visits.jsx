import { useState, useEffect } from 'react'
import { getApiErrorMessage, getVisits, getCats, updateVisit, deleteVisit } from '../api/client'
import VisitsList from '../components/VisitsList'
import Icon from '../components/Icon'
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
  const [pendingDelete, setPendingDelete] = useState(null)
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

  async function confirmDelete() {
    if (!pendingDelete) return
    try {
      await deleteVisit(pendingDelete.id)
      setVisits(prev => prev.filter(v => v.id !== pendingDelete.id))
      setPendingDelete(null)
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

      <div className="visits-toolbar">
        <div className="filter-group" aria-label="Visit filters">
          <button
            className={`filter-chip ${selectedCat === null ? 'active' : ''}`}
            onClick={() => selectFilter(null)}
          >
            All
          </button>
          {cats.map(cat => (
            <button
              key={cat.id}
              className={`filter-chip ${selectedCat === cat.id ? 'active' : ''}`}
              onClick={() => selectFilter(cat.id)}
            >
              {cat.name}
            </button>
          ))}
          <button
            className={`filter-chip filter-chip--warning ${selectedCat === 'unidentified' ? 'active' : ''}`}
            onClick={() => selectFilter('unidentified')}
          >
            Unidentified
          </button>
        </div>
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
        <VisitsList
          visits={visits}
          cats={cats}
          onReassign={handleReassign}
          onDelete={setPendingDelete}
          showDiagnosticsLinks
          emptyMessage={selectedCat === null ? 'No visits recorded yet' : 'No visits match this filter'}
        />
      </div>

      {(page > 0 || hasMore) && (
        <div className="pagination pagination--visits">
          <button className="btn btn-secondary btn-sm" onClick={() => setPage(p => p - 1)} disabled={page === 0}>
            Previous
          </button>
          <span className="pagination__label">
            Page {page + 1} · {page * PAGE_SIZE + 1}-{page * PAGE_SIZE + visits.length}
          </span>
          <button className="btn btn-secondary btn-sm" onClick={() => setPage(p => p + 1)} disabled={!hasMore}>
            Next
          </button>
        </div>
      )}


      {pendingDelete && (
        <ModalShell
          title="Delete visit"
          onClose={() => setPendingDelete(null)}
          description="Remove this visit from the history. This cannot be undone."
        >
          <div className="delete-visit-summary">
            <div>
              <span>Started</span>
              <strong>{new Date(pendingDelete.started_at).toLocaleString('en-GB', { dateStyle: 'medium', timeStyle: 'short' })}</strong>
            </div>
            <div>
              <span>Weight</span>
              <strong>{pendingDelete.weight_kg ? `${pendingDelete.weight_kg.toFixed(3)} kg` : '-'}</strong>
            </div>
          </div>
          <div className="modal-actions">
            <button className="btn btn-secondary" onClick={() => setPendingDelete(null)}>
              Cancel
            </button>
            <button className="btn btn-secondary text-danger" onClick={confirmDelete}>
              Delete visit
            </button>
          </div>
        </ModalShell>
      )}

      {reassigning && (
        <ModalShell
          title="Reassign visit"
          onClose={() => setReassigning(null)}
          description="Choose the cat that most likely used the litterbox for this visit."
        >
          <div className="reassign-summary">
            <div>
              <span>Started</span>
              <strong>{new Date(reassigning.started_at).toLocaleString('en-GB', { dateStyle: 'medium', timeStyle: 'short' })}</strong>
            </div>
            <div>
              <span>Weight</span>
              <strong>{reassigning.weight_kg ? `${reassigning.weight_kg.toFixed(3)} kg` : '-'}</strong>
            </div>
            <div>
              <span>Current</span>
              <strong>
                {reassigning.cat_id
                  ? cats.find(c => c.id === reassigning.cat_id)?.name ?? `Cat #${reassigning.cat_id}`
                  : 'unidentified'
                }
              </strong>
            </div>
          </div>
          <div className="reassign-options">
            {cats.map(cat => (
              <button
                key={cat.id}
                className={`btn w-full btn-align-start ${cat.id === reassigning.cat_id ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => confirmReassign(cat.id)}
              >
                <Icon name="cat" size={15} />
                {cat.name}
                {cat.reference_weight_kg && (
                  <span className="button-meta">ref: {cat.reference_weight_kg.toFixed(2)} kg</span>
                )}
              </button>
            ))}
            <button
              className="btn btn-secondary w-full btn-align-start reassign-option--visitor"
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
