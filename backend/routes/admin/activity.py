"""Admin audit activity log viewer."""
from flask import jsonify, request

from database.models import db
from database.models.user import ActivityLog
from backend.routes.decorators import admin_required
from . import admin_bp


@admin_bp.route('/activity-log')
@admin_required
def activity_log():
    """Audit log viewer — returns JSON list, filterable by action type."""
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

    return jsonify({
        'success': True,
        'logs': [
            {
                'id': log.id,
                'user_id': log.user_id,
                'action': log.action,
                'entity_type': log.entity_type,
                'entity_id': log.entity_id,
                'details': log.details or '',
                'ip_address': log.ip_address or '',
                'created_at': log.created_at.isoformat() if log.created_at else None,
            }
            for log in pagination.items
        ],
        'pagination': {
            'page': pagination.page,
            'pages': pagination.pages,
            'total': pagination.total,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next,
        },
        'action_types': action_types,
        'action_filter': action_filter,
    })
