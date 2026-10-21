from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from db import db
from extensions import login_required, roles_required, verify_csrf, get_now_local
from services.appointment_service import AppointmentService
from services.doctor_service import DoctorService
from services.audit_service import AuditService

patient_bp = Blueprint("patient", __name__, url_prefix="/patient")

@patient_bp.before_request
@login_required
@roles_required("patient")
def enforce_patient_role():
    """Ensure all endpoints in patient_bp are accessible only to authenticated patients."""
    pass

@patient_bp.route("/dashboard")
def dashboard():
    """Patient dashboard overview: appointment metrics, upcoming appointments, and quick booking access."""
    patient_id = ObjectId(session["user_id"])
    now_local = get_now_local()
    today_str = now_local.strftime("%Y-%m-%d")

    # Fetch appointment statistics
    total_count = 0
    upcoming_count = 0
    completed_count = 0
    cancelled_count = 0
    upcoming_appointments = []

    if db.is_connected and db.appointments is not None:
        total_count = db.appointments.count_documents({"patient_id": patient_id})
        upcoming_count = db.appointments.count_documents({
            "patient_id": patient_id,
            "status": {"$in": ["pending", "confirmed"]},
            "appointment_date": {"$gte": today_str}
        })
        completed_count = db.appointments.count_documents({"patient_id": patient_id, "status": "completed"})
        cancelled_count = db.appointments.count_documents({"patient_id": patient_id, "status": "cancelled"})

        # Next upcoming appointments
        cursor = db.appointments.find({
            "patient_id": patient_id,
            "status": {"$in": ["pending", "confirmed"]},
            "appointment_date": {"$gte": today_str}
        }).sort([("appointment_date", 1), ("start_time", 1)]).limit(5)

        for app in cursor:
            doc = db.users.find_one({"_id": app["doctor_id"]})
            profile = db.doctor_profiles.find_one({"user_id": app["doctor_id"]})
            app["doctor"] = doc
            app["doctor_profile"] = profile
            upcoming_appointments.append(app)

    return render_template(
        "patient/dashboard.html",
        stats={
            "total": total_count,
            "upcoming": upcoming_count,
            "completed": completed_count,
            "cancelled": cancelled_count
        },
        upcoming_appointments=upcoming_appointments
    )

@patient_bp.route("/book", methods=["GET", "POST"])
def book_appointment():
    """Book appointment page with doctor selector, date picker, slot loader, and submission."""
    selected_doctor_id = request.args.get("doctor_id", "")

    if request.method == "POST":
        verify_csrf()

        doctor_id = request.form.get("doctor_id", "").strip()
        appointment_date = request.form.get("appointment_date", "").strip()
        start_time = request.form.get("start_time", "").strip()
        reason = request.form.get("reason_for_visit", "").strip()

        if not doctor_id or not appointment_date or not start_time:
            flash("Please fill in all required fields (Doctor, Date, and Time Slot).", "danger")
            return redirect(url_for("patient.book_appointment", doctor_id=doctor_id))

        result = AppointmentService.book_appointment(
            patient_id=session["user_id"],
            doctor_id=doctor_id,
            appointment_date=appointment_date,
            start_time=start_time,
            reason_for_visit=reason
        )

        if result.get("success"):
            flash(result["message"], "success")
            return redirect(url_for("patient.my_appointments"))
        else:
            flash(result.get("error", "Failed to book appointment"), "danger")
            return redirect(url_for("patient.book_appointment", doctor_id=doctor_id))

    # GET request
    doctors, _ = DoctorService.search_doctors(page=1, per_page=100, approved_only=True)
    specializations = DoctorService.get_specializations()
    today_min = get_now_local().strftime("%Y-%m-%d")

    return render_template(
        "patient/book_appointment.html",
        doctors=doctors,
        specializations=specializations,
        selected_doctor_id=selected_doctor_id,
        today_min=today_min
    )

@patient_bp.route("/appointments")
def my_appointments():
    """View patient's personal appointment history and upcoming bookings with status filter."""
    patient_id = ObjectId(session["user_id"])
    filter_status = request.args.get("status", "all").strip().lower()
    page = int(request.args.get("page", 1))
    per_page = 10

    query = {"patient_id": patient_id}
    if filter_status in ["pending", "confirmed", "completed", "cancelled"]:
        query["status"] = filter_status

    appointments = []
    total = 0

    if db.is_connected and db.appointments is not None:
        total = db.appointments.count_documents(query)
        cursor = (
            db.appointments.find(query)
            .sort([("appointment_date", -1), ("start_time", -1)])
            .skip((page - 1) * per_page)
            .limit(per_page)
        )
        for app in cursor:
            doc = db.users.find_one({"_id": app["doctor_id"]})
            profile = db.doctor_profiles.find_one({"user_id": app["doctor_id"]})
            app["doctor"] = doc
            app["doctor_profile"] = profile
            appointments.append(app)

    total_pages = max(1, (total + per_page - 1) // per_page)

    return render_template(
        "patient/my_appointments.html",
        appointments=appointments,
        current_status=filter_status,
        current_page=page,
        total_pages=total_pages,
        total_count=total
    )

@patient_bp.route("/appointments/<appointment_id>")
def appointment_detail(appointment_id):
    """Detailed view for a specific appointment owned by the current patient."""
    try:
        details = AppointmentService.get_appointment_details(appointment_id)
    except Exception:
        details = None

    if not details or str(details["appointment"]["patient_id"]) != session["user_id"]:
        flash("Appointment not found or unauthorized.", "warning")
        return redirect(url_for("patient.my_appointments"))

    return render_template("patient/appointment_detail.html", **details)

@patient_bp.route("/calendar")
def calendar_view():
    """Interactive calendar view displaying all appointments booked by the patient."""
    return render_template("patient/calendar.html")

@patient_bp.route("/profile", methods=["GET", "POST"])
def profile():
    """View and update patient personal profile details."""
    patient_id = ObjectId(session["user_id"])
    user = db.users.find_one({"_id": patient_id})

    if request.method == "POST":
        verify_csrf()
        full_name = request.form.get("full_name", "").strip()
        phone = request.form.get("phone", "").strip()
        current_pwd = request.form.get("current_password", "")
        new_pwd = request.form.get("new_password", "")

        if not full_name or len(full_name) < 2:
            flash("Full name must be at least 2 characters.", "danger")
            return render_template("patient/profile.html", user=user)

        update_fields = {
            "full_name": full_name,
            "phone": phone,
            "updated_at": datetime.now(timezone.utc)
        }

        # Handle optional password change
        if new_pwd:
            if not current_pwd or not check_password_hash(user.get("password_hash", ""), current_pwd):
                flash("Current password is incorrect.", "danger")
                return render_template("patient/profile.html", user=user)
            if len(new_pwd) < 6:
                flash("New password must be at least 6 characters.", "danger")
                return render_template("patient/profile.html", user=user)
            update_fields["password_hash"] = generate_password_hash(new_pwd)

        db.users.update_one({"_id": patient_id}, {"$set": update_fields})
        session["user_name"] = full_name

        AuditService.log_action(
            actor_user_id=patient_id,
            action="update_profile",
            target_type="user",
            target_id=patient_id
        )

        flash("Profile updated successfully!", "success")
        return redirect(url_for("patient.profile"))

    return render_template("patient/profile.html", user=user)
