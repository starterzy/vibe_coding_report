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

  rejectRecord(id, data) {
    return api.post(`/api/report/records/${id}/reject`, data)
  },

  getDepartments() {
    return api.get('/api/departments')
  }
}
