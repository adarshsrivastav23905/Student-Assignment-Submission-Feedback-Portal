"""
Database Models Module
======================
Defines all database tables using SQLAlchemy ORM.
Tables: Users, Courses, Assignments, Submissions, Enrollments.
Works with SQLite locally, PostgreSQL in cloud.
"""

from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy instance (attached to Flask app in app.py)
db = SQLAlchemy()


class User(db.Model):
    """
    User model — stores students, teachers, and admins.
    
    Cloud Concept: This table lives in the cloud database (e.g., Supabase PostgreSQL,
    Firestore, AWS RDS). Locally, it uses SQLite.
    """
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")  # student | teacher | admin
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    courses_teaching = db.relationship("Course", backref="teacher", lazy=True)
    submissions = db.relationship(
        "Submission",
        back_populates="student",
        lazy=True,
        foreign_keys="Submission.student_id",
    )
    enrollments = db.relationship("Enrollment", backref="student", lazy=True)

    def to_dict(self):
        """Convert user to dictionary (excludes password hash for security)."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Course(db.Model):
    """
    Course model — groups assignments under a course taught by a teacher.
    
    Relationship: One Teacher → Many Courses → Many Assignments
    """
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    course_name = db.Column(db.String(200), nullable=False)
    course_code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    assignments = db.relationship("Assignment", backref="course", lazy=True, cascade="all, delete-orphan")
    enrollments = db.relationship("Enrollment", backref="course", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "course_name": self.course_name,
            "course_code": self.course_code,
            "description": self.description,
            "teacher_id": self.teacher_id,
            "teacher_name": self.teacher.name if self.teacher else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Enrollment(db.Model):
    """
    Enrollment model — links students to courses.
    
    A student must be enrolled in a course to see and submit its assignments.
    """
    __tablename__ = "enrollments"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Unique constraint: a student can only enroll once per course
    __table_args__ = (
        db.UniqueConstraint("student_id", "course_id", name="unique_enrollment"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "course_id": self.course_id,
            "enrolled_at": self.enrolled_at.isoformat() if self.enrolled_at else None,
        }


class Assignment(db.Model):
    """
    Assignment model — created by teachers for a specific course.
    
    Cloud Concept: Assignment metadata is in the database.
    Actual assignment description files (if any) go to cloud object storage.
    """
    __tablename__ = "assignments"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    deadline = db.Column(db.DateTime, nullable=False)
    max_marks = db.Column(db.Integer, nullable=False, default=100)
    allowed_extensions = db.Column(db.String(200), default="pdf,docx,doc,txt,zip")
    max_file_size_mb = db.Column(db.Integer, default=10)
    allow_late_submission = db.Column(db.Boolean, default=False)
    allow_resubmission = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    submissions = db.relationship("Submission", backref="assignment", lazy=True, cascade="all, delete-orphan")
    creator = db.relationship("User", foreign_keys=[created_by])

    def to_dict(self):
        return {
            "id": self.id,
            "course_id": self.course_id,
            "course_name": self.course.course_name if self.course else None,
            "title": self.title,
            "description": self.description,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "max_marks": self.max_marks,
            "allowed_extensions": self.allowed_extensions,
            "max_file_size_mb": self.max_file_size_mb,
            "allow_late_submission": self.allow_late_submission,
            "allow_resubmission": self.allow_resubmission,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Submission(db.Model):
    """
    Submission model — tracks student assignment submissions.
    
    Cloud Concepts:
    - file_name: Original filename uploaded by student
    - storage_path: Path in cloud object storage (e.g., assignments/1/students/5/submission.pdf)
    - file_url: Signed URL or public URL for downloading
    - The actual file is in CLOUD OBJECT STORAGE, not in the database
    - Only metadata (who, when, marks, feedback) is in the database
    
    Submission Statuses:
    - NOT_SUBMITTED: Default state
    - SUBMITTED: Submitted before deadline
    - LATE: Submitted after deadline
    - GRADED: Teacher has provided marks and feedback
    """
    __tablename__ = "submissions"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey("assignments.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    storage_path = db.Column(db.String(500), nullable=False)  # Cloud storage path
    file_url = db.Column(db.String(500), nullable=True)       # Download URL
    submitted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    status = db.Column(db.String(20), default="SUBMITTED")    # SUBMITTED | LATE | GRADED
    marks = db.Column(db.Integer, nullable=True)
    feedback = db.Column(db.Text, nullable=True)
    graded_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    graded_at = db.Column(db.DateTime, nullable=True)

    # Unique constraint: one submission per student per assignment (resubmission replaces)
    __table_args__ = (
        db.UniqueConstraint("assignment_id", "student_id", name="unique_submission"),
    )

    # Relationship for grader and student
    student = db.relationship("User", back_populates="submissions", foreign_keys=[student_id])
    grader = db.relationship("User", foreign_keys=[graded_by])

    def to_dict(self):
        return {
            "id": self.id,
            "assignment_id": self.assignment_id,
            "assignment_title": self.assignment.title if self.assignment else None,
            "student_id": self.student_id,
            "student_name": self.student.name if self.student else None,
            "file_name": self.file_name,
            "storage_path": self.storage_path,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "status": self.status,
            "marks": self.marks,
            "feedback": self.feedback,
            "graded_by": self.graded_by,
            "graded_at": self.graded_at.isoformat() if self.graded_at else None,
            "max_marks": self.assignment.max_marks if self.assignment else None,
        }


def init_db(app):
    """
    Initialize the database with the Flask application.
    Creates all tables if they don't exist.
    Seeds dummy data for demonstration.
    """
    db.init_app(app)
    with app.app_context():
        db.create_all()
        _seed_dummy_data()


def _seed_dummy_data():
    """
    Seed the database with dummy teachers, students, courses, and assignments
    for demonstration purposes. Only runs if database is empty.
    """
    from werkzeug.security import generate_password_hash
    from datetime import timedelta

    # Skip if data already exists
    if User.query.first() is not None:
        return

    print("📦 Seeding database with dummy data...")

    # --- Create Teachers ---
    teacher1 = User(
        name="Dr. Sarah Johnson",
        email="teacher@example.com",
        password_hash=generate_password_hash("teacher123"),
        role="teacher",
    )
    teacher2 = User(
        name="Prof. Michael Chen",
        email="teacher2@example.com",
        password_hash=generate_password_hash("teacher123"),
        role="teacher",
    )

    # --- Create Students ---
    student1 = User(
        name="Alice Smith",
        email="student@example.com",
        password_hash=generate_password_hash("student123"),
        role="student",
    )
    student2 = User(
        name="Bob Wilson",
        email="student2@example.com",
        password_hash=generate_password_hash("student123"),
        role="student",
    )
    student3 = User(
        name="Charlie Davis",
        email="student3@example.com",
        password_hash=generate_password_hash("student123"),
        role="student",
    )

    # --- Create Admin ---
    admin = User(
        name="System Admin",
        email="admin@example.com",
        password_hash=generate_password_hash("admin123"),
        role="admin",
    )

    db.session.add_all([teacher1, teacher2, student1, student2, student3, admin])
    db.session.flush()  # Get IDs assigned

    # --- Create Courses ---
    course1 = Course(
        course_name="Cloud Computing Fundamentals",
        course_code="CC101",
        description="Introduction to cloud computing concepts, services, and deployment models.",
        teacher_id=teacher1.id,
    )
    course2 = Course(
        course_name="Web Development",
        course_code="WD201",
        description="Full-stack web development with modern frameworks.",
        teacher_id=teacher1.id,
    )
    course3 = Course(
        course_name="Database Systems",
        course_code="DB301",
        description="Relational databases, SQL, and cloud database services.",
        teacher_id=teacher2.id,
    )

    db.session.add_all([course1, course2, course3])
    db.session.flush()

    # --- Enroll Students ---
    enrollments = [
        Enrollment(student_id=student1.id, course_id=course1.id),
        Enrollment(student_id=student1.id, course_id=course2.id),
        Enrollment(student_id=student2.id, course_id=course1.id),
        Enrollment(student_id=student2.id, course_id=course3.id),
        Enrollment(student_id=student3.id, course_id=course1.id),
        Enrollment(student_id=student3.id, course_id=course2.id),
        Enrollment(student_id=student3.id, course_id=course3.id),
    ]
    db.session.add_all(enrollments)

    # --- Create Assignments ---
    now = datetime.now(timezone.utc)

    assignment1 = Assignment(
        course_id=course1.id,
        title="Cloud Service Models Report",
        description="Write a detailed report comparing IaaS, PaaS, and SaaS. Include real-world examples of each model and explain when to use each one. Minimum 1500 words.",
        deadline=now + timedelta(days=7),
        max_marks=100,
        allowed_extensions="pdf,docx",
        allow_late_submission=True,
        allow_resubmission=True,
        created_by=teacher1.id,
    )
    assignment2 = Assignment(
        course_id=course1.id,
        title="Deploy a Web App to Cloud",
        description="Deploy a simple web application to any free-tier cloud platform (Render, Railway, Vercel, etc.). Submit a PDF containing: deployment URL, screenshots, and a brief explanation of the deployment process.",
        deadline=now + timedelta(days=14),
        max_marks=50,
        allowed_extensions="pdf",
        allow_late_submission=False,
        allow_resubmission=True,
        created_by=teacher1.id,
    )
    assignment3 = Assignment(
        course_id=course2.id,
        title="REST API Design Document",
        description="Design a REST API for a library management system. Include endpoints, HTTP methods, request/response formats, and authentication strategy.",
        deadline=now + timedelta(days=10),
        max_marks=75,
        allowed_extensions="pdf,docx,doc",
        allow_late_submission=True,
        allow_resubmission=True,
        created_by=teacher1.id,
    )
    assignment4 = Assignment(
        course_id=course3.id,
        title="Database Normalization Exercise",
        description="Normalize the given denormalized dataset to 3NF. Show all intermediate normal forms and explain each step. Submit as PDF.",
        deadline=now + timedelta(days=5),
        max_marks=80,
        allowed_extensions="pdf",
        allow_late_submission=False,
        allow_resubmission=False,
        created_by=teacher2.id,
    )
    # Past deadline assignment for demo
    assignment5 = Assignment(
        course_id=course1.id,
        title="Introduction to Virtualization",
        description="Write a short essay on virtualization technologies. Cover hypervisors, containers, and their role in cloud computing.",
        deadline=now - timedelta(days=2),  # Already past
        max_marks=50,
        allowed_extensions="pdf,docx",
        allow_late_submission=True,
        allow_resubmission=False,
        created_by=teacher1.id,
    )

    db.session.add_all([assignment1, assignment2, assignment3, assignment4, assignment5])
    db.session.commit()

    print("✅ Dummy data seeded successfully!")
    print("   👨‍🏫 Teachers: teacher@example.com / teacher123")
    print("   👨‍🏫 Teachers: teacher2@example.com / teacher123")
    print("   👨‍🎓 Students: student@example.com / student123")
    print("   👨‍🎓 Students: student2@example.com / student123")
    print("   👨‍🎓 Students: student3@example.com / student123")
    print("   🔑 Admin:    admin@example.com / admin123")
