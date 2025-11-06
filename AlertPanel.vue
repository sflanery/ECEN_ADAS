<template>
  <div class="alert-panel">
    <h3>Alerts ({{ alerts.length }})</h3>
    <div class="alerts-container">
      <div v-if="alerts.length === 0" class="no-alerts">
        No active alerts
      </div>
      <transition-group name="alert" tag="div">
        <div
          v-for="alert in alerts"
          :key="alert.id"
          class="alert-item"
          :class="'alert-' + alert.type"
        >
          <div class="alert-icon">
            <span v-if="alert.type === 'warning'">⚠️</span>
            <span v-else-if="alert.type === 'error'">❌</span>
            <span v-else-if="alert.type === 'info'">ℹ️</span>
            <span v-else>🔔</span>
          </div>
          <div class="alert-message">{{ alert.message }}</div>
        </div>
      </transition-group>
    </div>
  </div>
</template>

<script setup>
import { defineProps, watch, onMounted } from 'vue';

const props = defineProps({
  alerts: {
    type: Array,
    default: () => [],
  },
});

let previousAlertIds = new Set();
const alertSound = new Audio('/alert-sound.mp3');

onMounted(() => {
  console.log('[AlertPanel] Mounted with alerts:', props.alerts);
});

// Play sound when a new alert appears
watch(
  () => props.alerts,
  (newAlerts) => {
    console.log('[AlertPanel] Alerts changed:', newAlerts);
    console.log('[AlertPanel] Number of alerts:', newAlerts.length);
    
    const newIds = new Set(newAlerts.map(a => a.id));
    for (const id of newIds) {
      if (!previousAlertIds.has(id)) {
        console.log('[AlertPanel] New alert detected:', id);
        alertSound.play().catch(() => {
          console.log('[AlertPanel] Could not play sound (no audio file)');
        });
        break; // Only play once for the first new alert
      }
    }
    previousAlertIds = newIds;
  },
  { deep: true, immediate: true }
);
</script>

<style scoped>
.alert-panel {
  width: 100%;
  padding: 10px;
  background-color: rgba(40, 40, 40, 0.9);
  border-radius: 8px;
  color: white;
  font-family: sans-serif;
}

h3 {
  margin: 0 0 10px 0;
  font-size: 1.1rem;
  font-weight: 600;
  border-bottom: 1px solid #555;
  padding-bottom: 5px;
}

.alerts-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 50px;
}

.no-alerts {
  color: #888;
  font-style: italic;
  padding: 10px;
  text-align: center;
}

/* Alert item */
.alert-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 6px;
  opacity: 0.95;
  transition: all 0.3s ease;
  font-size: 0.95rem;
}

.alert-item:hover {
  opacity: 1;
  transform: translateX(2px);
}

/* Alert types */
.alert-warning {
  background-color: rgba(255, 193, 7, 0.3);
  border-left: 4px solid #ffc107;
}

.alert-error {
  background-color: rgba(244, 67, 54, 0.3);
  border-left: 4px solid #f44336;
}

.alert-info {
  background-color: rgba(33, 150, 243, 0.3);
  border-left: 4px solid #2196f3;
}

/* Icon */
.alert-icon {
  margin-right: 10px;
  font-size: 1.2rem;
}

.alert-message {
  flex: 1;
  font-weight: 500;
}

/* Transition animations */
.alert-enter-active, .alert-leave-active {
  transition: all 0.4s ease;
}
.alert-enter-from, .alert-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>