import os
import sys
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

# Ensure app root is on python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from config import Config
from db import db
from pymongo import MongoClient

def run_seed(clean=False, database=None):
    """Seed initial administrator, specializations, demo doctors, patients, and appointments."""
    if database is None:
        mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/hospital_appointment_system")
        db_name = os.getenv("MONGO_DB_NAME", "hospital_appointment_system")

        print(f"[*] Connecting to MongoDB at: {mongo_uri}")
        try:
            client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
            client.admin.command("ping")
            database = client[db_name]
            print(f"[+] Successfully connected to database '{db_name}'.")
        except Exception as e:
            print(f"[!] MongoDB Connection Error: {e}")
            print("[!] Please ensure MongoDB is running or update MONGO_URI in your .env file.")
            return False
    else:
        print("[*] Seeding provided database instance (Embedded Mode)...")

    if clean:
        print("[*] Cleaning existing collections...")
        database.users.delete_many({})
        database.doctor_profiles.delete_many({})
        database.appointments.delete_many({})
        database.specializations.delete_many({})
        database.notifications.delete_many({})
        database.audit_logs.delete_many({})
        database.platform_settings.delete_many({})
        print("[+] Cleaned successfully.")

    # 1. Platform Settings
    database.platform_settings.update_one(
        {"_id": "general_settings"},
        {"$set": {
            "hospital_name": "Antigravity Care General Hospital",
            "contact_email": "care@antigravityhospital.com",
            "contact_phone": "+91 80 2345 6789",
            "address": "42 Health Sciences Avenue, Bangalore, Karnataka 560001",
            "allow_doctor_self_registration": True,
            "cancellation_lead_hours": 2,
            "max_advance_booking_days": 30,
            "updated_at": datetime.now(timezone.utc)
        }},
        upsert=True
    )

    # 2. Specializations
    specialization_data = [
        {"name": "General Medicine", "description": "Primary healthcare, preventive medicine, and routine wellness checkups."},
        {"name": "Cardiology", "description": "Heart conditions, hypertension, coronary care, and cardiovascular health."},
        {"name": "Pediatrics", "description": "Compassionate pediatric healthcare, child development, and vaccinations."},
        {"name": "Dermatology", "description": "Skin health, eczema, acne, clinical aesthetics, and dermatological care."},
        {"name": "Orthopedics", "description": "Bone, joint, spine, sports injury, and musculoskeletal treatments."},
        {"name": "Neurology", "description": "Brain, nerve, migraine, stroke recovery, and neuromuscular care."},
        {"name": "Ophthalmology", "description": "Comprehensive vision care, cataracts, and eye diagnostics."},
        {"name": "ENT (Otolaryngology)", "description": "Ear, nose, throat, sinuses, and auditory health."}
    ]
    for spec in specialization_data:
        database.specializations.update_one(
            {"name": spec["name"]},
            {"$set": {**spec, "is_active": True, "created_at": datetime.now(timezone.utc)}},
            upsert=True
        )
    print(f"[+] Ensured {len(specialization_data)} clinical specializations.")

    # 3. Administrator Account
    admin_email = os.getenv("INITIAL_ADMIN_EMAIL", "admin@hospital.com").lower()
    admin_password = os.getenv("INITIAL_ADMIN_PASSWORD", "Admin@Hospital2026")
    admin_name = os.getenv("INITIAL_ADMIN_NAME", "System Administrator")

    admin_user = database.users.find_one({"email": admin_email})
    if not admin_user:
        admin_doc = {
            "full_name": admin_name,
            "email": admin_email,
            "password_hash": generate_password_hash(admin_password),
            "phone": "+91 98765 43210",
            "role": "admin",
            "account_status": "active",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        res = database.users.insert_one(admin_doc)
        admin_id = res.inserted_id
        print(f"[+] Created Administrator Account: {admin_email} (Password: {admin_password})")
    else:
        admin_id = admin_user["_id"]
        print(f"[i] Administrator account already exists ({admin_email}).")

    # 4. Demo Doctors
    doctors_info = [
        {
            "name": "Dr. Sarah Jenkins",
            "email": "sarah.jenkins@hospital.com",
            "password": "Doctor@123456",
            "phone": "+91 98111 22334",
            "specialization": "Cardiology",
            "qualifications": "MBBS, MD (Cardiology), FACC",
            "experience_years": 14,
            "consultation_fee": 800.0,
            "biography": "Senior Interventional Cardiologist specializing in preventive heart health and cardiovascular diagnostics.",
            "working_hours": {"start": "09:00", "end": "16:00"},
            "working_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "break_times": [{"start": "13:00", "end": "14:00"}],
            "duration": 30
        },
        {
            "name": "Dr. Rajesh Sharma",
            "email": "rajesh.sharma@hospital.com",
            "password": "Doctor@123456",
            "phone": "+91 98222 33445",
            "specialization": "General Medicine",
            "qualifications": "MBBS, DNB (Internal Medicine)",
            "experience_years": 10,
            "consultation_fee": 500.0,
            "biography": "Experienced general practitioner focused on chronic disease management and lifestyle wellness.",
            "working_hours": {"start": "09:00", "end": "17:00"},
            "working_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Saturday"],
            "break_times": [{"start": "13:00", "end": "14:00"}],
            "duration": 30
        },
        {
            "name": "Dr. Priya Nair",
            "email": "priya.nair@hospital.com",
            "password": "Doctor@123456",
            "phone": "+91 98333 44556",
            "specialization": "Pediatrics",
            "qualifications": "MBBS, MD (Pediatrics), DCH",
            "experience_years": 8,
            "consultation_fee": 650.0,
            "biography": "Passionate child healthcare specialist dedicated to infant care and developmental pediatrics.",
            "working_hours": {"start": "10:00", "end": "18:00"},
            "working_days": ["Monday", "Wednesday", "Thursday", "Friday", "Saturday"],
            "break_times": [{"start": "14:00", "end": "15:00"}],
            "duration": 30
        },
        {
            "name": "Dr. Marcus Vance",
            "email": "marcus.vance@hospital.com",
            "password": "Doctor@123456",
            "phone": "+91 98444 55667",
            "specialization": "Dermatology",
            "qualifications": "MBBS, MD (Dermatology)",
            "experience_years": 11,
            "consultation_fee": 750.0,
            "biography": "Board-certified dermatologist with deep expertise in clinical dermatology and allergy treatments.",
            "working_hours": {"start": "09:00", "end": "15:00"},
            "working_days": ["Tuesday", "Wednesday", "Thursday", "Friday"],
            "break_times": [{"start": "12:30", "end": "13:30"}],
            "duration": 30
        }
    ]

    doctor_ids = []
    for d in doctors_info:
        existing = database.users.find_one({"email": d["email"]})
        if not existing:
            user_doc = {
                "full_name": d["name"],
                "email": d["email"],
                "password_hash": generate_password_hash(d["password"]),
                "phone": d["phone"],
                "role": "doctor",
                "account_status": "active",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            res = database.users.insert_one(user_doc)
            doc_id = res.inserted_id
            print(f"[+] Created Doctor: {d['name']} ({d['email']})")
        else:
            doc_id = existing["_id"]

        doctor_ids.append(doc_id)

        # Ensure doctor profile
        database.doctor_profiles.update_one(
            {"user_id": doc_id},
            {"$set": {
                "user_id": doc_id,
                "specialization": d["specialization"],
                "qualifications": d["qualifications"],
                "experience_years": d["experience_years"],
                "consultation_fee": d["consultation_fee"],
                "biography": d["biography"],
                "working_hours": d["working_hours"],
                "working_days": d["working_days"],
                "break_times": d["break_times"],
                "appointment_duration_minutes": d["duration"],
                "blocked_dates": [],
                "is_approved": True,
                "updated_at": datetime.now(timezone.utc)
            }},
            upsert=True
        )

    # 5. Demo Patients
    patients_info = [
        {"name": "Ananya Sharma", "email": "patient@hospital.com", "password": "Patient@123456", "phone": "+91 99000 11223"},
        {"name": "David Miller", "email": "david.miller@gmail.com", "password": "Patient@123456", "phone": "+91 99111 22334"},
        {"name": "Rohan Patel", "email": "rohan.patel@gmail.com", "password": "Patient@123456", "phone": "+91 99222 33445"}
    ]

    patient_ids = []
    for p in patients_info:
        existing = database.users.find_one({"email": p["email"]})
        if not existing:
            user_doc = {
                "full_name": p["name"],
                "email": p["email"],
                "password_hash": generate_password_hash(p["password"]),
                "phone": p["phone"],
                "role": "patient",
                "account_status": "active",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            res = database.users.insert_one(user_doc)
            p_id = res.inserted_id
            print(f"[+] Created Patient: {p['name']} ({p['email']})")
        else:
            p_id = existing["_id"]
        patient_ids.append(p_id)

    # 6. Sample Appointments
    today = datetime.now().date()
    sample_appointments = [
        {
            "patient_id": patient_ids[0],
            "doctor_id": doctor_ids[0],
            "appointment_date": (today + timedelta(days=1)).strftime("%Y-%m-%d"),
            "start_time": "10:00",
            "end_time": "10:30",
            "reason_for_visit": "Routine blood pressure and ECG follow-up.",
            "status": "confirmed",
            "consultation_fee": 800.0
        },
        {
            "patient_id": patient_ids[0],
            "doctor_id": doctor_ids[1],
            "appointment_date": (today + timedelta(days=2)).strftime("%Y-%m-%d"),
            "start_time": "11:00",
            "end_time": "11:30",
            "reason_for_visit": "Seasonal allergies and persistent cough.",
            "status": "pending",
            "consultation_fee": 500.0
        },
        {
            "patient_id": patient_ids[1],
            "doctor_id": doctor_ids[2],
            "appointment_date": (today + timedelta(days=3)).strftime("%Y-%m-%d"),
            "start_time": "11:30",
            "end_time": "12:00",
            "reason_for_visit": "Pediatric wellness checkup and vaccination schedule.",
            "status": "confirmed",
            "consultation_fee": 650.0
        },
        {
            "patient_id": patient_ids[0],
            "doctor_id": doctor_ids[0],
            "appointment_date": (today - timedelta(days=7)).strftime("%Y-%m-%d"),
            "start_time": "09:30",
            "end_time": "10:00",
            "reason_for_visit": "Initial chest discomfort assessment.",
            "status": "completed",
            "consultation_fee": 800.0
        },
        {
            "patient_id": patient_ids[2],
            "doctor_id": doctor_ids[3],
            "appointment_date": (today - timedelta(days=3)).strftime("%Y-%m-%d"),
            "start_time": "14:00",
            "end_time": "14:30",
            "reason_for_visit": "Dermatological rash consultation.",
            "status": "cancelled",
            "cancellation_reason": "Patient had an unavoidable travel conflict.",
            "consultation_fee": 750.0
        }
    ]

    for app in sample_appointments:
        existing_app = database.appointments.find_one({
            "doctor_id": app["doctor_id"],
            "appointment_date": app["appointment_date"],
            "start_time": app["start_time"]
        })
        if not existing_app:
            app["created_at"] = datetime.now(timezone.utc)
            app["updated_at"] = datetime.now(timezone.utc)
            database.appointments.insert_one(app)

    print(f"[+] Ensured realistic sample appointments across various statuses.")

    # 7. Initial Notifications
    database.notifications.insert_one({
        "recipient_user_id": patient_ids[0],
        "title": "Welcome to Antigravity Care",
        "message": "Welcome! You can now browse doctors and schedule medical consultations with ease.",
        "notification_type": "general",
        "is_read": False,
        "created_at": datetime.now(timezone.utc)
    })

    print("[SUCCESS] Database seeding completed successfully!")
    print("\nAvailable Demo Credentials:")
    print("-" * 50)
    print("Admin:   admin@hospital.com         / Admin@Hospital2026")
    print("Doctor:  sarah.jenkins@hospital.com / Doctor@123456")
    print("Doctor:  rajesh.sharma@hospital.com / Doctor@123456")
    print("Patient: patient@hospital.com       / Patient@123456")
    print("-" * 50)
    return True

if __name__ == "__main__":
    clean_flag = "--clean" in sys.argv
    run_seed(clean=clean_flag)
