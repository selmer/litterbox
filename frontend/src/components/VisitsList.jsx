import { format } from 'date-fns'
import { enGB, nl } from 'date-fns/locale'
import Icon from './Icon'
import { EmptyState, StatusBadge } from './ui'
import { useLanguage } from '../i18n/LanguageContext'

function formatDuration(seconds) {
  if (!seconds) return '-'
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  if (m === 0) return `${s}s`
  return `${m}m ${s}s`
}

function IdentificationBadge({ identifiedBy, catId, t }) {
  if (!catId) return <StatusBadge tone="yellow">{t('status.unidentified')}</StatusBadge>
  if (identifiedBy === 'manual') return <StatusBadge tone="accent">{t('status.manual')}</StatusBadge>
  return <StatusBadge tone="green">{t('status.auto')}</StatusBadge>
}

function ConfidenceBadge({ confidence, t }) {
  if (confidence === 'ignored') return <StatusBadge tone="muted">{t('status.ignored')}</StatusBadge>
  if (confidence === 'suspect') return <StatusBadge tone="yellow">{t('status.suspect')}</StatusBadge>
  return null
}

function getCatName(visit, catMap, t) {
  if (!visit.cat_id) return t('visits.unknownCat')
  return catMap[visit.cat_id]?.name || `Cat #${visit.cat_id}`
}

function VisitActions({ visit, onEdit, onDelete, showDiagnosticsLink, t }) {
  if (!onEdit && !onDelete && !showDiagnosticsLink) return null

  return (
    <details className="visit-actions">
      <summary className="btn btn-secondary btn-sm visit-actions__trigger">
        {t('common.edit')}
      </summary>
      <div className="visit-actions__menu">
        {onEdit && (
          <button className="visit-actions__item" onClick={() => onEdit(visit)}>
            {t('common.editVisit')}
          </button>
        )}
        {showDiagnosticsLink && (
          <a className="visit-actions__item" href={`/diagnostics?visit=${visit.id}`}>
            {t('nav.diagnostics')}
          </a>
        )}
        {onDelete && (
          <button className="visit-actions__item text-danger" onClick={() => onDelete(visit)}>
            {t('common.delete')}
          </button>
        )}
      </div>
    </details>
  )
}

function VisitMobileCard({ visit, catMap, onEdit, onDelete, showId = true, showDiagnosticsLink = false, t, dateLocale }) {
  const catName = getCatName(visit, catMap, t)

  return (
    <article className="visit-card">
      <div className="visit-card__header">
        <div className="visit-card__cat">
          <span className={`visit-card__marker ${visit.cat_id ? '' : 'is-unidentified'}`} />
          <span>{catName}</span>
        </div>
        <div className="visit-card__meta">
          {showId && <span className="visit-id text-mono">#{visit.id}</span>}
          <IdentificationBadge identifiedBy={visit.identified_by} catId={visit.cat_id} t={t} />
        </div>
      </div>
      <dl className="visit-card__details">
        <div>
          <dt>{t('field.started')}</dt>
          <dd>{format(new Date(visit.started_at), 'dd MMM, HH:mm', { locale: dateLocale })}</dd>
        </div>
        <div>
          <dt>{t('field.duration')}</dt>
          <dd>{formatDuration(visit.duration_seconds)}</dd>
        </div>
        <div>
          <dt>{t('field.weight')}</dt>
          <dd>
            {visit.weight_kg ? `${visit.weight_kg.toFixed(3)} kg` : '-'}
            <ConfidenceBadge confidence={visit.weight_confidence} t={t} />
          </dd>
        </div>
      </dl>
      <VisitActions visit={visit} onEdit={onEdit} onDelete={onDelete} showDiagnosticsLink={showDiagnosticsLink} t={t} />
    </article>
  )
}

export default function VisitsList({ visits, cats = [], onEdit, onDelete, emptyMessage, showIds = true, showDiagnosticsLinks = false }) {
  const { language, t } = useLanguage()
  const dateLocale = language === 'nl' ? nl : enGB
  const catMap = Object.fromEntries(cats.map(c => [c.id, c]))
  const resolvedEmptyMessage = emptyMessage || t('visits.empty')

  if (!visits?.length) {
    return <EmptyState icon={<Icon name="cat" />} message={resolvedEmptyMessage} compact />
  }

  return (
    <>
      <div className="card card--flush visits-table-card">
        <table className="table visits-table">
          <colgroup>
            {showIds && <col className="visits-table__id-col" />}
            <col className="visits-table__cat-col" />
            <col className="visits-table__started-col" />
            <col className="visits-table__duration-col" />
            <col className="visits-table__weight-col" />
            <col className="visits-table__source-col" />
            {(onEdit || onDelete || showDiagnosticsLinks) && <col className="visits-table__actions-col" />}
          </colgroup>
          <thead>
            <tr>
              {showIds && <th>ID</th>}
              <th>{t('field.cat')}</th>
              <th>{t('field.started')}</th>
              <th>{t('field.duration')}</th>
              <th>{t('field.weight')}</th>
              <th>{t('field.source')}</th>
              {(onEdit || onDelete || showDiagnosticsLinks) && <th>{t('field.actions')}</th>}
            </tr>
          </thead>
          <tbody>
            {visits.map(visit => (
              <tr key={visit.id} className={`visit-row ${visit.cat_id ? '' : 'visit-row--unidentified'}`}>
                {showIds && <td className="visit-id text-mono table-small">#{visit.id}</td>}
                <td className="visit-cat text-primary">
                  {getCatName(visit, catMap, t)}
                </td>
                <td className="text-mono table-small">
                  {format(new Date(visit.started_at), 'dd MMM, HH:mm', { locale: dateLocale })}
                </td>
                <td>{formatDuration(visit.duration_seconds)}</td>
                <td className="text-primary">
                  {visit.weight_kg ? `${visit.weight_kg.toFixed(3)} kg` : '-'}
                  <ConfidenceBadge confidence={visit.weight_confidence} t={t} />
                </td>
                <td>
                  <IdentificationBadge identifiedBy={visit.identified_by} catId={visit.cat_id} t={t} />
                </td>
                {(onEdit || onDelete || showDiagnosticsLinks) && (
                  <td>
                    <VisitActions visit={visit} onEdit={onEdit} onDelete={onDelete} showDiagnosticsLink={showDiagnosticsLinks} t={t} />
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="visit-card-list" aria-label={t('visits.listLabel')}>
        {visits.map(visit => (
          <VisitMobileCard
            key={visit.id}
            visit={visit}
            catMap={catMap}
            onEdit={onEdit}
            onDelete={onDelete}
            showId={showIds}
            showDiagnosticsLink={showDiagnosticsLinks}
            t={t}
            dateLocale={dateLocale}
          />
        ))}
      </div>
    </>
  )
}
