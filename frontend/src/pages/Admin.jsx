import { useMemo, useRef, useState } from 'react'
import {
  createBackup,
  getApiErrorMessage,
  restoreBackup,
  validateRestoreArtifact,
} from '../api/client'
import Icon from '../components/Icon'
import { useToast } from '../components/ToastContext'
import { EmptyState, PageHeader, StatusBadge } from '../components/ui'

function fileToDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.onerror = () => reject(reader.error)
    reader.readAsDataURL(file)
  })
}

function formatDateTime(value) {
  if (!value) return '-'
  return new Date(value).toLocaleString('en-GB', { dateStyle: 'medium', timeStyle: 'medium' })
}

function formatTableName(name) {
  return name.replaceAll('_', ' ')
}

function ValidationSummary({ validation }) {
  const tableEntries = Object.entries(validation.tables || {}).sort(([a], [b]) => a.localeCompare(b))
  return (
    <div className="admin-validation">
      <div className="admin-validation__meta">
        <div>
          <span>Created</span>
          <strong>{formatDateTime(validation.metadata?.created_at)}</strong>
        </div>
        <div>
          <span>Schema</span>
          <strong>{validation.metadata?.schema_revision || 'unknown'}</strong>
        </div>
        <div>
          <span>Uploads</span>
          <strong>{validation.uploads}</strong>
        </div>
      </div>
      <div className="admin-table-counts">
        {tableEntries.map(([table, count]) => (
          <div key={table}>
            <span>{formatTableName(table)}</span>
            <strong>{count}</strong>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function Admin() {
  const toast = useToast()
  const fileInputRef = useRef(null)
  const [backupLoading, setBackupLoading] = useState(false)
  const [restoreLoading, setRestoreLoading] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)
  const [archiveData, setArchiveData] = useState(null)
  const [validation, setValidation] = useState(null)
  const [confirmRestore, setConfirmRestore] = useState(false)

  const restoreReady = useMemo(() => Boolean(archiveData && validation?.valid && confirmRestore), [archiveData, validation, confirmRestore])

  async function handleBackup() {
    setBackupLoading(true)
    try {
      const response = await createBackup()
      const url = window.URL.createObjectURL(response.data)
      const contentDisposition = response.headers?.['content-disposition'] || ''
      const filename = contentDisposition.match(/filename="([^"]+)"/)?.[1] || 'litterbox-backup.zip'
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
      toast('Backup download started', 'success')
    } catch (error) {
      toast(getApiErrorMessage(error), 'error')
    } finally {
      setBackupLoading(false)
    }
  }

  async function handleFileChange(event) {
    const file = event.target.files?.[0]
    setSelectedFile(file || null)
    setArchiveData(null)
    setValidation(null)
    setConfirmRestore(false)
    if (!file) return

    setRestoreLoading(true)
    try {
      const dataUrl = await fileToDataUrl(file)
      const result = await validateRestoreArtifact(dataUrl)
      setArchiveData(dataUrl)
      setValidation(result)
      toast('Backup archive validated', 'success')
    } catch (error) {
      toast(getApiErrorMessage(error), 'error')
      if (fileInputRef.current) fileInputRef.current.value = ''
      setSelectedFile(null)
    } finally {
      setRestoreLoading(false)
    }
  }

  async function handleRestore() {
    if (!restoreReady) return
    setRestoreLoading(true)
    try {
      const result = await restoreBackup({ archiveData, confirm: true })
      setValidation({ ...validation, tables: result.tables, uploads: result.uploads })
      setConfirmRestore(false)
      toast('Restore completed', 'success')
    } catch (error) {
      toast(getApiErrorMessage(error), 'error')
    } finally {
      setRestoreLoading(false)
    }
  }

  return (
    <div>
      <PageHeader
        title="Admin"
        subtitle="Create portable backups and restore application data from a validated archive"
        actions={<StatusBadge tone="accent">backup v1</StatusBadge>}
      />

      <div className="admin-layout">
        <section className="card admin-section">
          <div className="admin-section__header">
            <div className="admin-section__icon" aria-hidden="true">
              <Icon name="download" size={18} />
            </div>
            <div>
              <h3>Create backup</h3>
              <p>Database records and uploaded files are bundled into one zip archive.</p>
            </div>
          </div>
          <button className="btn btn-primary" type="button" onClick={handleBackup} disabled={backupLoading}>
            <Icon name="download" size={16} />
            {backupLoading ? 'Preparing…' : 'Download backup'}
          </button>
        </section>

        <section className="card admin-section">
          <div className="admin-section__header">
            <div className="admin-section__icon" aria-hidden="true">
              <Icon name="upload" size={18} />
            </div>
            <div>
              <h3>Restore backup</h3>
              <p>Upload a backup archive, review its contents, then confirm the restore.</p>
            </div>
          </div>

          <label className="admin-file-picker">
            <input
              ref={fileInputRef}
              type="file"
              accept=".zip,application/zip"
              onChange={handleFileChange}
              disabled={restoreLoading}
            />
            <Icon name="upload" size={16} />
            <span>{selectedFile ? selectedFile.name : 'Choose backup archive'}</span>
          </label>

          {validation ? (
            <>
              <ValidationSummary validation={validation} />
              <label className="admin-confirm">
                <input
                  type="checkbox"
                  checked={confirmRestore}
                  onChange={event => setConfirmRestore(event.target.checked)}
                  disabled={restoreLoading}
                />
                <span>I understand this will replace the current database and uploads.</span>
              </label>
              <button
                className="btn btn-danger"
                type="button"
                onClick={handleRestore}
                disabled={!restoreReady || restoreLoading}
              >
                <Icon name="restore" size={16} />
                {restoreLoading ? 'Restoring…' : 'Restore backup'}
              </button>
            </>
          ) : (
            <EmptyState icon={<Icon name="archive" />} message="No backup archive selected" compact />
          )}
        </section>
      </div>
    </div>
  )
}
