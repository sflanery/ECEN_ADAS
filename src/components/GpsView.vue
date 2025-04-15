<template>
  <div class="gps-view">
    <!-- Status indicator -->
    <div v-if="loadingStatus" class="status-message">{{ loadingStatus }}</div>
    
    <!-- Debug info -->
    <div v-if="debugMode" class="debug-info">
      <div>Current Location: {{ currentLocation.lat.toFixed(4) }}, {{ currentLocation.lng.toFixed(4) }}</div>
      <div>Location Status: {{ locationStatus }}</div>
      <div>Location Source: {{ locationSource }}</div>
      <button @click="retryGeolocation" class="debug-button">Retry Location</button>
    </div>
    
    <!-- Search Box -->
    <input
      type="text"
      v-model="searchQuery"
      placeholder="Enter destination..."
      @keyup.enter="searchLocation"
      class="search-box"
    />
    
    <div id="map" ref="mapContainer" class="map-container"></div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Try to import Leaflet Routing Machine if available
try {
  require('leaflet-routing-machine');
} catch (e) {
  console.warn("Leaflet Routing Machine not available, navigation will be disabled");
}

const mapContainer = ref(null);
const searchQuery = ref('');
const loadingStatus = ref('Initializing map...');
const locationStatus = ref('Waiting for location...');
const locationSource = ref('None');
const debugMode = ref(true); // Set to false for production

// Default location (Texas - somewhere in central Texas)
const currentLocation = reactive({
  lat: 30.2672,
  lng: -97.7431 // Austin, Texas as a starting point
});

let map, marker, routingControl;
let accuracyCircle;
let watchId = null;
// let locationUpdateCount = 0;

// Initialize Map
onMounted(() => {
  initializeMap();
});

const initializeMap = async () => {
  try {
    // Create a safety check for the container element
    if (!mapContainer.value) {
      loadingStatus.value = 'Map container not found. Please reload the page.';
      return;
    }
    
    loadingStatus.value = 'Loading map...';
    
    // Fix for Leaflet icon issue in bundled environments
    fixLeafletIcons();
    
    // Create the map with Texas location as default
    map = L.map(mapContainer.value, {
      zoomControl: true,
      attributionControl: true
    }).setView([currentLocation.lat, currentLocation.lng], 10);
    
    // Add tile layer with error handling
    try {
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
      }).addTo(map);
    } catch (error) {
      console.error("Error loading map tiles:", error);
      loadingStatus.value = 'Error loading map tiles. Check internet connection.';
      return;
    }
    
    // Create marker for user location
    marker = L.marker([currentLocation.lat, currentLocation.lng]).addTo(map);
    
    // Force a map resize to fix rendering issues
    setTimeout(() => {
      map.invalidateSize();
    }, 100);
    
    loadingStatus.value = 'Locating you...';
    
    // Start location detection process
    getLocation();
  } catch (error) {
    console.error("Error initializing map:", error);
    loadingStatus.value = `Map initialization failed: ${error.message}`;
  }
};

const getLocation = async () => {
  locationStatus.value = 'Requesting position...';
  
  // Try browser geolocation first with less strict settings (will use IP if GPS not available)
  if (navigator.geolocation) {
    try {
      // Clear existing watch if any
      if (watchId !== null) {
        navigator.geolocation.clearWatch(watchId);
        watchId = null;
      }
      
      // Use a less aggressive approach suitable for devices without GPS
      navigator.geolocation.getCurrentPosition(
        (position) => {
          console.log("Got position:", position.coords);
          updateLocation(position);
          loadingStatus.value = ''; // Clear status when successful
          locationStatus.value = 'Position acquired';
          locationSource.value = 'Browser Geolocation API';
        },
        (error) => {
          console.warn("Browser geolocation failed:", error);
          // Fall back to IP-based geolocation
          useIpBasedGeolocation();
        },
        {
          enableHighAccuracy: false, // Set to false for IP-based location
          maximumAge: 30000, // Accept cached positions up to 30 seconds old
          timeout: 10000  // Don't wait too long for a GPS fix
        }
      );
    } catch (error) {
      console.error("Error with geolocation:", error);
      // Fall back to IP-based geolocation
      useIpBasedGeolocation();
    }
  } else {
    // Browser doesn't support geolocation, use IP-based
    useIpBasedGeolocation();
  }
};

const retryGeolocation = () => {
  getLocation();
};

// IP-based geolocation as fallback
const useIpBasedGeolocation = async () => {
  locationStatus.value = 'Using IP-based location...';
  
  try {
    // Use a free IP geolocation service (you might want to replace with a more reliable API)
    const response = await fetch('https://ipapi.co/json/');
    if (!response.ok) throw new Error('IP geolocation request failed');
    
    const data = await response.json();
    
    if (data.latitude && data.longitude) {
      console.log("Got IP-based location:", data);
      
      // Create a position object similar to the browser's geolocation API
      const position = {
        coords: {
          latitude: data.latitude,
          longitude: data.longitude,
          accuracy: 5000 // IP geolocation is typically less accurate (5km)
        }
      };
      
      updateLocation(position);
      loadingStatus.value = '';
      locationStatus.value = 'Position acquired';
      locationSource.value = 'IP Geolocation';
    } else {
      throw new Error('Invalid IP geolocation data');
    }
  } catch (error) {
    console.error("IP geolocation failed:", error);
    locationStatus.value = 'Location detection failed';
    loadingStatus.value = 'Could not determine your location. Using default location.';
    
    // Use default location in Texas as fallback
    const defaultPosition = {
      coords: {
        latitude: currentLocation.lat,
        longitude: currentLocation.lng,
        accuracy: 10000 // Very low accuracy for default position
      }
    };
    
    updateLocation(defaultPosition);
    locationSource.value = 'Default Location';
    
    // Clear the loading status after 5 seconds
    setTimeout(() => {
      loadingStatus.value = '';
    }, 5000);
  }
};

// Fix for Leaflet icons in bundled environments
const fixLeafletIcons = () => {
  // Method 1: Using default icon URLs directly
  delete L.Icon.Default.prototype._getIconUrl;
  L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
    iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
    shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
  });
};

// Function to update user location
const updateLocation = (position) => {
  if (!map || !marker) return;
  
  const { latitude, longitude, accuracy } = position.coords;
  
  // Update our reactive location object
  currentLocation.lat = latitude;
  currentLocation.lng = longitude;
  
  const newLatLng = [latitude, longitude];
  
  console.log(`Setting location to: ${latitude}, ${longitude} (accuracy: ${accuracy}m)`);
  
  // Update marker position
  marker.setLatLng(newLatLng);
  
  // Adjust zoom level based on accuracy
  // IP-based location is less accurate, so we use a lower zoom level
  const zoomLevel = accuracy < 100 ? 16 : // High accuracy (rare for IP)
                   accuracy < 1000 ? 13 : // Medium accuracy
                   accuracy < 5000 ? 11 : // Low accuracy (typical for IP)
                   9; // Very low accuracy
  
  // Set view to new location
  map.setView(newLatLng, zoomLevel);
  
  // Add or update accuracy circle
  if (!accuracyCircle) {
    accuracyCircle = L.circle(newLatLng, {
      color: 'blue',
      fillColor: '#30f',
      fillOpacity: 0.2,
      radius: accuracy
    }).addTo(map);
  } else {
    accuracyCircle.setLatLng(newLatLng);
    accuracyCircle.setRadius(accuracy);
  }
  
 // locationUpdateCount++;
};

// Search function to find nearby destinations
const searchLocation = async (event) => {
  event.preventDefault(); // Prevent page refresh on Enter key
  
  if (!searchQuery.value || !map || !marker) return;
  
  loadingStatus.value = "Searching...";
  
  // Use current location to prioritize results near the user
  const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(searchQuery.value)}&limit=1&lat=${currentLocation.lat}&lon=${currentLocation.lng}`;
  
  try {
    const response = await fetch(url);
    const data = await response.json();
    
    if (data.length > 0) {
      const { lat, lon } = data[0]; // Get first result
      const destination = [parseFloat(lat), parseFloat(lon)];
      
      // Add marker for destination
      L.marker(destination).addTo(map)
        .bindPopup(`Destination: ${searchQuery.value}`)
        .openPopup();
      
      // Draw route from current location to destination
      drawRoute(destination);
      loadingStatus.value = "";
    } else {
      loadingStatus.value = "No matching locations found.";
      setTimeout(() => { loadingStatus.value = ""; }, 3000);
    }
  } catch (error) {
    console.error("Error fetching location:", error);
    loadingStatus.value = "Search failed. Check internet connection.";
    setTimeout(() => { loadingStatus.value = ""; }, 3000);
  }
};

// Function to draw route using Leaflet Routing Machine
const drawRoute = (destination) => {
  if (!map || !marker) return;
  
  try {
    // Check if routing machine is available
    if (!L.Routing || !L.Routing.control) {
      console.warn("Routing Machine not available");
      loadingStatus.value = "Navigation features unavailable";
      setTimeout(() => { loadingStatus.value = ""; }, 3000);
      return;
    }
    
    if (routingControl) {
      map.removeControl(routingControl); // Remove previous route if exists
    }
    
    routingControl = L.Routing.control({
      waypoints: [
        L.latLng(currentLocation.lat, currentLocation.lng), // User's current position
        L.latLng(destination) // Destination
      ],
      routeWhileDragging: true,
      createMarker: () => null, // Hide additional markers
      lineOptions: {
        styles: [{ color: '#6FA1EC', weight: 4 }]
      }
    }).addTo(map);
  } catch (error) {
    console.error("Error creating route:", error);
    loadingStatus.value = "Routing failed";
    setTimeout(() => { loadingStatus.value = ""; }, 3000);
  }
};

// Cleanup on component unmount
onUnmounted(() => {
  if (watchId !== null) {
    navigator.geolocation.clearWatch(watchId);
  }
  
  if (map) {
    map.remove();
    map = null;
  }
});
</script>

<style scoped>
.gps-view {
  width: 100%;
  height: 100%;
  position: relative;
  background-color: #f0f0f0;
}

.map-container {
  width: 100%;
  height: 100%;
  border-radius: 8px;
  background-color: #e5e5e5;
}

/* Search Box Styling */
.search-box {
  position: absolute;
  top: 10px;
  left: 50%;
  transform: translateX(-50%);
  width: 80%;
  max-width: 300px;
  padding: 10px;
  border-radius: 8px;
  border: none;
  box-shadow: 0 2px 6px rgba(0,0,0,0.3);
  outline: none;
  font-size: 14px;
  z-index: 1000;
}

.status-message {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  padding: 8px 16px;
  background-color: rgba(0,0,0,0.7);
  color: white;
  border-radius: 20px;
  font-size: 14px;
  z-index: 1000;
  max-width: 80%;
  text-align: center;
}

/* Debug elements */
.debug-info {
  position: absolute;
  top: 10px;
  right: 10px;
  background-color: rgba(0,0,0,0.7);
  color: white;
  padding: 10px;
  border-radius: 8px;
  z-index: 1000;
  font-size: 12px;
}

.debug-button {
  margin-top: 8px;
  padding: 5px 10px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}
</style>