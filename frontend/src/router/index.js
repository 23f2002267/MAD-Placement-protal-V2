import { createRouter, createWebHistory } from 'vue-router'
import AuthForm from '../components/AuthForm.vue'
import AdminDashboard from '../views/AdminDashboard.vue'
import StudentDashboard from '../views/StudentDashboard.vue'
import CompanyDashboard from '../views/CompanyDashboard.vue'

const routes = [
  { 
    path: '/', 
    name: 'Login',
    component: AuthForm,
    beforeEnter: (to, from, next) => {
      const user = JSON.parse(localStorage.getItem('user'))
      const role = localStorage.getItem('role')
      if (user && role) {
        return next({ name: role + 'Dashboard' })
      }
      next()
    }
  },
  { 
    path: '/admin', 
    name: 'AdminDashboard',
    component: AdminDashboard, 
    meta: { requiresAuth: true, role: 'Admin' } 
  },
  { 
    path: '/student', 
    name: 'StudentDashboard',
    component: StudentDashboard, 
    meta: { requiresAuth: true, role: 'Student' } 
  },
  { 
    path: '/company', 
    name: 'CompanyDashboard',
    component: CompanyDashboard, 
    meta: { requiresAuth: true, role: 'Company' } 
  },
  //redirection route
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Global Route Guard
router.beforeEach((to, from, next) => {
  const loggedInUser = JSON.parse(localStorage.getItem('user'))
  const userRole = localStorage.getItem('role')
  const isBlacklisted = localStorage.getItem('blacklist') === 'true'

  // block blscklisted traffic from progreasing
  if (isBlacklisted && to.path !== '/') {
    alert('Account restrained. Please contact portal administration.')
    localStorage.clear()
    return next({ name: 'Login' })
  }

  // requires authentication validation
  if (to.matched.some(record => record.meta.requiresAuth)) {
    if (!loggedInUser) {
      // redirect
      return next({ name: 'Login' })
    }

    // verify
    if (to.meta.role && to.meta.role !== userRole) {
      alert('Access Denied: Unauthorized role space access.')
      return next({ name: userRole + 'Dashboard' })
    }
  }
  next()
})

export default router