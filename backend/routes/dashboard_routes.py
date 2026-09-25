"""
Dashboard Routes
================
Provides aggregated data for Student and Teacher dashboards.

Cloud Concept: These queries run against the cloud database,
aggregating data for real-time dashboard views.

Endpoints:
    GET /api/dashboard/student  — Student dashboard data
    GET /api/dashboard/teacher  — Teacher dashboard data
"""

from datetime import datetime, timezone, timedelta
from flask import Blueprint, jsonify, g
from sqlalchemy import func
from backend.models.database import (
    db, User, Course, Assignment, Submission, Enrollment,
)
from backend.middleware.auth_middleware import require_auth, require_role

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/api/dashboard/student", methods=["GET"])
@require_auth
@require_role("student")
def student_dashboard():
    """
    Student Dashboard Data.

    Returns:
    - Welcome message
    - Total assignments (across enrolled courses)
    - Pending (not submitted)
    - Submitted count
    - Late submissions count
    - Graded count
    - Upcoming deadlines
    - Recent feedback
    """
    student_id = g.user_id
    now = datetime.now(timezone.utc)

    # Get enrolled course IDs
    enrollments = Enrollment.query.filter_by(student_id=student_id).all()
    course_ids = [e.course_id for e in enrollments]

    # Get all assignments for enrolled courses
    assignments = Assignment.query.filter(
        Assignment.course_id.in_(course_ids)
    ).all()
    assignment_ids = [a.id for a in assignments]

    # Get student's submissions
    submissions = Submission.query.filter(
        Submission.student_id == student_id,
        Submission.assignment_id.in_(assignment_ids),
    ).all()
    submission_map = {s.assignment_id: s for s in submissions}

    # Calculate statistics
    total = len(assignments)
    submitted = sum(1 for s in submissions if s.status in ("SUBMITTED", "LATE", "GRADED"))
    pending = total - submitted
    late = sum(1 for s in submissions if s.status == "LATE")
    graded = sum(1 for s in submissions if s.status == "GRADED")

    # Upcoming deadlines (assignments not yet submitted, deadline in future)
    upcoming = []
    for a in assignments:
        deadline_aware = a.deadline.replace(tzinfo=timezone.utc) if a.deadline.tzinfo is None else a.deadline
        if a.id not in submission_map and deadline_aware > now:
            upcoming.append({
                "id": a.id,
                "title": a.title,
                "course_name": a.course.course_name if a.course else "",
                "deadline": a.deadline.isoformat(),
                "days_remaining": (deadline_aware - now).days,
            })
    upcoming.sort(key=lambda x: x["deadline"])

    # Recent feedback (last 5 graded submissions)
    recent_feedback = []
    graded_subs = [s for s in submissions if s.status == "GRADED"]
    graded_subs.sort(key=lambda s: s.graded_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    for s in graded_subs[:5]:
        recent_feedback.append({
            "submission_id": s.id,
            "assignment_title": s.assignment.title if s.assignment else "",
            "marks": s.marks,
            "max_marks": s.assignment.max_marks if s.assignment else None,
            "feedback": s.feedback,
            "graded_at": s.graded_at.isoformat() if s.graded_at else None,
        })

    return jsonify({
        "dashboard": {
            "welcome": f"Welcome, {g.user_name}",
            "stats": {
                "total_assignments": total,
                "pending": pending,
                "submitted": submitted,
                "late": late,
                "graded": graded,
            },
            "upcoming_deadlines": upcoming[:5],
            "recent_feedback": recent_feedback,
            "enrolled_courses": len(course_ids),
        }
    }), 200


@dashboard_bp.route("/api/dashboard/teacher", methods=["GET"])
@require_auth
@require_role("teacher", "admin")
def teacher_dashboard():
    """
    Teacher Dashboard Data.

    Returns:
    - Total assignments created
    - Total students across courses
    - Total submissions received
    - Pending reviews (ungraded submissions)
    - Late submissions
    - Graded submissions
    - Recent uploads
    - Upcoming deadlines
    """
    teacher_id = g.user_id
    now = datetime.now(timezone.utc)

    # Get teacher's courses
    if g.user_role == "admin":
        courses = Course.query.all()
    else:
        courses = Course.query.filter_by(teacher_id=teacher_id).all()
    course_ids = [c.id for c in courses]

    # Get all assignments for these courses
    assignments = Assignment.query.filter(
        Assignment.course_id.in_(course_ids)
    ).all()
    assignment_ids = [a.id for a in assignments]

    # Get all submissions
    submissions = Submission.query.filter(
        Submission.assignment_id.in_(assignment_ids)
    ).all()

    # Count unique students
    student_ids = set()
    for enrollment in Enrollment.query.filter(Enrollment.course_id.in_(course_ids)).all():
        student_ids.add(enrollment.student_id)

    # Statistics
    total_submissions = len(submissions)
    pending_reviews = sum(1 for s in submissions if s.status in ("SUBMITTED", "LATE"))
    late_submissions = sum(1 for s in submissions if s.status == "LATE")
    graded_submissions = sum(1 for s in submissions if s.status == "GRADED")

    # Recent uploads (last 10)
    recent = sorted(submissions, key=lambda s: s.submitted_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)[:10]
    recent_uploads = [{
        "submission_id": s.id,
        "student_name": s.student.name if s.student else "",
        "assignment_title": s.assignment.title if s.assignment else "",
        "file_name": s.file_name,
        "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None,
        "status": s.status,
    } for s in recent]

    # Upcoming deadlines
    upcoming = []
    for a in assignments:
        deadline_aware = a.deadline.replace(tzinfo=timezone.utc) if a.deadline.tzinfo is None else a.deadline
        if deadline_aware > now:
            upcoming.append({
                "id": a.id,
                "title": a.title,
                "course_name": a.course.course_name if a.course else "",
                "deadline": a.deadline.isoformat(),
                "days_remaining": (deadline_aware - now).days,
            })
    upcoming.sort(key=lambda x: x["deadline"])

    return jsonify({
        "dashboard": {
            "welcome": f"Welcome, {g.user_name}",
            "stats": {
                "total_assignments": len(assignments),
                "total_students": len(student_ids),
                "total_submissions": total_submissions,
                "pending_reviews": pending_reviews,
                "late_submissions": late_submissions,
                "graded_submissions": graded_submissions,
            },
            "recent_uploads": recent_uploads,
            "upcoming_deadlines": upcoming[:5],
            "courses": [c.to_dict() for c in courses],
        }
    }), 200
