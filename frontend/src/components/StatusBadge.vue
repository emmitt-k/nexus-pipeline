<script setup>
defineProps({
  status: {
    type: String,
    required: true
  }
})

const statusLabels = {
  pending_approval: 'Pending',
  approved: 'Approved',
  rejected: 'Rejected',
  processing: 'Processing',
  completed: 'Completed',
  failed: 'Failed'
}
</script>

<template>
  <span class="badge" :class="status">
    {{ statusLabels[status] || status }}
  </span>
</template>