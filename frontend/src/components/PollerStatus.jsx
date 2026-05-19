import { formatDistanceToNow } from 'date-fns'
import { nl } from 'date-fns/locale'
import { useLanguage } from '../i18n/useLanguage'

export default function PollerStatus({ healthy, generatedAt, lastSuccessfulAt, lastError }) {
  const { language, t } = useLanguage()
  const statusTime = lastSuccessfulAt || generatedAt
  const ago = statusTime
    ? formatDistanceToNow(new Date(statusTime), { addSuffix: true, locale: language === 'nl' ? nl : undefined })
    : null

  const tooltip = healthy
    ? t('poller.healthyTooltip', { ago: ago ?? t('common.unknown') })
    : t('poller.unhealthyTooltip', { message: lastError || t('poller.outdated') })

  return (
    <div className="poller-status" title={tooltip}>
      <div className={`poller-dot ${healthy ? 'healthy' : 'unhealthy'}`} />
      <span>{healthy ? t('status.polling') : t('status.disconnected')}</span>
      {ago && <span className="poller-status__time">· {ago}</span>}
    </div>
  )
}
