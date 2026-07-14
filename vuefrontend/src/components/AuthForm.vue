<script setup>
import { reactive, computed } from 'vue';

const props = defineProps({
  authMode: { type: String, default: 'login' }
});

const emit = defineEmits(['submit-auth', 'toggle-mode']);

const form = reactive({ email: 'admin@placeport.com', password: '', role: 'Student', name: '' });

const modeLabel = computed(() => props.authMode === 'login' ? 'Login' : 'Register');

function submitAuth() {
  emit('submit-auth', { ...form });
}

function toggleMode() {
  emit('toggle-mode');
}
</script>

<template>
  <div class="card p-4 shadow-sm">
    <h2 class="text-center mb-4">{{ modeLabel }}</h2>

    <div class="mb-3">
      <label class="form-label">Email</label>
      <input v-model="form.email" type="email" class="form-control" placeholder="admin@placeport.com" />
    </div>

    <div class="mb-3">
      <label class="form-label">Password</label>
      <input v-model="form.password" type="password" class="form-control" />
    </div>

    <div v-if="authMode === 'register'" class="mb-3">
      <label class="form-label">Role</label>
      <select v-model="form.role" class="form-select">
        <option value="Student">Student</option>
        <option value="Company">Company</option>
      </select>
    </div>

    <div v-if="authMode === 'register'" class="mb-3">
      <label class="form-label">Name</label>
      <input v-model="form.name" type="text" class="form-control" />
    </div>

    <button class="btn btn-primary w-100" @click="submitAuth">
      {{ authMode === 'login' ? 'Sign In' : 'Sign Up' }}
    </button>

    <div class="text-center mt-3">
      <a href="#" @click.prevent="toggleMode">
        {{ authMode === 'login' ? 'Create an account' : 'Back to login' }}
      </a>
    </div>
  </div>
</template>