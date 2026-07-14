<script setup>
import { reactive } from 'vue'
const props = defineProps({
  user: { type: Object, default: () => ({ user_id: 0, username: 0, email: 0, password: 0 }) },
  drives: { type: Array, default: () => [] }
});

const companyDrives = [];
const newDrive = reactive({ company_id: props.user?.id, title: '', desc: '', salary: 0,
      skills_required: '', min_cgpa: 0, start_date: '', deadline: '', status: 'Pending'});

const emit = defineEmits(['save-drive']);

</script>

<template>
  <div>
    <div class="d-flex justify-content-between mb-4">
      <h3>Welcome, {{ props.user?.email }}</h3>
      <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#driveModal">New Drive</button>
    </div>
    <div class="card p-3">
      <h5>Job Postings</h5>
      <table class="table">
        <thead>
          <tr>
            <th>Title</th>
            <th>Status</th>
            <th>Applicants</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="drive in drives" :key="drive.id">
            <td>{{ drive?.title }}</td>
            <td><span class="badge bg-secondary">{{ drive?.status }}</span></td>
            <td>{{ drive?.applicants }}</td>
          </tr>
        </tbody>
      </table>      
    </div>
  </div>
        <div class="modal fade" id="driveModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header"><h5>Create Drive</h5></div>
                <div class="modal-body">
                    <input v-model="newDrive.title" class="form-control mb-2" placeholder="Title">
                    <input v-model="newDrive.desc" class="form-control mb-2" placeholder="Description">
                    <input v-model="newDrive.salary" type="number" class="form-control mb-2" placeholder="Salary">
                    <input v-model="newDrive.skills_required" class="form-control mb-2" placeholder="Skills Required">
                    <input v-model="newDrive.min_cgpa" type="number" class="form-control mb-2" placeholder="Min CGPA">
                    <input v-model="newDrive.start_date" type="date" class="form-control mb-2" placeholder="Start Date">
                    <input v-model="newDrive.deadline" type="date" class="form-control mb-2" placeholder="Deadline">
                </div>
                <div class="modal-footer">
                    <button class="btn btn-success" @click="$emit('save-drive', newDrive)" data-bs-dismiss="modal">Create</button>
                </div>
            </div>
        </div>
    </div>
  
</template>