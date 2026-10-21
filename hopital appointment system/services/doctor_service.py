from datetime import datetime, timezone
from bson import ObjectId
from db import db

class DoctorService:
    @staticmethod
    def get_doctor_by_id(doctor_user_id):
        """Fetch doctor user record and their profile."""
        if not db.is_connected or db.users is None:
            return None

        oid = ObjectId(doctor_user_id) if isinstance(doctor_user_id, str) else doctor_user_id
        user = db.users.find_one({"_id": oid, "role": "doctor"})
        if not user:
            return None

        profile = db.doctor_profiles.find_one({"user_id": oid})
        return {
            "user": user,
            "profile": profile or DoctorService.get_default_profile(oid)
        }

    @staticmethod
    def get_default_profile(user_id):
        """Default baseline profile for a new doctor."""
        return {
            "user_id": ObjectId(user_id) if isinstance(user_id, str) else user_id,
            "specialization": "General Medicine",
            "qualifications": "MBBS",
            "experience_years": 5,
            "consultation_fee": 500.0,
            "biography": "Dedicated healthcare specialist committed to compassionate patient care.",
            "working_hours": {"start": "09:00", "end": "17:00"},
            "working_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "break_times": [{"start": "13:00", "end": "14:00"}],
            "appointment_duration_minutes": 30,
            "blocked_dates": [],
            "is_approved": True
        }

    @staticmethod
    def ensure_doctor_profile(user_id, initial_data=None):
        """Ensure doctor profile document exists in database."""
        if not db.is_connected or db.doctor_profiles is None:
            return None

        oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
        profile = db.doctor_profiles.find_one({"user_id": oid})
        if not profile:
            new_profile = DoctorService.get_default_profile(oid)
            if initial_data:
                new_profile.update(initial_data)
            db.doctor_profiles.insert_one(new_profile)
            return new_profile
        return profile

    @staticmethod
    def update_doctor_profile(user_id, data):
        """Update doctor professional details and schedule parameters."""
        if not db.is_connected or db.doctor_profiles is None:
            return False

        oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
        allowed_fields = [
            "specialization", "qualifications", "experience_years",
            "consultation_fee", "biography", "working_hours",
            "working_days", "break_times", "appointment_duration_minutes",
            "blocked_dates", "is_approved"
        ]
        update_data = {k: v for k, v in data.items() if k in allowed_fields}
        update_data["updated_at"] = datetime.now(timezone.utc)

        result = db.doctor_profiles.update_one(
            {"user_id": oid},
            {"$set": update_data},
            upsert=True
        )
        return True

    @staticmethod
    def search_doctors(search_query="", specialization="", date_str="", page=1, per_page=12, approved_only=True):
        """Search and filter doctors with pagination."""
        if not db.is_connected or db.users is None:
            return [], 0

        # Query users collection
        user_query = {"role": "doctor"}
        if approved_only:
            user_query["account_status"] = "active"

        if search_query:
            user_query["$or"] = [
                {"full_name": {"$regex": search_query, "$options": "i"}},
                {"email": {"$regex": search_query, "$options": "i"}}
            ]

        doctors_cursor = db.users.find(user_query)
        doctors_list = list(doctors_cursor)

        results = []
        for doctor in doctors_list:
            profile = db.doctor_profiles.find_one({"user_id": doctor["_id"]})
            if not profile:
                profile = DoctorService.get_default_profile(doctor["_id"])

            if approved_only and not profile.get("is_approved", True):
                continue

            if specialization and profile.get("specialization") != specialization:
                continue

            # Optional filter by day of week if date provided
            if date_str:
                try:
                    target_date = datetime.strptime(date_str, "%Y-%m-%d")
                    day_name = target_date.strftime("%A")
                    working_days = profile.get("working_days", [])
                    blocked_dates = profile.get("blocked_dates", [])

                    if day_name not in working_days or date_str in blocked_dates:
                        continue
                except ValueError:
                    pass

            results.append({
                "user": doctor,
                "profile": profile
            })

        total = len(results)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_results = results[start:end]

        return paginated_results, total

    @staticmethod
    def get_specializations():
        """Retrieve list of active specializations."""
        if not db.is_connected or db.specializations is None:
            return []
        return list(db.specializations.find({"is_active": True}).sort("name", 1))
