import os
import sys
# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from datetime import datetime, timezone
from bson import ObjectId
from werkzeug.security import generate_password_hash
from app import create_app
from config import TestConfig
from db import db

@pytest.fixture(scope="function")
def app():
    """Create a clean Flask test application with isolated in-memory database."""
    test_app = create_app(TestConfig)
    with test_app.app_context():
        # Clear collections in mock db
        if db.db is not None:
            db.db.users.delete_many({})
            db.db.doctor_profiles.delete_many({})
            db.db.appointments.delete_many({})
            db.db.specializations.delete_many({})
            db.db.notifications.delete_many({})
            db.db.audit_logs.delete_many({})
        yield test_app

@pytest.fixture(scope="function")
def client(app):
    """Test client."""
    return app.test_client()

@pytest.fixture(scope="function")
def init_roles(app):
    """Seed test users for each role."""
    # Patient
    patient_doc = {
        "full_name": "Test Patient",
        "email": "patient@test.com",
        "password_hash": generate_password_hash("Patient@123"),
        "phone": "+91 99999 11111",
        "role": "patient",
        "account_status": "active",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    pat_res = db.users.insert_one(patient_doc)
    patient_id = pat_res.inserted_id

    # Another Patient
    patient2_doc = {
        "full_name": "Second Patient",
        "email": "patient2@test.com",
        "password_hash": generate_password_hash("Patient@123"),
        "phone": "+91 99999 22222",
        "role": "patient",
        "account_status": "active",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    pat2_res = db.users.insert_one(patient2_doc)
    patient2_id = pat2_res.inserted_id

    # Doctor
    doctor_doc = {
        "full_name": "Test Doctor",
        "email": "doctor@test.com",
        "password_hash": generate_password_hash("Doctor@123"),
        "phone": "+91 99999 33333",
        "role": "doctor",
        "account_status": "active",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    doc_res = db.users.insert_one(doctor_doc)
    doctor_id = doc_res.inserted_id

    db.doctor_profiles.insert_one({
        "user_id": doctor_id,
        "specialization": "Cardiology",
        "qualifications": "MBBS, MD",
        "experience_years": 8,
        "consultation_fee": 600.0,
        "biography": "Experienced heart specialist.",
        "working_hours": {"start": "09:00", "end": "17:00"},
        "working_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "break_times": [{"start": "13:00", "end": "14:00"}],
        "appointment_duration_minutes": 30,
        "blocked_dates": [],
        "is_approved": True
    })

    # Admin
    admin_doc = {
        "full_name": "Admin User",
        "email": "admin@test.com",
        "password_hash": generate_password_hash("Admin@123"),
        "phone": "+91 99999 44444",
        "role": "admin",
        "account_status": "active",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    adm_res = db.users.insert_one(admin_doc)
    admin_id = adm_res.inserted_id

    return {
        "patient_id": patient_id,
        "patient2_id": patient2_id,
        "doctor_id": doctor_id,
        "admin_id": admin_id
    }
