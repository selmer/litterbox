import { useState, useEffect, useCallback } from 'react'
import { subYears } from 'date-fns'
import { getDashboard, getWeightHistory, getVisits, getCats } from '../api/client'
import CatCard from '../components/CatCard'
import WeightChart from '../components/WeightChart'
import VisitsList from '../components/VisitsList'
import PollerStatus from '../components/PollerStatus'

const REFRESH_INTERVAL_MS = 15000

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
          return <CatCard key={cat.cat_id} cat={cat} />
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
    </div>
  )
}
