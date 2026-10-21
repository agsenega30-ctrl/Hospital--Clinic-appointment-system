import logging
from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import mongomock

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.client = None
        self.db = None
        self._is_connected = False
        self._connection_error = None
        self._is_mock = False

    def init_app(self, app):
        """Initialize database connection with Flask app configuration."""
        mongo_uri = app.config.get("MONGO_URI", "mongodb://localhost:27017/hospital_appointment_system")
        db_name = app.config.get("MONGO_DB_NAME", "hospital_appointment_system")
        is_testing = app.config.get("TESTING", False)

        if is_testing or mongo_uri.startswith("mongomock://"):
            logger.info("Initializing in-memory mongomock database for testing.")
            self.client = mongomock.MongoClient()
            self.db = self.client[db_name]
            self._is_connected = True
            self._is_mock = True
            self.create_indexes()
            return

        try:
            self.client = MongoClient(
                mongo_uri,
                serverSelectionTimeoutMS=app.config.get("MONGO_SERVER_SELECTION_TIMEOUT_MS", 2000),
                connectTimeoutMS=app.config.get("MONGO_CONNECT_TIMEOUT_MS", 2000),
            )
            # Test ping
            self.client.admin.command("ping")
            self.db = self.client.get_database(db_name)
            self._is_connected = True
            self._connection_error = None
            self._is_mock = False
            logger.info(f"Successfully connected to MongoDB database '{db_name}'.")
            self.create_indexes()
        except (ConnectionFailure, ServerSelectionTimeoutError, Exception) as exc:
            enable_fallback = app.config.get("ENABLE_EMBEDDED_FALLBACK", True)
            if enable_fallback:
                logger.warning(f"Live MongoDB not detected ({exc}). Switching to 1-Click Embedded Database Mode.")
                self.client = mongomock.MongoClient()
                self.db = self.client[db_name]
                self._is_connected = True
                self._is_mock = True
                self._connection_error = None
                self.create_indexes()
                # Pre-seed embedded database with demo accounts & doctors
                try:
                    from seed import run_seed
                    run_seed(database=self.db)
                except Exception as seed_err:
                    logger.warning(f"Auto-seed warning: {seed_err}")
            else:
                self._is_connected = False
                self._connection_error = str(exc)
                self.db = None
                logger.warning(
                    f"MongoDB connection failed: {exc}. Please verify MongoDB is running or check MONGO_URI in .env."
                )

    @property
    def is_connected(self):
        return self._is_connected

    @property
    def is_mock(self):
        return self._is_mock

    @property
    def connection_error(self):
        return self._connection_error

    def create_indexes(self):
        """Create indexes and unique constraints for data integrity and performance."""
        if self.db is None:
            return

        try:
            # Users collection: unique email
            self.db.users.create_index([("email", ASCENDING)], unique=True)
            self.db.users.create_index([("role", ASCENDING)])

            # Doctor profiles: unique user_id
            self.db.doctor_profiles.create_index([("user_id", ASCENDING)], unique=True)
            self.db.doctor_profiles.create_index([("specialization", ASCENDING)])
            self.db.doctor_profiles.create_index([("is_approved", ASCENDING)])

            # Specializations: unique name
            self.db.specializations.create_index([("name", ASCENDING)], unique=True)

            # Appointments indexes
            self.db.appointments.create_index([("patient_id", ASCENDING), ("appointment_date", ASCENDING)])
            self.db.appointments.create_index([("doctor_id", ASCENDING), ("appointment_date", ASCENDING)])
            self.db.appointments.create_index([("status", ASCENDING)])

            # Concurrency-safe unique compound index on active bookings:
            # Prevent double booking for the same doctor, date, and start_time when status in ('pending', 'confirmed')
            try:
                self.db.appointments.create_index(
                    [
                        ("doctor_id", ASCENDING),
                        ("appointment_date", ASCENDING),
                        ("start_time", ASCENDING)
                    ],
                    unique=True,
                    partialFilterExpression={"status": {"$in": ["pending", "confirmed"]}},
                    name="unique_doctor_active_slot"
                )
            except Exception as e:
                # Some mock libraries don't support partialFilterExpression
                logger.debug(f"Partial index not created (possibly mock client): {e}")

            # Notifications
            self.db.notifications.create_index([("recipient_user_id", ASCENDING), ("created_at", ASCENDING)])
            self.db.notifications.create_index([("is_read", ASCENDING)])

            # Audit logs
            self.db.audit_logs.create_index([("timestamp", ASCENDING)])
            self.db.audit_logs.create_index([("actor_user_id", ASCENDING)])
            
            logger.info("Database indexes ensured successfully.")
        except Exception as e:
            logger.warning(f"Error creating indexes: {e}")

    # Convenience properties for collections
    @property
    def users(self):
        return self.db.users if self.db is not None else None

    @property
    def doctor_profiles(self):
        return self.db.doctor_profiles if self.db is not None else None

    @property
    def appointments(self):
        return self.db.appointments if self.db is not None else None

    @property
    def notifications(self):
        return self.db.notifications if self.db is not None else None

    @property
    def specializations(self):
        return self.db.specializations if self.db is not None else None

    @property
    def audit_logs(self):
        return self.db.audit_logs if self.db is not None else None

    @property
    def platform_settings(self):
        return self.db.platform_settings if self.db is not None else None


# Global singleton instance
db = Database()
