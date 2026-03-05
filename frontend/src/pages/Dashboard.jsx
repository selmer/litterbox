import { useState, useEffect, useCallback } from 'react'
import { subYears } from 'date-fns'
import { getDashboard, getWeightHistory, getVisits, getCats, createVisit } from '../api/client'
import CatCard from '../components/CatCard'
import WeightChart from '../components/WeightChart'
import VisitsList from '../components/VisitsList'
import PollerStatus from '../components/PollerStatus'

const REFRESH_INTERVAL_MS = 15000

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
  const [dateRange, setDateRange] = useState({
    fromDate: subYears(new Date(), 1),
    toDate: new Date(),
  })
  const [addingVisitForCat, setAddingVisitForCat] = useState(null)
  const [visitForm, setVisitForm] = useState({ date: '', weight_g: '', duration_seconds: '' })
  const [submitError, setSubmitError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const fetchDashboard = useCallback(async () => {
    try {
      const data = await getDashboard()
      setDashboard(data)
      setError(null)
    } catch (e) {
      setError('Could not reach the API')
    }
  }, [])

  const fetchWeightHistory = useCallback(async (range) => {
    try {
      const data = await getWeightHistory(range || dateRange)
      setWeightHistory(data)
    } catch (e) {
      console.error('Failed to fetch weight history', e)
    }
  }, [dateRange])

  const fetchInitial = useCallback(async () => {
    setLoading(true)
    try {
      const [dash, history, visits, catsData] = await Promise.all([
        getDashboard(),
        getWeightHistory(dateRange),
        getVisits({ limit: 10 }),
        getCats(),
      ])
      setDashboard(dash)
      setWeightHistory(history)
      setRecentVisits(visits)
      setCats(catsData)
    } catch (e) {
      setError('Could not reach the API')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchInitial()
  }, [fetchInitial])

  // Auto-refresh dashboard every 15 seconds
  useEffect(() => {
    const interval = setInterval(fetchDashboard, REFRESH_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [fetchDashboard])

  function handleRangeChange(newRange) {
    setDateRange(newRange)
    fetchWeightHistory(newRange)
  }

  function openAddVisit(cat) {
    setAddingVisitForCat(cat)
    setVisitForm({
      date: toLocalDateTimeString(new Date()),
      weight_g: '',
      duration_seconds: '',
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
    const duration = parseInt(visitForm.duration_seconds)
    if (!visitForm.date || isNaN(weight_g) || isNaN(duration)) {
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
      const [dash, visits] = await Promise.all([getDashboard(), getVisits({ limit: 10 })])
      setDashboard(dash)
      setRecentVisits(visits)
      closeAddVisit()
    } catch (e) {
      setSubmitError('Failed to save visit. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) return <div className="loading">Loading…</div>
  if (error) return (
    <div className="empty-state">
      <div className="empty-icon">⚠️</div>
      <p>{error}</p>
    </div>
  )

  // Active cats from dashboard + a placeholder for cats not yet active
  const activeCatIds = new Set(dashboard.cats.map(c => c.cat_id))
  const inactiveCats = cats.filter(c => !activeCatIds.has(c.id) && c.active)

  return (
    <div>
      <div className="page-header">
        <div className="flex-between">
          <div>
            <h2>Dashboard</h2>
            <p>
              {new Date().toLocaleDateString('en-GB', {
                weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
              })}
            </p>
          </div>
          <PollerStatus
            healthy={dashboard.poller_healthy}
            generatedAt={dashboard.generated_at}
          />
        </div>
      </div>

      {/* Cat cards */}
      <div className="grid-2 mb-6">
        {dashboard.cats.map(cat => {
          return <CatCard key={cat.cat_id} cat={cat} onAddVisit={openAddVisit} />
        })}
        {inactiveCats.map(cat => (
          <CatCard key={cat.id} cat={cat} isPlaceholder />
        ))}
        {/* If no cats at all yet */}
        {dashboard.cats.length === 0 && inactiveCats.length === 0 && (
          <div className="card" style={{ gridColumn: '1 / -1' }}>
            <div className="empty-state">
              <div className="empty-icon">🐱</div>
              <p>No cats added yet. Go to Cats to add one.</p>
            </div>
          </div>
        )}
      </div>

      {/* Alerts */}
      {dashboard.unidentified_visits_today > 0 && (
        <div className="alert alert-yellow mb-6">
          ⚠️ {dashboard.unidentified_visits_today} unidentified visit
          {dashboard.unidentified_visits_today > 1 ? 's' : ''} today —{' '}
          <a href="/visits">review in Visits</a>
        </div>
      )}

      {/* Weight chart */}
      <div className="mb-6">
        <WeightChart
          weightHistory={weightHistory}
          onRangeChange={handleRangeChange}
        />
      </div>

      {/* Recent visits */}
      <div>
        <div className="flex-between mb-4">
          <div className="card-label" style={{ margin: 0 }}>Recent visits</div>
          <a href="/visits" className="text-muted" style={{ fontSize: 12 }}>
            view all →
          </a>
        </div>
        <VisitsList visits={recentVisits} cats={cats} />
      </div>

      {/* Cleaning cycles today */}
      {dashboard.cleaning_cycles_today > 0 && (
        <div className="mt-4 text-muted" style={{ fontSize: 12 }}>
          🧹 {dashboard.cleaning_cycles_today} cleaning cycle
          {dashboard.cleaning_cycles_today > 1 ? 's' : ''} today
        </div>
      )}

      {/* Add visit modal */}
      {addingVisitForCat && (
        <div className="modal-overlay" onClick={closeAddVisit}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-title">Add visit</div>
            <p className="text-muted" style={{ fontSize: 13, marginBottom: 16 }}>
              Manual visit for {addingVisitForCat.cat_name || addingVisitForCat.name}
            </p>
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
                <label className="form-label">Duration (seconds)</label>
                <input
                  type="number"
                  className="form-input"
                  placeholder="e.g. 120"
                  min="1"
                  step="1"
                  value={visitForm.duration_seconds}
                  onChange={e => setVisitForm(f => ({ ...f, duration_seconds: e.target.value }))}
                  required
                />
              </div>
              {submitError && (
                <p style={{ fontSize: 12, color: 'var(--red)' }}>{submitError}</p>
              )}
              <button
                type="submit"
                className="btn btn-primary w-full"
                disabled={submitting}
              >
                {submitting ? 'Saving…' : 'Save visit'}
              </button>
            </form>
            <button
              className="btn btn-secondary w-full mt-4"
              onClick={closeAddVisit}
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
