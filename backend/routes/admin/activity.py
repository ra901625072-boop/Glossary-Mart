"""Admin audit activity log viewer."""
from flask import render_template, request

from database.models import db
from database.models.user import ActivityLog
from backend.constants import MAX_ACTIVITY_LOG
from backend.routes.decorators import admin_required
from . import admin_bp


@admin_bp.route('/activity-log')
@admin_required
def activity_log():
    """Audit log viewer — last MAX_ACTIVITY_LOG entries, filterable by action type."""
    action_filter = request.args.get('action', '')
    query = db.session.query(ActivityLog).order_by(ActivityLog.created_at.desc())

    if action_filter:
        query = query.filter(ActivityLog.action == action_filter)

    page = request.args.get('page', 1, type=int)
    per_page = 50
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # Distinct action types for the filter dropdown
    action_types = [
        row[0] for row in
        db.session.query(ActivityLog.action).distinct().order_by(ActivityLog.action).all()
    ]

    return render_template(
        'admin/activity_log.html',
        logs=pagination.items,
        pagination=pagination,
        action_types=action_types,
        action_filter=action_filter,
    )
