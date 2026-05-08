/**
 * Jobs store - manages job state for the dashboard
 */

import { defineStore } from 'pinia'
import { api } from '../api/client'

export const useJobsStore = defineStore('jobs', {
  state: () => ({
    jobs: [],
    selectedJob: null,
    loading: false,
    error: null,
    filter: 'pending_approval'
  }),

  actions: {
    async fetchJobs() {
      this.loading = true
      this.error = null
      try {
        this.jobs = await api.getJobs(this.filter)
      } catch (err) {
        this.error = err.message || 'Failed to fetch jobs'
        this.jobs = []
      } finally {
        this.loading = false
      }
    },

    async selectJob(jobId) {
      this.loading = true
      try {
        this.selectedJob = await api.getJob(jobId)
      } catch (err) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },

    clearSelectedJob() {
      this.selectedJob = null
    },

    async approveJob(jobId) {
      this.loading = true
      try {
        await api.approveJob(jobId)
        await this.fetchJobs()
        if (this.selectedJob?.jobId === jobId) {
          this.selectedJob = null
        }
      } catch (err) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },

    async rejectJob(jobId) {
      this.loading = true
      try {
        await api.rejectJob(jobId)
        await this.fetchJobs()
        if (this.selectedJob?.jobId === jobId) {
          this.selectedJob = null
        }
      } catch (err) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },

    setFilter(filter) {
      this.filter = filter
      this.fetchJobs()
    }
  }
})