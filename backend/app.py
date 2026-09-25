"""
Cloud-Based Student Assignment Submission & Feedback Portal
============================================================
Main Flask Application Entry Point

This is the REST API backend that handles:
- Authentication & Authorization (JWT + Role-Based Access)
- Assignment CRUD (Create, Read, Update, Delete)
- File Upload to Cloud Object Storage
- Submission Management & Deadline Validation
- Teacher Grading & Student Feedback
- Dashboard Aggregation

Cloud Computing Concepts Demonstrated:
- Cloud Database (SQLite locally → PostgreSQL/Firestore in cloud)
- Cloud Object Storage (local filesystem → S3/Firebase Storage)
- REST API Architecture (Client-Server model)
- Authentication & RBAC (JWT tokens, role-based middleware)
- Environment Variables (secrets management)
- CORS (Cross-Origin Resource Sharing for frontend-backend separation)

Author: Adarsh Srivastav
Course: Cloud Computing
"""

import os
import sys
import logging
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import get_config
from backend.models.database import init_db
from backend.routes.auth_routes import auth_bp
from backend.routes.assignment_routes import assignment_bp
from backend.routes.submission_routes import submission_bp
from backend.routes.dashboard_routes import dashboard_bp


def create_app(config_class=None):
    """
    Application Factory Pattern — creates and configures the Flask app.
    
    This pattern is an industry best practice that allows:
    - Multiple configurations (dev, test, prod)
    - Clean testing with isolated app instances
    - Cloud deployment flexibility
    """
    app = Flask(__name__, static_folder=None)

    # Load configuration
    if config_class is None:
        config_class = get_config()
    app.config.from_object(config_class)

    # Configure SQLAlchemy
    app.config["SQLALCHEMY_DATABASE_URI"] = config_class.DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["MAX_CONTENT_LENGTH"] = config_class.MAX_FILE_SIZE_BYTES

    # --- CORS Configuration ---
    # Cloud Concept: CORS allows the frontend (hosted on a different domain/port)
    # to make API calls to the backend. Essential for cloud-deployed SPAs.
    CORS(app, resources={
        r"/api/*": {
            "origins": config_class.CORS_ORIGINS,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True,
        }
    })

    # --- Logging Configuration ---
    # Cloud Concept: Structured logging is essential for cloud monitoring.
    # In production, logs go to CloudWatch, Stackdriver, or similar.
    logging.basicConfig(
        level=getattr(logging, config_class.LOG_LEVEL),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger(__name__)

    # --- Initialize Database ---
    init_db(app)

    # --- Register Route Blueprints ---
    app.register_blueprint(auth_bp)
    app.register_blueprint(assignment_bp)
    app.register_blueprint(submission_bp)
    app.register_blueprint(dashboard_bp)

    # --- Serve Frontend Static Files ---
    frontend_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend"
    )

    @app.route("/")
    def serve_frontend():
        """Serve the main frontend page."""
        return send_from_directory(frontend_dir, "index.html")

    @app.route("/<path:path>")
    def serve_static(path):
        """Serve frontend static files (CSS, JS, images)."""
        # Check frontend directory first
        full_path = os.path.join(frontend_dir, path)
        if os.path.exists(full_path):
            return send_from_directory(frontend_dir, path)
        # If not found, serve index.html for SPA routing
        return send_from_directory(frontend_dir, "index.html")

    # --- Health Check Endpoint ---
    @app.route("/api/health", methods=["GET"])
    def health_check():
        """
        Health check endpoint for cloud monitoring.
        Used by load balancers and container orchestrators to verify
        the application is running correctly.
        """
        return jsonify({
            "status": "healthy",
            "service": "Cloud Assignment Portal API",
            "version": "1.0.0",
        }), 200

    # --- Global Error Handlers ---
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(413)
    def file_too_large(error):
        return jsonify({
            "error": f"File too large. Maximum size: {config_class.MAX_FILE_SIZE_MB}MB"
        }), 413

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({"error": "Internal server error. Please try again later."}), 500

    logger.info("🚀 Cloud Assignment Portal API started!")
    logger.info(f"   Database: {config_class.DATABASE_URL}")
    logger.info(f"   Storage:  {config_class.STORAGE_BACKEND}")
    logger.info(f"   Debug:    {config_class.DEBUG}")

    return app


# --- Entry Point ---
if __name__ == "__main__":
    app = create_app()
    config = get_config()
    print(f"\n🌐 Server running at http://localhost:{config.PORT}")
    print(f"📖 API Health: http://localhost:{config.PORT}/api/health")
    print(f"🖥️  Frontend:   http://localhost:{config.PORT}/\n")
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
