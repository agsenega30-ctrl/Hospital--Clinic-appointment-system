from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from db import db
from extensions import login_required, roles_required, verify_csrf, get_now_local
from services.doctor_service import DoctorService
from services.appointment_service import AppointmentService
from services.audit_service import AuditService

doctor_bp = Blueprint("doctor", __name__, url_prefix="/doctor")

@doctor_bp.before_request
@login_required
@roles_required("doctor")
def enforce_doctor_role():
    """Ensure all doctor endpoints are restricted to authenticated doctors."""
    pass

@doctor_bp.route("/dashboard")
def dashboard():
    """Doctor dashboard: today's schedule, appointment metrics, and quick response controls."""
    doctor_id = ObjectId(session["user_id"])
    now_local = get_now_local()
    today_str = now_local.strftime("%Y-%m-%d")

    today_appointments = []
    today_count = 0
    pending_count = 0
    upcoming_count = 0
    completed_count = 0

    if db.is_connected and db.appointments is not None:
        today_count = db.appointments.count_documents({
            "doctor_id": doctor_id,
            "appointment_date": today_str
        })
        pending_count = db.appointments.count_documents({
            "doctor_id": doctor_id,
            "status": "pending"
        })
        upcoming_count = db.appointments.count_documents({
            "doctor_id": doctor_id,
            "status": "confirmed",
            "appointment_date": {"$gte": today_str}
        })
        completed_count = db.appointments.count_documents({
            "doctor_id": doctor_id,
            "status": "completed"
        })

        cursor = db.appointments.find({
            "doctor_id": doctor_id,
            "appointment_date": today_str
        }).sort("start_time", 1)

        for app in cursor:
            pat = db.users.find_one({"_id": app["patient_id"]})
            app["patient"] = pat
            today_appointments.append(app)

    profile = db.doctor_profiles.find_one({"user_id": doctor_id}) or DoctorService.get_default_profile(doctor_id)

    return render_template(
        "doctor/dashboard.html",
        stats={
            "today": today_count,
            "pending": pending_count,
            "upcoming": upcoming_count,
            "completed": completed_count
        },
        today_appointments=today_appointments,
        profile=profile,
        today_str=today_str
    )

@doctor_bp.route("/calendar")
def calendar_view():
    """Interactive FullCalendar view of doctor's working schedule and appointments."""
    return render_template("doctor/calendar.html")

@doctor_bp.route("/appointments")
def appointment_management():
    """List and manage all patient appointments for this doctor with search and status filtering."""
    doctor_id = ObjectId(session["user_id"])
    filter_status = request.args.get("status", "all").strip().lower()
    filter_date = request.args.get("date", "").strip()
    page = int(request.args.get("page", 1))
    per_page = 15

    query = {"doctor_id": doctor_id}
    if filter_status in ["pending", "confirmed", "completed", "cancelled"]:
        query["status"] = filter_status
    if filter_date:
        query["appointment_date"] = filter_date

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
            pat = db.users.find_one({"_id": app["patient_id"]})
            app["patient"] = pat
            appointments.append(app)

    total_pages = max(1, (total + per_page - 1) // per_page)

    return render_template(
        "doctor/appointments.html",
        appointments=appointments,
        current_status=filter_status,
        selected_date=filter_date,
        current_page=page,
        total_pages=total_pages,
        total_count=total
    )

@doctor_bp.route("/availability", methods=["GET", "POST"])
def availability_settings():
    """Configure working days, hours, appointment duration, breaks, and blocked dates."""
    doctor_id = ObjectId(session["user_id"])
    profile = db.doctor_profiles.find_one({"user_id": doctor_id}) or DoctorService.get_default_profile(doctor_id)

    if request.method == "POST":
        verify_csrf()

        # Parse working days
        working_days = request.form.getlist("working_days")
        start_hour = request.form.get("start_hour", "09:00").strip()
        end_hour = request.form.get("end_hour", "17:00").strip()
        duration_minutes = int(request.form.get("appointment_duration_minutes", 30))

        # Parse break times
        break_start = request.form.get("break_start", "").strip()
        break_end = request.form.get("break_end", "").strip()
        break_times = []
        if break_start and break_end:
            break_times.append({"start": break_start, "end": break_end})

        # Parse blocked date actions
        action = request.form.get("action")
        blocked_dates = list(profile.get("blocked_dates", []))

        if action == "add_block_date":
            new_block_date = request.form.get("new_block_date", "").strip()
            if new_block_date and new_block_date not in blocked_dates:
                blocked_dates.append(new_block_date)
                blocked_dates.sort()
                flash(f"Blocked date {new_block_date} added.", "info")
        elif action == "remove_block_date":
            remove_date = request.form.get("remove_date", "").strip()
            if remove_date in blocked_dates:
                blocked_dates.remove(remove_date)
                flash(f"Blocked date {remove_date} removed.", "info")

        update_payload = {
            "working_days": working_days,
            "working_hours": {"start": start_hour, "end": end_hour},
            "appointment_duration_minutes": duration_minutes,
            "break_times": break_times,
            "blocked_dates": blocked_dates
        }

        DoctorService.update_doctor_profile(doctor_id, update_payload)

        AuditService.log_action(
            actor_user_id=doctor_id,
            action="update_availability",
            target_type="doctor_profile",
            target_id=doctor_id,
            details={"working_days": working_days, "hours": f"{start_hour}-{end_hour}"}
        )

        flash("Schedule and availability settings saved successfully!", "success")
        return redirect(url_for("doctor.availability_settings"))

    all_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return render_template(
        "doctor/availability.html",
        profile=profile,
        all_days=all_days,
        today_min=get_now_local().strftime("%Y-%m-%d")
    )

@doctor_bp.route("/profile", methods=["GET", "POST"])
def profile():
    """Update professional credentials, fees, specialization, and biography."""
    doctor_id = ObjectId(session["user_id"])
    user = db.users.find_one({"_id": doctor_id})
    profile_doc = db.doctor_profiles.find_one({"user_id": doctor_id}) or DoctorService.get_default_profile(doctor_id)
    specializations = DoctorService.get_specializations()

    if request.method == "POST":
        verify_csrf()

        full_name = request.form.get("full_name", "").strip()
        phone = request.form.get("phone", "").strip()
        specialization = request.form.get("specialization", "").strip()
        qualifications = request.form.get("qualifications", "").strip()
        experience_years = int(request.form.get("experience_years", 0))
        consultation_fee = float(request.form.get("consultation_fee", 500.0))
        biography = request.form.get("biography", "").strip()

        # Update user doc
        user_update = {"full_name": full_name, "phone": phone, "updated_at": datetime.now(timezone.utc)}

        new_pwd = request.form.get("new_password", "")
        current_pwd = request.form.get("current_password", "")
        if new_pwd:
            if not check_password_hash(user.get("password_hash", ""), current_pwd):
                flash("Current password is incorrect.", "danger")
                return render_template("doctor/profile.html", user=user, profile=profile_doc, specializations=specializations)
            if len(new_pwd) < 6:
                flash("New password must be at least 6 characters.", "danger")
                return render_template("doctor/profile.html", user=user, profile=profile_doc, specializations=specializations)
            user_update["password_hash"] = generate_password_hash(new_pwd)

        db.users.update_one({"_id": doctor_id}, {"$set": user_update})
        session["user_name"] = full_name

        # Update doctor profile doc
        profile_update = {
            "specialization": specialization,
            "qualifications": qualifications,
            "experience_years": experience_years,
            "consultation_fee": consultation_fee,
            "biography": biography
        }
        DoctorService.update_doctor_profile(doctor_id, profile_update)

        AuditService.log_action(
            actor_user_id=doctor_id,
            action="update_doctor_profile",
            target_type="doctor_profile",
            target_id=doctor_id
        )

        flash("Professional profile updated successfully!", "success")
        return redirect(url_for("doctor.profile"))

    return render_template(
        "doctor/profile.html",
        user=user,
        profile=profile_doc,
        specializations=specializations
    )
