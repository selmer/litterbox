import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import * as client from '../api/client'
import Admin from './Admin'
import { ToastProvider } from '../components/Toast'
import { LanguageProvider } from '../i18n/LanguageContext'

vi.mock('../api/client', () => ({
  createBackup: vi.fn(),
  getApiErrorMessage: error => error.message || 'API error',
  restoreBackup: vi.fn(),
  validateRestoreArtifact: vi.fn(),
}))

class MockFileReader {
  readAsDataURL() {
    this.result = 'data:application/zip;base64,YmFja3Vw'
    setTimeout(() => this.onload?.(), 0)
  }
}

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
    vi.clearAllMocks()
    vi.stubGlobal('FileReader', MockFileReader)
  })

  it('groups admin tools by risk and purpose', () => {
    renderAdmin()

    expect(screen.getByRole('heading', { name: 'Preferences' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Operations' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Backup' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Danger zone' })).toBeInTheDocument()
    expect(screen.getByText(/Restoring a backup replaces the current database records/i)).toBeInTheDocument()
  })

  it('links to diagnostics as an operational tool', () => {
    renderAdmin()

    expect(screen.getByRole('heading', { name: 'Operational tools' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Diagnostics' })).toHaveAttribute('href', '/diagnostics')
  })

  it('requires a valid archive and explicit confirmation before restore', async () => {
    client.validateRestoreArtifact.mockResolvedValue({
      valid: true,
      metadata: {
        created_at: '2026-06-18T10:00:00Z',
        schema_revision: 'head',
      },
      uploads: 2,
      tables: { cats: 3, visits: 4 },
    })

    const { container } = renderAdmin()
    const input = container.querySelector('input[type="file"]')
    const file = new File(['backup'], 'backup.zip', { type: 'application/zip' })

    fireEvent.change(input, { target: { files: [file] } })

    await waitFor(() => {
      expect(client.validateRestoreArtifact).toHaveBeenCalledWith('data:application/zip;base64,YmFja3Vw')
    })

    const restoreButton = screen.getByRole('button', { name: 'Restore backup' })
    expect(restoreButton).toBeDisabled()

    fireEvent.click(screen.getByLabelText('I understand this will replace the current database and uploads.'))

    expect(restoreButton).toBeEnabled()
  })
})
