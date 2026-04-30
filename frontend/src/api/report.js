import { api } from './index'

export const reportApi = {
  getTasks(year = 2026) {
    return api.get(`/api/report/tasks`, { params: { year } })
  },

  getRecords(params = {}) {
    return api.get(`/api/report/records`, { params })
  },

  createRecord(data) {
    return api.post(`/api/report/records`, data)
  },

  updateRecord(id, data) {
    return api.put(`/api/report/records/${id}`, data)
  },

  submitRecord(id) {
    return api.post(`/api/report/records/${id}/submit`)
  },

  approveRecord(id) {
    return api.post(`/api/report/records/${id}/approve`)
  },

  rejectRecord(id) {
    return api.post(`/api/report/records/${id}/reject`)
  },

  getDepartments() {
    return api.get('/api/departments')
  },

  exportRecords(params = {}) {
    // Remove columns from params since we're not doing column selection anymore
    const { columns, ...rest } = params
    return api.get('/api/report/export', {
      params: rest,
      responseType: 'blob'
    })
  }
}
