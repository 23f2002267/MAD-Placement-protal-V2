<script setup>
import { computed, ref } from 'vue';

const props = defineProps({
  currentBtn: { type: String },
  user: {
    type: Object,
    default: null
  },
  role: {
    type: String,
    default: ''
  }
});

const query = ref('')
const res = ref([])
async function searchQuery() {
  const response = await fetch(`/api/search?query=${encodeURIComponent(query.value)}`)
  const data = await response.json()
  console.log(data)
  res.value = data
}

const studentnav = ['Profile', 'Dashboard', 'History'];
const companynav = ['Profile', 'Dashboard', 'Applicants', 'History'];
const adminnav = ['Dashboard', 'Students', 'Companies', 'Drives', 'Applications', 'About'];

const visibleNav = computed(() => {
  if (props.role === 'Admin') return adminnav;
  if (props.role === 'Company') return companynav;
  if (props.role === 'Student') return studentnav;
  return [];
});

const isMenuOpen = ref(false);

function toggleMenu() {
  isMenuOpen.value = !isMenuOpen.value;
}

const emit = defineEmits(['logout', 'update:currentBtn']);
</script>

<template>
    <nav class="navbar navbar-expand-lg shadow-sm" style="background-color: #3f4a5a !important;">
      <div class="container-fluid">
        <a class="navbar-brand text-success fw-bold" href="#">Place Port</a>
        <div class="ms-auto" v-if="user">
          <span class="navbar-text text-white me-4">
            {{ user.email }} <span class="badge bg-light text-primary">{{ role }}</span>
          </span>
          <button class="btn btn-sm btn-outline-light" @click='$emit("logout")'>Logout</button>
        </div>
      </div>
    </nav>

<nav v-if="user" class="navbar navbar-expand-lg shadow-sm" style="background-color: #3f4a5a !important;">
  <div class="container-fluid">
    <button class="navbar-toggler" type="button" @click="toggleMenu" aria-label="Toggle navigation">
      <span class="navbar-toggler-icon"></span>
    </button>
    <div v-show="isMenuOpen" class="collapse navbar-collapse show">
      <ul class="nav navpills">
        <li v-for="btn in visibleNav" :key="btn" class="nav-item dropdown">
          <a class="nav-link" :class="props.currentBtn === btn ? 'text-white fw-bold' : 'text-white'"
           href="#" @click.prevent="$emit('update:currentBtn', btn)">{{ btn }}</a>
        </li>
      </ul>
    </div>
        <form class="d-flex" @submit.prevent="searchQuery">
            <input v-model="query" class="form-control me-2" type="search" placeholder="Search">
            <button class="btn btn-outline-light" type="submit">Search</button>
        </form>
  </div>
</nav>
  <!-- Results section -->
  <div v-if="res.length" class="mt-3 container">
    <h5>Search Results</h5>
    <ul class="list-group">
      <li v-for="r in res" :key="r.rowid" class="list-group-item">
        {{ r.username || r.name }}
      </li>
    </ul>
  </div>
</template>