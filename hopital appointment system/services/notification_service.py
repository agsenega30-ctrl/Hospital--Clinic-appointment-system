from datetime import datetime, timezone
from bson import ObjectId
from db import db

class NotificationService:
    @staticmethod
    def send_notification(recipient_user_id, title, message, notification_type="general"):
        """Create and store an in-app notification for a user."""
        if not db.is_connected or db.notifications is None:
            return None

        try:
            oid = ObjectId(recipient_user_id) if isinstance(recipient_user_id, str) else recipient_user_id
            notification = {
                "recipient_user_id": oid,
                "title": title,
                "message": message,
                "notification_type": notification_type,  # booking, confirmation, cancellation, reschedule, general
                "is_read": False,
                "created_at": datetime.now(timezone.utc)
            }
            return db.notifications.insert_one(notification)
        except Exception as e:
            print(f"[NOTIFICATION ERROR] Failed to send notification: {e}")
            return None

    @staticmethod
    def get_user_notifications(user_id, limit=30, skip=0, unread_only=False):
        """Retrieve notifications for a user, sorted newest first."""
        if not db.is_connected or db.notifications is None:
            return [], 0

        oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
        query = {"recipient_user_id": oid}
        if unread_only:
            query["is_read"] = False

        total = db.notifications.count_documents(query)
        items = list(
            db.notifications.find(query)
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )
        return items, total

    @staticmethod
    def mark_as_read(notification_id, user_id):
        """Mark a specific notification as read by its recipient."""
        if not db.is_connected or db.notifications is None:
            return False

        n_oid = ObjectId(notification_id) if isinstance(notification_id, str) else notification_id
        u_oid = ObjectId(user_id) if isinstance(user_id, str) else user_id

        result = db.notifications.update_one(
            {"_id": n_oid, "recipient_user_id": u_oid},
            {"$set": {"is_read": True}}
        )
        return result.modified_count > 0

    @staticmethod
    def mark_all_as_read(user_id):
        """Mark all notifications as read for a given user."""
        if not db.is_connected or db.notifications is None:
            return 0

        u_oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
        result = db.notifications.update_many(
            {"recipient_user_id": u_oid, "is_read": False},
            {"$set": {"is_read": True}}
        )
        return result.modified_count
