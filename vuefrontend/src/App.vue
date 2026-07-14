<script setup>
import { ref, onMounted } from 'vue';
import NavBar from './components/NavBar.vue';
import AuthForm from './components/AuthForm.vue';
import AdminDashboard from './views/AdminDashboard.vue';
import StudentDashboard from './views/StudentDashboard.vue';
import CompanyDashboard from './views/CompanyDashboard.vue';

const user = ref(JSON.parse(localStorage.getItem('user')) || null);
const role = ref(localStorage.getItem('role') || '');
const authMode = ref('login');
const stats = ref({ students: 0, companies: 0, drives: 0, applications: 0 });
const pendingCompanies = ref([]);
const pendingDrives = ref([]);
const adminUser = ref([]);
const adminDrives = ref([]);
const adminApplications = ref([]);
const allDrives = ref([]);
const companyDrives = ref([]);
const currentBtn = ref('Dashboard')

function toggleAuthMode() {
  authMode.value = authMode.value === 'login' ? 'register' : 'login';
}

async function handleAuth(form) {
  const endpoint = authMode.value === 'login' ? '/api/login' : '/api/register';
  const res = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(form)
  });
  const data = await res.json();

  if (res.ok) {
    user.value = data;
    role.value = data.role;
    localStorage.setItem('user', JSON.stringify(data));
    localStorage.setItem('role', data.role);
    await fetchDashboardData();
  } else {
    alert(data.message || 'Request failed');
  }
}

async function fetchDashboardData() {
  if (role.value === 'Admin') {
    const s = await fetch('/api/admin/stats');
    stats.value = await s.json();
    console.log(stats.value)
    const c = await fetch('/api/admin/pending-companies');
    pendingCompanies.value = await c.json();
    const d = await fetch('/api/admin/pending-drives');
    pendingDrives.value = await d.json();
    const u = await fetch('/api/admin/search');
    adminUser.value = await u.json();
    const k = await fetch('/api/admin/drive');
    adminDrives.value = await k.json();
    const j = await fetch('/api/admin/application');
    adminApplications.value = await j.json();
  } else if (role.value === 'Student') {
    const d = await fetch('/api/student/drives');
    allDrives.value = await d.json();
  } else if (role.value === 'Company') {
    const d = await fetch(`/api/company/drives/${user.value?.id}`);
    companyDrives.value = await d.json();
  }
}


async function approveCompany(id) {
  await fetch(`/api/admin/approve-company/${id}`, { method: 'POST' });
  await fetchDashboardData();
}

async function approveDrive(id) {
  await fetch(`/api/admin/approve-drive/${id}`, { method: 'POST' });
  await fetchDashboardData();
}
async function rejectCompany(id) {
  await fetch(`/api/admin/reject-company/${id}`, { method: 'POST' });
  await fetchDashboardData();
}
async function rejectDrive(id) {
  await fetch(`/api/admin/reject-drive/${id}`, { method: 'POST' });
  await fetchDashboardData();
}
async function blacklistUser(id) {
  await fetch(`/api/admin/blacklist-user/${id}`, { method: 'POST' });
  await fetchDashboardData();
}
async function deleteUser(id) {
  const conf = window.confirm("Delete User id ?")
  if (conf) {
    const res = await fetch(`/api/admin/delete-user/${id}`, { method: 'POST' });
    await fetchDashboardData();
    alert(res.message)
  }
}

async function saveDrive(newDrive) {
  const res = await fetch('/api/company/create-drive', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newDrive)
  });
  const data = await res.json();
  alert(data.message);
  await fetchDashboardData();

  }

async function applyDrive(id) {
  const res = await fetch('/api/student/apply', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: user.value?.id, drive_id: id })
  });
  const data = await res.json();
  alert(data.message);
  await fetchDashboardData();
}

function logout() {
  user.value = null;
  role.value = '';
  localStorage.clear();
  fetch('/api/logout', { method: 'POST' });
}

function viewDetails(item) {
  console.log('View details', item);
}

onMounted(() => {
  if (user.value) {
    fetchDashboardData();
  }
});
</script>

<template>
  <div>
    
    <NavBar :user="user" :role="role" v-model:currentBtn="currentBtn" @logout="logout" />
    
    <div class="container mt-4">
      <div v-if="!user" class="row justify-content-center">
        <div class="col-md-5 mt-5">
          <AuthForm :auth-mode="authMode" @submit-auth="handleAuth" @toggle-mode="toggleAuthMode" />
        </div>
      </div>

      <div v-else-if="role === 'Admin'">
        <AdminDashboard
          :current-btn="currentBtn"
          :stats="stats"
          :pending-companies="pendingCompanies"
          :pending-drives="pendingDrives"
          :user-search="adminUser"
          :drives="adminDrives"
          :applications="adminApplications"
          @approve-company="approveCompany"
          @approve-drive="approveDrive"
          @reject-company="rejectCompany"
          @reject-drive="rejectDrive"
          @blacklist-user="blacklistUser"
          @delete-user="deleteUser"
          @select-view="currentBtn = $event"
          @view-details="viewDetails"
        />
      </div>

      <div v-else-if="role === 'Student'">
        <StudentDashboard :drives="allDrives" @apply-drive="applyDrive" />
      </div>

      <div v-else-if="role === 'Company'">
        <CompanyDashboard 
        :user="user"
        :drives="companyDrives"
        @save-drive="saveDrive"
        />
      </div>
    </div>
  </div>
</template>