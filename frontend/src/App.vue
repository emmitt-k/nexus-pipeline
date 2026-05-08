<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { useJobsStore } from './stores/jobs'
import JobList from './components/JobList.vue'

const store = useJobsStore()
const apiConfigured = ref(true)

onMounted(() => {
  // Check if API is configured
  if (!import.meta.env.VITE_API_URL || !import.meta.env.VITE_API_KEY) {
    apiConfigured.value = false
  }
})
</script>

<template>
  <div class="app">
    <header>
      <h1>Nexus Pipeline</h1>
      <p class="subtitle">ETL Job Dashboard</p>
    </header>

    <main>
      <div v-if="!apiConfigured" class="config-needed">
        <h2>Configuration Needed</h2>
        <p>Copy <code>.env.example</code> to <code>.env</code> and add your API URL and key.</p>
        <p>Get values from CloudFormation stack output after deploying.</p>
      </div>

      <JobList v-else />
    </main>
  </div>
</template>

<style scoped>
.app {
  min-height: 100vh;
}

header {
  background: var(--card-bg);
  border-bottom: 1px solid var(--border);
  padding: 20px;
  text-align: center;
}

header h1 {
  font-size: 24px;
  margin-bottom: 4px;
}

.subtitle {
  color: var(--text-muted);
  font-size: 14px;
}

main {
  padding: 20px;
}

.config-needed {
  text-align: center;
  padding: 60px 20px;
  background: var(--card-bg);
  border-radius: var(--radius);
  max-width: 500px;
  margin: 40px auto;
}

.config-needed h2 {
  color: var(--warning);
  margin-bottom: 16px;
}

.config-needed p {
  color: var(--text-muted);
  margin-bottom: 12px;
}

.config-needed code {
  background: var(--bg);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
}
</style>