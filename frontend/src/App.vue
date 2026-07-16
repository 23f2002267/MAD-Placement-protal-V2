<script setup>
import { ref, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import NavBar from './components/NavBar.vue';

const router = useRouter();

const user = ref(JSON.parse(localStorage.getItem('user')) || null);
const role = ref(localStorage.getItem('role') || '');
const authMode = ref('login');
const currentBtn = ref('Dashboard');

const stats = ref({ students: 0, companies: 0, drives: 0, applications: 0, bl_stud: 0, bl_comp: 0 });
const pendingCompanies = ref([]);
const pendingDrives = ref([]);
const adminUser = ref([]);
const adminDrives = ref([]);
const adminApplications = ref([]);
const allDrives = ref([]);
const companyDrives = ref([]);
const companyProfile = ref({ id: 0, name: '', website: '', status: 'Pending' });
const studentProfile = ref({ id: 0, name: '', branch_cgpa: {}, resume: '', education: '', skills: '', experience: '' });
const companyApplications = ref([]);
const studentApplications = ref([]);
const notifications = ref([]);

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
    localStorage.setItem('blacklist', String(data.blacklist));
    
    await fetchDashboardData();
    
    if (data.role === 'Admin') router.push('/admin');
    else if (data.role === 'Student') router.push('/student');
    else if (data.role === 'Company') router.push('/company');
  } else {
    alert(data.message || 'Request failed');
  }
}

async function apiFetch(url, options = {}) {
  const headers = options.headers || {};
  if (user.value?.token) {
    headers['Authentication-Token'] = user.value.token;
  }
  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...headers
    }
  });
  if (res.status === 401 && url !== '/api/logout') {
    logout();
  }
  return res;
}

async function fetchDashboardData() {
  if (!user.value) return;
  
  fetchNotifications();

  if (role.value === 'Admin') {
    const s = await apiFetch('/api/admin/stats');
    if (s.ok) stats.value = await s.json();
    
    const c = await apiFetch('/api/admin/pending-companies');
    if (c.ok) pendingCompanies.value = await c.json();
    
    const d = await apiFetch('/api/admin/pending-drives');
    if (d.ok) pendingDrives.value = await d.json();
    
    const u = await apiFetch('/api/admin/search');
    if (u.ok) adminUser.value = await u.json();
    
    const k = await apiFetch('/api/admin/drive');
    if (k.ok) adminDrives.value = await k.json();
    
    const j = await apiFetch('/api/admin/application');
    if (j.ok) adminApplications.value = await j.json();
    
  } else if (role.value === 'Student') {
    const d = await apiFetch('/api/student/drives');
    allDrives.value = d.ok ? await d.json() : [];
    
    const a = await apiFetch('/api/student/applications');
    studentApplications.value = a.ok ? await a.json() : [];
    
    const p = await apiFetch('/api/student/profile');
    if (p.ok) studentProfile.value = await p.json();
    
  } else if (role.value === 'Company') {
    const d = await apiFetch(`/api/company/drives/${user.value?.id}`);
    companyDrives.value = d.ok ? await d.json() : [];
    
    const p = await apiFetch('/api/company/profile');
    if (p.ok) companyProfile.value = await p.json();
    
    const a = await apiFetch('/api/company/applications');
    companyApplications.value = a.ok ? await a.json() : [];
  }
}

// global Async Emitters Event Handlers
async function updateApplicationStatus({ appId, status, feedback, interview_time, interview_link, offer_letter_link }) {
  const res = await apiFetch(`/api/company/applications/${appId}/status`, {
    method: 'POST',
    body: JSON.stringify({ status, feedback, interview_time, interview_link, offer_letter_link })
  });
  const data = await res.json();
  alert(data.message || 'Status updated successfully');
  await fetchDashboardData();
}

async function updateDriveStatus({ driveId, status }) {
  const res = await apiFetch(`/api/company/drives/${driveId}/status`, {
    method: 'POST',
    body: JSON.stringify({ status })
  });
  const data = await res.json();
  alert(data.message || 'Drive status updated successfully');
  await fetchDashboardData();
}

async function saveCompanyProfile(profileData) {
  const res = await apiFetch('/api/company/profile', {
    method: 'POST',
    body: JSON.stringify(profileData)
  });
  const data = await res.json();
  alert(data.message || 'Profile updated successfully');
  if (res.ok) {
    companyProfile.value = data.company;
    await fetchDashboardData();
  }
}

async function saveStudentProfile(profileData) {
  const res = await apiFetch('/api/student/profile', {
    method: 'POST',
    body: JSON.stringify(profileData)
  });
  const data = await res.json();
  alert(data.message || 'Profile updated successfully');
  if (res.ok) {
    studentProfile.value = data.student;
    await fetchDashboardData();
  }
}

async function approveCompany(id) {
  await apiFetch(`/api/admin/approve-company/${id}`, { method: 'POST' });
  await fetchDashboardData();
}

async function approveDrive(id) {
  await apiFetch(`/api/admin/approve-drive/${id}`, { method: 'POST' });
  await fetchDashboardData();
}

async function rejectCompany(id) {
  await apiFetch(`/api/admin/reject-company/${id}`, { method: 'POST' });
  await fetchDashboardData();
}

async function rejectDrive(id) {
  await apiFetch(`/api/admin/reject-drive/${id}`, { method: 'POST' });
  await fetchDashboardData();
}

async function blacklistUser(id) {
  await apiFetch(`/api/admin/blacklist-user/${id}`, { method: 'POST' });
  await fetchDashboardData();
}

async function deleteUser(id) {
  if (window.confirm("Delete User id?")) {
    const res = await apiFetch(`/api/admin/delete-user/${id}`, { method: 'POST' });
    const resData = await res.json();
    await fetchDashboardData();
    alert(resData.message);
  }
}

async function saveDrive(newDrive) {
  const res = await apiFetch('/api/company/create-drive', {
      method: 'POST',
      body: JSON.stringify(newDrive)
  });
  const data = await res.json();
  alert(data.message);
  await fetchDashboardData();
}

async function applyDrive(id) {
  const res = await apiFetch('/api/student/apply', {
    method: 'POST',
    body: JSON.stringify({ user_id: user.value?.id, drive_id: id })
  });
  const data = await res.json();
  alert(data.message);
  await fetchDashboardData();
}

async function fetchNotifications() {
  if (!user.value) return;
  const res = await apiFetch('/api/notifications');
  if (res.ok) {
    notifications.value = await res.json();
  }
}

async function dismissNotification(id) {
  const res = await apiFetch(`/api/notifications/${id}/read`, { method: 'POST' });
  if (res.ok) {
    await fetchNotifications();
  }
}

async function markAllAsRead() {
  const res = await apiFetch('/api/notifications/read-all', { method: 'POST' });
  if (res.ok) {
    await fetchNotifications();
  }
}

async function triggerStudentExport() {
  const res = await apiFetch('/api/student/export-csv', { method: 'POST' });
  const data = await res.json();
  alert(data.message || 'Export started');
}

async function triggerCompanyExport() {
  const res = await apiFetch('/api/company/export-csv', { method: 'POST' });
  const data = await res.json();
  alert(data.message || 'Export started');
}
async function logout() {
  await apiFetch('/api/logout', { method: 'POST' });
  user.value = null;
  role.value = '';
  localStorage.clear();
  router.push('/');
}

function formatTime(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + ' ' + d.toLocaleDateString();
}

watch(role, (newRole) => {
  if (newRole && router.currentRoute.value.path === '/') {
    if (newRole === 'Admin') router.push('/admin');
    else if (newRole === 'Student') router.push('/student');
    else if (newRole === 'Company') router.push('/company');
  }
});

onMounted(() => {
  if (user.value) {
    fetchDashboardData();
  }
  
  //alerts polling intervals matching worker completions
  setInterval(() => {
    if (user.value) {
      fetchNotifications();
    }
  }, 10000);
});
</script>

<template>
  <div>
    <NavBar :user="user" :role="role" v-model:currentBtn="currentBtn" @logout="logout" />
    
    <div class="container mt-4">
      <!-- notification -->
      <div v-if="user && currentBtn === 'Notification'" class="row mb-4">
        <div class="col-12">
          <div class="card border-0 shadow-sm rounded-4 p-4 bg-white">
            <div class="d-flex justify-content-between align-items-center mb-3">
              <h5 class="fw-bold text-dark m-0 d-flex align-items-center">
                <span class="me-2">🔔</span> Notifications & Alerts
                <span class="badge bg-danger rounded-pill ms-2" style="font-size: 0.75rem;">
                  {{ notifications.length }}
                </span>
              </h5>
              <button class="btn btn-sm btn-link text-muted text-decoration-none p-0 fw-semibold" @click="markAllAsRead">
                Mark all as read
              </button>
            </div>
            <div class="d-flex flex-column gap-2">
              <div v-for="notif in notifications" :key="notif.id" class="alert alert-info alert-dismissible fade show border-0 rounded-3 shadow-sm m-0 py-3 p-3 pe-5" role="alert" style="background-color: #f0f7ff; color: #1e3a8a;">
                <div class="d-flex align-items-center">
                  <span class="fs-4 me-3" v-if="notif.message.includes('Reminder')">⏰</span>
                  <span class="fs-4 me-3" v-else-if="notif.message.includes('export') || notif.message.includes('complete')">📥</span>
                  <span class="fs-4 me-3" v-else>📊</span>
                  <div class="flex-grow-1">
                    <p class="m-0 fw-semibold text-dark">{{ notif.message }}</p>
                    <a v-if="notif.link" :href="notif.link" target="_blank" class="btn btn-sm btn-primary mt-2 fw-semibold rounded-pill px-3 py-1">
                      📁 Download File
                    </a>
                    <small class="text-muted d-block mt-1" style="font-size: 0.7rem;">
                      {{ formatTime(notif.created_at) }}
                    </small>
                  </div>
                </div>
                <button type="button" class="btn-close" @click="dismissNotification(notif.id)" aria-label="Close"></button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- root app router view port -->
      <router-view 
        :user="user"
        :auth-mode="authMode"
        :current-btn="currentBtn"
        :stats="stats"
        :pending-companies="pendingCompanies"
        :pending-drives="pendingDrives"
        :user-search="adminUser"
        :drives="role === 'Student' ? allDrives : (role === 'Company' ? companyDrives : adminDrives)"
        :applications="role === 'Student' ? studentApplications : (role === 'Company' ? companyApplications : adminApplications)"
        :profile="role === 'Student' ? studentProfile : companyProfile"
        @toggle-mode="toggleAuthMode"
        @submit-auth="handleAuth"
        @apply-drive="applyDrive"
        @update-profile="role === 'Student' ? saveStudentProfile : saveCompanyProfile"
        @approve-company="approveCompany"
        @approve-drive="approveDrive"
        @reject-company="rejectCompany"
        @reject-drive="rejectDrive"
        @blacklist-user="blacklistUser"
        @delete-user="deleteUser"
        @select-view="currentBtn = $event"
        @save-drive="saveDrive"
        @update-application-status="updateApplicationStatus"
        @update-drive-status="updateDriveStatus"
        @trigger-student-export="triggerStudentExport"
        @trigger-company-export="triggerCompanyExport"
      />
    </div>
  </div>
</template>

<style>
.transition-all {
  transition: all 0.2s ease-in-out;
}
</style>