<script setup>
import { computed, ref, watch } from 'vue';
import { Modal } from 'bootstrap';
import Card from '../components/Card.vue';
import AdminList from '../components/AdminList.vue';

const props = defineProps({
  user: { type: Object, default: null },
  currentBtn: { type: String, default: 'Dashboard' },
  stats: { type: Object, default: () => ({ students: 0, companies: 0, drives: 0, applications: 0, bl_stud: 0, bl_comp: 0 }) },
  pendingCompanies: { type: Array, default: () => [] },
  pendingDrives: { type: Array, default: () => [] },
  userSearch: { type: Array, default: () => [] },
  drives: { type: Array, default: () => [] },
  applications: { type: Array, default: () => [] }
});

const emit = defineEmits([
  'approve-company', 'approve-drive', 'reject-company', 'reject-drive', 
  'select-view', 'view-details', 'blacklist-user', 'delete-user', 'update-user-email'
]);

const adminForm = ref({ username: '', email: '', password: '' });
const savingProfile = ref(false);
let bootstrapModalInstance = null; // Single tracking handle to prevent duplicate layers

async function fetchAdminProfile() {
  try {
    const headers = { 'Content-Type': 'application/json' };
    if (props.user?.token) {
      headers['Authentication-Token'] = props.user.token;
    }
    const res = await fetch('/api/admin/profile', { headers });
    if (res.ok) {
      const data = await res.json();
      adminForm.value.username = data.username || '';
      adminForm.value.email = data.email || '';
      adminForm.value.password = '';
    }
  } catch (err) {
    console.error('Failed to load admin profile', err);
  }
}

async function handleUpdateProfile() {
  savingProfile.value = true;
  try {
    const headers = { 'Content-Type': 'application/json' };
    if (props.user?.token) {
      headers['Authentication-Token'] = props.user.token;
    }
    const res = await fetch('/api/admin/profile', {
      method: 'POST',
      headers,
      body: JSON.stringify({
        username: adminForm.value.username,
        email: adminForm.value.email,
        password: adminForm.value.password || undefined
      })
    });
    const data = await res.json();
    if (res.ok) {
      alert(data.message || 'Profile updated successfully!');
      adminForm.value.password = '';
      if (props.user) {
        localStorage.setItem('user', JSON.stringify({ ...props.user, email: adminForm.value.email }));
      }
    } else {
      alert(data.message || 'Failed to update profile');
    }
  } catch (err) {
    alert('An error occurred while updating profile.');
  } finally {
    savingProfile.value = false;
  }
}

watch(() => props.currentBtn, (newBtn) => {
  if (newBtn === 'Profile') {
    fetchAdminProfile();
  }
}, { immediate: true });

const selectedDrive = ref(null);
const studentProfileRef = ref(null);
const loadingProfile = ref(false);
const errorProfile = ref('');

const viewingType = computed(() => {
  if (!selectedDrive.value) return '';
  if (selectedDrive.value.role === 'Student') return 'Student';
  if (selectedDrive.value.role === 'Company') return 'Company';
  if (selectedDrive.value.drive_title !== undefined) return 'Application';
  return 'Drive';
});

const studentApplications = computed(() => {
  if (!studentProfileRef.value || !Array.isArray(props.applications)) return [];
  return props.applications.filter(app => app.student_id === studentProfileRef.value.id);
});

const driveApplications = computed(() => {
  if (viewingType.value !== 'Drive' || !selectedDrive.value || !Array.isArray(props.applications)) return [];
  return props.applications.filter(app => app.drive_id === selectedDrive.value.id);
});

const companyDrivesList = computed(() => {
  if (viewingType.value !== 'Company' || !selectedDrive.value || !Array.isArray(props.drives)) return [];
  return props.drives.filter(drive => drive.company_id === selectedDrive.value.id || drive.company === selectedDrive.value.username);
});

async function onViewDetails(item) {
  selectedDrive.value = item;
  studentProfileRef.value = null;
  errorProfile.value = '';
  
  if (!bootstrapModalInstance) {
    const element = document.getElementById('driveModal');
    bootstrapModalInstance = Modal.getOrCreateInstance(element);
  }
  bootstrapModalInstance.show();

  if (item.role === 'Student') {
    loadingProfile.value = true;
    try {
      const headers = { 'Content-Type': 'application/json' };
      if (props.user?.token) {
        headers['Authentication-Token'] = props.user.token;
      }
      const res = await fetch(`/api/student/profile/user/${item.id}`, { headers });
      if (res.ok) {
        studentProfileRef.value = await res.json();
      } else {
        errorProfile.value = 'Could not fetch student profile details.';
      }
    } catch (e) {
      errorProfile.value = 'Failed to load profile.';
    } finally {
      loadingProfile.value = false;
    }
  }
}

const cards = computed(() => [
  [
    { title: 'Students', color: '#1ecd6a', data: props.stats?.students ?? 0 },
    { title: 'Applications', color: '#46eebf', data: props.stats?.applications ?? 0 },
    { title: 'Blacklisted Students', color: '#bc5d40', data: props.stats?.bl_stud ?? 0 }
  ],
  [
    { title: 'Companies', color: '#1d61cd', data: props.stats?.companies ?? 0 },
    { title: 'Drives', color: '#70cd1e', data: props.stats?.drives ?? 0 },
    { title: 'Blacklisted Companies', color: '#cd381e', data: props.stats?.bl_comp ?? 0 } // Fixed tracking key bug
  ]
]);

function handleCardTap(card) {
  const target = card.title;
  if (target === 'Students' || target === 'Companies' || target === 'Drives' || target === 'Applications') {
    emit('select-view', target);
  }
}

const studentsList = computed(() => Array.isArray(props.userSearch) ? props.userSearch.filter(u => u.role === 'Student') : []);
const companiesList = computed(() => Array.isArray(props.userSearch) ? props.userSearch.filter(u => u.role === 'Company') : []);
const drivesList = computed(() => Array.isArray(props.drives) ? props.drives : []);
const applicationsList = computed(() => Array.isArray(props.applications) ? props.applications : []);
const pendingCompaniesList = computed(() => Array.isArray(props.pendingCompanies) ? props.pendingCompanies : []);
const pendingDrivesList = computed(() => Array.isArray(props.pendingDrives) ? props.pendingDrives : []);
</script>

<template>
  <div class='mt-4 pt-4'>
    <template v-if="props.currentBtn === 'Dashboard'">
      <div v-for="(ro, roi) in cards" :key="roi" class="row justify-content-center mx-4 my-4">
        <div v-for="(card, coi) in ro" :key="coi" class="col-md-4">
          <Card 
            :title="card.title" 
            :color="card.color" 
            :data="card.data" 
            @click="handleCardTap(card)"
          />
        </div>
      </div>

      <div class="row mt-4 pt-4">
        <div class="col-md-6">
          <div class="card p-3 shadow-sm border-0 rounded-3">
            <h5 class="fw-bold mb-3">Pending Companies</h5>
            <ul class="list-group list-scroll">
              <li v-for="c in pendingCompaniesList" :key="c.id" class="list-group-item d-flex justify-content-between align-items-center border-start-0 border-end-0">
                <span>{{ c.name }}</span>
                <div>
                  <button class="btn btn-sm btn-success me-2 rounded-2" @click="emit('approve-company', c.id)">Approve</button>
                  <button class="btn btn-sm btn-danger rounded-2" @click="emit('reject-company', c.id)">Reject</button>
                </div>
              </li>
              <li v-if="!pendingCompaniesList.length" class="list-group-item text-muted text-center py-3">No pending company registrations.</li>
            </ul>
          </div>
        </div>
        <div class="col-md-6">
          <div class="card p-3 shadow-sm border-0 rounded-3">
            <h5 class="fw-bold mb-3">Pending Drives</h5>
            <ul class="list-group list-scroll">
              <li v-for="d in pendingDrivesList" :key="d.id" class="list-group-item d-flex justify-content-between align-items-center border-start-0 border-end-0">
                <span><strong>{{ d.company }}</strong> | {{ d.title }}</span>
                <div>
                  <button class="btn btn-sm btn-success me-2 rounded-2" @click="emit('approve-drive', d.id)">Approve</button>
                  <button class="btn btn-sm btn-danger rounded-2" @click="emit('reject-drive', d.id)">Reject</button>
                </div>
              </li>
              <li v-if="!pendingDrivesList.length" class="list-group-item text-muted text-center py-3">No pending job postings.</li>
            </ul>
          </div>
        </div>
      </div>
    </template>

    <!-- ADMIN-STUDENTS PAGE -->
    <template v-else-if="props.currentBtn === 'Students'">
      <AdminList
        :items="studentsList"
        title="Students"
        item-key="id"
        :search-fields="['username', 'email']"
        search-placeholder="Search students..."
        empty-text="No students found."
        view-label="View Details"
        @view-details="onViewDetails"
      >
        <template #actions="{ item }">
          <button v-if="item.blacklist" class="btn btn-sm btn-success rounded-2" @click="emit('blacklist-user', item.id)">Approve</button>
          <button v-else class="btn btn-sm btn-warning rounded-2 text-white" @click="emit('blacklist-user', item.id)">Blacklist</button>
          <button class="btn btn-sm btn-danger rounded-2" @click="emit('delete-user', item.id)">Delete</button>
        </template>
      </AdminList>
    </template>
    
    <!-- ADMIN-COMPANY PAGE -->
    <template v-else-if="props.currentBtn === 'Companies'">
      <AdminList
        :items="companiesList"
        title="Companies"
        item-key="id"
        :search-fields="['username', 'email']"
        search-placeholder="Search companies..."
        empty-text="No companies found."
        view-label="View Details"
        @view-details="onViewDetails"
      >
        <template #actions="{ item }">
          <button v-if="item.blacklist" class="btn btn-sm btn-success rounded-2" @click="emit('blacklist-user', item.id)">Approve</button>
          <button v-else class="btn btn-sm btn-warning rounded-2 text-white" @click="emit('blacklist-user', item.id)">Blacklist</button>
          <button class="btn btn-sm btn-danger rounded-2" @click="emit('delete-user', item.id)">Delete</button>
        </template>
      </AdminList>
    </template>
    
    <!-- ADMIN-DRIVES PAGE -->
    <template v-else-if="props.currentBtn === 'Drives'">
      <AdminList
        :items="drivesList"
        title="Drives"
        item-key="id"
        :search-fields="['title', 'company', 'skills_required', 'status']"
        search-placeholder="Search drives..."
        empty-text="No drives found."
        view-label="View Details"
        @view-details="onViewDetails"
      >
        <template #actions="{ item }">
          <button class="btn btn-sm btn-success rounded-2"
           @click="emit('approve-drive', item.id)"
           :disabled="item.status === 'Approved' || item.status === 'Closed'">Approve</button>
          <button class="btn btn-sm btn-danger rounded-2" 
           @click="emit('reject-drive', item.id)"
           :disabled="item.status === 'Rejected' || item.status === 'Closed'">Reject</button>
        </template>
      </AdminList>
    </template>
    
    <!-- ADMIN-APPLICATIONS PAGE -->
    <template v-else-if="props.currentBtn === 'Applications'">
      <AdminList
        :items="applicationsList"
        title="Applications"
        item-key="id"
        :search-fields="['status', 'company', 'title']"
        search-placeholder="Search applications..."
        empty-text="No applications found."
        view-label="View Details"
        @view-details="onViewDetails"
      />
    </template>
    
    <!-- ADMIN-PROFILE PAGE -->
    <template v-else-if="props.currentBtn === 'Profile'">
      <div class="row justify-content-center">
        <div class="col-lg-6 col-md-8">
          <div class="card border-0 shadow-sm rounded-4 p-4 bg-white text-center mb-4">
            <div class="avatar-placeholder mx-auto mb-3 d-flex align-items-center justify-content-center bg-success-subtle text-success rounded-circle" style="width: 80px; height: 80px; font-size: 2.2rem;">
              👤
            </div>
            <h4 class="fw-bold text-dark mb-1">{{ adminForm.username || props.user?.username || 'Admin User' }}</h4>
            <p class="text-muted small">System Administrator</p>
          </div>

          <div class="card border-0 shadow-sm rounded-4 p-4 bg-white">
            <h5 class="fw-bold text-dark mb-4">Update Admin Credentials</h5>
            
            <form @submit.prevent="handleUpdateProfile">
              <div class="mb-3">
                <label class="form-label small fw-bold text-muted text-uppercase">Admin Username</label>
                <input v-model="adminForm.username" type="text" class="form-control rounded-3" required placeholder="Admin Name">
              </div>

              <div class="mb-3">
                <label class="form-label small fw-bold text-muted text-uppercase">Admin Email</label>
                <input v-model="adminForm.email" type="email" class="form-control rounded-3" required placeholder="admin@placeport.com">
              </div>

              <div class="mb-3">
                <label class="form-label small fw-bold text-muted text-uppercase">New Password (leave blank to keep current)</label>
                <input v-model="adminForm.password" type="password" class="form-control rounded-3" placeholder="••••••••" minlength="4">
              </div>

              <div class="text-end mt-4">
                <button type="submit" class="btn btn-success rounded-3 fw-semibold px-4 py-2" :disabled="savingProfile">
                  <span v-if="savingProfile" class="spinner-border spinner-border-sm me-2" role="status"></span>
                  💾 Save Profile Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </template>

    <template v-else-if="props.currentBtn === 'About'">
      <div class="card p-4 text-center shadow-sm border-0 rounded-3">
        <h3>About Admin Portal</h3>
        <p class="text-muted">Use this portal to approve companies, drives, and manage campus placements.</p>
      </div>
    </template>
  </div>

  <!-- Dynamic Details Modal Shell -->
  <div class="modal fade" id="driveModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-lg modal-dialog-scrollable">
      <div class="modal-content border-0 shadow-lg rounded-4">
        <div class="modal-header bg-light border-0 py-3">
          <h5 class="fw-bold m-0 text-dark">{{ viewingType }} Details</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body p-4" v-if="selectedDrive">
          
          <div v-if="viewingType === 'Student'">
            <div class="d-flex align-items-center gap-3 mb-4">
              <div class="bg-primary text-white rounded-circle d-flex align-items-center justify-content-center fw-bold fs-3" style="width: 60px; height: 60px;">
                {{ (selectedDrive.username || 'S')[0].toUpperCase() }}
              </div>
              <div>
                <h4 class="mb-1 fw-bold text-dark">{{ selectedDrive.username }}</h4>
                <p class="text-muted mb-0">{{ selectedDrive.email }}</p>
              </div>
            </div>

            <div v-if="loadingProfile" class="text-center py-4">
              <div class="spinner-border text-primary" role="status"></div>
              <p class="text-muted mt-2">Loading student profile...</p>
            </div>
            
            <div v-else-if="errorProfile" class="alert alert-danger">{{ errorProfile }}</div>

            <div v-else-if="studentProfileRef">
              <div class="row g-3 mb-4">
                <div class="col-md-6">
                  <div class="p-3 bg-light rounded-3">
                    <span class="text-muted small fw-semibold d-block text-uppercase">Branch & CGPA</span>
                    <div v-if="studentProfileRef.branch_cgpa && Object.keys(studentProfileRef.branch_cgpa).length" class="mt-1">
                      <div v-for="(cgpa, branch) in studentProfileRef.branch_cgpa" :key="branch" class="fw-bold">
                        {{ branch }}: <span class="text-primary">{{ cgpa }} CGPA</span>
                      </div>
                    </div>
                    <div v-else class="text-muted small mt-1">Not entered</div>
                  </div>
                </div>
                <div class="col-md-6">
                  <div class="p-3 bg-light rounded-3">
                    <span class="text-muted small fw-semibold d-block text-uppercase">Resume File</span>
                    <div class="mt-1">
                      <a v-if="studentProfileRef.resume" :href="studentProfileRef.resume" target="_blank" class="btn btn-sm btn-outline-primary d-inline-flex align-items-center gap-1 mt-1">
                        📄 Open Resume
                      </a>
                      <span v-else class="text-muted small">No Resume uploaded</span>
                    </div>
                  </div>
                </div>
              </div>

              <div class="mb-4">
                <h6 class="fw-bold text-dark border-bottom pb-2">Skills</h6>
                <div v-if="studentProfileRef.skills" class="d-flex flex-wrap gap-1 mt-2">
                  <span v-for="skill in studentProfileRef.skills.split(',')" :key="skill" class="badge bg-secondary-subtle text-secondary-emphasis px-2 py-1 rounded-pill small">
                    {{ skill.trim() }}
                  </span>
                </div>
                <p v-else class="text-muted small">No skills listed.</p>
              </div>

              <div class="mb-4">
                <h6 class="fw-bold text-dark border-bottom pb-2">Education</h6>
                <p class="small text-dark" style="white-space: pre-wrap;">{{ studentProfileRef.education || 'No education history specified.' }}</p>
              </div>

              <div class="mb-4">
                <h6 class="fw-bold text-dark border-bottom pb-2">Experience</h6>
                <p class="small text-dark" style="white-space: pre-wrap;">{{ studentProfileRef.experience || 'No experience details specified.' }}</p>
              </div>

              <div>
                <h6 class="fw-bold text-dark border-bottom pb-2">Applications History (€3{{ studentApplications.length }})</h6>
                <div v-if="studentApplications.length" class="table-responsive">
                  <table class="table table-sm align-middle">
                    <thead>
                      <tr>
                        <th>Company</th>
                        <th>Drive</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="app in studentApplications" :key="app.id">
                        <td><strong>{{ app.company_name }}</strong></td>
                        <td>{{ app.drive_title }}</td>
                        <td>
                          <span class="badge" :class="{
                            'bg-warning text-dark': app.status === 'Applied',
                            'bg-info text-white': app.status === 'Shortlisted',
                            'bg-success text-white': app.status === 'Selected',
                            'bg-danger text-white': app.status === 'Rejected'
                          }">{{ app.status }}</span>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <p v-else class="text-muted small">This student has not applied to any drives yet.</p>
              </div>
            </div>
          </div>

          <div v-else-if="viewingType === 'Application'">
            <div class="p-3 bg-light rounded-3 mb-4">
              <h5 class="fw-bold text-dark mb-1">Application for {{ selectedDrive.drive_title }}</h5>
              <p class="text-muted mb-0">Company: <strong class="text-dark">{{ selectedDrive.company_name }}</strong></p>
              <hr class="my-2">
              <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
                <div class="small">Applied on: <span class="fw-semibold">{{ selectedDrive.date_applied }}</span></div>
                <div>
                  <span class="badge fs-6 px-3 py-1 rounded-pill" :class="{
                    'bg-warning text-dark': selectedDrive.status === 'Applied',
                    'bg-info text-white': selectedDrive.status === 'Shortlisted',
                    'bg-success text-white': selectedDrive.status === 'Selected',
                    'bg-danger text-white': selectedDrive.status === 'Rejected'
                  }">{{ selectedDrive.status }}</span>
                </div>
              </div>
            </div>

            <div class="mb-4">
              <h6 class="fw-bold text-dark border-bottom pb-2">Applicant Information</h6>
              <div class="row g-3">
                <div class="col-sm-6">
                  <span class="text-muted small fw-semibold d-block text-uppercase">Student Name</span>
                  <strong>{{ selectedDrive.student_name }}</strong>
                </div>
                <div class="col-sm-6">
                  <span class="text-muted small fw-semibold d-block text-uppercase">Student Email</span>
                  <strong>{{ selectedDrive.student_email }}</strong>
                </div>
                <div class="col-sm-6">
                  <span class="text-muted small fw-semibold d-block text-uppercase">Branch & CGPA</span>
                  <div v-if="selectedDrive.branch_cgpa && Object.keys(selectedDrive.branch_cgpa).length">
                    <div v-for="(cgpa, branch) in selectedDrive.branch_cgpa" :key="branch">
                      <strong>{{ branch }}:</strong> {{ cgpa }}
                    </div>
                  </div>
                  <span v-else class="text-muted small">Not specified</span>
                </div>
                <div class="col-sm-6">
                  <span class="text-muted small fw-semibold d-block text-uppercase">Resume</span>
                  <a v-if="selectedDrive.resume" :href="selectedDrive.resume" target="_blank" class="btn btn-sm btn-outline-primary d-inline-flex align-items-center gap-1 mt-1">
                    📄 View Resume
                  </a>
                  <span v-else class="text-muted small">No Resume Attached</span>
                </div>
              </div>
            </div>

            <div class="mb-4" v-if="selectedDrive.skills">
              <h6 class="fw-bold text-dark border-bottom pb-2">Skills</h6>
              <div class="d-flex flex-wrap gap-1 mt-1">
                <span v-for="skill in selectedDrive.skills.split(',')" :key="skill" class="badge bg-secondary-subtle text-secondary-emphasis px-2 py-1 rounded-pill small">
                  {{ skill.trim() }}
                </span>
              </div>
            </div>

            <div class="mb-4" v-if="selectedDrive.education">
              <h6 class="fw-bold text-dark border-bottom pb-2">Education</h6>
              <p class="small text-dark" style="white-space: pre-wrap;">{{ selectedDrive.education }}</p>
            </div>

            <div class="mb-4" v-if="selectedDrive.experience">
              <h6 class="fw-bold text-dark border-bottom pb-2">Experience</h6>
              <p class="small text-dark" style="white-space: pre-wrap;">{{ selectedDrive.experience }}</p>
            </div>

            <div class="p-3 bg-warning-subtle rounded-3" v-if="selectedDrive.feedback || selectedDrive.interview_time">
              <h6 class="fw-bold text-warning-emphasis">Status Updates & Feedback</h6>
              <p class="small mb-1" v-if="selectedDrive.feedback">💬 Feedback: <span class="fst-italic">"{{ selectedDrive.feedback }}"</span></p>
              <p class="small mb-1" v-if="selectedDrive.interview_time">🕒 Interview: <strong>{{ selectedDrive.interview_time }}</strong></p>
              <p class="small mb-0" v-if="selectedDrive.interview_link">
                🔗 Link: <a :href="selectedDrive.interview_link" target="_blank">{{ selectedDrive.interview_link }}</a>
              </p>
              <p class="small mb-0" v-if="selectedDrive.offer_letter_link">
                📄 Offer: <a :href="selectedDrive.offer_letter_link" target="_blank">Download Offer Letter</a>
              </p>
            </div>
          </div>

          <div v-else-if="viewingType === 'Drive'">
            <div class="p-3 bg-light rounded-3 mb-4">
              <div class="d-flex justify-content-between align-items-start">
                <div>
                  <h4 class="fw-bold text-dark mb-1">{{ selectedDrive.title }}</h4>
                  <p class="text-muted mb-0">Company: <strong class="text-dark">{{ selectedDrive.company }}</strong></p>
                </div>
                <span class="badge px-3 py-1 rounded-pill fs-6" :class="{
                  'bg-warning text-dark': selectedDrive.status === 'Pending',
                  'bg-success text-white': selectedDrive.status === 'Approved',
                  'bg-danger text-white': selectedDrive.status === 'Rejected',
                  'bg-secondary text-white': selectedDrive.status === 'Closed'
                }">{{ selectedDrive.status }}</span>
              </div>
            </div>

            <div class="row g-3 mb-4">
              <div class="col-sm-6">
                <span class="text-muted small fw-semibold d-block text-uppercase">Salary / Package</span>
                <strong class="text-success fs-5">${{ selectedDrive.salary?.toLocaleString() }}</strong>
              </div>
              <div class="col-sm-6">
                <span class="text-muted small fw-semibold d-block text-uppercase">Minimum CGPA Required</span>
                <strong>{{ selectedDrive.min_cgpa }} CGPA</strong>
              </div>
              <div class="col-sm-6">
                <span class="text-muted small fw-semibold d-block text-uppercase">Start Date</span>
                <span>{{ selectedDrive.start_date }}</span>
              </div>
              <div class="col-sm-6">
                <span class="text-muted small fw-semibold d-block text-uppercase">Application Deadline</span>
                <span class="text-danger fw-semibold">{{ selectedDrive.deadline }}</span>
              </div>
            </div>

            <div class="mb-4">
              <h6 class="fw-bold text-dark border-bottom pb-2">Description</h6>
              <p class="small text-dark" style="white-space: pre-wrap;">{{ selectedDrive.description }}</p>
            </div>

            <div class="mb-4" v-if="selectedDrive.skills_required">
              <h6 class="fw-bold text-dark border-bottom pb-2">Skills Required</h6>
              <div class="d-flex flex-wrap gap-1 mt-1">
                <span v-for="skill in selectedDrive.skills_required.split(',')" :key="skill" class="badge bg-primary-subtle text-primary px-2 py-1 rounded-pill small">
                  {{ skill.trim() }}
                </span>
              </div>
            </div>

            <div>
              <h6 class="fw-bold text-dark border-bottom pb-2">Candidates Applied ({{ driveApplications.length }})</h6>
              <div v-if="driveApplications.length" class="table-responsive">
                <table class="table table-sm align-middle">
                  <thead>
                    <tr>
                      <th>Candidate</th>
                      <th>Email</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="app in driveApplications" :key="app.id">
                      <td><strong>{{ app.student_name }}</strong></td>
                      <td>{{ app.student_email }}</td>
                      <td>
                        <span class="badge" :class="{
                          'bg-warning text-dark': app.status === 'Applied',
                          'bg-info text-white': app.status === 'Shortlisted',
                          'bg-success text-white': app.status === 'Selected',
                          'bg-danger text-white': app.status === 'Rejected'
                        }">{{ app.status }}</span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p v-else class="text-muted small">No applications received for this drive yet.</p>
            </div>
          </div>

          <div v-else-if="viewingType === 'Company'">
            <div class="d-flex align-items-center gap-3 mb-4">
              <div class="bg-primary text-white rounded-circle d-flex align-items-center justify-content-center fw-bold fs-3" style="width: 60px; height: 60px;">
                {{ (selectedDrive.username || 'C')[0].toUpperCase() }}
              </div>
              <div>
                <h4 class="mb-1 fw-bold text-dark">{{ selectedDrive.username }}</h4>
                <p class="text-muted mb-0">{{ selectedDrive.email }}</p>
              </div>
            </div>

            <div class="mb-4">
              <h6 class="fw-bold text-dark border-bottom pb-2">Placement Drives Created ({{ companyDrivesList.length }})</h6>
              <div v-if="companyDrivesList.length" class="list-group">
                <div v-for="drive in companyDrivesList" :key="drive.id" class="list-group-item d-flex justify-content-between align-items-center">
                  <div>
                    <strong class="d-block">{{ drive.title }}</strong>
                    <span class="text-muted small">Salary: ${{ drive.salary?.toLocaleString() }}</span>
                  </div>
                  <span class="badge" :class="{
                    'bg-warning text-dark': drive.status === 'Pending',
                    'bg-success text-white': drive.status === 'Approved',
                    'bg-danger text-white': drive.status === 'Rejected',
                    'bg-secondary text-white': drive.status === 'Closed'
                  }">{{ drive.status }}</span>
                </div>
              </div>
              <p v-else class="text-muted small">No drives created by this company yet.</p>
            </div>
          </div>

        </div>
        <div class="modal-footer bg-light border-0 py-3" v-if="selectedDrive">
          <template v-if="viewingType === 'Drive'">
            <button class="btn btn-success rounded-2" @click="emit('approve-drive', selectedDrive.id)" :disabled="selectedDrive.status==='Approved'">Approve Drive</button>
            <button class="btn btn-danger rounded-2" @click="emit('reject-drive', selectedDrive.id)" :disabled="selectedDrive.status==='Rejected'">Reject Drive</button>
          </template>
          <button type="button" class="btn btn-secondary rounded-2" data-bs-dismiss="modal">Close</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.list-scroll {
  max-height: 250px;
  overflow-y: auto;
}
</style>