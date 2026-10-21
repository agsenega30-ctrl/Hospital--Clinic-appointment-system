import os
from datetime import datetime
from flask import Flask, render_template, jsonify, request, g, session
from config import Config
from db import db
from extensions import (
    limiter,
    generate_csrf_token,
    verify_csrf,
    get_current_user,
    get_unread_notification_count,
    get_app_timezone,
    get_now_local
)

# Import Blueprints
from routes.auth import auth_bp
from routes.public import public_bp
from routes.patient import patient_bp
from routes.doctor import doctor_bp
from routes.admin import admin_bp
from routes.appointments import appointments_bp
from routes.notifications import notifications_bp

def create_app(config_class=Config):
    """Application factory for Hospital Appointment System."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Database Connection
    db.init_app(app)

    # Initialize Rate Limiter
    limiter.init_app(app)

    # CSRF Protection Hook
    @app.before_request
    def handle_csrf():
        return verify_csrf()

    # Context Processors for Templates
    @app.context_processor
    def inject_global_template_context():
        return {
            "csrf_token": generate_csrf_token,
            "current_user": get_current_user(),
            "unread_count": get_unread_notification_count(),
            "db_connected": db.is_connected,
            "db_error": db.connection_error,
            "is_mock": db.is_mock,
            "now_year": get_now_local().year,
            "get_now_local": get_now_local,
            "app_name": "Antigravity Hospital"
        }

    # Register Custom Template Filters
    @app.template_filter("format_date")
    def format_date_filter(date_str):
        if not date_str:
            return ""
        try:
            dt = datetime.strptime(str(date_str), "%Y-%m-%d")
            return dt.strftime("%b %d, %Y")
        except Exception:
            return str(date_str)

    @app.template_filter("format_time")
    def format_time_filter(time_str):
        if not time_str:
            return ""
        try:
            t = datetime.strptime(str(time_str), "%H:%M")
            return t.strftime("%I:%M %p")
        except Exception:
            return str(time_str)

    # Register Blueprints
    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(doctor_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(appointments_bp)
    app.register_blueprint(notifications_bp)

    # Register CLI Commands
    @app.cli.command("seed-db")
    def seed_db_command():
        """Seed initial admin, specializations, and demo records."""
        from seed import run_seed
        run_seed()

    # Error Handlers
    @app.errorhandler(400)
    def handle_bad_request(e):
        if request.is_json:
            return jsonify({"success": False, "error": "Bad request"}), 400
        return render_template("shared/error.html", code=400, title="Bad Request", message="The request could not be processed."), 400

    @app.errorhandler(403)
    def handle_forbidden(e):
        if request.is_json:
            return jsonify({"success": False, "error": "Access forbidden"}), 403
        return render_template("shared/error.html", code=403, title="Access Forbidden", message="You do not have permission to view or modify this resource."), 403

    @app.errorhandler(404)
    def handle_not_found(e):
        if request.is_json:
            return jsonify({"success": False, "error": "Resource not found"}), 404
        return render_template("shared/404.html"), 404

    @app.errorhandler(429)
    def handle_ratelimit_exceeded(e):
        if request.is_json:
            return jsonify({"success": False, "error": "Rate limit exceeded. Please wait a moment."}), 429
        return render_template("shared/error.html", code=429, title="Too Many Requests", message="You have made too many requests. Please slow down and try again shortly."), 429

    @app.errorhandler(500)
    def handle_server_error(e):
        if request.is_json:
            return jsonify({"success": False, "error": "An internal server error occurred"}), 500
        return render_template("shared/error.html", code=500, title="Server Error", message="A temporary server error occurred. Our technical staff has been notified."), 500

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
