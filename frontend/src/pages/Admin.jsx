import { useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  createBackup,
  getApiErrorMessage,
  getTuyaConfig,
  reloadTuyaConfig,
  restoreBackup,
  testTuyaConfig,
  updateTuyaConfig,
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


function emptyTuyaForm() {
  return {
    device_id: '',
    device_ip: '',
    api_region: 'eu',
    api_key: '',
    api_secret: '',
  }
}

function tuyaFormFromConfig(config) {
  return {
    device_id: config?.device_id || '',
    device_ip: config?.device_ip || '',
    api_region: config?.api_region || 'eu',
    api_key: '',
    api_secret: '',
  }
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
  const [tuyaConfig, setTuyaConfig] = useState(null)
  const [tuyaForm, setTuyaForm] = useState(emptyTuyaForm)
  const [tuyaLoading, setTuyaLoading] = useState(true)
  const [tuyaSaving, setTuyaSaving] = useState(false)
  const [tuyaTesting, setTuyaTesting] = useState(false)
  const [tuyaReloading, setTuyaReloading] = useState(false)

  useEffect(() => {
    let cancelled = false
    async function loadTuyaConfig() {
      setTuyaLoading(true)
      try {
        const config = await getTuyaConfig()
        if (cancelled) return
        setTuyaConfig(config)
        setTuyaForm(tuyaFormFromConfig(config))
      } catch (error) {
        if (!cancelled) toast(getApiErrorMessage(error), 'error')
      } finally {
        if (!cancelled) setTuyaLoading(false)
      }
    }
    loadTuyaConfig()
    return () => {
      cancelled = true
    }
  }, [toast])

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

  function handleTuyaFieldChange(field, value) {
    setTuyaForm(current => ({ ...current, [field]: value }))
  }

  function updateTuyaState(result) {
    const config = result.config || result
    setTuyaConfig(config)
    setTuyaForm(tuyaFormFromConfig(config))
    return result
  }

  async function handleTuyaSave(event) {
    event.preventDefault()
    setTuyaSaving(true)
    try {
      const result = await updateTuyaConfig(tuyaForm)
      updateTuyaState(result)
      if (result.reloaded) {
        toast(t('admin.toast.tuyaSaved'), 'success')
      } else {
        toast(result.message || t('admin.toast.tuyaReloadFailed'), 'error')
      }
    } catch (error) {
      toast(getApiErrorMessage(error), 'error')
    } finally {
      setTuyaSaving(false)
    }
  }

  async function handleTuyaTest() {
    setTuyaTesting(true)
    try {
      const result = await testTuyaConfig(tuyaForm)
      toast(result.message || (result.ok ? t('admin.toast.tuyaTestSucceeded') : t('admin.toast.tuyaTestFailed')), result.ok ? 'success' : 'error')
    } catch (error) {
      toast(getApiErrorMessage(error), 'error')
    } finally {
      setTuyaTesting(false)
    }
  }

  async function handleTuyaReload() {
    setTuyaReloading(true)
    try {
      const result = await reloadTuyaConfig()
      updateTuyaState(result)
      toast(result.message || (result.reloaded ? t('admin.toast.tuyaReloaded') : t('admin.toast.tuyaReloadFailed')), result.reloaded ? 'success' : 'error')
    } catch (error) {
      toast(getApiErrorMessage(error), 'error')
    } finally {
      setTuyaReloading(false)
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
            <section className="card admin-section">
              <div className="admin-section__header">
                <div className="admin-section__icon" aria-hidden="true">
                  <Icon name="activity" size={18} />
                </div>
                <div>
                  <h3>{t('admin.tuyaTitle')}</h3>
                  <p>{t('admin.tuyaDescription')}</p>
                </div>
              </div>

              <form className="admin-config-form" onSubmit={handleTuyaSave}>
                <div className="admin-config-grid">
                  <label className="form-field">
                    <span className="form-label">{t('admin.tuyaDeviceId')}</span>
                    <input
                      className="form-input"
                      value={tuyaForm.device_id}
                      onChange={event => handleTuyaFieldChange('device_id', event.target.value)}
                      disabled={tuyaLoading || tuyaSaving}
                    />
                  </label>
                  <label className="form-field">
                    <span className="form-label">{t('admin.tuyaDeviceIp')}</span>
                    <input
                      className="form-input"
                      value={tuyaForm.device_ip}
                      onChange={event => handleTuyaFieldChange('device_ip', event.target.value)}
                      disabled={tuyaLoading || tuyaSaving}
                    />
                  </label>
                  <label className="form-field">
                    <span className="form-label">{t('admin.tuyaApiRegion')}</span>
                    <input
                      className="form-input"
                      value={tuyaForm.api_region}
                      onChange={event => handleTuyaFieldChange('api_region', event.target.value)}
                      disabled={tuyaLoading || tuyaSaving}
                    />
                  </label>
                  <label className="form-field">
                    <span className="form-label">{t('admin.tuyaApiKey')}</span>
                    <input
                      className="form-input"
                      type="password"
                      autoComplete="off"
                      value={tuyaForm.api_key}
                      placeholder={tuyaConfig?.api_key_configured ? '••••••••' : ''}
                      onChange={event => handleTuyaFieldChange('api_key', event.target.value)}
                      disabled={tuyaLoading || tuyaSaving}
                    />
                  </label>
                  <label className="form-field">
                    <span className="form-label">{t('admin.tuyaApiSecret')}</span>
                    <input
                      className="form-input"
                      type="password"
                      autoComplete="off"
                      value={tuyaForm.api_secret}
                      placeholder={tuyaConfig?.api_secret_configured ? '••••••••' : ''}
                      onChange={event => handleTuyaFieldChange('api_secret', event.target.value)}
                      disabled={tuyaLoading || tuyaSaving}
                    />
                  </label>
                </div>

                <div className="admin-config-status">
                  <span>{t(tuyaConfig?.api_key_configured ? 'admin.tuyaApiKeyConfigured' : 'admin.tuyaApiKeyMissing')}</span>
                  <span>{t(tuyaConfig?.api_secret_configured ? 'admin.tuyaApiSecretConfigured' : 'admin.tuyaApiSecretMissing')}</span>
                </div>

                <div className="admin-actions">
                  <button className="btn btn-primary" type="submit" disabled={tuyaLoading || tuyaSaving}>
                    <Icon name="download" size={16} />
                    {tuyaSaving ? t('common.saving') : t('admin.tuyaSave')}
                  </button>
                  <button className="btn btn-secondary" type="button" onClick={handleTuyaTest} disabled={tuyaLoading || tuyaTesting}>
                    <Icon name="activity" size={16} />
                    {tuyaTesting ? t('common.testing') : t('admin.tuyaTest')}
                  </button>
                  <button className="btn btn-secondary" type="button" onClick={handleTuyaReload} disabled={tuyaLoading || tuyaReloading}>
                    <Icon name="restore" size={16} />
                    {tuyaReloading ? t('common.reloading') : t('admin.tuyaReload')}
                  </button>
                </div>
              </form>
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
