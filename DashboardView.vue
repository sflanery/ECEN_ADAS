<template>
  <div class="dashboard">
    <div class="dashboard-grid">
      <div class="camera-section">
        <CameraView />
        <div class="camera-overlay-signs">
          <TrafficSignDisplay :signs="upcomingSigns" />
        </div>
      </div>
      <div class="gps-section">
        <GpsView />
      </div>
      <div class="info-section">
        <div class="speed-limit-container">
          <SpeedDisplay :speed="currentSpeed" :speedLimit="currentSpeedLimit" />
        </div>
        <div class="alerts-container">
          <AlertPanel 
            :alerts="activeAlerts"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue';
import io from 'socket.io-client';
import CameraView from './CameraView.vue';
import GpsView from './GpsView.vue';
import SpeedDisplay from './SpeedDisplay.vue';
import AlertPanel from './AlertPanel.vue';
import TrafficSignDisplay from './TrafficSignDisplay.vue';

// Reactive state for dashboard
const dashboardState = reactive({
  signs: [],
  speed: 0
});

// Alerts array directly from backend
const activeAlerts = ref([]);
const currentSpeed = ref(0);
const upcomingSigns = ref(dashboardState.signs);

// Computed speed limit
const currentSpeedLimit = computed(() => {
  const speedSign = dashboardState.signs.find(sign => sign.type === 'speed_limit');
  return speedSign ? speedSign.value : null;
});

// ---------------- SOCKET.IO ----------------
let socket = null;

const connectWebSocket = () => {
  socket = io('http://localhost:8080');

  socket.on('dashboard_state_updated', (updatedState) => {
    // Update active alerts directly from backend
    if (updatedState.activeAlerts) {
      activeAlerts.value = updatedState.activeAlerts;
    }

    // Update speed
    if (updatedState.speed !== undefined) {
      currentSpeed.value = updatedState.speed;
    }

    // Update signs
    if (updatedState.signs) {
      dashboardState.signs = updatedState.signs;
      upcomingSigns.value = updatedState.signs;
    }
  });
};

onMounted(() => {
  connectWebSocket();
});

onUnmounted(() => {
  if (socket) socket.disconnect();
});
</script>

<style scoped>
.dashboard {
  width: 100%;
  height: 100vh;
  background-color: #222;
  color: white;
  padding: 20px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  grid-template-rows: 2fr 1fr;
  gap: 20px;
  height: 100%;
}

.camera-section {
  grid-row: 1 / 2;
  grid-column: 1 / 2;
  background-color: #333;
  border-radius: 10px;
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
  position: relative;
}

.camera-overlay-signs {
  position: absolute;
  bottom: 20px;
  right: 20px;
  width: 100px;
  background-color: rgba(0, 0, 0, 0.7);
  border-radius: 10px;
  z-index: 1000;
  pointer-events: none;
}

.gps-section {
  grid-row: 1 / 3;
  grid-column: 2 / 3;
  background-color: #333;
  border-radius: 10px;
}

.info-section {
  grid-row: 2 / 3;
  grid-column: 1 / 2;
  display: flex;
  gap: 10px;
  background-color: #333;
  border-radius: 10px;
  padding: 15px;
  height: 100%;
}

.speed-limit-container {
  width: 40%;
  height: 100%;
  display: flex;
  align-items: center;
}

.alerts-container {
  width: 60%;
  height: 100%;
  padding-left: 20px;
}
</style>