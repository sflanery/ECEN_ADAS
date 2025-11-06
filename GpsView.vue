<template>
  <div class="gps-view">
    <!-- GPS Status Indicator -->
    <div class="gps-status" :class="{ 'gps-active': gpsActive }">
      <span v-if="gpsActive">📡 GPS Active</span>
      <span v-else>📡 No GPS Signal</span>
    </div>
    
    <!-- Search Box -->
    <input
      type="text"
      v-model="searchQuery"
      placeholder="Enter destination..."
      @keyup.enter="searchLocation"
      class="search-box"
    />
    <div id="map" ref="mapContainer"></div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import 'leaflet-routing-machine';
import io from 'socket.io-client';

const mapContainer = ref(null);
const searchQuery = ref('');
const gpsActive = ref(false);
let map, marker, routingControl, accuracyCircle;
let socket = null;

// Initialize Map
onMounted(() => {
  // Fix Leaflet icon issue
  delete L.Icon.Default.prototype._getIconUrl;
  L.Icon.Default.mergeOptions({
    iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
    iconUrl: require('leaflet/dist/images/marker-icon.png'),
    shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
  });

  // Create the map (initially centered at Texas A&M)
  map = L.map(mapContainer.value).setView([30.6280, -96.3344], 13);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);

  // Create marker for user location
  marker = L.marker([30.6280, -96.3344]).addTo(map);

  // Connect to backend for GPS updates
  socket = io('http://localhost:8080');
  socket.on('gps_update', updateLocationFromGPS);

  // Fallback to browser geolocation if no GPS data
  if (navigator.geolocation) {
    navigator.geolocation.watchPosition(updateLocationFromBrowser, handleError, {
      enableHighAccuracy: true,
      maximumAge: 5000,
      timeout: 10000,
    });
  }
});

// Function to update location from GPS module (via backend)
const updateLocationFromGPS = (gpsData) => {
  console.log('[GPS] Received update:', gpsData);
  
  if (!gpsData.latitude || !gpsData.longitude) {
    console.log('[GPS] No valid coordinates');
    return;
  }
  
  gpsActive.value = gpsData.active || true;
  const newLatLng = [gpsData.latitude, gpsData.longitude];

  // Update marker position
  marker.setLatLng(newLatLng);

  // Adjust zoom based on accuracy
  if (gpsData.accuracy && gpsData.accuracy < 50) {
    map.setView(newLatLng, 18);
  } else {
    map.setView(newLatLng, 16);
  }

  // Update or create accuracy circle
  const radius = gpsData.accuracy || 10;
  if (!accuracyCircle) {
    accuracyCircle = L.circle(newLatLng, {
      color: 'green',
      fillColor: '#0f0',
      fillOpacity: 0.2,
      radius: radius,
    }).addTo(map);
  } else {
    accuracyCircle.setLatLng(newLatLng);
    accuracyCircle.setRadius(radius);
  }

  console.log(`[GPS] Updated: ${gpsData.latitude.toFixed(6)}, ${gpsData.longitude.toFixed(6)} (±${radius}m)`);
};

// Fallback function for browser geolocation
const updateLocationFromBrowser = (position) => {
  // Only use browser location if GPS module isn't providing data
  if (gpsActive.value) return;

  const { latitude, longitude, accuracy } = position.coords;
  const newLatLng = [latitude, longitude];

  marker.setLatLng(newLatLng);

  if (accuracy < 50) {
    map.setView(newLatLng, 18);
  } else {
    map.setView(newLatLng, 16);
  }

  if (!accuracyCircle) {
    accuracyCircle = L.circle(newLatLng, {
      color: 'blue',
      fillColor: '#30f',
      fillOpacity: 0.2,
      radius: accuracy,
    }).addTo(map);
  } else {
    accuracyCircle.setLatLng(newLatLng);
    accuracyCircle.setRadius(accuracy);
  }
};

// Handle geolocation errors
const handleError = (error) => {
  console.error("Error obtaining location:", error);
};

// Search function to find nearby destinations
const searchLocation = async (event) => {
  event.preventDefault();

  if (!searchQuery.value) return;

  const userLocation = marker.getLatLng();
  const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(searchQuery.value)}&lat=${userLocation.lat}&lon=${userLocation.lng}&zoom=13&viewbox=${userLocation.lng-0.1},${userLocation.lat-0.1},${userLocation.lng+0.1},${userLocation.lat+0.1}&bounded=1`;

  try {
    const response = await fetch(url);
    const data = await response.json();

    if (data.length > 0) {
      const { lat, lon } = data[0];
      const destination = [parseFloat(lat), parseFloat(lon)];

      L.marker(destination).addTo(map)
        .bindPopup(`Destination: ${searchQuery.value}`)
        .openPopup();

      drawRoute(destination);
    } else {
      alert("No matching locations found near you.");
    }
  } catch (error) {
    console.error("Error fetching location:", error);
  }
};

// Function to draw route using Leaflet Routing Machine
const drawRoute = (destination) => {
  if (routingControl) {
    map.removeControl(routingControl);
  }

  routingControl = L.Routing.control({
    waypoints: [
      marker.getLatLng(),
      L.latLng(destination)
    ],
    routeWhileDragging: true,
    createMarker: () => null,
  }).addTo(map);
};
</script>

<style scoped>
.gps-view {
  width: 100%;
  height: 100%;
  position: relative;
}

#map {
  width: 100%;
  height: 100%;
  border-radius: 8px;
}

/* GPS Status Indicator */
.gps-status {
  position: absolute;
  top: 10px;
  left: 10px;
  background-color: rgba(255, 0, 0, 0.8);
  color: white;
  padding: 5px 10px;
  border-radius: 5px;
  font-size: 12px;
  font-weight: bold;
  z-index: 1000;
  transition: background-color 0.3s;
}

.gps-status.gps-active {
  background-color: rgba(0, 200, 0, 0.8);
}

/* Search Box Styling */
.search-box {
  position: absolute;
  top: 10px;
  left: 50%;
  transform: translateX(-50%);
  width: 250px;
  padding: 8px;
  border-radius: 5px;
  border: none;
  outline: none;
  font-size: 14px;
  z-index: 1000;
}
</style>