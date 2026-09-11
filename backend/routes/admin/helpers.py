"""
Shared helper functions for admin routes.

_log_action      — persist an audit log entry.
_create_notification — broadcast an admin notification.
"""
from flask import request as flask_request
from flask_login import current_user

from database.models import db
from database.models.user import ActivityLog
from database.models.promotion import Notification


def _log_action(action: str, entity_type: str, entity_id: int, details: str = "") -> None:
    """Persist an audit log entry for a critical admin action (does NOT commit)."""
    try:
        ip = flask_request.remote_addr
    except RuntimeError:
        ip = None
    db.session.add(ActivityLog(
        user_id=current_user.id if current_user and current_user.is_authenticated else None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        ip_address=ip,
    ))


def _create_notification(title: str, message: str, notif_type: str = "info", link: str = None) -> None:
    """Create a broadcast admin notification — not user-specific (does NOT commit)."""
    db.session.add(Notification(
        user_id=None,
        title=title,
        message=message,
        notif_type=notif_type,
        link=link,
    ))
