<script setup>
import StatusBadge from './StatusBadge.vue'

defineProps({
  job: {
    type: Object,
    required: true
  }
})

defineEmits(['click'])

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div class="job-card" @click="$emit('click', job)">
    <div class="job-header">
      <span class="job-topic">{{ job.dataTopic }}</span>
      <StatusBadge :status="job.status" />
    </div>

    <div class="job-details">
      <div class="detail">
        <span class="label">Target:</span>
        <span class="value">{{ job.targetTable }}</span>
      </div>
      <div class="detail">
        <span class="label">File:</span>
        <span class="value file-key">{{ job.fileKey }}</span>
      </div>
      <div class="detail">
        <span class="label">Created:</span>
        <span class="value">{{ formatDate(job.createdAt) }}</span>
      </div>
      <div class="detail">
        <span class="label">Confidence:</span>
        <span class="value">{{ Math.round((job.confidence || 0) * 100) }}%</span>
      </div>
    </div>

    <button class="btn-view">View Details</button>
  </div>
</template>

<style scoped>
.job-card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s;
}

.job-card:hover {
  border-color: var(--primary);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.job-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.job-topic {
  font-weight: 600;
  font-size: 16px;
  text-transform: capitalize;
}

.job-details {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 12px;
}

.detail {
  font-size: 13px;
}

.label {
  color: var(--text-muted);
  margin-right: 4px;
}

.value {
  color: var(--text);
}

.file-key {
  font-family: monospace;
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 150px;
}

.btn-view {
  width: 100%;
  background: var(--bg);
  color: var(--text);
  border: 1px solid var(--border);
}

.btn-view:hover {
  background: var(--border);
}
</style>