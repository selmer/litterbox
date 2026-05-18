import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { getApiErrorMessage, getDiagnosticsSummary } from '../api/client'
import Icon from '../components/Icon'
import { EmptyState, PageHeader, StatusBadge } from '../components/ui'

function isCanceled(error) {
  return error?.code === 'ERR_CANCELED' || error?.name === 'CanceledError'
}

function formatDateTime(value) {
  if (!value) return '-'
  return new Date(value).toLocaleString('en-GB', { dateStyle: 'medium', timeStyle: 'medium' })
}

function formatDuration(seconds) {
  if (seconds == null) return '-'
  if (seconds < 60) return `${seconds}s`
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  if (minutes < 60) return remainingSeconds ? `${minutes}m ${remainingSeconds}s` : `${minutes}m`
  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60
  return remainingMinutes ? `${hours}h ${remainingMinutes}m` : `${hours}h`
}

function formatWeight(value) {
  return value == null ? '-' : `${Number(value).toFixed(3)} kg`
}

function JsonSnippet({ value }) {
  return <pre className="diagnostics-json">{JSON.stringify(value, null, 2)}</pre>
}

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false)

  async function copy() {
    if (!navigator.clipboard) return
    await navigator.clipboard.writeText(text)
    setCopied(true)
    window.setTimeout(() => setCopied(false), 1200)
  }

  return (
    <button className="btn btn-secondary btn-sm" onClick={copy} type="button">
      {copied ? 'Copied' : 'Copy'}
    </button>
  )
}

function EndpointRow({ endpoint }) {
  const command = `${endpoint.method} ${endpoint.path}`
  return (
    <div className="diagnostics-endpoint-row">
      <div>
        <span className="diagnostics-endpoint-row__label">{endpoint.label}</span>
        <code>{command}</code>
      </div>
      <CopyButton text={endpoint.path} />
    </div>
  )
}

function StatCard({ label, value, children }) {
  return (
    <div className="card diagnostics-stat-card">
      <span>{label}</span>
      <strong>{value}</strong>
      {children}
    </div>
  )
}

function DiagnosticsEvent({ event, highlighted }) {
  return (
    <tr className={highlighted ? 'diagnostics-row-highlight' : ''}>
      <td className="text-mono table-small">#{event.visit_id}</td>
      <td>{event.event_type}</td>
      <td className="text-mono table-small">{formatDateTime(event.recorded_at)}</td>
      <td><JsonSnippet value={event.payload} /></td>
    </tr>
  )
}

export default function Diagnostics() {
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchParams] = useSearchParams()
  const highlightedVisitId = searchParams.get('visit')

  useEffect(() => {
    const controller = new AbortController()
    async function load() {
      setLoading(true)
      setError(null)
      try {
        setSummary(await getDiagnosticsSummary({ signal: controller.signal }))
      } catch (e) {
        if (!isCanceled(e)) setError(getApiErrorMessage(e))
      } finally {
        setLoading(false)
      }
    }
    load()
    return () => controller.abort()
  }, [])

  const highlightedEvents = useMemo(() => {
    if (!summary || !highlightedVisitId) return []
    return summary.recent_diagnostics.filter(event => String(event.visit_id) === highlightedVisitId)
  }, [summary, highlightedVisitId])

  if (loading) return <div className="loading">Loading…</div>
  if (error) return <EmptyState icon={<Icon name="alert" />} message={error} />

  const pollerTone = summary.poller.healthy ? 'green' : 'yellow'
  const display = summary.display

  return (
    <div>
      <PageHeader
        title="Diagnostics"
        subtitle="Operational state for polling, visits, Tuya reconciliation and the e-paper display"
        actions={<StatusBadge tone={pollerTone}>{summary.poller.mode}</StatusBadge>}
      />

      {highlightedVisitId && (
        <div className="alert alert-yellow alert-with-icon mb-6">
          <Icon name="activity" size={16} />
          <span>
            Showing recent diagnostics for visit <strong>#{highlightedVisitId}</strong>.{' '}
            {highlightedEvents.length === 0 ? 'No recent events are in the summary window.' : `${highlightedEvents.length} event(s) highlighted below.`}
          </span>
        </div>
      )}

      <div className="diagnostics-grid mb-6">
        <StatCard label="Poller" value={summary.poller.healthy ? 'Healthy' : 'Attention'}>
          <p>Last success: {formatDateTime(summary.poller.last_successful_at)}</p>
          <p>Last attempt: {formatDateTime(summary.poller.last_attempted_at)}</p>
          {summary.poller.last_error && <p className="text-danger">{summary.poller.last_error}</p>}
        </StatCard>
        <StatCard label="Open visits" value={summary.open_visits.count}>
          <p>Oldest age: {formatDuration(summary.open_visits.oldest_age_seconds)}</p>
        </StatCard>
        <StatCard label="Report-log attempts" value={summary.reconciliation.reconciliation_attempts}>
          <p>Fetched: {summary.reconciliation.report_logs_fetched}</p>
          <p>Pending retries: {summary.reconciliation.pending_retries}</p>
        </StatCard>
        <StatCard label="Display preview" value={display.status.healthy ? 'Healthy' : 'Attention'}>
          <p>Alert: {display.alert || '-'}</p>
          <p>Generated: {formatDateTime(display.generated_at)}</p>
        </StatCard>
      </div>

      <div className="diagnostics-layout">
        <section className="card card--flush diagnostics-section">
          <div className="diagnostics-section__header">
            <h3>Open visits</h3>
          </div>
          {summary.open_visits.visits.length === 0 ? (
            <EmptyState icon={<Icon name="visits" />} message="No open visits" compact />
          ) : (
            <table className="table diagnostics-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Started</th>
                  <th>Age</th>
                  <th>Weight</th>
                  <th>Source</th>
                </tr>
              </thead>
              <tbody>
                {summary.open_visits.visits.map(visit => (
                  <tr key={visit.id}>
                    <td><Link to={`/diagnostics?visit=${visit.id}`} className="text-mono">#{visit.id}</Link></td>
                    <td className="text-mono table-small">{formatDateTime(visit.started_at)}</td>
                    <td>{formatDuration(visit.age_seconds)}</td>
                    <td>{formatWeight(visit.weight_kg)}</td>
                    <td>{visit.duration_source}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>

        <section className="card diagnostics-section diagnostics-display-preview">
          <div className="diagnostics-section__header diagnostics-section__header--plain">
            <h3>Display summary</h3>
            <code>/display/summary</code>
          </div>
          <div className="diagnostics-display-grid">
            <div><span>Status</span><strong>{display.status.label}</strong></div>
            <div><span>Latest visit</span><strong>{display.latest_visit?.cat_name || '-'}</strong></div>
            <div><span>Visits today</span><strong>{display.today.visits}</strong></div>
            <div><span>Unidentified</span><strong>{display.today.unidentified_visits}</strong></div>
          </div>
          <JsonSnippet value={{ alert: display.alert, cats: display.cats }} />
        </section>
      </div>

      <section className="card card--flush diagnostics-section mt-6">
        <div className="diagnostics-section__header">
          <h3>Recent visit diagnostics</h3>
          <code>/visits/{'{visit_id}'}/diagnostics</code>
        </div>
        {summary.recent_diagnostics.length === 0 ? (
          <EmptyState icon={<Icon name="activity" />} message="No visit diagnostics recorded yet" compact />
        ) : (
          <table className="table diagnostics-table diagnostics-events-table">
            <thead>
              <tr>
                <th>Visit</th>
                <th>Event</th>
                <th>Recorded</th>
                <th>Payload</th>
              </tr>
            </thead>
            <tbody>
              {summary.recent_diagnostics.map(event => (
                <DiagnosticsEvent
                  key={event.id}
                  event={event}
                  highlighted={highlightedVisitId && String(event.visit_id) === highlightedVisitId}
                />
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="card diagnostics-section mt-6">
        <div className="diagnostics-section__header diagnostics-section__header--plain">
          <h3>Useful endpoints</h3>
        </div>
        <div className="diagnostics-endpoint-list">
          {summary.endpoints.map(endpoint => <EndpointRow key={`${endpoint.method}-${endpoint.path}`} endpoint={endpoint} />)}
        </div>
      </section>
    </div>
  )
}
