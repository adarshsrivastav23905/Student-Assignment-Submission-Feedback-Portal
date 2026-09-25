"""
Input Validators
================
Validates all user inputs before processing.

Cloud Security: Input validation is a critical security layer.
Never trust client-side data — always validate on the server.
"""

import os
import re
from datetime import datetime, timezone
from backend.config import Config


def validate_email(email):
    """Validate email format."""
    if not email:
        return False, "Email is required"
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email.strip()):
        return False, "Invalid email format"
    return True, None


def validate_password(password):
    """Validate password strength."""
    if not password:
        return False, "Password is required"
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    return True, None


def validate_name(name):
    """Validate user name."""
    if not name or not name.strip():
        return False, "Name is required"
    if len(name.strip()) < 2:
        return False, "Name must be at least 2 characters"
    if len(name.strip()) > 100:
        return False, "Name must be less than 100 characters"
    return True, None


def validate_file(file, allowed_extensions=None, max_size_mb=None):
    """
    Validate an uploaded file.

    Checks:
    1. File exists and is not empty
    2. File extension is allowed (prevents malicious uploads)
    3. File size is within limits (prevents storage abuse)

    Cloud Security: These validations prevent:
    - Malicious file uploads (e.g., .exe, .sh)
    - Storage exhaustion attacks (huge files)
    - Path traversal attacks (handled by secure_filename)
    """
    if not file:
        return False, "No file provided"

    if file.filename == "":
        return False, "No file selected"

    # Check file extension
    if allowed_extensions is None:
        allowed_extensions = Config.ALLOWED_EXTENSIONS

    if isinstance(allowed_extensions, str):
        allowed_extensions = [ext.strip() for ext in allowed_extensions.split(",")]

    file_ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if file_ext not in allowed_extensions:
        return False, f"File type '.{file_ext}' not allowed. Allowed: {', '.join(allowed_extensions)}"

    # Check file size
    if max_size_mb is None:
        max_size_mb = Config.MAX_FILE_SIZE_MB

    max_size_bytes = max_size_mb * 1024 * 1024

    # Read file to check size, then reset position
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Reset to beginning for later reading

    if file_size == 0:
        return False, "File is empty"

    if file_size > max_size_bytes:
        return False, f"File size ({file_size / (1024*1024):.1f}MB) exceeds limit ({max_size_mb}MB)"

    return True, None


def validate_assignment_data(data):
    """
    Validate assignment creation/update data.

    Checks:
    - Required fields exist
    - Deadline is in the future (for creation)
    - Max marks is positive
    """
    errors = []

    if not data.get("title", "").strip():
        errors.append("Title is required")

    if not data.get("course_id"):
        errors.append("Course ID is required")

    if not data.get("deadline"):
        errors.append("Deadline is required")
    else:
        try:
            deadline = datetime.fromisoformat(data["deadline"].replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            errors.append("Invalid deadline format. Use ISO 8601 (e.g., 2025-12-31T23:59:59)")

    max_marks = data.get("max_marks", 100)
    if not isinstance(max_marks, int) or max_marks <= 0:
        errors.append("Max marks must be a positive integer")

    if errors:
        return False, errors
    return True, None


def validate_grade_data(data, max_marks):
    """
    Validate grading data.

    Checks:
    - Marks are within valid range (0 to max_marks)
    - Feedback is provided
    """
    errors = []

    marks = data.get("marks")
    if marks is None:
        errors.append("Marks are required")
    elif not isinstance(marks, (int, float)):
        errors.append("Marks must be a number")
    elif marks < 0:
        errors.append("Marks cannot be negative")
    elif marks > max_marks:
        errors.append(f"Marks ({marks}) cannot exceed maximum marks ({max_marks})")

    # Feedback is optional but encouraged
    feedback = data.get("feedback", "")

    if errors:
        return False, errors
    return True, None


def validate_deadline(deadline, allow_late=False):
    """
    Check if a submission is within the deadline.

    Cloud Concept: Always use SERVER-SIDE timestamps for deadline checking.
    Client-side clocks can be manipulated or in different timezones.

    Returns:
        tuple: (is_allowed, status)
        - (True, "SUBMITTED") if on time
        - (True, "LATE") if late but late submission is allowed
        - (False, "LATE") if late and late submission is not allowed
    """
    now = datetime.now(timezone.utc)

    # Ensure deadline is timezone-aware
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)

    if now <= deadline:
        return True, "SUBMITTED"
    elif allow_late:
        return True, "LATE"
    else:
        return False, "LATE"
