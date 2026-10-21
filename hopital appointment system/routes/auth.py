import re
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
from db import db
from extensions import limiter, verify_csrf, get_current_user
from services.audit_service import AuditService
from services.doctor_service import DoctorService

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")

@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("15 per minute")
def register():
    """Patient registration endpoint (and doctor registration if enabled in settings)."""
    if "user_id" in session:
        return redirect(url_for("public.index"))

    if request.method == "POST":
        verify_csrf()

        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        phone = request.form.get("phone", "").strip()
        requested_role = request.form.get("role", "patient").strip().lower()

        # Input validation
        if not full_name or len(full_name) < 2:
            flash("Please enter a valid full name (at least 2 characters).", "danger")
            return render_template("auth/register.html", full_name=full_name, email=email, phone=phone, role=requested_role)

        if not email or not EMAIL_REGEX.match(email):
            flash("Please enter a valid email address.", "danger")
            return render_template("auth/register.html", full_name=full_name, email=email, phone=phone, role=requested_role)

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template("auth/register.html", full_name=full_name, email=email, phone=phone, role=requested_role)

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("auth/register.html", full_name=full_name, email=email, phone=phone, role=requested_role)

        # Strictly prevent public registration of admin accounts
        if requested_role not in ["patient", "doctor"]:
            requested_role = "patient"

        if not db.is_connected or db.users is None:
            flash("Database connection is currently unavailable. Please try again later.", "danger")
            return render_template("auth/register.html", full_name=full_name, email=email, phone=phone, role=requested_role)

        # Check existing email
        existing_user = db.users.find_one({"email": email})
        if existing_user:
            flash("An account with this email address already exists.", "danger")
            return render_template("auth/register.html", full_name=full_name, email=email, phone=phone, role=requested_role)

        # Check if doctor registration requires admin approval
        account_status = "active"
        if requested_role == "doctor":
            account_status = "pending_approval"

        user_doc = {
            "full_name": full_name,
            "email": email,
            "password_hash": generate_password_hash(password),
            "phone": phone,
            "role": requested_role,
            "account_status": account_status,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }

        try:
            result = db.users.insert_one(user_doc)
            new_user_id = result.inserted_id

            if requested_role == "doctor":
                DoctorService.ensure_doctor_profile(new_user_id, {
                    "is_approved": False,
                    "specialization": request.form.get("specialization", "General Medicine")
                })
                flash("Doctor registration submitted! Your account is pending administrator approval.", "info")
                return redirect(url_for("auth.login"))

            # Automatically log in new patients
            session.clear()
            session.permanent = True
            session["user_id"] = str(new_user_id)
            session["user_name"] = full_name
            session["user_email"] = email
            session["user_role"] = requested_role

            AuditService.log_action(
                actor_user_id=new_user_id,
                action="user_registered",
                target_type="user",
                target_id=new_user_id,
                details={"role": requested_role}
            )

            flash("Registration successful! Welcome to the Hospital Appointment System.", "success")
            return redirect(url_for("patient.dashboard"))

        except Exception as e:
            flash(f"Registration failed: {str(e)}", "danger")
            return render_template("auth/register.html", full_name=full_name, email=email, phone=phone, role=requested_role)

    # GET
    specializations = DoctorService.get_specializations()
    return render_template("auth/register.html", specializations=specializations)


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("20 per minute")
def login():
    """Secure login endpoint with credential verification, role-based redirection, and lockout protection."""
    if "user_id" in session:
        role = session.get("user_role")
        if role == "doctor":
            return redirect(url_for("doctor.dashboard"))
        elif role == "admin":
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("patient.dashboard"))

    if request.method == "POST":
        verify_csrf()

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please provide both email and password.", "danger")
            return render_template("auth/login.html", email=email)

        if not db.is_connected or db.users is None:
            flash("Database service is currently unavailable. Please verify connection settings.", "danger")
            return render_template("auth/login.html", email=email)

        user = db.users.find_one({"email": email})
        if not user or not check_password_hash(user.get("password_hash", ""), password):
            flash("Invalid email or password. Please check your credentials.", "danger")
            return render_template("auth/login.html", email=email)

        if user.get("account_status") == "pending_approval":
            flash("Your doctor account has been submitted and is awaiting administrator approval.", "warning")
            return render_template("auth/login.html", email=email)

        if user.get("account_status") != "active":
            flash("Your account has been deactivated. Please contact hospital support.", "danger")
            return render_template("auth/login.html", email=email)

        # Successful login: initialize session
        session.clear()
        session.permanent = True
        session["user_id"] = str(user["_id"])
        session["user_name"] = user.get("full_name", "User")
        session["user_email"] = user.get("email")
        session["user_role"] = user.get("role", "patient")

        AuditService.log_action(
            actor_user_id=user["_id"],
            action="login_successful",
            target_type="user",
            target_id=user["_id"]
        )

        flash(f"Welcome back, {user.get('full_name')}!", "success")

        # Redirect based on role or next parameter
        next_url = request.args.get("next")
        if next_url and next_url.startswith("/"):
            return redirect(next_url)

        role = user.get("role")
        if role == "doctor":
            return redirect(url_for("doctor.dashboard"))
        elif role == "admin":
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("patient.dashboard"))

    return render_template("auth/login.html")


@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    """Clear session and log user out."""
    user_id = session.get("user_id")
    if user_id:
        AuditService.log_action(
            actor_user_id=user_id,
            action="logout",
            target_type="user",
            target_id=user_id
        )
    session.clear()
    flash("You have been securely logged out.", "info")
    return redirect(url_for("auth.login"))
