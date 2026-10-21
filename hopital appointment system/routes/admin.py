from datetime import datetime, timedelta, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from bson import ObjectId
from werkzeug.security import generate_password_hash
from db import db
from extensions import login_required, roles_required, verify_csrf, get_now_local
from services.doctor_service import DoctorService
from services.appointment_service import AppointmentService
from services.audit_service import AuditService

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.before_request
@login_required
@roles_required("admin")
def enforce_admin_role():
    """Ensure all administrative routes are strictly protected and restricted to administrators."""
    pass

@admin_bp.route("/dashboard")
def dashboard():
    """Admin dashboard overview: high-level metrics, pending approvals, and chart statistics."""
    total_patients = 0
    total_doctors = 0
    total_appointments = 0
    pending_appointments = 0
    cancelled_appointments = 0
    pending_doctor_approvals = 0

    if db.is_connected and db.users is not None:
        total_patients = db.users.count_documents({"role": "patient"})
        total_doctors = db.users.count_documents({"role": "doctor"})
        pending_doctor_approvals = db.users.count_documents({"role": "doctor", "account_status": "pending_approval"})
        total_appointments = db.appointments.count_documents({})
        pending_appointments = db.appointments.count_documents({"status": "pending"})
        cancelled_appointments = db.appointments.count_documents({"status": "cancelled"})

    # Fetch pending doctor approval list
    pending_doctors = []
    if pending_doctor_approvals > 0 and db.users is not None:
        cursor = db.users.find({"role": "doctor", "account_status": "pending_approval"}).limit(5)
        for doc in cursor:
            prof = db.doctor_profiles.find_one({"user_id": doc["_id"]})
            doc["profile"] = prof
            pending_doctors.append(doc)

    # Recent appointments
    recent_appointments = []
    if db.appointments is not None:
        cursor = db.appointments.find().sort("created_at", -1).limit(6)
        for app in cursor:
            app["patient"] = db.users.find_one({"_id": app["patient_id"]})
            app["doctor"] = db.users.find_one({"_id": app["doctor_id"]})
            recent_appointments.append(app)

    return render_template(
        "admin/dashboard.html",
        stats={
            "patients": total_patients,
            "doctors": total_doctors,
            "appointments": total_appointments,
            "pending": pending_appointments,
            "cancelled": cancelled_appointments,
            "pending_approvals": pending_doctor_approvals
        },
        pending_doctors=pending_doctors,
        recent_appointments=recent_appointments
    )

@admin_bp.route("/doctors", methods=["GET", "POST"])
def doctor_management():
    """Manage doctor accounts: list, create new doctor, activate, deactivate, approve, or reject."""
    if request.method == "POST":
        verify_csrf()
        action = request.form.get("action")

        if action == "create":
            full_name = request.form.get("full_name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            phone = request.form.get("phone", "").strip()
            specialization = request.form.get("specialization", "General Medicine")
            fee = float(request.form.get("consultation_fee", 500.0))

            if not full_name or not email or len(password) < 6:
                flash("Please provide valid details (password must be at least 6 characters).", "danger")
                return redirect(url_for("admin.doctor_management"))

            existing = db.users.find_one({"email": email})
            if existing:
                flash("A user with this email already exists.", "danger")
                return redirect(url_for("admin.doctor_management"))

            doc_user = {
                "full_name": full_name,
                "email": email,
                "password_hash": generate_password_hash(password),
                "phone": phone,
                "role": "doctor",
                "account_status": "active",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            res = db.users.insert_one(doc_user)
            DoctorService.ensure_doctor_profile(res.inserted_id, {
                "specialization": specialization,
                "consultation_fee": fee,
                "is_approved": True
            })

            AuditService.log_action(
                actor_user_id=session["user_id"],
                action="admin_created_doctor",
                target_type="user",
                target_id=res.inserted_id,
                details={"email": email, "specialization": specialization}
            )

            flash(f"Doctor account for Dr. {full_name} created successfully!", "success")
            return redirect(url_for("admin.doctor_management"))

        elif action in ["approve", "reject", "activate", "deactivate"]:
            target_user_id = ObjectId(request.form.get("user_id"))
            if action == "approve":
                db.users.update_one({"_id": target_user_id}, {"$set": {"account_status": "active"}})
                db.doctor_profiles.update_one({"user_id": target_user_id}, {"$set": {"is_approved": True}})
                flash("Doctor registration approved successfully.", "success")
            elif action == "reject":
                db.users.update_one({"_id": target_user_id}, {"$set": {"account_status": "inactive"}})
                db.doctor_profiles.update_one({"user_id": target_user_id}, {"$set": {"is_approved": False}})
                flash("Doctor registration rejected.", "warning")
            elif action == "deactivate":
                db.users.update_one({"_id": target_user_id}, {"$set": {"account_status": "inactive"}})
                flash("Doctor account deactivated.", "info")
            elif action == "activate":
                db.users.update_one({"_id": target_user_id}, {"$set": {"account_status": "active"}})
                flash("Doctor account activated.", "success")

            AuditService.log_action(
                actor_user_id=session["user_id"],
                action=f"doctor_{action}",
                target_type="user",
                target_id=target_user_id
            )
            return redirect(url_for("admin.doctor_management"))

    # GET doctors list
    search = request.args.get("search", "").strip()
    status_filter = request.args.get("status", "all").strip()

    query = {"role": "doctor"}
    if search:
        query["$or"] = [
            {"full_name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    if status_filter != "all":
        query["account_status"] = status_filter

    doctors_cursor = db.users.find(query).sort("created_at", -1)
    doctors = []
    for doc in doctors_cursor:
        prof = db.doctor_profiles.find_one({"user_id": doc["_id"]}) or DoctorService.get_default_profile(doc["_id"])
        doc["profile"] = prof
        doctors.append(doc)

    specializations = DoctorService.get_specializations()

    return render_template(
        "admin/doctors.html",
        doctors=doctors,
        specializations=specializations,
        search=search,
        status_filter=status_filter
    )

@admin_bp.route("/patients")
def patient_management():
    """View and manage patient accounts with status toggling."""
    search = request.args.get("search", "").strip()
    status_filter = request.args.get("status", "all").strip()
    page = int(request.args.get("page", 1))
    per_page = 15

    query = {"role": "patient"}
    if search:
        query["$or"] = [
            {"full_name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
            {"phone": {"$regex": search, "$options": "i"}}
        ]
    if status_filter != "all":
        query["account_status"] = status_filter

    total = db.users.count_documents(query) if db.users is not None else 0
    patients = []
    if db.users is not None:
        cursor = (
            db.users.find(query)
            .sort("created_at", -1)
            .skip((page - 1) * per_page)
            .limit(per_page)
        )
        for p in cursor:
            # count bookings
            p["appointment_count"] = db.appointments.count_documents({"patient_id": p["_id"]})
            patients.append(p)

    total_pages = max(1, (total + per_page - 1) // per_page)

    return render_template(
        "admin/patients.html",
        patients=patients,
        search=search,
        status_filter=status_filter,
        current_page=page,
        total_pages=total_pages,
        total=total
    )

@admin_bp.route("/patients/<patient_id>/toggle-status", methods=["POST"])
def toggle_patient_status(patient_id):
    """Activate or deactivate a patient account."""
    verify_csrf()
    p_oid = ObjectId(patient_id)
    patient = db.users.find_one({"_id": p_oid, "role": "patient"})
    if not patient:
        flash("Patient not found.", "warning")
        return redirect(url_for("admin.patient_management"))

    new_status = "inactive" if patient.get("account_status") == "active" else "active"
    db.users.update_one({"_id": p_oid}, {"$set": {"account_status": new_status, "updated_at": datetime.now(timezone.utc)}})

    AuditService.log_action(
        actor_user_id=session["user_id"],
        action=f"patient_status_{new_status}",
        target_type="user",
        target_id=p_oid
    )

    flash(f"Patient account {new_status}d successfully.", "success")
    return redirect(url_for("admin.patient_management"))

@admin_bp.route("/appointments")
def appointment_management():
    """Global appointment management with multi-criteria filtering."""
    date_filter = request.args.get("date", "").strip()
    status_filter = request.args.get("status", "all").strip()
    doctor_filter = request.args.get("doctor_id", "").strip()
    page = int(request.args.get("page", 1))
    per_page = 15

    query = {}
    if date_filter:
        query["appointment_date"] = date_filter
    if status_filter != "all":
        query["status"] = status_filter
    if doctor_filter:
        try:
            query["doctor_id"] = ObjectId(doctor_filter)
        except Exception:
            pass

    appointments = []
    total = 0
    if db.appointments is not None:
        total = db.appointments.count_documents(query)
        cursor = (
            db.appointments.find(query)
            .sort([("appointment_date", -1), ("start_time", -1)])
            .skip((page - 1) * per_page)
            .limit(per_page)
        )
        for app in cursor:
            app["patient"] = db.users.find_one({"_id": app["patient_id"]})
            app["doctor"] = db.users.find_one({"_id": app["doctor_id"]})
            appointments.append(app)

    doctors = list(db.users.find({"role": "doctor"}).sort("full_name", 1)) if db.users is not None else []
    total_pages = max(1, (total + per_page - 1) // per_page)

    return render_template(
        "admin/appointments.html",
        appointments=appointments,
        doctors=doctors,
        date_filter=date_filter,
        status_filter=status_filter,
        doctor_filter=doctor_filter,
        current_page=page,
        total_pages=total_pages,
        total=total
    )

@admin_bp.route("/specializations", methods=["GET", "POST"])
def specialization_management():
    """Manage medical specializations / clinic departments."""
    if request.method == "POST":
        verify_csrf()
        action = request.form.get("action")

        if action == "add":
            name = request.form.get("name", "").strip()
            description = request.form.get("description", "").strip()
            if not name:
                flash("Department name is required.", "danger")
                return redirect(url_for("admin.specialization_management"))

            existing = db.specializations.find_one({"name": name})
            if existing:
                flash("Specialization already exists.", "warning")
            else:
                db.specializations.insert_one({
                    "name": name,
                    "description": description,
                    "is_active": True,
                    "created_at": datetime.now(timezone.utc)
                })
                AuditService.log_action(session["user_id"], "add_specialization", "specialization", None, {"name": name})
                flash(f"Department '{name}' added successfully.", "success")

        elif action == "toggle":
            spec_id = ObjectId(request.form.get("specialization_id"))
            spec = db.specializations.find_one({"_id": spec_id})
            if spec:
                new_state = not spec.get("is_active", True)
                db.specializations.update_one({"_id": spec_id}, {"$set": {"is_active": new_state}})
                flash(f"Department status updated to {'Active' if new_state else 'Inactive'}.", "info")

        return redirect(url_for("admin.specialization_management"))

    specializations = list(db.specializations.find().sort("name", 1)) if db.specializations is not None else []
    return render_template("admin/specializations.html", specializations=specializations)

@admin_bp.route("/analytics")
def analytics():
    """Reports and analytical visualizations with Chart.js integration."""
    return render_template("admin/analytics.html")

@admin_bp.route("/audit-logs")
def audit_logs():
    """Audit logs viewer for administrative compliance and system tracking."""
    action_filter = request.args.get("action", "").strip()
    page = int(request.args.get("page", 1))
    per_page = 25
    skip = (page - 1) * per_page

    logs, total = AuditService.get_recent_logs(limit=per_page, skip=skip, action_filter=action_filter)
    total_pages = max(1, (total + per_page - 1) // per_page)

    return render_template(
        "admin/audit_logs.html",
        logs=logs,
        action_filter=action_filter,
        current_page=page,
        total_pages=total_pages,
        total=total
    )

@admin_bp.route("/settings", methods=["GET", "POST"])
def platform_settings():
    """Platform global configurations (cancellation limits, self-registration toggle, contact info)."""
    default_settings = {
        "_id": "general_settings",
        "hospital_name": "Antigravity General Hospital & Medical Center",
        "contact_email": "care@antigravityhospital.com",
        "contact_phone": "+91 80 2345 6789",
        "address": "42 Health Sciences Avenue, Bangalore, Karnataka 560001",
        "allow_doctor_self_registration": True,
        "cancellation_lead_hours": 2,
        "max_advance_booking_days": 30
    }

    current_settings = db.platform_settings.find_one({"_id": "general_settings"}) if db.platform_settings is not None else None
    if not current_settings:
        current_settings = default_settings
        if db.platform_settings is not None:
            db.platform_settings.update_one({"_id": "general_settings"}, {"$set": default_settings}, upsert=True)

    if request.method == "POST":
        verify_csrf()

        updated_settings = {
            "hospital_name": request.form.get("hospital_name", "").strip(),
            "contact_email": request.form.get("contact_email", "").strip(),
            "contact_phone": request.form.get("contact_phone", "").strip(),
            "address": request.form.get("address", "").strip(),
            "allow_doctor_self_registration": request.form.get("allow_doctor_self_registration") == "on",
            "cancellation_lead_hours": int(request.form.get("cancellation_lead_hours", 2)),
            "max_advance_booking_days": int(request.form.get("max_advance_booking_days", 30)),
            "updated_at": datetime.now(timezone.utc)
        }

        if db.platform_settings is not None:
            db.platform_settings.update_one({"_id": "general_settings"}, {"$set": updated_settings}, upsert=True)

        AuditService.log_action(session["user_id"], "update_settings", "platform_settings", "general_settings")
        flash("Platform settings saved successfully!", "success")
        return redirect(url_for("admin.platform_settings"))

    return render_template("admin/settings.html", settings=current_settings)
