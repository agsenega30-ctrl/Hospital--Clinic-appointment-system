from datetime import datetime, timedelta, time, timezone
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from db import db
from extensions import get_now_local, get_app_timezone
from services.notification_service import NotificationService
from services.audit_service import AuditService

class AppointmentService:
    @staticmethod
    def get_available_slots(doctor_user_id, date_str):
        """
        Generate available appointment slots for a given doctor on a specific date (YYYY-MM-DD).
        Enforces working hours, working days, break times, blocked dates, existing bookings,
        and eliminates past time slots.
        """
        if not db.is_connected or db.users is None:
            return {"success": False, "error": "Database unavailable", "slots": []}

        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return {"success": False, "error": "Invalid date format. Expected YYYY-MM-DD", "slots": []}

        now_local = get_now_local()
        today_local = now_local.date()

        # Prevent querying past dates
        if target_date < today_local:
            return {"success": False, "error": "Cannot view or book appointments for past dates", "slots": []}

        doc_oid = ObjectId(doctor_user_id) if isinstance(doctor_user_id, str) else doctor_user_id
        doctor_user = db.users.find_one({"_id": doc_oid, "role": "doctor"})
        if not doctor_user or doctor_user.get("account_status") != "active":
            return {"success": False, "error": "Doctor not found or inactive", "slots": []}

        profile = db.doctor_profiles.find_one({"user_id": doc_oid})
        if not profile:
            from services.doctor_service import DoctorService
            profile = DoctorService.get_default_profile(doc_oid)

        if not profile.get("is_approved", True):
            return {"success": False, "error": "Doctor account is pending approval", "slots": []}

        # Check blocked dates
        blocked_dates = profile.get("blocked_dates", [])
        if date_str in blocked_dates:
            return {"success": True, "slots": [], "message": "Doctor has blocked this date for leave or unavailability"}

        # Check working days
        day_name = target_date.strftime("%A")
        working_days = profile.get("working_days", [])
        if day_name not in working_days:
            return {"success": True, "slots": [], "message": f"Doctor does not work on {day_name}s"}

        working_hours = profile.get("working_hours", {"start": "09:00", "end": "17:00"})
        duration_minutes = int(profile.get("appointment_duration_minutes", 30))
        break_times = profile.get("break_times", [{"start": "13:00", "end": "14:00"}])

        try:
            start_hour, start_min = map(int, working_hours.get("start", "09:00").split(":"))
            end_hour, end_min = map(int, working_hours.get("end", "17:00").split(":"))
        except Exception:
            start_hour, start_min = 9, 0
            end_hour, end_min = 17, 0

        # Fetch existing active appointments for doctor on this date
        existing_appointments = list(db.appointments.find({
            "doctor_id": doc_oid,
            "appointment_date": date_str,
            "status": {"$in": ["pending", "confirmed"]}
        }))
        booked_times = {app["start_time"] for app in existing_appointments}

        slots = []
        current_dt = datetime.combine(target_date, time(start_hour, start_min))
        end_dt = datetime.combine(target_date, time(end_hour, end_min))

        while current_dt + timedelta(minutes=duration_minutes) <= end_dt:
            slot_start_str = current_dt.strftime("%H:%M")
            slot_end_dt = current_dt + timedelta(minutes=duration_minutes)
            slot_end_str = slot_end_dt.strftime("%H:%M")

            # Check if slot falls in a break time
            in_break = False
            for brk in break_times:
                brk_start = brk.get("start", "")
                brk_end = brk.get("end", "")
                if brk_start and brk_end:
                    if not (slot_end_str <= brk_start or slot_start_str >= brk_end):
                        in_break = True
                        break

            # Check if slot is in the past for today
            is_past = False
            if target_date == today_local:
                if current_dt.time() <= now_local.time():
                    is_past = True

            is_booked = slot_start_str in booked_times

            slots.append({
                "start_time": slot_start_str,
                "end_time": slot_end_str,
                "is_available": (not in_break) and (not is_past) and (not is_booked),
                "reason": "Break time" if in_break else ("Past time" if is_past else ("Booked" if is_booked else "Available"))
            })

            current_dt += timedelta(minutes=duration_minutes)

        return {"success": True, "slots": slots, "doctor_name": doctor_user.get("full_name")}

    @staticmethod
    def book_appointment(patient_id, doctor_id, appointment_date, start_time, reason_for_visit=""):
        """
        Concurrency-safe atomic appointment booking.
        Validates doctor schedule, breaks, working days, double-booking, and past dates.
        """
        if not db.is_connected or db.appointments is None:
            return {"success": False, "error": "Database service is currently unavailable"}

        pat_oid = ObjectId(patient_id) if isinstance(patient_id, str) else patient_id
        doc_oid = ObjectId(doctor_id) if isinstance(doctor_id, str) else doctor_id

        # Verify patient exists and is active
        patient = db.users.find_one({"_id": pat_oid, "role": "patient", "account_status": "active"})
        if not patient:
            return {"success": False, "error": "Invalid or inactive patient account"}

        # Verify doctor exists and is active
        doctor = db.users.find_one({"_id": doc_oid, "role": "doctor", "account_status": "active"})
        if not doctor:
            return {"success": False, "error": "Selected doctor was not found or is currently inactive"}

        profile = db.doctor_profiles.find_one({"user_id": doc_oid})
        if not profile:
            from services.doctor_service import DoctorService
            profile = DoctorService.get_default_profile(doc_oid)

        if not profile.get("is_approved", True):
            return {"success": False, "error": "Selected doctor is not approved for consultations"}

        # Validate date format and ensure it's not past
        try:
            app_date_obj = datetime.strptime(appointment_date, "%Y-%m-%d").date()
        except ValueError:
            return {"success": False, "error": "Invalid date format. Expected YYYY-MM-DD"}

        now_local = get_now_local()
        today_local = now_local.date()

        if app_date_obj < today_local:
            return {"success": False, "error": "Appointments cannot be booked for past dates"}

        # Check doctor working days
        day_name = app_date_obj.strftime("%A")
        if day_name not in profile.get("working_days", []):
            return {"success": False, "error": f"Dr. {doctor.get('full_name')} is not available on {day_name}s"}

        # Check blocked dates
        if appointment_date in profile.get("blocked_dates", []):
            return {"success": False, "error": f"Dr. {doctor.get('full_name')} is unavailable on {appointment_date}"}

        # Calculate end_time based on doctor's configured appointment duration
        duration_minutes = int(profile.get("appointment_duration_minutes", 30))
        try:
            slot_h, slot_m = map(int, start_time.split(":"))
            slot_start_dt = datetime.combine(app_date_obj, time(slot_h, slot_m))
            slot_end_dt = slot_start_dt + timedelta(minutes=duration_minutes)
            end_time = slot_end_dt.strftime("%H:%M")
        except Exception:
            return {"success": False, "error": "Invalid start time format"}

        # Validate working hours
        working_hours = profile.get("working_hours", {"start": "09:00", "end": "17:00"})
        wh_start = working_hours.get("start", "09:00")
        wh_end = working_hours.get("end", "17:00")

        if start_time < wh_start or end_time > wh_end:
            return {"success": False, "error": f"Appointment must fall within doctor's working hours ({wh_start} - {wh_end})"}

        # Check break times
        for brk in profile.get("break_times", []):
            brk_start = brk.get("start", "")
            brk_end = brk.get("end", "")
            if brk_start and brk_end:
                if not (end_time <= brk_start or start_time >= brk_end):
                    return {"success": False, "error": f"Selected time slot conflicts with doctor's scheduled break ({brk_start} - {brk_end})"}

        # Check past time for today
        if app_date_obj == today_local:
            if slot_start_dt.time() <= now_local.time():
                return {"success": False, "error": "Selected time slot has already passed today"}

        # Check if patient already has an active appointment at the exact same date & time
        patient_conflict = db.appointments.find_one({
            "patient_id": pat_oid,
            "appointment_date": appointment_date,
            "start_time": start_time,
            "status": {"$in": ["pending", "confirmed"]}
        })
        if patient_conflict:
            return {"success": False, "error": "You already have another active appointment booked at this time"}

        # Secondary check for doctor conflict
        existing_doc_booking = db.appointments.find_one({
            "doctor_id": doc_oid,
            "appointment_date": appointment_date,
            "start_time": start_time,
            "status": {"$in": ["pending", "confirmed"]}
        })
        if existing_doc_booking:
            return {"success": False, "error": "This time slot is already booked. Please choose another slot."}

        consultation_fee = float(profile.get("consultation_fee", 500.0))

        appointment_doc = {
            "patient_id": pat_oid,
            "doctor_id": doc_oid,
            "appointment_date": appointment_date,
            "start_time": start_time,
            "end_time": end_time,
            "reason_for_visit": (reason_for_visit or "").strip(),
            "status": "pending",
            "cancellation_reason": None,
            "consultation_fee": consultation_fee,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }

        try:
            result = db.appointments.insert_one(appointment_doc)
            app_id = result.inserted_id

            # Send notifications
            NotificationService.send_notification(
                recipient_user_id=pat_oid,
                title="Appointment Booked",
                message=f"Your appointment with Dr. {doctor.get('full_name')} for {appointment_date} at {start_time} has been requested and is Pending.",
                notification_type="booking"
            )
            NotificationService.send_notification(
                recipient_user_id=doc_oid,
                title="New Appointment Request",
                message=f"Patient {patient.get('full_name')} has requested an appointment for {appointment_date} at {start_time}.",
                notification_type="booking"
            )

            # Audit log
            AuditService.log_action(
                actor_user_id=pat_oid,
                action="book_appointment",
                target_type="appointment",
                target_id=app_id,
                details={"doctor_id": str(doc_oid), "date": appointment_date, "start_time": start_time}
            )

            return {
                "success": True,
                "message": "Appointment booked successfully!",
                "appointment_id": str(app_id)
            }

        except DuplicateKeyError:
            return {
                "success": False,
                "error": "This slot was just booked by another user right before you. Please select a different available slot."
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to book appointment: {str(e)}"}

    @staticmethod
    def cancel_appointment(appointment_id, user_id, user_role, reason=""):
        """
        Cancel an existing appointment with role-based checks and state validation.
        """
        if not db.is_connected or db.appointments is None:
            return {"success": False, "error": "Database service is currently unavailable"}

        app_oid = ObjectId(appointment_id) if isinstance(appointment_id, str) else appointment_id
        u_oid = ObjectId(user_id) if isinstance(user_id, str) else user_id

        appointment = db.appointments.find_one({"_id": app_oid})
        if not appointment:
            return {"success": False, "error": "Appointment not found"}

        # Role permission & ownership check
        if user_role == "patient" and appointment["patient_id"] != u_oid:
            return {"success": False, "error": "Unauthorized: You can only cancel your own appointments"}
        if user_role == "doctor" and appointment["doctor_id"] != u_oid:
            return {"success": False, "error": "Unauthorized: You can only cancel appointments under your schedule"}

        # State transition validation
        if appointment["status"] == "cancelled":
            return {"success": False, "error": "This appointment is already cancelled"}
        if appointment["status"] == "completed":
            return {"success": False, "error": "Completed consultations cannot be cancelled"}

        update_fields = {
            "status": "cancelled",
            "cancellation_reason": reason.strip() or f"Cancelled by {user_role}",
            "cancelled_by": user_role,
            "updated_at": datetime.now(timezone.utc)
        }

        db.appointments.update_one({"_id": app_oid}, {"$set": update_fields})

        # Send notifications
        patient = db.users.find_one({"_id": appointment["patient_id"]})
        doctor = db.users.find_one({"_id": appointment["doctor_id"]})

        cancel_msg = f"Appointment on {appointment['appointment_date']} at {appointment['start_time']} was cancelled ({update_fields['cancellation_reason']})."

        NotificationService.send_notification(
            recipient_user_id=appointment["patient_id"],
            title="Appointment Cancelled",
            message=cancel_msg,
            notification_type="cancellation"
        )
        NotificationService.send_notification(
            recipient_user_id=appointment["doctor_id"],
            title="Appointment Cancelled",
            message=cancel_msg,
            notification_type="cancellation"
        )

        AuditService.log_action(
            actor_user_id=u_oid,
            action="cancel_appointment",
            target_type="appointment",
            target_id=app_oid,
            details={"reason": update_fields["cancellation_reason"], "role": user_role}
        )

        return {"success": True, "message": "Appointment cancelled successfully"}

    @staticmethod
    def reschedule_appointment(appointment_id, user_id, user_role, new_date, new_start_time):
        """
        Reschedule an existing pending or confirmed appointment to a new available time slot.
        """
        if not db.is_connected or db.appointments is None:
            return {"success": False, "error": "Database unavailable"}

        app_oid = ObjectId(appointment_id) if isinstance(appointment_id, str) else appointment_id
        u_oid = ObjectId(user_id) if isinstance(user_id, str) else user_id

        appointment = db.appointments.find_one({"_id": app_oid})
        if not appointment:
            return {"success": False, "error": "Appointment not found"}

        # Ownership validation
        if user_role == "patient" and appointment["patient_id"] != u_oid:
            return {"success": False, "error": "Unauthorized: You can only reschedule your own appointments"}
        if user_role == "doctor" and appointment["doctor_id"] != u_oid:
            return {"success": False, "error": "Unauthorized: You can only reschedule your own schedule"}

        if appointment["status"] not in ["pending", "confirmed"]:
            return {"success": False, "error": f"Cannot reschedule appointment with status '{appointment['status']}'"}

        doctor_id = appointment["doctor_id"]
        profile = db.doctor_profiles.find_one({"user_id": doctor_id})
        if not profile:
            from services.doctor_service import DoctorService
            profile = DoctorService.get_default_profile(doctor_id)

        # Validate new date & time slot
        try:
            target_date = datetime.strptime(new_date, "%Y-%m-%d").date()
        except ValueError:
            return {"success": False, "error": "Invalid date format"}

        now_local = get_now_local()
        today_local = now_local.date()

        if target_date < today_local:
            return {"success": False, "error": "Cannot reschedule to a past date"}

        day_name = target_date.strftime("%A")
        if day_name not in profile.get("working_days", []):
            return {"success": False, "error": f"Doctor does not work on {day_name}s"}

        if new_date in profile.get("blocked_dates", []):
            return {"success": False, "error": f"Doctor is unavailable on {new_date}"}

        duration_minutes = int(profile.get("appointment_duration_minutes", 30))
        try:
            slot_h, slot_m = map(int, new_start_time.split(":"))
            slot_start_dt = datetime.combine(target_date, time(slot_h, slot_m))
            slot_end_dt = slot_start_dt + timedelta(minutes=duration_minutes)
            new_end_time = slot_end_dt.strftime("%H:%M")
        except Exception:
            return {"success": False, "error": "Invalid time format"}

        if target_date == today_local and slot_start_dt.time() <= now_local.time():
            return {"success": False, "error": "Selected time has already passed today"}

        # Check working hours
        wh = profile.get("working_hours", {"start": "09:00", "end": "17:00"})
        if new_start_time < wh.get("start", "09:00") or new_end_time > wh.get("end", "17:00"):
            return {"success": False, "error": "Selected time is outside doctor working hours"}

        # Check breaks
        for brk in profile.get("break_times", []):
            b_s, b_e = brk.get("start", ""), brk.get("end", "")
            if b_s and b_e and not (new_end_time <= b_s or new_start_time >= b_e):
                return {"success": False, "error": "Selected time conflicts with a scheduled break"}

        # Check conflict with other appointments (excluding this appointment)
        conflict = db.appointments.find_one({
            "_id": {"$ne": app_oid},
            "doctor_id": doctor_id,
            "appointment_date": new_date,
            "start_time": new_start_time,
            "status": {"$in": ["pending", "confirmed"]}
        })
        if conflict:
            return {"success": False, "error": "The selected time slot is already booked"}

        # Update appointment
        old_date = appointment["appointment_date"]
        old_time = appointment["start_time"]

        db.appointments.update_one(
            {"_id": app_oid},
            {
                "$set": {
                    "appointment_date": new_date,
                    "start_time": new_start_time,
                    "end_time": new_end_time,
                    "status": "pending",  # reset to pending confirmation upon reschedule
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )

        reschedule_msg = f"Appointment was rescheduled from {old_date} {old_time} to {new_date} at {new_start_time}."
        NotificationService.send_notification(
            recipient_user_id=appointment["patient_id"],
            title="Appointment Rescheduled",
            message=reschedule_msg,
            notification_type="reschedule"
        )
        NotificationService.send_notification(
            recipient_user_id=appointment["doctor_id"],
            title="Appointment Rescheduled",
            message=reschedule_msg,
            notification_type="reschedule"
        )

        AuditService.log_action(
            actor_user_id=u_oid,
            action="reschedule_appointment",
            target_type="appointment",
            target_id=app_oid,
            details={"from": f"{old_date} {old_time}", "to": f"{new_date} {new_start_time}"}
        )

        return {"success": True, "message": "Appointment rescheduled successfully!"}

    @staticmethod
    def update_status(appointment_id, new_status, actor_user_id, actor_role, reason=""):
        """
        Update appointment status: confirmed, completed, cancelled.
        Only doctors and admins can confirm or mark completed.
        """
        if not db.is_connected or db.appointments is None:
            return {"success": False, "error": "Database unavailable"}

        valid_statuses = ["pending", "confirmed", "completed", "cancelled"]
        if new_status not in valid_statuses:
            return {"success": False, "error": f"Invalid status '{new_status}'"}

        app_oid = ObjectId(appointment_id) if isinstance(appointment_id, str) else appointment_id
        appointment = db.appointments.find_one({"_id": app_oid})
        if not appointment:
            return {"success": False, "error": "Appointment not found"}

        # Role checks
        if actor_role == "doctor" and appointment["doctor_id"] != ObjectId(actor_user_id):
            return {"success": False, "error": "Unauthorized"}
        if actor_role == "patient" and new_status != "cancelled":
            return {"success": False, "error": "Patients cannot change appointment status directly"}

        update_data = {
            "status": new_status,
            "updated_at": datetime.now(timezone.utc)
        }
        if new_status == "cancelled":
            update_data["cancellation_reason"] = reason or f"Cancelled by {actor_role}"
            update_data["cancelled_by"] = actor_role

        db.appointments.update_one({"_id": app_oid}, {"$set": update_data})

        # Notifications
        title_map = {
            "confirmed": "Appointment Confirmed",
            "completed": "Appointment Completed",
            "cancelled": "Appointment Cancelled"
        }
        notif_msg = f"Your appointment on {appointment['appointment_date']} at {appointment['start_time']} has been marked as {new_status.capitalize()}."
        NotificationService.send_notification(
            recipient_user_id=appointment["patient_id"],
            title=title_map.get(new_status, "Appointment Updated"),
            message=notif_msg,
            notification_type="confirmation" if new_status == "confirmed" else "general"
        )

        AuditService.log_action(
            actor_user_id=actor_user_id,
            action=f"appointment_status_{new_status}",
            target_type="appointment",
            target_id=app_oid,
            details={"old_status": appointment["status"], "new_status": new_status, "reason": reason}
        )

        return {"success": True, "message": f"Appointment status updated to {new_status}"}

    @staticmethod
    def get_appointment_details(appointment_id):
        """Fetch complete appointment with patient and doctor details."""
        if not db.is_connected or db.appointments is None:
            return None

        app_oid = ObjectId(appointment_id) if isinstance(appointment_id, str) else appointment_id
        appointment = db.appointments.find_one({"_id": app_oid})
        if not appointment:
            return None

        patient = db.users.find_one({"_id": appointment["patient_id"]})
        doctor = db.users.find_one({"_id": appointment["doctor_id"]})
        doc_profile = db.doctor_profiles.find_one({"user_id": appointment["doctor_id"]})

        return {
            "appointment": appointment,
            "patient": patient,
            "doctor": doctor,
            "doctor_profile": doc_profile
        }
