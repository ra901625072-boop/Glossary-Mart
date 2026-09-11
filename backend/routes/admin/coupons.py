"""Admin coupon management route."""
from flask import render_template

from database.models import db
from database.models.promotion import Coupon
from backend.routes.decorators import admin_required
from . import admin_bp


@admin_bp.route('/coupons')
@admin_required
def coupons():
    """List all discount coupons."""
    coupons_list = db.session.query(Coupon).order_by(Coupon.created_at.desc()).all()
    return render_template('admin/coupons.html', coupons=coupons_list)
