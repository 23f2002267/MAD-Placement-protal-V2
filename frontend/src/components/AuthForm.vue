<script setup>
import { reactive, computed } from 'vue';

const props = defineProps({
  authMode: { type: String, default: 'login' }
});

const emit = defineEmits(['submit-auth', 'toggle-mode']);

const form = reactive({ email: '', password: '', role: 'Student', name: '' });

const modeLabel = computed(() => props.authMode === 'login' ? 'Login' : 'Register');

function submitAuth() {
  if (!form.email || !form.password) {
    alert('Please fill out all required fields.');
    return;
  }
  if (props.authMode === 'register' && !form.name) {
    alert('Please provide your name to register.');
    return;
  }
  emit('submit-auth', { ...form });
}

function toggleMode() {
  form.password = '';
  emit('toggle-mode');
}
</script>

<template>
  <div class="card p-4 shadow-sm auth-card-limiter mx-auto mt-5">
    <h2 class="text-center mb-4">{{ modeLabel }}</h2>

    <form @submit.prevent="submitAuth">
      <div class="mb-3">
        <label class="form-label">Email</label>
        <input v-model="form.email" type="email" class="form-control" required />
      </div>

      <div class="mb-3">
        <label class="form-label">Password</label>
        <input v-model="form.password" type="password" class="form-control" required />
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
        <input v-model="form.name" type="text" class="form-control" required />
      </div>

      <button type="submit" class="btn btn-primary w-100">
        {{ authMode === 'login' ? 'Sign In' : 'Sign Up' }}
      </button>
    </form>

    <div class="text-center mt-3">
      <a href="#" @click.prevent="toggleMode">
        {{ authMode === 'login' ? 'Create an account' : 'Back to login' }}
      </a>
    </div>
  </div>
</template>
<style scoped>
.auth-card-limiter {
  width: 100%;
  max-width: 420px; 
}
</style>p