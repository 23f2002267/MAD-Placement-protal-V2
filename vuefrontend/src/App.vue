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
const companyProfile = ref({ id: 0, name: '', website: '', status: 'Pending' });
const studentProfile = ref({ id: 0, name: '', branch_cgpa: {}, resume: '', education: '', skills: '', experience: '' });
const companyApplications = ref([]);
const studentApplications = ref([]);
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
  if (role.value === 'Admin') {
    const s = await apiFetch('/api/admin/stats');
    if (s.ok) {
      stats.value = await s.json();
    }
    const c = await apiFetch('/api/admin/pending-companies');
    if (c.ok) {
      pendingCompanies.value = await c.json();
    }
    const d = await apiFetch('/api/admin/pending-drives');
    if (d.ok) {
      pendingDrives.value = await d.json();
    }
    const u = await apiFetch('/api/admin/search');
    if (u.ok) {
      adminUser.value = await u.json();
    }
    const k = await apiFetch('/api/admin/drive');
    if (k.ok) {
      adminDrives.value = await k.json();
    }
    const j = await apiFetch('/api/admin/application');
    if (j.ok) {
      adminApplications.value = await j.json();
    }
  } else if (role.value === 'Student') {
    const d = await apiFetch('/api/student/drives');
    if (d.ok) {
      allDrives.value = await d.json();
    } else {
      allDrives.value = [];
    }
    const a = await apiFetch('/api/student/applications');
    if (a.ok) {
      studentApplications.value = await a.json();
    } else {
      studentApplications.value = [];
    }
    const p = await apiFetch('/api/student/profile');
    if (p.ok) {
      studentProfile.value = await p.json();
    }
  } else if (role.value === 'Company') {
    const d = await apiFetch(`/api/company/drives/${user.value?.id}`);
    if (d.ok) {
      companyDrives.value = await d.json();
    } else {
      companyDrives.value = [];
    }
    const p = await apiFetch('/api/company/profile');
    if (p.ok) {
      companyProfile.value = await p.json();
    }
    const a = await apiFetch('/api/company/applications');
    if (a.ok) {
      companyApplications.value = await a.json();
    } else {
      companyApplications.value = [];
    }
  }
}

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
  const conf = window.confirm("Delete User id ?")
  if (conf) {
    const res = await apiFetch(`/api/admin/delete-user/${id}`, { method: 'POST' });
    const resData = await res.json();
    await fetchDashboardData();
    alert(resData.message)
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

function logout() {
  user.value = null;
  role.value = '';
  localStorage.clear();
  apiFetch('/api/logout', { method: 'POST' });
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
          :user="user"
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
        <StudentDashboard 
          :drives="allDrives" 
          :applications="studentApplications" 
          :profile="studentProfile" 
          @apply-drive="applyDrive" 
          @update-profile="saveStudentProfile" 
        />
      </div>

      <div v-else-if="role === 'Company'">
        <CompanyDashboard 
        :user="user"
        :drives="companyDrives"
        :profile="companyProfile"
        :applications="companyApplications"
        @save-drive="saveDrive"
        @update-profile="saveCompanyProfile"
        @update-application-status="updateApplicationStatus"
        @update-drive-status="updateDriveStatus"
        />
      </div>
    </div>
  </div>
</template>