<script setup>
import { ref } from 'vue'
const props = defineProps({
  title: { type: String, default: () => 'No Data' },
  data: { type: Number, default: () => 0 },
  color: { type: String, default: () => '#1eb0cd' },
  link: { type: String, default: () => '#'}
});

const emit = defineEmits(['click'])
const bg = ref(props.color)
const hoverColor = '#272424a5'

function onMouseEnter() {
  bg.value = hoverColor
}

function onMouseLeave() {
  bg.value = props.color
}

function onClick() {
  emit('click')
}
</script>

<template>
  <div class="text-decoration-none text-primary" style="cursor:pointer" @click="onClick">
    <div class="stats-box size-lim" :style="{ backgroundColor: bg }" @mouseenter="onMouseEnter" @mouseleave="onMouseLeave" >
      <h5>{{ props.title }}</h5>
      <h3>{{ props.data }}</h3>
    </div>
  </div>
</template>

<style scoped>
.size-lim{
  max-width : 350px;
}
</style>