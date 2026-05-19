import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { getApiErrorMessage, getDiagnosticsSummary } from '../api/client'
import Icon from '../components/Icon'
import { EmptyState, PageHeader, StatusBadge } from '../components/ui'
import { useLanguage } from '../i18n/useLanguage'

function isCanceled(error) {
  return error?.code === 'ERR_CANCELED' || error?.name === 'CanceledError'
}

function formatDateTime(value, locale) {
  if (!value) return '-'
  return new Date(value).toLocaleString(locale, { dateStyle: 'medium', timeStyle: 'medium' })
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

function CopyButton({ text, t }) {
  const [copied, setCopied] = useState(false)

  async function copy() {
    if (!navigator.clipboard) return
    await navigator.clipboard.writeText(text)
    setCopied(true)
    window.setTimeout(() => setCopied(false), 1200)
  }

  return (
    <button className="btn btn-secondary btn-sm" onClick={copy} type="button">
      {copied ? t('diagnostics.copied') : t('common.copy')}
    </button>
  )
}

function EndpointRow({ endpoint, t }) {
  const command = `${endpoint.method} ${endpoint.path}`
  return (
    <div className="diagnostics-endpoint-row">
      <div>
        <span className="diagnostics-endpoint-row__label">{endpoint.label}</span>
        <code>{command}</code>
      </div>
      <CopyButton text={endpoint.path} t={t} />
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

function DiagnosticsEvent({ event, highlighted, locale }) {
  return (
    <tr className={highlighted ? 'diagnostics-row-highlight' : ''}>
      <td className="text-mono table-small">#{event.visit_id}</td>
      <td>{event.event_type}</td>
      <td className="text-mono table-small">{formatDateTime(event.recorded_at, locale)}</td>
      <td><JsonSnippet value={event.payload} /></td>
    </tr>
  )
}

export default function Diagnostics() {
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchParams] = useSearchParams()
  const { locale, t } = useLanguage()
  const highlightedVisitId = searchParams.get('visit')

  useEffect(() => {
    const controller = new AbortController()
    async function load() {
      setLoading(true)
      setError(null)
      try {
        setSummary(await getDiagnosticsSummary({ signal: controller.signal }))
      } catch (e) {
        if (!isCanceled(e)) setError(getApiErrorMessage(e) || e?.message || t('diagnostics.unavailable'))
      } finally {
        setLoading(false)
      }
    }
    load()
    return () => controller.abort()
  }, [t])

  const highlightedEvents = useMemo(() => {
    if (!summary || !highlightedVisitId) return []
    return summary.recent_diagnostics.filter(event => String(event.visit_id) === highlightedVisitId)
  }, [summary, highlightedVisitId])

  if (loading) return <div className="loading">{t('state.loading')}</div>
  if (error) return <EmptyState icon={<Icon name="alert" />} message={error} />
  if (!summary) return <EmptyState icon={<Icon name="alert" />} message={t('diagnostics.unavailable')} />

  const pollerTone = summary.poller.healthy ? 'green' : 'yellow'
  const display = summary.display

  return (
    <div>
      <PageHeader
        title={t('diagnostics.title')}
        subtitle={t('diagnostics.subtitle')}
        actions={<StatusBadge tone={pollerTone}>{summary.poller.mode}</StatusBadge>}
      />

      {highlightedVisitId && (
        <div className="alert alert-yellow alert-with-icon mb-6">
          <Icon name="activity" size={16} />
          <span>
            {t('diagnostics.showingVisit')} <strong>#{highlightedVisitId}</strong>.{' '}
            {highlightedEvents.length === 0 ? t('diagnostics.noRecentEvents') : t('diagnostics.eventsHighlighted', { count: highlightedEvents.length })}
          </span>
        </div>
      )}

      <div className="diagnostics-grid mb-6">
        <StatCard label={t('diagnostics.poller')} value={summary.poller.healthy ? t('diagnostics.healthy') : t('diagnostics.attention')}>
          <p>{t('diagnostics.lastSuccess')}: {formatDateTime(summary.poller.last_successful_at, locale)}</p>
          <p>{t('diagnostics.lastAttempt')}: {formatDateTime(summary.poller.last_attempted_at, locale)}</p>
          {summary.poller.last_error && <p className="text-danger">{summary.poller.last_error}</p>}
        </StatCard>
        <StatCard label={t('diagnostics.openVisits')} value={summary.open_visits.count}>
          <p>{t('diagnostics.oldestAge')}: {formatDuration(summary.open_visits.oldest_age_seconds)}</p>
        </StatCard>
        <StatCard label={t('diagnostics.reportLogAttempts')} value={summary.reconciliation.reconciliation_attempts}>
          <p>{t('diagnostics.fetched')}: {summary.reconciliation.report_logs_fetched}</p>
          <p>{t('diagnostics.pendingRetries')}: {summary.reconciliation.pending_retries}</p>
        </StatCard>
        <StatCard label={t('diagnostics.displayPreview')} value={display.status.healthy ? t('diagnostics.healthy') : t('diagnostics.attention')}>
          <p>{t('diagnostics.alert')}: {display.alert || '-'}</p>
          <p>{t('diagnostics.generated')}: {formatDateTime(display.generated_at, locale)}</p>
        </StatCard>
      </div>

      <div className="diagnostics-layout">
        <section className="card card--flush diagnostics-section">
          <div className="diagnostics-section__header">
            <h3>{t('diagnostics.openVisits')}</h3>
          </div>
          {summary.open_visits.visits.length === 0 ? (
            <EmptyState icon={<Icon name="visits" />} message={t('diagnostics.noOpenVisits')} compact />
          ) : (
            <table className="table diagnostics-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>{t('field.started')}</th>
                  <th>{t('field.duration')}</th>
                  <th>{t('field.weight')}</th>
                  <th>{t('field.source')}</th>
                </tr>
              </thead>
              <tbody>
                {summary.open_visits.visits.map(visit => (
                  <tr key={visit.id}>
                    <td><Link to={`/diagnostics?visit=${visit.id}`} className="text-mono">#{visit.id}</Link></td>
                    <td className="text-mono table-small">{formatDateTime(visit.started_at, locale)}</td>
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
            <h3>{t('diagnostics.displaySummary')}</h3>
            <code>/display/summary</code>
          </div>
          <div className="diagnostics-display-grid">
            <div><span>{t('diagnostics.status')}</span><strong>{display.status.label}</strong></div>
            <div><span>{t('diagnostics.latestVisit')}</span><strong>{display.latest_visit?.cat_name || '-'}</strong></div>
            <div><span>{t('catCard.visitsToday')}</span><strong>{display.today.visits}</strong></div>
            <div><span>{t('diagnostics.unidentified')}</span><strong>{display.today.unidentified_visits}</strong></div>
          </div>
          <JsonSnippet value={{ alert: display.alert, cats: display.cats }} />
        </section>
      </div>

      <section className="card card--flush diagnostics-section mt-6">
        <div className="diagnostics-section__header">
          <h3>{t('diagnostics.recentVisitDiagnostics')}</h3>
          <code>/visits/{'{visit_id}'}/diagnostics</code>
        </div>
        {summary.recent_diagnostics.length === 0 ? (
          <EmptyState icon={<Icon name="activity" />} message={t('diagnostics.none')} compact />
        ) : (
          <table className="table diagnostics-table diagnostics-events-table">
            <thead>
              <tr>
                <th>{t('diagnostics.visit')}</th>
                <th>{t('diagnostics.event')}</th>
                <th>{t('diagnostics.recorded')}</th>
                <th>{t('diagnostics.payload')}</th>
              </tr>
            </thead>
            <tbody>
              {summary.recent_diagnostics.map(event => (
                <DiagnosticsEvent
                  key={event.id}
                  event={event}
                  highlighted={highlightedVisitId && String(event.visit_id) === highlightedVisitId}
                  locale={locale}
                />
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="card diagnostics-section mt-6">
        <div className="diagnostics-section__header diagnostics-section__header--plain">
          <h3>{t('diagnostics.usefulEndpoints')}</h3>
        </div>
        <div className="diagnostics-endpoint-list">
          {summary.endpoints.map(endpoint => <EndpointRow key={`${endpoint.method}-${endpoint.path}`} endpoint={endpoint} t={t} />)}
        </div>
      </section>
    </div>
  )
}
