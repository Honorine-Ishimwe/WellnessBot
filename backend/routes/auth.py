"""
Authentication routes — Google OAuth login and user profile.
Thin handlers that delegate to user_service.
"""

from flask import Blueprint, request, jsonify, g

from backend.middleware.auth import require_auth
from backend.services import user_service

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.post("/google")
def google_login():
    """
    Verify a Google ID token, create/find the user, and return a JWT.

    Expects JSON body: { "credential": "<google-id-token>" }
    """
    data = request.get_json(force=True) or {}
    credential = data.get("credential", "").strip()

    if not credential:
        return jsonify({"error": "Missing Google credential"}), 400

    try:
        token, user_dict = user_service.authenticate_with_google(credential)
    except ValueError as e:
        return jsonify({"error": str(e)}), 401

    return jsonify({"token": token, "user": user_dict})


@auth_bp.get("/me")
@require_auth
def get_me():
    """Return the current authenticated user's profile."""
    user_dict = user_service.get_profile(g.user_id)
    if user_dict is None:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"user": user_dict})
