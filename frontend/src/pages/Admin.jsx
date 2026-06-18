import { useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  createBackup,
  getApiErrorMessage,
  restoreBackup,
  validateRestoreArtifact,
} from '../api/client'
import Icon from '../components/Icon'
import { useToast } from '../components/ToastContext'
import { useLanguage } from '../i18n/useLanguage'
import { EmptyState, PageHeader, StatusBadge } from '../components/ui'

function fileToDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.onerror = () => reject(reader.error)
    reader.readAsDataURL(file)
  })
}

function formatDateTime(value, locale) {
  if (!value) return '-'
  return new Date(value).toLocaleString(locale, { dateStyle: 'medium', timeStyle: 'medium' })
}

function formatTableName(name) {
  return name.replaceAll('_', ' ')
}

function ValidationSummary({ validation, locale, t }) {
  const tableEntries = Object.entries(validation.tables || {}).sort(([a], [b]) => a.localeCompare(b))
  return (
    <div className="admin-validation">
      <div className="admin-validation__meta">
        <div>
          <span>{t('field.created')}</span>
          <strong>{formatDateTime(validation.metadata?.created_at, locale)}</strong>
        </div>
        <div>
          <span>{t('field.schema')}</span>
          <strong>{validation.metadata?.schema_revision || t('common.unknown')}</strong>
        </div>
        <div>
          <span>{t('field.uploads')}</span>
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
  const { language, languages, locale, setLanguage, t } = useLanguage()
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
      toast(t('admin.toast.backupStarted'), 'success')
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
      toast(t('admin.toast.archiveValidated'), 'success')
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
      toast(t('admin.toast.restoreCompleted'), 'success')
    } catch (error) {
      toast(getApiErrorMessage(error), 'error')
    } finally {
      setRestoreLoading(false)
    }
  }

  return (
    <div>
      <PageHeader
        title={t('admin.title')}
        subtitle={t('admin.subtitle')}
        actions={<StatusBadge tone="accent">{t('status.backupV1')}</StatusBadge>}
      />

      <div className="admin-page-sections">
        <section className="admin-group" aria-labelledby="admin-preferences-title">
          <div className="admin-group__heading">
            <h2 id="admin-preferences-title">{t('admin.preferences')}</h2>
            <p>{t('admin.preferencesDescription')}</p>
          </div>
          <div className="admin-layout admin-layout--single">
            <section className="card admin-section">
              <div className="admin-section__header">
                <div className="admin-section__icon" aria-hidden="true">
                  <Icon name="activity" size={18} />
                </div>
                <div>
                  <h3>{t('admin.languageTitle')}</h3>
                  <p>{t('admin.languageDescription')}</p>
                </div>
              </div>
              <select
                className="form-input"
                value={language}
                onChange={event => setLanguage(event.target.value)}
                aria-label={t('admin.languageTitle')}
              >
                {languages.map(item => (
                  <option key={item.code} value={item.code}>{item.label}</option>
                ))}
              </select>
            </section>
          </div>
        </section>

        <section className="admin-group" aria-labelledby="admin-operations-title">
          <div className="admin-group__heading">
            <h2 id="admin-operations-title">{t('admin.operations')}</h2>
            <p>{t('admin.operationsDescription')}</p>
          </div>
          <div className="admin-layout admin-layout--single">
            <section className="card admin-section">
              <div className="admin-section__header">
                <div className="admin-section__icon" aria-hidden="true">
                  <Icon name="activity" size={18} />
                </div>
                <div>
                  <h3>{t('admin.operationalTools')}</h3>
                  <p>{t('admin.operationalToolsDescription')}</p>
                </div>
              </div>
              <Link className="btn btn-secondary" to="/diagnostics">
                <Icon name="activity" size={16} />
                {t('nav.diagnostics')}
              </Link>
            </section>
          </div>
        </section>

        <section className="admin-group" aria-labelledby="admin-backup-title">
          <div className="admin-group__heading">
            <h2 id="admin-backup-title">{t('admin.backup')}</h2>
            <p>{t('admin.backupDescription')}</p>
          </div>
          <div className="admin-layout admin-layout--single">
            <section className="card admin-section">
              <div className="admin-section__header">
                <div className="admin-section__icon" aria-hidden="true">
                  <Icon name="download" size={18} />
                </div>
                <div>
                  <h3>{t('admin.createBackup')}</h3>
                  <p>{t('admin.createBackupDescription')}</p>
                </div>
              </div>
              <button className="btn btn-primary" type="button" onClick={handleBackup} disabled={backupLoading}>
                <Icon name="download" size={16} />
                {backupLoading ? t('common.preparing') : t('admin.downloadBackup')}
              </button>
            </section>
          </div>
        </section>

        <section className="admin-group admin-group--danger" aria-labelledby="admin-danger-title">
          <div className="admin-group__heading">
            <h2 id="admin-danger-title">{t('admin.dangerZone')}</h2>
            <p>{t('admin.dangerZoneDescription')}</p>
          </div>
          <div className="admin-layout admin-layout--single">
            <section className="card admin-section admin-section--danger">
              <div className="admin-section__header">
                <div className="admin-section__icon" aria-hidden="true">
                  <Icon name="upload" size={18} />
                </div>
                <div>
                  <h3>{t('admin.restoreBackup')}</h3>
                  <p>{t('admin.restoreBackupDescription')}</p>
                </div>
              </div>

              <p className="admin-danger-note">{t('admin.restoreWarning')}</p>

              <label className="admin-file-picker">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".zip,application/zip"
                  onChange={handleFileChange}
                  disabled={restoreLoading}
                />
                <Icon name="upload" size={16} />
                <span>{selectedFile ? selectedFile.name : t('admin.chooseBackupArchive')}</span>
              </label>

              {validation ? (
                <>
                  <ValidationSummary validation={validation} locale={locale} t={t} />
                  <label className="admin-confirm">
                    <input
                      type="checkbox"
                      checked={confirmRestore}
                      onChange={event => setConfirmRestore(event.target.checked)}
                      disabled={restoreLoading}
                    />
                    <span>{t('admin.confirmRestore')}</span>
                  </label>
                  <button
                    className="btn btn-danger"
                    type="button"
                    onClick={handleRestore}
                    disabled={!restoreReady || restoreLoading}
                  >
                    <Icon name="restore" size={16} />
                    {restoreLoading ? t('common.restoring') : t('admin.restoreBackup')}
                  </button>
                </>
              ) : (
                <EmptyState icon={<Icon name="archive" />} message={t('admin.noBackupSelected')} compact />
              )}
            </section>
          </div>
        </section>
      </div>
    </div>
  )
}
