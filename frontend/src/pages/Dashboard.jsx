import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import {
  createVisit,
  getApiErrorMessage,
  getCats,
  getDashboard,
  getVisits,
  getWeightHistory,
} from '../api/client'
import CatCard from '../components/CatCard'
import WeightChart from '../components/WeightChart'
import { getInitialRangeLabel, getRangeDates } from '../utils/chartRanges'
import VisitsList from '../components/VisitsList'
import PollerStatus from '../components/PollerStatus'
import { useToast } from '../components/ToastContext'
import Icon from '../components/Icon'
import { EmptyState, ModalShell, PageHeader } from '../components/ui'

const REFRESH_INTERVAL_MS = 15000

function isCanceled(error) {
  return error?.code === 'ERR_CANCELED' || error?.name === 'CanceledError'
}

function toLocalDateTimeString(date) {
  const pad = n => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`
}

export default function Dashboard() {
  const [dashboard, setDashboard] = useState(null)
  const [weightHistory, setWeightHistory] = useState([])
  const [recentVisits, setRecentVisits] = useState([])
  const [cats, setCats] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [dateRange, setDateRange] = useState(() => {
    const { from, to } = getRangeDates(getInitialRangeLabel())
    return { fromDate: from, toDate: to }
  })
  const [weightLoading, setWeightLoading] = useState(false)
  const [addingVisitForCat, setAddingVisitForCat] = useState(null)
  const [visitForm, setVisitForm] = useState({ date: '', weight_g: '', duration_min: '', duration_sec: '' })
  const [submitError, setSubmitError] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const toast = useToast()

  const fetchDashboardData = useCallback(async ({ signal, initial = false } = {}) => {
    if (initial) setLoading(true)
    try {
      const [dash, history, visits, catsData] = await Promise.all([
        getDashboard({ signal }),
        getWeightHistory({ ...dateRange, signal }),
        getVisits({ limit: 10, signal }),
        getCats(false, { signal }),
      ])
      setDashboard(dash)
      setWeightHistory(history)
      setRecentVisits(visits)
      setCats(catsData)
      setError(null)
    } catch (e) {
      if (!isCanceled(e)) {
        setError(getApiErrorMessage(e))
      }
    } finally {
      if (initial) setLoading(false)
    }
  }, [dateRange])

  const fetchWeightHistory = useCallback(async (range) => {
    try {
      const data = await getWeightHistory(range || dateRange)
      setWeightHistory(data)
    } catch (e) {
      console.error('Failed to fetch weight history', e)
    }
  }, [dateRange])

  useEffect(() => {
    const controller = new AbortController()
    fetchDashboardData({ signal: controller.signal, initial: true })
    return () => controller.abort()
  }, [fetchDashboardData])

  useEffect(() => {
    const interval = setInterval(() => fetchDashboardData(), REFRESH_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [fetchDashboardData])

  async function handleRangeChange(newRange) {
    setDateRange(newRange)
    setWeightLoading(true)
    try {
      await fetchWeightHistory(newRange)
    } finally {
      setWeightLoading(false)
    }
  }

  function openAddVisit(cat) {
    setAddingVisitForCat(cat)
    setVisitForm({
      date: toLocalDateTimeString(new Date()),
      weight_g: '',
      duration_min: '',
      duration_sec: '',
    })
    setSubmitError(null)
  }

  function closeAddVisit() {
    setAddingVisitForCat(null)
    setSubmitError(null)
  }

  async function handleSubmitVisit(e) {
    e.preventDefault()
    const weight_g = parseFloat(visitForm.weight_g)
    const durationMin = parseInt(visitForm.duration_min) || 0
    const durationSec = parseInt(visitForm.duration_sec) || 0
    const duration = durationMin * 60 + durationSec
    if (!visitForm.date || isNaN(weight_g) || duration <= 0) {
      setSubmitError('Please fill in all fields with valid values.')
      return
    }
    setSubmitting(true)
    setSubmitError(null)
    try {
      const catId = addingVisitForCat.cat_id || addingVisitForCat.id
      await createVisit({
        cat_id: catId,
        started_at: new Date(visitForm.date).toISOString(),
        duration_seconds: duration,
        weight_kg: weight_g / 1000,
      })
      await fetchDashboardData()
      closeAddVisit()
      toast('Visit saved', 'success')
    } catch {
      setSubmitError('Failed to save visit. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) return <div className="loading">Loading…</div>
  if (error) return <EmptyState icon={<Icon name="alert" />} message={error} />

  const activeCatIds = new Set(dashboard.cats.map(c => c.cat_id))
  const catsWithoutVisits = cats.filter(c => !activeCatIds.has(c.id) && c.active)
  const pageDate = new Date().toLocaleDateString('en-GB', {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
  })

  return (
    <div>
      <PageHeader
        title="Dashboard"
        subtitle={pageDate}
        actions={(
          <PollerStatus
            healthy={dashboard.poller_healthy}
            generatedAt={dashboard.generated_at}
            lastSuccessfulAt={dashboard.poller_last_successful_at}
            lastError={dashboard.poller_last_error}
          />
        )}
      />

      {!dashboard.poller_healthy && (
        <div className="alert alert-red alert-with-icon mb-6">
          <Icon name="alert" size={16} />
          <span>{dashboard.poller_last_error || 'Poller is disconnected. Dashboard data may be stale.'}</span>
        </div>
      )}

      <div className="dashboard-grid mb-6">
        <div className="cat-summary-column">
          {dashboard.cats.map(cat => (
            <CatCard key={cat.cat_id} cat={cat} onAddVisit={openAddVisit} />
          ))}
          {catsWithoutVisits.map(cat => (
            <CatCard key={cat.id} cat={cat} isPlaceholder onAddVisit={openAddVisit} />
          ))}
          {cats.length === 0 && (
            <div className="card">
              <EmptyState icon={<Icon name="cat" />} message="No cats yet">
                <Link to="/cats" className="btn btn-primary">Add a cat</Link>
              </EmptyState>
            </div>
          )}
        </div>

        <WeightChart
          weightHistory={weightHistory}
          onRangeChange={handleRangeChange}
          weightLoading={weightLoading}
        />
      </div>

      {dashboard.unidentified_visits_today > 0 && (
        <div className="alert alert-yellow alert-with-icon mb-6">
          <Icon name="alert" size={16} />
          <span>
            {dashboard.unidentified_visits_today} unidentified visit
            {dashboard.unidentified_visits_today > 1 ? 's' : ''} today —{' '}
            <Link to="/visits">review in Visits</Link>
          </span>
        </div>
      )}

      <div>
        <div className="section-header">
          <div className="card-label">Recent visits</div>
          <Link to="/visits" className="section-link">view all →</Link>
        </div>
        <VisitsList visits={recentVisits} cats={cats} />
      </div>

      {dashboard.cleaning_cycles_today > 0 && (
        <div className="status-note status-note--icon">
          <Icon name="clean" size={15} />
          <span>
            {dashboard.cleaning_cycles_today} cleaning cycle
            {dashboard.cleaning_cycles_today > 1 ? 's' : ''} today
          </span>
        </div>
      )}

      {addingVisitForCat && (
        <ModalShell
          title="Add visit"
          description={`Manual visit for ${addingVisitForCat.cat_name || addingVisitForCat.name}`}
          onClose={closeAddVisit}
        >
          <form onSubmit={handleSubmitVisit} className="cat-form">
            <div className="form-field">
              <label className="form-label">Date &amp; time</label>
              <input
                type="datetime-local"
                className="form-input"
                value={visitForm.date}
                onChange={e => setVisitForm(f => ({ ...f, date: e.target.value }))}
                required
              />
            </div>
            <div className="form-field">
              <label className="form-label">Weight (g)</label>
              <input
                type="number"
                className="form-input"
                placeholder="e.g. 4520"
                min="0"
                step="1"
                value={visitForm.weight_g}
                onChange={e => setVisitForm(f => ({ ...f, weight_g: e.target.value }))}
                required
              />
            </div>
            <div className="form-field">
              <label className="form-label">Duration</label>
              <div className="form-row">
                <input
                  type="number"
                  className="form-input"
                  placeholder="min"
                  min="0"
                  step="1"
                  value={visitForm.duration_min}
                  onChange={e => setVisitForm(f => ({ ...f, duration_min: e.target.value }))}
                />
                <input
                  type="number"
                  className="form-input"
                  placeholder="sec"
                  min="0"
                  max="59"
                  step="1"
                  value={visitForm.duration_sec}
                  onChange={e => setVisitForm(f => ({ ...f, duration_sec: e.target.value }))}
                />
              </div>
            </div>
            {submitError && <p className="form-error">{submitError}</p>}
            <button type="submit" className="btn btn-primary w-full" disabled={submitting}>
              {submitting ? 'Saving…' : 'Save visit'}
            </button>
          </form>
          <button className="btn btn-secondary w-full mt-4" onClick={closeAddVisit}>
            Cancel
          </button>
        </ModalShell>
      )}
    </div>
  )
}
