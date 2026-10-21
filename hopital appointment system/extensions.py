import secrets
from functools import wraps
from datetime import datetime
import pytz
from flask import session, request, abort, redirect, url_for, flash, g, jsonify, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from bson import ObjectId
from db import db

# Initialize Flask-Limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["500 per day", "120 per hour"],
    storage_uri="memory://",
)

def get_app_timezone():
    """Return configured application pytz timezone."""
    tz_name = current_app.config.get("APP_TIMEZONE", "Asia/Kolkata")
    try:
        return pytz.timezone(tz_name)
    except Exception:
        return pytz.timezone("Asia/Kolkata")

def get_now_local():
    """Get current datetime localized to APP_TIMEZONE."""
    tz = get_app_timezone()
    return datetime.now(tz)

def generate_csrf_token():
    """Generate or retrieve CSRF token stored in session."""
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_hex(32)
    return session["_csrf_token"]

def verify_csrf():
    """Verify CSRF token for mutating HTTP methods."""
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return

    # Check for CSRF exempt flag on view functions
    if getattr(current_app.view_functions.get(request.endpoint, None), "_csrf_exempt", False):
        return

    expected_token = session.get("_csrf_token")
    if not expected_token:
        if request.is_json or request.headers.get("Accept") == "application/json":
            return jsonify({"success": False, "error": "CSRF session token missing or expired"}), 403
        flash("Your session or security token has expired. Please try again.", "danger")
        abort(403)

    # Check header or form body
    received_token = request.headers.get("X-CSRFToken") or request.form.get("csrf_token")
    if not received_token or not secrets.compare_digest(received_token, expected_token):
        if request.is_json or request.headers.get("Accept") == "application/json":
            return jsonify({"success": False, "error": "Invalid or missing CSRF security token"}), 403
        flash("Security validation failed (CSRF mismatch). Please try again.", "danger")
        abort(403)

def csrf_exempt(view_func):
    """Mark a view function as exempt from CSRF validation."""
    view_func._csrf_exempt = True
    return view_func

def login_required(f):
    """Decorator to require authenticated session."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            if request.is_json or request.headers.get("Accept") == "application/json":
                return jsonify({"success": False, "error": "Authentication required"}), 401
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        
        # Verify user still exists in database
        if db.is_connected and db.users is not None:
            user = db.users.find_one({"_id": ObjectId(session["user_id"])})
            if not user or user.get("account_status") != "active":
                session.clear()
                flash("Your account is either inactive or no longer exists.", "danger")
                return redirect(url_for("auth.login"))
            g.current_user = user
        return f(*args, **kwargs)
    return decorated_function

def roles_required(*roles):
    """Decorator to enforce role-based access control."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                if request.is_json or request.headers.get("Accept") == "application/json":
                    return jsonify({"success": False, "error": "Authentication required"}), 401
                flash("Please log in to access this page.", "warning")
                return redirect(url_for("auth.login", next=request.path))

            user_role = session.get("user_role")
            if user_role not in roles:
                if request.is_json or request.headers.get("Accept") == "application/json":
                    return jsonify({"success": False, "error": "Access forbidden: insufficient role permissions"}), 403
                flash("You do not have permission to access that resource.", "danger")
                return redirect(url_for("public.index"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_current_user():
    """Helper to retrieve active user document from database."""
    if "user_id" not in session:
        return None
    if hasattr(g, "current_user") and g.current_user:
        return g.current_user
    if db.is_connected and db.users is not None:
        try:
            user = db.users.find_one({"_id": ObjectId(session["user_id"])})
            g.current_user = user
            return user
        except Exception:
            return None
    return None

def get_unread_notification_count():
    """Retrieve count of unread notifications for current user."""
    user_id = session.get("user_id")
    if not user_id or not db.is_connected or db.notifications is None:
        return 0
    try:
        return db.notifications.count_documents({
            "recipient_user_id": ObjectId(user_id),
            "is_read": False
        })
    except Exception:
        return 0
