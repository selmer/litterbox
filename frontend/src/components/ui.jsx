import { useEffect, useId, useRef } from 'react'
import Icon from './Icon'
import { useLanguage } from '../i18n/useLanguage'

const FOCUSABLE_SELECTOR = [
  'a[href]',
  'button:not([disabled])',
  'textarea:not([disabled])',
  'input:not([disabled])',
  'select:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(',')

function isVisibleFocusable(element) {
  if (element.hasAttribute('disabled') || element.getAttribute('aria-hidden') === 'true') return false
  if (element.type === 'hidden' || element.hidden) return false
  const style = window.getComputedStyle?.(element)
  return style?.display !== 'none' && style?.visibility !== 'hidden'
}

function getFocusableElements(container) {
  if (!container) return []
  return Array.from(container.querySelectorAll(FOCUSABLE_SELECTOR)).filter(isVisibleFocusable)
}

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
  const { t } = useLanguage()
  const modalRef = useRef(null)
  const previouslyFocusedRef = useRef(null)
  const titleId = useId()
  const descriptionId = useId()

  useEffect(() => {
    previouslyFocusedRef.current = document.activeElement
    const modal = modalRef.current
    const focusable = getFocusableElements(modal)
    const initialFocusTarget = focusable[0] || modal
    initialFocusTarget?.focus()

    return () => {
      const previous = previouslyFocusedRef.current
      if (previous && document.contains(previous) && typeof previous.focus === 'function') {
        previous.focus()
      }
    }
  }, [])

  function handleKeyDown(event) {
    if (event.key === 'Escape') {
      event.stopPropagation()
      onClose?.()
      return
    }

    if (event.key !== 'Tab') return

    const focusable = getFocusableElements(modalRef.current)
    if (focusable.length === 0) {
      event.preventDefault()
      modalRef.current?.focus()
      return
    }

    const first = focusable[0]
    const last = focusable[focusable.length - 1]

    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault()
      last.focus()
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault()
      first.focus()
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        ref={modalRef}
        className={`modal ${className}`.trim()}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={description ? descriptionId : undefined}
        tabIndex={-1}
        onClick={event => event.stopPropagation()}
        onKeyDown={handleKeyDown}
      >
        <div className="modal-header">
          <div className="modal-title" id={titleId}>{title}</div>
          <button
            type="button"
            className="modal-close-btn"
            onClick={onClose}
            aria-label={t('common.closeDialog')}
          >
            <Icon name="close" size={16} />
          </button>
        </div>
        {description && <p className="modal-description" id={descriptionId}>{description}</p>}
        {children}
      </div>
    </div>
  )
}
