<template>
  <div class="camera-view">
    <div v-if="!cameraActive" class="camera-placeholder">
      <div class="camera-icon">📷</div>
      <p>USB Camera Feed Not Available</p>
      <button @click="activateCamera">Activate USB Camera</button>
    </div>
    <div v-else>
      <video ref="videoElement" autoplay></video>
    </div>
  </div>
</template>

<script setup>
import { ref, onUnmounted, nextTick } from 'vue';

const videoElement = ref(null);
const cameraActive = ref(false);
let stream = null;

const activateCamera = async () => {
  try {
    // Request any camera first to populate labels
    await navigator.mediaDevices.getUserMedia({ video: true });

    // Enumerate video input devices
    const devices = await navigator.mediaDevices.enumerateDevices();
    const cameras = devices.filter(d => d.kind === 'videoinput');

    // Pick the first camera that is NOT a Pi camera
    const usbCamera = cameras.find(c =>
      c.label && !c.label.toLowerCase().includes('imx') &&
      !c.label.toLowerCase().includes('ov')
    );

    if (!usbCamera) {
      alert('No USB camera detected by the browser.');
      return;
    }

    // Use the USB camera
    stream = await navigator.mediaDevices.getUserMedia({
      video: { deviceId: { exact: usbCamera.deviceId } }
    });

    cameraActive.value = true;

    await nextTick();
    if (videoElement.value) {
      videoElement.value.srcObject = stream;
    }
  } catch (err) {
    console.error('Error accessing USB camera:', err);
    alert(`Could not access USB camera: ${err.message}`);
  }
};

// Stop camera on unmount
onUnmounted(() => {
  if (stream) stream.getTracks().forEach(track => track.stop());
});
</script>

<style scoped>
.camera-view { width: 100%; height: 100%; position: relative; }
video { width: 100%; height: 100%; object-fit: cover; }
.camera-placeholder {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  height: 100%; background-color: #222; color: white;
}
.camera-icon { font-size: 48px; margin-bottom: 10px; }
button { margin-top: 15px; padding: 8px 16px; background-color: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; }
</style>
