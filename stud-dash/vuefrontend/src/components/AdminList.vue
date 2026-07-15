<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  items: { type: Array, default: () => [] },
  title: { type: String, default: 'Items' },
  itemKey: { type: String, default: 'id' },
  searchFields: { type: Array, default: () => ['name', 'title', 'email', 'company'] },
  searchPlaceholder: { type: String, default: 'Search...' },
  emptyText: { type: String, default: 'No records found.' },
  viewLabel: { type: String, default: 'View Details' }
})

const emit = defineEmits(['view-details'])
const search = ref('')

const normalizedSearch = computed(() => search.value.trim().toLowerCase())
const filteredItems = computed(() => {
  if (!normalizedSearch.value) return props.items

  return props.items.filter(item =>
    props.searchFields.some(field => {
      const value = item[field]
      return value != null && String(value).toLowerCase().includes(normalizedSearch.value)
    })
  )
})

const itemTitle = item => item.name || item.title || item.company || item.username || item.email || item.drive_id || 'Unknown'
const itemSubtitle = item => {
  if (item.title && item.email) return `${item.title} · ${item.email}`
  if (item.company && item.title) return `${item.company} · ${item.title}`
  if (item.email) return item.email
  if (item.role) return item.role
  if (item.date_applied) return item.date_applied
  return ''
}

function onViewDetails(item) {
  emit('view-details', item)
}
</script>

<template>
  <div class="admin-list">
    <div class="d-flex flex-column flex-md-row justify-content-between align-items-start align-items-md-center mb-4 gap-3">
      <div>
        <h4 class="mb-1">{{ title }}</h4>
        <p class="text-muted mb-0">{{ filteredItems.length }} record{{ filteredItems.length === 1 ? '' : 's' }}</p>
      </div>
      <div class="input-group w-100 w-md-50">
        <input
          v-model="search"
          class="form-control"
          type="search"
          :placeholder="searchPlaceholder"
          aria-label="Search"
        />
        <button class="btn btn-outline-secondary" type="button" @click="search = ''">Clear</button>
      </div>
    </div>

    <div v-if="filteredItems.length" class="list-group admin-list-group">
      <div
        v-for="item in filteredItems"
        :key="item[props.itemKey]"
        class="list-group-item d-flex flex-column flex-md-row justify-content-between align-items-start align-items-md-center gap-3"
      >
        <div class="flex-grow-1" style="cursor:pointer" @click="onViewDetails(item)">
          <strong class="d-block">{{ itemTitle(item) }}</strong>
          <span class="text-muted small">{{ itemSubtitle(item) }}</span>
        </div>
        <div class="d-flex flex-wrap gap-2">
          <button class="btn btn-sm btn-outline-secondary" @click="onViewDetails(item)">{{ viewLabel }}</button>
          <slot name="actions" :item="item" />
        </div>
      </div>
    </div>

    <div v-else class="text-center text-muted py-4 border rounded">
      {{ emptyText }}
    </div>
  </div>
  
</template>

<style scoped>
.admin-list-group {
  border: 1px solid var(--bs-border-color, #dee2e6);
  border-radius: 0.5rem;
}
.list-scroll {
  height: 200px;
  overflow-y: auto;
}
</style>
