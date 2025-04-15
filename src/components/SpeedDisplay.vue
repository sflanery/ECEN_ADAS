<template>
    <div class="speed-display">
      <div class="speed-value">{{ speed }}</div>
      <div class="speed-unit">MPH</div>
    </div>
  </template>
<script setup>
import { defineProps } from 'vue';

defineProps({
  speed: {
    type: Number,
    default: 0
  }
});
</script>
  
  <style scoped>
  .speed-display {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: 200px;
    height: 200px;
    background-color: #282828;
    border-radius: 50%;
    margin: 0 auto;
  }
  
  .speed-value {
    font-size: 60px;
    font-weight: bold;
  }
  
  .speed-unit {
    font-size: 20px;
    margin-top: 5px;
  }
  </style>