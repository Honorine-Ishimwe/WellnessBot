"""
User service — business logic for user management.
No Flask imports — pure Python logic.
"""

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from backend.config import GOOGLE_CLIENT_ID
from backend.repositories import user_repo
from backend.middleware.auth import _create_jwt


def authenticate_with_google(credential):
    """
    Verify a Google ID token and find/create the user.
    Returns (token, user_dict) on success.
    Raises ValueError if the token is invalid or the profile is incomplete.
    """
    # Verify the Google ID token
    idinfo = id_token.verify_oauth2_token(
        credential,
        google_requests.Request(),
        GOOGLE_CLIENT_ID,
    )

    # Extract user info from Google's verified payload
    google_id = idinfo.get("sub")
    email = idinfo.get("email", "")
    display_name = idinfo.get("name", "")
    avatar_url = idinfo.get("picture", "")

    if not google_id or not email:
        raise ValueError("Incomplete Google profile")

    # Find or create user
    user = user_repo.find_by_google_id(google_id)

    if user is None:
        user = user_repo.create(google_id, email, display_name, avatar_url)
    else:
        # Update display name / avatar in case they changed on Google's side
        user_repo.update_profile(google_id, display_name, avatar_url)

    # Issue our own JWT
    token = _create_jwt(user["id"], user["email"])

    user_dict = {
        "id": user["id"],
        "email": user["email"],
        "display_name": display_name or user["display_name"],
        "avatar_url": avatar_url or user["avatar_url"],
    }

    return token, user_dict


def get_profile(user_id):
    """Get a user's profile by ID. Returns dict or None."""
    user = user_repo.find_by_id(user_id)
    if user is None:
        return None

    user_dict = dict(user)
    if user_dict.get("created_at"):
        user_dict["created_at"] = user_dict["created_at"].isoformat()

    return user_dict
