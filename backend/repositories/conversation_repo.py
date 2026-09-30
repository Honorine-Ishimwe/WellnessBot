"""
Conversation repository — data access for the conversations table.
"""

from backend.db import query, execute


def create(user_id, title, mood=None):
    """Create a new conversation and return its ID."""
    row = query(
        """
        INSERT INTO conversations (user_id, title, mood)
        VALUES (%s, %s, %s)
        RETURNING id
        """,
        (user_id, title, mood),
        fetchone=True,
    )
    return row["id"]


def update_mood(conversation_id, user_id, mood):
    """Update the mood for a conversation."""
    execute(
        "UPDATE conversations SET mood = %s WHERE id = %s AND user_id = %s",
        (mood, conversation_id, user_id),
    )


def list_by_user(user_id):
    """List all conversations for a user, most recent first."""
    return query(
        """
        SELECT id, title, mood, created_at, updated_at
        FROM conversations
        WHERE user_id = %s
        ORDER BY updated_at DESC
        """,
        (user_id,),
        fetchall=True,
    ) or []


def find_by_id_and_user(conversation_id, user_id):
    """Find a conversation by ID, scoped to a user."""
    return query(
        "SELECT id, title, mood FROM conversations WHERE id = %s AND user_id = %s",
        (conversation_id, user_id),
        fetchone=True,
    )


def delete(conversation_id):
    """Delete a conversation and all its messages (via CASCADE)."""
    execute("DELETE FROM conversations WHERE id = %s", (conversation_id,))


def delete_older_than(days):
    """Delete conversations older than the given number of days. Returns deleted rows."""
    return query(
        """
        DELETE FROM conversations
        WHERE updated_at < NOW() - INTERVAL '%s days'
        RETURNING id
        """,
        (days,),
        fetchall=True,
    )
