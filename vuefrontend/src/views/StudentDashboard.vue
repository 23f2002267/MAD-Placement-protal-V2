<script setup>
import { ref, watch, computed } from 'vue'

const props = defineProps({
  drives: { type: Array, default: () => [] },
  applications: { type: Array, default: () => [] },
  profile: { type: Object, default: () => ({}) }
});

const emit = defineEmits(['apply-drive', 'update-profile']);

const activeTab = ref('drives');

// Local reactive variables for profile form
const profileName = ref('');
const profileBranch = ref('');
const profileCgpa = ref('');
const profileResume = ref('');
const profileEducation = ref('');
const profileSkills = ref('');
const profileExperience = ref('');

// Search & Filter state variables
const searchQuery = ref('');
const filterCompany = ref('');
const filterSkill = ref('');
const filterCgpa = ref(false);

// Sync props.profile to local state on load/change
watch(() => props.profile, (newProfile) => {
  if (newProfile) {
    profileName.value = newProfile.name || '';
    profileResume.value = newProfile.resume || '';
    profileEducation.value = newProfile.education || '';
    profileSkills.value = newProfile.skills || '';
    profileExperience.value = newProfile.experience || '';
    
    // Extract first key-value of branch_cgpa
    if (newProfile.branch_cgpa && typeof newProfile.branch_cgpa === 'object') {
      const keys = Object.keys(newProfile.branch_cgpa);
      if (keys.length > 0) {
        profileBranch.value = keys[0];
        profileCgpa.value = newProfile.branch_cgpa[keys[0]] || '';
      } else {
        profileBranch.value = '';
        profileCgpa.value = '';
      }
    } else {
      profileBranch.value = '';
      profileCgpa.value = '';
    }
  }
}, { immediate: true });

function handleSaveProfile() {
  const branch_cgpa = {};
  if (profileBranch.value) {
    branch_cgpa[profileBranch.value] = parseFloat(profileCgpa.value) || 0;
  }
  
  emit('update-profile', {
    name: profileName.value,
    branch_cgpa,
    resume: profileResume.value,
    education: profileEducation.value,
    skills: profileSkills.value,
    experience: profileExperience.value
  });
}

function formatDate(dateStr) {
  if (!dateStr) return 'N/A';
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  });
}

// Search and Filter computed properties
const uniqueCompanies = computed(() => {
  if (!Array.isArray(props.drives)) return [];
  const cos = props.drives.map(d => d.company).filter(Boolean);
  return [...new Set(cos)].sort();
});

const uniqueSkills = computed(() => {
  if (!Array.isArray(props.drives)) return [];
  const skillsSet = new Set();
  props.drives.forEach(d => {
    if (d.skills_required) {
      d.skills_required.split(',').forEach(s => {
        const trimmed = s.trim();
        if (trimmed) skillsSet.add(trimmed);
      });
    }
  });
  return [...skillsSet].sort();
});

const filteredDrives = computed(() => {
  if (!Array.isArray(props.drives)) return [];
  return props.drives.filter(d => {
    // Search query matching company name, title, or skills
    const q = searchQuery.value.toLowerCase().trim();
    const matchQuery = !q || 
      d.company?.toLowerCase().includes(q) ||
      d.title?.toLowerCase().includes(q) ||
      d.skills_required?.toLowerCase().includes(q) ||
      d.description?.toLowerCase().includes(q);

    // Specific Company dropdown filter
    const matchCompany = !filterCompany.value || d.company === filterCompany.value;

    // Specific Skill dropdown/badge filter
    const matchSkill = !filterSkill.value || (
      d.skills_required && d.skills_required.toLowerCase().split(',').map(s => s.trim()).includes(filterSkill.value.toLowerCase())
    );

    // Eligibility based on CGPA
    let matchEligibility = true;
    if (filterCgpa.value && profileCgpa.value) {
      matchEligibility = parseFloat(profileCgpa.value) >= parseFloat(d.min_cgpa || 0);
    }

    return matchQuery && matchCompany && matchSkill && matchEligibility;
  });
});

function clearFilters() {
  searchQuery.value = '';
  filterCompany.value = '';
  filterSkill.value = '';
  filterCgpa.value = false;
}

const hiredApplications = computed(() => {
  if (!Array.isArray(props.applications)) return [];
  return props.applications.filter(a => a.status === 'Selected');
});
</script>

<template>
  <div class="student-dashboard py-4">
    <!-- Header -->
    <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
      <div>
        <h3 class="fw-bold text-dark mb-1">Student Placement Portal</h3>
        <p class="text-muted mb-0">Apply to matching placement drives and track your application status.</p>
      </div>
    </div>

    <!-- Tab Buttons -->
    <div class="card border-0 shadow-sm rounded-4 mb-4 bg-white overflow-hidden">
      <div class="card-header bg-white border-0 p-3 pb-0">
        <ul class="nav nav-tabs border-0 gap-2">
          <li class="nav-item">
            <button 
              class="nav-link border-0 px-4 py-2.5 rounded-3 fw-semibold transition-all"
              :class="activeTab === 'drives' ? 'bg-primary text-white' : 'bg-light text-secondary'"
              @click="activeTab = 'drives'"
            >
              💼 Available Placement Drives ({{ props.drives?.length || 0 }})
            </button>
          </li>
          <li class="nav-item">
            <button 
              class="nav-link border-0 px-4 py-2.5 rounded-3 fw-semibold transition-all"
              :class="activeTab === 'applications' ? 'bg-primary text-white' : 'bg-light text-secondary'"
              @click="activeTab = 'applications'"
            >
              📥 My Submitted Applications ({{ props.applications?.length || 0 }})
            </button>
          </li>
          <li class="nav-item">
            <button 
              class="nav-link border-0 px-4 py-2.5 rounded-3 fw-semibold transition-all"
              :class="activeTab === 'hirings' ? 'bg-primary text-white' : 'bg-light text-secondary'"
              @click="activeTab = 'hirings'"
            >
              🎉 My Offer Letters ({{ hiredApplications?.length || 0 }})
            </button>
          </li>
          <li class="nav-item">
            <button 
              class="nav-link border-0 px-4 py-2.5 rounded-3 fw-semibold transition-all"
              :class="activeTab === 'profile' ? 'bg-primary text-white' : 'bg-light text-secondary'"
              @click="activeTab = 'profile'"
            >
              👤 My Profile
            </button>
          </li>
        </ul>
      </div>
    </div>

    <!-- Tab Contents -->
    <div v-if="activeTab === 'drives'">
      <!-- Search & Filters Controls -->
      <div class="card border-0 shadow-sm rounded-4 mb-4 bg-white p-3">
        <div class="row g-3 align-items-center">
          <!-- Text Search input -->
          <div class="col-md-4">
            <div class="input-group">
              <span class="input-group-text bg-light border-0 text-secondary">
                🔍
              </span>
              <input 
                v-model="searchQuery" 
                type="text" 
                class="form-control bg-light border-0 py-2" 
                placeholder="Search company, position, or skills..."
              >
            </div>
          </div>
          
          <!-- Company Filter select -->
          <div class="col-sm-6 col-md-3">
            <select v-model="filterCompany" class="form-select bg-light border-0 py-2">
              <option value="">All Companies</option>
              <option v-for="company in uniqueCompanies" :key="company" :value="company">
                {{ company }}
              </option>
            </select>
          </div>
          
          <!-- Skill Filter select -->
          <div class="col-sm-6 col-md-3">
            <select v-model="filterSkill" class="form-select bg-light border-0 py-2">
              <option value="">All Required Skills</option>
              <option v-for="skill in uniqueSkills" :key="skill" :value="skill">
                {{ skill }}
              </option>
            </select>
          </div>

          <!-- Eligibility Toggle -->
          <div class="col-sm-12 col-md-2">
            <div class="form-check form-switch mb-0">
              <input 
                v-model="filterCgpa" 
                class="form-check-input" 
                type="checkbox" 
                id="eligibilityToggle"
              >
              <label class="form-check-label small fw-semibold text-secondary" for="eligibilityToggle">
                Eligible Only
              </label>
            </div>
          </div>
        </div>
        
        <!-- Active Filter Tags list -->
        <div v-if="searchQuery || filterCompany || filterSkill || filterCgpa" class="d-flex flex-wrap gap-2 mt-3 pt-3 border-top">
          <span class="text-muted small align-self-center">Active filters:</span>
          
          <span v-if="searchQuery" class="badge bg-secondary-subtle text-secondary border border-secondary-subtle d-flex align-items-center gap-1 py-1.5 px-2.5 rounded-pill">
            Query: "{{ searchQuery }}"
            <button @click="searchQuery = ''" class="btn-close" style="font-size: 0.5rem;" aria-label="Close"></button>
          </span>
          
          <span v-if="filterCompany" class="badge bg-secondary-subtle text-secondary border border-secondary-subtle d-flex align-items-center gap-1 py-1.5 px-2.5 rounded-pill">
            Company: {{ filterCompany }}
            <button @click="filterCompany = ''" class="btn-close" style="font-size: 0.5rem;" aria-label="Close"></button>
          </span>
          
          <span v-if="filterSkill" class="badge bg-secondary-subtle text-secondary border border-secondary-subtle d-flex align-items-center gap-1 py-1.5 px-2.5 rounded-pill">
            Skill: {{ filterSkill }}
            <button @click="filterSkill = ''" class="btn-close" style="font-size: 0.5rem;" aria-label="Close"></button>
          </span>

          <span v-if="filterCgpa" class="badge bg-secondary-subtle text-secondary border border-secondary-subtle d-flex align-items-center gap-1 py-1.5 px-2.5 rounded-pill">
            Eligible Only
            <button @click="filterCgpa = false" class="btn-close" style="font-size: 0.5rem;" aria-label="Close"></button>
          </span>
          
          <button @click="clearFilters" class="btn btn-link btn-sm p-0 text-decoration-none text-danger small ms-auto fw-semibold">
            Clear All
          </button>
        </div>
      </div>

      <div class="row g-4">
        <!-- Available drives loop -->
        <div class="col-12" v-if="props.drives?.length === 0">
          <div class="card p-5 text-center border-0 shadow-sm rounded-4 bg-white text-muted">
            <div class="display-6 mb-2">💼</div>
            <p class="mb-0">No placement drives are currently approved and open for applications.</p>
          </div>
        </div>

        <div class="col-12" v-else-if="filteredDrives.length === 0">
          <div class="card p-5 text-center border-0 shadow-sm rounded-4 bg-white text-muted">
            <div class="display-6 mb-2">🔍</div>
            <p class="mb-1 fw-semibold text-dark">No matching placement drives found.</p>
            <p class="mb-0 small">Try modifying your search queries or clearing active filters.</p>
          </div>
        </div>
        
        <div v-else class="col-md-6 col-lg-4" v-for="d in filteredDrives" :key="d.id">
          <div class="card h-100 border-0 shadow-sm rounded-4 p-4 bg-white d-flex flex-column">
            <div class="d-flex justify-content-between align-items-start mb-2">
              <span class="badge bg-primary-subtle text-primary rounded-pill px-3 py-1.5 fw-semibold">{{ d.company }}</span>
              <span class="fw-bold text-success">${{ d.salary?.toLocaleString() }}/yr</span>
            </div>
            
            <h5 class="fw-bold text-dark mt-2 mb-1">{{ d.title }}</h5>
            
            <div class="d-flex align-items-center gap-2 mb-2">
              <div class="text-muted small">Min CGPA: <strong class="text-dark">{{ d.min_cgpa }}</strong></div>
              <span v-if="profileCgpa && parseFloat(profileCgpa) < parseFloat(d.min_cgpa)" class="badge bg-danger-subtle text-danger rounded-pill px-2 py-0.5 fw-semibold" style="font-size: 0.7rem;">Ineligible</span>
              <span v-else-if="profileCgpa" class="badge bg-success-subtle text-success rounded-pill px-2 py-0.5 fw-semibold" style="font-size: 0.7rem;">Eligible</span>
            </div>

            <!-- Required Skills display -->
            <div v-if="d.skills_required" class="d-flex flex-wrap gap-1 mb-3">
              <span 
                v-for="skill in d.skills_required.split(',')" 
                :key="skill" 
                class="badge bg-secondary-subtle text-secondary rounded-pill px-2 py-1 fw-medium"
                style="font-size: 0.75rem;"
              >
                {{ skill.trim() }}
              </span>
            </div>
            
            <p class="text-secondary small flex-grow-1 line-clamp-3 mb-3">{{ d.description }}</p>
            
            <div class="border-top pt-3 mt-auto">
              <div class="d-flex justify-content-between align-items-center mb-3 text-muted small">
                <span>Deadline:</span>
                <span class="text-danger fw-semibold">{{ formatDate(d.deadline) }}</span>
              </div>
              
              <button 
                class="btn w-100 py-2 rounded-3 fw-semibold transition-all"
                :class="d.applied ? 'btn-secondary' : 'btn-primary'"
                @click="$emit('apply-drive', d.id)" 
                :disabled="d.applied"
              >
                <span v-if="d.applied">✔ Applied</span>
                <span v-else>Apply Now</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="activeTab === 'applications'">
      <div class="card p-4 border-0 shadow-sm rounded-4 bg-white">
        <h5 class="fw-bold text-dark mb-3">Your Job Applications History</h5>
        
        <div v-if="props.applications?.length === 0" class="text-center py-5 text-muted">
          <div class="display-6 mb-2">📥</div>
          <p class="mb-0">You have not submitted any applications yet.</p>
        </div>
        
        <div v-else class="table-responsive">
          <table class="table align-middle">
            <thead>
              <tr>
                <th class="text-muted small fw-bold text-uppercase border-0">Job / Placement Drive</th>
                <th class="text-muted small fw-bold text-uppercase border-0">Company</th>
                <th class="text-muted small fw-bold text-uppercase border-0">Salary</th>
                <th class="text-muted small fw-bold text-uppercase border-0">Date Applied</th>
                <th class="text-muted small fw-bold text-uppercase border-0">Status</th>
              </tr>
            </thead>
            <tbody>
              <template v-for="app in props.applications" :key="app.id">
                <!-- Application Row -->
                <tr>
                  <td class="fw-bold text-dark border-0">
                    {{ app.drive_title }}
                  </td>
                  <td class="text-secondary border-0 fw-semibold">{{ app.company_name }}</td>
                  <td class="text-dark border-0">${{ app.salary?.toLocaleString() }}</td>
                  <td class="text-muted small border-0">{{ formatDate(app.date_applied) }}</td>
                  <td class="border-0">
                    <span 
                      class="badge px-3 py-2 rounded-pill fw-semibold"
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
                </tr>
                <!-- Feedback, Interview, and Offer Letter Sub-Row -->
                <tr v-if="app.feedback || (app.status === 'Shortlisted' && app.interview_time) || (app.status === 'Selected' && app.offer_letter_link)" :key="'fb-' + app.id">
                  <td colspan="5" class="bg-light-subtle py-2 px-3 border-0">
                    <div class="d-flex flex-column gap-2 my-1">
                      <!-- Offer Letter Details Card -->
                      <div v-if="app.status === 'Selected' && app.offer_letter_link" class="card border-0 bg-success-subtle p-3 rounded-4">
                        <div class="small fw-bold text-success text-uppercase tracking-wider mb-2" style="font-size: 0.75rem;">🎉 Congratulations! You have been Selected / Hired!</div>
                        <div class="row align-items-center">
                          <div class="col-sm-6 mb-2 mb-sm-0">
                            <span class="text-secondary small d-block">Offer Letter from <strong>{{ app.company_name }}</strong>:</span>
                            <div class="fw-bold text-success">Active Placement Offer</div>
                          </div>
                          <div class="col-sm-6 text-sm-end">
                            <a :href="app.offer_letter_link" target="_blank" class="btn btn-success btn-sm rounded-3 fw-semibold px-3 py-1.5">
                              📄 View & Download Offer Letter
                            </a>
                          </div>
                        </div>
                      </div>

                      <!-- Interview Details Card -->
                      <div v-if="app.status === 'Shortlisted' && app.interview_time" class="card border-0 bg-primary-subtle p-3 rounded-4">
                        <div class="small fw-bold text-primary text-uppercase tracking-wider mb-2" style="font-size: 0.75rem;">🎉 Interview Invitation Scheduled!</div>
                        <div class="row align-items-center">
                          <div class="col-sm-6 mb-2 mb-sm-0">
                            <span class="text-secondary small d-block">Scheduled Time:</span>
                            <div class="fw-bold text-dark">{{ app.interview_time }}</div>
                          </div>
                          <div class="col-sm-6 text-sm-end">
                            <a v-if="app.interview_link" :href="app.interview_link" target="_blank" class="btn btn-primary btn-sm rounded-3 fw-semibold px-3 py-1.5">
                              🚀 Join Meeting Link
                            </a>
                            <span v-else class="text-muted small italic">Meeting link will be shared soon</span>
                          </div>
                        </div>
                      </div>

                      <!-- Feedback Card -->
                      <div v-if="app.feedback" class="card border-0 bg-light p-3 rounded-4">
                        <div class="small fw-bold text-secondary mb-1">💬 Company Feedback:</div>
                        <p class="mb-0 text-dark small italic">"{{ app.feedback }}"</p>
                      </div>
                    </div>
                  </td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Hired & Offer Letters Tab -->
    <div v-else-if="activeTab === 'hirings'">
      <div class="card p-4 border-0 shadow-sm rounded-4 bg-white">
        <h5 class="fw-bold text-dark mb-3">🎉 Your Hirings & Official Offer Letters</h5>
        <p class="text-secondary small mb-4">
          Congratulations on your placement! Below are the companies that have selected you, along with your official offer letter links.
        </p>
        
        <div v-if="hiredApplications.length === 0" class="text-center py-5 text-muted">
          <div class="display-6 mb-2">🎓</div>
          <p class="mb-0">No active hires or offer letters yet. Keep applying and doing your best!</p>
        </div>
        
        <div v-else class="row g-4">
          <div v-for="app in hiredApplications" :key="app.id" class="col-md-6">
            <div class="card border border-success-subtle rounded-4 p-4 h-100 bg-white shadow-sm position-relative overflow-hidden">
              <!-- Corner Accent -->
              <div class="position-absolute top-0 end-0 bg-success text-white px-3 py-1 fw-bold small" style="border-bottom-left-radius: 12px;">
                Hired
              </div>
              
              <div class="mb-3">
                <span class="badge bg-success-subtle text-success rounded-pill px-3 py-1 fw-semibold mb-2">
                  {{ app.company_name }}
                </span>
                <h4 class="fw-bold text-dark mb-1">{{ app.drive_title }}</h4>
                <div class="text-muted small">Offered Salary: <strong class="text-dark">${{ app.salary?.toLocaleString() }}/yr</strong></div>
              </div>

              <!-- Offer Letter Section -->
              <div class="bg-light p-3 rounded-3 mb-3 border border-success-subtle">
                <div class="d-flex justify-content-between align-items-center">
                  <div>
                    <span class="text-muted small d-block">Official Offer:</span>
                    <strong class="text-success text-uppercase" style="font-size: 0.85rem;">Letter Issued</strong>
                  </div>
                  <a v-if="app.offer_letter_link" :href="app.offer_letter_link" target="_blank" class="btn btn-success rounded-3 btn-sm fw-bold px-3">
                    📄 View Offer Letter
                  </a>
                  <span v-else class="text-muted small italic">Link pending</span>
                </div>
              </div>

              <div v-if="app.feedback" class="small text-secondary">
                <strong class="text-dark d-block mb-1">Company Feedback / Congratulations Message:</strong>
                <span class="italic">"{{ app.feedback }}"</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- My Profile Tab -->
    <div v-else-if="activeTab === 'profile'">
      <div class="row g-4">
        <!-- Left: Profile summary display -->
        <div class="col-lg-4">
          <div class="card border-0 shadow-sm rounded-4 p-4 bg-white text-center">
            <div class="avatar-placeholder mx-auto mb-3 d-flex align-items-center justify-content-center bg-primary-subtle text-primary rounded-circle" style="width: 80px; height: 80px; font-size: 2.2rem;">
              🎓
            </div>
            <h4 class="fw-bold text-dark mb-1">{{ props.profile?.name || 'Your Name' }}</h4>
            <p class="text-muted small mb-3">Student Candidate</p>
            
            <hr class="my-3 opacity-50">
            
            <div class="text-start">
              <div class="mb-3">
                <span class="text-muted small d-block">Department / Branch:</span>
                <span class="fw-semibold text-dark">{{ profileBranch || 'Not specified yet' }}</span>
              </div>
              <div class="mb-3">
                <span class="text-muted small d-block">Current CGPA:</span>
                <span class="fw-bold text-success" v-if="profileCgpa">{{ profileCgpa }} / 10.0</span>
                <span class="text-muted small italic" v-else>Not specified yet</span>
              </div>
              <div class="mb-3">
                <span class="text-muted small d-block">Resume Link / URL:</span>
                <a v-if="profileResume" :href="profileResume" target="_blank" class="text-decoration-underline fw-semibold text-primary break-all small">
                  📄 View Saved Resume
                </a>
                <span class="text-muted small italic" v-else>No resume linked yet</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Right: Edit Profile Form -->
        <div class="col-lg-8">
          <div class="card border-0 shadow-sm rounded-4 p-4 bg-white">
            <h5 class="fw-bold text-dark mb-4">Update Profile Information</h5>
            
            <form @submit.prevent="handleSaveProfile">
              <div class="row g-3">
                <!-- Name -->
                <div class="col-md-12">
                  <label class="form-label small fw-bold text-muted text-uppercase">Full Name</label>
                  <input v-model="profileName" type="text" class="form-control rounded-3" required placeholder="John Doe">
                </div>

                <!-- Branch & CGPA -->
                <div class="col-md-6">
                  <label class="form-label small fw-bold text-muted text-uppercase">Academic Branch</label>
                  <select v-model="profileBranch" class="form-select rounded-3">
                    <option value="">Select Branch</option>
                    <option value="Computer Science">Computer Science</option>
                    <option value="Information Technology">Information Technology</option>
                    <option value="Electronics">Electronics</option>
                    <option value="Electrical">Electrical</option>
                    <option value="Mechanical">Mechanical</option>
                    <option value="Civil">Civil</option>
                  </select>
                </div>
                
                <div class="col-md-6">
                  <label class="form-label small fw-bold text-muted text-uppercase">Cumulative GPA (CGPA)</label>
                  <input v-model="profileCgpa" type="number" step="0.01" min="0" max="10" class="form-control rounded-3" placeholder="e.g. 8.5">
                </div>

                <!-- Resume Link -->
                <div class="col-12">
                  <label class="form-label small fw-bold text-muted text-uppercase">Resume Link / URL</label>
                  <input v-model="profileResume" type="url" class="form-control rounded-3" placeholder="e.g. https://drive.google.com/file/d/.../view">
                  <div class="form-text small">Provide a public, shareable link to your PDF resume (Google Drive, Dropbox, etc).</div>
                </div>

                <!-- Education -->
                <div class="col-12">
                  <label class="form-label small fw-bold text-muted text-uppercase">Education History</label>
                  <textarea v-model="profileEducation" class="form-control rounded-3" rows="3" placeholder="e.g. B.Tech in Computer Science - XYZ University (2022-2026)"></textarea>
                  <div class="form-text small">List your degrees, majors, colleges/universities, and years.</div>
                </div>

                <!-- Experience -->
                <div class="col-12">
                  <label class="form-label small fw-bold text-muted text-uppercase">Experience / Internships</label>
                  <textarea v-model="profileExperience" class="form-control rounded-3" rows="3" placeholder="e.g. Frontend Intern at TechSolutions Inc (May 2025 - July 2025)&#10;Worked on developing user dashboards using React and Bootstrap."></textarea>
                  <div class="form-text small">Describe your previous work experience, internships, or key academic/personal projects.</div>
                </div>

                <!-- Skills -->
                <div class="col-12">
                  <label class="form-label small fw-bold text-muted text-uppercase">Key Skills</label>
                  <textarea v-model="profileSkills" class="form-control rounded-3" rows="2" placeholder="e.g. HTML, CSS, JavaScript, Vue, Node.js, SQL, Git"></textarea>
                  <div class="form-text small">List your technical skills separated by commas (e.g. React, Python, AWS).</div>
                </div>
              </div>

              <div class="text-end mt-4">
                <button type="submit" class="btn btn-primary rounded-3 fw-semibold px-4 py-2.5 transition-all">
                  💾 Save Profile Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;  
  overflow: hidden;
}
.transition-all {
  transition: all 0.2s ease-in-out;
}
</style>
