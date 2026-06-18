import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { useState } from 'react'
import { ModalShell } from './ui'

function BasicModal({ onClose = () => {} }) {
  return (
    <ModalShell title="Edit visit" description="Visit #12" onClose={onClose}>
      <button>Cancel</button>
      <button>Save</button>
    </ModalShell>
  )
}

describe('ModalShell', () => {
  it('exposes dialog semantics with title and description', () => {
    render(<BasicModal />)

    const dialog = screen.getByRole('dialog', { name: 'Edit visit' })
    expect(dialog).toHaveAttribute('aria-modal', 'true')
    expect(dialog).toHaveAccessibleDescription('Visit #12')
  })

  it('shows a close button that closes the modal', () => {
    const onClose = vi.fn()
    render(<BasicModal onClose={onClose} />)

    fireEvent.click(screen.getByRole('button', { name: 'Close dialog' }))

    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('closes with Escape', () => {
    const onClose = vi.fn()
    render(<BasicModal onClose={onClose} />)

    fireEvent.keyDown(screen.getByRole('dialog', { name: 'Edit visit' }), { key: 'Escape' })

    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('moves focus into the modal and traps tab focus at the edges', () => {
    render(<BasicModal />)

    const closeButton = screen.getByRole('button', { name: 'Close dialog' })
    const cancelButton = screen.getByRole('button', { name: 'Cancel' })
    const saveButton = screen.getByRole('button', { name: 'Save' })
    const dialog = screen.getByRole('dialog', { name: 'Edit visit' })

    expect(closeButton).toHaveFocus()

    fireEvent.keyDown(dialog, { key: 'Tab', shiftKey: true })
    expect(saveButton).toHaveFocus()

    fireEvent.keyDown(dialog, { key: 'Tab' })
    expect(closeButton).toHaveFocus()

    cancelButton.focus()
    expect(cancelButton).toHaveFocus()
  })

  it('restores focus to the previously focused trigger when closed', () => {
    function ModalTrigger() {
      const [open, setOpen] = useState(false)
      return (
        <>
          <button onClick={() => setOpen(true)}>Open modal</button>
          {open && <BasicModal onClose={() => setOpen(false)} />}
        </>
      )
    }

    render(<ModalTrigger />)
    const trigger = screen.getByRole('button', { name: 'Open modal' })
    trigger.focus()
    fireEvent.click(trigger)

    fireEvent.click(screen.getByRole('button', { name: 'Close dialog' }))

    expect(trigger).toHaveFocus()
  })
})
