"""
Decoupled API Backend Status Utility.

The frontend is completely decoupled and hosted separately (on Vercel in production
or via a local static server during development). When the backend receives requests
for pages, it returns an informative JSON status confirming the backend API is online.
"""
from flask import current_app, jsonify


def serve_frontend_page(filename=None):
    """Return backend status indicating the API is online and frontend is decoupled."""
    frontend_url = current_app.config.get('FRONTEND_URL', 'https://glossary-mart.vercel.app')
    return jsonify({
        "status": "online",
        "message": "e Grossary API Backend is running. Frontend is hosted separately on Vercel.",
        "frontend_url": frontend_url,
        "page_requested": filename
    }), 200

