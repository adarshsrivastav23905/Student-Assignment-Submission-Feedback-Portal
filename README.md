# Student Assignment Submission & Feedback Portal

A cloud-ready student assignment portal built with Python, Flask, SQLAlchemy, and a lightweight local storage backend that mirrors common cloud patterns such as object storage, secure file access, and role-based authorization.

## Project Overview

This application allows:

- Students to register, log in, enroll in courses, submit assignments, and view feedback.
- Teachers to create courses and assignments, review submissions, grade work, and provide feedback.
- Admins to manage the overall environment and access protected routes.
- A REST API to support a web-based frontend and future cloud deployment integration.

The project demonstrates cloud concepts such as:

- Cloud-hosted application architecture
- Cloud authentication using JWT
- Role-based authorization
- Cloud-style database persistence
- Object/file storage abstraction
- Secure file upload and download flow
- Scalable REST API design
- Local free-tier friendly deployment patterns

## Tech Stack

- Python 3.11+
- Flask
- Flask-SQLAlchemy
- SQLite for local development and testing
- JWT authentication
- Werkzeug password hashing
- HTML, CSS, and JavaScript frontend
- Pytest for automated tests

## Project Structure

```text
backend/
  app.py
  config.py
  middleware/
  models/
  routes/
  services/
  utils/
frontend/
  index.html
  css/
  js/
  
 tests/
  test_app.py
requirements.txt
.env.example
README.md
```

## Features

### Authentication and Authorization

- User registration and login
- JWT-based session management
- Role-based access control for students, teachers, and admins
- Protected routes using middleware decorators

### Course and Assignment Management

- Create and manage courses
- Create assignments with due dates and rules
- Restrict access to teacher-owned courses
- List assignments for enrolled students

### Submission Handling

- File upload validation
- Storage abstraction for uploaded files
- Download submitted files
- Prevent late submission when disallowed
- Allow resubmission if enabled

### Feedback and Grading

- Teacher grading interface
- Marks validation against assignment maximum
- Feedback saved in database
- Student feedback retrieval endpoint

## Local Setup

1. Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

2. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

3. Create environment variables if needed by copying the example file:

```bash
copy .env.example .env
```

4. Start the app:

```bash
python -m flask --app backend.app run
```

Alternative:

```bash
python run.py
```

5. Open the frontend in a browser at:

```text
http://localhost:5000/
```

## Running Tests

```bash
python -m pytest -q
```

The project includes automated tests covering:

- health checks
- user registration and login
- teacher assignment creation
- student submission upload
- grading workflow

## Cloud Deployment Notes

This implementation uses a local filesystem storage layer as a free-tier-friendly substitute for a production cloud object store. In a production environment, the same service layer can be swapped for:

- AWS S3
- Azure Blob Storage
- Google Cloud Storage

The code is structured so the storage abstraction remains consistent while the provider changes.

## Security Considerations

- No hardcoded passwords, API keys, secrets, or credentials are included in source files.
- JWT tokens are used for authenticated API access.
- File validation enforces extension and size constraints.
- Server-side deadline checks prevent client-side tampering.
- Role checks restrict access to sensitive endpoints.

## License

This project is intended for academic and educational use in the context of cloud computing coursework.
