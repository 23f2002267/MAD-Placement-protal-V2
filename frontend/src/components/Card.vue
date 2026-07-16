<script setup>
defineProps({
  title: { type: String, default: 'No Data' },
  data: { type: Number, default: 0 },
  color: { type: String, default: '#1eb0cd' }
});

const emit = defineEmits(['click']);

function onClick() {
  emit('click');
}
</script>

<template>
  <button 
    type="button"
    class="card-action-wrapper text-start border-0 bg-transparent p-0 w-100" 
    @click="onClick"
  >
    <div class="stats-box size-lim text-white p-3 rounded-3 shadow-sm" :style="{ '--card-bg': color }">
      <h5 class="fw-normal mb-1 opacity-75">{{ title }}</h5>
      <h3 class="fw-bold m-0">{{ data }}</h3>
    </div>
  </button>
</template>

<style scoped>
.size-lim {
  max-width: 350px;
}

.stats-box {
  background-color: var(--card-bg);
  transition: background-color 0.2s ease-in-out, transform 0.15s ease-in-out;
}

.stats-box:hover {
  background-color: #272424a5 !important;
  transform: translateY(-2px);
}

.stats-box:active {
  transform: translateY(0px);
}

.card-action-wrapper:focus-visible .stats-box {
  outline: 3px solid #0d6efd;
  outline-offset: 2px;
}
</style>