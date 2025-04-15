<template>
    <div class="traffic-sign-display">
      <h4>Upcoming Signs</h4>
      <div 
        v-for="sign in signs" 
        :key="sign.id"
        class="sign-item"
      >
        <div class="sign-icon" :class="'sign-' + sign.type">
          <span v-if="sign.type === 'speed_limit'">{{ sign.value }}</span>
          <span v-else-if="sign.type === 'stop'">STOP</span>
          <span v-else>⚠️</span>
        </div>
        <div class="sign-distance">{{ sign.distance }}</div>
      </div>
    </div>
  </template>
  
  <script setup>
import { defineProps } from 'vue';

defineProps({
  signs: {
    type: Array,
    default: () => []
  }
});
</script>
  
  <style scoped>
  .traffic-sign-display {
    padding: 10px;
    height: 100%;
  }
  
  h4 {
    margin-top: 0;
    margin-bottom: 10px;
    text-align: center;
  }
  
  .sign-item {
    display: flex;
    align-items: center;
    margin-bottom: 10px;
  }
  
  .sign-icon {
    width: 50px;
    height: 50px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    margin-right: 10px;
  }
  
  .sign-speed_limit {
    background-color: white;
    color: black;
    border: 2px solid red;
  }
  
  .sign-stop {
    background-color: red;
    color: white;
    border: 2px solid white;
  }
  
  .sign-distance {
    font-size: 12px;
  }
  </style>