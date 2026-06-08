import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Admin from './Admin'
import { ToastProvider } from '../components/Toast'
import { LanguageProvider } from '../i18n/LanguageContext'

vi.mock('../api/client', () => ({
  createBackup: vi.fn(),
  getApiErrorMessage: error => error.message || 'API error',
  restoreBackup: vi.fn(),
  validateRestoreArtifact: vi.fn(),
}))

function renderAdmin() {
  return render(
    <MemoryRouter>
      <LanguageProvider>
        <ToastProvider>
          <Admin />
        </ToastProvider>
      </LanguageProvider>
    </MemoryRouter>
  )
}

describe('Admin page', () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  it('links to diagnostics as an operational tool', () => {
    renderAdmin()

    expect(screen.getByRole('heading', { name: 'Operational tools' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Diagnostics' })).toHaveAttribute('href', '/diagnostics')
  })
})
