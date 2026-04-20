import { api } from './index'

export const userApi = {
  getUsers() {
    return api.get('/api/users')
  },

  createUser(data) {
    return api.post('/api/users', data)
  },

  updateUser(id, data) {
    return api.put(`/api/users/${id}`, data)
  },

  deleteUser(id) {
    return api.delete(`/api/users/${id}`)
  },

  activateUser(id) {
    return api.post(`/api/users/${id}/activate`)
  },

  getDepartments() {
    return api.get('/api/departments')
  }
}
