from flask import Blueprint, render_template, request, jsonify, session
from bson import ObjectId
from db import db
from extensions import login_required, verify_csrf
from services.notification_service import NotificationService

notifications_bp = Blueprint("notifications", __name__)

@notifications_bp.route("/notifications")
@login_required
def view_notifications():
    """Render user notifications page."""
    user_id = session.get("user_id")
    page = int(request.args.get("page", 1))
    per_page = 20
    skip = (page - 1) * per_page

    items, total = NotificationService.get_user_notifications(user_id, limit=per_page, skip=skip)
    total_pages = max(1, (total + per_page - 1) // per_page)

    return render_template(
        "shared/notifications.html",
        notifications=items,
        current_page=page,
        total_pages=total_pages,
        total_count=total
    )

@notifications_bp.route("/api/notifications")
@login_required
def api_get_notifications():
    """JSON API to fetch recent notifications and unread counter for topbar dropdown."""
    user_id = session.get("user_id")
    items, total = NotificationService.get_user_notifications(user_id, limit=7)

    # Format items
    formatted = []
    unread_count = 0
    for item in items:
        if not item.get("is_read"):
            unread_count += 1
        formatted.append({
            "id": str(item["_id"]),
            "title": item.get("title", "Notification"),
            "message": item.get("message", ""),
            "type": item.get("notification_type", "general"),
            "is_read": item.get("is_read", False),
            "created_at": item["created_at"].strftime("%b %d, %H:%M") if item.get("created_at") else ""
        })

    return jsonify({
        "notifications": formatted,
        "unread_count": unread_count,
        "total": total
    })

@notifications_bp.route("/api/notifications/<notification_id>/read", methods=["POST"])
@login_required
def api_mark_read(notification_id):
    """Mark a notification as read."""
    verify_csrf()
    user_id = session.get("user_id")
    success = NotificationService.mark_as_read(notification_id, user_id)
    return jsonify({"success": success})

@notifications_bp.route("/api/notifications/read-all", methods=["POST"])
@login_required
def api_mark_all_read():
    """Mark all notifications as read for current user."""
    verify_csrf()
    user_id = session.get("user_id")
    count = NotificationService.mark_all_as_read(user_id)
    return jsonify({"success": True, "marked_count": count})
