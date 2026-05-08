/**
 * API client for Nexus Dashboard
 */

import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL
const API_KEY = import.meta.env.VITE_API_KEY

const client = axios.create({
  baseURL: API_BASE,
  headers: {
    'x-api-key': API_KEY,
    'Content-Type': 'application/json'
  }
})

export const api = {
  async getJobs(status = null) {
    const params = status ? { status } : {}
    const response = await client.get('/jobs', { params })
    return response.data
  },

  async getJob(jobId) {
    const response = await client.get(`/jobs/${jobId}`)
    return response.data
  },

  async approveJob(jobId) {
    const response = await client.post(`/jobs/${jobId}/approve`)
    return response.data
  },

  async rejectJob(jobId) {
    const response = await client.post(`/jobs/${jobId}/reject`)
    return response.data
  }
}