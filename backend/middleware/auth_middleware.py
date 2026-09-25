"""
Authentication Middleware
=========================
JWT token verification middleware for protecting API routes.

Cloud Concept: This implements AUTHORIZATION — deciding what each
authenticated user is allowed to do based on their role.

Authentication = "Who are you?" (handled by login/JWT)
Authorization  = "What can you do?" (handled by this middleware)
"""

from functools import wraps
from flask import request, jsonify, g
from backend.services.auth_service import AuthService


def require_auth(f):
    """
    Decorator that requires a valid JWT token.
    Extracts user info and stores it in Flask's `g` object.

    Usage:
        @app.route('/protected')
        @require_auth
        def protected_route():
            user_id = g.user_id
            role = g.user_role
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Extract token from Authorization header: "Bearer <token>"
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]

        if not token:
            return jsonify({"error": "Authentication required. Please provide a valid token."}), 401

        # Verify the token
        payload = AuthService.verify_token(token)
        if not payload:
            return jsonify({"error": "Token is invalid or expired. Please login again."}), 401

        # Store user info in Flask's global context for route handlers
        g.user_id = payload["user_id"]
        g.user_email = payload["email"]
        g.user_role = payload["role"]
        g.user_name = payload["name"]

        return f(*args, **kwargs)

    return decorated


def require_role(*roles):
    """
    Decorator that requires the authenticated user to have a specific role.
    Must be used AFTER @require_auth.

    This is ROLE-BASED ACCESS CONTROL (RBAC):
    - Students can only access student routes
    - Teachers can only access teacher routes
    - Admins can access everything

    Usage:
        @app.route('/teacher-only')
        @require_auth
        @require_role('teacher', 'admin')
        def teacher_route():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if g.user_role not in roles:
                return jsonify({
                    "error": f"Access denied. Required role: {', '.join(roles)}. Your role: {g.user_role}"
                }), 403
            return f(*args, **kwargs)
        return decorated
    return decorator
