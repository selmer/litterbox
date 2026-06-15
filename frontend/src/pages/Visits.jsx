import { useState, useEffect } from 'react'
import { getApiErrorMessage, getVisits, getVisitSummary, getCats, updateVisit, deleteVisit } from '../api/client'
import VisitsList from '../components/VisitsList'
import { useToast } from '../components/ToastContext'
import { useLanguage } from '../i18n/useLanguage'
import { ModalShell, PageHeader } from '../components/ui'

const PAGE_SIZE = 50
const SUMMARY_MODES = ['day', 'week', 'month']

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

function formatDuration(seconds) {
  if (!seconds) return '-'
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  if (m === 0) return `${s}s`
  return `${m}m ${s}s`
}

function formatBucketLabel(summary, mode, locale, t) {
  const start = new Date(summary.bucket_start)
  if (mode === 'day') {
    const today = new Date()
    const yesterday = new Date()
    yesterday.setDate(today.getDate() - 1)
    if (start.toDateString() === today.toDateString()) return t('visits.today')
    if (start.toDateString() === yesterday.toDateString()) return t('visits.yesterday')
    return start.toLocaleDateString(locale, { day: 'numeric', month: 'short', year: 'numeric' })
  }
  if (mode === 'week') {
    return t('visits.weekOf', { date: start.toLocaleDateString(locale, { day: 'numeric', month: 'short', year: 'numeric' }) })
  }
  return start.toLocaleDateString(locale, { month: 'long', year: 'numeric' })
}

function SummaryList({ summaries, mode, locale, t, onViewDetails, emptyMessage }) {
  if (!summaries?.length) {
    return <div className="empty-state empty-state--compact">{emptyMessage}</div>
  }

  return (
    <>
      <div className="card card--flush visits-summary-table-card">
        <table className="table visits-summary-table">
          <thead>
            <tr>
              <th>{t('field.date')}</th>
              <th>{t('visits.total')}</th>
              <th>{t('visits.byCat')}</th>
              <th>{t('visits.average')}</th>
              <th>{t('catCard.lastVisit')}</th>
              <th>{t('field.actions')}</th>
            </tr>
          </thead>
          <tbody>
            {summaries.map(summary => (
              <tr key={summary.bucket_start}>
                <td className="text-primary">{formatBucketLabel(summary, mode, locale, t)}</td>
                <td>
                  <strong>{summary.visit_count}</strong>
                  {summary.unidentified_visit_count > 0 && (
                    <span className="summary-warning">{t('visits.unidentifiedCount', { count: summary.unidentified_visit_count })}</span>
                  )}
                </td>
                <td>
                  <div className="summary-cat-list">
                    {summary.cats.map(cat => (
                      <span className="summary-cat-pill" key={`${summary.bucket_start}-${cat.cat_id ?? 'unknown'}`}>
                        {cat.cat_name || t('visits.unknownCat')}: {cat.visit_count}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="table-small">
                  {mode === 'day'
                    ? formatDuration(summary.average_duration_seconds)
                    : t('visits.averagePerDay', { count: summary.average_visits_per_day })}
                </td>
                <td className="text-mono table-small">
                  {summary.latest_visit_at ? new Date(summary.latest_visit_at).toLocaleString(locale, { dateStyle: 'medium', timeStyle: 'short' }) : '-'}
                </td>
                <td>
                  <button className="btn btn-secondary btn-sm" onClick={() => onViewDetails(summary)}>
                    {t('visits.viewDetails')}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="visit-summary-card-list" aria-label={t('visits.summaryListLabel')}>
        {summaries.map(summary => (
          <article className="visit-summary-card" key={summary.bucket_start}>
            <div className="visit-summary-card__header">
              <strong>{formatBucketLabel(summary, mode, locale, t)}</strong>
              <span>{summary.visit_count}</span>
            </div>
            <div className="summary-cat-list">
              {summary.cats.map(cat => (
                <span className="summary-cat-pill" key={`${summary.bucket_start}-${cat.cat_id ?? 'unknown'}`}>
                  {cat.cat_name || t('visits.unknownCat')}: {cat.visit_count}
                </span>
              ))}
            </div>
            <div className="visit-summary-card__meta">
              {summary.unidentified_visit_count > 0 && <span>{t('visits.unidentifiedCount', { count: summary.unidentified_visit_count })}</span>}
              <span>{mode === 'day' ? formatDuration(summary.average_duration_seconds) : t('visits.averagePerDay', { count: summary.average_visits_per_day })}</span>
            </div>
            <button className="btn btn-secondary btn-sm" onClick={() => onViewDetails(summary)}>
              {t('visits.viewDetails')}
            </button>
          </article>
        ))}
      </div>
    </>
  )
}

export default function Visits() {
  const [visits, setVisits] = useState([])
  const [summaries, setSummaries] = useState([])
  const [cats, setCats] = useState([])
  const [initialLoading, setInitialLoading] = useState(true)
  const [fetching, setFetching] = useState(false)
  const [selectedCat, setSelectedCat] = useState(null)
  const [mode, setMode] = useState('day')
  const [detailRange, setDetailRange] = useState(null)
  const [page, setPage] = useState(0)
  const [hasMore, setHasMore] = useState(false)
  const [loadError, setLoadError] = useState(null)
  const [reloadNonce, setReloadNonce] = useState(0)
  const [editingVisit, setEditingVisit] = useState(null)
  const [editForm, setEditForm] = useState(null)
  const [editError, setEditError] = useState(null)
  const [savingEdit, setSavingEdit] = useState(false)
  const [pendingDelete, setPendingDelete] = useState(null)
  const toast = useToast()
  const { locale, t } = useLanguage()
  const isDetailsMode = mode === 'details'
  const currentItems = isDetailsMode ? visits : summaries

  useEffect(() => {
    getCats().then(setCats).catch(e => {
      console.error('Failed to load cats', e)
      toast(t('visits.toast.catsFailed'))
    })
  }, [toast, t])

  useEffect(() => {
    let canceled = false
    const controller = new AbortController()

    async function fetchVisitData() {
      setFetching(true)
      setLoadError(null)
      try {
        const params = { limit: PAGE_SIZE + 1, offset: page * PAGE_SIZE, signal: controller.signal }
        if (selectedCat === 'unidentified') {
          params.unidentified = true
        } else if (selectedCat !== null) {
          params.catId = selectedCat
        }
        if (isDetailsMode && detailRange) {
          params.fromDate = new Date(detailRange.from)
          params.toDate = new Date(detailRange.to)
        }

        const result = isDetailsMode
          ? await getVisits(params)
          : await getVisitSummary({ ...params, bucket: mode })
        if (canceled) return
        setHasMore(result.length > PAGE_SIZE)
        if (isDetailsMode) {
          setVisits(result.slice(0, PAGE_SIZE))
        } else {
          setSummaries(result.slice(0, PAGE_SIZE))
        }
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
    fetchVisitData()
    return () => {
      canceled = true
      controller.abort()
    }
  }, [selectedCat, mode, detailRange, page, reloadNonce, isDetailsMode])

  function selectFilter(cat) {
    setSelectedCat(cat)
    setDetailRange(null)
    setPage(0)
  }

  function selectMode(nextMode) {
    setMode(nextMode)
    setDetailRange(null)
    setPage(0)
  }

  function viewSummaryDetails(summary) {
    setMode('details')
    setDetailRange({ from: summary.bucket_start, to: summary.bucket_end })
    setPage(0)
  }

  async function confirmDelete() {
    if (!pendingDelete) return
    try {
      await deleteVisit(pendingDelete.id)
      setVisits(prev => prev.filter(v => v.id !== pendingDelete.id))
      setPendingDelete(null)
      setReloadNonce(n => n + 1)
    } catch (e) {
      console.error('Failed to delete visit', e)
      toast(t('visits.toast.deleteFailed'))
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
      setEditError(t('visits.error.invalidEdit'))
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
      setReloadNonce(n => n + 1)
      toast(t('visits.toast.updated'), 'success')
    } catch (err) {
      setEditError(getApiErrorMessage(err))
    } finally {
      setSavingEdit(false)
    }
  }

  if (initialLoading) return <div className="loading">{t('state.loading')}</div>

  return (
    <div>
      <PageHeader title={t('visits.title')} subtitle={t('visits.subtitle')} />

      <div className="visits-toolbar">
        <div className="filter-group" aria-label={t('visits.viewModes')}>
          {SUMMARY_MODES.map(summaryMode => (
            <button
              key={summaryMode}
              className={`filter-chip ${mode === summaryMode ? 'active' : ''}`}
              onClick={() => selectMode(summaryMode)}
            >
              {t(`visits.mode.${summaryMode}`)}
            </button>
          ))}
          <button
            className={`filter-chip ${mode === 'details' ? 'active' : ''}`}
            onClick={() => selectMode('details')}
          >
            {t('visits.mode.details')}
          </button>
        </div>

        <div className="filter-group" aria-label={t('visits.filters')}>
          <button
            className={`filter-chip ${selectedCat === null ? 'active' : ''}`}
            onClick={() => selectFilter(null)}
          >
            {t('visits.all')}
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
            {t('visits.unidentified')}
          </button>
        </div>
      </div>

      {detailRange && isDetailsMode && (
        <div className="visits-detail-range">
          <span>{t('visits.detailRange', { date: new Date(detailRange.from).toLocaleDateString(locale, { dateStyle: 'medium' }) })}</span>
          <button className="btn btn-secondary btn-sm" onClick={() => setDetailRange(null)}>{t('visits.clearRange')}</button>
        </div>
      )}

      <div className={`fetch-state ${fetching ? 'is-fetching' : ''}`}>
        {loadError && (
          <div className="alert alert-yellow mb-4">
            {loadError}
            <button className="btn btn-secondary btn-sm alert__action" onClick={() => setReloadNonce(n => n + 1)}>
              {t('common.retry')}
            </button>
          </div>
        )}
        {isDetailsMode ? (
          <VisitsList
            visits={visits}
            cats={cats}
            onEdit={handleEdit}
            onDelete={setPendingDelete}
            emptyMessage={selectedCat === null ? t('visits.empty') : t('visits.emptyFilter')}
          />
        ) : (
          <SummaryList
            summaries={summaries}
            mode={mode}
            locale={locale}
            t={t}
            onViewDetails={viewSummaryDetails}
            emptyMessage={selectedCat === null ? t('visits.empty') : t('visits.emptyFilter')}
          />
        )}
      </div>

      {(page > 0 || hasMore) && (
        <div className="pagination pagination--visits">
          <button className="btn btn-secondary btn-sm" onClick={() => setPage(p => p - 1)} disabled={page === 0}>
            {t('common.previous')}
          </button>
          <span className="pagination__label">
            {t('visits.pageRange', { page: page + 1, from: page * PAGE_SIZE + 1, to: page * PAGE_SIZE + currentItems.length })}
          </span>
          <button className="btn btn-secondary btn-sm" onClick={() => setPage(p => p + 1)} disabled={!hasMore}>
            {t('common.next')}
          </button>
        </div>
      )}

      {editingVisit && editForm && (
        <ModalShell
          title={t('common.editVisit')}
          onClose={closeEdit}
          description={t('visits.editDescription', { id: editingVisit.id })}
        >
          <form onSubmit={confirmEdit} className="cat-form">
            <div className="form-field">
              <label className="form-label" htmlFor="edit-visit-cat">{t('field.cat')}</label>
              <select
                id="edit-visit-cat"
                className="form-input"
                value={editForm.cat_id}
                onChange={e => setEditForm(f => ({ ...f, cat_id: e.target.value }))}
              >
                <option value="">{t('visits.visitorOption')}</option>
                {cats.map(cat => <option key={cat.id} value={cat.id}>{cat.name}</option>)}
              </select>
            </div>
            <div className="form-field">
              <label className="form-label" htmlFor="edit-visit-started-at">{t('field.dateTime')}</label>
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
                <label className="form-label" htmlFor="edit-visit-duration-min">{t('field.minutes')}</label>
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
                <label className="form-label" htmlFor="edit-visit-duration-sec">{t('field.seconds')}</label>
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
                <label className="form-label" htmlFor="edit-visit-weight">{t('field.weightKg')}</label>
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
                <label className="form-label" htmlFor="edit-visit-confidence">{t('field.confidence')}</label>
                <select
                  id="edit-visit-confidence"
                  className="form-input"
                  value={editForm.weight_confidence}
                  onChange={e => setEditForm(f => ({ ...f, weight_confidence: e.target.value }))}
                >
                  <option value="normal">{t('status.normal')}</option>
                  <option value="suspect">{t('status.suspect')}</option>
                  <option value="ignored">{t('status.ignored')}</option>
                </select>
              </div>
            </div>
            {editError && <div className="form-error">{editError}</div>}
            <div className="modal-actions">
              <button type="button" className="btn btn-secondary" onClick={closeEdit} disabled={savingEdit}>
                {t('common.cancel')}
              </button>
              <button type="submit" className="btn btn-primary" disabled={savingEdit}>
                {savingEdit ? t('common.saving') : t('common.saveVisit')}
              </button>
            </div>
          </form>
        </ModalShell>
      )}

      {pendingDelete && (
        <ModalShell
          title={t('common.deleteVisit')}
          onClose={() => setPendingDelete(null)}
          description={t('visits.deleteDescription')}
        >
          <div className="delete-visit-summary">
            <div>
              <span>{t('field.started')}</span>
              <strong>{new Date(pendingDelete.started_at).toLocaleString(locale, { dateStyle: 'medium', timeStyle: 'short' })}</strong>
            </div>
            <div>
              <span>{t('field.weight')}</span>
              <strong>{pendingDelete.weight_kg ? `${pendingDelete.weight_kg.toFixed(3)} kg` : '-'}</strong>
            </div>
          </div>
          <div className="modal-actions">
            <button className="btn btn-secondary" onClick={() => setPendingDelete(null)}>
              {t('common.cancel')}
            </button>
            <button className="btn btn-secondary text-danger" onClick={confirmDelete}>
              {t('common.deleteVisit')}
            </button>
          </div>
        </ModalShell>
      )}
    </div>
  )
}
