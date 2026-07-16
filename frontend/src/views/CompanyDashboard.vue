<script setup>
import { reactive, watch, ref, computed } from 'vue'

const props = defineProps({
  currentBtn: { type: String, default: 'Dashboard' },
  user: { type: Object, default: () => ({ id: 0, email: '', blacklist: false }) },
  drives: { type: Array, default: () => [] },
  profile: { type: Object, default: () => ({ id: 0, name: '', website: '', status: 'Pending' }) },
  applications: { type: Array, default: () => [] }
});

const emit = defineEmits(['save-drive', 'update-profile', 'update-application-status', 'update-drive-status', 'trigger-company-export']);

const activeTab = ref('overview');
const reports = ref([]);

watch(() => props.currentBtn, (newBtn) => {
  if (newBtn === 'Dashboard') {
    if (activeTab.value !== 'overview' && activeTab.value !== 'drives' && activeTab.value !== 'applications' && activeTab.value !== 'shortlisted') {
      activeTab.value = 'overview';
    }
  } else if (newBtn === 'History') {
    activeTab.value = 'reports';
  }
}, { immediate: true });

async function fetchReports() {
  try {
    const res = await fetch('/api/company/reports');
    if (res.ok) {
      reports.value = await res.json();
    }
  } catch (err) {
    console.error(err);
  }
}

watch(activeTab, (newTab) => {
  if (newTab === 'reports') {
    fetchReports();
  }
});

function triggerCompanyExport() {
  emit('trigger-company-export');
}

const newDrive = reactive({ 
  company_id: props.user?.id, 
  title: '', 
  desc: '', 
  salary: 0,
  skills_required: '', 
  min_cgpa: 0, 
  start_date: '', 
  deadline: '', 
  status: 'Pending'
});

const profileForm = reactive({
  name: '',
  website: ''
});

watch(() => props.profile, (newProfile) => {
  if (newProfile) {
    profileForm.name = newProfile.name || '';
    profileForm.website = newProfile.website || '';
  }
}, { immediate: true });

const totalDrives = computed(() => Array.isArray(props.drives) ? props.drives.length : 0);
const totalApps = computed(() => Array.isArray(props.applications) ? props.applications.length : 0);
const shortlistedCount = computed(() => Array.isArray(props.applications) ? props.applications.filter(a => a.status === 'Shortlisted').length : 0);
const selectedCount = computed(() => Array.isArray(props.applications) ? props.applications.filter(a => a.status === 'Selected').length : 0);

const pendingApps = computed(() => Array.isArray(props.applications) ? props.applications.filter(a => a.status === 'Applied') : []);
const shortlistedApps = computed(() => Array.isArray(props.applications) ? props.applications.filter(a => a.status === 'Shortlisted' || a.status === 'Selected') : []);

function formatDate(dateStr) {
  if (!dateStr) return 'N/A';
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  });
}

const activeAppToReview = ref(null);
const reviewStatus = ref('');
const reviewFeedback = ref('');
const reviewInterviewTime = ref('');
const reviewInterviewLink = ref('');
const reviewOfferLetterLink = ref('');

function openReviewModal(app, status) {
  activeAppToReview.value = app;
  reviewStatus.value = status;
  reviewFeedback.value = app.feedback || '';
  reviewInterviewTime.value = app.interview_time || '';
  reviewInterviewLink.value = app.interview_link || '';
  reviewOfferLetterLink.value = app.offer_letter_link || '';
}

function closeReviewModal() {
  activeAppToReview.value = null;
}

function submitReview() {
  if (!activeAppToReview.value) return;
  
  emit('update-application-status', { 
    appId: activeAppToReview.value.id, 
    status: reviewStatus.value, 
    feedback: reviewFeedback.value,
    interview_time: reviewStatus.value === 'Shortlisted' ? reviewInterviewTime.value : '',
    interview_link: reviewStatus.value === 'Shortlisted' ? reviewInterviewLink.value : '',
    offer_letter_link: reviewStatus.value === 'Selected' ? reviewOfferLetterLink.value : ''
  });
  
  closeReviewModal();
}

function toggleDriveStatus(driveId, currentStatus) {
  const newStatus = currentStatus === 'Approved' ? 'Closed' : 'Approved';
  const actionText = currentStatus === 'Approved' ? 'close' : 'activate';
  if (confirm(`Are you sure you want to ${actionText} this job posting?`)) {
    emit('update-drive-status', { driveId, status: newStatus });
  }
}

const selectedCandidate = ref(null);
function selectCandidate(app) {
  selectedCandidate.value = app;
}
</script>

<template>
  <div class="company-dashboard-container py-4">
    <!-- Verification / Pending Profile screen -->
    <div v-if="props.profile?.status !== 'Approved' || props.user?.blacklist === true" class="verification-screen mx-auto py-5" style="max-width: 550px;">
      <div class="card shadow border-0 p-5 rounded-4 bg-light">
        <div v-if="props.profile?.status === 'Pending'" class="mb-4 text-center">
          <div class="display-3 text-warning mb-3">🕒</div>
          <h2 class="fw-bold text-dark mb-2">Verification Pending</h2>
          <p class="text-secondary">
            Thank you for registering with <strong>PlacePort</strong>! Your company account is currently under review by our administrators.
          </p>
        </div>
        
        <div v-if="props.user?.blacklist === true" class="mb-4 text-center">
          <div class="display-3 text-danger mb-3">❌</div>
          <h2 class="fw-bold text-dark mb-2">Blacklisted!</h2>
          <p class="text-secondary">
            Blacklisted on <strong>PlacePort</strong>! Contact support team.
          </p>
        </div>

        <div v-else-if="props.profile?.status === 'Rejected'" class="mb-4 text-center">
          <div class="display-3 text-danger mb-3">❌</div>
          <h2 class="fw-bold text-dark mb-2">Registration Rejected</h2>
          <p class="text-secondary">
            Unfortunately, your registration was rejected by the Admin. Please review and update your company profile details below to resubmit for approval.
          </p>
        </div>

        <div class="profile-update-box border-top pt-4 mt-2 text-start" v-if="props.user?.blacklist !== true">
          <h5 class="fw-semibold text-dark mb-2">Update Company Profile</h5>
          <p class="text-muted small mb-4">
            Ensure your profile information is accurate and complete to avoid registration rejection.
          </p>
          
          <form @submit.prevent="emit('update-profile', { name: profileForm.name, website: profileForm.website })">
            <div class="mb-3">
              <label class="form-label small fw-bold text-uppercase text-muted">Company Name</label>
              <input v-model="profileForm.name" type="text" class="form-control rounded-3" placeholder="Enter company name" required>
            </div>
            
            <div class="mb-4">
              <label class="form-label small fw-bold text-uppercase text-muted">Company Website</label>
              <input v-model="profileForm.website" type="url" class="form-control rounded-3" placeholder="https://example.com" required>
            </div>
            
            <button type="submit" class="btn btn-primary w-100 py-2 rounded-3 fw-semibold">
              Update Profile & Submit for Verification
            </button>
          </form>
        </div>
      </div>
    </div>

    <!-- Approved Dashboard View -->
    <div v-else>
      <div class="d-flex justify-content-between mb-4 align-items-center flex-wrap gap-3" v-if="props.currentBtn === 'Dashboard'">
        <div>
          <h3 class="fw-bold text-dark mb-1">Welcome, {{ props.profile?.name || props.user?.email }}</h3>
          <p class="text-muted mb-0">Manage placement drives, review applications, and select top talents.</p>
        </div>
        <div class="d-flex gap-2">
          <button class="btn btn-outline-primary px-4 py-2 rounded-3 fw-semibold" @click="triggerCompanyExport">
            📥 Export History (CSV)
          </button>
          <button class="btn btn-primary px-4 py-2 rounded-3 fw-semibold" data-bs-toggle="modal" data-bs-target="#driveModal">
            ➕ New Placement Drive
          </button>
        </div>
      </div>

      <!-- Quick Metrics Grid -->
      <div class="row g-3 mb-4" v-if="props.currentBtn === 'Dashboard'">
        <div class="col-6 col-md-3">
          <div class="card border-0 shadow-sm rounded-4 p-3 bg-white h-100">
            <div class="small fw-bold text-muted text-uppercase mb-1">Job Postings</div>
            <div class="d-flex align-items-baseline gap-2">
              <span class="fs-2 fw-bold text-primary">{{ totalDrives }}</span>
              <span class="text-muted small">created</span>
            </div>
          </div>
        </div>
        <div class="col-6 col-md-3">
          <div class="card border-0 shadow-sm rounded-4 p-3 bg-white h-100">
            <div class="small fw-bold text-muted text-uppercase mb-1">Applications</div>
            <div class="d-flex align-items-baseline gap-2">
              <span class="fs-2 fw-bold text-info">{{ totalApps }}</span>
              <span class="text-muted small">received</span>
            </div>
          </div>
        </div>
        <div class="col-6 col-md-3">
          <div class="card border-0 shadow-sm rounded-4 p-3 bg-white h-100">
            <div class="small fw-bold text-muted text-uppercase mb-1">Shortlisted</div>
            <div class="d-flex align-items-baseline gap-2">
              <span class="fs-2 fw-bold text-warning">{{ shortlistedCount }}</span>
              <span class="text-muted small">candidates</span>
            </div>
          </div>
        </div>
        <div class="col-6 col-md-3">
          <div class="card border-0 shadow-sm rounded-4 p-3 bg-white h-100">
            <div class="small fw-bold text-muted text-uppercase mb-1">Selected</div>
            <div class="d-flex align-items-baseline gap-2">
              <span class="fs-2 fw-bold text-success">{{ selectedCount }}</span>
              <span class="text-muted small">hired</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Combined Tab Navigation Options -->
      <div v-if="props.currentBtn === 'Dashboard'" class="card border-0 shadow-sm rounded-4 mb-4 bg-white overflow-hidden">
        <div class="card-header bg-white border-0 p-3 pb-0">
          <ul class="nav nav-tabs border-0 gap-2">
            <li class="nav-item">
              <button 
                class="nav-link border-0 px-4 py-2 rounded-3 fw-semibold transition-all"
                :class="activeTab === 'overview' ? 'bg-primary text-white' : 'bg-light text-secondary'"
                @click="activeTab = 'overview'"
              >
                📊 Dashboard Overview
              </button>
            </li>
            <li class="nav-item">
              <button 
                class="nav-link border-0 px-4 py-2 rounded-3 fw-semibold transition-all"
                :class="activeTab === 'drives' ? 'bg-primary text-white' : 'bg-light text-secondary'"
                @click="activeTab = 'drives'"
              >
                💼 Placement Drives ({{ totalDrives }})
              </button>
            </li>
            <li class="nav-item">
              <button 
                class="nav-link border-0 px-4 py-2 rounded-3 fw-semibold transition-all"
                :class="activeTab === 'applications' ? 'bg-primary text-white' : 'bg-light text-secondary'"
                @click="activeTab = 'applications'"
              >
                📥 Received Applications ({{ pendingApps.length }})
              </button>
            </li>
            <li class="nav-item">
              <button 
                class="nav-link border-0 px-4 py-2 rounded-3 fw-semibold transition-all"
                :class="activeTab === 'shortlisted' ? 'bg-primary text-white' : 'bg-light text-secondary'"
                @click="activeTab = 'shortlisted'"
              >
                🏆 Shortlist & Selections ({{ shortlistedCount + selectedCount }})
              </button>
            </li>
          </ul>
        </div>
      </div>

      <!-- TAB CONTENTS -->
      <template v-if="props.currentBtn === 'Dashboard'">
        <div v-if="activeTab === 'overview'" class="tab-pane-content">
          <div class="row g-4">
            <div class="col-lg-12">
              <div class="card border-0 shadow-sm rounded-4 p-4 bg-white">
                <div class="d-flex justify-content-between align-items-center mb-3">
                  <h5 class="fw-bold text-dark mb-0">Recent Application Activity</h5>
                  <button @click="activeTab = 'applications'" class="btn btn-link btn-sm text-decoration-none fw-semibold">View All</button>
                </div>

                <div v-if="props.applications?.length === 0" class="text-center py-5 text-muted">
                  <p class="mb-0">No application activity found yet.</p>
                </div>
                <div v-else class="table-responsive">
                  <table class="table align-middle">
                    <thead>
                      <tr>
                        <th class="border-0 small fw-bold text-muted text-uppercase">Student</th>
                        <th class="border-0 small fw-bold text-muted text-uppercase">Role / Drive</th>
                        <th class="border-0 small fw-bold text-muted text-uppercase">Status</th>
                        <th class="border-0 small fw-bold text-muted text-uppercase">Applied On</th>
                      </tr>
                    </thead>
                    <tbody>
                      <template v-for="app in props.applications.slice(0, 5)" :key="app.id">
                        <tr>
                          <td class="border-0">
                            <button @click="selectCandidate(app)" data-bs-toggle="modal" data-bs-target="#candidateProfileModal" class="btn btn-link text-start p-0 fw-semibold text-dark text-decoration-none hover-underline">
                              {{ app.student_name }} 🔍
                            </button>
                            <div class="text-muted small">{{ app.student_email }}</div>
                          </td>
                          <td class="border-0 fw-semibold text-secondary">{{ app.drive_title }}</td>
                          <td class="border-0">
                            <span 
                              class="badge px-3 py-2 rounded-pill"
                              :class="{
                                'bg-warning text-dark': app.status === 'Applied',
                                'bg-info text-white': app.status === 'Shortlisted',
                                'bg-success text-white': app.status === 'Selected',
                                'bg-danger text-white': app.status === 'Rejected'
                              }"
                            >
                              {{ app.status }}
                            </span>
                          </td>
                          <td class="border-0 text-muted small">{{ formatDate(app.date_applied) }}</td>
                        </tr>
                        <tr v-if="app.feedback" :key="'fb-' + app.id">
                          <td colspan="4" class="py-1 px-3 border-0 bg-light-subtle">
                            <div class="text-muted small ms-2">💬 Feedback: <span class="fst-italic text-dark">"{{ app.feedback }}"</span></div>
                          </td>
                        </tr>
                      </template>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Tab: Placement Drives -->
        <div v-else-if="activeTab === 'drives'" class="tab-pane-content">
          <div class="card p-4 border-0 shadow-sm rounded-4 bg-white">
            <h5 class="fw-bold text-dark mb-3">Your Created Placement Drives</h5>
            
            <div v-if="props.drives?.length === 0" class="text-center py-5 text-muted">
              <div class="display-6 mb-2">💼</div>
              <p>No job postings or placement drives created yet. Click "New Placement Drive" to get started.</p>
            </div>
            <div v-else class="table-responsive">
              <table class="table align-middle">
                <thead>
                  <tr>
                    <th class="text-muted small fw-bold text-uppercase border-0">Title</th>
                    <th class="text-muted small fw-bold text-uppercase border-0">Budget/Salary</th>
                    <th class="text-muted small fw-bold text-uppercase border-0">Timeline</th>
                    <th class="text-muted small fw-bold text-uppercase border-0">Status</th>
                    <th class="text-muted small fw-bold text-uppercase border-0 text-end">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="drive in props.drives" :key="drive.id">
                    <td class="border-0">
                      <div class="fw-bold text-dark">{{ drive?.title }}</div>
                      <p class="text-muted small mb-0 text-truncate" style="max-width: 320px;">{{ drive?.desc }}</p>
                    </td>
                    <td class="text-dark border-0 fw-semibold">${{ drive?.salary?.toLocaleString() }}</td>
                    <td class="border-0">
                      <div class="small text-dark"><span class="text-muted">Start:</span> {{ formatDate(drive?.start_date) }}</div>
                      <div class="small text-danger"><span class="text-muted">Deadline:</span> {{ formatDate(drive?.deadline) }}</div>
                    </td>
                    <td class="border-0">
                      <span 
                        class="badge px-3 py-2 rounded-pill"
                        :class="{
                          'bg-warning text-dark': drive?.status === 'Pending',
                          'bg-success text-white': drive?.status === 'Approved',
                          'bg-danger text-white': drive?.status === 'Rejected',
                          'bg-secondary text-white': drive?.status === 'Closed'
                        }"
                      >
                        {{ drive?.status === 'Approved' ? 'Active' : drive?.status }}
                      </span>
                    </td>
                    <td class="border-0 text-end">
                      <button 
                        v-if="drive?.status === 'Approved'"
                        @click="toggleDriveStatus(drive.id, 'Approved')"
                        class="btn btn-outline-secondary btn-sm rounded-3 px-3 py-1"
                      >
                        🛑 Close Job
                      </button>
                      <button 
                        v-else-if="drive?.status === 'Closed'"
                        @click="toggleDriveStatus(drive.id, 'Closed')"
                        class="btn btn-success btn-sm rounded-3 px-3 py-1 text-white"
                      >
                        🚀 Re-activate
                      </button>
                      <span v-else class="text-muted small fst-italic">Awaiting Admin Approval</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- Tab: Received Applications -->
        <div v-else-if="activeTab === 'applications'" class="tab-pane-content">
          <div class="card p-4 border-0 shadow-sm rounded-4 bg-white">
            <h5 class="fw-bold text-dark mb-3">Received Candidate Applications</h5>
            
            <div v-if="pendingApps.length === 0" class="text-center py-5 text-muted">
              <div class="display-6 mb-2">📥</div>
              <p class="mb-0">No pending applications received for review.</p>
            </div>
            
            <div v-else class="table-responsive">
              <table class="table align-middle">
                <thead>
                  <tr>
                    <th class="text-muted small fw-bold text-uppercase border-0">Candidate Info</th>
                    <th class="text-muted small fw-bold text-uppercase border-0">Applied Role</th>
                    <th class="text-muted small fw-bold text-uppercase border-0">Academic CGPA</th>
                    <th class="text-muted small fw-bold text-uppercase border-0">Resume</th>
                    <th class="text-muted small fw-bold text-uppercase border-0 text-end">Review Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="app in pendingApps" :key="app.id">
                    <td class="border-0">
                      <button @click="selectCandidate(app)" data-bs-toggle="modal" data-bs-target="#candidateProfileModal" class="btn btn-link text-start p-0 fw-bold text-dark text-decoration-none hover-underline">
                        {{ app.student_name }} 🔍
                      </button>
                      <div class="text-muted small">{{ app.student_email }}</div>
                    </td>
                    <td class="border-0 fw-semibold text-secondary">{{ app.drive_title }}</td>
                    <td class="border-0">
                      <div v-if="app.branch_cgpa && Object.keys(app.branch_cgpa).length" class="small">
                        <div v-for="(cgpa, branch) in app.branch_cgpa" :key="branch">
                          <strong>{{ branch }}:</strong> {{ cgpa }} CGPA
                        </div>
                      </div>
                      <span v-else class="text-muted small">N/A</span>
                    </td>
                    <td class="border-0">
                      <a v-if="app.resume" :href="app.resume" target="_blank" class="btn btn-outline-primary btn-sm rounded-3">
                        📄 View Resume
                      </a>
                      <span v-else class="text-muted small">No Resume</span>
                    </td>
                    <td class="border-0 text-end">
                      <div class="d-flex gap-2 justify-content-end">
                        <button @click="openReviewModal(app, 'Shortlisted')" class="btn btn-warning btn-sm fw-semibold rounded-3 px-3 py-1">⭐ Shortlist</button>
                        <button @click="openReviewModal(app, 'Rejected')" class="btn btn-outline-danger btn-sm fw-semibold rounded-3 px-3 py-1">Dismiss</button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- Tab: Shortlist & Selections -->
        <div v-else-if="activeTab === 'shortlisted'" class="tab-pane-content">
          <div class="card p-4 border-0 shadow-sm rounded-4 bg-white">
            <h5 class="fw-bold text-dark mb-3">Shortlisted & Selected Candidates</h5>
            
            <div v-if="shortlistedApps.length === 0" class="text-center py-5 text-muted">
              <div class="display-6 mb-2">🏆</div>
              <p class="mb-0">No candidates shortlisted or selected yet.</p>
            </div>
            
            <div v-else class="table-responsive">
              <table class="table align-middle">
                <thead>
                  <tr>
                    <th class="text-muted small fw-bold text-uppercase border-0">Candidate Info</th>
                    <th class="text-muted small fw-bold text-uppercase border-0">Applied Role</th>
                    <th class="text-muted small fw-bold text-uppercase border-0">Resume</th>
                    <th class="text-muted small fw-bold text-uppercase border-0">Decision State</th>
                    <th class="text-muted small fw-bold text-uppercase border-0 text-end">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="app in shortlistedApps" :key="app.id">
                    <td class="border-0">
                      <button @click="selectCandidate(app)" data-bs-toggle="modal" data-bs-target="#candidateProfileModal" class="btn btn-link text-start p-0 fw-bold text-dark text-decoration-none hover-underline">
                        {{ app.student_name }} 🔍
                      </button>
                      <div class="text-muted small mb-1">{{ app.student_email }}</div>
                      
                      <div v-if="app.status === 'Shortlisted' && app.interview_time" class="mt-2 p-2 rounded-3 border bg-primary-subtle text-primary-emphasis" style="max-width: 280px;">
                        <div class="small fw-bold text-uppercase tracking-wider opacity-75 mb-1" style="font-size: 0.7rem;">💬 Interview Scheduled</div>
                        <div class="small fw-semibold d-flex align-items-center gap-1">🕒 {{ app.interview_time }}</div>
                        <div v-if="app.interview_link" class="small mt-1 d-flex align-items-center gap-1 text-truncate">
                          🔗 Link: <a :href="app.interview_link" target="_blank" class="fw-bold text-decoration-underline text-truncate text-primary" style="max-width: 180px;">Join Meeting</a>
                        </div>
                      </div>
                    </td>
                    <td class="border-0 fw-semibold text-secondary">{{ app.drive_title }}</td>
                    <td class="border-0">
                      <a v-if="app.resume" :href="app.resume" target="_blank" class="btn btn-outline-primary btn-sm rounded-3">📄 View Resume</a>
                      <span v-else class="text-muted small">No Resume</span>
                    </td>
                    <td class="border-0">
                      <span class="badge px-3 py-2 rounded-pill fw-semibold" :class="app.status === 'Selected' ? 'bg-success text-white' : 'bg-warning text-dark'">{{ app.status }}</span>
                    </td>
                    <td class="border-0 text-end">
                      <div class="d-flex gap-2 justify-content-end">
                        <button v-if="app.status === 'Shortlisted'" @click="openReviewModal(app, 'Selected')" class="btn btn-success btn-sm fw-semibold rounded-3 px-3 py-1">✔ Mark Selected</button>
                        <button @click="openReviewModal(app, 'Rejected')" class="btn btn-outline-danger btn-sm fw-semibold rounded-3 px-3 py-1">Reject Candidate</button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </template>

      <!-- History Section -->
      <template v-else-if="props.currentBtn === 'History'">
        <div class="tab-pane-content">
          <div class="card border-0 shadow-sm rounded-4 p-4 bg-white">
            <div class="d-flex justify-content-between align-items-center mb-3">
              <div>
                <h5 class="fw-bold text-dark mb-1">Company Placement Analytics Reports</h5>
                <p class="text-muted small mb-0">Monthly statistics, hire rates, and drive performance breakdowns.</p>
              </div>
              <button @click="fetchReports" class="btn btn-sm btn-outline-secondary rounded-pill px-3">🔄 Refresh List</button>
            </div>

            <div v-if="reports.length === 0" class="text-center py-5 text-muted">
              <div class="display-6 mb-2">📊</div>
              <p class="mb-0">No monthly reports generated yet. Reports are generated automatically by our scheduler.</p>
            </div>
            
            <div v-else class="row g-3">
              <div v-for="report in reports" :key="report.filename" class="col-md-6 col-lg-4">
                <div class="card border border-light-subtle rounded-4 p-4 h-100 bg-light shadow-sm d-flex flex-column justify-content-between">
                  <div>
                    <div class="d-flex justify-content-between align-items-start mb-3">
                      <span class="badge bg-primary-subtle text-primary rounded-pill px-3 py-1 fw-semibold small">Performance</span>
                      <span class="text-muted small">HTML Report</span>
                    </div>
                    <h5 class="fw-bold text-dark mb-1">Placement Analytics</h5>
                    <p class="text-secondary small mb-3">Report period: <strong>{{ report.month }}</strong></p>
                  </div>
                  <div class="pt-2 border-top">
                    <a :href="report.link" target="_blank" class="btn btn-primary w-100 rounded-3 fw-semibold py-2">📄 View Report</a>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- Profile Section Content Layer -->
      <template v-else-if="props.currentBtn === 'Profile'">
        <div class="row g-4 justify-content-center">
          <div class="col-lg-6">
            <div class="card border-0 shadow-sm rounded-4 p-4 bg-white">
              <h5 class="fw-bold text-dark mb-4">Company Profile Settings</h5>
              
              <form @submit.prevent="emit('update-profile', { name: profileForm.name, website: profileForm.website })">
                <div class="mb-3">
                  <label class="form-label small fw-bold text-muted text-uppercase">Company Name</label>
                  <input v-model="profileForm.name" type="text" class="form-control rounded-3" placeholder="Enter company name" required>
                </div>
                
                <div class="mb-4">
                  <label class="form-label small fw-bold text-muted text-uppercase">Company Website</label>
                  <input v-model="profileForm.website" type="url" class="form-control rounded-3" placeholder="https://example.com" required>
                </div>
                
                <div class="p-3 bg-light rounded-3 mb-4 border">
                  <div class="small text-secondary mb-1">Verification Status:</div>
                  <span class="badge bg-success-subtle text-success px-3 py-1 fw-semibold">Verified & Approved</span>
                  <div class="small text-secondary mt-3 mb-1">Portal Account Email:</div>
                  <div class="fw-bold text-dark">{{ props.user?.email }}</div>
                </div>

                <div class="text-end">
                  <button type="submit" class="btn btn-primary px-4 py-2 rounded-3 fw-semibold">💾 Save Profile Changes</button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>

  <!-- Reviw shell modal -->
  <div v-if="activeAppToReview" class="modal-backdrop fade show" style="z-index: 1040;"></div>
  <div v-if="activeAppToReview" class="modal fade show d-block" tabindex="-1" style="z-index: 1050; background: rgba(0, 0, 0, 0.55);" @click.self="closeReviewModal">
    <div class="modal-dialog modal-dialog-centered">
      <div class="modal-content rounded-4 border-0 shadow">
        <div class="modal-header border-0 pb-0">
          <h5 class="modal-title fw-bold">Reviewing Candidate: {{ activeAppToReview.student_name }}</h5>
          <button type="button" class="btn-close" @click="closeReviewModal"></button>
        </div>
        <div class="modal-body">
          <div class="bg-light p-3 rounded-3 mb-3 border">
            <div class="small mb-1" v-if="activeAppToReview.branch_cgpa && Object.keys(activeAppToReview.branch_cgpa).length">
              <strong>Academic Background:</strong> {{ Object.keys(activeAppToReview.branch_cgpa)[0] }} ({{ Object.values(activeAppToReview.branch_cgpa)[0] }} CGPA)
            </div>
            <div v-if="activeAppToReview.skills" class="d-flex flex-wrap gap-1 mt-2">
              <span v-for="skill in activeAppToReview.skills.split(',')" :key="skill" class="badge bg-secondary text-white rounded-pill small">{{ skill.trim() }}</span>
            </div>
          </div>

          <div class="mb-3">
            <label class="form-label small fw-bold text-muted text-uppercase">Evaluation Verdict</label>
            <select v-model="reviewStatus" class="form-select rounded-3">
              <option value="Shortlisted">⭐ Shortlist Candidate & Schedule Interview</option>
              <option value="Selected">✔ Confirm Selection & Placed</option>
              <option value="Rejected">❌ Dismiss Application</option>
            </select>
          </div>

          <div v-if="reviewStatus === 'Shortlisted'" class="p-3 bg-light border border-warning-subtle rounded-3 mb-3">
            <div class="mb-2">
              <label class="form-label small fw-bold text-muted text-uppercase">Interview Calendar Target</label>
              <input v-model="reviewInterviewTime" type="text" class="form-control form-control-sm rounded-3" placeholder="e.g., July 24, 2026, 03:00 PM IST">
            </div>
            <div>
              <label class="form-label small fw-bold text-muted text-uppercase">Meeting Broadcast URL</label>
              <input v-model="reviewInterviewLink" type="url" class="form-control form-control-sm rounded-3" placeholder="https://meet.google.com/xyz">
            </div>
          </div>

          <div v-if="reviewStatus === 'Selected'" class="p-3 bg-light border border-success-subtle rounded-3 mb-3">
            <label class="form-label small fw-bold text-muted text-uppercase">Public Document Share Link (Offer Letter PDF)</label>
            <input v-model="reviewOfferLetterLink" type="url" class="form-control form-control-sm rounded-3" required placeholder="https://drive.google.com/file/d/...">
          </div>

          <div class="mb-3">
            <label class="form-label small fw-bold text-muted text-uppercase">Recruiter Feedback Note</label>
            <textarea v-model="reviewFeedback" class="form-control rounded-3" rows="3"></textarea>
          </div>
        </div>
        <div class="modal-footer border-0 pt-0">
          <button type="button" class="btn btn-light rounded-3 fw-semibold" @click="closeReviewModal">Cancel</button>
          <button class="btn btn-primary rounded-3 fw-semibold" @click="submitReview">Save Decision</button>
        </div>
      </div>
    </div>
  </div>

  <!-- posting Creation Modal -->
  <div class="modal fade" id="driveModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog">
      <div class="modal-content rounded-4 border-0 shadow">
        <div class="modal-header border-0 pb-0">
          <h5 class="modal-title fw-bold">Create Campus Placement Drive</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <div class="mb-3"><label class="form-label small fw-bold text-muted text-uppercase">Role Title</label><input v-model="newDrive.title" class="form-control rounded-3"></div>
          <div class="mb-3"><label class="form-label small fw-bold text-muted text-uppercase">Job Specifications</label><textarea v-model="newDrive.desc" class="form-control rounded-3" rows="2"></textarea></div>
          <div class="mb-3"><label class="form-label small fw-bold text-muted text-uppercase">Compensation ($ Per Annum)</label><input v-model="newDrive.salary" type="number" class="form-control rounded-3"></div>
          <div class="mb-3"><label class="form-label small fw-bold text-muted text-uppercase">Skills Stack Required</label><input v-model="newDrive.skills_required" class="form-control rounded-3"></div>
          <div class="mb-3"><label class="form-label small fw-bold text-muted text-uppercase">Min CGPA Threshold</label><input v-model="newDrive.min_cgpa" type="number" step="0.1" class="form-control rounded-3"></div>
          <div class="row">
            <div class="col-6 mb-3"><label class="form-label small fw-bold text-muted text-uppercase">Commencement Date</label><input v-model="newDrive.start_date" type="date" class="form-control rounded-3"></div>
            <div class="col-6 mb-3"><label class="form-label small fw-bold text-muted text-uppercase">Submission Deadline</label><input v-model="newDrive.deadline" type="date" class="form-control rounded-3"></div>
          </div>
        </div>
        <div class="modal-footer border-0 pt-0">
          <button type="button" class="btn btn-light rounded-3 fw-semibold px-4" data-bs-dismiss="modal">Cancel</button>
          <button class="btn btn-primary rounded-3 fw-semibold px-4" @click="emit('save-drive', newDrive)" data-bs-dismiss="modal">Submit for Approval</button>
        </div>
      </div>
    </div>
  </div>

  <!-- Candidate Profile Preview -->
  <div class="modal fade" id="candidateProfileModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-lg">
      <div class="modal-content border-0 shadow rounded-4" v-if="selectedCandidate">
        <div class="modal-header border-0 bg-light p-4 rounded-top-4">
          <h5 class="fw-bold m-0">{{ selectedCandidate.student_name }} Profile</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body p-4">
          <div class="mb-3 small bg-light p-3 rounded-3 border">
            <div><strong>Applied Role Target:</strong> {{ selectedCandidate.drive_title }}</div>
            <div v-if="selectedCandidate.branch_cgpa && Object.keys(selectedCandidate.branch_cgpa).length" class="mt-1">
              <div v-for="(cgpa, branch) in selectedCandidate.branch_cgpa" :key="branch"><strong>{{ branch }}:</strong> {{ cgpa }} CGPA</div>
            </div>
          </div>
          <div class="mb-3" v-if="selectedCandidate.skills">
            <h6 class="fw-bold border-bottom pb-1">Technical Competencies</h6>
            <div class="d-flex flex-wrap gap-1">
              <span v-for="s in selectedCandidate.skills.split(',')" :key="s" class="badge bg-secondary text-white rounded-pill">{{ s.trim() }}</span>
            </div>
          </div>
          <div class="mb-3" v-if="selectedCandidate.education">
            <h6 class="fw-bold border-bottom pb-1">Academic Education History</h6>
            <small style="white-space:pre-wrap;">{{ selectedCandidate.education }}</small>
          </div>
          <div class="mb-3" v-if="selectedCandidate.experience">
            <h6 class="fw-bold border-bottom pb-1">Experience & Project Portfolios</h6>
            <small style="white-space:pre-wrap;">{{ selectedCandidate.experience }}</small>
          </div>
          <a v-if="selectedCandidate.resume" :href="selectedCandidate.resume" target="_blank" class="btn btn-sm btn-primary py-2 rounded-3 w-100 mt-2">📄 Open Candidate Verification Resume</a>
        </div>
      </div>
    </div>
  </div>
</template>