import io
import uuid

import pytest

from backend.app import create_app
from backend.config import TestingConfig


@pytest.fixture
def client():
    app = create_app(config_class=TestingConfig)
    with app.test_client() as client:
        yield client


def get_token(client, email, password):
    response = client.post(
        "/api/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.get_data(as_text=True)
    return response.get_json()["token"]


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"


def test_user_registration_and_login(client):
    unique_email = f"teststudent_{uuid.uuid4().hex[:8]}@example.com"

    response = client.post(
        "/api/register",
        json={
            "name": "Test Student",
            "email": unique_email,
            "password": "student123",
            "role": "student",
        },
    )
    assert response.status_code == 201

    login = client.post(
        "/api/login",
        json={"email": unique_email, "password": "student123"},
    )
    assert login.status_code == 200
    token = login.get_json()["token"]
    assert token


def test_student_dashboard_authorization(client):
    teacher_token = get_token(client, "teacher@example.com", "teacher123")
    response = client.get(
        "/api/dashboard/student",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert response.status_code == 403


def test_teacher_can_create_assignment(client):
    token = get_token(client, "teacher@example.com", "teacher123")
    response = client.post(
        "/api/assignments",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "course_id": 1,
            "title": "Cloud Test Assignment",
            "description": "Submit a short cloud note.",
            "deadline": "2035-12-31T23:59:59",
            "max_marks": 80,
            "allowed_extensions": "pdf,docx",
            "max_file_size_mb": 5,
            "allow_late_submission": True,
            "allow_resubmission": True,
        },
    )
    assert response.status_code == 201, response.get_data(as_text=True)
    data = response.get_json()
    assert data["assignment"]["title"] == "Cloud Test Assignment"


def test_student_can_submit_assignment(client):
    token = get_token(client, "student@example.com", "student123")
    file_obj = io.BytesIO(b"cloud assignment content")
    file_obj.name = "sample.pdf"

    response = client.post(
        "/api/assignments/1/submit",
        headers={"Authorization": f"Bearer {token}"},
        data={"file": (file_obj, "sample.pdf")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 201, response.get_data(as_text=True)
    payload = response.get_json()
    assert payload["message"] in {"Assignment submitted successfully", "Assignment resubmitted successfully"}


def test_teacher_can_download_submission_file(client):
    student_token = get_token(client, "student@example.com", "student123")
    teacher_token = get_token(client, "teacher@example.com", "teacher123")

    file_obj = io.BytesIO(b"downloadable file content")
    file_obj.name = "download-test.pdf"
    submit = client.post(
        "/api/assignments/1/submit",
        headers={"Authorization": f"Bearer {student_token}"},
        data={"file": (file_obj, "download-test.pdf")},
        content_type="multipart/form-data",
    )
    assert submit.status_code == 201, submit.get_data(as_text=True)
    submission_id = submit.get_json()["submission"]["id"]

    download = client.get(
        f"/api/submissions/{submission_id}/download",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert download.status_code == 200, download.get_data(as_text=True)
    assert b"downloadable file content" in download.data


def test_teacher_can_grade_submission(client):
    student_token = get_token(client, "student@example.com", "student123")
    teacher_token = get_token(client, "teacher@example.com", "teacher123")

    file_obj = io.BytesIO(b"second submission")
    file_obj.name = "second.pdf"
    submit = client.post(
        "/api/assignments/1/submit",
        headers={"Authorization": f"Bearer {student_token}"},
        data={"file": (file_obj, "second.pdf")},
        content_type="multipart/form-data",
    )
    submission_id = submit.get_json()["submission"]["id"]

    grade = client.post(
        f"/api/submissions/{submission_id}/grade",
        headers={"Authorization": f"Bearer {teacher_token}"},
        json={"marks": 85, "feedback": "Strong cloud reasoning and structure."},
    )
    assert grade.status_code == 200, grade.get_data(as_text=True)
    body = grade.get_json()
    assert body["submission"]["status"] == "GRADED"


def test_auth_alias_routes_work(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "teacher@example.com", "password": "teacher123"},
    )
    assert response.status_code == 200, response.get_data(as_text=True)
    assert response.get_json()["token"]
