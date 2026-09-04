"""
Google OAuth authentication for WellnessBot.
Provides /auth/google endpoint and @require_auth decorator.
"""

import os
import functools
from typing import Optional
from datetime import datetime, timezone, timedelta

import jwt
from flask import Blueprint, request, jsonify, g
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from db import query

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

JWT_SECRET = os.getenv("JWT_SECRET", "change-me-to-a-random-secret-string")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_DAYS = 7
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")


def _create_jwt(user_id: int, email: str) -> str:
    """Create a JWT token for a verified user."""
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRY_DAYS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _verify_jwt(token: str) -> Optional[dict]:
    """Verify and decode a JWT token. Returns payload or None."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def require_auth(f):
    """Decorator that requires a valid JWT in the Authorization header."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        token = auth_header[7:]  # Strip "Bearer "
        payload = _verify_jwt(token)
        if payload is None:
            return jsonify({"error": "Invalid or expired token"}), 401

        # Inject user info into Flask's g object
        g.user_id = payload["user_id"]
        g.user_email = payload["email"]
        return f(*args, **kwargs)

    return decorated


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

    # Verify the Google ID token
    try:
        idinfo = id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            GOOGLE_CLIENT_ID,
        )
    except ValueError as e:
        return jsonify({"error": f"Invalid Google token: {e}"}), 401

    # Extract user info from Google's verified payload
    google_id = idinfo.get("sub")
    email = idinfo.get("email", "")
    display_name = idinfo.get("name", "")
    avatar_url = idinfo.get("picture", "")

    if not google_id or not email:
        return jsonify({"error": "Incomplete Google profile"}), 400

    # Find or create user
    user = query(
        "SELECT id, email, display_name, avatar_url FROM users WHERE google_id = %s",
        (google_id,),
        fetchone=True,
    )

    if user is None:
        # Create new user
        user = query(
            """
            INSERT INTO users (google_id, email, display_name, avatar_url)
            VALUES (%s, %s, %s, %s)
            RETURNING id, email, display_name, avatar_url
            """,
            (google_id, email, display_name, avatar_url),
            fetchone=True,
        )
    else:
        # Update display name / avatar in case they changed on Google's side
        query(
            "UPDATE users SET display_name = %s, avatar_url = %s WHERE google_id = %s",
            (display_name, avatar_url, google_id),
        )

    # Issue our own JWT
    token = _create_jwt(user["id"], user["email"])

    return jsonify({
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "display_name": display_name or user["display_name"],
            "avatar_url": avatar_url or user["avatar_url"],
        },
    })


@auth_bp.get("/me")
@require_auth
def get_me():
    """Return the current authenticated user's profile."""
    user = query(
        "SELECT id, email, display_name, avatar_url, created_at FROM users WHERE id = %s",
        (g.user_id,),
        fetchone=True,
    )
    if user is None:
        return jsonify({"error": "User not found"}), 404

    # Convert datetime to string for JSON serialization
    user_dict = dict(user)
    if user_dict.get("created_at"):
        user_dict["created_at"] = user_dict["created_at"].isoformat()

    return jsonify({"user": user_dict})
