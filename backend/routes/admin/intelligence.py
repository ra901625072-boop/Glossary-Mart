"""Admin business intelligence and decision-making routes."""
from flask import jsonify
from backend.services.intelligence_service import IntelligenceService
from backend.routes.decorators import admin_required
from . import admin_bp


@admin_bp.route('/intelligence')
@admin_required
def get_intelligence():
    """Return complete AI business intelligence, forecast, and health score payload."""
    payload = IntelligenceService.get_full_intelligence_payload()
    return jsonify(payload)


@admin_bp.route('/action-center')
@admin_required
def get_action_center():
    """Return prioritized Smart Alerts for Today's Attention."""
    alerts = IntelligenceService.get_action_center_alerts()
    return jsonify({
        'success': True,
        **alerts
    })


@admin_bp.route('/cashflow')
@admin_required
def get_cashflow():
    """Return cash-flow metrics (Today and Monthly)."""
    cf = IntelligenceService.calculate_cash_flow()
    return jsonify({
        'success': True,
        'cash_flow': cf
    })


@admin_bp.route('/health-score')
@admin_required
def get_health_score():
    """Return shop composite health score (0-100) and sub-indices."""
    hs = IntelligenceService.calculate_health_score()
    return jsonify({
        'success': True,
        'health_score': hs
    })


@admin_bp.route('/forecast')
@admin_required
def get_forecast():
    """Return sales and stockout predictive forecast."""
    fc = IntelligenceService.forecast_sales_and_demand()
    return jsonify({
        'success': True,
        'forecast': fc
    })


@admin_bp.route('/profitability-matrix')
@admin_required
def get_profitability_matrix():
    """Return BCG 4-quadrant product profitability matrix."""
    matrix = IntelligenceService.generate_profitability_matrix()
    return jsonify({
        'success': True,
        'profitability_matrix': matrix
    })
