"""
Assignment Routes
=================
CRUD operations for assignments (Teacher creates, Students view).

Endpoints:
    POST   /api/assignments          — Create assignment (teacher)
    GET    /api/assignments          — List assignments
    GET    /api/assignments/<id>     — Get assignment details
    PUT    /api/assignments/<id>     — Update assignment (teacher)
    DELETE /api/assignments/<id>     — Delete assignment (teacher)
    GET    /api/courses              — List courses
    POST   /api/courses              — Create course (teacher)
    POST   /api/courses/<id>/enroll  — Enroll student in course
"""

from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, g
from backend.models.database import db, Assignment, Course, Enrollment, Submission, User
from backend.middleware.auth_middleware import require_auth, require_role
from backend.utils.validators import validate_assignment_data

assignment_bp = Blueprint("assignments", __name__)


# =============================================================================
# COURSE ENDPOINTS
# =============================================================================

@assignment_bp.route("/api/courses", methods=["GET"])
@require_auth
def list_courses():
    """
    List courses based on user role.
    - Teacher: courses they teach
    - Student: all available courses with enrollment status
    - Admin: all courses
    """
    if g.user_role == "teacher":
        courses = Course.query.filter_by(teacher_id=g.user_id).all()
        course_list = [c.to_dict() for c in courses]
    elif g.user_role == "student":
        enrolled = Enrollment.query.filter_by(student_id=g.user_id).all()
        enrolled_ids = {e.course_id for e in enrolled}
        courses = Course.query.all()
        course_list = []
        for c in courses:
            course_data = c.to_dict()
            course_data["enrolled"] = c.id in enrolled_ids
            course_list.append(course_data)
    else:  # admin
        courses = Course.query.all()
        course_list = [c.to_dict() for c in courses]

    return jsonify({"courses": course_list}), 200


@assignment_bp.route("/api/courses", methods=["POST"])
@require_auth
@require_role("teacher", "admin")
def create_course():
    """
    Create a new course (teacher/admin only).

    Request Body:
        {
            "course_name": "Cloud Computing",
            "course_code": "CC101",
            "description": "Introduction to cloud computing"
        }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    if not data.get("course_name", "").strip():
        return jsonify({"error": "Course name is required"}), 400
    if not data.get("course_code", "").strip():
        return jsonify({"error": "Course code is required"}), 400

    # Check for duplicate course code
    existing = Course.query.filter_by(course_code=data["course_code"].strip().upper()).first()
    if existing:
        return jsonify({"error": "Course code already exists"}), 409

    course = Course(
        course_name=data["course_name"].strip(),
        course_code=data["course_code"].strip().upper(),
        description=data.get("description", "").strip(),
        teacher_id=g.user_id,
    )
    db.session.add(course)
    db.session.commit()

    return jsonify({"message": "Course created", "course": course.to_dict()}), 201


@assignment_bp.route("/api/courses/<int:course_id>/enroll", methods=["POST"])
@require_auth
def enroll_in_course(course_id):
    """
    Enroll a student in a course.
    - Students can enroll themselves
    - Teachers/admins can enroll students by providing student_id
    """
    course = db.session.get(Course, course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404

    # Determine which student to enroll
    if g.user_role == "student":
        student_id = g.user_id
    else:
        data = request.get_json() or {}
        student_id = data.get("student_id")
        if not student_id:
            return jsonify({"error": "student_id is required"}), 400

    # Check if already enrolled
    existing = Enrollment.query.filter_by(
        student_id=student_id, course_id=course_id
    ).first()
    if existing:
        return jsonify({"error": "Already enrolled in this course"}), 409

    enrollment = Enrollment(student_id=student_id, course_id=course_id)
    db.session.add(enrollment)
    db.session.commit()

    return jsonify({"message": "Enrolled successfully"}), 201


# =============================================================================
# ASSIGNMENT ENDPOINTS
# =============================================================================

@assignment_bp.route("/api/assignments", methods=["POST"])
@require_auth
@require_role("teacher", "admin")
def create_assignment():
    """
    Create a new assignment (teacher/admin only).

    Request Body:
        {
            "course_id": 1,
            "title": "Cloud Service Models Report",
            "description": "Write a report on IaaS, PaaS, SaaS",
            "deadline": "2025-12-31T23:59:59",
            "max_marks": 100,
            "allowed_extensions": "pdf,docx",
            "max_file_size_mb": 10,
            "allow_late_submission": true,
            "allow_resubmission": true
        }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    # Validate input
    valid, errors = validate_assignment_data(data)
    if not valid:
        return jsonify({"error": "Validation failed", "details": errors}), 400

    # Verify course exists and teacher owns it
    course = db.session.get(Course, data["course_id"])
    if not course:
        return jsonify({"error": "Course not found"}), 404

    if g.user_role == "teacher" and course.teacher_id != g.user_id:
        return jsonify({"error": "You are not the teacher of this course"}), 403

    # Parse deadline
    deadline = datetime.fromisoformat(data["deadline"].replace("Z", "+00:00"))
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)

    assignment = Assignment(
        course_id=data["course_id"],
        title=data["title"].strip(),
        description=data.get("description", "").strip(),
        deadline=deadline,
        max_marks=data.get("max_marks", 100),
        allowed_extensions=data.get("allowed_extensions", "pdf,docx,doc,txt,zip"),
        max_file_size_mb=data.get("max_file_size_mb", 10),
        allow_late_submission=data.get("allow_late_submission", False),
        allow_resubmission=data.get("allow_resubmission", True),
        created_by=g.user_id,
    )
    db.session.add(assignment)
    db.session.commit()

    return jsonify({
        "message": "Assignment created successfully",
        "assignment": assignment.to_dict(),
    }), 201


@assignment_bp.route("/api/assignments", methods=["GET"])
@require_auth
def list_assignments():
    """
    List assignments based on user role.
    - Teacher: all assignments for their courses
    - Student: assignments for enrolled courses
    """
    if g.user_role == "teacher":
        courses = Course.query.filter_by(teacher_id=g.user_id).all()
        course_ids = [c.id for c in courses]
    elif g.user_role == "student":
        enrollments = Enrollment.query.filter_by(student_id=g.user_id).all()
        course_ids = [e.course_id for e in enrollments]
    else:  # admin
        course_ids = [c.id for c in Course.query.all()]

    assignments = Assignment.query.filter(
        Assignment.course_id.in_(course_ids)
    ).order_by(Assignment.deadline.asc()).all()

    # For students, include submission status for each assignment
    result = []
    for a in assignments:
        a_dict = a.to_dict()
        if g.user_role == "student":
            submission = Submission.query.filter_by(
                assignment_id=a.id, student_id=g.user_id
            ).first()
            a_dict["submission_status"] = submission.status if submission else "NOT_SUBMITTED"
            a_dict["submission_id"] = submission.id if submission else None
        else:
            # For teachers, include submission count
            sub_count = Submission.query.filter_by(assignment_id=a.id).count()
            a_dict["submission_count"] = sub_count
        result.append(a_dict)

    return jsonify({"assignments": result}), 200


@assignment_bp.route("/api/assignments/<int:assignment_id>", methods=["GET"])
@require_auth
def get_assignment(assignment_id):
    """Get a single assignment by ID."""
    assignment = db.session.get(Assignment, assignment_id)
    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404

    a_dict = assignment.to_dict()

    # Add submission info for students
    if g.user_role == "student":
        submission = Submission.query.filter_by(
            assignment_id=assignment_id, student_id=g.user_id
        ).first()
        a_dict["submission_status"] = submission.status if submission else "NOT_SUBMITTED"
        a_dict["submission"] = submission.to_dict() if submission else None
    else:
        # For teachers, include all submissions
        submissions = Submission.query.filter_by(assignment_id=assignment_id).all()
        a_dict["submissions"] = [s.to_dict() for s in submissions]
        a_dict["submission_count"] = len(submissions)

    return jsonify({"assignment": a_dict}), 200


@assignment_bp.route("/api/assignments/<int:assignment_id>", methods=["PUT"])
@require_auth
@require_role("teacher", "admin")
def update_assignment(assignment_id):
    """
    Update an assignment (teacher/admin only).
    Only the creating teacher or admin can update.
    """
    assignment = db.session.get(Assignment, assignment_id)
    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404

    if g.user_role == "teacher" and assignment.created_by != g.user_id:
        return jsonify({"error": "You can only update your own assignments"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    # Update allowed fields
    if "title" in data:
        assignment.title = data["title"].strip()
    if "description" in data:
        assignment.description = data["description"].strip()
    if "deadline" in data:
        deadline = datetime.fromisoformat(data["deadline"].replace("Z", "+00:00"))
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        assignment.deadline = deadline
    if "max_marks" in data:
        assignment.max_marks = data["max_marks"]
    if "allowed_extensions" in data:
        assignment.allowed_extensions = data["allowed_extensions"]
    if "max_file_size_mb" in data:
        assignment.max_file_size_mb = data["max_file_size_mb"]
    if "allow_late_submission" in data:
        assignment.allow_late_submission = data["allow_late_submission"]
    if "allow_resubmission" in data:
        assignment.allow_resubmission = data["allow_resubmission"]

    db.session.commit()

    return jsonify({
        "message": "Assignment updated",
        "assignment": assignment.to_dict(),
    }), 200


@assignment_bp.route("/api/assignments/<int:assignment_id>", methods=["DELETE"])
@require_auth
@require_role("teacher", "admin")
def delete_assignment(assignment_id):
    """Delete an assignment and all its submissions (teacher/admin only)."""
    assignment = db.session.get(Assignment, assignment_id)
    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404

    if g.user_role == "teacher" and assignment.created_by != g.user_id:
        return jsonify({"error": "You can only delete your own assignments"}), 403

    # Delete associated files from storage
    from backend.services.storage_service import storage_service
    submissions = Submission.query.filter_by(assignment_id=assignment_id).all()
    for sub in submissions:
        storage_service.delete_file(sub.storage_path)

    db.session.delete(assignment)
    db.session.commit()

    return jsonify({"message": "Assignment deleted"}), 200
