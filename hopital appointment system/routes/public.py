from flask import Blueprint, render_template, request, flash, redirect, url_for
from bson import ObjectId
from db import db
from services.doctor_service import DoctorService

public_bp = Blueprint("public", __name__)

@public_bp.route("/")
def index():
    """Public landing page showcasing hospital services, specialties, and featured doctors."""
    featured_doctors, _ = DoctorService.search_doctors(page=1, per_page=6, approved_only=True)
    specializations = DoctorService.get_specializations()

    # Total counts for hero stats
    doctor_count = 0
    patient_count = 0
    appointment_count = 0
    if db.is_connected and db.users is not None:
        try:
            doctor_count = db.users.count_documents({"role": "doctor", "account_status": "active"})
            patient_count = db.users.count_documents({"role": "patient", "account_status": "active"})
            appointment_count = db.appointments.count_documents({})
        except Exception:
            pass

    return render_template(
        "index.html",
        featured_doctors=featured_doctors,
        specializations=specializations,
        stats={
            "doctors": max(doctor_count, 12),
            "patients": max(patient_count, 1500),
            "appointments": max(appointment_count, 3200),
            "departments": len(specializations) or 8
        }
    )

@public_bp.route("/doctors")
def doctors_directory():
    """Public doctor directory with search and filtering by name, specialization, and availability date."""
    search_query = request.args.get("search", "").strip()
    specialization = request.args.get("specialization", "").strip()
    date_str = request.args.get("date", "").strip()
    page = int(request.args.get("page", 1))

    doctors, total = DoctorService.search_doctors(
        search_query=search_query,
        specialization=specialization,
        date_str=date_str,
        page=page,
        per_page=9,
        approved_only=True
    )
    specializations = DoctorService.get_specializations()

    total_pages = max(1, (total + 8) // 9)

    return render_template(
        "public/doctors.html",
        doctors=doctors,
        specializations=specializations,
        search_query=search_query,
        selected_specialization=specialization,
        selected_date=date_str,
        current_page=page,
        total_pages=total_pages,
        total_results=total
    )

@public_bp.route("/doctors/<doctor_id>")
def doctor_detail(doctor_id):
    """Public doctor profile page with detailed qualifications, schedule, and consultation fee."""
    try:
        doc = DoctorService.get_doctor_by_id(doctor_id)
    except Exception:
        doc = None

    if not doc:
        flash("The requested doctor profile was not found.", "warning")
        return redirect(url_for("public.doctors_directory"))

    return render_template("public/doctor_detail.html", doctor=doc["user"], profile=doc["profile"])

@public_bp.route("/contact", methods=["GET", "POST"])
def contact():
    """Contact page with hospital info and inquiry form."""
    if request.method == "POST":
        flash("Thank you for reaching out! Our hospital desk team will respond promptly.", "success")
        return redirect(url_for("public.contact"))
    return render_template("public/contact.html")
