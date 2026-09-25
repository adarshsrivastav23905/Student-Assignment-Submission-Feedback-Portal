/**
 * Authentication Module
 * =====================
 * Manages JWT token storage, user session state, and auth UI.
 * 
 * Cloud Concept: Authentication answers "Who are you?"
 * The JWT token is stored in localStorage and sent with every API request.
 * In cloud deployment, this would integrate with Firebase Auth, AWS Cognito, etc.
 */

const Auth = {
    /**
     * Get stored JWT token.
     */
    getToken() {
        return localStorage.getItem('token');
    },

    /**
     * Get current user data from localStorage.
     */
    getUser() {
        const userData = localStorage.getItem('user');
        return userData ? JSON.parse(userData) : null;
    },

    /**
     * Check if user is authenticated.
     */
    isAuthenticated() {
        return !!this.getToken();
    },

    /**
     * Get current user's role.
     */
    getRole() {
        const user = this.getUser();
        return user ? user.role : null;
    },

    /**
     * Save authentication data after login/register.
     */
    saveAuth(token, user) {
        localStorage.setItem('token', token);
        localStorage.setItem('user', JSON.stringify(user));
    },

    /**
     * Clear authentication data (logout).
     */
    logout() {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        App.navigate('login');
        showToast('Logged out successfully', 'info');
    },

    /**
     * Handle login form submission.
     */
    async handleLogin(e) {
        e.preventDefault();
        const email = document.getElementById('loginEmail').value;
        const password = document.getElementById('loginPassword').value;
        const btn = document.getElementById('loginBtn');

        btn.disabled = true;
        btn.textContent = 'Signing in...';

        try {
            const data = await AuthAPI.login(email, password);
            Auth.saveAuth(data.token, data.user);
            showToast(`Welcome back, ${data.user.name}!`, 'success');

            // Navigate to role-specific dashboard
            if (data.user.role === 'teacher') {
                App.navigate('teacher-dashboard');
            } else {
                App.navigate('student-dashboard');
            }
        } catch (error) {
            showToast(error.error || 'Login failed', 'error');
        } finally {
            btn.disabled = false;
            btn.textContent = 'Sign In';
        }
    },

    /**
     * Handle registration form submission.
     */
    async handleRegister(e) {
        e.preventDefault();
        const name = document.getElementById('regName').value;
        const email = document.getElementById('regEmail').value;
        const password = document.getElementById('regPassword').value;
        const role = document.getElementById('regRole').value;
        const btn = document.getElementById('registerBtn');

        btn.disabled = true;
        btn.textContent = 'Creating account...';

        try {
            const data = await AuthAPI.register(name, email, password, role);
            Auth.saveAuth(data.token, data.user);
            showToast(`Account created! Welcome, ${data.user.name}!`, 'success');

            if (data.user.role === 'teacher') {
                App.navigate('teacher-dashboard');
            } else {
                App.navigate('student-dashboard');
            }
        } catch (error) {
            showToast(error.error || 'Registration failed', 'error');
        } finally {
            btn.disabled = false;
            btn.textContent = 'Create Account';
        }
    },
};
