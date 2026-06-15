import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
})

export function getApiErrorMessage(error) {
  return error?.response?.data?.detail || error?.message || 'The API request failed'
}


// --- Admin ---

export const createBackup = () =>
  api.get('/admin/backup', { responseType: 'blob' })

export const validateRestoreArtifact = (archiveData) =>
  api.post('/admin/restore/validate', { archive_data: archiveData }).then(r => r.data)

export const restoreBackup = ({ archiveData, confirm }) =>
  api.post('/admin/restore', { archive_data: archiveData, confirm }).then(r => r.data)

// --- Dashboard ---

export const getDashboard = ({ signal } = {}) =>
  api.get('/dashboard', { signal }).then(r => r.data)

// --- Diagnostics ---

export const getDiagnosticsSummary = ({ signal } = {}) =>
  api.get('/diagnostics/summary', { signal }).then(r => r.data)

// --- Cats ---

export const getCats = (includeInactive = false, { signal } = {}) =>
  api.get('/cats', { params: { include_inactive: includeInactive }, signal }).then(r => r.data)

export const getCat = (id) =>
  api.get(`/cats/${id}`).then(r => r.data)

export const createCat = (data) =>
  api.post('/cats', data).then(r => r.data)

export const updateCat = (id, data) =>
  api.patch(`/cats/${id}`, data).then(r => r.data)

export const getCatEvents = (catId, { signal } = {}) =>
  api.get(`/cats/${catId}/events`, { signal }).then(r => r.data)

export const createCatEvent = (catId, data) =>
  api.post(`/cats/${catId}/events`, data).then(r => r.data)

export const updateCatEvent = (catId, eventId, data) =>
  api.patch(`/cats/${catId}/events/${eventId}`, data).then(r => r.data)

export const deleteCatEvent = (catId, eventId) =>
  api.delete(`/cats/${catId}/events/${eventId}`)

// --- Visits ---

export const getVisits = ({ limit = 50, offset = 0, catId, unidentified, fromDate, toDate, signal } = {}) =>
  api.get('/visits', {
    params: {
      limit,
      offset,
      cat_id: catId,
      unidentified,
      from_date: fromDate?.toISOString(),
      to_date: toDate?.toISOString(),
    },
    signal,
  }).then(r => r.data)

export const getVisitSummary = ({ bucket = 'day', limit = 50, offset = 0, catId, unidentified, fromDate, toDate, signal } = {}) =>
  api.get('/visits/summary', {
    params: {
      bucket,
      limit,
      offset,
      cat_id: catId,
      unidentified,
      from_date: fromDate?.toISOString(),
      to_date: toDate?.toISOString(),
    },
    signal,
  }).then(r => r.data)

export const createVisit = (data) =>
  api.post('/visits', data).then(r => r.data)

export const updateVisit = (id, data) =>
  api.patch(`/visits/${id}`, data).then(r => r.data)

export const deleteVisit = (id) =>
  api.delete(`/visits/${id}`)

export const getWeightHistory = ({ fromDate, toDate, catId, signal } = {}) =>
  api.get('/visits/weight-history', {
    params: {
      from_date: fromDate?.toISOString(),
      to_date: toDate?.toISOString(),
      cat_id: catId,
    },
    signal,
  }).then(r => r.data)

// --- Cat photos ---

export const uploadCatPhoto = (catId, photoData) =>
  api.post(`/cats/${catId}/photo`, { photo_data: photoData }).then(r => r.data)

export const deleteCatPhoto = (catId) =>
  api.delete(`/cats/${catId}/photo`).then(r => r.data)

// --- Cleaning cycles ---

export const getCleaningCycles = (limit = 50) =>
  api.get('/cleaning-cycles', { params: { limit } }).then(r => r.data)
