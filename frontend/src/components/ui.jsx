export function PageHeader({ title, subtitle, actions }) {
  return (
    <div className="page-header">
      <div className="page-header__row">
        <div className="page-header__content">
          <h2>{title}</h2>
          {subtitle && <p>{subtitle}</p>}
        </div>
        {actions && <div className="page-header__actions">{actions}</div>}
      </div>
    </div>
  )
}

export function EmptyState({ icon, message, children, compact = false }) {
  return (
    <div className={`empty-state ${compact ? 'empty-state--compact' : ''}`}>
      {icon && <div className="empty-icon" aria-hidden="true">{icon}</div>}
      <p>{message}</p>
      {children && <div className="empty-state__actions">{children}</div>}
    </div>
  )
}

export function StatusBadge({ tone = 'muted', children, className = '' }) {
  return <span className={`badge badge-${tone} ${className}`.trim()}>{children}</span>
}

export function ModalShell({ title, description, children, onClose, className = '' }) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className={`modal ${className}`.trim()}
        onClick={event => event.stopPropagation()}
      >
        <div className="modal-title">{title}</div>
        {description && <p className="modal-description">{description}</p>}
        {children}
      </div>
    </div>
  )
}
