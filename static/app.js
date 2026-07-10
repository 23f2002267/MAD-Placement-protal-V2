const { createApp } = Vue;

createApp({
    data() {
        return {
            user: JSON.parse(localStorage.getItem('user')) || null,
            role: localStorage.getItem('role') || '',
            authMode: 'login',
            auth: { email: '', password: '', role: 'student', name: '' },
            
            // Admin Data
            stats: { students: 0, companies: 0, drives: 0 },
            pendingCompanies: [],
            pendingDrives: [],

            // Company Data
            companyDrives: [],
            newDrive: { title: '', desc: '', cgpa: 7.0 },

            // Student Data
            allDrives: [],
            searchQuery: '',
            history: []
        }
    },
    methods: {
        async handleAuth() {

            console.log("AuthMode at submission:", this.authMode);
            // Determine endpoint based on authMode
            const endpoint = this.authMode === 'login' ? '/api/login' : '/api/register';
            
            const res = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(this.auth)
            });
            
            console.log("Response status:", res.status, res.statusText, res.ok, res.headers.get('Content-Type'));
            const data = await res.json();
            if (res.status === 200 || res.status === 201) {
                this.user = data;
                this.role = data.role;
                localStorage.setItem('user', JSON.stringify(data));
                localStorage.setItem('role', data.role);
                this.fetchDashboardData();
            } else if (res.ok === false) {
                if (res.status === 400) {
                    alert(data.message);
                    this.authMode = 'login'; 
                } else {
                    alert(data.message);
                }
            } else {
                alert(data.message);
                
            }
        },
        async fetchDashboardData() {
            if (this.role === 'admin') {
                const s = await fetch('/api/admin/stats');
                this.stats = await s.json();
                const c = await fetch('/api/admin/pending-companies');
                this.pendingCompanies = await c.json();
            } else if (this.role === 'student') {
                const d = await fetch('/api/student/drives');
                this.allDrives = await d.json();
            }
        },
        async approveCompany(id) {
            await fetch(`/api/admin/approve-company/${id}`, { method: 'POST' });
            this.fetchDashboardData();
        },
        async apply(driveId) {
            const res = await fetch('/api/student/apply', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: this.user.id, drive_id: driveId })
            });
            const data = await res.json();
            alert(data.message);
            this.fetchDashboardData();
        },
        async exportHistory() {
            const res = await fetch(`/api/student/export-csv/${this.user.id}`);
            const data = await res.json();
            alert("Celery Task Triggered: " + data.message);
        },
        logout() {
            this.user = null;
            localStorage.clear();
        }
    },
    // watch: {
    // authMode(newValue) {
    //     console.log("Auth Mode changed to:", newValue);
    // }
    // },
    mounted() {
        if (this.user) this.fetchDashboardData();
    }
}).mount('#app');