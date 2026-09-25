"""
Authentication Routes
=====================
Handles user registration, login, and profile endpoints.

Endpoints:
    POST /api/register  — Register a new student or teacher
    POST /api/login     — Login and receive JWT token
    GET  /api/profile   — Get current user's profile (protected)
    GET  /api/users     — List all users (admin only)
"""

from flask import Blueprint, request, jsonify, g
from backend.services.auth_service import AuthService
from backend.middleware.auth_middleware import require_auth, require_role
from backend.utils.validators import validate_email, validate_password, validate_name

# Create Blueprint for auth routes
auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/api/register", methods=["POST"])
@auth_bp.route("/api/auth/register", methods=["POST"])
def register():
    """
    Register a new user.

    Request Body (JSON):
        {
            "name": "Alice Smith",
            "email": "alice@example.com",
            "password": "securepass123",
            "role": "student"  // "student" or "teacher"
        }

    Response (201):
        {
            "message": "Registration successful",
            "user": { ... },
            "token": "jwt_token_here"
        }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    # Validate inputs
    valid, err = validate_name(data.get("name", ""))
    if not valid:
        return jsonify({"error": err}), 400

    valid, err = validate_email(data.get("email", ""))
    if not valid:
        return jsonify({"error": err}), 400

    valid, err = validate_password(data.get("password", ""))
    if not valid:
        return jsonify({"error": err}), 400

    # Register the user
    result, status_code = AuthService.register(
        name=data["name"],
        email=data["email"],
        password=data["password"],
        role=data.get("role", "student"),
    )

    return jsonify(result), status_code


@auth_bp.route("/api/login", methods=["POST"])
@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    """
    Login and receive a JWT token.

    Request Body (JSON):
        {
            "email": "alice@example.com",
            "password": "securepass123"
        }

    Response (200):
        {
            "message": "Login successful",
            "user": { ... },
            "token": "jwt_token_here"
        }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    result, status_code = AuthService.login(
        email=data.get("email", ""),
        password=data.get("password", ""),
    )

    return jsonify(result), status_code


@auth_bp.route("/api/profile", methods=["GET"])
@auth_bp.route("/api/auth/profile", methods=["GET"])
@require_auth
def get_profile():
    """
    Get current user's profile.
    Requires: Valid JWT token in Authorization header.

    Response (200):
        {
            "user": { ... }
        }
    """
    result, status_code = AuthService.get_user_by_id(g.user_id)
    return jsonify(result), status_code


@auth_bp.route("/api/logout", methods=["POST"])
@auth_bp.route("/api/auth/logout", methods=["POST"])
@require_auth
def logout():
    """Client-side logout endpoint for explicit session closure."""
    return jsonify({"message": "Logged out successfully"}), 200


@auth_bp.route("/api/users", methods=["GET"])
@require_auth
@require_role("admin")
def list_users():
    """
    List all users (admin only).
    Demonstrates RBAC — only admins can see all users.
    """
    from backend.models.database import User
    users = User.query.all()
    return jsonify({"users": [u.to_dict() for u in users]}), 200
