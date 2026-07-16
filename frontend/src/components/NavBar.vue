<script setup>
import { computed, ref } from 'vue';

const props = defineProps({
  currentBtn: { type: String },
  user: { type: Object, default: null },
  role: { type: String, default: '' }
});

const emit = defineEmits(['logout', 'update:currentBtn']);

const isMenuOpen = ref(false);

function toggleMenu() {
  isMenuOpen.value = !isMenuOpen.value;
}

const studentnav = ['Profile', 'Dashboard', 'History', 'Notification'];
const companynav = ['Profile', 'Dashboard', 'History', 'Notification'];
const adminnav = ['Profile', 'Dashboard', 'Students', 'Companies', 'Drives', 'Applications', 'About', 'Notification'];

const visibleNav = computed(() => {
  if (props.role === 'Admin') return adminnav;
  if (props.role === 'Company') return companynav;
  if (props.role === 'Student') return studentnav;
  return [];
});
</script>

<template>
  <nav class="navbar navbar-expand-lg navbar-dark shadow-sm" style="background-color: #3f4a5a !important;">
    <div class="container-fluid">
      <a class="navbar-brand text-success fw-bold" href="#">Place Port</a>
      
      <button v-if="user" class="navbar-toggler" type="button" @click="toggleMenu" aria-label="Toggle navigation">
        <span class="navbar-toggler-icon"></span>
      </button>

      <div class="collapse navbar-collapse" :class="{ 'show': isMenuOpen && user }">
        <ul v-if="user" class="navbar-nav me-auto mb-2 mb-lg-0">
          <li v-for="btn in visibleNav" :key="btn" class="nav-item">
            <a 
              class="nav-link" 
              :class="props.currentBtn === btn ? 'active fw-bold text-white' : 'text-light'"
              href="#" 
              @click.prevent="emit('update:currentBtn', btn)"
            >
              {{ btn }}
            </a>
          </li>
        </ul>

        <div class="d-flex align-items-center ms-auto flex-wrap gap-3" v-if="user">

          <span class="navbar-text text-white">
            {{ user.email }} <span class="badge bg-light text-primary ms-1">{{ role }}</span>
          </span>
          
          <button class="btn btn-sm btn-outline-danger" @click="emit('logout')">Logout</button>
        </div>
      </div>
    </div>
  </nav>

</template>