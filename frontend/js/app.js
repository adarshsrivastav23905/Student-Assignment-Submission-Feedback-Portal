const App = {
    state: {
        assignments: [],
        courses: [],
        dashboard: null,
        submissions: [],
        currentAssignment: null,
        currentSubmission: null,
        currentUser: Auth.getUser(),
    },

    init() {
        this.bindGlobalEvents();
        this.loadRoute();
    },

    bindGlobalEvents() {
        document.addEventListener('click', async (event) => {
            const route = event.target.closest('[data-route]');
            const action = event.target.closest('[data-action]');

            if (route) {
                this.navigate(route.dataset.route);
                return;
            }

            if (action) {
                const actionName = action.dataset.action;
                const id = action.dataset.id;

                if (actionName === 'back-to-dashboard') {
                    this.navigate(Auth.getRole() === 'teacher' ? 'teacher-dashboard' : 'student-dashboard');
                    return;
                }

                if (actionName === 'download-submission') {
                    await this.downloadSubmission(id);
                    return;
                }

                if (actionName === 'view-feedback') {
                    await this.viewFeedback(id);
                    return;
                }

                if (actionName === 'teacher-view-assignment') {
                    await this.openAssignment(id);
                    return;
                }

                if (actionName === 'delete-assignment') {
                    await this.deleteAssignment(id);
                    return;
                }

                if (actionName === 'grade-submission') {
                    await this.gradeSubmissionPrompt(id);
                    return;
                }

                if (actionName === 'view-assignment') {
                    await this.openAssignment(id);
                    return;
                }

                if (actionName === 'enroll-course') {
                    await this.enrollInCourse(id);
                    return;
                }

                if (actionName === 'focus-assignment-form') {
                    document.getElementById('assignmentForm')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    document.getElementById('assignmentTitle')?.focus({ preventScroll: true });
                    return;
                }
            }

            if (event.target.id === 'logoutBtn') {
                this.logout();
            }
        });

        document.addEventListener('submit', async (event) => {
            if (event.target.id === 'loginForm') {
                event.preventDefault();
                await Auth.handleLogin(event);
            }

            if (event.target.id === 'registerForm') {
                event.preventDefault();
                await Auth.handleRegister(event);
            }

            if (event.target.id === 'assignmentForm') {
                event.preventDefault();
                await this.createAssignment(event);
            }

            if (event.target.id === 'courseForm') {
                event.preventDefault();
                await this.createCourse(event);
            }
        });

        document.addEventListener('change', async (event) => {
            const input = event.target;
            if (input.classList.contains('file-input')) {
                const assignmentId = input.dataset.assignmentId;
                const file = input.files[0];
                if (file) {
                    await this.uploadSubmission(assignmentId, file);
                    input.value = '';
                }
            }
        });

        window.addEventListener('hashchange', () => this.loadRoute());
    },

    navRouteFromRole() {
        const user = Auth.getUser();
        if (!user) return 'login';
        return user.role === 'teacher' ? 'teacher-dashboard' : 'student-dashboard';
    },

    navigate(route) {
        window.location.hash = route || 'login';
    },

    async loadRoute() {
        const route = window.location.hash.replace('#', '') || (Auth.isAuthenticated() ? this.navRouteFromRole() : 'login');
        renderNavbar();

        const app = document.getElementById('app');
        if (!app) return;

        if (route === 'login') {
            app.innerHTML = renderAuthPage('login');
            return;
        }

        if (route === 'register') {
            app.innerHTML = renderAuthPage('register');
            return;
        }

        if (!Auth.isAuthenticated()) {
            this.navigate('login');
            return;
        }

        if (route === 'courses') {
            await this.loadCoursesPage();
            return;
        }

        if (route === 'assignments') {
            await this.loadAssignmentsPage();
            return;
        }

        app.innerHTML = renderLoading('Loading dashboard...');
        if (route === 'teacher-dashboard' || Auth.getRole() === 'teacher') {
            await this.loadTeacherDashboard();
            return;
        }

        await this.loadStudentDashboard();
    },

    async loadStudentDashboard() {
        try {
            const [dashboardData, assignmentData, submissionData, courseData] = await Promise.all([
                DashboardAPI.getStudentDashboard(),
                AssignmentsAPI.list(),
                SubmissionsAPI.getMySubmissions(),
                CoursesAPI.list(),
            ]);

            this.state.dashboard = dashboardData.dashboard;
            this.state.assignments = assignmentData.assignments || [];
            this.state.submissions = submissionData.submissions || [];
            this.state.courses = courseData.courses || [];

            const app = document.getElementById('app');
            app.innerHTML = renderStudentDashboard({
                dashboard: dashboardData.dashboard,
                assignments: this.state.assignments,
                submissions: this.state.submissions,
                courses: this.state.courses,
            });
        } catch (error) {
            showToast(error.error || 'Unable to load dashboard', 'error');
        }
    },

    async loadTeacherDashboard() {
        try {
            const [dashboardData, assignmentData, courseData] = await Promise.all([
                DashboardAPI.getTeacherDashboard(),
                AssignmentsAPI.list(),
                CoursesAPI.list(),
            ]);

            this.state.dashboard = dashboardData.dashboard;
            this.state.assignments = assignmentData.assignments || [];
            this.state.courses = courseData.courses || [];

            const app = document.getElementById('app');
            app.innerHTML = renderTeacherDashboard(dashboardData, this.state.assignments, this.state.courses);
        } catch (error) {
            showToast(error.error || 'Unable to load teacher dashboard', 'error');
        }
    },

    async loadAssignmentsPage() {
        try {
            const response = await AssignmentsAPI.list();
            const app = document.getElementById('app');
            app.innerHTML = renderAssignmentsPage(response.assignments || []);
        } catch (error) {
            showToast(error.error || 'Unable to load assignments', 'error');
        }
    },

    async loadCoursesPage() {
        try {
            const response = await CoursesAPI.list();
            const app = document.getElementById('app');
            app.innerHTML = renderCoursesPage({
                courses: response.courses || [],
                isTeacher: Auth.getRole() === 'teacher',
            });
        } catch (error) {
            showToast(error.error || 'Unable to load courses', 'error');
        }
    },

    async createCourse(event) {
        const form = new FormData(event.target);
        const payload = {
            course_name: form.get('course_name'),
            course_code: form.get('course_code'),
            description: form.get('description') || '',
        };

        try {
            const response = await CoursesAPI.create(payload);
            showToast(response.message || 'Course created', 'success');
            await this.loadCoursesPage();
        } catch (error) {
            showToast(error.error || 'Failed to create course', 'error');
        }
    },

    async enrollInCourse(courseId) {
        try {
            const response = await CoursesAPI.enroll(courseId);
            showToast(response.message || 'Enrolled successfully', 'success');
            await this.loadCoursesPage();
        } catch (error) {
            showToast(error.error || 'Unable to enroll in course', 'error');
        }
    },

    async createAssignment(event) {
        const form = new FormData(event.target);
        const payload = {
            course_id: Number(form.get('course_id')),
            title: form.get('title'),
            description: form.get('description') || '',
            deadline: new Date(form.get('deadline')).toISOString(),
            max_marks: Number(form.get('max_marks')),
            allowed_extensions: form.get('allowed_extensions'),
            max_file_size_mb: Number(form.get('max_file_size_mb')),
            allow_late_submission: true,
            allow_resubmission: true,
        };

        try {
            const response = await AssignmentsAPI.create(payload);
            showToast(response.message || 'Assignment created', 'success');
            this.loadTeacherDashboard();
        } catch (error) {
            showToast(error.error || 'Failed to create assignment', 'error');
        }
    },

    async uploadSubmission(assignmentId, file) {
        try {
            const response = await SubmissionsAPI.submit(assignmentId, file);
            showToast(response.message || 'Submission successful', 'success');
            await this.loadStudentDashboard();
        } catch (error) {
            showToast(error.error || 'Upload failed', 'error');
        }
    },

    async openAssignment(assignmentId) {
        try {
            const response = await AssignmentsAPI.get(assignmentId);
            const assignment = response.assignment;
            const app = document.getElementById('app');
            app.innerHTML = renderAssignmentDetail(assignment);
        } catch (error) {
            showToast(error.error || 'Unable to load assignment', 'error');
        }
    },

    async viewFeedback(submissionId) {
        try {
            const submissionRes = await SubmissionsAPI.get(submissionId);
            const feedbackRes = await SubmissionsAPI.getFeedback(submissionId);
            const app = document.getElementById('app');
            app.innerHTML = renderSubmissionFeedback(submissionRes.submission, feedbackRes);
        } catch (error) {
            showToast(error.error || 'Unable to load feedback', 'error');
        }
    },

    async downloadSubmission(submissionId) {
        try {
            const submissionRes = await SubmissionsAPI.get(submissionId);
            const fileName = submissionRes.submission?.file_name || 'submission';
            await SubmissionsAPI.download(submissionId, fileName);
            showToast('Download started', 'success');
        } catch (error) {
            showToast(error.error || 'Download failed', 'error');
        }
    },

    async deleteAssignment(id) {
        try {
            const response = await AssignmentsAPI.delete(id);
            showToast(response.message || 'Assignment deleted', 'success');
            await this.loadTeacherDashboard();
        } catch (error) {
            showToast(error.error || 'Delete failed', 'error');
        }
    },

    async gradeSubmissionPrompt(submissionId) {
        const marks = window.prompt('Enter marks for this submission:', '0');
        if (marks === null) return;

        const feedback = window.prompt('Enter feedback for the student:', 'Good effort.');
        if (feedback === null) return;

        try {
            const response = await SubmissionsAPI.grade(submissionId, marks, feedback);
            showToast(response.message || 'Submission graded', 'success');
            await this.loadTeacherDashboard();
        } catch (error) {
            showToast(error.error || 'Grading failed', 'error');
        }
    },

    logout() {
        Auth.logout();
        this.navigate('login');
    },
};

window.addEventListener('DOMContentLoaded', () => {
    App.init();
});
