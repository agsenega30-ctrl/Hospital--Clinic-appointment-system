from datetime import datetime, timezone
from bson import ObjectId
from db import db
from extensions import get_now_local

class AuditService:
    @staticmethod
    def log_action(actor_user_id, action, target_type, target_id=None, details=None):
        """Record an audit trail event."""
        if not db.is_connected or db.audit_logs is None:
            return None

        try:
            actor_oid = ObjectId(actor_user_id) if actor_user_id and isinstance(actor_user_id, str) else actor_user_id
            target_str = str(target_id) if target_id else None

            log_entry = {
                "actor_user_id": actor_oid,
                "action": action,
                "target_type": target_type,
                "target_id": target_str,
                "details": details or {},
                "timestamp": datetime.now(timezone.utc)
            }
            return db.audit_logs.insert_one(log_entry)
        except Exception as e:
            # Audit logging failure should not crash application flow
            print(f"[AUDIT LOG ERROR] Failed to record audit log: {e}")
            return None

    @staticmethod
    def get_recent_logs(limit=50, skip=0, action_filter=None):
        """Retrieve recent audit logs with actor information."""
        if not db.is_connected or db.audit_logs is None:
            return [], 0

        query = {}
        if action_filter:
            query["action"] = action_filter

        total = db.audit_logs.count_documents(query)
        logs = list(
            db.audit_logs.find(query)
            .sort("timestamp", -1)
            .skip(skip)
            .limit(limit)
        )

        # Populate actor info
        for log in logs:
            if log.get("actor_user_id"):
                user = db.users.find_one({"_id": log["actor_user_id"]}, {"full_name": 1, "email": 1, "role": 1})
                log["actor"] = user
            else:
                log["actor"] = {"full_name": "System", "email": "system@internal", "role": "system"}

        return logs, total
