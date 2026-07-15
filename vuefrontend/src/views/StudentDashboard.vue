<script setup>
import { ref } from 'vue'

const props = defineProps({
  drives: { type: Array, default: () => [] },
  applications: { type: Array, default: () => [] }
});

const emit = defineEmits(['apply-drive']);

const activeTab = ref('drives');

function formatDate(dateStr) {
  if (!dateStr) return 'N/A';
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  });
}
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
        </ul>
      </div>
    </div>

    <!-- Tab Contents -->
    <div v-if="activeTab === 'drives'">
      <div class="row g-4">
        <!-- Available drives loop -->
        <div class="col-12" v-if="props.drives?.length === 0">
          <div class="card p-5 text-center border-0 shadow-sm rounded-4 bg-white text-muted">
            <div class="display-6 mb-2">💼</div>
            <p class="mb-0">No placement drives are currently approved and open for applications.</p>
          </div>
        </div>
        
        <div v-else class="col-md-6 col-lg-4" v-for="d in props.drives" :key="d.id">
          <div class="card h-100 border-0 shadow-sm rounded-4 p-4 bg-white d-flex flex-column">
            <div class="d-flex justify-content-between align-items-start mb-2">
              <span class="badge bg-primary-subtle text-primary rounded-pill px-3 py-1.5 fw-semibold">{{ d.company }}</span>
              <span class="fw-bold text-success">${{ d.salary?.toLocaleString() }}/yr</span>
            </div>
            
            <h5 class="fw-bold text-dark mt-2 mb-1">{{ d.title }}</h5>
            <div class="text-muted small mb-3">Min CGPA: <strong>{{ d.min_cgpa }}</strong></div>
            
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
                <!-- Feedback and Interview Sub-Row -->
                <tr v-if="app.feedback || (app.status === 'Shortlisted' && app.interview_time)" :key="'fb-' + app.id">
                  <td colspan="5" class="bg-light-subtle py-2 px-3 border-0">
                    <div class="d-flex flex-column gap-2 my-1">
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
