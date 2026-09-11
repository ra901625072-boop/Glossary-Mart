"""Admin notification API endpoints (bell dropdown + mark-read)."""
from flask import jsonify

from database.models import db
from database.models.promotion import Notification
from backend.constants import MAX_NOTIFICATIONS
from backend.routes.decorators import admin_required
from . import admin_bp


@admin_bp.route('/api/notifications')
@admin_required
def api_notifications():
    """
    Return recent admin notifications with unread count.

    Returns JSON:
      {
        "unread_count": <int>,
        "notifications": [{id, title, message, notif_type, is_read, link, created_at}, ...]
      }
    """
    notifications = (
        db.session.query(Notification)
        .filter(Notification.user_id.is_(None))   # Broadcast (not user-specific)
        .order_by(Notification.created_at.desc())
        .limit(MAX_NOTIFICATIONS)
        .all()
    )
    unread_count = db.session.query(Notification).filter(
        Notification.user_id.is_(None),
        Notification.is_read == False,  # noqa: E712
    ).count()

    return jsonify({
        'unread_count': unread_count,
        'notifications': [
            {
                'id': n.id,
                'title': n.title,
                'message': n.message,
                'notif_type': n.notif_type,
                'is_read': n.is_read,
                'link': n.link or '',
                'created_at': n.created_at.strftime('%d %b %Y, %I:%M %p'),
            }
            for n in notifications
        ],
    })


@admin_bp.route('/api/notifications/mark-read', methods=['POST'])
@admin_required
def api_notifications_mark_read():
    """Mark all broadcast admin notifications as read."""
    db.session.query(Notification).filter(
        Notification.user_id.is_(None),
        Notification.is_read == False,  # noqa: E712
    ).update({'is_read': True}, synchronize_session=False)
    db.session.commit()
    return jsonify({'success': True})
