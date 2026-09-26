"""
Submission Routes
=================
Handles file upload, download, resubmission, and grading.

Cloud Concepts Demonstrated:
- File upload → Cloud Object Storage
- Metadata → Cloud Database
- Signed URLs → Secure file downloads
- Deadline validation → Server-side timestamps

Endpoints:
    POST /api/assignments/<id>/submit       — Submit assignment (student)
    GET  /api/submissions/me                — My submissions (student)
    GET  /api/assignments/<id>/submissions  — All submissions for assignment (teacher)
    GET  /api/submissions/<id>              — Get submission details
    GET  /api/submissions/<id>/download     — Download submitted file
    POST /api/submissions/<id>/grade        — Grade submission (teacher)
    GET  /api/submissions/<id>/feedback     — Get feedback (student)
"""

import os
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, g, send_file
from backend.models.database import db, Assignment, Submission, Course, Enrollment
from backend.middleware.auth_middleware import require_auth, require_role
from backend.services.storage_service import storage_service
from backend.utils.validators import validate_file, validate_grade_data, validate_deadline

submission_bp = Blueprint("submissions", __name__)


@submission_bp.route("/api/assignments/<int:assignment_id>/submit", methods=["POST"])
@require_auth
@require_role("student")
def submit_assignment(assignment_id):
    """
    Submit an assignment file.

    Workflow:
    1. Validate student authentication ✓ (middleware)
    2. Validate assignment exists
    3. Validate student is enrolled in the course
    4. Check deadline (server-side timestamp)
    5. Validate file (type, size)
    6. Upload file to cloud object storage
    7. Save submission metadata to cloud database
    8. Return confirmation

    Request: multipart/form-data with 'file' field
    """
    # 1. Get the assignment
    assignment = db.session.get(Assignment, assignment_id)
    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404

    # 2. Verify student is enrolled in the course
    enrollment = Enrollment.query.filter_by(
        student_id=g.user_id, course_id=assignment.course_id
    ).first()
    if not enrollment:
        return jsonify({"error": "You are not enrolled in this course"}), 403

    # 3. Check deadline using SERVER-SIDE timestamp (never trust client time)
    is_allowed, status = validate_deadline(
        assignment.deadline, assignment.allow_late_submission
    )
    if not is_allowed:
        return jsonify({
            "error": "Deadline has passed and late submissions are not allowed",
            "deadline": assignment.deadline.isoformat(),
        }), 400

    # 4. Check for existing submission
    existing_submission = Submission.query.filter_by(
        assignment_id=assignment_id, student_id=g.user_id
    ).first()

    if existing_submission and not assignment.allow_resubmission:
        return jsonify({
            "error": "You have already submitted this assignment. Resubmission is not allowed."
        }), 400

    # 5. Get the file from the request
    if "file" not in request.files:
        return jsonify({"error": "No file provided. Use 'file' field in form-data."}), 400

    file = request.files["file"]

    # 6. Validate file type and size
    allowed_ext = assignment.allowed_extensions
    valid, error = validate_file(file, allowed_ext, assignment.max_file_size_mb)
    if not valid:
        return jsonify({"error": error}), 400

    # 7. Upload file to CLOUD OBJECT STORAGE
    try:
        upload_result = storage_service.upload_file(
            file=file,
            assignment_id=assignment_id,
            student_id=g.user_id,
            original_filename=file.filename,
        )
    except Exception as e:
        # Cloud storage failure handling
        return jsonify({
            "error": "File upload failed. Please try again.",
            "details": str(e),
        }), 500

    # 8. Save/update SUBMISSION METADATA in cloud database
    if existing_submission:
        # Resubmission: delete old file, update record
        storage_service.delete_file(existing_submission.storage_path)
        existing_submission.file_name = file.filename
        existing_submission.storage_path = upload_result["storage_path"]
        existing_submission.file_url = upload_result.get("file_url", "")
        existing_submission.submitted_at = datetime.now(timezone.utc)
        existing_submission.status = status
        # Reset grading on resubmission
        existing_submission.marks = None
        existing_submission.feedback = None
        existing_submission.graded_by = None
        existing_submission.graded_at = None
        submission = existing_submission
        message = "Assignment resubmitted successfully"
    else:
        # New submission
        submission = Submission(
            assignment_id=assignment_id,
            student_id=g.user_id,
            file_name=file.filename,
            storage_path=upload_result["storage_path"],
            file_url=upload_result.get("file_url", ""),
            status=status,
        )
        db.session.add(submission)
        message = "Assignment submitted successfully"

    db.session.commit()

    return jsonify({
        "message": message,
        "submission": submission.to_dict(),
        "status": status,
    }), 201


@submission_bp.route("/api/submissions/me", methods=["GET"])
@require_auth
@require_role("student")
def get_my_submissions():
    """
    Get all submissions by the current student.
    Students can only see their OWN submissions (privacy/authorization).
    """
    submissions = Submission.query.filter_by(student_id=g.user_id)\
        .order_by(Submission.submitted_at.desc()).all()

    return jsonify({
        "submissions": [s.to_dict() for s in submissions],
        "count": len(submissions),
    }), 200


@submission_bp.route("/api/assignments/<int:assignment_id>/submissions", methods=["GET"])
@require_auth
@require_role("teacher", "admin")
def get_assignment_submissions(assignment_id):
    """
    Get all submissions for an assignment (teacher/admin only).
    Teachers can view all student submissions for their assignments.
    """
    assignment = db.session.get(Assignment, assignment_id)
    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404

    # Verify teacher owns the course
    if g.user_role == "teacher":
        course = db.session.get(Course, assignment.course_id)
        if course.teacher_id != g.user_id:
            return jsonify({"error": "Access denied"}), 403

    submissions = Submission.query.filter_by(assignment_id=assignment_id)\
        .order_by(Submission.submitted_at.desc()).all()

    return jsonify({
        "assignment": assignment.to_dict(),
        "submissions": [s.to_dict() for s in submissions],
        "count": len(submissions),
    }), 200


@submission_bp.route("/api/submissions/<int:submission_id>", methods=["GET"])
@require_auth
def get_submission(submission_id):
    """
    Get a specific submission.
    - Students can only view their own submissions
    - Teachers can view submissions for their courses
    """
    submission = db.session.get(Submission, submission_id)
    if not submission:
        return jsonify({"error": "Submission not found"}), 404

    # Authorization check
    if g.user_role == "student" and submission.student_id != g.user_id:
        return jsonify({"error": "Access denied. You can only view your own submissions."}), 403

    if g.user_role == "teacher":
        assignment = db.session.get(Assignment, submission.assignment_id)
        course = db.session.get(Course, assignment.course_id)
        if course.teacher_id != g.user_id:
            return jsonify({"error": "Access denied"}), 403

    return jsonify({"submission": submission.to_dict()}), 200


@submission_bp.route("/api/submissions/<int:submission_id>/download", methods=["GET"])
@require_auth
def download_submission(submission_id):
    """
    Download a submitted file.

    Cloud Concept: In cloud deployment, this would generate a SIGNED URL
    that provides temporary, secure access to the file in cloud storage.
    The signed URL expires after a set time, preventing unauthorized access.

    Authorization:
    - Students can download their own submissions
    - Teachers can download submissions for their courses
    """
    submission = db.session.get(Submission, submission_id)
    if not submission:
        return jsonify({"error": "Submission not found"}), 404

    # Authorization check
    if g.user_role == "student" and submission.student_id != g.user_id:
        return jsonify({"error": "Access denied"}), 403

    if g.user_role == "teacher":
        assignment = db.session.get(Assignment, submission.assignment_id)
        course = db.session.get(Course, assignment.course_id)
        if course.teacher_id != g.user_id:
            return jsonify({"error": "Access denied"}), 403

    # Get file from storage
    file_path = storage_service.download_file(submission.storage_path)
    if not file_path or not os.path.exists(file_path):
        return jsonify({"error": "File not found in storage"}), 404

    # For local storage, send the file directly
    # For cloud storage, this would return a signed URL
    return send_file(
        file_path,
        download_name=submission.file_name,
        as_attachment=True,
    )


@submission_bp.route("/api/submissions/<int:submission_id>/grade", methods=["POST"])
@require_auth
@require_role("teacher", "admin")
def grade_submission(submission_id):
    """
    Grade a submission — assign marks and provide feedback.

    Request Body:
        {
            "marks": 85,
            "feedback": "Excellent work! Clear understanding of cloud concepts."
        }

    Authorization: Only the course teacher can grade submissions.
    Validation: Marks cannot exceed assignment's max_marks.
    """
    submission = db.session.get(Submission, submission_id)
    if not submission:
        return jsonify({"error": "Submission not found"}), 404

    # Verify teacher owns the course
    assignment = db.session.get(Assignment, submission.assignment_id)
    if g.user_role == "teacher":
        course = db.session.get(Course, assignment.course_id)
        if course.teacher_id != g.user_id:
            return jsonify({"error": "Access denied. You are not the teacher of this course."}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    # Validate grade data
    valid, errors = validate_grade_data(data, assignment.max_marks)
    if not valid:
        return jsonify({"error": "Validation failed", "details": errors}), 400

    # Update submission with grade
    submission.marks = int(data["marks"])
    submission.feedback = data.get("feedback", "")
    submission.graded_by = g.user_id
    submission.graded_at = datetime.now(timezone.utc)
    submission.status = "GRADED"

    db.session.commit()

    return jsonify({
        "message": "Submission graded successfully",
        "submission": submission.to_dict(),
    }), 200


@submission_bp.route("/api/submissions/<int:submission_id>/feedback", methods=["GET"])
@require_auth
def get_feedback(submission_id):
    """
    Get feedback for a submission.
    Students can only see feedback on their own submissions.
    """
    submission = db.session.get(Submission, submission_id)
    if not submission:
        return jsonify({"error": "Submission not found"}), 404

    # Authorization
    if g.user_role == "student" and submission.student_id != g.user_id:
        return jsonify({"error": "Access denied"}), 403

    if submission.status != "GRADED":
        return jsonify({
            "message": "This submission has not been graded yet",
            "status": submission.status,
        }), 200

    return jsonify({
        "feedback": {
            "marks": submission.marks,
            "max_marks": submission.assignment.max_marks if submission.assignment else None,
            "feedback": submission.feedback,
            "graded_at": submission.graded_at.isoformat() if submission.graded_at else None,
            "assignment_title": submission.assignment.title if submission.assignment else None,
        }
    }), 200
