/**
 * API Service Module
 * ==================
 * Centralized HTTP client for communicating with the REST API backend.
 * 
 * Cloud Concept: This module talks to the REST API layer, which in turn
 * communicates with the cloud database and cloud object storage.
 * All requests include JWT tokens for authentication.
 */

const API_BASE = window.location.origin;

/**
 * Core fetch wrapper with authentication and error handling.
 */
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const token = localStorage.getItem('token');

    const headers = {
        ...options.headers,
    };

    // Add auth token if available
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    // Add JSON content type for non-FormData requests
    if (!(options.body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
    }

    try {
        const response = await fetch(url, {
            ...options,
            headers,
        });

        // Handle different response types
        const contentType = response.headers.get('content-type');

        if (contentType && contentType.includes('application/json')) {
            const data = await response.json();
            if (!response.ok) {
                throw { status: response.status, ...data };
            }
            return data;
        }

        // For file downloads, return the response blob
        if (!response.ok) {
            throw { status: response.status, error: 'Request failed' };
        }
        return response;

    } catch (error) {
        // Handle network errors
        if (error instanceof TypeError && error.message.includes('fetch')) {
            throw { error: 'Network error. Please check your connection.', status: 0 };
        }
        throw error;
    }
}


// =============================================================================
// AUTH API
// =============================================================================

const AuthAPI = {
    /**
     * Register a new user.
     * POST /api/auth/register
     */
    async register(name, email, password, role = 'student') {
        return apiRequest('/api/auth/register', {
            method: 'POST',
            body: JSON.stringify({ name, email, password, role }),
        });
    },

    /**
     * Login and receive JWT token.
     * POST /api/auth/login
     */
    async login(email, password) {
        return apiRequest('/api/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password }),
        });
    },

    /**
     * Get current user's profile.
     * GET /api/auth/profile
     */
    async getProfile() {
        return apiRequest('/api/auth/profile');
    },
};


// =============================================================================
// ASSIGNMENTS API
// =============================================================================

const AssignmentsAPI = {
    /**
     * List all assignments for the current user.
     * GET /api/assignments
     */
    async list() {
        return apiRequest('/api/assignments');
    },

    /**
     * Get a single assignment by ID.
     * GET /api/assignments/:id
     */
    async get(id) {
        return apiRequest(`/api/assignments/${id}`);
    },

    /**
     * Create a new assignment (teacher only).
     * POST /api/assignments
     */
    async create(data) {
        return apiRequest('/api/assignments', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },

    /**
     * Update an assignment (teacher only).
     * PUT /api/assignments/:id
     */
    async update(id, data) {
        return apiRequest(`/api/assignments/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    },

    /**
     * Delete an assignment (teacher only).
     * DELETE /api/assignments/:id
     */
    async delete(id) {
        return apiRequest(`/api/assignments/${id}`, {
            method: 'DELETE',
        });
    },
};


// =============================================================================
// COURSES API
// =============================================================================

const CoursesAPI = {
    /**
     * List courses.
     * GET /api/courses
     */
    async list() {
        return apiRequest('/api/courses');
    },

    /**
     * Create a new course (teacher only).
     * POST /api/courses
     */
    async create(data) {
        return apiRequest('/api/courses', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },

    /**
     * Enroll in a course.
     * POST /api/courses/:id/enroll
     */
    async enroll(courseId, studentId = null) {
        const body = studentId ? { student_id: studentId } : {};
        return apiRequest(`/api/courses/${courseId}/enroll`, {
            method: 'POST',
            body: JSON.stringify(body),
        });
    },
};


// =============================================================================
// SUBMISSIONS API
// =============================================================================

const SubmissionsAPI = {
    /**
     * Submit an assignment file.
     * POST /api/assignments/:id/submit
     * Sends as multipart/form-data (for file upload to cloud storage).
     */
    async submit(assignmentId, file) {
        const formData = new FormData();
        formData.append('file', file);
        return apiRequest(`/api/assignments/${assignmentId}/submit`, {
            method: 'POST',
            body: formData,
        });
    },

    /**
     * Get my submissions (student only).
     * GET /api/submissions/me
     */
    async getMySubmissions() {
        return apiRequest('/api/submissions/me');
    },

    /**
     * Get all submissions for an assignment (teacher only).
     * GET /api/assignments/:id/submissions
     */
    async getForAssignment(assignmentId) {
        return apiRequest(`/api/assignments/${assignmentId}/submissions`);
    },

    /**
     * Get a single submission.
     * GET /api/submissions/:id
     */
    async get(id) {
        return apiRequest(`/api/submissions/${id}`);
    },

    /**
     * Download a submission file.
     * GET /api/submissions/:id/download
     * Returns a blob for file download.
     */
    async download(id, fileName) {
        const response = await apiRequest(`/api/submissions/${id}/download`);
        const blob = await response.blob();
        // Trigger browser download
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = fileName || 'submission';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    },

    /**
     * Grade a submission (teacher only).
     * POST /api/submissions/:id/grade
     */
    async grade(id, marks, feedback) {
        return apiRequest(`/api/submissions/${id}/grade`, {
            method: 'POST',
            body: JSON.stringify({ marks: parseInt(marks), feedback }),
        });
    },

    /**
     * Get feedback for a submission.
     * GET /api/submissions/:id/feedback
     */
    async getFeedback(id) {
        return apiRequest(`/api/submissions/${id}/feedback`);
    },
};


// =============================================================================
// DASHBOARD API
// =============================================================================

const DashboardAPI = {
    /**
     * Get student dashboard data.
     * GET /api/dashboard/student
     */
    async getStudentDashboard() {
        return apiRequest('/api/dashboard/student');
    },

    /**
     * Get teacher dashboard data.
     * GET /api/dashboard/teacher
     */
    async getTeacherDashboard() {
        return apiRequest('/api/dashboard/teacher');
    },
};
