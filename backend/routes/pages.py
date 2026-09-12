"""
Utility for serving static frontend SPA pages.

After removing Jinja2 templates, backend routes serve the pre-built
SPA HTML files (index.html, customer.html, admin.html) directly from
the frontend/ directory using Flask's send_from_directory.
"""
import os

from flask import send_from_directory

_FRONTEND_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', 'frontend')
)


def serve_frontend_page(filename):
    """Serve a static HTML page from the frontend directory.

    Args:
        filename: The HTML filename to serve (e.g. 'index.html', 'admin.html').

    Returns:
        Flask Response with the static file contents.
    """
    return send_from_directory(_FRONTEND_DIR, filename)
