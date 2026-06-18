import { createContext, useContext, useEffect, useId, useRef, useState } from 'react'
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

const ActionMenuContext = createContext({ closeMenu: () => {} })

export function ActionMenu({ label, children, className = '' }) {
  const [open, setOpen] = useState(false)
  const menuRef = useRef(null)
  const triggerRef = useRef(null)

  function closeMenu({ restoreFocus = true } = {}) {
    setOpen(false)
    if (restoreFocus) triggerRef.current?.focus()
  }

  useEffect(() => {
    if (!open) return undefined

    function handlePointerDown(event) {
      if (!menuRef.current?.contains(event.target)) {
        closeMenu({ restoreFocus: false })
      }
    }

    document.addEventListener('pointerdown', handlePointerDown)
    return () => document.removeEventListener('pointerdown', handlePointerDown)
  }, [open])

  function handleKeyDown(event) {
    if (event.key === 'Escape') {
      event.preventDefault()
      closeMenu()
    }
  }

  return (
    <div ref={menuRef} className={`action-menu ${className}`.trim()} onKeyDown={handleKeyDown}>
      <button
        ref={triggerRef}
        type="button"
        className="btn btn-secondary btn-sm action-menu__trigger"
        aria-label={label}
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen(current => !current)}
      >
        <Icon name="moreHorizontal" size={16} />
      </button>
      {open && (
        <div className="action-menu__menu">
          <ActionMenuContext.Provider value={{ closeMenu }}>
            {children}
          </ActionMenuContext.Provider>
        </div>
      )}
    </div>
  )
}

export function ActionMenuItem({ children, href, onClick, danger = false }) {
  const { closeMenu } = useContext(ActionMenuContext)
  const className = `action-menu__item ${danger ? 'action-menu__item--danger' : ''}`.trim()

  function handleClick(event) {
    onClick?.(event)
    closeMenu({ restoreFocus: false })
  }

  if (href) {
    return <a className={className} href={href} onClick={handleClick}>{children}</a>
  }

  return (
    <button type="button" className={className} onClick={handleClick}>
      {children}
    </button>
  )
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
