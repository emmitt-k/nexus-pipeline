<script setup>
import { useJobsStore } from '../stores/jobs'
import StatusBadge from './StatusBadge.vue'

const props = defineProps({
  job: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['close'])
const store = useJobsStore()

function getSchemaMapping(obj) {
  if (!obj) return []
  return Object.entries(obj)
}

function getTransformSpec(obj) {
  if (!obj) return []
  return Object.entries(obj)
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString()
}

async function handleApprove() {
  await store.approveJob(props.job.jobId)
  emit('close')
}

async function handleReject() {
  await store.rejectJob(props.job.jobId)
  emit('close')
}
</script>

<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal">
      <div class="modal-header">
        <div>
          <h2>{{ job.dataTopic }} → {{ job.targetTable }}</h2>
          <StatusBadge :status="job.status" />
        </div>
        <button class="btn-close" @click="$emit('close')">&times;</button>
      </div>

      <div class="modal-body">
        <div class="section">
          <h3>Schema Mapping</h3>
          <p class="hint">Source column → Target column</p>
          <table class="mapping-table">
            <thead>
              <tr>
                <th>Source</th>
                <th>Target</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(target, source) in job.schemaMapping" :key="source">
                <td>{{ source }}</td>
                <td>{{ target }}</td>
              </tr>
              <tr v-if="!job.schemaMapping || Object.keys(job.schemaMapping).length === 0">
                <td colspan="2" class="empty">No mapping available</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="section">
          <h3>Transform Spec</h3>
          <table class="mapping-table">
            <thead>
              <tr>
                <th>Column</th>
                <th>Transform</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(spec, column) in job.transformSpec" :key="column">
                <td>{{ column }}</td>
                <td>{{ spec.transform || spec.type || spec.format || spec.mask || '-' }}</td>
              </tr>
              <tr v-if="!job.transformSpec || Object.keys(job.transformSpec).length === 0">
                <td colspan="2" class="empty">No transforms</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="info-grid">
          <div class="info-item">
            <span class="label">Confidence</span>
            <span class="value">{{ Math.round((job.confidence || 0) * 100) }}%</span>
          </div>
          <div class="info-item">
            <span class="label">File</span>
            <span class="value">{{ job.fileKey }}</span>
          </div>
          <div class="info-item">
            <span class="label">Created</span>
            <span class="value">{{ formatDate(job.createdAt) }}</span>
          </div>
        </div>
      </div>

      <div class="modal-footer" v-if="job.status === 'pending_approval'">
        <button class="danger" @click="handleReject">Reject</button>
        <button class="success" @click="handleApprove">Approve & Run</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  padding: 20px;
}

.modal {
  background: var(--card-bg);
  border-radius: var(--radius);
  max-width: 700px;
  width: 100%;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 20px;
  border-bottom: 1px solid var(--border);
}

.modal-header h2 {
  display: inline-block;
  margin-right: 12px;
  font-size: 18px;
  text-transform: capitalize;
}

.btn-close {
  background: none;
  border: none;
  font-size: 24px;
  color: var(--text-muted);
  padding: 0;
  width: auto;
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.section {
  margin-bottom: 20px;
}

.section h3 {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
}

.hint {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 8px;
}

.mapping-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.mapping-table th,
.mapping-table td {
  padding: 8px 12px;
  text-align: left;
  border-bottom: 1px solid var(--border);
}

.mapping-table th {
  background: var(--bg);
  font-weight: 600;
}

.mapping-table td:first-child {
  font-weight: 500;
}

.empty {
  text-align: center;
  color: var(--text-muted);
  font-style: italic;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
}

.info-item {
  font-size: 13px;
}

.info-item .label {
  display: block;
  color: var(--text-muted);
  margin-bottom: 4px;
}

.info-item .value {
  word-break: break-all;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid var(--border);
}

.modal-footer button {
  padding: 10px 20px;
}
</style>