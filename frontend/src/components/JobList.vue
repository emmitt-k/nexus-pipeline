<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { useJobsStore } from '../stores/jobs'
import JobCard from './JobCard.vue'
import JobDetail from './JobDetail.vue'

const store = useJobsStore()
const showDetail = ref(false)
const selectedJob = ref(null)

const filters = [
  { value: 'pending_approval', label: 'Pending' },
  { value: 'approved', label: 'Approved' },
  { value: 'processing', label: 'Processing' },
  { value: 'completed', label: 'Completed' },
  { value: 'failed', label: 'Failed' }
]

let refreshInterval = null

onMounted(() => {
  store.fetchJobs()
  // Auto-refresh every 30 seconds
  refreshInterval = setInterval(() => {
    store.fetchJobs()
  }, 30000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})

function handleJobClick(job) {
  selectedJob.value = job
  showDetail.value = true
}

function closeDetail() {
  showDetail.value = false
  selectedJob.value = null
}
</script>

<template>
  <div class="job-list">
    <div class="filters">
      <button
        v-for="f in filters"
        :key="f.value"
        :class="['filter-btn', { active: store.filter === f.value }]"
        @click="store.setFilter(f.value)"
      >
        {{ f.label }}
      </button>
    </div>

    <div class="content">
      <div v-if="store.loading" class="loading">Loading...</div>

      <div v-else-if="store.error" class="error">
        {{ store.error }}
        <button @click="store.fetchJobs()">Retry</button>
      </div>

      <div v-else-if="store.jobs.length === 0" class="empty">
        No {{ store.filter.replace('_', ' ') }} jobs
      </div>

      <div v-else class="jobs-grid">
        <JobCard
          v-for="job in store.jobs"
          :key="job.jobId"
          :job="job"
          @click="handleJobClick"
        />
      </div>
    </div>

    <JobDetail
      v-if="showDetail && selectedJob"
      :job="selectedJob"
      @close="closeDetail"
    />
  </div>
</template>

<style scoped>
.job-list {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.filters {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
}

.filter-btn {
  background: var(--card-bg);
  border: 1px solid var(--border);
  color: var(--text-muted);
  padding: 8px 16px;
}

.filter-btn.active {
  background: var(--primary);
  border-color: var(--primary);
  color: white;
}

.filter-btn:hover:not(.active) {
  border-color: var(--primary);
  color: var(--primary);
}

.content {
  min-height: 200px;
}

.loading,
.error,
.empty {
  text-align: center;
  padding: 40px;
  color: var(--text-muted);
}

.error button {
  margin-top: 12px;
  background: var(--bg);
}

.jobs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}
</style>