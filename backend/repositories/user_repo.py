"""
User repository — data access for the users table.
"""

from backend.db import query


def find_by_google_id(google_id):
    """Find a user by their Google ID."""
    return query(
        "SELECT id, email, display_name, avatar_url FROM users WHERE google_id = %s",
        (google_id,),
        fetchone=True,
    )


def create(google_id, email, display_name, avatar_url):
    """Create a new user and return the created row."""
    return query(
        """
        INSERT INTO users (google_id, email, display_name, avatar_url)
        VALUES (%s, %s, %s, %s)
        RETURNING id, email, display_name, avatar_url
        """,
        (google_id, email, display_name, avatar_url),
        fetchone=True,
    )


def update_profile(google_id, display_name, avatar_url):
    """Update display name and avatar for a user."""
    query(
        "UPDATE users SET display_name = %s, avatar_url = %s WHERE google_id = %s",
        (display_name, avatar_url, google_id),
    )


def find_by_id(user_id):
    """Find a user by their internal ID."""
    return query(
        "SELECT id, email, display_name, avatar_url, created_at FROM users WHERE id = %s",
        (user_id,),
        fetchone=True,
    )
