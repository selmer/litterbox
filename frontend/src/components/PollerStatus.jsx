import { formatDistanceToNow } from 'date-fns'

export default function PollerStatus({ healthy, generatedAt }) {
  const ago = generatedAt
    ? formatDistanceToNow(new Date(generatedAt), { addSuffix: true })
    : null

  const tooltip = healthy
    ? `Device is connected and reporting. Last update: ${ago ?? 'unknown'}.`
    : 'Device connection lost. Data may be outdated.'

  return (
    <div className="poller-status" title={tooltip}>
      <div className={`poller-dot ${healthy ? 'healthy' : 'unhealthy'}`} />
      <span>{healthy ? 'polling' : 'disconnected'}</span>
      {ago && <span style={{ color: 'var(--text-faint)' }}>· {ago}</span>}
    </div>
  )
}
