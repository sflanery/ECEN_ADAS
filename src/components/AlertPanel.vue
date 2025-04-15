<template>
  <div class="alert-panel">
    <h3>Alerts</h3>
    <div class="alerts-container">
      <div 
        v-for="alert in allAlerts" 
        :key="alert.id" 
        class="alert-item"
        :class="[
          'alert-' + alert.type, 
          { 'alert-active': isAlertActive(alert.id) }
        ]"
      >
        <div class="alert-icon">
          <span v-if="alert.type === 'warning'">⚠️</span>
          <span v-else-if="alert.type === 'error'">❌</span>
          <span v-else-if="alert.type === 'info'">ℹ️</span>
          <span v-else>🔔</span>
        </div>
        <div class="alert-message">{{ alert.message }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps, ref, watch } from 'vue';

const props = defineProps({
  alerts: {
    type: Array,
    default: () => []
  }
});

// Define all possible alerts
const allAlerts = ref([
  { id: 1, type: 'warning', message: 'Pedestrian Detected' },
  { id: 2, type: 'warning', message: 'Collision' },
  { id: 3, type: 'warning', message: 'Blind Spot' },
  { id: 4, type: 'warning', message: 'Lane Departure' }
]);

// Track previously active alerts to detect new activations
const previousActiveAlertIds = ref(new Set());

// Function to check if an alert is active
const isAlertActive = (id) => {
  return props.alerts.some(alert => alert.id === id);
};

// Audio for alert sound
const alertSound = new Audio();
alertSound.src = '/alert-sound.mp3'; // Path to your alert sound file

// Watch for changes in active alerts to play sound
watch(() => props.alerts, (newAlerts) => {
  const currentActiveAlertIds = new Set(newAlerts.map(alert => alert.id));
  
  // Check for newly activated alerts
  for (const alert of newAlerts) {
    if (!previousActiveAlertIds.value.has(alert.id)) {
      // Play sound for newly activated alert
      alertSound.play().catch(error => {
        console.error('Error playing alert sound:', error);
      });
      break; // Only play sound once even if multiple alerts activate
    }
  }
  
  // Update previous active alerts
  previousActiveAlertIds.value = currentActiveAlertIds;
}, { deep: true });
</script>

<style scoped>
.alert-panel {
  flex: 1;
  padding: 15px;
}

h3 {
  margin-top: 0;
  margin-bottom: 15px;
}

.alerts-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.alert-item {
  display: flex;
  align-items: center;
  padding: 10px;
  border-radius: 6px;
  transition: all 0.3s ease;
  opacity: 0.35; /* Default low opacity for inactive alerts */
}

/* Active alert styling */
.alert-active {
  opacity: 1;
  box-shadow: 0 0 8px rgba(255, 255, 255, 0.3);
}

.alert-warning {
  background-color: rgba(255, 193, 7, 0.2);
  border-left: 4px solid #ffc107;
}

.alert-error {
  background-color: rgba(244, 67, 54, 0.2);
  border-left: 4px solid #f44336;
}

.alert-info {
  background-color: rgba(33, 150, 243, 0.2);
  border-left: 4px solid #2196f3;
}

.alert-notification {
  background-color: rgba(139, 195, 74, 0.2);
  border-left: 4px solid #8bc34a;
}

.alert-icon {
  margin-right: 10px;
  font-size: 20px;
}
</style>