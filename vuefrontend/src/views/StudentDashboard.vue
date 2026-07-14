<script setup>
defineProps({
  drives: { type: Array, default: () => [] }
});

defineEmits(['apply-drive']);
</script>

<template>
  <div>
    <h3 class="mb-3">Available Drives</h3>
    <div class="row">
      <div class="col-md-8">
        <div v-for="d in drives" :key="d.id" class="card p-3 mb-3">
          <h5>{{ d.title }}</h5>
          <p class="text-muted mb-2">{{ d.company }} | Min CGPA: {{ d.min_cgpa }}</p>
          <p>{{ d.description }}</p>
          <button class="btn btn-sm btn-primary" @click="$emit('apply-drive', d.id)" :disabled="d.applied">
            {{ d.applied ? 'Applied' : 'Apply Now' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>