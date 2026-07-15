<script setup>
import { reactive, watch, ref, computed } from 'vue'

const props = defineProps({
  user: { type: Object, default: () => ({ id: 0, email: '' }) },
  drives: { type: Array, default: () => [] },
  profile: { type: Object, default: () => ({ id: 0, name: '', website: '', status: 'Pending' }) },
  applications: { type: Array, default: () => [] }
});

const emit = defineEmits(['save-drive', 'update-profile', 'update-application-status', 'update-drive-status']);

const activeTab = ref('overview');

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

// Computed Statistics
const totalDrives = computed(() => props.drives?.length || 0);
const totalApps = computed(() => props.applications?.length || 0);
const shortlistedCount = computed(() => props.applications?.filter(a => a.status === 'Shortlisted').length || 0);
const selectedCount = computed(() => props.applications?.filter(a => a.status === 'Selected').length || 0);

// Filter lists
const pendingApps = computed(() => props.applications?.filter(a => a.status === 'Applied') || []);
const shortlistedApps = computed(() => props.applications?.filter(a => a.status === 'Shortlisted' || a.status === 'Selected') || []);

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

function openReviewModal(app, status) {
  activeAppToReview.value = app;
  reviewStatus.value = status;
  reviewFeedback.value = app.feedback || '';
  reviewInterviewTime.value = app.interview_time || '';
  reviewInterviewLink.value = app.interview_link || '';
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
    interview_link: reviewStatus.value === 'Shortlisted' ? reviewInterviewLink.value : ''
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
</script>

<template>
  <div class="company-dashboard-container py-4">
    <!-- Verification / Pending Profile screen -->
    <div v-if="props.profile?.status !== 'Approved'" class="verification-screen max-w-lg mx-auto py-5" style="max-width: 550px;">
      <div class="card shadow border-0 p-5 rounded-4 bg-light">
        <!-- Pending State Icon/Badge -->
        <div v-if="props.profile?.status === 'Pending'" class="mb-4 text-center">
          <div class="display-3 text-warning mb-3">🕒</div>
          <h2 class="fw-bold text-dark mb-2">Verification Pending</h2>
          <p class="text-secondary">
            Thank you for registering with <strong>PlacePort</strong>! Your company account is currently under review by our administrators.
          </p>
        </div>

        <!-- Rejected State Icon/Badge -->
        <div v-else-if="props.profile?.status === 'Rejected'" class="mb-4 text-center">
          <div class="display-3 text-danger mb-3">❌</div>
          <h2 class="fw-bold text-dark mb-2">Registration Rejected</h2>
          <p class="text-secondary">
            Unfortunately, your registration was rejected by the Admin. Please review and update your company profile details below to resubmit for approval.
          </p>
        </div>

        <!-- Update Profile Notice & Form -->
        <div class="profile-update-box border-top pt-4 mt-2 text-start">
          <h5 class="fw-semibold text-dark mb-2">Update Company Profile</h5>
          <p class="text-muted small mb-4">
            Ensure your profile information is accurate and complete to avoid registration rejection.
          </p>
          
          <form @submit.prevent="$emit('update-profile', { name: profileForm.name, website: profileForm.website })">
            <div class="mb-3">
              <label class="form-label small fw-bold text-uppercase text-muted">Company Name</label>
              <input 
                v-model="profileForm.name" 
                type="text" 
                class="form-control rounded-3" 
                placeholder="Enter company name" 
                required
              >
            </div>
            
            <div class="mb-4">
              <label class="form-label small fw-bold text-uppercase text-muted">Company Website</label>
              <input 
                v-model="profileForm.website" 
                type="url" 
                class="form-control rounded-3" 
                placeholder="https://example.com"
                required
              >
            </div>
            
            <button type="submit" class="btn btn-primary w-100 py-2.5 rounded-3 fw-semibold">
              Update Profile & Submit for Verification
            </button>
          </form>
        </div>
      </div>
    </div>

    <!-- Approved Dashboard View -->
    <div v-else>
      <div class="d-flex justify-content-between mb-4 align-items-center flex-wrap gap-3">
        <div>
          <h3 class="fw-bold text-dark mb-1">Welcome, {{ props.profile?.name || props.user?.email }}</h3>
          <p class="text-muted mb-0">Manage placement drives, review applications, and select top talents.</p>
        </div>
        <button class="btn btn-primary px-4 py-2.5 rounded-3 fw-semibold" data-bs-toggle="modal" data-bs-target="#driveModal">
          <span class="me-1">➕</span> New Placement Drive
        </button>
      </div>

      <!-- Quick Metrics Grid -->
      <div class="row g-3 mb-4">
        <div class="col-6 col-md-3">
          <div class="card border-0 shadow-sm rounded-4 p-3 bg-white h-100">
            <div class="small fw-bold text-muted text-uppercase mb-1">Job Postings</div>
            <div class="d-flex align-items-baseline gap-2">
              <span class="fs-2 fw-extrabold text-primary">{{ totalDrives }}</span>
              <span class="text-muted small">created</span>
            </div>
          </div>
        </div>
        <div class="col-6 col-md-3">
          <div class="card border-0 shadow-sm rounded-4 p-3 bg-white h-100">
            <div class="small fw-bold text-muted text-uppercase mb-1">Applications</div>
            <div class="d-flex align-items-baseline gap-2">
              <span class="fs-2 fw-extrabold text-info">{{ totalApps }}</span>
              <span class="text-muted small">received</span>
            </div>
          </div>
        </div>
        <div class="col-6 col-md-3">
          <div class="card border-0 shadow-sm rounded-4 p-3 bg-white h-100">
            <div class="small fw-bold text-muted text-uppercase mb-1">Shortlisted</div>
            <div class="d-flex align-items-baseline gap-2">
              <span class="fs-2 fw-extrabold text-warning">{{ shortlistedCount }}</span>
              <span class="text-muted small">candidates</span>
            </div>
          </div>
        </div>
        <div class="col-6 col-md-3">
          <div class="card border-0 shadow-sm rounded-4 p-3 bg-white h-100">
            <div class="small fw-bold text-muted text-uppercase mb-1">Selected</div>
            <div class="d-flex align-items-baseline gap-2">
              <span class="fs-2 fw-extrabold text-success">{{ selectedCount }}</span>
              <span class="text-muted small">hired</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Tab Navigation -->
      <div class="card border-0 shadow-sm rounded-4 mb-4 bg-white overflow-hidden">
        <div class="card-header bg-white border-0 p-3 pb-0">
          <ul class="nav nav-tabs border-0 gap-2">
            <li class="nav-item">
              <button 
                class="nav-link border-0 px-4 py-2.5 rounded-3 fw-semibold transition-all"
                :class="activeTab === 'overview' ? 'bg-primary text-white' : 'bg-light text-secondary'"
                @click="activeTab = 'overview'"
              >
                📊 Dashboard Overview
              </button>
            </li>
            <li class="nav-item">
              <button 
                class="nav-link border-0 px-4 py-2.5 rounded-3 fw-semibold transition-all"
                :class="activeTab === 'drives' ? 'bg-primary text-white' : 'bg-light text-secondary'"
                @click="activeTab = 'drives'"
              >
                💼 Placement Drives ({{ totalDrives }})
              </button>
            </li>
            <li class="nav-item">
              <button 
                class="nav-link border-0 px-4 py-2.5 rounded-3 fw-semibold transition-all"
                :class="activeTab === 'applications' ? 'bg-primary text-white' : 'bg-light text-secondary'"
                @click="activeTab = 'applications'"
              >
                📥 Received Applications ({{ pendingApps.length }})
              </button>
            </li>
            <li class="nav-item">
              <button 
                class="nav-link border-0 px-4 py-2.5 rounded-3 fw-semibold transition-all"
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

      <!-- Tab: Overview -->
      <div v-if="activeTab === 'overview'" class="tab-pane-content">
        <div class="row g-4">
          <!-- Left: Recent Applications -->
          <div class="col-lg-8">
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
                          <div class="fw-semibold text-dark">{{ app.student_name }}</div>
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

          <!-- Right: Profile Details -->
          <div class="col-lg-4">
            <div class="card border-0 shadow-sm rounded-4 p-4 bg-white">
              <h5 class="fw-bold text-dark mb-3">Company Profile</h5>
              <div class="mb-3">
                <label class="small text-muted text-uppercase fw-bold d-block">Status</label>
                <span class="badge bg-success-subtle text-success px-3 py-1.5 rounded-pill fw-semibold mt-1">Verified Approved</span>
              </div>
              <div class="mb-3">
                <label class="small text-muted text-uppercase fw-bold d-block">Registered Name</label>
                <div class="fw-bold text-dark mt-1">{{ props.profile?.name }}</div>
              </div>
              <div class="mb-3">
                <label class="small text-muted text-uppercase fw-bold d-block">Website</label>
                <a :href="props.profile?.website" target="_blank" class="text-decoration-none text-primary fw-medium d-block mt-1">
                  {{ props.profile?.website || 'Not specified' }}
                </a>
              </div>
              <div class="mb-3">
                <label class="small text-muted text-uppercase fw-bold d-block">Portal Email</label>
                <div class="text-dark mt-1">{{ props.user?.email }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Tab: Placement Drives -->
      <div v-else-if="activeTab === 'drives'" class="tab-pane-content">
        <div class="card p-4 border-0 shadow-sm rounded-4 bg-white">
          <div class="d-flex justify-content-between align-items-center mb-3">
            <h5 class="fw-bold text-dark mb-0">Your Created Placement Drives</h5>
          </div>
          
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
                    <p class="text-muted small mb-0 max-w-sm text-truncate" style="max-width: 320px;">{{ drive?.desc }}</p>
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
                      class="btn btn-outline-secondary btn-sm rounded-3 px-3 py-1.5 fw-semibold"
                    >
                      🛑 Close Job
                    </button>
                    <button 
                      v-else-if="drive?.status === 'Closed'"
                      @click="toggleDriveStatus(drive.id, 'Closed')"
                      class="btn btn-success btn-sm rounded-3 px-3 py-1.5 fw-semibold text-white"
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
                    <div class="fw-bold text-dark">{{ app.student_name }}</div>
                    <div class="text-muted small">{{ app.student_email }}</div>
                  </td>
                  <td class="border-0 fw-semibold text-secondary">{{ app.drive_title }}</td>
                  <td class="border-0">
                    <div v-if="app.branch_cgpa" class="small">
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
                      <button 
                        @click="openReviewModal(app, 'Shortlisted')" 
                        class="btn btn-warning btn-sm fw-semibold rounded-3 px-3 py-1.5"
                      >
                        ⭐ Shortlist
                      </button>
                      <button 
                        @click="openReviewModal(app, 'Rejected')" 
                        class="btn btn-outline-danger btn-sm fw-semibold rounded-3 px-3 py-1.5"
                      >
                        Dismiss
                      </button>
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
                    <div class="fw-bold text-dark">{{ app.student_name }}</div>
                    <div class="text-muted small mb-1">{{ app.student_email }}</div>
                    
                    <!-- Scheduled Interview Info Block -->
                    <div v-if="app.status === 'Shortlisted' && app.interview_time" class="mt-2 p-2.5 rounded-3 border-0 bg-primary-subtle text-primary-emphasis" style="max-width: 280px;">
                      <div class="small fw-bold text-uppercase tracking-wider opacity-75 mb-1" style="font-size: 0.7rem;">💬 Interview Scheduled</div>
                      <div class="small fw-semibold d-flex align-items-center gap-1">
                        <span>🕒</span> {{ app.interview_time }}
                      </div>
                      <div v-if="app.interview_link" class="small mt-1 d-flex align-items-center gap-1 text-truncate">
                        <span>🔗</span> Link: 
                        <a :href="app.interview_link" target="_blank" class="fw-bold text-decoration-underline text-truncate text-primary" style="max-width: 180px;">
                          Join Meeting
                        </a>
                      </div>
                    </div>
                  </td>
                  <td class="border-0 fw-semibold text-secondary">{{ app.drive_title }}</td>
                  <td class="border-0">
                    <a v-if="app.resume" :href="app.resume" target="_blank" class="btn btn-outline-primary btn-sm rounded-3">
                      📄 View Resume
                    </a>
                    <span v-else class="text-muted small">No Resume</span>
                  </td>
                  <td class="border-0">
                    <span 
                      class="badge px-3 py-2 rounded-pill fw-semibold"
                      :class="app.status === 'Selected' ? 'bg-success text-white' : 'bg-warning text-dark'"
                    >
                      {{ app.status }}
                    </span>
                  </td>
                  <td class="border-0 text-end">
                    <div class="d-flex gap-2 justify-content-end">
                      <button 
                        v-if="app.status === 'Shortlisted'"
                        @click="openReviewModal(app, 'Selected')" 
                        class="btn btn-success btn-sm fw-semibold rounded-3 px-3 py-1.5"
                      >
                        ✔ Mark as Selected / Hired
                      </button>
                      <button 
                        @click="openReviewModal(app, 'Rejected')" 
                        class="btn btn-outline-danger btn-sm fw-semibold rounded-3 px-3 py-1.5"
                      >
                        Reject Candidate
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Application Review / Interview Scheduling Modal -->
  <div v-if="activeAppToReview" class="modal-backdrop fade show" style="z-index: 1040;"></div>
  <div v-if="activeAppToReview" class="modal fade show d-block" tabindex="-1" style="z-index: 1050; background: rgba(0, 0, 0, 0.55);" @click.self="closeReviewModal">
    <div class="modal-dialog modal-dialog-centered">
      <div class="modal-content rounded-4 border-0 shadow">
        <div class="modal-header border-0 pb-0">
          <h5 class="modal-title fw-bold text-dark">
            Review Candidate: {{ activeAppToReview.student_name }}
          </h5>
          <button type="button" class="btn-close" @click="closeReviewModal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <p class="text-secondary small mb-3">
            Applying for: <strong class="text-dark">{{ activeAppToReview.drive_title }}</strong>
          </p>

          <div class="mb-3">
            <label class="form-label small fw-bold text-muted text-uppercase">Decision Status</label>
            <select v-model="reviewStatus" class="form-select rounded-3">
              <option value="Shortlisted">⭐ Shortlisted (Schedule Interview)</option>
              <option value="Selected">✔ Selected / Hired</option>
              <option value="Rejected">❌ Rejected / Dismissed</option>
            </select>
          </div>

          <!-- Conditional Interview Scheduling Fields -->
          <div v-if="reviewStatus === 'Shortlisted'" class="p-3 bg-light rounded-4 mb-3 border border-warning-subtle">
            <h6 class="fw-bold text-dark mb-3">📅 Schedule Interview</h6>
            
            <div class="mb-3">
              <label class="form-label small fw-bold text-muted text-uppercase">Date & Time</label>
              <input v-model="reviewInterviewTime" type="text" class="form-control rounded-3" placeholder="e.g. July 20, 2026, 10:00 AM PST">
              <span class="text-muted" style="font-size: 0.75rem;">Specify a date/time or standard calendar slot.</span>
            </div>

            <div class="mb-1">
              <label class="form-label small fw-bold text-muted text-uppercase">Interview Link / URL</label>
              <input v-model="reviewInterviewLink" type="url" class="form-control rounded-3" placeholder="e.g. https://meet.google.com/abc-defg-hij">
              <span class="text-muted" style="font-size: 0.75rem;">Google Meet, Zoom, or Teams link.</span>
            </div>
          </div>

          <div class="mb-3">
            <label class="form-label small fw-bold text-muted text-uppercase">Review Feedback / Reason</label>
            <textarea v-model="reviewFeedback" class="form-control rounded-3" rows="3" placeholder="Provide feedback or reasons for the student..."></textarea>
          </div>
        </div>
        <div class="modal-footer border-0 pt-0">
          <button type="button" class="btn btn-light rounded-3 fw-semibold px-4" @click="closeReviewModal">Cancel</button>
          <button class="btn btn-primary rounded-3 fw-semibold px-4" @click="submitReview">Save Decision</button>
        </div>
      </div>
    </div>
  </div>

  <!-- Drive Modal -->
  <div class="modal fade" id="driveModal" tabindex="-1">
    <div class="modal-dialog">
      <div class="modal-content rounded-4 border-0 shadow">
        <div class="modal-header border-0 pb-0">
          <h5 class="modal-title fw-bold text-dark">Create Placement Drive</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <div class="mb-3">
            <label class="form-label small fw-bold text-muted text-uppercase">Title</label>
            <input v-model="newDrive.title" class="form-control rounded-3" placeholder="Software Engineer Intern">
          </div>
          <div class="mb-3">
            <label class="form-label small fw-bold text-muted text-uppercase">Description</label>
            <textarea v-model="newDrive.desc" class="form-control rounded-3" rows="3" placeholder="Describe the job role and responsibilities..."></textarea>
          </div>
          <div class="mb-3">
            <label class="form-label small fw-bold text-muted text-uppercase">Salary ($ / Annum)</label>
            <input v-model="newDrive.salary" type="number" class="form-control rounded-3" placeholder="100000">
          </div>
          <div class="mb-3">
            <label class="form-label small fw-bold text-muted text-uppercase">Skills Required</label>
            <input v-model="newDrive.skills_required" class="form-control rounded-3" placeholder="React, Node.js, Python">
          </div>
          <div class="mb-3">
            <label class="form-label small fw-bold text-muted text-uppercase">Min CGPA Required</label>
            <input v-model="newDrive.min_cgpa" type="number" step="0.1" class="form-control rounded-3" placeholder="7.5">
          </div>
          <div class="row">
            <div class="col-6 mb-3">
              <label class="form-label small fw-bold text-muted text-uppercase">Start Date</label>
              <input v-model="newDrive.start_date" type="date" class="form-control rounded-3">
            </div>
            <div class="col-6 mb-3">
              <label class="form-label small fw-bold text-muted text-uppercase">Deadline</label>
              <input v-model="newDrive.deadline" type="date" class="form-control rounded-3">
            </div>
          </div>
        </div>
        <div class="modal-footer border-0 pt-0">
          <button type="button" class="btn btn-light rounded-3 fw-semibold px-4" data-bs-toggle="modal" data-bs-target="#driveModal">Cancel</button>
          <button class="btn btn-primary rounded-3 fw-semibold px-4" @click="$emit('save-drive', newDrive)" data-bs-dismiss="modal">Submit for Approval</button>
        </div>
      </div>
    </div>
  </div>
</template>
