<template>
  <div class="camera-view">
    <div v-if="!cameraActive" class="camera-placeholder">
      <div class="camera-icon">📷</div>
      <p>USB Camera Feed Not Available</p>
      <button @click="activateCamera">Activate USB Camera</button>
    </div>
    <div v-else>
      <video ref="videoElement" autoplay></video>
      <div class="camera-controls">
        <select v-if="availableCameras.length > 0" v-model="selectedCamera" @change="switchCamera" class="camera-select">
          <option v-for="camera in availableCameras" :key="camera.deviceId" :value="camera.deviceId">
            {{ camera.label || `Camera ${camera.deviceId.substring(0, 5)}...` }}
          </option>
        </select>
        <button @click="stopCamera" class="stop-button">Stop Camera</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onUnmounted, nextTick } from 'vue';

const videoElement = ref(null);
const cameraActive = ref(false);
const availableCameras = ref([]);
const selectedCamera = ref('');
let stream = null;

// Function to enumerate all available video devices
const getAvailableCameras = async () => {
  try {
    const devices = await navigator.mediaDevices.enumerateDevices();
    // Filter only video input devices (cameras)
    const cameras = devices.filter(device => device.kind === 'videoinput');
    availableCameras.value = cameras;
    
    // Look for USB cameras (not built-in)
    const usbCameras = cameras.filter(camera => 
      camera.label && !camera.label.toLowerCase().includes('built-in') && 
      !camera.label.toLowerCase().includes('raspberry pi'));
    
    // If USB cameras found, select the first one
    if (usbCameras.length > 0) {
      selectedCamera.value = usbCameras[0].deviceId;
    } 
    // Otherwise select the first available camera
    else if (cameras.length > 0) {
      selectedCamera.value = cameras[0].deviceId;
    }
    
    console.log('Available cameras:', cameras);
  } catch (err) {
    console.error('Error enumerating devices:', err);
  }
};

const activateCamera = async () => {
  try {
    // First get available cameras
    await getAvailableCameras();
    
    if (availableCameras.value.length === 0) {
      alert('No cameras detected on your system');
      return;
    }
    
    // Use the selected camera or the first available one
    const constraints = {
      video: {
        deviceId: selectedCamera.value ? { exact: selectedCamera.value } : undefined
      }
    };
    
    stream = await navigator.mediaDevices.getUserMedia(constraints);
    cameraActive.value = true;
    
    // Use nextTick to ensure the video element is rendered before setting srcObject
    await nextTick();
    if (videoElement.value) {
      videoElement.value.srcObject = stream;
    } else {
      console.error('Video element not available');
      cameraActive.value = false;
    }
  } catch (err) {
    console.error('Error accessing camera:', err.name, err.message);
    alert(`Could not access camera: ${err.message}. Please check permissions and connections.`);
  }
};

const switchCamera = async () => {
  // Stop current stream
  if (stream) {
    stream.getTracks().forEach(track => track.stop());
  }
  
  // Start new stream with selected camera
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: {
        deviceId: { exact: selectedCamera.value }
      }
    });
    
    if (videoElement.value) {
      videoElement.value.srcObject = stream;
    }
  } catch (err) {
    console.error('Error switching camera:', err);
    alert(`Could not switch to selected camera: ${err.message}`);
  }
};

const stopCamera = () => {
  if (stream) {
    stream.getTracks().forEach(track => track.stop());
    stream = null;
  }
  cameraActive.value = false;
};

// Clean up when component is unmounted
onUnmounted(() => {
  if (stream) {
    stream.getTracks().forEach(track => track.stop());
  }
});
</script>

<style scoped>
.camera-view {
  width: 100%;
  height: 100%;
  overflow: hidden;
  position: relative;
}

video {
  width: 100%;
  height: calc(100% - 50px);
  object-fit: cover;
}

.camera-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  background-color: #222;
  color: white;
}

.camera-icon {
  font-size: 48px;
  margin-bottom: 10px;
}

button {
  margin-top: 15px;
  padding: 8px 16px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.camera-controls {
  display: flex;
  justify-content: center;
  gap: 10px;
  padding: 10px;
}

.camera-select {
  padding: 8px;
  border-radius: 4px;
}

.stop-button {
  background-color: #f44336;
}
</style>