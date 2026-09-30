"""
JWT authentication middleware for WellnessBot.
Provides JWT creation/verification and the @require_auth decorator.
"""

import functools
from typing import Optional
from datetime import datetime, timezone, timedelta

import jwt
from flask import request, jsonify, g

from backend.config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRY_DAYS


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
