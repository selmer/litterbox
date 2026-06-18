import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { useState } from 'react'
import { ActionMenu, ActionMenuItem, ModalShell } from './ui'

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


describe('ActionMenu', () => {
  it('uses an accessible icon trigger and closes after action selection', () => {
    const onEdit = vi.fn()
    render(
      <ActionMenu label="Actions for visit #12">
        <ActionMenuItem onClick={onEdit}>Edit visit</ActionMenuItem>
        <ActionMenuItem danger>Delete</ActionMenuItem>
      </ActionMenu>
    )

    const trigger = screen.getByRole('button', { name: 'Actions for visit #12' })
    fireEvent.click(trigger)
    expect(trigger).toHaveAttribute('aria-expanded', 'true')

    fireEvent.click(screen.getByRole('button', { name: 'Edit visit' }))

    expect(onEdit).toHaveBeenCalledTimes(1)
    expect(trigger).toHaveAttribute('aria-expanded', 'false')
  })

  it('closes with Escape and restores focus to the trigger', () => {
    render(
      <ActionMenu label="Actions for Mochi">
        <ActionMenuItem>Deactivate</ActionMenuItem>
      </ActionMenu>
    )

    const trigger = screen.getByRole('button', { name: 'Actions for Mochi' })
    const menu = trigger.closest('.action-menu')
    fireEvent.click(trigger)
    expect(trigger).toHaveAttribute('aria-expanded', 'true')

    fireEvent.keyDown(menu, { key: 'Escape' })

    expect(trigger).toHaveAttribute('aria-expanded', 'false')
    expect(trigger).toHaveFocus()
  })
})
