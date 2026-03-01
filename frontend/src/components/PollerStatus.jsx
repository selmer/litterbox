import { formatDistanceToNow } from 'date-fns'

export default function PollerStatus({ healthy, generatedAt }) {
  const ago = generatedAt
    ? formatDistanceToNow(new Date(generatedAt), { addSuffix: true })
    : null

  return (
    <div className="poller-status">
      <div className={`poller-dot ${healthy ? 'healthy' : 'unhealthy'}`} />
      <span>{healthy ? 'polling' : 'disconnected'}</span>
      {ago && <span style={{ color: 'var(--text-faint)' }}>· {ago}</span>}
    </div>
  )
}
