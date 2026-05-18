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

function toLocalDateTimeString(value) {
  const date = new Date(value)
  const pad = n => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function visitToEditForm(visit) {
  const duration = visit.duration_seconds || 0
  return {
    cat_id: visit.cat_id ? String(visit.cat_id) : '',
    started_at: toLocalDateTimeString(visit.started_at),
    duration_min: String(Math.floor(duration / 60)),
    duration_sec: String(duration % 60),
    weight_kg: visit.weight_kg == null ? '' : String(visit.weight_kg),
    weight_confidence: visit.weight_confidence || 'normal',
  }
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
  const [editingVisit, setEditingVisit] = useState(null)
  const [editForm, setEditForm] = useState(null)
  const [editError, setEditError] = useState(null)
  const [savingEdit, setSavingEdit] = useState(false)
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

  function handleEdit(visit) {
    setEditingVisit(visit)
    setEditForm(visitToEditForm(visit))
    setEditError(null)
  }

  function closeEdit() {
    setEditingVisit(null)
    setEditForm(null)
    setEditError(null)
    setSavingEdit(false)
  }

  async function confirmEdit(e) {
    e.preventDefault()
    if (!editingVisit || !editForm) return

    const durationMin = parseInt(editForm.duration_min, 10) || 0
    const durationSec = parseInt(editForm.duration_sec, 10) || 0
    const duration = durationMin * 60 + durationSec
    const weight = parseFloat(editForm.weight_kg)
    if (!editForm.started_at || duration <= 0 || Number.isNaN(weight) || weight <= 0) {
      setEditError('Please enter a valid date, duration and weight.')
      return
    }

    setSavingEdit(true)
    setEditError(null)
    try {
      const payload = {
        cat_id: editForm.cat_id ? Number(editForm.cat_id) : null,
        started_at: new Date(editForm.started_at).toISOString(),
        duration_seconds: duration,
        weight_kg: weight,
        weight_confidence: editForm.weight_confidence,
      }
      const updated = await updateVisit(editingVisit.id, payload)
      setVisits(prev => prev.map(v => v.id === updated.id ? updated : v))
      closeEdit()
      toast('Visit updated', 'success')
    } catch (err) {
      setEditError(getApiErrorMessage(err))
    } finally {
      setSavingEdit(false)
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
          onEdit={handleEdit}
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


      {editingVisit && editForm && (
        <ModalShell
          title="Edit visit"
          onClose={closeEdit}
          description={`Visit #${editingVisit.id}`}
        >
          <form onSubmit={confirmEdit} className="cat-form">
            <div className="form-field">
              <label className="form-label" htmlFor="edit-visit-cat">Cat</label>
              <select
                id="edit-visit-cat"
                className="form-input"
                value={editForm.cat_id}
                onChange={e => setEditForm(f => ({ ...f, cat_id: e.target.value }))}
              >
                <option value="">Unidentified / visitor</option>
                {cats.map(cat => <option key={cat.id} value={cat.id}>{cat.name}</option>)}
              </select>
            </div>
            <div className="form-field">
              <label className="form-label" htmlFor="edit-visit-started-at">Date &amp; time</label>
              <input
                id="edit-visit-started-at"
                type="datetime-local"
                className="form-input"
                value={editForm.started_at}
                onChange={e => setEditForm(f => ({ ...f, started_at: e.target.value }))}
                required
              />
            </div>
            <div className="form-row">
              <div className="form-field">
                <label className="form-label" htmlFor="edit-visit-duration-min">Minutes</label>
                <input
                  id="edit-visit-duration-min"
                  type="number"
                  className="form-input"
                  min="0"
                  value={editForm.duration_min}
                  onChange={e => setEditForm(f => ({ ...f, duration_min: e.target.value }))}
                />
              </div>
              <div className="form-field">
                <label className="form-label" htmlFor="edit-visit-duration-sec">Seconds</label>
                <input
                  id="edit-visit-duration-sec"
                  type="number"
                  className="form-input"
                  min="0"
                  max="59"
                  value={editForm.duration_sec}
                  onChange={e => setEditForm(f => ({ ...f, duration_sec: e.target.value }))}
                />
              </div>
            </div>
            <div className="form-row">
              <div className="form-field">
                <label className="form-label" htmlFor="edit-visit-weight">Weight (kg)</label>
                <input
                  id="edit-visit-weight"
                  type="number"
                  className="form-input"
                  min="0"
                  step="0.001"
                  value={editForm.weight_kg}
                  onChange={e => setEditForm(f => ({ ...f, weight_kg: e.target.value }))}
                  required
                />
              </div>
              <div className="form-field">
                <label className="form-label" htmlFor="edit-visit-confidence">Confidence</label>
                <select
                  id="edit-visit-confidence"
                  className="form-input"
                  value={editForm.weight_confidence}
                  onChange={e => setEditForm(f => ({ ...f, weight_confidence: e.target.value }))}
                >
                  <option value="normal">Normal</option>
                  <option value="suspect">Suspect</option>
                  <option value="ignored">Ignored</option>
                </select>
              </div>
            </div>
            {editError && <div className="form-error">{editError}</div>}
            <div className="modal-actions">
              <button type="button" className="btn btn-secondary" onClick={closeEdit} disabled={savingEdit}>
                Cancel
              </button>
              <button type="submit" className="btn btn-primary" disabled={savingEdit}>
                {savingEdit ? 'Saving…' : 'Save visit'}
              </button>
            </div>
          </form>
        </ModalShell>
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
