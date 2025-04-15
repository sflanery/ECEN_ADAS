<template>
  <div class="dashboard">
    <div class="dashboard-grid">
      <div class="camera-section">
        <CameraView />
      </div>
      <div class="gps-section">
        <GpsView />
      </div>
      <div class="info-section">
        <SpeedDisplay :speed="currentSpeed" />
        <AlertPanel :alerts="activeAlerts" />
      </div>
      <div class="signs-section">
        <TrafficSignDisplay :signs="upcomingSigns" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue';
import io from 'socket.io-client';
import CameraView from './CameraView.vue';
import GpsView from './GpsView.vue';
import SpeedDisplay from './SpeedDisplay.vue';
import AlertPanel from './AlertPanel.vue';
import TrafficSignDisplay from './TrafficSignDisplay.vue';

// Reactive state for different dashboard components
const dashboardState = reactive({
  alerts: {
    pedestrian: 0,
    collision: 0,
    blindSpot: 0,
    laneDeparture: 0
  },
  speed: 0,
  signs: [
    { id: 1, type: 'speed_limit', value: '50', distance: '300m' },
    { id: 2, type: 'stop', distance: '500m' }
  ]
});

// Computed/derived values for components
const activeAlerts = ref([]);
const currentSpeed = ref(60);
const upcomingSigns = ref(dashboardState.signs);

// Socket connection
let socket = null;

const processAlerts = () => {
  const alerts = [];
  
  if (dashboardState.alerts.pedestrian === 1) {
    alerts.push({ id: 1, type: 'warning', message: 'Pedestrian Detected' });
  }
  
  if (dashboardState.alerts.collision === 1) {
    alerts.push({ id: 2, type: 'warning', message: 'Collision' });
  }
  
  if (dashboardState.alerts.blindSpot === 1) {
    alerts.push({ id: 3, type: 'warning', message: 'Blind Spot' });
  }
  
  if (dashboardState.alerts.laneDeparture === 1) {
    alerts.push({ id: 4, type: 'warning', message: 'Lane Departure' });
  }
  
  activeAlerts.value = alerts;
};

const connectWebSocket = () => {
  // Connect to your Flask backend WebSocket
  socket = io('http://localhost:8080');

  // Listen for state updates
  socket.on('dashboard_state_updated', (updatedState) => {
    // Selectively update only changed values
    if (updatedState.alerts) {
      Object.keys(updatedState.alerts).forEach(key => {
        if (dashboardState.alerts[key] !== updatedState.alerts[key]) {
          dashboardState.alerts[key] = updatedState.alerts[key];
        }
      });
    }

    // Process alerts after update
    processAlerts();

    // Update speed if provided
    if (updatedState.speed !== undefined) {
      currentSpeed.value = updatedState.speed;
    }

    // Update signs if provided
    if (updatedState.signs) {
      dashboardState.signs = updatedState.signs;
      upcomingSigns.value = updatedState.signs;
    }
  });
};

onMounted(() => {
  // Initial WebSocket connection
  connectWebSocket();
  
  // Initial alert processing
  processAlerts();
});

onUnmounted(() => {
  // Disconnect socket when component is destroyed
  if (socket) {
    socket.disconnect();
  }
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
  overflow: hidden;  /* Prevents content from overflowing */
  display: flex;     /* Ensures CameraView fits properly */
  justify-content: center;
  align-items: center;
  width: 100%;       /* Restricts the section */
  height: 100%;
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
  background-color: #333;
  border-radius: 10px;
}

.signs-section {
  position: absolute;
  bottom: 20px;
  right: 20px;
  width: 150px;
  height: 150px;
  background-color: rgba(0, 0, 0, 0.7);
  border-radius: 10px;
  z-index: 1000;  /* Increase to make sure it's above other elements */
  pointer-events: none; /* Ensures it does not interfere with clicks */
}
</style>