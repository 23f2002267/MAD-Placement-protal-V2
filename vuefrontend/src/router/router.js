import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/AdminDashboard.vue'
import Students from '../views/StudentDashboard.vue'
import Companies from '../views/CompanyDashboard.vue'

const routes = [
  { path: '/dashboard', component: Dashboard },
  { path: '/students', component: Students },
  { path: '/companies', component: Companies }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router