function renderNavbar() {
    const navLinks = document.getElementById('navLinks');
    const user = Auth.getUser();
    if (!navLinks) return;

    if (!user) {
        navLinks.innerHTML = `
            <button class="nav-link active" data-route="login">Login</button>
            <button class="nav-link" data-route="register">Register</button>
        `;
        return;
    }

    const role = user.role || 'student';
    const routes = role === 'teacher'
        ? ['teacher-dashboard', 'courses', 'assignments']
        : ['student-dashboard', 'courses', 'assignments'];

    const links = routes.map(route => {
        const label = route === 'student-dashboard' ? 'Dashboard' : route === 'teacher-dashboard' ? 'Dashboard' : route === 'courses' ? 'Courses' : 'Assignments';
        return `<button class="nav-link" data-route="${route}">${label}</button>`;
    }).join('');

    navLinks.innerHTML = `
        <div class="nav-user">
            <span>${user.name}</span>
            <span class="role-badge ${role}">${role}</span>
        </div>
        ${links}
        <button class="btn-logout" id="logoutBtn">Logout</button>
    `;
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('show');
    }, 10);

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function renderLoading(message = 'Loading Cloud Portal...') {
    return `
        <div class="loading-spinner">
            <div class="spinner"></div>
            <p>${message}</p>
        </div>
    `;
}

function renderAuthPage(mode = 'login') {
    const isLogin = mode === 'login';
    return `
        <div class="auth-container">
            <div class="auth-card">
                <div class="auth-header">
                    <span class="icon">☁️</span>
                    <h1>${isLogin ? 'Welcome Back' : 'Create Your Account'}</h1>
                    <p>${isLogin ? 'Sign in to continue to the portal.' : 'Register as a student or teacher to begin.'}</p>
                </div>

                <form id="${isLogin ? 'loginForm' : 'registerForm'}">
                    ${!isLogin ? `
                        <div class="form-group">
                            <label for="regName">Full Name</label>
                            <input class="form-input" id="regName" name="name" type="text" placeholder="Enter full name" required>
                        </div>
                    ` : ''}

                    <div class="form-group">
                        <label for="${isLogin ? 'loginEmail' : 'regEmail'}">Email</label>
                        <input class="form-input" id="${isLogin ? 'loginEmail' : 'regEmail'}" name="email" type="email" placeholder="you@example.com" required>
                    </div>

                    <div class="form-group">
                        <label for="${isLogin ? 'loginPassword' : 'regPassword'}">Password</label>
                        <input class="form-input" id="${isLogin ? 'loginPassword' : 'regPassword'}" name="password" type="password" placeholder="Enter password" required>
                    </div>

                    ${!isLogin ? `
                        <div class="form-group">
                            <label for="regRole">Role</label>
                            <select class="form-input" id="regRole" name="role">
                                <option value="student">Student</option>
                                <option value="teacher">Teacher</option>
                            </select>
                        </div>
                    ` : ''}

                    <button class="primary-btn" type="submit" id="${isLogin ? 'loginBtn' : 'registerBtn'}">
                        ${isLogin ? 'Sign In' : 'Create Account'}
                    </button>
                </form>

                <div class="auth-switch">
                    <span>${isLogin ? 'New here?' : 'Already have an account?'}</span>
                    <button type="button" class="link-btn" data-route="${isLogin ? 'register' : 'login'}">
                        ${isLogin ? 'Create account' : 'Login'}
                    </button>
                </div>

                <div class="demo-credentials">
                    <p><strong>Demo credentials</strong></p>
                    <p>Teacher: teacher@example.com / teacher123</p>
                    <p>Student: student@example.com / student123</p>
                </div>
            </div>
        </div>
    `;
}

function renderStudentDashboard(data) {
    const stats = data.dashboard?.stats || {};
    const assignments = data.assignments || [];
    const submissions = data.submissions || [];
    const courses = data.courses || [];

    const upcoming = (data.dashboard?.upcoming_deadlines || []).map(item => `
        <div class="mini-card">
            <div>
                <strong>${item.title}</strong>
                <small>${item.course_name}</small>
            </div>
            <span>Deadline: ${new Date(item.deadline).toLocaleDateString()}</span>
        </div>
    `).join('') || '<p class="empty-state">No upcoming deadlines.</p>';

    const feedback = (data.dashboard?.recent_feedback || []).map(item => `
        <div class="mini-card feedback-card">
            <div>
                <strong>${item.assignment_title}</strong>
                <small>${item.marks}/${item.max_marks}</small>
            </div>
            <span>${item.feedback || 'No feedback yet.'}</span>
        </div>
    `).join('') || '<p class="empty-state">No graded feedback yet.</p>';

    const courseTiles = courses.map(course => `
        <div class="mini-card">
            <div>
                <strong>${course.course_name}</strong>
                <small>${course.teacher_name || 'Teacher'} · ${course.course_code}</small>
            </div>
            <span class="status-badge ${course.enrolled ? 'submitted' : 'not-submitted'}">${course.enrolled ? 'Enrolled' : 'Open'}</span>
        </div>
    `).join('') || '<p class="empty-state">No courses available yet.</p>';

    const assignmentTiles = assignments.map(a => {
        const status = a.submission_status || 'NOT_SUBMITTED';
        const statusClass = status.toLowerCase();
        const due = new Date(a.deadline).toLocaleString();
        return `
            <article class="assignment-card">
                <div class="card-top-row">
                    <div>
                        <h3>${a.title}</h3>
                        <small>${a.course_name}</small>
                    </div>
                    <span class="status-badge ${statusClass}">${status}</span>
                </div>
                <p>${a.description || 'No description provided.'}</p>
                <div class="meta-row">
                    <span>Due: ${due}</span>
                    <span>Max Marks: ${a.max_marks}</span>
                </div>
                <div class="action-row">
                    <button class="secondary-btn" data-action="view-assignment" data-id="${a.id}">View</button>
                    <label class="upload-inline">
                        <input type="file" data-assignment-id="${a.id}" class="file-input" />
                        <span>Upload</span>
                    </label>
                </div>
            </article>
        `;
    }).join('') || '<p class="empty-state">No assignments available yet.</p>';

    const submissionList = submissions.map(s => `
        <div class="mini-card submission-row">
            <div>
                <strong>${s.assignment_title || 'Assignment'}</strong>
                <small>${s.status}</small>
            </div>
            <div class="submission-actions">
                <button class="secondary-btn" data-action="view-feedback" data-id="${s.id}">Feedback</button>
                <button class="secondary-btn" data-action="download-submission" data-id="${s.id}">Download</button>
            </div>
        </div>
    `).join('') || '<p class="empty-state">No submissions yet.</p>';

    return `
        <div class="dashboard-shell">
            <section class="hero-card">
                <div>
                    <p class="eyebrow">Student Portal</p>
                    <h1>${data.dashboard?.welcome || 'Welcome'}</h1>
                    <p>Track assignments, deadlines, teacher-led courses, and submitted work in one place.</p>
                </div>
            </section>

            <section class="stats-grid">
                <div class="stat-card purple"><span class="stat-label">Assignments</span><strong class="stat-value">${stats.total_assignments ?? 0}</strong></div>
                <div class="stat-card blue"><span class="stat-label">Pending</span><strong class="stat-value">${stats.pending ?? 0}</strong></div>
                <div class="stat-card green"><span class="stat-label">Submitted</span><strong class="stat-value">${stats.submitted ?? 0}</strong></div>
                <div class="stat-card yellow"><span class="stat-label">Late</span><strong class="stat-value">${stats.late ?? 0}</strong></div>
                <div class="stat-card cyan"><span class="stat-label">Graded</span><strong class="stat-value">${stats.graded ?? 0}</strong></div>
            </section>

            <section class="content-grid two-col">
                <div class="panel">
                    <div class="panel-header">
                        <h2>My Courses</h2>
                    </div>
                    <div class="stack-list">${courseTiles}</div>
                </div>
                <div class="panel">
                    <div class="panel-header">
                        <h2>Upcoming Deadlines</h2>
                    </div>
                    <div class="stack-list">${upcoming}</div>
                </div>
            </section>

            <section class="content-grid two-col">
                <div class="panel">
                    <div class="panel-header">
                        <h2>Assignments</h2>
                    </div>
                    <div class="assignment-list">${assignmentTiles}</div>
                </div>
                <div class="panel">
                    <div class="panel-header">
                        <h2>Teacher Feedback</h2>
                    </div>
                    <div class="stack-list">${feedback}</div>
                </div>
            </section>

            <section class="content-grid two-col">
                <div class="panel">
                    <div class="panel-header">
                        <h2>My Submissions</h2>
                    </div>
                    <div class="stack-list">${submissionList}</div>
                </div>
                <div class="panel">
                    <div class="panel-header">
                        <h2>Course Timeline</h2>
                    </div>
                    <div class="stack-list">${courseTiles}</div>
                </div>
            </section>
        </div>
    `;
}

function renderTeacherDashboard(data, assignments = [], courses = []) {
    const stats = data.dashboard?.stats || {};

    const assignmentRows = assignments.map(a => `
        <div class="mini-card assignment-row">
            <div>
                <strong>${a.title}</strong>
                <small>${a.course_name}</small>
            </div>
            <div class="submission-actions">
                <button class="secondary-btn" data-action="teacher-view-assignment" data-id="${a.id}">View</button>
                <button class="secondary-btn danger" data-action="delete-assignment" data-id="${a.id}">Delete</button>
            </div>
        </div>
    `).join('') || '<p class="empty-state">No assignments created yet.</p>';

    const recentUploads = (data.dashboard?.recent_uploads || []).map(item => `
        <div class="mini-card">
            <strong>${item.assignment_title}</strong>
            <small>${item.student_name}</small>
            <span>${item.status}</span>
        </div>
    `).join('') || '<p class="empty-state">No recent uploads.</p>';

    const courseList = courses.map(c => `
        <div class="mini-card">
            <div>
                <strong>${c.course_name}</strong>
                <small>${c.course_code}</small>
            </div>
            <span class="status-badge submitted">Active</span>
        </div>
    `).join('') || '<p class="empty-state">No courses yet.</p>';

    return `
        <div class="dashboard-shell">
            <section class="hero-card">
                <div>
                    <p class="eyebrow">Teacher Portal</p>
                    <h1>${data.dashboard?.welcome || 'Welcome'}</h1>
                    <p>Monitor assignment activity, review student submissions, and grade work efficiently.</p>
                </div>
            </section>

            <section class="stats-grid">
                <div class="stat-card purple"><span class="stat-label">Total Assignments</span><strong class="stat-value">${stats.total_assignments ?? 0}</strong></div>
                <div class="stat-card blue"><span class="stat-label">Total Students</span><strong class="stat-value">${stats.total_students ?? 0}</strong></div>
                <div class="stat-card green"><span class="stat-label">Total Submissions</span><strong class="stat-value">${stats.total_submissions ?? 0}</strong></div>
                <div class="stat-card yellow"><span class="stat-label">Pending Reviews</span><strong class="stat-value">${stats.pending_reviews ?? 0}</strong></div>
                <div class="stat-card red"><span class="stat-label">Late</span><strong class="stat-value">${stats.late_submissions ?? 0}</strong></div>
                <div class="stat-card cyan"><span class="stat-label">Graded</span><strong class="stat-value">${stats.graded_submissions ?? 0}</strong></div>
            </section>

            <section class="content-grid two-col">
                <div class="panel">
                    <div class="panel-header">
                        <h2>Create Assignment</h2>
                    </div>
                    <form id="assignmentForm" class="stack-form">
                        <div class="form-group">
                            <label for="courseId">Course</label>
                            <select class="form-input" id="courseId" name="course_id" required>
                                ${courses.map(c => `<option value="${c.id}">${c.course_name}</option>`).join('') || '<option value="">No courses</option>'}
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="assignmentTitle">Title</label>
                            <input class="form-input" id="assignmentTitle" name="title" required>
                        </div>
                        <div class="form-group">
                            <label for="assignmentDesc">Description</label>
                            <textarea class="form-input" id="assignmentDesc" name="description"></textarea>
                        </div>
                        <div class="form-row two">
                            <div class="form-group">
                                <label for="assignmentDeadline">Deadline</label>
                                <input class="form-input" id="assignmentDeadline" name="deadline" type="datetime-local" required>
                            </div>
                            <div class="form-group">
                                <label for="assignmentMarks">Max Marks</label>
                                <input class="form-input" id="assignmentMarks" name="max_marks" type="number" value="100" required>
                            </div>
                        </div>
                        <div class="form-row two">
                            <div class="form-group">
                                <label for="allowedExtensions">Allowed Extensions</label>
                                <input class="form-input" id="allowedExtensions" name="allowed_extensions" value="pdf,docx" required>
                            </div>
                            <div class="form-group">
                                <label for="maxFileSize">Max File Size (MB)</label>
                                <input class="form-input" id="maxFileSize" name="max_file_size_mb" type="number" value="10" required>
                            </div>
                        </div>
                        <button type="submit" class="primary-btn">Create Assignment</button>
                    </form>
                </div>

                <div class="panel">
                    <div class="panel-header">
                        <h2>Courses</h2>
                    </div>
                    <form id="courseForm" class="stack-form">
                        <div class="form-group">
                            <label for="courseName">Course Name</label>
                            <input class="form-input" id="courseName" name="course_name" placeholder="Cloud Computing" required>
                        </div>
                        <div class="form-row two">
                            <div class="form-group">
                                <label for="courseCode">Course Code</label>
                                <input class="form-input" id="courseCode" name="course_code" placeholder="CC101" required>
                            </div>
                            <div class="form-group">
                                <label for="courseDescription">Description</label>
                                <input class="form-input" id="courseDescription" name="description" placeholder="Short summary" >
                            </div>
                        </div>
                        <button type="submit" class="primary-btn">Create Course</button>
                    </form>
                    <div class="stack-list" style="margin-top: 18px;">${courseList}</div>
                </div>
            </section>

            <section class="content-grid two-col">
                <div class="panel">
                    <div class="panel-header">
                        <h2>Assignments</h2>
                    </div>
                    <div class="stack-list">${assignmentRows}</div>
                </div>
                <div class="panel">
                    <div class="panel-header">
                        <h2>Recent Uploads</h2>
                    </div>
                    <div class="stack-list">${recentUploads}</div>
                </div>
            </section>
        </div>
    `;
}

function renderAssignmentsPage(assignments = []) {
    const cards = assignments.map(a => `
        <article class="assignment-card">
            <div class="card-top-row">
                <div>
                    <h3>${a.title}</h3>
                    <small>${a.course_name || 'Course'}</small>
                </div>
                <span class="status-badge ${a.submission_status ? a.submission_status.toLowerCase() : 'not-submitted'}">${a.submission_status || 'Open'}</span>
            </div>
            <p class="desc">${a.description || 'No description provided.'}</p>
            <div class="meta-row">
                <span>Deadline: ${new Date(a.deadline).toLocaleString()}</span>
                <span>Max Marks: ${a.max_marks}</span>
            </div>
            <div class="action-row">
                <button class="secondary-btn" data-action="view-assignment" data-id="${a.id}">View</button>
            </div>
        </article>
    `).join('') || '<p class="empty-state">No assignments available.</p>';

    return `
        <div class="dashboard-shell">
            <section class="hero-card">
                <p class="eyebrow">Assignments</p>
                <h1>Course work overview</h1>
                <p>View all upcoming assignments and access submission details.</p>
            </section>
            <section class="panel">
                <div class="panel-header">
                    <h2>All Assignments</h2>
                </div>
                <div class="assignment-list">${cards}</div>
            </section>
        </div>
    `;
}

function renderCoursesPage({ courses = [], isTeacher = false }) {
    const cards = courses.map(course => {
        const enrolled = Boolean(course.enrolled);
        return `
            <article class="assignment-card">
                <div class="card-top-row">
                    <div>
                        <h3>${course.course_name}</h3>
                        <small>${course.course_code}</small>
                    </div>
                    <span class="status-badge ${enrolled ? 'submitted' : 'not-submitted'}">${enrolled ? 'Enrolled' : 'Open'}</span>
                </div>
                <p class="desc">${course.description || 'No course description available yet.'}</p>
                <div class="meta-row">
                    <span>Teacher: ${course.teacher_name || 'Course staff'}</span>
                </div>
                <div class="action-row">
                    ${isTeacher ? '<button class="secondary-btn" data-route="teacher-dashboard">Manage</button>' : (enrolled ? '<button class="secondary-btn" data-route="student-dashboard">View Dashboard</button>' : `<button class="secondary-btn" data-action="enroll-course" data-id="${course.id}">Enroll</button>`) }
                </div>
            </article>
        `;
    }).join('') || '<p class="empty-state">No courses found.</p>';

    return `
        <div class="dashboard-shell">
            <section class="hero-card">
                <p class="eyebrow">Courses</p>
                <h1>${isTeacher ? 'Manage your teaching courses' : 'Course catalog and enrollment'}</h1>
                <p>${isTeacher ? 'Create and organize courses for your students.' : 'Browse all courses and enroll in the ones you want to join.'}</p>
            </section>

            ${isTeacher ? `
                <section class="panel">
                    <div class="panel-header">
                        <h2>Create Course</h2>
                    </div>
                    <form id="courseForm" class="stack-form">
                        <div class="form-group">
                            <label for="courseName">Course Name</label>
                            <input class="form-input" id="courseName" name="course_name" placeholder="Cloud Computing" required>
                        </div>
                        <div class="form-row two">
                            <div class="form-group">
                                <label for="courseCode">Course Code</label>
                                <input class="form-input" id="courseCode" name="course_code" placeholder="CC101" required>
                            </div>
                            <div class="form-group">
                                <label for="courseDescription">Course Description</label>
                                <input class="form-input" id="courseDescription" name="description" placeholder="Brief summary">
                            </div>
                        </div>
                        <button type="submit" class="primary-btn">Create Course</button>
                    </form>
                </section>
            ` : ''}

            <section class="panel">
                <div class="panel-header">
                    <h2>${isTeacher ? 'My Courses' : 'Available Courses'}</h2>
                </div>
                <div class="assignment-list">${cards}</div>
            </section>
        </div>
    `;
}

function renderAssignmentDetail(assignment) {
    const dueDate = new Date(assignment.deadline).toLocaleString();
    const submissions = assignment.submissions || [];

    const submissionRows = submissions.map(sub => `
        <div class="mini-card">
            <div>
                <strong>${sub.student_name || 'Student'}</strong>
                <small>${sub.file_name}</small>
            </div>
            <div class="submission-actions">
                <button class="secondary-btn" data-action="grade-submission" data-id="${sub.id}">Grade</button>
                <button class="secondary-btn" data-action="download-submission" data-id="${sub.id}">Download</button>
            </div>
        </div>
    `).join('') || '<p class="empty-state">No submissions yet.</p>';

    return `
        <div class="detail-shell">
            <div class="detail-card">
                <h2>${assignment.title}</h2>
                <p>${assignment.description || 'No description provided.'}</p>
                <div class="meta-row">
                    <span>Course: ${assignment.course_name}</span>
                    <span>Deadline: ${dueDate}</span>
                    <span>Max Marks: ${assignment.max_marks}</span>
                </div>
                <div class="detail-actions">
                    <button class="secondary-btn" data-action="back-to-dashboard">Back</button>
                </div>
            </div>
            <div class="panel">
                <div class="panel-header"><h2>Submission Review</h2></div>
                <div class="stack-list">${submissionRows}</div>
            </div>
        </div>
    `;
}

function renderSubmissionFeedback(submission, feedback) {
    const marks = feedback?.feedback?.marks ?? submission?.marks ?? '—';
    const maxMarks = feedback?.feedback?.max_marks ?? submission?.max_marks ?? '—';
    const note = feedback?.feedback?.feedback || 'No feedback available yet.';

    return `
        <div class="detail-card">
            <h2>Submission Feedback</h2>
            <div class="meta-row">
                <span>Marks: ${marks}/${maxMarks}</span>
                <span>Status: ${submission?.status || 'Pending'}</span>
            </div>
            <p>${note}</p>
            <button class="secondary-btn" data-action="back-to-dashboard">Back</button>
        </div>
    `;
}
