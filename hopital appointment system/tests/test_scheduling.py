import pytest
from datetime import datetime, timedelta
from bson import ObjectId
from db import db
from services.appointment_service import AppointmentService
from services.doctor_service import DoctorService

def get_next_weekday(start_date, weekday_name):
    """Utility to get upcoming date matching a specific weekday."""
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    target_idx = days.index(weekday_name)
    current_idx = start_date.weekday()
    diff = (target_idx - current_idx) % 7
    if diff == 0:
        diff = 7  # ensure next week
    return start_date + timedelta(days=diff)

def test_successful_appointment_booking(client, app, init_roles):
    """Test standard appointment booking within doctor working hours."""
    patient_id = init_roles["patient_id"]
    doctor_id = init_roles["doctor_id"]

    # Target a future Monday
    future_date = get_next_weekday(datetime.now().date(), "Monday").strftime("%Y-%m-%d")

    result = AppointmentService.book_appointment(
        patient_id=str(patient_id),
        doctor_id=str(doctor_id),
        appointment_date=future_date,
        start_time="10:00",
        reason_for_visit="Routine cardiac checkup"
    )

    assert result["success"] is True
    assert "appointment_id" in result

    # Verify document in DB
    app_doc = db.appointments.find_one({"_id": ObjectId(result["appointment_id"])})
    assert app_doc is not None
    assert app_doc["status"] == "pending"
    assert app_doc["start_time"] == "10:00"
    assert app_doc["end_time"] == "10:30"
    assert app_doc["consultation_fee"] == 600.0

def test_double_booking_prevention(client, app, init_roles):
    """Ensure two patients cannot book the same doctor at the same slot."""
    patient1_id = init_roles["patient_id"]
    patient2_id = init_roles["patient2_id"]
    doctor_id = init_roles["doctor_id"]

    future_date = get_next_weekday(datetime.now().date(), "Tuesday").strftime("%Y-%m-%d")

    # Patient 1 books 10:00
    res1 = AppointmentService.book_appointment(
        patient_id=str(patient1_id),
        doctor_id=str(doctor_id),
        appointment_date=future_date,
        start_time="10:00",
        reason_for_visit="First visit"
    )
    assert res1["success"] is True

    # Patient 2 attempts to book the exact same slot
    res2 = AppointmentService.book_appointment(
        patient_id=str(patient2_id),
        doctor_id=str(doctor_id),
        appointment_date=future_date,
        start_time="10:00",
        reason_for_visit="Conflicting visit"
    )
    assert res2["success"] is False
    assert "already booked" in res2["error"].lower() or "slot" in res2["error"].lower()

def test_booking_outside_working_hours(client, app, init_roles):
    """Verify booking fails if requested time is before or after doctor working hours."""
    patient_id = init_roles["patient_id"]
    doctor_id = init_roles["doctor_id"]

    future_date = get_next_weekday(datetime.now().date(), "Wednesday").strftime("%Y-%m-%d")

    # Doctor works 09:00 - 17:00, test 07:00 and 19:00
    res_early = AppointmentService.book_appointment(
        patient_id=str(patient_id),
        doctor_id=str(doctor_id),
        appointment_date=future_date,
        start_time="07:00"
    )
    assert res_early["success"] is False
    assert "working hours" in res_early["error"].lower()

    res_late = AppointmentService.book_appointment(
        patient_id=str(patient_id),
        doctor_id=str(doctor_id),
        appointment_date=future_date,
        start_time="18:00"
    )
    assert res_late["success"] is False
    assert "working hours" in res_late["error"].lower()

def test_booking_during_break_time(client, app, init_roles):
    """Verify booking fails if slot overlaps with doctor's scheduled break (13:00-14:00)."""
    patient_id = init_roles["patient_id"]
    doctor_id = init_roles["doctor_id"]

    future_date = get_next_weekday(datetime.now().date(), "Wednesday").strftime("%Y-%m-%d")

    res = AppointmentService.book_appointment(
        patient_id=str(patient_id),
        doctor_id=str(doctor_id),
        appointment_date=future_date,
        start_time="13:00"
    )
    assert res["success"] is False
    assert "break" in res["error"].lower()

def test_past_date_booking_prevention(client, app, init_roles):
    """Verify bookings cannot be made for past dates."""
    patient_id = init_roles["patient_id"]
    doctor_id = init_roles["doctor_id"]

    past_date = (datetime.now().date() - timedelta(days=5)).strftime("%Y-%m-%d")

    res = AppointmentService.book_appointment(
        patient_id=str(patient_id),
        doctor_id=str(doctor_id),
        appointment_date=past_date,
        start_time="10:00"
    )
    assert res["success"] is False
    assert "past" in res["error"].lower()

def test_appointment_cancellation_and_reschedule(client, app, init_roles):
    """Test patient cancellation and rescheduling workflow."""
    patient_id = init_roles["patient_id"]
    doctor_id = init_roles["doctor_id"]

    future_date1 = get_next_weekday(datetime.now().date(), "Thursday").strftime("%Y-%m-%d")
    future_date2 = get_next_weekday(datetime.now().date() + timedelta(days=7), "Thursday").strftime("%Y-%m-%d")

    # 1. Book
    book_res = AppointmentService.book_appointment(
        patient_id=str(patient_id),
        doctor_id=str(doctor_id),
        appointment_date=future_date1,
        start_time="11:00"
    )
    app_id = book_res["appointment_id"]

    # 2. Reschedule to date 2
    resched_res = AppointmentService.reschedule_appointment(
        appointment_id=app_id,
        user_id=str(patient_id),
        user_role="patient",
        new_date=future_date2,
        new_start_time="11:30"
    )
    assert resched_res["success"] is True

    app_doc = db.appointments.find_one({"_id": ObjectId(app_id)})
    assert app_doc["appointment_date"] == future_date2
    assert app_doc["start_time"] == "11:30"

    # 3. Cancel
    cancel_res = AppointmentService.cancel_appointment(
        appointment_id=app_id,
        user_id=str(patient_id),
        user_role="patient",
        reason="Family emergency"
    )
    assert cancel_res["success"] is True

    app_doc = db.appointments.find_one({"_id": ObjectId(app_id)})
    assert app_doc["status"] == "cancelled"
    assert "Family emergency" in app_doc["cancellation_reason"]

def test_patient_data_ownership(client, app, init_roles):
    """Verify Patient 2 cannot cancel or access Patient 1's appointment."""
    patient1_id = init_roles["patient_id"]
    patient2_id = init_roles["patient2_id"]
    doctor_id = init_roles["doctor_id"]

    future_date = get_next_weekday(datetime.now().date(), "Friday").strftime("%Y-%m-%d")

    book_res = AppointmentService.book_appointment(
        patient_id=str(patient1_id),
        doctor_id=str(doctor_id),
        appointment_date=future_date,
        start_time="14:00"
    )
    app_id = book_res["appointment_id"]

    # Patient 2 tries to cancel Patient 1's appointment
    unauth_cancel = AppointmentService.cancel_appointment(
        appointment_id=app_id,
        user_id=str(patient2_id),
        user_role="patient",
        reason="Malicious cancel attempt"
    )
    assert unauth_cancel["success"] is False
    assert "unauthorized" in unauth_cancel["error"].lower()

    # Verify status is still active
    app_doc = db.appointments.find_one({"_id": ObjectId(app_id)})
    assert app_doc["status"] == "pending"

def test_doctor_schedule_management(client, app, init_roles):
    """Test doctor modifying working days, break times, and blocked dates."""
    doctor_id = init_roles["doctor_id"]

    update_payload = {
        "working_days": ["Monday", "Wednesday", "Friday"],
        "working_hours": {"start": "10:00", "end": "16:00"},
        "appointment_duration_minutes": 45,
        "blocked_dates": ["2026-11-20"]
    }
    success = DoctorService.update_doctor_profile(doctor_id, update_payload)
    assert success is True

    profile = db.doctor_profiles.find_one({"user_id": ObjectId(doctor_id)})
    assert profile["working_days"] == ["Monday", "Wednesday", "Friday"]
    assert profile["working_hours"]["start"] == "10:00"
    assert profile["appointment_duration_minutes"] == 45
    assert "2026-11-20" in profile["blocked_dates"]
