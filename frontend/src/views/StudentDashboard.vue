<script setup>
import { ref, watch, computed } from 'vue'

const props = defineProps({
  currentBtn: { type: String, default: 'Dashboard' },
  drives: { type: Array, default: () => [] },
  applications: { type: Array, default: () => [] },
  profile: { type: Object, default: () => ({}) }
});

const emit = defineEmits(['apply-drive', 'update-profile', 'trigger-student-export']);

function triggerStudentExport() {
  emit('trigger-student-export');
}

const activeTab = ref('drives');

watch(() => props.currentBtn, (newBtn) => {
  if (newBtn === 'Dashboard') {
    if (activeTab.value !== 'drives' && activeTab.value !== 'hirings') {
      activeTab.value = 'drives';
    }
  }
}, { immediate: true });

const profileName = ref('');
const profileBranch = ref('');
const profileCgpa = ref('');
const profileResume = ref('');
const profileEducation = ref('');
const profileSkills = ref('');
const profileExperience = ref('');

const searchQuery = ref('');
const filterCompany = ref('');
const filterSkill = ref('');
const filterCgpa = ref(false);

watch(() => props.profile, (newProfile) => {
  if (newProfile) {
    profileName.value = newProfile.name || '';
    profileResume.value = newProfile.resume || '';
    profileEducation.value = newProfile.education || '';
    profileSkills.value = newProfile.skills || '';
    profileExperience.value = newProfile.experience || '';
    
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
  const branch_cgpa = props.profile?.branch_cgpa ? { ...props.profile.branch_cgpa } : {};
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
    const q = searchQuery.value.toLowerCase().trim();
    const matchQuery = !q || 
      d.company?.toLowerCase().includes(q) ||
      d.title?.toLowerCase().includes(q) ||
      d.skills_required?.toLowerCase().includes(q) ||
      d.description?.toLowerCase().includes(q);

    const matchCompany = !filterCompany.value || d.company === filterCompany.value;

    const matchSkill = !filterSkill.value || (
      d.skills_required && d.skills_required.toLowerCase().split(',').map(s => s.trim()).includes(filterSkill.value.toLowerCase())
    );

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
    <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2" v-if="currentBtn !== 'Notification'">
      <div >
        <h3 class="fw-bold text-dark mb-1">Student Placement Portal</h3>
        <p class="text-muted mb-0">Apply to matching placement drives and track your application status.</p>
      </div>
      <button class="btn btn-outline-primary px-4 py-2 rounded-3 fw-semibold" @click="triggerStudentExport">
        📥 Export History (CSV)
      </button>
    </div>

    <div v-if="props.currentBtn === 'Dashboard'" class="card border-0 shadow-sm rounded-4 mb-4 bg-white overflow-hidden">
      <div class="card-header bg-white border-0 p-3 pb-0">
        <ul class="nav nav-tabs border-0 gap-2">
          <li class="nav-item">
            <button 
              class="nav-link border-0 px-4 py-2 rounded-3 fw-semibold transition-all"
              :class="activeTab === 'drives' ? 'bg-primary text-white' : 'bg-light text-secondary'"
              @click="activeTab = 'drives'"
            >
              💼 Available Placement Drives ({{ props.drives?.length || 0 }})
            </button>
          </li>
          <li class="nav-item">
            <button 
              class="nav-link border-0 px-4 py-2 rounded-3 fw-semibold transition-all"
              :class="activeTab === 'hirings' ? 'bg-primary text-white' : 'bg-light text-secondary'"
              @click="activeTab = 'hirings'"
            >
              🎉 My Offer Letters ({{ hiredApplications?.length || 0 }})
            </button>
          </li>
        </ul>
      </div>
    </div>

    <!-- MAIN TEMPLATE -->
    <template v-if="props.currentBtn === 'Dashboard'">
      <div v-if="activeTab === 'drives'">
        <!-- filter Engine Card Controls -->
        <div class="card border-0 shadow-sm rounded-4 mb-4 bg-white p-3">
          <div class="row g-3 align-items-center">
            <div class="col-md-4">
              <div class="input-group">
                <span class="input-group-text bg-light border-0 text-secondary">🔍</span>
                <input v-model="searchQuery" type="text" class="form-control bg-light border-0 py-2" placeholder="Search position or skills...">
              </div>
            </div>
            
            <div class="col-sm-6 col-md-3">
              <select v-model="filterCompany" class="form-select bg-light border-0 py-2">
                <option value="">All Companies</option>
                <option v-for="company in uniqueCompanies" :key="company" :value="company">{{ company }}</option>
              </select>
            </div>
            
            <div class="col-sm-6 col-md-3">
              <select v-model="filterSkill" class="form-select bg-light border-0 py-2">
                <option value="">All Required Skills</option>
                <option v-for="skill in uniqueSkills" :key="skill" :value="skill">{{ skill }}</option>
              </select>
            </div>

            <div class="col-sm-12 col-md-2">
              <div class="form-check form-switch mb-0">
                <input v-model="filterCgpa" class="form-check-input" type="checkbox" id="eligibilityToggle">
                <label class="form-check-label small fw-semibold text-secondary" for="eligibilityToggle">Eligible Only</label>
              </div>
            </div>
          </div>
          
          <!-- filter -->
          <div v-if="searchQuery || filterCompany || filterSkill || filterCgpa" class="d-flex flex-wrap gap-2 mt-3 pt-3 border-top">
            <span class="text-muted small align-self-center">Active filters:</span>
            
            <span v-if="searchQuery" class="badge bg-secondary-subtle text-secondary border border-secondary-subtle d-flex align-items-center gap-1 py-1 px-3 rounded-pill">
              Query: "{{ searchQuery }}"
              <button @click="searchQuery = ''" class="btn-close" style="font-size: 0.5rem;" aria-label="Close"></button>
            </span>
            
            <span v-if="filterCompany" class="badge bg-secondary-subtle text-secondary border border-secondary-subtle d-flex align-items-center gap-1 py-1 px-3 rounded-pill">
              Company: {{ filterCompany }}
              <button @click="filterCompany = ''" class="btn-close" style="font-size: 0.5rem;" aria-label="Close"></button>
            </span>
            
            <span v-if="filterSkill" class="badge bg-secondary-subtle text-secondary border border-secondary-subtle d-flex align-items-center gap-1 py-1 px-3 rounded-pill">
              Skill: {{ filterSkill }}
              <button @click="filterSkill = ''" class="btn-close" style="font-size: 0.5rem;" aria-label="Close"></button>
            </span>

            <span v-if="filterCgpa" class="badge bg-secondary-subtle text-secondary border border-secondary-subtle d-flex align-items-center gap-1 py-1 px-3 rounded-pill">
              Eligible Only
              <button @click="filterCgpa = false" class="btn-close" style="font-size: 0.5rem;" aria-label="Close"></button>
            </span>
            
            <button @click="clearFilters" class="btn btn-link btn-sm p-0 text-decoration-none text-danger small ms-auto fw-semibold">Clear All</button>
          </div>
        </div>

        <!-- Drives Renders Loop -->
        <div class="row g-4">
          <div class="col-12" v-if="props.drives?.length === 0">
            <div class="card p-5 text-center border-0 shadow-sm rounded-4 bg-white text-muted">
              <div class="display-6 mb-2">💼</div>
              <p class="mb-0">No placement drives are open for applications right now.</p>
            </div>
          </div>

          <div class="col-12" v-else-if="filteredDrives.length === 0">
            <div class="card p-5 text-center border-0 shadow-sm rounded-4 bg-white text-muted">
              <div class="display-6 mb-2">🔍</div>
              <p class="mb-1 fw-semibold text-dark">No matching placement drives found.</p>
              <p class="mb-0 small">Try clearing or modifying your filter conditions.</p>
            </div>
          </div>
          
          <div v-else class="col-md-6 col-lg-4" v-for="d in filteredDrives" :key="d.id">
            <div class="card h-100 border-0 shadow-sm rounded-4 p-4 bg-white d-flex flex-column">
              <div class="d-flex justify-content-between align-items-start mb-2">
                <span class="badge bg-primary-subtle text-primary rounded-pill px-3 py-1 fw-semibold">{{ d.company }}</span>
                <span class="fw-bold text-success">${{ d.salary?.toLocaleString() }}/yr</span>
              </div>
              
              <h5 class="fw-bold text-dark mt-2 mb-1">{{ d.title }}</h5>
              
              <div class="d-flex align-items-center gap-2 mb-2">
                <div class="text-muted small">Min CGPA: <strong class="text-dark">{{ d.min_cgpa }}</strong></div>
                <span v-if="profileCgpa && parseFloat(profileCgpa) < parseFloat(d.min_cgpa)" class="badge bg-danger-subtle text-danger rounded-pill px-2 py-1 fw-semibold" style="font-size: 0.7rem;">Ineligible</span>
                <span v-else-if="profileCgpa" class="badge bg-success-subtle text-success rounded-pill px-2 py-1 fw-semibold" style="font-size: 0.7rem;">Eligible</span>
              </div>

              <div v-if="d.skills_required" class="d-flex flex-wrap gap-1 mb-3">
                <span v-for="skill in d.skills_required.split(',')" :key="skill" class="badge bg-secondary-subtle text-secondary rounded-pill px-2 py-1 fw-medium" style="font-size: 0.75rem;">
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
                  :disabled="d.applied || (profileCgpa && parseFloat(profileCgpa) < parseFloat(d.min_cgpa))"
                >
                  <span v-if="d.applied">✔ Applied</span>
                  <span v-else-if="profileCgpa && parseFloat(profileCgpa) < parseFloat(d.min_cgpa)">Locked (CGPA Requirement)</span>
                  <span v-else>Apply Now</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- PLACEMENT HISTORY -->
    <template v-else-if="props.currentBtn === 'History'">
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
                <th>Job / Drive</th>
                <th>Company</th>
                <th>Salary</th>
                <th>Date Applied</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <template v-for="app in props.applications" :key="app.id">
                <tr>
                  <td class="fw-bold text-dark border-0">{{ app.drive_title }}</td>
                  <td class="text-secondary border-0 fw-semibold">{{ app.company_name }}</td>
                  <td class="text-dark border-0">${{ app.salary?.toLocaleString() }}</td>
                  <td class="text-muted small border-0">{{ formatDate(app.date_applied) }}</td>
                  <td class="border-0">
                    <span class="badge px-3 py-2 rounded-pill fw-semibold" :class="{ 'bg-warning text-dark': app.status === 'Applied', 'bg-info text-white': app.status === 'Shortlisted', 'bg-success text-white': app.status === 'Selected', 'bg-danger text-white': app.status === 'Rejected' }">
                      {{ app.status }}
                    </span>
                  </td>
                </tr>

                <tr v-if="app.feedback || (app.status === 'Shortlisted' && app.interview_time) || (app.status === 'Selected' && app.offer_letter_link)" :key="'fb-' + app.id">
                  <td colspan="5" class="bg-light-subtle py-2 px-3 border-0">
                    <div class="d-flex flex-column gap-2 my-1">
                      <!-- placed Banner -->
                      <div v-if="app.status === 'Selected' && app.offer_letter_link" class="card border-0 bg-success-subtle p-3 rounded-3">
                        <div class="small fw-bold text-success text-uppercase tracking-wider mb-2" style="font-size: 0.75rem;">🎉 Congratulations! Offer Letter Issued!</div>
                        <div class="row align-items-center">
                          <div class="col-sm-6">
                            <span class="text-secondary small d-block">Offer from <strong>{{ app.company_name }}</strong></span>
                          </div>
                          <div class="col-sm-6 text-sm-end">
                            <a :href="app.offer_letter_link" target="_blank" class="btn btn-success btn-sm rounded-3 fw-semibold px-3 py-1">View Offer Letter</a>
                          </div>
                        </div>
                      </div>

                      <!-- interview card banner -->
                      <div v-if="app.status === 'Shortlisted' && app.interview_time" class="card border-0 bg-primary-subtle p-3 rounded-3">
                        <div class="small fw-bold text-primary text-uppercase tracking-wider mb-2" style="font-size: 0.75rem;">📅 Interview Invitation Details</div>
                        <div class="row align-items-center">
                          <div class="col-sm-6">
                            <span class="text-secondary small d-block">Scheduled Time Slot:</span>
                            <div class="fw-bold text-dark">{{ app.interview_time }}</div>
                          </div>
                          <div class="col-sm-6 text-sm-end">
                            <a v-if="app.interview_link" :href="app.interview_link" target="_blank" class="btn btn-primary btn-sm rounded-3 fw-semibold px-3 py-1">Join Meeting Link</a>
                            <span v-else class="text-muted small italic">Link will update shortly</span>
                          </div>
                        </div>
                      </div>

                      <div v-if="app.feedback" class="card border-0 bg-light p-3 rounded-3">
                        <div class="small fw-bold text-secondary mb-1">💬 Evaluation Feedback:</div>
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
    </template>

    <template v-if="props.currentBtn === 'Dashboard' && activeTab === 'hirings'">
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
            <div class="card border border-success-subtle rounded-4 p-4 bg-white shadow-sm position-relative overflow-hidden">
              <div class="position-absolute top-0 end-0 bg-success text-white px-3 py-1 fw-bold small" style="border-bottom-left-radius: 12px;">Hired</div>
              <div class="mb-3">
                <span class="badge bg-success-subtle text-success rounded-pill px-3 py-1 fw-semibold mb-2">{{ app.company_name }}</span>
                <h4 class="fw-bold text-dark mb-1">{{ app.drive_title }}</h4>
                <div class="text-muted small">Package Compensation: <strong class="text-dark">${{ app.salary?.toLocaleString() }}/yr</strong></div>
              </div>
              <div class="bg-light p-3 rounded-3 mb-3 border border-success-subtle d-flex justify-content-between align-items-center">
                <span class="text-muted small">Official Offer Letter:</span>
                <a v-if="app.offer_letter_link" :href="app.offer_letter_link" target="_blank" class="btn btn-success rounded-3 btn-sm fw-bold px-3">📄 View Document</a>
              </div>
              <div v-if="app.feedback" class="small text-secondary">
                <strong class="text-dark d-block mb-1">Recruiter Message:</strong>
                <span class="italic">"{{ app.feedback }}"</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
    <!-- PROFILE EDITOR WORKSPACE -->
    <template v-else-if="props.currentBtn === 'Profile'">
      <div class="row g-4">
        <div class="col-lg-4">
          <div class="card border-0 shadow-sm rounded-4 p-4 bg-white text-center">
            <div class="avatar-placeholder mx-auto mb-3 d-flex align-items-center justify-content-center bg-primary-subtle text-primary rounded-circle" style="width: 80px; height: 80px; font-size: 2.2rem;">🎓</div>
            <h4 class="fw-bold text-dark mb-1">{{ props.profile?.name || 'Your Name' }}</h4>
            <p class="text-muted small mb-3">Placement Candidate</p>
            <hr class="my-3 opacity-50">
            <div class="text-start">
              <div class="mb-3">
                <span class="text-muted small d-block">Department:</span>
                <span class="fw-semibold text-dark">{{ profileBranch || 'Unassigned' }}</span>
              </div>
              <div class="mb-3">
                <span class="text-muted small d-block">Active Track GPA:</span>
                <span class="fw-bold text-success" v-if="profileCgpa">{{ profileCgpa }} / 10.0</span>
                <span class="text-muted small italic" v-else>Not specified</span>
              </div>
              <div class="mb-3">
                <span class="text-muted small d-block">Resume Verification Attachment:</span>
                <a v-if="profileResume" :href="profileResume" target="_blank" class="text-decoration-underline fw-semibold text-primary small">📄 Open PDF Profile File</a>
                <span class="text-muted small italic" v-else>No resume attached</span>
              </div>
            </div>
          </div>
        </div>

        <div class="col-lg-8">
          <div class="card border-0 shadow-sm rounded-4 p-4 bg-white">
            <h5 class="fw-bold text-dark mb-4">Update Profile Information</h5>
            
            <form @submit.prevent="handleSaveProfile">
              <div class="row g-3">
                <div class="col-md-12">
                  <label class="form-label small fw-bold text-muted text-uppercase">Full Legal Name</label>
                  <input v-model="profileName" type="text" class="form-control rounded-3" required>
                </div>
                
                <div class="col-md-6">
                  <label class="form-label small fw-bold text-muted text-uppercase">Academic Branch Track</label>
                  <select v-model="profileBranch" class="form-select rounded-3">
                    <option value="">Select Department Branch</option>
                    <option value="Computer Science">Computer Science</option>
                    <option value="Information Technology">Information Technology</option>
                    <option value="Electronics">Electronics</option>
                    <option value="Electrical">Electrical</option>
                    <option value="Mechanical">Mechanical</option>
                    <option value="Civil">Civil</option>
                  </select>
                </div>
                
                <div class="col-md-6">
                  <label class="form-label small fw-bold text-muted text-uppercase">Cumulative Grade Tracker (CGPA)</label>
                  <input v-model="profileCgpa" type="number" step="0.01" min="0" max="10" class="form-control rounded-3">
                </div>

                <div class="col-12">
                  <label class="form-label small fw-bold text-muted text-uppercase">Verification Resume URL</label>
                  <input v-model="profileResume" type="url" class="form-control rounded-3" placeholder="https://drive.google.com/...">
                </div>

                <div class="col-12">
                  <label class="form-label small fw-bold text-muted text-uppercase">Educational Milestones History</label>
                  <textarea v-model="profileEducation" class="form-control rounded-3" rows="3"></textarea>
                </div>

                <div class="col-12">
                  <label class="form-label small fw-bold text-muted text-uppercase">Project & Internship Portfolios</label>
                  <textarea v-model="profileExperience" class="form-control rounded-3" rows="3"></textarea>
                </div>

                <div class="col-12">
                  <label class="form-label small fw-bold text-muted text-uppercase">Key Skills Stack (Comma Separated Strings)</label>
                  <textarea v-model="profileSkills" class="form-control rounded-3" rows="2" placeholder="e.g. Python, Java, SQL, Flask"></textarea>
                </div>
              </div>

              <div class="text-end mt-4">
                <button type="submit" class="btn btn-primary rounded-3 fw-semibold px-4 py-2">💾 Save Profile Changes</button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </template>
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