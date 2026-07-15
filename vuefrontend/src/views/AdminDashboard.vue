<script setup>
import { computed , ref } from 'vue';
import { Modal } from 'bootstrap';
import Card from '../components/Card.vue';
import AdminList from '../components/AdminList.vue';

const props = defineProps({
  currentBtn: { type: String, default: 'Dashboard' },
  stats: { type: Object, default: () => ({ students: 0, companies: 0, drives: 0, applications: 0 }) },
  pendingCompanies: { type: Array, default: () => [] },
  pendingDrives: { type: Array, default: () => [] },
  userSearch: { type: Array, default: () => [] },
  drives: { type: Array, default: () => [] },
  applications: { type: Array, default: () => [] }
});

function formatKey(key) {
  return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

const selectedDrive = ref(null);
function onViewDetails(drive) {
  selectedDrive.value = drive
  const modal = new Modal(document.getElementById('driveModal'))
  modal.show()
}
const cards = computed(() => [
  [
    { title: 'Students', color: '#1ecd6a', data: props.stats?.students ?? 0, link: '/students'},
    { title: 'Applications', color: '#46eebf', data: props.stats?.applications ?? 0 },
    { title: 'Blacklisted Students', color: '#bc5d40', data: props.stats?.blstudents ?? 0 }
  ],
  [
    { title: 'Companies', color: '#1d61cd', data: props.stats?.companies ?? 0, link: '/companies'},
    { title: 'Drives', color: '#70cd1e', data: props.stats?.drives ?? 0},
    { title: 'Blacklisted Drives', color: '#cd381e', data: props.stats?.bldrives ?? 0 }
  ]
]);

const emit = defineEmits(['approve-company', 'approve-drive','reject-company','reject-drive','select-view',
                          'view-details', 'blacklist-user','delete-user']);

function handleCardTap(card) {
  const target = card.title;
  if (target === 'Students' || target === 'Companies' || target === 'Drives' || target === 'Applications') {
    emit('select-view', target);
  }
}

const studentsList = computed(() => {
  if (!Array.isArray(props.userSearch)) return [];
  return props.userSearch.filter(u => u.role === 'Student');
});

const companiesList = computed(() => {
  if (!Array.isArray(props.userSearch)) return [];
  return props.userSearch.filter(u => u.role === 'Company');
});

const drivesList = computed(() => {
  return Array.isArray(props.drives) ? props.drives : [];
});

const applicationsList = computed(() => {
  return Array.isArray(props.applications) ? props.applications : [];
});

const pendingCompaniesList = computed(() => {
  return Array.isArray(props.pendingCompanies) ? props.pendingCompanies : [];
});

const pendingDrivesList = computed(() => {
  return Array.isArray(props.pendingDrives) ? props.pendingDrives : [];
});

// function onViewDetails(item) {
//   emit('view-details', item);
// }

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
            :link="card.link" 
            @click="handleCardTap(card)"
          />
        </div>
      </div>

      <div class="row mt-4 pt-4">
        <div class="col-md-6">
          <div class="card p-3">
            <h5>Pending Companies</h5>
            <ul class="list-group list-scroll">
              <li v-for="c in pendingCompaniesList" :key="c.id" class="list-group-item d-flex justify-content-between align-items-center">
                {{ c.name }}
                <div class="justify-content-between">
                  <button class="btn btn-sm btn-success me-2" @click="$emit('approve-company', c.id)">Approve</button>
                  <button class="btn btn-sm btn-danger" @click="$emit('reject-company', c.id)">Reject</button>
                </div>
              </li>
            </ul>
          </div>
        </div>
        <div class="col-md-6">
          <div class="card p-3">
            <h5>Pending Drives</h5>
            <ul class="list-group list-scroll">
              <li v-for="d in pendingDrivesList" :key="d.id" class="list-group-item d-flex justify-content-between align-items-center">
                {{ d.company }} | {{ d.title }}
                <div>
                  <button class="btn btn-sm btn-success me-2" @click="$emit('approve-drive', d.id)">Approve</button>
                  <button class="btn btn-sm btn-danger" @click="$emit('reject-drive', d.id)">Reject</button>
                </div>
              </li>
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
        :search-fields="['username', 'email', 'role']"
        search-placeholder="Search students..."
        empty-text="No students found."
        view-label="View Details"
        @view-details="onViewDetails"
      >
        <template #actions="{ item }">
          <button v-if="item.blacklist" class="btn btn-sm btn-success" @click="$emit('blacklist-user', item.id)">Approve</button>
          <button v-else class="btn btn-sm btn-danger" @click="$emit('blacklist-user', item.id)">Blacklist</button>
          <button class="btn btn-sm btn-danger" @click="$emit('delete-user', item.id)">Delete</button>
        </template>
      </AdminList>
    </template>
    
                    <!-- ADMIN-COMPANY PAGE -->

    <template v-else-if="props.currentBtn === 'Companies'">
      <AdminList
        :items="companiesList"
        title="Companies"
        item-key="id"
        :search-fields="['username', 'email', 'role']"
        search-placeholder="Search companies..."
        empty-text="No companies found."
        view-label="View Details"
        @view-details="onViewDetails"
      >
        <template #actions="{ item }">
          <button v-if="item.blacklist" class="btn btn-sm btn-success" @click="$emit('blacklist-user', item.id)">Approve</button>
          <button v-else class="btn btn-sm btn-danger" @click="$emit('blacklist-user', item.id)">Blacklist</button>
          <button class="btn btn-sm btn-danger" @click="$emit('delete-user', item.id)">Delete</button>
        </template>
      </AdminList>
    </template>
    
                    <!-- ADMIN-DRIVES PAGE -->

    <template v-else-if="props.currentBtn === 'Drives'">
      <AdminList
        :items="drivesList"
        title="Drives"
        item-key="id"
        :search-fields="['title', 'company', 'skills_required','status']"
        search-placeholder="Search drives..."
        empty-text="No drives found."
        view-label="View Details"
        @view-details="onViewDetails"
      >
        <template #actions="{ item }">
          <button class="btn btn-sm btn-success"
           @click="$emit('approve-drive', item.id)"
           :disabled="item.status === 'Approved' || item.status === 'Closed'">Approve</button>
          <button class="btn btn-sm btn-danger" 
           @click="$emit('reject-drive', item.id)"
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
      >
        <template #actions="{ item }">
          <button class="btn btn-sm btn-outline-secondary">Details</button>
        </template>
      </AdminList>
    </template>
    
                    <!-- ADMIN-ABOUT PAGE -->

    <template v-else-if="props.currentBtn === 'About'">
      <div class="card p-4 text-center">
        <h3>About Admin Portal</h3>
        <p>Use this portal to approve companies, drives, and manage campus placements.</p>
      </div>
    </template>

    <template v-else>
      <div class="text-center p-5 text-muted">
        <p>No view available for "{{ props.currentBtn }}".</p>
      </div>
    </template>
  </div>
  <div class="modal fade" id="driveModal" tabindex="-1">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <h5>Details</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body" v-if="selectedDrive">
        <div v-for="[key, value] in Object.entries(selectedDrive)" :key="key">
          <p><strong>{{ formatKey(key) }}:</strong> {{ value }}</p>
        </div>
      </div>
      <div class="modal-footer" v-if="selectedDrive">
        <button class="btn btn-success" @click="$emit('approve-drive', selectedDrive.id)" :disabled="selectedDrive.status==='Approved'">Approve</button>
        <button class="btn btn-danger" @click="$emit('reject-drive', selectedDrive.id)" :disabled="selectedDrive.status==='Rejected'">Reject</button>
      </div>
    </div>
  </div>
</div>

</template>

<style scoped>
.list-scroll {
  height: 200px;
  overflow-y: auto;
}
</style>