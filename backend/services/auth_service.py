"""
Authentication Service
======================
Handles user registration, login, and JWT token management.

Cloud Concept: In production, this would integrate with cloud authentication
providers like Firebase Auth, AWS Cognito, or Supabase Auth. Locally, we use
JWT tokens with werkzeug password hashing (bcrypt-equivalent).
"""

from datetime import datetime, timezone, timedelta
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from backend.models.database import db, User
from backend.config import Config


class AuthService:
    """Service class for authentication operations."""

    @staticmethod
    def register(name, email, password, role="student"):
        """
        Register a new user.

        Args:
            name: Full name of the user
            email: Email address (must be unique)
            password: Plain text password (will be hashed)
            role: User role — 'student', 'teacher', or 'admin'

        Returns:
            dict: Success response with user data, or error response

        Cloud Concept: In cloud deployment, this would create a user in
        Firebase Auth / Cognito and sync to the database.
        """
        # Validate inputs
        if not name or not email or not password:
            return {"error": "Name, email, and password are required"}, 400

        if len(password) < 6:
            return {"error": "Password must be at least 6 characters"}, 400

        if role not in ("student", "teacher", "admin"):
            return {"error": "Invalid role. Must be student, teacher, or admin"}, 400

        # Check if email already exists
        existing_user = User.query.filter_by(email=email.lower().strip()).first()
        if existing_user:
            return {"error": "Email already registered"}, 409

        # Create new user with hashed password
        new_user = User(
            name=name.strip(),
            email=email.lower().strip(),
            password_hash=generate_password_hash(password),
            role=role,
        )
        db.session.add(new_user)
        db.session.commit()

        # Generate JWT token
        token = AuthService._generate_token(new_user)

        return {
            "message": "Registration successful",
            "user": new_user.to_dict(),
            "token": token,
        }, 201

    @staticmethod
    def login(email, password):
        """
        Authenticate a user and return a JWT token.

        Args:
            email: User's email address
            password: User's password

        Returns:
            dict: Success response with token, or error response
        """
        if not email or not password:
            return {"error": "Email and password are required"}, 400

        # Find user by email
        user = User.query.filter_by(email=email.lower().strip()).first()

        if not user or not check_password_hash(user.password_hash, password):
            return {"error": "Invalid email or password"}, 401

        # Generate JWT token
        token = AuthService._generate_token(user)

        return {
            "message": "Login successful",
            "user": user.to_dict(),
            "token": token,
        }, 200

    @staticmethod
    def get_user_by_id(user_id):
        """Get user details by ID."""
        user = db.session.get(User, user_id)
        if not user:
            return {"error": "User not found"}, 404
        return {"user": user.to_dict()}, 200

    @staticmethod
    def _generate_token(user):
        """
        Generate a JWT access token.

        The token contains the user's ID and role, enabling stateless
        authentication. In cloud deployment, this would be handled by
        Firebase Auth tokens or AWS Cognito JWTs.
        """
        payload = {
            "user_id": user.id,
            "email": user.email,
            "role": user.role,
            "name": user.name,
            "exp": datetime.now(timezone.utc) + Config.JWT_ACCESS_TOKEN_EXPIRES,
            "iat": datetime.now(timezone.utc),
        }
        token = jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm="HS256")
        return token

    @staticmethod
    def verify_token(token):
        """
        Verify and decode a JWT token.

        Returns:
            dict: Decoded token payload, or None if invalid
        """
        try:
            payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
