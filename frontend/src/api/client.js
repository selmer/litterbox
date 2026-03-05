import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
})

// --- Dashboard ---

export const getDashboard = () =>
  api.get('/dashboard').then(r => r.data)

// --- Cats ---

export const getCats = (includeInactive = false) =>
  api.get('/cats', { params: { include_inactive: includeInactive } }).then(r => r.data)

export const getCat = (id) =>
  api.get(`/cats/${id}`).then(r => r.data)

export const createCat = (data) =>
  api.post('/cats', data).then(r => r.data)

export const updateCat = (id, data) =>
  api.patch(`/cats/${id}`, data).then(r => r.data)

// --- Visits ---

export const getVisits = ({ limit = 50, catId } = {}) =>
  api.get('/visits', { params: { limit, cat_id: catId } }).then(r => r.data)

export const createVisit = (data) =>
  api.post('/visits', data).then(r => r.data)

export const updateVisit = (id, data) =>
  api.patch(`/visits/${id}`, data).then(r => r.data)

export const deleteVisit = (id) =>
  api.delete(`/visits/${id}`)

export const getWeightHistory = ({ fromDate, toDate, catId } = {}) =>
  api.get('/visits/weight-history', {
    params: {
      from_date: fromDate?.toISOString(),
      to_date: toDate?.toISOString(),
      cat_id: catId,
    },
  }).then(r => r.data)

// --- Cleaning cycles ---

export const getCleaningCycles = (limit = 50) =>
  api.get('/cleaning-cycles', { params: { limit } }).then(r => r.data)
