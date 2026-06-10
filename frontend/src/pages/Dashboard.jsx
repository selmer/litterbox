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
import { useLanguage } from '../i18n/useLanguage'
import Icon from '../components/Icon'
import { EmptyState, ModalShell, PageHeader } from '../components/ui'

const REFRESH_INTERVAL_MS = 15000


function formatDeviceFaultLabel(fault, t) {
  if (fault?.startsWith('unknown_fault_code_')) {
    return t('dashboard.deviceFaultUnknown', { code: fault.replace('unknown_fault_code_', '') })
  }
  return t(`deviceFault.${fault}`)
}

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
  const { locale, t } = useLanguage()

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
      setSubmitError(t('dashboard.error.invalidVisit'))
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
      toast(t('dashboard.toast.visitSaved'), 'success')
    } catch {
      setSubmitError(t('dashboard.error.saveVisit'))
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) return <div className="loading">{t('state.loading')}</div>
  if (error) return <EmptyState icon={<Icon name="alert" />} message={error} />

  const activeCatIds = new Set(dashboard.cats.map(c => c.cat_id))
  const catsWithoutVisits = cats.filter(c => !activeCatIds.has(c.id) && c.active)
  const pageDate = new Date().toLocaleDateString(locale, {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
  })
  const deviceFaults = dashboard.device_faults || []
  const healthSignals = dashboard.health_signals || []
  const deviceFaultLabels = deviceFaults.map(fault => formatDeviceFaultLabel(fault, t)).join(', ')

  return (
    <div>
      <PageHeader
        title={t('dashboard.title')}
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
          <span>{dashboard.poller_last_error || t('dashboard.pollerDisconnected')}</span>
        </div>
      )}

      {deviceFaults.length > 0 && (
        <div className="alert alert-red alert-with-icon mb-6">
          <Icon name="alert" size={16} />
          <span>
            {t(deviceFaults.length === 1 ? 'dashboard.deviceFault' : 'dashboard.deviceFaults', { faults: deviceFaultLabels })}
            {' '}
            <Link to="/diagnostics">{t('dashboard.viewDiagnostics')}</Link>
          </span>
        </div>
      )}

      {healthSignals.length > 0 && (
        <section className="health-signals mb-6" aria-label={t('dashboard.healthSignals')}>
          <div className="section-header">
            <div className="card-label">{t('dashboard.healthSignals')}</div>
          </div>
          <div className="health-signals__list">
            {healthSignals.slice(0, 4).map(signal => (
              <div key={signal.id} className={'health-signal health-signal--' + signal.severity}>
                <Icon name="activity" size={16} />
                <div className="health-signal__body">
                  <div className="health-signal__message">
                    {signal.cat_name && <span>{signal.cat_name}: </span>}
                    {signal.message}
                  </div>
                  {signal.detail && <div className="health-signal__detail">{signal.detail}</div>}
                </div>
              </div>
            ))}
          </div>
        </section>
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
              <EmptyState icon={<Icon name="cat" />} message={t('dashboard.noCats')}>
                <Link to="/cats" className="btn btn-primary">{t('dashboard.addCatCta')}</Link>
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
            {t('dashboard.unidentifiedToday', {
              count: dashboard.unidentified_visits_today,
              plural: dashboard.unidentified_visits_today > 1 ? 's' : '',
            })}
            <Link to="/visits">{t('dashboard.reviewVisits')}</Link>
          </span>
        </div>
      )}

      <div>
        <div className="section-header">
          <div className="card-label">{t('dashboard.recentVisits')}</div>
          <Link to="/visits" className="section-link">{t('dashboard.viewAll')}</Link>
        </div>
        <VisitsList visits={recentVisits} cats={cats} showIds={false} />
      </div>

      {dashboard.cleaning_cycles_today > 0 && (
        <div className="status-note status-note--icon">
          <Icon name="clean" size={15} />
          <span>
            {t('dashboard.cleaningCyclesToday', {
              count: dashboard.cleaning_cycles_today,
              plural: dashboard.cleaning_cycles_today > 1 ? 's' : '',
            })}
          </span>
        </div>
      )}

      {addingVisitForCat && (
        <ModalShell
          title={t('dashboard.addVisitTitle')}
          description={t('dashboard.manualVisitFor', { name: addingVisitForCat.cat_name || addingVisitForCat.name })}
          onClose={closeAddVisit}
        >
          <form onSubmit={handleSubmitVisit} className="cat-form">
            <div className="form-field">
              <label className="form-label">{t('field.dateTime')}</label>
              <input
                type="datetime-local"
                className="form-input"
                value={visitForm.date}
                onChange={e => setVisitForm(f => ({ ...f, date: e.target.value }))}
                required
              />
            </div>
            <div className="form-field">
              <label className="form-label">{t('field.weightG')}</label>
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
              <label className="form-label">{t('field.duration')}</label>
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
              {submitting ? t('common.saving') : t('common.saveVisit')}
            </button>
          </form>
          <button className="btn btn-secondary w-full mt-4" onClick={closeAddVisit}>
            {t('common.cancel')}
          </button>
        </ModalShell>
      )}
    </div>
  )
}
